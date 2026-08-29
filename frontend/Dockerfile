FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install --include=dev --no-audit --no-fund \
    && npm cache clean --force

COPY . .

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_APP_VERSION=production
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_APP_VERSION=$VITE_APP_VERSION

RUN npm run build

FROM nginx:1.31-alpine AS production

RUN rm -f /etc/nginx/conf.d/default.conf \
    && sed -i '/^user /d' /etc/nginx/nginx.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

RUN chown -R nginx:nginx /usr/share/nginx/html \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:80/ || exit 1

USER nginx
CMD ["nginx", "-g", "daemon off;"]
