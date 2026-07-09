# Assistant Code du travail (RAG)

Assistant juridique répondant à des questions sur le droit du travail français, avec citation systématique des articles du Code du travail. Projet réalisé dans le cadre du M2 MD5 — Data & IA.

> Cet assistant ne fournit pas de conseil juridique. Consultez un avocat ou l'inspection du travail pour votre situation personnelle.

## Sommaire

- [Installation](#installation)
- [Utilisation](#utilisation)
- [Versions](#versions)
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

```bash
# 1. Préparer le corpus LEGI (jalon 1) — détails : docs/jalon1_corpus_legi.md
python src/data/extract_legi_corpus.py

# 2. Construire et persister la base vectorielle (jalon 2, à lancer une seule fois)
python index.py

# 3. Valider le retrieval avant de brancher le LLM (jalon 3)
python evaluate_retrieval.py

# 4. Interroger l'assistant (jalon 4-5)
python main.py
```

## Versions

| Tag | Contenu | Détail |
|---|---|---|
| `v0.1.0` | Jalons 1 à 3 : corpus LEGI, chunking/indexation, retrieval validé sur 5 questions | [docs/jalon1_corpus_legi.md](docs/jalon1_corpus_legi.md), [docs/jalon2_jalon3_indexation_retrieval.md](docs/jalon2_jalon3_indexation_retrieval.md) |
| `v1.0.0` | Jalons 1 à 5 : pipeline complet — génération avec citations, modération anti-injection, interface CLI interactive | [docs/fix_integration_jalon2_4.md](docs/fix_integration_jalon2_4.md) |

Les deux tags sont posés sur `main`. `v1.0.0` a été validé de bout en bout (indexation, retrieval, génération, modération, CLI) avec un vrai appel à l'API Groq avant d'être taggé.

## Choix techniques

| Choix | Décision | Détail |
|---|---|---|
| Source du corpus | Option B — base LEGI (data.gouv.fr) | [docs/jalon1_corpus_legi.md](docs/jalon1_corpus_legi.md) |
| Stratégie de chunking | Par article, section en métadonnée, seuil de découpage secondaire à 1500 caractères | [Q1](#1-granularité-du-chunking), [docs/jalon2_jalon3_indexation_retrieval.md](docs/jalon2_jalon3_indexation_retrieval.md) |
| Modèle d'embedding | `intfloat/multilingual-e5-base` (sentence-transformers), choisi après comparaison empirique, fixé par l'équipe via `.env` | [docs/jalon2_jalon3_indexation_retrieval.md](docs/jalon2_jalon3_indexation_retrieval.md) |
| Base vectorielle | ChromaDB, persistance locale, métadonnées + nom du modèle stockés avec la collection | [docs/jalon2_jalon3_indexation_retrieval.md](docs/jalon2_jalon3_indexation_retrieval.md) |
| Validation du retrieval | 5 questions de test, 3 modèles d'embedding comparés (2/5 → 4/5 → 5/5) | [docs/jalon2_jalon3_indexation_retrieval.md](docs/jalon2_jalon3_indexation_retrieval.md) |
| Amélioration jalon 6 | Décomposition (exigée à l'oral) + recherche hybride (utile en général, moins urgente depuis le 5/5) | [docs/jalon6_ameliorations.md](docs/jalon6_ameliorations.md) |
| Modèle Groq | `openai/gpt-oss-120b` (génération), `openai/gpt-oss-safeguard-20b` (modérateur) — fixés par l'équipe via `.env` | [Jalon 6](docs/jalon6_ameliorations.md) |

## Questions de réflexion

### 1. Granularité du chunking

**Chunking par article (isolé)**

Avantages :
- Correspond à l'unité atomique du droit : un article = une règle complète et autonome. C'est le cas idéal pour ce corpus : le Code du travail est structuré en articles numérotés, regroupés en sections thématiques.
- Citation précise et sans ambiguïté : un chunk = un numéro d'article, donc pas de risque de citer un mauvais article ou d'en fusionner plusieurs.
- Les articles du Code du travail sont déjà courts et denses → peu de risque de dépasser une taille de chunk raisonnable, peu de coupures en pleine phrase.

Inconvénients :
- Perte de contexte inter-articles : les articles se citent entre eux (« au sens de l'article L1234-5... »), donc un article isolé peut être difficile à interpréter seul.
- Certains articles très courts (une seule phrase, un simple renvoi) produisent des chunks pauvres en signal sémantique, donc mal retrouvés par la recherche vectorielle.
- Aucune vision d'ensemble de la section thématique dans le vecteur lui-même.

**Chunking par section**

Avantages :
- Conserve le fil directeur thématique, utile pour les questions larges (« comment fonctionne la rupture conventionnelle ? » touche plusieurs articles liés).
- Moins de chunks à gérer, moins de doublons de contexte.

Inconvénients :
- Les sections sont souvent trop longues pour un chunk efficace → dilution vectorielle : un vecteur qui mélange plusieurs règles distinctes est moins précis pour matcher une question ciblée.
- Perte de la traçabilité fine : impossible de dire « l'article X dit exactement Y » si le chunk envoyé au LLM fusionne dix articles — or la traçabilité est le critère n°1 du projet.

**Choix retenu : approche hybride, article comme unité de base + section en métadonnée**

- Chunk = un article (unité de recherche et de citation).
- Chaque chunk porte en métadonnée : numéro d'article, section thématique, titre de la section. Cela permet de regrouper/filtrer par thème sans sacrifier la précision de citation.
- Pour les articles très longs, on applique un découpage secondaire récursif à l'intérieur de l'article (overlap 10-20 %), en gardant le même numéro d'article sur tous les sous-chunks.
- Pour les articles très courts ou peu informatifs seuls, on prévoit d'envoyer au LLM le contexte de section en complément si besoin — logique proche du pattern parent-enfant (petits chunks indexés pour la recherche, contexte plus large fourni au LLM).

Ce choix est cohérent avec la contrainte de traçabilité (voir Q2) : le numéro d'article doit être fiable et non ambigu, ce que le chunk-par-article garantit mieux qu'un chunk-par-section.

**Seuil de découpage secondaire : aucun seuil n'est imposé par le sujet ni le cours — c'est un choix d'équipe, calibré sur le corpus réel.**

Sur les 812 articles du corpus LEGI (jalon 1), la taille moyenne est de ~653 caractères, mais 3 articles dépassent largement cette moyenne : `L1233-58` (5553 caractères), `L2312-26` (4569 caractères), `L1233-68` (3226 caractères). On retient un seuil de **1500 caractères** (~300-400 tokens en français) : il laisse 809 des 812 articles intacts en un seul chunk, et ne déclenche le découpage secondaire que pour ces 3 cas réels identifiés. Détail d'implémentation : [docs/jalon2_jalon3_indexation_retrieval.md](docs/jalon2_jalon3_indexation_retrieval.md).

### 2. Traçabilité

**Où stocker le numéro d'article : dans les métadonnées, en priorité.**

| Emplacement | Rôle |
|---|---|
| **Métadonnées** (`article: "L1237-11"`) | Source de vérité, structurée, fiable — c'est elle qui sert à citer, vérifier, filtrer |
| Texte embeddé | Le numéro peut aussi apparaître en tête du texte du chunk (ex. « Article L1237-11 — ... »), mais uniquement comme signal additionnel pour l'embedding, jamais comme source de vérité |

Sans métadonnées, pas de traçabilité fiable : un numéro d'article mentionné seulement dans le texte libre dépend de l'interprétation du LLM, donc pas garanti exact.

**Comment garantir que le LLM cite correctement (et n'invente pas) :**

1. **Dans le prompt** : chaque chunk envoyé au LLM est numéroté et étiqueté avec sa métadonnée (`[Source 1 — Article L1237-11] <texte>`). Consigne stricte : ne citer que des numéros présents dans le contexte fourni, interdiction de toute connaissance extérieure, et obligation de répondre « je ne trouve pas cette information » si le contexte ne suffit pas.
2. **Température basse** (0 à 0.2) pour limiter l'improvisation.
3. **Vérification côté code (filet de sécurité)** : après la génération, on extrait les numéros d'articles cités dans la réponse (regex) et on vérifie qu'ils appartiennent bien à l'ensemble des métadonnées des chunks récupérés. Si un article cité n'existe pas dans le contexte fourni, c'est un signal d'hallucination détectable automatiquement — indépendamment du bon vouloir du prompt.

La combinaison métadonnées + prompt strict + vérification code est plus robuste qu'une seule de ces trois couches isolément.

### 3. Fraîcheur

**Deux mécanismes complémentaires :**

1. **Métadonnée de date sur le corpus** : à l'indexation, on enregistre une date de collecte (`corpus_date`) au niveau de la base vectorielle elle-même — pas juste dans le README. Elle est chargée avec le modèle d'embedding (même logique que le nom du modèle, stocké avec la base).
2. **Avertissement systématique dans chaque réponse** : en plus de la mention légale obligatoire, on ajoute une ligne fixe type « Informations à jour au [date du corpus]. Le droit du travail évolue : vérifiez les éventuelles modifications récentes. » — générée par le code qui assemble la réponse (pas laissée à la discrétion du LLM), pour garantir qu'elle apparaît dans 100 % des réponses.

### 4. Réponses conditionnelles

**Mécanisme retenu : clarification active, pas juste réserve générale.**

L'objectif est que l'assistant se comporte comme un agent conversationnel, pas un simple système one-shot : quand la réponse dépend d'une information manquante ou que la question est ambiguë, il pose une question de clarification plutôt que de répondre à l'aveugle.

1. **Détection dans le prompt système** : consigne au LLM — si le contexte récupéré montre que la réponse dépend d'une condition non précisée par l'utilisateur (effectif, convention collective) OU si la question est trop vague/ambiguë pour être traitée avec confiance, ne pas répondre directement : poser une question de clarification précise et courte (ex. « Combien de salariés compte votre entreprise ? » ou « Parlez-vous d'un CDI ou d'un CDD ? »).
2. **Boucle conversationnelle** : la CLI doit supporter ce va-et-vient — afficher la question de clarification, lire la réponse de l'utilisateur, puis reformuler une requête complète (question initiale + précision) avant de relancer le retrieval. Cela nécessite de garder un historique des échanges (contrairement à un simple prompt one-shot), ce qui rend l'amélioration « historique de conversation » (jalon 6) indispensable dès la conception plutôt qu'un simple bonus.
3. **Filet de sécurité** : si après clarification l'information reste absente du corpus, retour au refus standard (« je ne trouve pas cette information dans ma base »).
4. **Réserve en complément, pas en remplacement** : même après clarification, si une incertitude demeure (ex. convention collective non couverte par le corpus), la réponse le signale explicitement.

### 5. La frontière du conseil juridique

**Distinction basée sur la nature de la réponse attendue par le corpus, pas sur des mots-clés.**

1. **Question factuelle** (répond directement à ce que dit un article) : le retrieval remonte un ou plusieurs articles qui énoncent une règle claire et applicable telle quelle → le système répond normalement, avec citation.
2. **Question d'interprétation/qualification** (demande d'appliquer la loi à une situation personnelle, ex. « mon licenciement est-il abusif ? », « ma situation relève-t-elle du harcèlement ? ») : même si des articles pertinents remontent (ex. les motifs de licenciement), aucun article ne peut trancher seul si le cas est abusif ou non — c'est une qualification juridique qui dépend des faits.
   - **Signal de détection** : dans le prompt système, on caractérise ce type de question par la présence de termes évaluatifs/subjectifs appliqués à une situation personnelle (« abusif », « est-ce que j'ai le droit de... dans mon cas », « suis-je victime de... ») plutôt qu'une demande de règle générale.
   - **Comportement imposé** : le système présente les articles pertinents à titre informatif (ex. les motifs légaux de licenciement), mais refuse explicitement de qualifier la situation personnelle de l'utilisateur, et renvoie vers l'avocat/inspection du travail — un renforcement de l'avertissement juridique standard, pas un cas à part.

Cette distinction est gérée dans le prompt système (instruction explicite de ne jamais trancher une qualification factuelle/personnelle), pas par une détection séparée en amont — pour rester simple et cohérent avec le reste du pipeline.

### Synthèse — nos 3 choix structurants

| # | Choix | Pourquoi | Impact code |
|---|---|---|---|
| 1 | Chunking par article, section en métadonnée | Le numéro d'article est l'info la plus précieuse à citer ; un chunk par article garantit une citation précise sans dilution vectorielle | Jalon 2 (indexation) : chaque document = 1 article, pas de fusion |
| 2 | Traçabilité en 3 couches : métadonnées (source de vérité) + prompt strict (citer uniquement le contexte fourni) + vérification code post-génération (extraction des numéros cités, comparés aux métadonnées) | Une seule couche (juste le prompt) ne suffit pas à garantir zéro hallucination d'article | Jalon 4 (génération) : ajouter une étape de vérification après l'appel LLM, pas juste un prompt bien écrit |
| 3 | Agent conversationnel avec clarification active plutôt qu'un système one-shot | Beaucoup de réponses dépendent d'infos non données (taille entreprise, convention collective) ; mieux vaut demander que supposer | Jalon 5 (interface) : la boucle CLI doit gérer un historique multi-tours. Ça rend l'amélioration « historique de conversation » du jalon 6 quasi obligatoire, pas optionnelle |
