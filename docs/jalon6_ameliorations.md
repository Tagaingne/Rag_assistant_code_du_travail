# Jalon 6 — Ameliorations prevues

## Agent formateur de question — implemente (decomposition + nettoyage + HyDE)

Non listees dans les 6 options ecrites du sujet (score de confiance, reformulation, mode comparaison, historique de conversation, recherche hybride, agent moderateur), mais **exigees a l'oral par l'enseignant** en complement du sujet ecrit (decomposition), et etendues a partir d'un schema d'architecture fourni par l'equipe (nettoyage des mots parasites + HyDE). La partie "agent recuperateur de reference -> API Legifrance" du schema n'est volontairement pas implementee (hors scope pour l'instant).

### Mecanisme

Trois classes a responsabilite unique, composees par un orchestrateur, elles-memes composees dans `RagAgent` :

- **`QuestionCleaner`** (`src/question_cleaner.py`) : nettoyage par regex, sans appel LLM (rapide, gratuit). Retire les formules de politesse et tournures ("bonjour", "pourriez-vous", "s'il vous plait"...) qui diluent le vecteur d'embedding sans apporter de signal juridique.
- **`DecompositionAgent`** (`src/decomposition_agent.py`) : agent Groq (meme pattern que `ModeratorAgent`) qui decompose la question nettoyee en 2 a 4 sous-questions atomiques, sortie JSON forcee (`prompts/decomposition_prompt_system.txt`). Une question deja simple reste une unique sous-question (pas de decoupage force).
- **`HydeAgent`** (`src/hyde_agent.py`) : agent Groq qui genere, pour chaque sous-question, un court paragraphe de reponse hypothetique dans le style du Code du travail (`prompts/hyde_prompt_system.txt`). Les chunks indexes sont des reponses (articles de loi), pas des questions : embedder une reponse hypothetique matche mieux qu'embedder la question brute.
- **`QuestionFormatterAgent`** (`src/question_formatter_agent.py`) : orchestrateur qui enchaine `clean` -> `decompose_question`, puis pour chaque sous-question renvoie **deux** requetes de recherche : la sous-question elle-meme et sa reponse hypothetique HyDE (voir bug HyDE/chiffres ci-dessous pour pourquoi les deux sont gardees).

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

Chaque question declenche maintenant jusqu'a : 1 moderation + 1 decomposition + 1 HyDE par sous-question (jusqu'a 4) + 1 generation finale = jusqu'a 7 appels LLM (le doublement des requetes de recherche sous-question/HyDE ne coute rien de plus : c'est de l'embedding local, pas un appel Groq). Plus lent et plus couteux qu'un pipeline a un seul appel, mais chaque etape ameliore ce qui est cherche, pas seulement ce qui est genere (cf. cours, section 07).

### Bugs trouves en test reel (interface FastAPI) et corriges

Trois bugs decouverts en utilisant l'assistant dans le navigateur, invisibles dans les tests automatises precedents :

1. **Sources non pertinentes sur les messages hors-question** (ex. « hello ») : HyDE genere un paragraphe juridique plausible meme pour une entree qui n'est pas une vraie question, ce qui remonte des chunks sans rapport et les affichait comme "sources" alors que la reponse ne les citait pas. **Corrige** : `RagAgent._keep_cited_sources` (extraction regex des numeros d'article dans la reponse, filtrage des sources affichees a celles reellement citees) — c'est le filet de securite anti-hallucination decrit dans la reponse Q2 du README, jamais implemente jusque-la.
2. **Refus alors que l'information existe dans le corpus** (« combien de jours de conges par an ? ») : un article long redecoupe en plusieurs chunks (`L3141-24`) polluait le top-k d'une seule sous-question avec des doublons du meme article, evincant l'article pertinent (`L3141-3`) avant meme l'agregation entre sous-questions. **Corrige** : `Retriever.search` sur-echantillonne (`OVERSAMPLE_FACTOR = 3`) puis deduplique par article, garantissant top_k *articles distincts* et non top_k *chunks* (potentiellement du meme article).
3. **HyDE peut degrader le retrieval sur les questions chiffrees** : le prompt HyDE interdit volontairement d'inventer des chiffres precis (bonne pratique anti-hallucination), donc pour une question du type « combien de jours ? » le paragraphe hypothetique reste vague et s'eloigne semantiquement de l'article qui donne le chiffre exact — alors que la question brute, elle, le retrouve directement (verifie : position 4/5, distance 0.27). **Corrige** : `QuestionFormatterAgent` cherche maintenant avec la sous-question brute *et* sa version HyDE, pas HyDE seul ; `RagAgent` deduplique et fusionne les deux jeux de resultats. Teste sur 3 executions repetees : 2/3 refus avant le fix, 3/3 reponses correctes apres.
4. **Une sous-question peut totalement evincer une autre du contexte final, sur une question composee/multi-sujets** (ex. « quelle est la duree legale du travail **et** combien de jours de conges ai-je ? »). `_retrieve_for_queries` fusionnait tous les candidats de toutes les sous-questions puis triait globalement par distance avant de plafonner a `MAX_CONTEXT_CHUNKS` : si les chunks d'un sujet scoraient tous mieux que ceux de l'autre, le sujet le moins bien classe disparaissait entierement du contexte envoye au LLM. Observe en conditions reelles : sur une question a deux sujets, le retrieval n'a remonte que des chunks "conges payes", `L3121-27` (duree legale, pourtant trouve dans 100% des tests precedents) a disparu — et le LLM a comble le vide avec une connaissance generale non sourcee (« 35h/semaine » sans citation), en violation de la regle « chaque affirmation doit etre rattachee a un article du contexte » du sujet. **Corrige en deux temps** :
   - `QuestionFormatterAgent.format_question` renvoie desormais les requetes groupees par sous-question (`list[list[str]]`) plutot qu'une liste plate ;
   - `RagAgent._interleave_groups` alterne entre les groupes (une sous-question a la fois) au lieu de trier globalement, garantissant une representation equitable de chaque sous-question dans le contexte final, meme si l'une matche moins bien que l'autre.
   - En complement (defense en profondeur), le prompt systeme interdit desormais explicitement de completer une reponse partielle avec des connaissances generales : si une partie de la question n'est pas couverte par le contexte, le systeme doit le dire clairement pour cette partie plutot que d'improviser.
   - Reteste sur le meme cas apres le fix : les deux sujets sont representes a parts egales dans le contexte (4 chunks "duree du travail" + 4 chunks "conges payes"), la reponse cite correctement `L3121-27` pour la duree legale et reconnait honnetement l'absence d'information precise sur le nombre de jours de conges plutot que d'inventer.

Aucun de ces bugs n'etait detecte par `evaluate_retrieval.py` (jalon 3), qui teste `Retriever.search` directement sur une question simple, sans passer par la decomposition/HyDE ni par des questions multi-sujets — utile a savoir : valider le retrieval brut ne garantit pas que le pipeline complet (formatage de question + generation, en particulier sur des questions composees) se comporte bien en conditions reelles.

## Recherche hybride (evaluee, priorite revue apres le jalon 3)

L'evaluation du retrieval (jalon 3, voir `docs/jalon2_jalon3_indexation_retrieval.md`) a compare 3 modeles d'embedding sur 5 questions de test : `paraphrase-multilingual-MiniLM-L12-v2` (2/5), `distiluse-base-multilingual-cased-v2` (4/5), puis `intfloat/multilingual-e5-base` (5/5, modele retenu). Le dernier modele, concu pour le retrieval, resout tous les cas d'echec observes precedemment.

- **Mecanisme** (si implemente malgre tout) : combiner un score lexical (BM25 sur le texte des chunks, ou correspondance directe sur un numero d'article du type `L3121-1`) avec le score vectoriel existant, fusionnes par une methode type RRF (Reciprocal Rank Fusion).
- **Pourquoi ce n'est plus la priorite** : le probleme empirique qui justifiait cette amelioration (echecs de retrieval sur le jeu de test) a ete resolu par un meilleur choix de modele d'embedding, pas besoin d'ajouter une couche lexicale pour ce cas precis.
- **Interet residuel** : reste utile pour un cas que le vectoriel seul ne couvre pas structurellement : une question qui cite un numero d'article exact (« que dit L3121-1 ? »), ou tape un numero d'article mal orthographie/segmente. Pourrait redevenir pertinent si de nouvelles questions de test le justifient.
- **Statut** : degrade de « priorite empirique » a « amelioration secondaire, a envisager si le temps le permet ». La **decomposition** (exigee a l'oral) reste la priorite du jalon 6.
