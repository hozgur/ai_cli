#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
PYTHON="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON" ]; then
  echo "Python bulunamadi. Once Python 3 kurun."
  exit 1
fi
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/ask" <<EOT
#!/bin/bash
exec "$PYTHON" "$SCRIPT_DIR/app.py" "\$@"
EOT
chmod +x "$BIN_DIR/ask"
echo "ask komutu $BIN_DIR dizinine kuruldu."
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    if [ -f "$rc" ]; then
      echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$rc"
    fi
  done
  echo "$BIN_DIR dizini PATH'e eklendi. Degisikliklerin etkili olmasi icin yeni terminal acin."
else
  echo "$BIN_DIR zaten PATH'te."
fi
