# ============================================
# USA IMAGEM OFICIAL DO KOKORO (já buildada!)
# ============================================
FROM ghcr.io/remsky/kokoro-fastapi-gpu:latest

# ============================================
# INSTALA RUNPOD SDK (só isso!)
# ============================================
RUN pip install --no-cache-dir runpod

# ============================================
# COPIA NOSSO HANDLER
# ============================================
WORKDIR /app
COPY handler.py .

# ============================================
# START SCRIPT: roda Kokoro + RunPod juntos
# ============================================
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ============================================
# COMANDO DE START
# ============================================
CMD ["/start.sh"]
