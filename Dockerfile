# Usa a imagem GPU do Kokoro, apropriada para endpoint Runpod com GPU
FROM hwdsl2/kokoro-server:cuda

WORKDIR /app

# Instala o SDK do Runpod no mesmo ambiente Python da imagem
RUN /opt/venv/bin/pip install --no-cache-dir runpod requests

# Copia arquivos do worker
COPY handler.py /app/handler.py
COPY start.sh /app/start.sh

# Permissão de execução
RUN chmod +x /app/start.sh

# Config opcional do Kokoro
ENV PYTHONUNBUFFERED=1
ENV KOKORO_PORT=8880
ENV KOKORO_LOG_LEVEL=INFO

# Sobe pelo script que inicia Kokoro + worker
CMD ["/app/start.sh"]
