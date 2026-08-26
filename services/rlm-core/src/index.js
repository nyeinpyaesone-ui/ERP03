const express = require('express');
const crypto = require('crypto');
const bodyParser = require('body-parser');
const Redis = require('ioredis');
const axios = require('axios');

const PORT = process.env.PORT || 3000;
const WEBHOOK_GITHUB_KEY = process.env.WEBHOOK_GITHUB_KEY;
const ERP_WEBHOOK_URL = process.env.ERP_WEBHOOK_URL || 'https://erp.anynoob.com/webhook/';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

if (!WEBHOOK_GITHUB_KEY) {
  console.error('❌ FATAL: WEBHOOK_GITHUB_KEY is missing');
  process.exit(1);
}

const app = express();
const redis = new Redis(REDIS_URL, { maxRetriesPerRequest: null });

const STREAM_KEY = 'erp03:github:events';
const GROUP_NAME = 'rlm-worker-group';
const CONSUMER_NAME = `worker-${process.pid}`;

async function initStreams() {
  try {
    await redis.xgroup('CREATE', STREAM_KEY, GROUP_NAME, '0', 'MKSTREAM');
  } catch (e) {
    if (!e.message.includes('BUSYGROUP')) console.error('Stream init error:', e);
  }
}

app.use(bodyParser.json({ verify: (req, res, buffer) => { req.rawBody = buffer; } }));

const verifySignature = async (req, res, next) => {
  const sig = req.headers['x-hub-signature-256'];
  const deliveryId = req.headers['x-github-delivery'];

  if (!deliveryId) return res.status(400).json({ error: 'Missing Delivery ID' });

  const exists = await redis.get(`processed:${deliveryId}`);
  if (exists) {
    console.log(`⚠️ Duplicate event ignored: ${deliveryId}`);
    return res.status(200).json({ status: 'duplicate_ignored' });
  }

  if (!sig) return res.status(401).json({ error: 'No Signature' });

  const hmac = crypto.createHmac('sha256', WEBHOOK_GITHUB_KEY);
  const digest = 'sha256=' + hmac.update(req.rawBody).digest('hex');

  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(digest))) {
    console.warn(`🚫 Invalid signature attempt from ${req.ip}`);
    return res.status(403).json({ error: 'Forbidden' });
  }

  next();
};

app.post('/webhook/github', verifySignature, async (req, res) => {
  const event = req.headers['x-github-event'];
  const payload = req.body;
  const deliveryId = req.headers['x-github-delivery'];

  // Fixed: Proper xadd syntax with separate key-value pairs
  await redis.xadd(STREAM_KEY, '*', 
    'event', event || 'unknown',
    'deliveryId', deliveryId || 'no-id',
    'repo', payload.repository?.full_name || 'unknown',
    'payload', JSON.stringify(payload)
  );

  await redis.setex(`processed:${deliveryId}`, 300, 'true');
  res.status(202).json({ status: 'queued', id: deliveryId });
});

async function processStream() {
  console.log(`🚀 Worker ${CONSUMER_NAME} started...`);
  
  while (true) {
    try {
      const results = await redis.xreadgroup(
        'GROUP', GROUP_NAME, CONSUMER_NAME, 
        'COUNT', 10, 
        'BLOCK', 5000,
        'STREAMS', STREAM_KEY, '>'
      );

      if (!results) continue;

      for (const [, messages] of results) {
        for (const [id, message] of messages) {
          const { event, deliveryId, payload } = message;
          console.log(`⚙️ Processing ${event} (${deliveryId})`);

          try {
            const data = JSON.parse(payload);
            
            await axios.post(ERP_WEBHOOK_URL, data, {
              headers: {
                'X-GitHub-Event': event,
                'X-GitHub-Delivery': deliveryId,
                'Content-Type': 'application/json'
              },
              timeout: 5000
            });

            console.log(`✅ Forwarded ${event} to ${ERP_WEBHOOK_URL}`);
            await redis.xack(STREAM_KEY, GROUP_NAME, id);
          } catch (err) {
            console.error(`❌ Failed to process ${id}:`, err.message);
          }
        }
      }
    } catch (err) {
      console.error('Stream read error:', err.message);
      await new Promise(r => setTimeout(r, 2000));
    }
  }
}

(async () => {
  await initStreams();
  app.listen(parseInt(PORT), () => {
    const codespace = process.env.CODESPACE_NAME || 'fantastic-garbanzo-qv7pg7px7x76fxwg9';
    console.log(`✅ RLM Core Listening on :${PORT}`);
    console.log(`🔗 Webhook URL: https://${codespace}-${PORT}.app.github.dev/webhook/github`);
    console.log(`🎯 Forwarding to: ${ERP_WEBHOOK_URL}`);
  });
  processStream();
})();
