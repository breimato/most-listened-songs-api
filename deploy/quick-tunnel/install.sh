#!/usr/bin/env bash
set -euo pipefail

# Instala el quick tunnel de Youtube como servicios de usuario systemd.
# El túnel apunta a Traefik (127.0.0.1:80) con Host youtube.home.arpa.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/../../frontend" && pwd)"
DATA_DIR="$HOME/.local/share/youtube-tunnel"
UNIT_DIR="$HOME/.config/systemd/user"
CLOUDFLARED="$DATA_DIR/cloudflared"

mkdir -p "$DATA_DIR" "$UNIT_DIR"

if [[ ! -x "$CLOUDFLARED" ]]; then
  echo "Descargando cloudflared…"
  curl -fsSL -o "$CLOUDFLARED" \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod 700 "$CLOUDFLARED"
fi

install -m 700 "$SCRIPT_DIR/refresh-runtime.py" "$DATA_DIR/refresh-runtime.py"

sed "s|__CLOUDFLARED__|$CLOUDFLARED|" \
  "$SCRIPT_DIR/youtube-quick-tunnel.service" > "$UNIT_DIR/youtube-quick-tunnel.service"
sed -e "s|__FRONTEND_DIR__|$FRONTEND_DIR|" \
  -e "s|__SCRIPT__|$DATA_DIR/refresh-runtime.py|" \
  "$SCRIPT_DIR/youtube-quick-runtime.service" > "$UNIT_DIR/youtube-quick-runtime.service"

systemctl --user daemon-reload
systemctl --user enable --now youtube-quick-tunnel.service youtube-quick-runtime.service

echo "Servicios instalados y arrancados:"
systemctl --user --no-pager --lines=0 status youtube-quick-tunnel.service youtube-quick-runtime.service
