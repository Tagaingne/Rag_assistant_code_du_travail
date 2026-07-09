#!/bin/sh
set -e

URL="http://localhost:8000"

if [ ! -f .env ]; then
    echo "Fichier .env manquant. Copiez .env.example vers .env et renseignez GROQ_API_KEY avant de continuer."
    exit 1
fi

if ! grep -q "^GROQ_API_KEY=.\+" .env; then
    echo "GROQ_API_KEY manquant ou vide dans .env."
    exit 1
fi

echo "Construction et demarrage du conteneur..."
echo "(premier demarrage : telechargement du modele d'embedding + indexation, quelques minutes)"
docker compose up --build -d

max_attempts=600
attempt=0
until curl -sf "$URL" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "$max_attempts" ]; then
        echo "Le serveur ne repond pas apres $((max_attempts * 2))s. Verifiez les logs : docker compose logs -f"
        exit 1
    fi
    if [ $((attempt % 30)) -eq 0 ]; then
        echo "Toujours en attente... ($((attempt * 2))s ecoulees, le telechargement du modele d'embedding peut prendre du temps sur une premiere execution)"
    fi
    sleep 2
done

echo "Assistant pret sur $URL"

if command -v open >/dev/null 2>&1; then
    open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"
else
    echo "Ouvrez $URL dans votre navigateur."
fi
