# Assistant Code du travail (RAG)

Assistant juridique répondant à des questions sur le droit du travail français, avec citation systématique des articles du Code du travail. Projet réalisé dans le cadre du M2 MD5 — Data & IA.

> Cet assistant ne fournit pas de conseil juridique. Consultez un avocat ou l'inspection du travail pour votre situation personnelle.

## Sommaire

- [Installation](#installation)
- [Utilisation](#utilisation)
- [Choix techniques](#choix-techniques)
- [Questions de réflexion](#questions-de-réflexion)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # puis renseigner GROQ_API_KEY
```

## Utilisation


## Choix techniques

_À compléter : source du corpus (option A/B/C), stratégie de chunking, modèle d'embedding, base vectorielle, modèle Groq utilisé..._

## Questions de réflexion

### 1. Granularité du chunking

_Indexer chaque article séparément ou regrouper par section ? Avantages/inconvénients des deux approches, choix retenu et pourquoi. Une approche hybride est-elle envisageable ?_

[À compléter]

### 2. Traçabilité

_Où stockez-vous le numéro d'article (texte embeddé ? métadonnées ? les deux ?) et comment garantissez-vous que le LLM le cite correctement plutôt que d'en inventer un ?_

[À compléter]

### 3. Fraîcheur

_Comment le système indique-t-il honnêtement la date du corpus et le risque d'obsolescence ?_

[À compléter]

### 4. Réponses conditionnelles

_Comment le prompt gère-t-il les cas où la réponse dépend de la taille de l'entreprise ou de la convention collective : réponse générale assortie de réserves ? question de clarification ?_

[À compléter]

### 5. La frontière du conseil juridique

_Comment distinguer une question à laquelle le Code répond directement d'une question qui demande une interprétation ? Que doit faire le système dans le second cas ?_

[À compléter]
