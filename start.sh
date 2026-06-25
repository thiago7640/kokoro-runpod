#!/bin/bash
set -euo pipefail

echo "🚀 Iniciando container Kokoro + RunPod Worker..."
echo "   Hostname: $(hostname)"
echo "   Python: $(/opt/venv/bin/python --version)"
echo "   KOKORO_PORT: ${KOKORO_PORT:-8880}"

# Inicia o servidor Kokoro em background
echo "🎙️ Iniciando servidor Kokoro..."
/opt/venv/bin/python /api_server.py &
KOKORO_PID=$!

cleanup() {
  echo "🛑 Encerrando processos..."
  kill -TERM "$KOKORO_PID" 2>/dev/null || true
}
trap cleanup EXIT TERM INT

# Aguarda o Kokoro responder
echo "⏳ Aguardando Kokoro ficar pronto..."
for i in $(seq 1 120); do
  if curl -fsS "http://127.0.0.1:${KOKORO_PORT:-8880}/v1/models" >/dev/null 2>&1; then
    echo "✅ Kokoro pronto na porta ${KOKORO_PORT:-8880}"
    break
  fi

  if ! kill -0 "$KOKORO_PID" 2>/dev/null; then
    echo "❌ Processo do Kokoro morreu antes de ficar pronto"
    exit 1
  fi

  echo "   tentativa $i/120"
  sleep 2
done

if ! curl -fsS "http://127.0.0.1:${KOKORO_PORT:-8880}/v1/models" >/dev/null 2>&1; then
  echo "❌ Kokoro não respondeu a tempo"
  exit 1
fi

# Inicia o worker Runpod em foreground
echo "🤖 Iniciando RunPod handler..."
cd /app
exec /opt/venv/bin/python -u handler.py
