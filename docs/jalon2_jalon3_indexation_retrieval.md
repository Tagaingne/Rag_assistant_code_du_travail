# Jalon 2 et 3 — Chunking, indexation, validation du retrieval

## Architecture du code

Le code est organise en petites classes a responsabilite unique, composees par des scripts d'entree (`index.py`, `evaluate_retrieval.py`) qui jouent le role d'orchestrateur.

```text
src/
  config.py                          Constantes centralisees (seuils, chemins, noms)
  chunking/
    chunk.py                         Chunk (dataclass)
    article_chunker.py               ArticleChunker : un article -> un ou plusieurs Chunk
  embedding/
    embedding_model.py               EmbeddingModel : wrapper sentence-transformers
  indexing/
    corpus_loader.py                 CorpusLoader : lit data/processed/corpus_legi_clean.json
    vector_store.py                  VectorStore : seule classe qui parle a ChromaDB
    index_builder.py                 IndexBuilder : orchestrateur (charge, chunk, embed, persiste)
  retrieval/
    search_result.py                 SearchResult (dataclass)
    retriever.py                     Retriever : encode une question, interroge le VectorStore
    test_question.py                 TestQuestion (dataclass)
    evaluation_result.py             EvaluationResult (dataclass)
    retrieval_evaluator.py           RetrievalEvaluator : verifie le retrieval sur des questions connues
    exceptions.py                    EmbeddingModelMismatch

index.py                             Script d'indexation (jalon 2)
evaluate_retrieval.py                Script de validation du retrieval (jalon 3)
```

Chaque classe fait une seule chose : `ArticleChunker` ne s'occupe que du decoupage, `EmbeddingModel` que de l'encodage, `VectorStore` que de la persistance ChromaDB, `Retriever` que de la recherche. `IndexBuilder` et `evaluate_retrieval.py` orchestrent ces briques sans connaitre leurs details internes.

## Jalon 2 — Chunking et indexation

### Strategie de chunking (implementation de la reponse Q1 du README)

`ArticleChunker.chunk_article(document)` :

1. Si le texte de l'article ne depasse pas `ARTICLE_CHUNK_SIZE_THRESHOLD` (1500 caracteres, voir `src/config.py`), l'article devient un seul `Chunk`.
2. Sinon, le texte est decoupe par phrases (`_split_into_sentences`, regex sur `.`/`!`/`?`) et regroupe en parts qui ne depassent pas le seuil (`_split_into_parts_with_overlap`), avec un chevauchement de ~15 % de phrases entre deux parts consecutives (`_carry_overlap`). Ce decoupage ne coupe jamais une phrase en deux.
3. Chaque part devient un `Chunk` avec le meme `article`, `theme`, `title`, `source` que le document d'origine, et un `chunk_index`/`chunk_count` pour tracer sa position si l'article a ete redecoupe.

Sur le corpus de 812 articles, cette strategie produit **877 chunks** (47 articles redecoupes en 120 chunks au total, le reste en un seul chunk chacun) : la grande majorite des articles restent un seul chunk, une poignee d'articles longs (ex. `L1233-58`, 5553 caracteres) sont redecoupes en plusieurs parts.

**Bug corrige lors du controle qualite du jalon 2** : la regex initiale de decoupage en phrases (`(?<=[.!?])\s+`) coupait a tort apres les abreviations de reference legale comme `"L. 1233-63"` (le point apres `L` etait pris pour une fin de phrase), produisant des chunks qui commencaient en plein milieu d'une enumeration d'articles (ex. `"1233-63, relatifs a la nature..."` au lieu de `"L'employeur, l'administrateur..."`). Corrige en exigeant qu'une lettre majuscule suive la ponctuation pour valider une coupure de phrase (`(?<=[.!?])\s+(?=[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ])`) : comme les references legales sont toujours suivies d'un chiffre (`"L. 1233-63"`), elles ne declenchent plus de coupure. Verifie manuellement sur plusieurs articles redecoupes (`L1233-58`, `L2312-26`, `L3141-24`, `L1235-3`) apres correction : plus aucune coupure en milieu de phrase.

### embed_text vs text

Chaque `Chunk` porte deux champs texte :

- `text` : le texte brut de l'article (ou de la part), utilise pour l'affichage/la citation.
- `embed_text` : `"{theme}. {text}"`, utilise uniquement pour le calcul de l'embedding.

Ce choix vient d'un constat empirique du jalon 3 (voir plus bas) : de nombreux articles du Code du travail partagent un vocabulaire juridique tres proche (« contrat de travail », « employeur », « salarie »...). Prefixer le theme donne au modele d'embedding un signal thematique explicite que le texte brut de l'article n'a pas toujours.

### Persistance

`VectorStore` (ChromaDB, client persistant sur `data/vector_store/`) stocke, pour chaque chunk : le texte (`documents`), les metadonnees (`article`, `theme`, `title`, `source`, `chunk_index`, `chunk_count`), et un embedding normalise.

La collection elle-meme porte deux metadonnees : `embedding_model` (nom exact du modele utilise) et `corpus_date` (date d'extraction la plus recente parmi les documents indexes). `Retriever` verifie au demarrage que le modele d'embedding utilise pour la recherche correspond a celui stocke avec l'index (`EmbeddingModelMismatch` sinon).

`index.py` reconstruit systematiquement la collection (`VectorStore.reset_collection`) : c'est le script d'indexation, concu pour etre relance volontairement apres une mise a jour du corpus. `evaluate_retrieval.py` (et plus tard le script d'interrogation) ne font jamais cette operation : ils chargent la collection existante via `VectorStore.get_collection`, qui leve une erreur explicite si elle n'existe pas encore.

### Modele d'embedding et base vectorielle retenus

- **Modele d'embedding** : `intfloat/multilingual-e5-base` (sentence-transformers), choisi apres comparaison empirique sur le jeu de questions du jalon 3 (voir Resultat ci-dessous). Doit rester identique sur toutes les branches de l'equipe (voir `.env.example`, variable `EMBEDDING_MODEL`).
- **Base vectorielle** : ChromaDB, persistance locale integree, gestion native des metadonnees.

Ce modele est concu pour le retrieval asymetrique (question courte / passage long), contrairement aux modeles `paraphrase-multilingual-*` ou `distiluse-*` concus pour la similarite entre phrases comparables. Il impose un prefixe different sur les textes indexes (`"passage: ..."`) et sur les questions (`"query: ..."`), gere dans `EmbeddingModel.encode_passages` / `EmbeddingModel.encode_query`.

**Historique des essais** (voir Resultat ci-dessous) : `paraphrase-multilingual-MiniLM-L12-v2` (2/5) puis `distiluse-base-multilingual-cased-v2` (4/5, modele initialement convenu par l'equipe) ont ete abandonnes au profit de `multilingual-e5-base` (5/5). **Ce changement doit etre repercute sur les autres branches** (notamment celle qui gere la generation) puisque le modele d'embedding doit rester identique partout — sinon la recherche casse silencieusement.

## Jalon 3 — Validation du retrieval

### Jeu de questions de test

Cinq questions couvrant cinq themes differents, avec l'article attendu identifie a la main dans le corpus :

| Question | Article attendu |
|---|---|
| Qu'est-ce qu'une rupture conventionnelle du contrat de travail ? | L1237-11 |
| Qu'est-ce que le harcelement moral au travail ? | L1152-1 |
| Quel est le role du salaire minimum de croissance (SMIC) ? | L3231-2 |
| Quelle est la duree legale du travail par semaine ? | L3121-27 |
| Quelle est la periode de prise des conges payes ? | L3141-13 |

### Resultat (top-5)

**Essai 1 — `paraphrase-multilingual-MiniLM-L12-v2` (abandonne) : 2 questions sur 5.** Harcelement moral et SMIC trouves, les trois autres echouent : l'article attendu n'apparaissait meme pas dans le top-15 pour la rupture conventionnelle et les conges payes ; il apparaissait en position 15/15 pour la duree legale du travail.

Diagnostic sur cet essai : le probleme n'etait ni le chunking (aucune coupure en pleine phrase, verifie manuellement) ni la qualite du corpus (controle qualite du jalon 1 sans anomalie), mais une faible discrimination du modele sur des articles juridiques lexicalement proches. Exemple : `L1237-11` (rupture conventionnelle) obtenait une similarite de 0.68-0.72 avec la question associee, contre 0.77-0.80 pour des articles voisins portant sur d'autres formes de rupture de contrat, qui partagent le meme vocabulaire dominant (« rupture », « contrat de travail »).

**Essai 2 — `distiluse-base-multilingual-cased-v2` : 4 questions sur 5.** Rupture conventionnelle, harcelement moral, SMIC et duree legale du travail sont tous retrouves, certains en premiere position. Seule la question sur la periode de prise des conges payes echoue encore (`L3141-13` non retrouve ; le retrieval remonte `L3141-1`, article voisin sur le meme theme mais un contenu different).

**Essai 3 — `intfloat/multilingual-e5-base` (modele retenu) : 5 questions sur 5.** Toutes les questions retrouvent l'article attendu, 4 sur 5 en premiere position. Ce modele, concu specifiquement pour le retrieval asymetrique question/passage (plutot que pour la similarite generale entre phrases), discrimine correctement les articles juridiques proches qui posaient probleme aux deux essais precedents.

### Consequence pour le jalon 6

Avec 5/5, l'urgence du diagnostic initial (justifiant la recherche hybride) est nettement reduite. La **recherche hybride** reste une amelioration valable en general (BM25 rattrape les correspondances exactes de numeros d'article, ex. « que dit L3121-1 ? »), mais elle n'est plus indispensable pour corriger un echec de retrieval identifie sur ce jeu de test. La **decomposition** (exigee a l'oral, voir `docs/jalon6_ameliorations.md`) reste la priorite.

Ces resultats n'ont pas ete corriges artificiellement (pas de reglage cible sur ces 5 questions, le changement de modele est une amelioration generale valable pour toute question) : ils sont conserves tels quels, comme preuve du diagnostic demande par le jalon 3 avant de brancher le LLM.
