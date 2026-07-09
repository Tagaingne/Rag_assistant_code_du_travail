# Jalon 6 — Ameliorations prevues

## Agent formateur de question — implemente (decomposition + nettoyage + HyDE)

Non listees dans les 6 options ecrites du sujet (score de confiance, reformulation, mode comparaison, historique de conversation, recherche hybride, agent moderateur), mais **exigees a l'oral par l'enseignant** en complement du sujet ecrit (decomposition), et etendues a partir d'un schema d'architecture fourni par l'equipe (nettoyage des mots parasites + HyDE). La partie "agent recuperateur de reference -> API Legifrance" du schema n'est volontairement pas implementee (hors scope pour l'instant).

### Mecanisme

Trois classes a responsabilite unique, composees par un orchestrateur, elles-memes composees dans `RagAgent` :

- **`QuestionCleaner`** (`src/question_cleaner.py`) : nettoyage par regex, sans appel LLM (rapide, gratuit). Retire les formules de politesse et tournures ("bonjour", "pourriez-vous", "s'il vous plait"...) qui diluent le vecteur d'embedding sans apporter de signal juridique.
- **`DecompositionAgent`** (`src/decomposition_agent.py`) : agent Groq (meme pattern que `ModeratorAgent`) qui decompose la question nettoyee en 2 a 4 sous-questions atomiques, sortie JSON forcee (`prompts/decomposition_prompt_system.txt`). Une question deja simple reste une unique sous-question (pas de decoupage force).
- **`HydeAgent`** (`src/hyde_agent.py`) : agent Groq qui genere, pour chaque sous-question, un court paragraphe de reponse hypothetique dans le style du Code du travail (`prompts/hyde_prompt_system.txt`). Les chunks indexes sont des reponses (articles de loi), pas des questions : embedder une reponse hypothetique matche mieux qu'embedder la question brute.
- **`QuestionFormatterAgent`** (`src/question_formatter_agent.py`) : orchestrateur qui enchaine les trois etapes (`clean` -> `decompose_question` -> `generate_hypothetical_answer` par sous-question) et renvoie la liste des requetes de recherche pretes a l'emploi.

`RagAgent.build_context` :
1. appelle `QuestionFormatterAgent.format_question(question)` -> liste de requetes de recherche (une par sous-question, deja au format HyDE) ;
2. recherche separement dans `VectorDB` pour chaque requete (`_retrieve_for_queries`) ;
3. deduplique les chunks obtenus par numero d'article ;
4. trie les candidats par score de similarite (`distance`, ajoute aux metadonnees renvoyees par `VectorDB.retrieve`) ;
5. plafonne le contexte final a `MAX_CONTEXT_CHUNKS` (8, voir `src/config.py`) pour eviter de noyer le LLM si plusieurs sous-questions remontent beaucoup de chunks.

### Pourquoi

- **Nettoyage** : une question polie/familiere ("Bonjour, pourriez-vous m'expliquer...") ajoute du bruit lexical a l'embedding sans rapport avec le besoin juridique.
- **Decomposition** : une question qui melange plusieurs idees donne un vecteur dilue, moins precis pour le retrieval (cf. README, Q1). Couvre naturellement le cas des questions comparatives (« quelle difference entre un licenciement et une rupture conventionnelle ? »), ce qui recoupe l'option ecrite « mode comparaison ».
- **HyDE** : les chunks indexes sont formules comme des articles de loi (reponses), pas comme des questions ; chercher avec une reponse hypothetique plutot qu'avec la question brute reduit cet ecart de forme.

### Verification

Teste avec de vrais appels Groq :
- Question polie et comparative (« Bonjour, pourriez-vous m'expliquer la difference entre un licenciement et une rupture conventionnelle s'il vous plait ? ») → nettoyee, decomposee en 2 sous-questions, HyDE genere une reponse hypothetique par sous-question, 8 chunks agreges couvrant les deux themes (5 Licenciement + 3 Rupture conventionnelle), reponse finale citant des articles des deux cotes.
- Question simple (« combien de jours de conges par an ? ») → une seule sous-question (pas de decoupage inutile), reponse normale avec citation.
- Suite de tests existante (`tests/test_generation.py`) toujours verte apres integration.

### Combinaison avec les autres choix

S'articule avec l'« historique de conversation », deja rendu quasi indispensable par le choix Q4 du README (agent conversationnel avec clarification active) — les deux mecanismes partagent la meme logique de reformulation de requete avant recherche. L'historique de conversation reste a implementer si le temps le permet.

### Cout

Chaque question declenche maintenant jusqu'a : 1 moderation + 1 decomposition + 1 HyDE par sous-question (jusqu'a 4) + 1 generation finale = jusqu'a 7 appels LLM. Plus lent et plus couteux qu'un pipeline a un seul appel, mais chaque etape ameliore ce qui est cherche, pas seulement ce qui est genere (cf. cours, section 07).

## Recherche hybride (evaluee, priorite revue apres le jalon 3)

L'evaluation du retrieval (jalon 3, voir `docs/jalon2_jalon3_indexation_retrieval.md`) a compare 3 modeles d'embedding sur 5 questions de test : `paraphrase-multilingual-MiniLM-L12-v2` (2/5), `distiluse-base-multilingual-cased-v2` (4/5), puis `intfloat/multilingual-e5-base` (5/5, modele retenu). Le dernier modele, concu pour le retrieval, resout tous les cas d'echec observes precedemment.

- **Mecanisme** (si implemente malgre tout) : combiner un score lexical (BM25 sur le texte des chunks, ou correspondance directe sur un numero d'article du type `L3121-1`) avec le score vectoriel existant, fusionnes par une methode type RRF (Reciprocal Rank Fusion).
- **Pourquoi ce n'est plus la priorite** : le probleme empirique qui justifiait cette amelioration (echecs de retrieval sur le jeu de test) a ete resolu par un meilleur choix de modele d'embedding, pas besoin d'ajouter une couche lexicale pour ce cas precis.
- **Interet residuel** : reste utile pour un cas que le vectoriel seul ne couvre pas structurellement : une question qui cite un numero d'article exact (« que dit L3121-1 ? »), ou tape un numero d'article mal orthographie/segmente. Pourrait redevenir pertinent si de nouvelles questions de test le justifient.
- **Statut** : degrade de « priorite empirique » a « amelioration secondaire, a envisager si le temps le permet ». La **decomposition** (exigee a l'oral) reste la priorite du jalon 6.
