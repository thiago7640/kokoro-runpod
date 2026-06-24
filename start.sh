#!/bin/bash

# ============================================
# START.SH - RUNPOD SERVERLESS HANDLER
# ============================================
# O servidor Kokoro já está rodando via ENTRYPOINT da imagem!
# Não precisamos iniciar manualmente.
# ============================================

set -e

echo "🚀 Iniciando RunPod Serverless Worker..."
echo "   Container: $(hostname)"
echo "   Python: $(python3 --version 2>/dev/null || python --version)"

# ============================================
# VERIFICA SE O KOKORO ESTÁ RODANDO
# ============================================
echo "   Verificando se Kokoro está disponível..."

for i in {1..30}; do
    if curl -s http://localhost:8880/v1/models > /dev/null 2>&1; then
        echo "   ✅ Kokoro está rodando na porta 8880!"
        break
    fi

    if [ $i -eq 30 ]; then
        echo "   ⚠️  Kokoro não respondeu em 30 segundos, mas vamos tentar mesmo assim..."
    fi

    echo "   ⏳ Tentativa $i/30..."
    sleep 1
done

# ============================================
# INICIA O HANDLER DO RUNPOD
# ============================================
echo "   Iniciando RunPod Serverless Handler..."
cd /app
exec python3 -u handler.py
