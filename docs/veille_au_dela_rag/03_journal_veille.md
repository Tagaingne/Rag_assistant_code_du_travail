# Journal de veille

## 1. From Local to Global: A Graph RAG Approach to Query-Focused Summarization

- Auteur / organisme : Darren Edge et al., Microsoft Research.
- Date : 24 avril 2024.
- Lien : https://arxiv.org/abs/2404.16130
- Resume : Papier fondateur du GraphRAG Microsoft. Il explique pourquoi le RAG vectoriel classique est faible sur les questions globales et propose un graphe d'entites avec resumes de communautes. Utile pour comprendre le principe scientifique, mais les evaluations restent centrees sur certaines classes de questions.
- Niveau de confiance : eleve.

## 2. GraphRAG documentation

- Auteur / organisme : Microsoft.
- Date : documentation consultee en juillet 2026.
- Lien : https://microsoft.github.io/graphrag/
- Resume : Documentation officielle du projet open source Microsoft GraphRAG. Elle detaille l'indexation, les entites, relations, communautes, modes Global Search, Local Search et DRIFT. Source utile pour relier le papier a une implementation concrete.
- Niveau de confiance : eleve.

## 3. Microsoft GraphRAG GitHub

- Auteur / organisme : Microsoft.
- Date : depot actif consulte en juillet 2026.
- Lien : https://github.com/microsoft/graphrag
- Resume : Depot officiel. Il confirme que GraphRAG est une suite de transformation de donnees pour extraire de la structure depuis du texte. Le README avertit que l'indexation peut etre couteuse, point important pour l'analyse architecturale.
- Niveau de confiance : eleve.

## 4. LazyGraphRAG: Setting a new standard for quality and cost

- Auteur / organisme : Microsoft Research.
- Date : 25 novembre 2024.
- Lien : https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/
- Resume : Article de recherche Microsoft sur la reduction du cout GraphRAG. L'idee est de garder les benefices du graphe sans payer autant d'indexation et de summaries a l'avance. Source interessante, mais reste produite par l'equipe qui promeut l'approche.
- Niveau de confiance : eleve pour le principe, moyen pour les gains chiffres.

## 5. LightRAG: Simple and Fast Retrieval-Augmented Generation

- Auteur / organisme : Zirui Guo et al.
- Date : 8 octobre 2024.
- Lien : https://arxiv.org/abs/2410.05779
- Resume : Propose une variante plus legere de GraphRAG avec representation graphe + vecteurs, retrieval a deux niveaux et mises a jour incrementales. Utile pour comparer avec Microsoft GraphRAG sur le cout et la fraicheur. Les benchmarks sont a lire comme resultats de recherche, pas comme garantie produit.
- Niveau de confiance : moyen a eleve.

## 6. HKUDS LightRAG GitHub

- Auteur / organisme : HKUDS.
- Date : depot actif consulte en juillet 2026.
- Lien : https://github.com/HKUDS/LightRAG
- Resume : Depot open source tres actif, avec support Neo4j, reranker, citations et multiples backends. Confirme que LightRAG a evolue au-dela du papier initial vers un outil plus complet. Source utile pour maturite outillage.
- Niveau de confiance : moyen a eleve.

## 7. RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval

- Auteur / organisme : Parth Sarthi et al., Stanford.
- Date : 31 janvier 2024.
- Lien : https://arxiv.org/abs/2401.18059
- Resume : Papier de reference sur le retrieval hierarchique. Les chunks sont regroupes, resumes, puis organises en arbre pour permettre une recherche a plusieurs niveaux d'abstraction. Tres utile pour les syntheses, mais les resumes posent un enjeu de mise a jour.
- Niveau de confiance : eleve.

## 8. Weaviate Hybrid Search documentation

- Auteur / organisme : Weaviate.
- Date : documentation consultee en juillet 2026.
- Lien : https://docs.weaviate.io/weaviate/concepts/search/hybrid-search
- Resume : Explique clairement la combinaison vector search + BM25 et les strategies de fusion. Source pratique pour justifier le retrieval hybride comme premiere amelioration d'un RAG. Weaviate est juge et partie, mais la documentation technique est precise.
- Niveau de confiance : eleve.

## 9. Qdrant Hybrid Queries documentation

- Auteur / organisme : Qdrant.
- Date : documentation consultee en juillet 2026.
- Lien : https://qdrant.tech/documentation/search/hybrid-queries/
- Resume : Decrit les requetes multi-stage et hybrides avec prefetch dense/sparse puis fusion. Source utile car elle montre comment industrialiser le melange de representations dans un moteur vectoriel moderne.
- Niveau de confiance : eleve.

## 10. Elasticsearch Reciprocal Rank Fusion

- Auteur / organisme : Elastic.
- Date : documentation consultee en juillet 2026.
- Lien : https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- Resume : Decrit RRF comme methode de fusion de resultats avec indicateurs de pertinence differents. Tres utile pour expliquer pourquoi on peut combiner BM25 et vecteur sans calibrer parfaitement leurs scores.
- Niveau de confiance : eleve.

## 11. Cohere Reranking documentation

- Auteur / organisme : Cohere.
- Date : documentation consultee en juillet 2026.
- Lien : https://docs.cohere.com/docs/reranking-with-cohere
- Resume : Documentation officielle des rerankers Cohere. Elle illustre le schema retrieve puis rerank, pertinent pour reclasser des candidats issus d'un retrieval hybride. Source commerciale, donc prudence sur les performances annoncees.
- Niveau de confiance : moyen a eleve.

## 12. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection

- Auteur / organisme : Akari Asai et al.
- Date : 17 octobre 2023.
- Lien : https://arxiv.org/abs/2310.11511
- Resume : Papier important pour le RAG agentique/reflexif. Le modele apprend a decider quand retrouver, generer et critiquer. Un peu plus ancien que 2024, mais toujours central pour comprendre l'evolution vers retrieval adaptatif.
- Niveau de confiance : eleve.

## 13. Corrective Retrieval Augmented Generation

- Auteur / organisme : Shi-Qi Yan et al.
- Date : 29 janvier 2024.
- Lien : https://arxiv.org/abs/2401.15884
- Resume : Propose un evaluateur de retrieval qui decide si les documents retrouves sont fiables, ambigus ou insuffisants, puis corrige la recherche. Tres pertinent pour un assistant juridique, ou un mauvais top-k peut produire une reponse dangereuse.
- Niveau de confiance : eleve.

## 14. Building effective agents

- Auteur / organisme : Anthropic.
- Date : 19 decembre 2024.
- Lien : https://www.anthropic.com/engineering/building-effective-agents
- Resume : Source de reference pragmatique sur workflows vs agents. Anthropic recommande de rester simple et de n'ajouter de l'agentique que si le gain justifie cout, latence et complexite. Tres utile pour eviter l'effet de mode.
- Niveau de confiance : eleve.

## 15. Prompt caching - Claude docs

- Auteur / organisme : Anthropic.
- Date : documentation consultee en juillet 2026.
- Lien : https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Resume : Explique le fonctionnement du cache de prompt, ses cas d'usage et sa tarification. Pertinent pour les architectures long context ou des corpus identiques sont relus souvent. Source fournisseur, donc fiable sur le fonctionnement de Claude, pas generalisable a tous les modeles.
- Niveau de confiance : eleve.

## 16. Lost in the Middle: How Language Models Use Long Contexts

- Auteur / organisme : Nelson F. Liu et al.
- Date : 6 juillet 2023.
- Lien : https://arxiv.org/abs/2307.03172
- Resume : Montre que les LLMs n'utilisent pas toujours correctement les informations situees au milieu d'un long contexte. La source est plus ancienne, mais reste importante car elle nuance l'idee "il suffit de tout mettre dans le prompt".
- Niveau de confiance : eleve.

## 17. Graphiti GitHub

- Auteur / organisme : Zep / getzep.
- Date : depot consulte en juillet 2026.
- Lien : https://github.com/getzep/graphiti
- Resume : Presente Graphiti comme moteur de graphes temporels pour agents, avec validite temporelle, provenance, mises a jour incrementales et retrieval hybride. Tres pertinent pour la fraicheur juridique et l'historique des articles.
- Niveau de confiance : moyen a eleve.

## 18. Zep: A Temporal Knowledge Graph Architecture for Agent Memory

- Auteur / organisme : Preston Rasmussen et al.
- Date : 20 janvier 2025.
- Lien : https://arxiv.org/abs/2501.13956
- Resume : Papier sur Zep et Graphiti comme architecture de memoire temporelle. Il presente des resultats sur memoire longue et raisonnement temporel. Comme les auteurs sont lies a l'outil, je garde de la prudence sur les chiffres.
- Niveau de confiance : moyen.

## 19. Cognee GitHub

- Auteur / organisme : Topoteretes / Cognee.
- Date : depot consulte en juillet 2026.
- Lien : https://github.com/topoteretes/cognee
- Resume : Presente Cognee comme plateforme open source de memoire long terme pour agents, avec knowledge graph auto-heberge, embeddings et recherche. Utile pour comparer Graphiti et Cognee dans les architectures memoire.
- Niveau de confiance : moyen a eleve.

## 20. Optimizing the Interface Between Knowledge Graphs and LLMs for Complex Reasoning

- Auteur / organisme : Vasilije Markovic et al.
- Date : 30 mai 2025.
- Lien : https://arxiv.org/abs/2505.24478
- Resume : Papier lie a Cognee qui montre que les performances des systemes KG + LLM dependent fortement de nombreux hyperparametres : chunking, construction du graphe, retrieval, prompting. Bon rappel que ces architectures demandent une vraie evaluation.
- Niveau de confiance : moyen.

## 21. Neo4j RAG tutorial

- Auteur / organisme : Tomaž Bratanič, Neo4j.
- Date : 22 aout 2025.
- Lien : https://neo4j.com/blog/developer/rag-tutorial/
- Resume : Tutoriel sur RAG avec knowledge graph et vector search. Il insiste sur l'explicabilite, les requetes structurees et les limites du vector-only RAG. Source utile pour les patterns, mais c'est aussi une source editeur.
- Niveau de confiance : moyen a eleve.
