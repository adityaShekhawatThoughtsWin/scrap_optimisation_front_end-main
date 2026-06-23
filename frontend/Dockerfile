# syntax=docker/dockerfile:1

FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
# npm install (not ci): lockfile from Windows may omit Linux-only optional deps (e.g. @emnapi/*)
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

RUN apk add --no-cache gettext

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r$//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

COPY --from=builder /app/dist /usr/share/nginx/html

ENV BACKEND_HOST=backend
ENV BACKEND_PORT=8000

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
