"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const crypto_1 = __importDefault(require("crypto"));
const body_parser_1 = __importDefault(require("body-parser"));
const ioredis_1 = require("ioredis");
const axios_1 = __importDefault(require("axios"));
const env_1 = require("./config/env");
const app = (0, express_1.default)();
const redis = new ioredis_1.Redis(env_1.config.REDIS_URL, { maxRetriesPerRequest: null });
// Redis Stream Keys
const STREAM_KEY = 'erp03:github:events';
const GROUP_NAME = 'rlm-worker-group';
const CONSUMER_NAME = `worker-${process.pid}`;
// Initialize Stream & Consumer Group
async function initStreams() {
    try {
        await redis.xGroup('CREATE', STREAM_KEY, GROUP_NAME, '0', 'MKSTREAM');
    }
    catch (e) {
        if (!e.message.includes('BUSYGROUP'))
            console.error('Stream init error:', e);
    }
}
// Middleware: Raw Body Parser for Signature Verification
app.use(body_parser_1.default.json({ verify: (req, res, buffer) => { req.rawBody = buffer; } }));
// Middleware: Security & Idempotency Check
const verifySignature = async (req, res, next) => {
    const sig = req.headers['x-hub-signature-256'];
    const deliveryId = req.headers['x-github-delivery'];
    if (!deliveryId)
        return res.status(400).json({ error: 'Missing Delivery ID' });
    // Check for duplicates in cache (5 min window)
    const exists = await redis.get(`processed:${deliveryId}`);
    if (exists) {
        console.log(`⚠️ Duplicate event ignored: ${deliveryId}`);
        return res.status(200).json({ status: 'duplicate_ignored' });
    }
    if (!sig)
        return res.status(401).json({ error: 'No Signature' });
    const hmac = crypto_1.default.createHmac('sha256', env_1.config.WEBHOOK_GITHUB_KEY);
    const digest = 'sha256=' + hmac.update(req.rawBody).digest('hex');
    if (!crypto_1.default.timingSafeEqual(Buffer.from(sig), Buffer.from(digest))) {
        console.warn(`🚫 Invalid signature attempt from ${req.ip}`);
        return res.status(403).json({ error: 'Forbidden' });
    }
    next();
};
// Route: High-Speed Ingestion (<20ms)
app.post('/webhook/github', verifySignature, async (req, res) => {
    const event = req.headers['x-github-event'];
    const payload = req.body;
    const deliveryId = req.headers['x-github-delivery'];
    // Push to Redis Stream (Durable Queue)
    await redis.xAdd(STREAM_KEY, '*', {
        event: event,
        deliveryId: deliveryId,
        repo: payload.repository?.full_name || 'unknown',
        payload: JSON.stringify(payload)
    });
    // Mark as seen to prevent duplicates
    await redis.setEx(`processed:${deliveryId}`, 300, 'true');
    // Immediate Acknowledgement
    res.status(202).json({ status: 'queued', id: deliveryId });
});
// Background Worker: Process & Forward
async function processStream() {
    console.log(`🚀 Worker ${CONSUMER_NAME} started...`);
    while (true) {
        try {
            const results = await redis.xReadGroup(GROUP_NAME, CONSUMER_NAME, { key: STREAM_KEY, id: '>' }, { COUNT: 10, BLOCK: 5000 });
            if (!results)
                continue;
            for (const [, messages] of results) {
                for (const [id, message] of messages) {
                    const { event, deliveryId, payload } = message;
                    console.log(`⚙️ Processing ${event} (${deliveryId})`);
                    try {
                        const data = JSON.parse(payload);
                        // 1. Forward to ERP Production Endpoint
                        await axios_1.default.post(env_1.config.ERP_WEBHOOK_URL, data, {
                            headers: {
                                'X-GitHub-Event': event,
                                'X-GitHub-Delivery': deliveryId,
                                'Content-Type': 'application/json'
                            },
                            timeout: 5000
                        });
                        console.log(`✅ Forwarded ${event} to ${env_1.config.ERP_WEBHOOK_URL}`);
                        // Acknowledge Success
                        await redis.xAck(STREAM_KEY, GROUP_NAME, id);
                    }
                    catch (err) {
                        console.error(`❌ Failed to process ${id}:`, err);
                    }
                }
            }
        }
        catch (err) {
            console.error('Stream read error:', err);
            await new Promise(r => setTimeout(r, 2000));
        }
    }
}
// Startup
(async () => {
    await initStreams();
    app.listen(parseInt(env_1.config.PORT), () => {
        console.log(`✅ RLM Core Listening on :${env_1.config.PORT}`);
        console.log(`🔗 Webhook URL: https://${process.env.CODESPACE_NAME}-3000.app.github.dev/webhook/github`);
        console.log(`🎯 Forwarding to: ${env_1.config.ERP_WEBHOOK_URL}`);
    });
    processStream();
})();
//# sourceMappingURL=index.js.map