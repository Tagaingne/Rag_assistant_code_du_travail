# Jalon 6 — Ameliorations prevues

## Decomposition de la question — implementee

Non listee dans les 6 options ecrites du sujet (score de confiance, reformulation, mode comparaison, historique de conversation, recherche hybride, agent moderateur), mais **exigee a l'oral par l'enseignant** en complement du sujet ecrit.

### Mecanisme

- **`DecompositionAgent`** (`src/decomposition_agent.py`) : un agent Groq dedie (meme pattern que `ModeratorAgent`), qui decompose la question en 2 a 4 sous-questions atomiques via un appel LLM avec sortie JSON forcee (`prompts/decomposition_prompt_system.txt`). Si la question porte deja sur une seule idee, le prompt renvoie une unique sous-question (pas de decoupage force).
- **`RagAgent`** (`src/rag_agent.py`) compose maintenant ce `DecompositionAgent`. `build_context` :
  1. decompose la question ;
  2. recherche separement dans `VectorDB` pour chaque sous-question (`_retrieve_for_sub_questions`) ;
  3. deduplique les chunks obtenus par numero d'article ;
  4. trie les candidats par score de similarite (`distance`, ajoute aux metadonnees renvoyees par `VectorDB.retrieve`) ;
  5. plafonne le contexte final a `MAX_CONTEXT_CHUNKS` (8, voir `src/config.py`) pour eviter de noyer le LLM si plusieurs sous-questions remontent beaucoup de chunks.

### Pourquoi

Une question qui melange plusieurs idees donne un vecteur dilue, moins precis pour le retrieval (cf. README, Q1). La decomposition evite ce piege et couvre naturellement le cas des questions comparatives (« quelle difference entre un licenciement et une rupture conventionnelle ? »), ce qui recoupe l'option ecrite « mode comparaison ».

### Verification

Teste avec de vrais appels Groq :
- Question comparative (« licenciement vs rupture conventionnelle ») → decomposee en 2 sous-questions, 8 chunks agreges couvrant les deux themes concernes, reponse citant des articles des deux cotes.
- Question simple (« combien de jours de conges par an ? ») → une seule sous-question (pas de decoupage inutile), reponse normale avec citation.
- Suite de tests existante (`tests/test_generation.py`) toujours verte apres integration.

### Combinaison avec les autres choix

S'articule avec l'« historique de conversation », deja rendu quasi indispensable par le choix Q4 du README (agent conversationnel avec clarification active) — les deux mecanismes partagent la meme logique de reformulation de requete avant recherche. L'historique de conversation reste a implementer si le temps le permet.

## Recherche hybride (evaluee, priorite revue apres le jalon 3)

L'evaluation du retrieval (jalon 3, voir `docs/jalon2_jalon3_indexation_retrieval.md`) a compare 3 modeles d'embedding sur 5 questions de test : `paraphrase-multilingual-MiniLM-L12-v2` (2/5), `distiluse-base-multilingual-cased-v2` (4/5), puis `intfloat/multilingual-e5-base` (5/5, modele retenu). Le dernier modele, concu pour le retrieval, resout tous les cas d'echec observes precedemment.

- **Mecanisme** (si implemente malgre tout) : combiner un score lexical (BM25 sur le texte des chunks, ou correspondance directe sur un numero d'article du type `L3121-1`) avec le score vectoriel existant, fusionnes par une methode type RRF (Reciprocal Rank Fusion).
- **Pourquoi ce n'est plus la priorite** : le probleme empirique qui justifiait cette amelioration (echecs de retrieval sur le jeu de test) a ete resolu par un meilleur choix de modele d'embedding, pas besoin d'ajouter une couche lexicale pour ce cas precis.
- **Interet residuel** : reste utile pour un cas que le vectoriel seul ne couvre pas structurellement : une question qui cite un numero d'article exact (« que dit L3121-1 ? »), ou tape un numero d'article mal orthographie/segmente. Pourrait redevenir pertinent si de nouvelles questions de test le justifient.
- **Statut** : degrade de « priorite empirique » a « amelioration secondaire, a envisager si le temps le permet ». La **decomposition** (exigee a l'oral) reste la priorite du jalon 6.
