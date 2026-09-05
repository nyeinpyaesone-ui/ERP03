import express, { Request, Response } from 'express';
import crypto from 'crypto';
import bodyParser from 'body-parser';
import Redis from 'ioredis';
import axios from 'axios';
import { config } from './config/env';

const app = express();
const redis = new Redis(config.REDIS_URL, { maxRetriesPerRequest: null });

// Redis Stream Keys
const STREAM_KEY = 'erp03:github:events';
const GROUP_NAME = 'rlm-worker-group';
const CONSUMER_NAME = `worker-${process.pid}`;

// Initialize Stream & Consumer Group
async function initStreams() {
  try {
    await (redis as any).xgroup('CREATE', STREAM_KEY, GROUP_NAME, '0', 'MKSTREAM');
  } catch (e: any) {
    if (!e.message.includes('BUSYGROUP')) console.error('Stream init error:', e);
  }
}

// Middleware: Raw Body Parser for Signature Verification
app.use(bodyParser.json({ verify: (req: any, res, buffer) => { (req as any).rawBody = buffer; } }));

// Middleware: Security & Idempotency Check
const verifySignature = async (req: Request, res: Response, next: any) => {
  const sig = req.headers['x-hub-signature-256'] as string;
  const deliveryId = req.headers['x-github-delivery'] as string;

  if (!deliveryId) return res.status(400).json({ error: 'Missing Delivery ID' });

  // Check for duplicates in cache (5 min window)
  const exists = await redis.get(`processed:${deliveryId}`);
  if (exists) {
    console.log(`⚠️ Duplicate event ignored: ${deliveryId}`);
    return res.status(200).json({ status: 'duplicate_ignored' });
  }

  if (!sig) return res.status(401).json({ error: 'No Signature' });

  const hmac = crypto.createHmac('sha256', config.WEBHOOK_GITHUB_KEY);
  const digest = 'sha256=' + hmac.update((req as any).rawBody || '').digest('hex');

  // Safe comparison: check length first, then compare content
  if (sig.length !== digest.length || !crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(digest))) {
    console.warn(`🚫 Invalid signature attempt from ${req.ip}`);
    return res.status(403).json({ error: 'Forbidden' });
  }

  next();
};

// Route: High-Speed Ingestion (<20ms)
app.post('/webhook/github', verifySignature, async (req: Request, res: Response) => {
  const event = req.headers['x-github-event'];
  const payload = req.body;
  const deliveryId = req.headers['x-github-delivery'];

  // Push to Redis Stream (Durable Queue)
  await (redis as any).xadd(STREAM_KEY, '*', {
    event: event as string,
    deliveryId: deliveryId as string,
    repo: payload.repository?.full_name || 'unknown',
    payload: JSON.stringify(payload)
  });

  // Mark as seen to prevent duplicates
  await redis.setex(`processed:${deliveryId}`, 300, 'true');

  // Immediate Acknowledgement
  res.status(202).json({ status: 'queued', id: deliveryId });
});

// Background Worker: Process & Forward
async function processStream() {
  console.log(`🚀 Worker ${CONSUMER_NAME} started...`);
  
  while (true) {
    try {
      const results = await (redis as any).xreadgroup(
        'GROUP', 
        GROUP_NAME, 
        `worker-${process.pid}`, 
        'COUNT', 10, 
        'BLOCK', 5000,
        'STREAMS', STREAM_KEY, '>'
      );

      if (!results || !Array.isArray(results)) continue;

      for (const [, messages] of results as any[]) {
        for (const [id, message] of messages) {
          const msg = message as any;
          const { event, deliveryId, payload } = msg;
          console.log(`⚙️ Processing ${event} (${deliveryId})`);

          try {
            const data = JSON.parse(payload);
            
            // Forward to ERP Production Endpoint
            await axios.post(config.ERP_WEBHOOK_URL, data, {
              headers: {
                'X-GitHub-Event': event,
                'X-GitHub-Delivery': deliveryId,
                'Content-Type': 'application/json'
              },
              timeout: 5000
            });

            console.log(`✅ Forwarded ${deliveryId} to ${config.ERP_WEBHOOK_URL}`);

            // Acknowledge Success
            await (redis as any).xack(STREAM_KEY, GROUP_NAME, id);
          } catch (err: any) {
            console.error(`❌ Failed to process ${id}:`, err.message);
          }
        }
      }
    } catch (err: any) {
      console.error('Stream read error:', err.message);
      await new Promise(r => setTimeout(r, 2000));
    }
  }
}

// Startup
(async () => {
  await initStreams();
  app.listen(parseInt(config.PORT), () => {
    console.log(`✅ RLM Core Listening on :${config.PORT}`);
    console.log(`🔗 Webhook URL: https://${process.env.CODESPACE_NAME || 'localhost'}-${config.PORT}.app.github.dev/webhook/github`);
    console.log(`🎯 Forwarding to: ${config.ERP_WEBHOOK_URL}`);
  });
  processStream();
})();
