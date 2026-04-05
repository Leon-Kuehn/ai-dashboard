#!/bin/sh
set -e

SSL_DIR="/etc/nginx/ssl"
CERT="$SSL_DIR/cert.pem"
KEY="$SSL_DIR/key.pem"

# VM_IP can be set in .env to your Proxmox VM's LAN IP (e.g. 192.168.1.50).
# If not set, defaults to 127.0.0.1.
# The cert includes BOTH IPs as Subject Alternative Names so the browser
# trusts HTTPS whether you access via localhost or the LAN IP.
VM_IP="${VM_IP:-127.0.0.1}"

# Generate self-signed certificate if it does not already exist
if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
  mkdir -p "$SSL_DIR"
  openssl req -x509 -nodes -days 3650 \
    -newkey rsa:2048 \
    -keyout "$KEY" \
    -out "$CERT" \
    -subj "/C=DE/ST=Local/L=Local/O=ai-dashboard/CN=ai-dashboard" \
    -addext "subjectAltName=IP:127.0.0.1,IP:${VM_IP}"
  echo "Self-signed TLS certificate generated (SAN: 127.0.0.1, ${VM_IP})."
fi

# Expand environment variables in the nginx config template.
# Only the listed variables are substituted; nginx's own $-variables are left intact.
envsubst '${OLLAMA_HOST} ${OLLAMA_PORT} ${OPENCLAW_HOST} ${OPENCLAW_PORT}' \
  < /etc/nginx/nginx.conf.template \
  > /tmp/nginx.conf

exec nginx -c /tmp/nginx.conf -g "daemon off;"
