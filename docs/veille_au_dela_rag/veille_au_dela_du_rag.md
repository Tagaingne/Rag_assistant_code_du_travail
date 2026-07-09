# Veille technologique – Au-delà du RAG

---

## 1. Note de synthèse (4 pages maximum)

Je pars de notre projet d'assistant RAG sur le Code du travail. Aujourd'hui, notre architecture ressemble au RAG classique vu en cours : on extrait les articles, on découpe, on ajoute des métadonnées juridiques, puis on recherche les passages utiles avant de générer une réponse. Cette base est saine, mais elle montre vite ses limites dès que l'on veut garantir une référence exacte, suivre une version d'article dans le temps, ou répondre à une question qui demande plusieurs étapes de raisonnement.

Le RAG vectoriel classique est surtout bon quand la question ressemble au texte à retrouver. Il est moins fiable pour les références exactes comme `L3121-1`, pour les questions globales du type "quelles sont les grandes règles sur le temps de travail ?", pour les questions multi-sauts et pour les situations où la première recherche est mauvaise. Les cinq approches ci-dessous ne remplacent donc pas toutes le RAG : elles étendent l'étage de contexte selon des besoins différents.

### 1.1 GraphRAG et graphes de connaissances

GraphRAG consiste à transformer un corpus en graphe. Au lieu de stocker seulement des chunks indépendants, on extrait des entités, des relations, parfois des événements ou des affirmations, puis on les relie. Dans l'approche Microsoft, l'index contient aussi une hiérarchie de communautés et des résumés de communautés qui servent aux questions globales sur le corpus [S1][S2]. C'est très différent d'un simple top-k vectoriel : la recherche peut exploiter la structure entre les informations.

La limite traitée est double : les questions multi-sauts et les questions de synthèse globale. Si une question demande de relier une personne, une société, un contrat et une décision, aucun chunk isolé n'a forcément une similarité très forte avec la question. Un graphe peut suivre les relations et donner une explication plus traçable. Sur notre projet Code du travail, cela pourrait relier articles, notions juridiques, obligations, sanctions, jurisprudences et conventions collectives.

Les avantages sont l'explicabilité, la navigation entre entités et la capacité à faire du sensemaking sur un corpus entier. Les inconvénients sont le coût et la maintenance : extraction d'entités, résolution d'entités, construction du graphe, résumés de communautés et contrôles qualité. Le coût de construction est élevé ; le coût par requête est moyen à élevé selon le mode de recherche ; le coût de maintenance est élevé si les textes changent souvent. LazyGraphRAG et LightRAG attaquent justement ce problème de coût en réduisant le travail LLM fait à l'indexation ou en ajoutant des mises à jour incrémentales [S3][S4].

La maturité est bonne côté recherche et en progression côté outils. Microsoft GraphRAG, Neo4j GraphRAG, LightRAG et Graphiti montrent que l'écosystème devient concret [S2][S4][S5][S17][S20]. Mon avis : ce n'est pas la première amélioration à faire sur notre assistant Code du travail. Pour retrouver précisément les articles en vigueur, le graphe est trop coûteux au départ. Il deviendrait pertinent si l'on ajoute jurisprudence, relations entre textes, réseaux d'acteurs ou historique temporel.

### 1.2 Retrieval hiérarchique (RAPTOR)

RAPTOR organise les documents en arbre de résumés. Les chunks de base sont regroupés, chaque groupe est résumé, puis les résumés sont eux-mêmes regroupés et résumés. À la requête, le système peut retrouver une feuille détaillée ou un nœud plus haut dans l'arbre [S6]. C'est proche de l'idée de parent-child chunking vue en cours, mais avec plusieurs niveaux de synthèse construits automatiquement.

La limite adressée est surtout la difficulté des questions globales. Un utilisateur ne demande pas toujours "que dit l'article X ?", il peut demander "quelles sont les grandes règles sur les congés payés ?" ou "résume les conditions de rupture du contrat". Un chunk isolé est trop local pour cela. RAPTOR donne une vue d'ensemble sans envoyer tout le corpus au modèle.

Les avantages sont la simplicité relative par rapport à un graphe et la capacité à naviguer entre détail et synthèse. Le coût de construction est moyen à élevé, car il faut faire du clustering et générer les résumés. Le coût par requête est moyen. Le coût de maintenance dépend de la fraîcheur : si un article change, il faut savoir quels résumés parents recalculer. Dans un corpus juridique, c'est un vrai sujet, car une modification de phrase peut changer l'interprétation.

La maturité est correcte comme approche de recherche, mais elle est moins standard en production que le retrieval hybride. Mon avis : RAPTOR serait utile pour des synthèses thématiques du Code du travail, à condition de ne jamais laisser le résumé remplacer la source exacte. Dans notre assistant, chaque résumé devrait pointer vers les articles LEGI, leur `legi_id`, leur état et leurs dates de validité.

### 1.3 Retrieval hybride (BM25 + recherche vectorielle + RRF + rerankers)

Le retrieval hybride est l'amélioration la plus pragmatique. Il combine une recherche lexicale, souvent BM25, avec une recherche vectorielle. BM25 excelle sur les références exactes, les sigles, les noms propres et les formulations présentes mot pour mot. La recherche vectorielle capte mieux les reformulations. On fusionne ensuite les classements, par exemple avec Reciprocal Rank Fusion, puis un reranker peut reclasser les meilleurs candidats [S7][S8][S9][S10].

La limite traitée est très concrète : le vectoriel seul peut rater une correspondance exacte. Dans notre projet, si l'utilisateur demande "Que dit l'article L3121-1 ?", il ne faut pas seulement trouver un passage proche sur la durée du travail ; il faut retrouver précisément la référence. C'est aussi essentiel pour les citations et la traçabilité.

Les avantages sont la maturité, le coût raisonnable et la compatibilité avec les métadonnées. Qdrant, Weaviate, Elasticsearch et Cohere couvrent déjà ces briques : dense + sparse, BM25, RRF, filtres, reranking [S7][S8][S9][S10]. Le coût de construction est faible à moyen. Le coût par requête est faible pour BM25 + vecteur, moyen si l'on ajoute un reranker. Le coût de maintenance reste maîtrisé : réindexer les documents modifiés et maintenir les filtres `etat`, `date_debut`, `date_fin`, `source_file`.

L'inconvénient est que l'hybride ne résout pas tout. Il ne construit pas de vision globale et ne modélise pas naturellement les relations multi-sauts. Mon avis est très clair : pour notre assistant Code du travail, c'est la meilleure prochaine étape. Avant GraphRAG ou agent, il faut fiabiliser le retrieval, gérer la fraîcheur des articles et assurer des références exactes.

### 1.4 RAG agentique

Le RAG agentique transforme la recherche en boucle. Au lieu de faire une seule recherche top-k puis une génération, un LLM outillé peut choisir une stratégie : chercher un article précis, vérifier que la version est en vigueur, reformuler si les résultats sont faibles, interroger une autre source, comparer plusieurs textes et seulement ensuite répondre. Anthropic distingue les workflows, où les étapes sont codées, des agents, où le modèle décide dynamiquement de ses outils [S11].

La limite traitée est le contexte figé. Le RAG classique ne sait pas vraiment se corriger. Self-RAG et Corrective RAG montrent deux directions : décider quand récupérer de l'information, critiquer sa génération, ou évaluer la qualité des documents retrouvés avant de répondre [S12][S13].

Les avantages sont la flexibilité et la capacité à traiter des questions plus complexes. Pour notre projet, un agent pourrait avoir des outils simples et contrôlés : `search_article(reference)`, `search_theme(query)`, `check_version(article, date)`, `compare_articles(a, b)`, `show_sources(ids)`. Cela aiderait sur une question comme "compare les obligations de l'employeur en matière de harcèlement et de sécurité".

Les inconvénients sont importants : coût par requête élevé, latence, non-déterminisme, évaluation plus difficile et risque d'actions inutiles. En droit, un agent trop libre est dangereux. Il faut des garde-fous : pas de réponse sans citation, vérification obligatoire de l'état en vigueur, limite d'itérations, logs d'outils et refus quand les sources ne suffisent pas. Mon avis : l'agentique doit venir après un retrieval hybride fiable, comme une couche avancée pour les questions complexes.

### 1.5 Long Context / Cache / Mémoire (Graphiti, Cognee...)

Les modèles à long contexte et le cache changent une partie du raisonnement. Si le corpus est petit ou très stable, on peut parfois mettre beaucoup de contenu directement dans le prompt. Le prompt caching permet de réutiliser un préfixe identique, donc de réduire coût et latence pour des requêtes répétées sur le même contexte [S14]. Mais cela ne supprime pas les besoins de sélection, citation et fraîcheur.

La limite traitée est le besoin de retrieval quand le contexte peut être fourni ou réutilisé directement. Le problème est que le long contexte coûte cher, dilue parfois l'attention et ne garantit pas que le modèle utilisera le bon passage. Le papier "Lost in the Middle" reste utile pour rappeler qu'une grande fenêtre de contexte n'est pas automatiquement une bonne mémoire [S15].

La mémoire agentique va plus loin. Graphiti construit des graphes temporels où les faits ont une provenance et une validité dans le temps [S16][S17]. Cognee propose une mémoire longue durée avec graphes de connaissances, embeddings et recherche [S18][S19]. Ces outils brouillent la frontière entre base documentaire, graphe et mémoire.

Pour le Code du travail, le lien est direct : la fraîcheur juridique est centrale. Aujourd'hui, on veut surtout la version en vigueur. Demain, on pourrait demander : "Quelle version de cet article était applicable en 2022 ?" Là, une mémoire temporelle ou un graphe de versions devient vraiment utile. Mon avis : long context et cache sont des optimisations, pas une architecture principale pour un assistant juridique. La mémoire temporelle est prometteuse, mais elle n'est justifiée que si l'historique des versions devient un besoin fonctionnel.

### Position générale

Je ne pense pas que le RAG soit dépassé. Il devient plutôt une brique dans un étage de contexte plus large : retrieval hybride pour la précision, graphe pour les relations, hiérarchie pour les synthèses, agent pour la recherche itérative, cache et mémoire pour la réutilisation et le temps long. Pour notre assistant Code du travail, ma trajectoire serait progressive : hybrid search + métadonnées juridiques, puis reranker, puis éventuellement agent encadré ou graphe temporel si le corpus s'étend.

---

## 2. Tableau comparatif

| Approche | Type de questions où elle excelle | Limite du RAG classique adressée | Coût de construction | Coût par requête | Fraîcheur des données | Maturité de l'écosystème | Cas d'usage type |
|---|---|---|---|---|---|---|---|
| GraphRAG et graphes de connaissances | Multi-sauts, relations entre entités, synthèse globale d'un corpus | Top-k vectoriel faible pour relier plusieurs documents et comprendre un corpus entier | Élevé : extraction, résolution d'entités, graphe, communautés, résumés | Moyen à élevé selon le parcours et les appels LLM | Bonne si le graphe est mis à jour ; maintenance complexe | Moyenne à forte : Microsoft GraphRAG, Neo4j, LightRAG, Graphiti | Investigation, conformité, corpus juridique enrichi, analyse de réseaux |
| Retrieval hiérarchique (RAPTOR) | Questions globales, synthèses par thème, navigation détail/synthèse | Le chunk isolé ne suffit pas pour répondre à une question globale | Moyen à élevé : clustering et résumés LLM | Moyen | Moyenne : les résumés parents doivent être recalculés | Moyenne : solide en recherche, moins standard en production | Rapports longs, documentation stable, synthèses de thèmes |
| Retrieval hybride BM25 + vecteur + RRF + reranker | Références exactes, sigles, recherche sémantique simple, questions factuelles citées | Le vectoriel seul rate parfois les correspondances exactes | Faible à moyen | Faible à moyen ; plus élevé avec reranker | Très bonne avec filtres sur dates, état, version et source | Forte : Elasticsearch, Weaviate, Qdrant, Cohere | Assistant juridique, support produit, documentation avec codes et références |
| RAG agentique | Questions complexes, recherche itérative, comparaison de sources | Pipeline figé incapable de reformuler ou corriger sa recherche | Moyen à élevé : outils, orchestration, évaluation | Élevé : plusieurs appels LLM et outils possibles | Bonne si l'agent vérifie explicitement les versions | En progression ; nécessite garde-fous et evals | Deep research, assistant expert, analyse juridique encadrée |
| Long context / cache / mémoire | Petits corpus répétés, dossiers longs, mémoire temporelle, historique | Besoin de retrieval quand le contexte peut être réutilisé ou mémorisé | Faible pour cache ; moyen à élevé pour mémoire graphe | Faible si cache hit ; élevé si tout le contexte est relu | Cache : limitée ; mémoire temporelle : forte si bien modélisée | Cache mature chez fournisseurs ; mémoire graphe plus jeune | Dossiers répétés, assistants personnels, historique de faits ou versions |

---

## 3. Les trois études de cas

### Cabinet juridique

**Architecture recommandée : retrieval hybride + reranker + filtres de métadonnées, avec GraphRAG ciblé en option.**

Le cabinet a 50 000 décisions et contrats, des recherches précises, des références exactes et une exigence forte de traçabilité. La base doit donc être un retrieval hybride. BM25 retrouve les numéros de décisions, clauses, parties, dates et articles. Le vectoriel couvre les reformulations. RRF fusionne les deux classements, puis un reranker améliore l'ordre final avant génération.

La justification vient directement du tableau : l'approche hybride a un coût raisonnable, une bonne maturité et surtout une très bonne gestion de la fraîcheur avec métadonnées. Comme dans notre corpus LEGI, il faut indexer le type de document, la juridiction, la date, la version, la source, l'état et l'identifiant stable. La mise à jour hebdomadaire est compatible avec ce modèle.

Les autres architectures sont moins adaptées comme socle. GraphRAG est intéressant avec un budget confortable, mais plutôt en deuxième étape pour relier jurisprudences, sociétés, clauses et notions. RAPTOR risque de lisser des nuances juridiques dans ses résumés. Un agent peut aider sur des recherches complexes, mais il doit rester contraint par le retrieval et les citations. Long context seul ne donne pas assez de contrôle sur les références et coûterait cher sur 50 000 documents.

### Analyste d'investigation

**Architecture recommandée : GraphRAG temporel + recherche hybride + agent encadré.**

Ici, le corpus contient des courriels, notes et rapports. Les questions portent sur "qui est lié à qui", "qui a rencontré qui" et "quand". C'est typiquement un problème de graphe : personnes, organisations, lieux, documents et événements deviennent des nœuds ; rencontres, échanges, signatures ou transferts deviennent des relations.

Le tableau montre que GraphRAG excelle sur les questions multi-sauts et l'analyse de réseaux. La dimension temporelle est importante : une relation peut être vraie à une date et fausse plus tard. Un outil inspiré de Graphiti est donc pertinent, car il garde la provenance et la validité temporelle des faits. La recherche hybride reste utile pour retrouver un email précis, et un agent encadré peut explorer le graphe, construire une timeline, puis revenir aux sources textuelles.

Les autres architectures seules sont moins adaptées. RAPTOR synthétise mais ne reconstruit pas naturellement les relations. Le retrieval hybride seul retrouve des documents, mais ne donne pas de réseau. Long context devient vite trop coûteux et peu lisible. Un agent sans graphe risquerait de multiplier les recherches sans représentation stable des liens.

### Start-up au support saturé

**Architecture recommandée : RAG hybride simple, automatisé quotidiennement, sans GraphRAG au départ.**

La start-up a 300 pages de documentation, trois semaines, un budget très limité et une documentation qui change chaque jour. Le meilleur choix est une architecture simple : ingestion automatisée, BM25 + vecteur, filtres sur produit/version/date/URL, génération avec citation de la page source.

Le tableau favorise l'hybride : coût de construction faible à moyen, coût par requête faible, maturité forte, fraîcheur facile à maintenir. Les questions support sont souvent directes : "comment réinitialiser un compte ?", "quelle API utiliser ?", "que signifie cette erreur ?". On peut ajouter un petit reranker plus tard si les réponses se mélangent.

Les autres architectures sont trop lourdes pour ce contexte. GraphRAG coûte trop cher à construire et maintenir. RAPTOR impose de recalculer des résumés presque tous les jours. Le RAG agentique augmente coût et latence alors que l'équipe doit livrer vite. Long context peut fonctionner sur 300 pages, mais il est moins propre pour citer les sources et moins économique si beaucoup d'utilisateurs posent des questions.

---

## 4. Journal de veille (annexe)

### Source S1

- **Titre :** From Local to Global: A Graph RAG Approach to Query-Focused Summarization
- **Auteur ou organisme :** Darren Edge et al., Microsoft Research
- **Date :** 24 avril 2024
- **Lien :** https://arxiv.org/abs/2404.16130
- **Résumé :** Papier de référence sur GraphRAG. Il explique la construction d'un graphe d'entités, la génération de résumés de communautés et l'usage de ces résumés pour les questions globales. Il montre surtout pourquoi un RAG classique échoue quand la question porte sur tout le corpus.
- **Commentaire personnel :** Source centrale pour comprendre GraphRAG. Je garde une prudence sur les résultats chiffrés, car les benchmarks ne couvrent pas forcément un corpus juridique français.
- **Niveau de confiance :** Élevé

### Source S2

- **Titre :** GraphRAG documentation
- **Auteur ou organisme :** Microsoft
- **Date :** documentation vivante, consultée le 9 juillet 2026
- **Lien :** https://microsoft.github.io/graphrag/
- **Résumé :** Documentation officielle du projet Microsoft GraphRAG. Elle décrit le processus : extraction d'un knowledge graph, hiérarchie de communautés, résumés et modes de requête comme Global Search, Local Search et DRIFT Search. Elle est utile pour passer du papier à l'architecture.
- **Commentaire personnel :** Très fiable pour l'outillage Microsoft, mais elle reste une documentation de produit. Je l'utilise pour les concepts et non comme preuve indépendante de performance.
- **Niveau de confiance :** Élevé

### Source S3

- **Titre :** LazyGraphRAG: Setting a new standard for quality and cost
- **Auteur ou organisme :** Darren Edge, Ha Trinh, Jonathan Larson, Microsoft Research
- **Date :** 25 novembre 2024
- **Lien :** https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/
- **Résumé :** Article Microsoft Research sur une variante de GraphRAG qui évite une partie des coûts d'indexation en reportant du travail LLM au moment de la requête. Il compare LazyGraphRAG à vector RAG, RAPTOR et GraphRAG. Il insiste sur le compromis coût/qualité.
- **Commentaire personnel :** Intéressant parce que Microsoft reconnaît implicitement que GraphRAG complet peut être cher. Les gains annoncés viennent de l'équipe Microsoft, donc je les prends comme indication à vérifier.
- **Niveau de confiance :** Élevé pour le principe, moyen pour les gains chiffrés

### Source S4

- **Titre :** LightRAG: Simple and Fast Retrieval-Augmented Generation
- **Auteur ou organisme :** Zirui Guo et al.
- **Date :** 8 octobre 2024
- **Lien :** https://arxiv.org/abs/2410.05779
- **Résumé :** Papier sur une approche de RAG avec graphes plus légère, retrieval à deux niveaux et mise à jour incrémentale. L'objectif est de mieux capter les dépendances complexes tout en réduisant coût et latence. Le papier cible directement les limites des représentations plates.
- **Commentaire personnel :** Pertinent pour des données qui changent, comme un corpus juridique. Je ne l'utiliserais pas sans benchmark local, car les performances papier ne garantissent pas le comportement sur LEGI.
- **Niveau de confiance :** Moyen à élevé

### Source S5

- **Titre :** GraphRAG for Python
- **Auteur ou organisme :** Neo4j
- **Date :** documentation vivante, consultée le 9 juillet 2026
- **Lien :** https://neo4j.com/docs/neo4j-graphrag-python/current/
- **Résumé :** Documentation officielle du package `neo4j-graphrag`. Elle présente des fonctions maintenues par Neo4j pour RAG, knowledge graph builder, pipelines, retrievers et intégrations LLM/vector stores. Cela montre une industrialisation progressive de GraphRAG.
- **Commentaire personnel :** Source utile pour évaluer la maturité outillage. Elle confirme que le graphe n'est pas seulement une idée de recherche, mais une brique exploitable.
- **Niveau de confiance :** Élevé

### Source S6

- **Titre :** RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval
- **Auteur ou organisme :** Parth Sarthi et al., Stanford
- **Date :** 31 janvier 2024
- **Lien :** https://arxiv.org/abs/2401.18059
- **Résumé :** Papier de référence sur le retrieval hiérarchique. RAPTOR construit un arbre par embedding, clustering et résumé récursif des chunks. Le retrieval peut ensuite utiliser plusieurs niveaux d'abstraction.
- **Commentaire personnel :** Très pertinent pour les synthèses longues. Pour du droit, je le vois comme une couche d'orientation, pas comme une source finale de vérité.
- **Niveau de confiance :** Élevé

### Source S7

- **Titre :** Hybrid search
- **Auteur ou organisme :** Weaviate
- **Date :** documentation vivante, consultée le 9 juillet 2026
- **Lien :** https://docs.weaviate.io/weaviate/concepts/search/hybrid-search
- **Résumé :** Documentation expliquant que la recherche hybride combine recherche vectorielle et BM25, puis fusionne les scores ou les rangs. Elle clarifie le rôle complémentaire du sémantique et du lexical. C'est exactement le besoin pour références exactes + reformulations.
- **Commentaire personnel :** Très utile pour notre projet Code du travail. La logique BM25 + vecteur est probablement le meilleur prochain incrément.
- **Niveau de confiance :** Élevé

### Source S8

- **Titre :** Hybrid Queries
- **Auteur ou organisme :** Qdrant
- **Date :** documentation vivante, consultée le 9 juillet 2026
- **Lien :** https://qdrant.tech/documentation/search/hybrid-queries/
- **Résumé :** Documentation sur les requêtes hybrides et multi-étapes dans Qdrant, avec prefetch sparse/dense et fusion RRF. Elle montre aussi des mécanismes de scoring et de reranking. C'est une base concrète pour industrialiser dense + sparse.
- **Commentaire personnel :** Source fiable si l'on choisit Qdrant. Les exemples sont très proches de ce que l'on pourrait construire pour LEGI.
- **Niveau de confiance :** Élevé

### Source S9

- **Titre :** Reciprocal rank fusion
- **Auteur ou organisme :** Elasticsearch
- **Date :** documentation vivante, consultée le 9 juillet 2026
- **Lien :** https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- **Résumé :** Documentation officielle sur RRF, méthode de fusion de classements qui ne demande pas que les scores soient comparables. Elle convient bien à la fusion de résultats BM25 et vectoriels. Elasticsearch en fait une brique de son API de recherche.
- **Commentaire personnel :** RRF est simple, robuste et facile à expliquer. Pour un livrable de Master, c'est un bon compromis entre qualité et complexité.
- **Niveau de confiance :** Élevé

### Source S10

- **Titre :** Master Reranking with Cohere Models
- **Auteur ou organisme :** Cohere
- **Date :** documentation vivante, consultée le 9 juillet 2026
- **Lien :** https://docs.cohere.com/docs/reranking-with-cohere
- **Résumé :** Documentation sur le reranking après une première recherche lexicale ou sémantique. Cohere explique l'intérêt du reranking comme deuxième étape pour améliorer la qualité de recherche dans un RAG. La documentation couvre aussi des données semi-structurées.
- **Commentaire personnel :** Pertinent après un retrieval hybride. Comme Cohere est fournisseur commercial, je ne reprends pas les promesses de performance sans test.
- **Niveau de confiance :** Moyen à élevé

### Source S11

- **Titre :** Building effective agents
- **Auteur ou organisme :** Anthropic
- **Date :** 19 décembre 2024
- **Lien :** https://www.anthropic.com/engineering/building-effective-agents
- **Résumé :** Article technique distinguant workflows et agents. Anthropic recommande de commencer simple et de n'ajouter l'agentique que si la flexibilité justifie coût et latence. L'article insiste aussi sur les outils et les garde-fous.
- **Commentaire personnel :** Très bon contrepoids aux effets de mode. Il justifie mon choix de ne pas placer l'agent avant un retrieval fiable.
- **Niveau de confiance :** Élevé

### Source S12

- **Titre :** Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
- **Auteur ou organisme :** Akari Asai et al.
- **Date :** 17 octobre 2023
- **Lien :** https://arxiv.org/abs/2310.11511
- **Résumé :** Papier fondateur sur un RAG réflexif qui apprend à décider quand récupérer de l'information, générer et critiquer. Il est un peu antérieur à 2024, mais reste central pour comprendre le passage d'un pipeline fixe à un système adaptatif. Il traite aussi la factualité et les citations.
- **Commentaire personnel :** Source plus ancienne que demandé, mais difficile à ignorer. Je la garde comme source historique principale pour Self-RAG.
- **Niveau de confiance :** Élevé

### Source S13

- **Titre :** Corrective Retrieval Augmented Generation
- **Auteur ou organisme :** Shi-Qi Yan et al.
- **Date :** 29 janvier 2024
- **Lien :** https://arxiv.org/abs/2401.15884
- **Résumé :** Papier sur CRAG, qui évalue la qualité des documents récupérés et déclenche des actions correctives si le retrieval est mauvais. Il répond directement au problème du RAG qui génère quand même avec de mauvaises sources. L'approche est plug-and-play avec des systèmes RAG.
- **Commentaire personnel :** Très pertinent pour un assistant juridique. Si les sources trouvées sont faibles, le système doit le signaler avant de répondre.
- **Niveau de confiance :** Élevé

### Source S14

- **Titre :** Prompt caching
- **Auteur ou organisme :** Anthropic
- **Date :** documentation vivante, consultée le 9 juillet 2026
- **Lien :** https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- **Résumé :** Documentation sur le cache de prompt. Le principe est de réutiliser des préfixes identiques pour réduire temps de traitement et coûts sur des contextes répétés. La documentation précise aussi les limites : cache invalidé si le contenu change, durée de vie, seuils et tarification.
- **Commentaire personnel :** Utile pour des documents relus souvent. Pour notre projet, cela peut optimiser certaines requêtes, mais ne remplace pas la recherche avec citations.
- **Niveau de confiance :** Élevé

### Source S15

- **Titre :** Lost in the Middle: How Language Models Use Long Contexts
- **Auteur ou organisme :** Nelson F. Liu et al.
- **Date :** 6 juillet 2023
- **Lien :** https://arxiv.org/abs/2307.03172
- **Résumé :** Papier montrant que les modèles peuvent moins bien utiliser une information placée au milieu d'un long contexte. Même si les modèles récents ont progressé, cette source reste importante pour nuancer "il suffit de tout mettre dans le prompt". Elle propose aussi des protocoles d'évaluation du long context.
- **Commentaire personnel :** Source historique mais encore utile. Elle rappelle qu'une grande fenêtre de contexte n'est pas une garantie de bonne exploitation des sources.
- **Niveau de confiance :** Élevé

### Source S16

- **Titre :** Zep: A Temporal Knowledge Graph Architecture for Agent Memory
- **Auteur ou organisme :** Preston Rasmussen et al.
- **Date :** 20 janvier 2025
- **Lien :** https://arxiv.org/abs/2501.13956
- **Résumé :** Papier sur une architecture de mémoire agentique fondée sur Graphiti, un moteur de graphe temporel. Il traite la mémoire dynamique, les relations historiques et les sources qui évoluent. Il positionne la mémoire comme plus qu'un simple retrieval statique.
- **Commentaire personnel :** Très pertinent pour l'historique juridique. Je reste prudent car le papier est lié à l'écosystème Zep.
- **Niveau de confiance :** Moyen

### Source S17

- **Titre :** Graphiti GitHub repository
- **Auteur ou organisme :** Zep / getzep
- **Date :** dépôt vivant, consulté le 9 juillet 2026
- **Lien :** https://github.com/getzep/graphiti
- **Résumé :** Dépôt officiel de Graphiti. Il présente des graphes de contexte temporels pour agents, avec suivi des changements de faits, provenance et construction incrémentale. Le dépôt cible explicitement les jeux de données dynamiques.
- **Commentaire personnel :** Outil intéressant si notre assistant doit gérer les versions passées des articles. Je le classe comme prometteur mais plus jeune qu'un moteur hybride classique.
- **Niveau de confiance :** Moyen à élevé

### Source S18

- **Titre :** Cognee GitHub repository
- **Auteur ou organisme :** Cognee / Topoteretes
- **Date :** dépôt vivant, consulté le 9 juillet 2026
- **Lien :** https://github.com/topoteretes/cognee
- **Résumé :** Dépôt officiel de Cognee, présenté comme une plateforme open source de mémoire pour agents. Cognee combine graphes de connaissances, embeddings et recherche pour donner une mémoire longue durée. Le dépôt pointe aussi vers un papier de recherche 2025.
- **Commentaire personnel :** Intéressant pour comparer les approches de mémoire. Je ne le choisirais pas en premier pour un RAG juridique simple, mais il donne une direction d'évolution.
- **Niveau de confiance :** Moyen à élevé

### Source S19

- **Titre :** Optimizing the Interface Between Knowledge Graphs and LLMs for Complex Reasoning
- **Auteur ou organisme :** Vasilije Markovic et al.
- **Date :** 30 mai 2025
- **Lien :** https://arxiv.org/abs/2505.24478
- **Résumé :** Papier lié à Cognee sur l'interface entre knowledge graphs et LLMs. Il montre que les performances dépendent fortement du chunking, de la construction du graphe, du retrieval et du prompting. Les résultats varient selon les jeux de données et les métriques.
- **Commentaire personnel :** Source utile car elle évite de présenter le graphe comme magique. L'architecture doit être optimisée et évaluée, sinon elle peut décevoir.
- **Niveau de confiance :** Moyen

### Source S20

- **Titre :** LightRAG GitHub repository
- **Auteur ou organisme :** HKUDS
- **Date :** dépôt vivant, consulté le 9 juillet 2026
- **Lien :** https://github.com/HKUDS/LightRAG
- **Résumé :** Dépôt open source de LightRAG. Il permet d'évaluer la maturité pratique de l'approche au-delà du papier, notamment les backends, l'installation et les intégrations. C'est une source d'outillage plutôt qu'une source scientifique.
- **Commentaire personnel :** Utile pour estimer la faisabilité. Pour notre projet, je m'en servirais seulement après une comparaison avec un baseline hybride.
- **Niveau de confiance :** Moyen à élevé

### Remarque sur les divergences entre sources

Les sources ne se contredisent pas frontalement, mais elles ne sont pas toutes neutres. Microsoft, Cohere, Neo4j, Zep et Cognee décrivent aussi leurs propres outils. Je considère donc leurs chiffres de performance comme des signaux à tester, pas comme des garanties. Le consensus est plus solide sur les principes : le RAG vectoriel seul est fragile pour les références exactes, les questions globales, les multi-sauts et la recherche en plusieurs étapes.

---

## Vérification finale des consignes

- Le document est bien un seul fichier Markdown : `docs/veille_au_dela_rag/veille_au_dela_du_rag.md`.
- La note de synthèse présente les cinq approches demandées, avec principe, limite traitée, avantages, inconvénients, coûts, maturité, outils et avis argumenté.
- Le tableau comparatif contient les colonnes minimales demandées.
- Les trois études de cas sont intégrées dans ce même fichier.
- Le journal de veille contient des sources fiables, datées, liées et commentées.
- Le lien avec notre projet Code du travail est fait : fraîcheur LEGI, métadonnées juridiques, traçabilité, références d'articles et pistes d'amélioration.
- Les divergences et limites des sources sont signalées.
