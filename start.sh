#!/bin/bash

# Inicia o Kokoro em background (já vem na imagem oficial)
# A imagem oficial já roda o servidor na porta 8880
cd /app/kokoro || true

# Verifica se o Kokoro já está rodando
sleep 3

# Testa se o Kokoro responde
for i in {1..10}; do
    if curl -s http://localhost:8880/v1/audio/voices > /dev/null 2>&1; then
        echo "✅ Kokoro está rodando!"
        break
    fi
    echo "⏳ Aguardando Kokoro iniciar... ($i/10)"
    sleep 2
done

# Inicia o handler do RunPod
cd /app
python handler.py
