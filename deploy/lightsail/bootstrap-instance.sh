#!/bin/bash
set -Eeuo pipefail

dnf update -y
dnf install -y docker nginx certbot python3-certbot-nginx
systemctl enable --now docker
systemctl enable --now nginx

cat >/etc/nginx/conf.d/navira-redirect.conf <<'NGINX'
server {
    listen 80 default_server;
    server_name _;
    location ^~ /.well-known/acme-challenge/ { root /var/www/html; }
    location / { return 444; }
}
NGINX

nginx -t
systemctl reload nginx
