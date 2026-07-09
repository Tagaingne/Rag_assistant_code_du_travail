# Assistant Code du travail (RAG)

Assistant juridique répondant à des questions sur le droit du travail français, avec citation systématique des articles du Code du travail. Projet réalisé dans le cadre du M2 MD5 — Data & IA.

> Cet assistant ne fournit pas de conseil juridique. Consultez un avocat ou l'inspection du travail pour votre situation personnelle.

## Sommaire

- [Installation](#installation)
- [Jalon 1 — Préparation des données (LEGI)](#jalon-1--préparation-des-données-legi)
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

## Jalon 1 — Préparation des données (LEGI)

### Source des données

Le corpus du projet provient de la base LEGI disponible sur data.gouv.fr. Cette base contient les textes juridiques francais, dont les codes, au format XML.

Pour le jalon 1, l'option retenue est l'option B du sujet : utiliser les fichiers XML de la base LEGI et les parser avec la bibliotheque standard Python, notamment `xml.etree.ElementTree`.

Les fichiers XML utiles extraits depuis la base LEGI doivent etre places dans le dossier suivant :

```text
data/raw/legi/
```

Le projet ne telecharge pas automatiquement l'archive LEGI complete, car elle peut etre volumineuse. Si l'archive complete a deja ete telechargee, le script `src/data/extract_code_travail_from_archive.py` permet de la lire directement sans tout decompresser et d'extraire uniquement les XML utiles au jalon 1 dans `data/raw/legi/`.

### Pourquoi l'option B

L'option B est retenue parce qu'elle donne un corpus officiel, public et structure sans dependre d'une API au moment de l'indexation. Les fichiers XML de la base LEGI permettent d'extraire les articles avec leurs metadonnees et de garder une trace du fichier source.

Cette option est un bon compromis pour le projet : elle est plus robuste qu'un corpus copie manuellement, mais elle reste developpable avec la bibliotheque standard Python.

### Role des dossiers

`data/raw/legi/` contient les fichiers XML bruts issus de la base LEGI. Ces fichiers peuvent etre volumineux et ne doivent pas etre ajoutes au depot Git.

`data/processed/` contient les fichiers propres generes par les scripts, notamment :

```text
data/processed/corpus_legi_clean.json
```

### Scripts disponibles

`src/data/extract_code_travail_from_archive.py` lit une archive `.tar.gz` LEGI avec `tarfile`, parcourt les entrees sans extraction globale, repere les XML du Code du travail (`LEGITEXT000006072050`) et extrait seulement les articles des plages demandees dans `data/raw/legi/`.

`src/data/explore_legi_xml.py` parcourt recursivement `data/raw/legi/`, lit les fichiers `.xml`, compte les balises rencontrees et affiche quelques exemples de texte. Il sert a comprendre la structure LEGI avant l'extraction.

`src/data/extract_legi_corpus.py` parcourt recursivement `data/raw/legi/`, extrait les articles correspondant aux themes demandes du Code du travail, nettoie le texte et genere un JSON homogene.

### Commandes

Extraire les XML utiles depuis l'archive complete sans tout decompresser :

```bash
python src/data/extract_code_travail_from_archive.py "C:/Users/33785/Downloads/Freemium_legi_global_20250713-140000.tar.gz"
```

Explorer les XML :

```bash
python src/data/explore_legi_xml.py
```

Generer le corpus propre :

```bash
python src/data/extract_legi_corpus.py
```

### Themes filtres

Le script filtre les articles par plages pour couvrir les themes du sujet :

- Duree du travail et heures supplementaires : `L3121-1` a `L3121-36`
- Conges payes : `L3141-1` a `L3141-32`
- Contrat de travail CDI/CDD : `L1221-1` a `L1248-11`
- Licenciement : `L1231-1` a `L1237-20`
- Rupture conventionnelle : `L1237-11` a `L1237-19`
- Salaire minimum SMIC : `L3231-1` a `L3232-9`
- Representation du personnel : `L2311-1` a `L2316-26`
- Harcelement et discrimination : `L1152-1` a `L1155-2`

Les plages specifiques sont testees avant la plage plus large du contrat de travail. La rupture conventionnelle est aussi testee avant la plage plus large du licenciement afin de conserver ce theme specifique.

### Fraicheur juridique des donnees

Le Code du travail evolue dans le temps. Un meme article peut donc exister sous plusieurs versions successives dans LEGI. Pour eviter de repondre avec une version obsolescente, le pipeline conserve uniquement la version juridiquement en vigueur de chaque article.

La selection repose sur les metadonnees LEGI :

- `ETAT` doit etre egal a `VIGUEUR` ;
- `DATE_DEBUT` doit etre anterieure ou egale a la date d'extraction ;
- `DATE_FIN` doit etre posterieure a la date d'extraction, generalement `2999-01-01` pour une version sans fin connue ;
- si plusieurs versions courantes existent pour le meme numero d'article, la version avec la date d'entree en vigueur la plus recente est conservee.

Les anciennes versions sont ignorees dans le corpus final. Elles ne sont pas stockees dans un historique separe pour le jalon 1.

### Champs du JSON final

Chaque document extrait a la structure suivante :

```json
{
  "id": "legi_L3121-1",
  "article": "L3121-1",
  "theme": "Duree du travail et heures supplementaires",
  "title": "Article L3121-1",
  "text": "Texte nettoye de l'article...",
  "content": "Article L3121-1\nTheme : ...\nTitre : ...\nEtat juridique : VIGUEUR\nDate d'entree en vigueur : ...\nDate de fin de validite : ...\nDate de derniere modification : ...\nTexte : ...",
  "legi_id": "LEGIARTI000033020517",
  "etat": "VIGUEUR",
  "date_debut": "2016-08-10",
  "date_fin": "2999-01-01",
  "date_derniere_modification": "2016-08-08",
  "date_derniere_modification_source": "LIEN typelien=MODIFIE",
  "source": "LEGI data.gouv.fr",
  "source_file": "data/raw/legi/...",
  "date_extraction": "YYYY-MM-DD"
}
```

Le champ `content` est prepare pour la suite du projet : il rassemble l'article, le theme, le titre, les metadonnees de validite juridique et le texte dans une seule chaine qui pourra etre indexee plus tard.

### Controles qualite

Le script verifie :

- aucun id vide ;
- aucun numero d'article vide ;
- aucun texte vide ;
- aucun etat juridique vide ;
- aucune date d'entree en vigueur vide ;
- aucune date de fin de validite vide ;
- aucune version non en vigueur dans le corpus final ;
- aucun doublon d'article ;
- au moins 5 themes extraits ;
- affichage du nombre total d'articles ;
- affichage du nombre d'articles par theme ;
- affichage de 5 exemples nettoyes avec leurs dates juridiques.

Sur l'archive `Freemium_legi_global_20250713-140000.tar.gz`, l'extraction ciblee a parcouru 5 253 903 entrees, analyse 41 815 XML du Code du travail et extrait 864 versions candidates. Apres filtrage des versions non en vigueur, le corpus propre genere contient 812 documents repartis sur 8 themes. Les 52 versions non en vigueur detectees sont ignorees.

### Limites actuelles

Les XML bruts dans `data/raw/legi/` restent ignores par Git afin d'eviter de versionner les donnees sources volumineuses. Le fichier propre `data/processed/corpus_legi_clean.json` est versionne car sa taille reste raisonnable.

La lecture d'un `.tar.gz` est sequentielle : meme sans decompresser toute l'archive, le script doit parcourir les entrees de l'archive pour trouver les XML utiles.

Le jalon 1 ne fait pas encore de chunking avance, pas d'embeddings, pas de base vectorielle, pas de recherche et pas d'appel LLM. LangChain et LlamaIndex ne sont pas utilises.

## Utilisation

```bash
# 1. Construire et persister la base vectorielle (à lancer une seule fois)
python index.py

# 2. Interroger l'assistant
python query.py
```

## Choix techniques

- **Source du corpus** : option B — base LEGI (data.gouv.fr), voir la section [Jalon 1](#jalon-1--préparation-des-données-legi) ci-dessus.
- **Stratégie de chunking** : par article, section en métadonnée — voir [Q1](#1-granularité-du-chunking) ci-dessous.
- **Modèle d'embedding, base vectorielle, modèle Groq** : à compléter.

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
- Pour les articles très longs (dépassant une taille cible, ex. ~500 tokens), on applique un découpage secondaire récursif à l'intérieur de l'article (overlap 10-20 %), en gardant le même numéro d'article sur tous les sous-chunks.
- Pour les articles très courts ou peu informatifs seuls, on prévoit d'envoyer au LLM le contexte de section en complément si besoin — logique proche du pattern parent-enfant (petits chunks indexés pour la recherche, contexte plus large fourni au LLM).

Ce choix est cohérent avec la contrainte de traçabilité (voir Q2) : le numéro d'article doit être fiable et non ambigu, ce que le chunk-par-article garantit mieux qu'un chunk-par-section.

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

1. **Métadonnée de date sur le corpus** : à l'indexation, on enregistre une date de collecte (ex. `corpus_date: "2026-07-09"`) au niveau de la base vectorielle elle-même — pas juste dans le README. Elle est chargée avec le modèle d'embedding (même logique que le nom du modèle, stocké avec la base).
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
