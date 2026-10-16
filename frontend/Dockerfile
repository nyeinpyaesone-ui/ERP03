# syntax=docker/dockerfile:1
# Frontend image: Vite build copied into a non-root nginx runtime.
#
# The build stage uses the committed lockfile (npm ci) so builds are
# reproducible. The runtime stage runs nginx as the unprivileged `nginx` user
# on port 8080 with writable state in /tmp, so no root privileges are needed
# to serve static assets.

FROM node:22-alpine@sha256:2c752226d477b4a886378baa95b9af252be59301b725fdb0b7e15208131505a8 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html ./
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine@sha256:62223d644fa234c3a1cc785ee14242ec47a77364226f1c811d2f669f96dc2ac8

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
