# Multi-stage Dockerfile for RLM Service
# Optimized for security, size, and production use

# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
COPY tsconfig.json ./
COPY src/ ./src/

RUN npm ci && \
    npm run build && \
    npm prune --production && \
    npm cache clean --force

# Stage 3: Runner (Minimal, Non-Root)
FROM node:20-alpine AS runner
WORKDIR /app

# Security: Create non-root user
RUN addgroup --system --gid 1001 rlm-group && \
    adduser --system --uid 1001 rlm-user

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy built application from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

# Change ownership to non-root user
RUN chown -R rlm-user:rlm-group /app

# Switch to non-root user
USER rlm-user

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start the application
CMD ["node", "dist/index.js"]

# Metadata
LABEL org.opencontainers.image.title="ERP03 RLM Service"
LABEL org.opencontainers.image.description="Repository Lifecycle Management Service for ERP03"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/nyeinpyaesone-ui/ERP03"
LABEL org.opencontainers.image.vendor="ERP03 DevOps Team"
LABEL security.hardening.enabled="true"
LABEL security.non-root="true"
LABEL security.read-only-fs="recommended"
