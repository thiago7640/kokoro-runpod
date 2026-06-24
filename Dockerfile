# ============================================
# USA IMAGEM HWDSL2/KOKORO-SERVER (já tem tudo!)
# ============================================
FROM hwdsl2/kokoro-server:latest

# ============================================
# INSTALA APENAS O RUNPOD SDK
# ============================================
RUN pip install --no-cache-dir runpod

# ============================================
# COPIA OS ARQUIVOS DO HANDLER
# ============================================
WORKDIR /app

COPY handler.py .
COPY start.sh /start.sh

# ============================================
# TORNA O START.SH EXECUTÁVEL
# ============================================
RUN chmod +x /start.sh

# ============================================
# COMANDO DE START OBRIGATÓRIO DO RUNPOD
# ============================================
CMD ["/start.sh"]
