# ERP03 Repository Lifecycle Manager (RLM)

## Setup Instructions

### 1. Install Dependencies
```bash
cd /workspace/services/rlm-core
npm install
```

### 2. Configure Environment Variables
Set these in your GitHub Codespace Secrets or export them locally:
```bash
export WEBHOOK_GITHUB_KEY="your-generated-secret-here"
export GITHUB_TOKEN="your-github-pat-here"
export ERP_WEBHOOK_URL="https://erp.anynoob.com/webhook/"
```

### 3. Start Redis
```bash
redis-server --daemonize yes
```

### 4. Run the Service
```bash
npm run dev
```

### 5. Update GitHub Webhook
- Go to Settings > Webhooks
- Set Payload URL to: `https://<your-codespace-name>-3000.app.github.dev/webhook/github`
- Set Secret to match `WEBHOOK_GITHUB_KEY`
- Enable SSL verification
- Select events: Push, Pull Request, Release, Issue Comment

## Architecture
- **Ingestion**: Express.js server with HMAC verification (<20ms response)
- **Queue**: Redis Streams for durable, scalable event processing
- **Worker**: Background processor with idempotency checks
- **Forwarding**: Securely relays validated events to ERP production endpoint
