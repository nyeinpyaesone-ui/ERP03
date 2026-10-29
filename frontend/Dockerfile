# syntax=docker/dockerfile:1
FROM node:22-alpine AS build

ARG VITE_API_BASE_URL=/api

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

COPY index.html ./
COPY vite.config.js ./
COPY src ./src
RUN VITE_API_BASE_URL=${VITE_API_BASE_URL} npm run build

FROM nginx:1.27-alpine AS runtime

RUN addgroup -g 1000 app && adduser -u 1000 -G app -s /bin/sh -D app

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build --chown=app:app /app/dist /usr/share/nginx/html

# nginx master process must run as root to bind the privileged port 80;
# worker processes drop to the unprivileged `nginx` user automatically.
EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
