# RLM Service Setup Guide

## Prerequisites
- Node.js 20+ installed
- Redis server running
- GitHub repository secrets configured

## Quick Start (Codespaces)

### 1. Configure GitHub Secrets
Before running locally, ensure these secrets are set in your GitHub repository:
- `WEBHOOK_GITHUB_KEY` - 64-character hex secret (generate with `openssl rand -hex 32`)
- `WEBHOOK_GITHUB_URL` - Your internal ERP endpoint (e.g., `https://erp.anynoob.com/webhook/github`)

These secrets will be automatically injected into your Codespace environment.

### 2. Install Dependencies
```bash
cd /workspace/rlm-service
npm install
```

### 3. Start Redis
```bash
# In Codespaces, Redis may already be available
# If not, start it:
redis-server --daemonize yes
```

### 4. Run the Service
```bash
# Development mode with hot reload
npm run dev

# Or build and run production
npm run build
npm start
```

### 5. Verify Installation
Check the health endpoint:
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "rlm-service",
  "version": "1.0.0",
  "timestamp": "2024-...",
  "redis": "connected",
  "repository": "nyeinpyaesone-ui/ERP03"
}
```

## GitHub Webhook Configuration

### Update Your GitHub Webhook
1. Go to repository Settings → Webhooks
2. Edit existing webhook or create new one
3. Set Payload URL to your Codespace URL:
   ```
   https://<YOUR_CODESPACE_NAME>-3000.app.github.dev/webhook/github
   ```
4. Set Content type: `application/json`
5. Set Secret: Same value as `WEBHOOK_GITHUB_KEY` secret
6. Select events: Push, Pull Request, Release, Workflow Run
7. Ensure SSL verification is enabled
8. Save changes

### Test the Webhook
1. In GitHub webhook settings, click "Redeliver" on a recent delivery
2. Check service logs for successful processing
3. Verify metrics endpoint: `curl http://localhost:3000/metrics`

## Production Deployment

### Docker Build
```bash
cd /workspace/rlm-service
docker build -t ghcr.io/nyeinpyaesone-ui/rlm-service:latest .
```

### Docker Run
```bash
docker run -d \
  --name rlm-service \
  -p 3000:3000 \
  -e WEBHOOK_GITHUB_KEY=$WEBHOOK_GITHUB_KEY \
  -e WEBHOOK_GITHUB_URL=$WEBHOOK_GITHUB_URL \
  -e REDIS_URL=redis://redis-host:6379 \
  ghcr.io/nyeinpyaesone-ui/rlm-service:latest
```

### Kubernetes Deployment
See `/workspace/infra/rlm-service/` for K8s manifests.

## Troubleshooting

### Common Issues

**Service won't start:**
- Check that `WEBHOOK_GITHUB_KEY` and `WEBHOOK_GITHUB_URL` are set
- Verify Redis is running and accessible
- Check logs: `docker logs rlm-service`

**Webhook signature failures:**
- Ensure GitHub webhook secret matches `WEBHOOK_GITHUB_KEY`
- Verify no extra whitespace in secret value
- Check system clock synchronization

**Redis connection errors:**
- Verify Redis URL format: `redis://host:port`
- Check firewall rules if using remote Redis
- Test connection: `redis-cli ping`

### Logs Location
- Console output (development)
- `logs/combined.log` (all logs)
- `logs/error.log` (errors only)

## Monitoring

### Health Check
```bash
curl http://localhost:3000/health
```

### Metrics
```bash
curl http://localhost:3000/metrics
```

### Queue Depth
```bash
redis-cli llen rlm_events
```

## Security Notes

- Never commit `.env` file with real secrets
- Rotate `WEBHOOK_GITHUB_KEY` periodically
- Use HTTPS for all production endpoints
- Enable rate limiting in production
- Monitor dead letter queue: `rlm_events_dead_letter`

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review `REPOSITORY_LIFECYCLE_MANAGEMENT.md` for architecture details
3. Contact DevOps team for production issues
