# Agent récupérateur de référence — vérification de fraîcheur via l'API Légifrance

Dernier composant du schéma d'architecture de l'équipe (`Agent formateur de question` → `Vector DB` → `RAG` → **`Agent récupérateur de référence` → API Légifrance**), implémenté séparément de la décomposition/HyDE (voir `docs/jalon6_ameliorations.md`).

## Ce que ça fait

Après génération de la réponse, pour chaque article **réellement cité** dans la réponse (filtre déjà en place, voir `RagAgent._keep_cited_sources`), l'agent interroge en direct l'API Légifrance (PISTE) pour vérifier que le texte stocké localement (jalon 1) est toujours d'actualité.

Trois verdicts possibles, stockés dans les métadonnées sous la clé `fraicheur` :
- **`a_jour`** : le texte en direct correspond exactement au texte indexé, l'article est toujours `VIGUEUR`.
- **`modifie`** : l'article est toujours en vigueur mais son texte a changé depuis l'indexation — signal fort qu'il faut réindexer.
- **`obsolete`** : l'article n'est plus `VIGUEUR` (abrogé, remplacé...) — le corpus est obsolète sur ce point précis.
- **`verification_indisponible`** : l'appel à l'API a échoué (réseau, quota, timeout) — ne bloque jamais la réponse, juste un indicateur en moins.
- **`non_verifiable`** : pas de `legi_id` disponible pour ce chunk (ne devrait plus arriver depuis l'ajout de ce champ aux métadonnées).

C'est un complément direct à la réponse Q3 du README (fraîcheur) : au lieu de se contenter d'annoncer une date de corpus, le système vérifie activement, article par article, si l'information citée est toujours correcte.

## Architecture (classes à responsabilité unique)

- **`src/legifrance/oauth_client.py` — `LegifranceOAuthClient`** : gère le flux OAuth2 `client_credentials` (endpoint production `https://oauth.piste.gouv.fr/api/oauth/token`), met en cache le token et le renouvelle automatiquement avant expiration (marge de 60s).
- **`src/legifrance/legifrance_client.py` — `LegifranceClient`** : appelle `POST /consult/getArticle` (endpoint production `https://api.piste.gouv.fr/dila/legifrance/lf-engine-app`) avec le `legi_id` de l'article, renvoie texte/état/numéro.
- **`src/legifrance/exceptions.py`** : `LegifranceAuthError`, `LegifranceApiError` — unifient les erreurs HTTP *et* réseau (timeout, connexion refusée) sous une seule exception exploitable par l'appelant (bug trouvé et corrigé pendant les tests : les erreurs réseau n'étaient pas rattrapées au départ, voir plus bas).
- **`src/reference_retriever_agent.py` — `ReferenceRetrieverAgent`** : orchestrateur, compare le texte stocké au texte en direct pour chaque source citée, ne lève jamais d'exception vers l'appelant (dégradation gracieuse systématique).
- **`src/freshness_label.py`** : traduit le statut `fraicheur` en libellé affichable, partagé par les 3 interfaces (CLI, Streamlit, FastAPI) pour éviter la duplication.

`RagAgent` compose `ReferenceRetrieverAgent` comme il compose déjà `QuestionFormatterAgent` — même pattern de composition que `ManagerAgent`/`ModeratorAgent`/`RagAgent`.

## Activation optionnelle, jamais bloquante

Sans `LEGIFRANCE_CLIENT_ID`/`LEGIFRANCE_CLIENT_SECRET` dans `.env`, `RagAgent._build_reference_retriever_agent()` renvoie `None` et la vérification est simplement ignorée (`metadatas` renvoyées telles quelles). Aucun coéquipier n'a besoin de ces identifiants pour que le reste du pipeline fonctionne — c'est un bonus, pas une dépendance dure comme `GROQ_API_KEY`.

## Pré-requis : `legi_id` dans les métadonnées

Le corpus (jalon 1) contenait déjà `legi_id` (identifiant interne Légifrance, ex. `LEGIARTI000033020376`) par document, mais ce champ n'était jamais propagé jusqu'aux métadonnées de la base vectorielle. Ajouté à `Chunk`, `SearchResult`, `VectorStore`/`VectorDB` — **nécessite une réindexation** (`python index.py`) après ce changement de schéma.

## Vérification effectuée

- **OAuth2** : testé en direct avec de vrais identifiants PISTE — l'endpoint sandbox renvoie `invalid_client`, l'endpoint **production** fonctionne (`access_token` obtenu, scope `openid resource.READ`).
- **`getArticle`** : testé avec le `legi_id` de `L3121-27` — l'API renvoie le texte exact déjà présent dans notre corpus, `etat: VIGUEUR`, confirmant que le corpus jalon 1 est toujours à jour sur cet article.
- **Bout en bout** : question réelle → réponse citant `L3121-27` → vérification automatique → `fraicheur: a_jour`, `etat_legifrance: VIGUEUR`.
- **Dégradation gracieuse** : testée avec un client factice qui échoue systématiquement → `fraicheur: verification_indisponible`, aucune exception propagée, la réponse reste utilisable.
- **Bug trouvé et corrigé** : les erreurs réseau (`requests.exceptions.RequestException` — timeout, DNS, connexion refusée) n'étaient initialement pas rattrapées par `LegifranceClient`/`LegifranceOAuthClient` (seules les erreurs HTTP avec un code de statut l'étaient), ce qui aurait fait planter toute la génération si l'API Légifrance était injoignable. Corrigé en enveloppant les appels `requests.post` dans un `try/except` dédié.

**Non testé faute de quota Groq disponible au moment du développement** : le cas `modifie`/`obsolete` sur un vrai article modifié récemment (nécessiterait de trouver un article réellement amendé depuis l'extraction du corpus pour l'observer en conditions réelles), et une vérification multi-sources (question comparative, plusieurs articles cités simultanément) — la logique est testée unitairement (`ReferenceRetrieverAgent.check_freshness` sur une liste), mais pas confirmée de bout en bout avec de vrais appels Groq sur plusieurs sources à la fois.
