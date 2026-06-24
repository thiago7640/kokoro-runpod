#!/bin/bash

# ============================================
# START.SH - INICIA KOKORO SERVER + RUNPOD HANDLER
# ============================================

set -e

echo "🚀 Iniciando Kokoro Server + RunPod Worker..."

# ============================================
# CONFIGURAÇÕES DO KOKORO
# ============================================
export KOKORO_PORT=8880
export KOKORO_LOG_LEVEL=INFO

echo "   Porta: $KOKORO_PORT"

# ============================================
# INICIA O SERVIDOR KOKORO EM BACKGROUND
# ============================================
echo "   Iniciando servidor Kokoro FastAPI..."

cd /opt/kokoro-server || cd /app || true

# Inicia o servidor em background na porta 8880
python -m uvicorn main:app --host 0.0.0.0 --port $KOKORO_PORT &

KOKORO_PID=$!

echo "   PID do Kokoro: $KOKORO_PID"

# ============================================
# AGUARDA O SERVIDOR INICIAR
# ============================================
echo "   Aguardando Kokoro ficar pronto..."

for i in {1..60}; do
    if curl -s http://localhost:$KOKORO_PORT/v1/models > /dev/null 2>&1; then
        echo "   ✅ Kokoro está rodando na porta $KOKORO_PORT!"
        break
    fi

    if [ $i -eq 60 ]; then
        echo "   ❌ Timeout! Kokoro não iniciou em 60 segundos."
        exit 1
    fi

    echo "   ⏳ Tentativa $i/60..."
    sleep 1
done

# ============================================
# INICIA O HANDLER DO RUNPOD
# ============================================
echo "   Iniciando RunPod Serverless Handler..."
cd /app
exec python -u handler.py
