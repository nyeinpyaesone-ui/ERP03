FROM node:20.20.2-alpine3.23 AS builder

WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund --legacy-peer-deps
COPY . .
RUN npm run build

FROM nginx:1.29.1-alpine3.22
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
