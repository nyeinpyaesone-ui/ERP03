# syntax=docker/dockerfile:1
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --no-audit --no-fund

COPY index.html ./
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine AS runtime

RUN addgroup -g 1000 app && adduser -u 1000 -G app -s /bin/sh -D app

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build --chown=app:app /app/dist /usr/share/nginx/html

USER app

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
