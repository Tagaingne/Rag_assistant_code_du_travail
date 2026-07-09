# Fix — Integration jalons 2/3 (chunking/indexation/retrieval) et 4/5 (generation/interface)

Apres la fusion de `feature/generation-interface` dans `dev`, le pipeline complet ne fonctionnait plus. Cette branche (`fix/integration-jalon2-4`) corrige les problemes d'integration entre les deux parties du projet, developpees independamment.

## Problemes trouves et corriges

1. **`src/config.py` ecrase** : le merge avait remplace le fichier au lieu de fusionner les deux jeux de constantes. Toutes les constantes du jalon 2/3 (`CORPUS_FILE`, `COLLECTION_NAME`, `EMBEDDING_MODEL_NAME`, `VECTOR_STORE_DIR`, `ARTICLE_CHUNK_SIZE_THRESHOLD`, `CHUNK_OVERLAP_RATIO`, `DEFAULT_TOP_K`) avaient disparu. `index.py` et `evaluate_retrieval.py` plantaient au demarrage (`ImportError`). Corrige en reconciliant un seul fichier de config couvrant tout le pipeline.

2. **`config.py` exigeait `GROQ_API_KEY` des l'import**, meme pour du code qui n'appelle jamais Groq (chunking, indexation). Deplace : la verification se fait maintenant dans `Agent.__init__` (`MissingGroqApiKey`), la ou elle a vraiment un sens.

3. **`vector_db.py` manquant** : `main.py` et les agents de generation dependaient d'un module `VectorDB` jamais cree/commite. Cree `src/vector_db.py`, un adaptateur qui reutilise les classes existantes du jalon 2/3 (`VectorStore`, `EmbeddingModel`, `Retriever`) plutot que de reimplementer la recherche vectorielle.

4. **Incompatibilite de schema** : le code de generation attendait une cle de metadonnee `"section"`, alors que le champ reellement persiste par le jalon 2 s'appelle `theme`. Uniformise sur `theme` partout (agents, `main.py`, tests) plutot que de faire un mapping silencieux dans l'adaptateur.

5. **Bug : `moderator_agent.py` utilisait `LLM_MODEL`** (le modele de generation, plus gros) **au lieu de `MODERATOR_MODEL`** (modele dedie, plus leger) pour la moderation. `MODERATOR_MODEL` etait defini mais jamais utilise. Corrige.

6. **Deux styles d'import incompatibles coexistaient** : le jalon 2/3 utilisait des imports de package (`from src.chunking.article_chunker import ...`), le jalon 4/5 utilisait `sys.path.insert(...)` puis des imports plats (`from manager_agent import ...`). Uniformise sur les imports de package partout ; les scripts se lancent depuis la racine du depot (`python main.py`, `python index.py`, `python -m tests.test_generation`).

7. **`main.py` duplique** (present a la racine et dans `src/main.py`, quasi identiques). Le doublon `src/main.py` est supprime, `main.py` reste le point d'entree unique a la racine.

8. **`.env.example` incoherent avec le code** : documentait des modeles Groq (`openai/gpt-oss-*`) differents de ceux reellement codes en dur (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`). Aligne sur les valeurs confirmees par l'equipe, et les deux modeles sont maintenant lus depuis `.env` (comme `EMBEDDING_MODEL`) au lieu d'etre figes dans le code.

## Verification effectuee

Pipeline teste de bout en bout avec une vraie cle Groq (fournie temporairement pour le test, jamais commitee) :

- `python index.py` : reindexation propre, 877 chunks.
- `python evaluate_retrieval.py` : 5/5 (jalon 3 toujours valide apres reconciliation du config).
- `python -m tests.test_generation` : moderation (legitime/injection) et generation RAG (citation d'article, refus hors corpus) toutes correctes.
- `python main.py` : boucle interactive complete testee (question -> reponse -> sources -> avertissement -> sortie propre).

Aucune reference residuelle a l'ancienne nomenclature (`VECTOR_DB_PATH`, `TOP_K`, `"section"`) trouvee apres correction.
