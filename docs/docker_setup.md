# Setup Docker — MLOps, une commande

## Ce que ça fait

`./docker-start.sh` : construit l'image, démarre le conteneur, indexe automatiquement le corpus si la base n'existe pas encore, attend que le serveur réponde, ouvre le navigateur sur `http://localhost:8000`.

- **`Dockerfile`** : image Python 3.11-slim, healthcheck intégré.
- **`docker/entrypoint.sh`** : vérifie si `data/vector_store/chroma.sqlite3` existe ; si non, lance `python index.py` avant de démarrer le serveur.
- **`docker-compose.yml`** : port 8000, volume nommé `vector_store` pour la persistance, `.env` chargé.
- **`docker-start.sh`** : vérifie que `.env`/`GROQ_API_KEY` existent avant de lancer quoi que ce soit, build + run, attend que le serveur réponde (avec un timeout), ouvre le navigateur.

## Bug trouvé et corrigé lors du premier build réel

Le premier build a semblé bloqué (plus de 10 minutes, débit en chute libre). En creusant les logs, la cause n'était pas un problème réseau : `pip install sentence-transformers` installe `torch` qui, par défaut sur Linux, tire la variante **CUDA/GPU** — plus de 2,5 Go de bibliothèques NVIDIA (`nvidia-cudnn`, `nvidia-cublas`, `nvidia-cufft`, `nvidia-curand`, `nvidia-cusolver`...) totalement inutiles ici : le conteneur tourne en CPU, ChromaDB et sentence-transformers n'ont besoin d'aucun GPU.

**Corrigé** en installant explicitement la variante CPU-only de `torch` avant le reste de `requirements.txt` :

```dockerfile
RUN pip install --no-cache-dir --timeout=180 --retries=10 \
    torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --timeout=180 --retries=10 -r requirements.txt
```

Un `--timeout`/`--retries` plus généreux a aussi été ajouté par précaution (les gros paquets peuvent dépasser le timeout par défaut de pip sur une connexion modeste), mais la vraie cause était bien les paquets CUDA superflus, pas le réseau.

## Vérification effectuée (build réel, pas juste la syntaxe)

- `docker compose build` : succès après le fix (`EXIT_CODE: 0`).
- `docker compose up -d` : démarrage propre, logs confirmant l'auto-indexation (`Base vectorielle absente : indexation initiale...` puis `Base vectorielle construite : 877 chunks indexes.`).
- `curl http://localhost:8000/` : page de chat servie (HTTP 200).
- `curl -X POST http://localhost:8000/ask` : réponse réelle avec citation d'article et vérification de fraîcheur Légifrance en direct (`"fraicheur": "à jour (vérifié en direct sur Légifrance)"`).
- `docker compose restart` : redémarrage confirmé **sans réindexation** (aucune nouvelle occurrence de « Base vectorielle absente » dans les logs après le premier démarrage) — la base persiste bien dans le volume nommé `vector_store`.
- Healthcheck Docker : statut `healthy` après le démarrage.
