#!/bin/sh
set -eu

cert_dir=/etc/nginx/certs
cert_file="$cert_dir/localhost.crt"
key_file="$cert_dir/localhost.key"

mkdir -p "$cert_dir"

if [ ! -f "$cert_file" ] || [ ! -f "$key_file" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -sha256 -days 365 \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    -keyout "$key_file" \
    -out "$cert_file"
fi

exec nginx -g "daemon off;"
