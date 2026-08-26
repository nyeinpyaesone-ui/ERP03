import express, { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';
import bodyParser from 'body-parser';
import Redis from 'ioredis';
import dotenv from 'dotenv';
import winston from 'winston';
import rateLimit from 'express-rate-limit';

// Load environment variables
dotenv.config();

// Configuration with strict validation
const PORT = process.env.PORT || 3000;
const WEBHOOK_KEY = process.env.WEBHOOK_GITHUB_KEY;
const TARGET_URL = process.env.WEBHOOK_GITHUB_URL;
const REPO_OWNER = process.env.REPO_OWNER || 'nyeinpyaesone-ui';
const REPO_NAME = process.env.REPO_NAME || 'ERP03';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';

// Critical dependency validation
if (!WEBHOOK_KEY) {
  console.error('❌ CRITICAL: WEBHOOK_GITHUB_KEY is not set in environment');
  process.exit(1);
}

if (!TARGET_URL) {
  console.error('❌ CRITICAL: WEBHOOK_GITHUB_URL is not set in environment');
  process.exit(1);
}

// Logger setup
const logger = winston.createLogger({
  level: LOG_LEVEL,
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'rlm-service', repository: `${REPO_OWNER}/${REPO_NAME}` },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' })
  ]
});

// Initialize Express app
const app = express();

// Redis client with retry logic
const redis = new Redis(REDIS_URL, {
  retryStrategy: (times) => {
    const delay = Math.min(times * 50, 2000);
    logger.warn(`Redis connection retry ${times}, delay: ${delay}ms`);
    return delay;
  },
  maxRetriesPerRequest: 3
});

redis.on('error', (err) => logger.error('Redis error:', err));
redis.on('connect', () => logger.info('Redis connected successfully'));

// Rate limiting middleware
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000'),
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'),
  message: { error: 'Too many requests, please try again later' },
  standardHeaders: true,
  legacyHeaders: false,
});

// Apply rate limiting to all routes
app.use(limiter);

// Raw body parser for signature verification (must be before JSON parser)
app.use(bodyParser.json({
  verify: (req: any, res, buffer, encoding) => {
    if (buffer.length) {
      req.rawBody = buffer.toString(encoding as BufferEncoding || 'utf-8');
    }
  }
}));

// Health check endpoint
app.get('/health', async (req: Request, res: Response) => {
  const redisStatus = redis.status === 'ready' ? 'connected' : 'disconnected';
  res.json({
    status: 'healthy',
    service: 'rlm-service',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    redis: redisStatus,
    repository: `${REPO_OWNER}/${REPO_NAME}`
  });
});

// Metrics endpoint
app.get('/metrics', async (req: Request, res: Response) => {
  try {
    const queueLength = await redis.llen('rlm_events');
    res.json({
      queue_length: queueLength,
      redis_status: redis.status,
      uptime: process.uptime()
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve metrics' });
  }
});

// Security middleware: HMAC-SHA256 signature verification
const verifyGitHubSignature = (req: Request, res: Response, next: NextFunction) => {
  const signature = req.headers['x-hub-signature-256'] as string;
  const event = req.headers['x-github-event'] as string;
  const deliveryId = req.headers['x-github-delivery'] as string;
  const repository = req.body.repository;

  // Scope validation: Ensure event is ONLY from authorized repository
  if (!repository || repository.full_name !== `${REPO_OWNER}/${REPO_NAME}`) {
    logger.warn({
      event: 'unauthorized_repository',
      repository: repository?.full_name || 'unknown',
      deliveryId
    });
    return res.status(403).json({ 
      error: 'Unauthorized Repository',
      message: 'Events from this repository are not accepted'
    });
  }

  // Signature presence check
  if (!signature) {
    logger.warn({
      event: 'missing_signature',
      repository: repository.full_name,
      deliveryId
    });
    return res.status(401).json({ error: 'Missing X-Hub-Signature-256 header' });
  }

  // HMAC calculation
  const hmac = crypto.createHmac('sha256', WEBHOOK_KEY);
  const digest = 'sha256=' + hmac.update(req.rawBody || '').digest('hex');

  // Timing-safe comparison to prevent timing attacks
  const signatureBuffer = Buffer.from(signature);
  const digestBuffer = Buffer.from(digest);

  if (!crypto.timingSafeEqual(signatureBuffer, digestBuffer)) {
    logger.warn({
      event: 'invalid_signature',
      repository: repository.full_name,
      deliveryId,
      ip: req.ip
    });
    return res.status(403).json({ error: 'Invalid signature' });
  }

  // Attach metadata to request for downstream handlers
  res.locals.githubEvent = event;
  res.locals.deliveryId = deliveryId;
  res.locals.repository = repository.full_name;

  next();
};

// Webhook endpoint - main entry point for GitHub events
app.post('/webhook/github', verifyGitHubSignature, async (req: Request, res: Response) => {
  const event = res.locals.githubEvent;
  const deliveryId = res.locals.deliveryId;
  const payload = req.body;

  logger.info({
    event: 'webhook_received',
    eventType: event,
    deliveryId,
    repository: res.locals.repository,
    action: payload.action
  });

  try {
    // Create structured event object
    const webhookEvent = {
      id: deliveryId,
      event: event,
      action: payload.action,
      receivedAt: new Date().toISOString(),
      repository: res.locals.repository,
      sender: payload.sender?.login,
      payload: payload
    };

    // Queue event for asynchronous processing
    await redis.lPush('rlm_events', JSON.stringify(webhookEvent));
    
    logger.info({
      event: 'webhook_queued',
      deliveryId,
      queue: 'rlm_events'
    });

    // Respond immediately to GitHub (required < 3 seconds)
    res.status(200).json({ 
      status: 'received', 
      id: deliveryId,
      queued: true
    });

    // Trigger background processor (in production, this would be a separate worker)
    processQueue().catch(err => logger.error('Queue processing failed:', err));

  } catch (error) {
    logger.error({
      event: 'queue_error',
      deliveryId,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
    
    res.status(500).json({ 
      error: 'Internal Queue Failure',
      deliveryId 
    });
  }
});

// Background queue processor
async function processQueue() {
  if (redis.status !== 'ready') {
    logger.warn('Cannot process queue: Redis not ready');
    return;
  }

  const item = await redis.rPop('rlm_events');
  
  if (item) {
    const eventData = JSON.parse(item);
    
    logger.info({
      event: 'processing_event',
      deliveryId: eventData.id,
      eventType: eventData.event
    });

    try {
      // Forward to internal ERP endpoint
      const axios = require('axios');
      await axios.post(TARGET_URL, eventData.payload, {
        headers: {
          'X-GitHub-Event': eventData.event,
          'X-GitHub-Delivery': eventData.id,
          'X-RLM-Processed': 'true',
          'Content-Type': 'application/json'
        },
        timeout: 5000
      });

      logger.info({
        event: 'forwarded_to_erp',
        deliveryId: eventData.id,
        targetUrl: TARGET_URL
      });

    } catch (error) {
      logger.error({
        event: 'forward_failed',
        deliveryId: eventData.id,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      
      // Re-queue for retry on failure
      await redis.lPush('rlm_events_dead_letter', JSON.stringify({
        ...eventData,
        failedAt: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error'
      }));
    }
  }
}

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error({
    event: 'unhandled_error',
    path: req.path,
    error: err.message,
    stack: err.stack
  });

  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({ error: 'Not Found' });
});

// Start server
app.listen(PORT, () => {
  logger.info({
    event: 'service_started',
    port: PORT,
    environment: process.env.NODE_ENV,
    repository: `${REPO_OWNER}/${REPO_NAME}`,
    webhookUrl: '/webhook/github'
  });
  
  console.log(`🚀 RLM Service running on port ${PORT}`);
  console.log(`🎯 Scope: ${REPO_OWNER}/${REPO_NAME}`);
  console.log(`🔗 Webhook endpoint: http://localhost:${PORT}/webhook/github`);
  console.log(`❤️ Health check: http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  await redis.quit();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully');
  await redis.quit();
  process.exit(0);
});

export default app;
