FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# torch (dependance de sentence-transformers) tire par defaut les paquets CUDA
# GPU sur Linux (plusieurs Go inutiles ici, le conteneur tourne en CPU) :
# on force la version CPU-only avant le reste, ca coupe le build de ~2,5 Go.
RUN pip install --no-cache-dir --timeout=180 --retries=10 \
    torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --timeout=180 --retries=10 -r requirements.txt

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["docker/entrypoint.sh"]
