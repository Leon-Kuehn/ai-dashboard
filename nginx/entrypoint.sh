#!/bin/sh
set -e

SSL_DIR="/etc/nginx/ssl"
CERT="$SSL_DIR/cert.pem"
KEY="$SSL_DIR/key.pem"

# Generate self-signed certificate if it does not already exist
if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
  mkdir -p "$SSL_DIR"
  openssl req -x509 -nodes -days 3650 \
    -newkey rsa:2048 \
    -keyout "$KEY" \
    -out "$CERT" \
    -subj "/C=US/ST=Local/L=Local/O=ai-dashboard/CN=ai-dashboard" \
    -addext "subjectAltName=IP:127.0.0.1"
  echo "Self-signed TLS certificate generated."
fi

# Expand environment variables in the nginx config template.
# Only the listed variables are substituted; nginx's own $-variables are left intact.
envsubst '${OLLAMA_HOST} ${OLLAMA_PORT} ${OPENCLAW_HOST} ${OPENCLAW_PORT}' \
  < /etc/nginx/nginx.conf.template \
  > /tmp/nginx.conf

exec nginx -c /tmp/nginx.conf -g "daemon off;"
