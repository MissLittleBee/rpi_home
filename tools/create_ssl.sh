#!/bin/bash

# create_ssl.sh: Generate self-signed SSL certificates for nginx

set -e

# Get project root directory
PROJECT_ROOT="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")"
# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load configuration if available
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
    CERT_HOSTNAME=${HOSTNAME:-ha.local}
    CERT_SERVER_IP=${SERVER_IP:-192.168.1.100}  
    CERT_VPN_IP=${VPN_IP:-10.10.20.1}
else
    # Fallback to defaults
    CERT_HOSTNAME="ha.local"
    CERT_SERVER_IP="192.168.1.100"
    CERT_VPN_IP="10.10.20.1"
fi

CERT_DIR="$PROJECT_ROOT/nginx/cert"
CRT_FILE="$CERT_DIR/server.crt"
KEY_FILE="$CERT_DIR/server.key"
CONF_FILE="$CERT_DIR/openssl.cnf"

# Create cert directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate OpenSSL configuration with dynamic values
cat > "$CONF_FILE" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = CZ
ST = Czech Republic
L = Prague
O = Home Server
OU = IT Department
CN = ${CERT_HOSTNAME}

[v3_req]
keyUsage = digitalSignature, keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${CERT_HOSTNAME}
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ${CERT_SERVER_IP}
IP.3 = ${CERT_VPN_IP}
EOF

# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout "$KEY_FILE" \
    -out "$CRT_FILE" \
    -config "$CONF_FILE" \
    -extensions v3_req

chmod 600 "$KEY_FILE" "$CRT_FILE"

echo "SSL certificates generated:"
echo "  Certificate: $CRT_FILE"
echo "  Private key: $KEY_FILE"
echo ""
echo "Certificate valid for:"
echo "  - ${CERT_HOSTNAME}"
echo "  - localhost"
echo "  - 127.0.0.1"
echo "  - ${CERT_SERVER_IP}"
echo "  - ${CERT_VPN_IP}"
