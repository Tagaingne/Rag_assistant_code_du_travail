# Note de synthese - Au-dela du RAG classique

Projet de reference : assistant RAG sur le Code du travail, corpus LEGI extrait en XML, 812 articles en vigueur, avec `date_debut`, `date_fin`, `etat`, `legi_id` et source XML. Mon point de depart est donc un RAG juridique : la precision des references, la fraicheur des articles et la tracabilite comptent autant que la qualite de la generation.

## 1. GraphRAG

Le principe de GraphRAG est de ne plus indexer seulement des chunks independants. On extrait des entites, des relations et parfois des "claims" depuis les documents, puis on construit un graphe de connaissances. Dans l'approche Microsoft GraphRAG, le graphe est ensuite groupe en communautes, qui sont resumees pour repondre aux questions globales. Microsoft decrit un processus avec extraction d'entites et relations, clustering hierarchique et resumes de communautes, puis modes de recherche globale, locale et DRIFT [Microsoft GraphRAG docs](https://microsoft.github.io/graphrag/). Le papier Microsoft de 2024 cible surtout les questions de "sensemaking" sur un corpus entier, la ou un top-k vectoriel retrouve des passages proches mais pas une vue d'ensemble [arXiv 2404.16130](https://arxiv.org/abs/2404.16130).

La limite du RAG classique adressee est double : les questions multi-sauts et les questions globales. Pour un corpus juridique, cela peut servir a relier des notions comme temps de travail, repos, astreinte, sanctions, convention collective et jurisprudence. Sur notre corpus Code du travail, l'interet serait moins de remplacer la recherche par article que de construire une couche de relations entre articles, notions et themes.

Ses avantages sont la capacite a expliciter les liens, a remonter des chaines de relations et a produire une vue globale d'un corpus. L'inconvenient principal est le cout de construction : extraction LLM sur tout le corpus, resolution d'entites, clustering, resumes et maintenance du graphe. Microsoft avertit d'ailleurs que l'indexation GraphRAG peut etre couteuse [GitHub Microsoft GraphRAG](https://github.com/microsoft/graphrag). LazyGraphRAG attaque ce probleme en evitant une partie des summaries LLM a l'indexation et en deplacant davantage de travail au moment de la requete [Microsoft Research LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/). LightRAG propose aussi une version plus legere avec graphe, double niveau de retrieval et mises a jour incrementales [LightRAG arXiv](https://arxiv.org/abs/2410.05779).

Mon avis d'architecte : je ne commencerais pas notre assistant Code du travail par GraphRAG complet. Pour 812 articles, l'urgence est d'abord un retrieval hybride robuste avec filtres de metadonnees. En revanche, GraphRAG deviendrait tres pertinent si on ajoute jurisprudence, conventions collectives, questions multi-hop ou analyse de coherence entre textes.

## 2. Retrieval hierarchique - RAPTOR

RAPTOR construit un arbre de resumes. Les chunks sont regroupes par similarite, chaque groupe est resume, puis les resumes sont eux-memes regroupes et resumes. A la requete, on peut interroger a plusieurs niveaux : feuilles pour le detail, noeuds plus hauts pour la synthese. Le papier RAPTOR montre que cette structure vise les limites des RAG qui ne recuperent que des passages courts et perdent le contexte global [RAPTOR arXiv](https://arxiv.org/abs/2401.18059).

La limite adressee est surtout la question globale ou semi-globale : "quelles sont les grandes obligations de l'employeur sur les conges payes ?" n'est pas toujours servie par un seul article. RAPTOR est proche du parent-child chunking vu en cours, mais avec une couche de resumes generes automatiquement et empiles.

Les avantages : meilleure navigation entre detail et synthese, architecture plus simple qu'un graphe, pas besoin de modeliser explicitement toutes les relations. Les inconvenients : les resumes peuvent lisser des nuances juridiques, introduire des erreurs, et doivent etre regeneres quand les documents changent. Pour un corpus legal vivant, la fraicheur devient un vrai sujet : si un article change, il faut savoir quels resumes parents invalider.

Cout de construction : moyen a eleve, car il faut embeddings, clustering et generation de resumes. Cout a l'utilisation : moyen, car on interroge une structure plus riche mais sans boucle agentique lourde. Maturite : recherche solide depuis 2024, mais moins standardisee dans les stacks de production que BM25 + vecteur + reranker.

Mon avis : interessant pour faire des syntheses par theme dans notre projet, par exemple "resume des regles sur la duree du travail". Mais je l'utiliserais uniquement avec citations vers les articles sources, jamais comme source juridique autonome.

## 3. Retrieval hybride - BM25 + vecteur + fusion + reranker

Le retrieval hybride combine recherche lexicale et recherche semantique. BM25 excelle sur les references exactes, sigles et termes rares ; le vectoriel retrouve les formulations proches meme si les mots changent. Les resultats peuvent etre fusionnes avec des scores normalises, du rank fusion ou du Reciprocal Rank Fusion. Elasticsearch decrit RRF comme une methode de combinaison de classements sans que les indicateurs de pertinence soient comparables entre eux [Elasticsearch RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion). Weaviate documente la combinaison BM25 + vector search avec strategies de fusion [Weaviate Hybrid Search](https://docs.weaviate.io/weaviate/concepts/search/hybrid-search). Qdrant expose des requetes hybrides avec prefetch dense/sparse et fusion [Qdrant Hybrid Queries](https://qdrant.tech/documentation/search/hybrid-queries/). Un reranker, par exemple Cohere Rerank, reordonne ensuite les candidats selon la question [Cohere Rerank docs](https://docs.cohere.com/docs/reranking-with-cohere).

La limite adressee est tres concrete : le RAG vectoriel rate parfois les correspondances exactes. Dans notre cas, une question comme "Que dit l'article L3121-1 ?" doit absolument trouver `L3121-1`, pas un article semantiquement proche. L'hybride permet aussi de filtrer sur `etat=VIGUEUR`, `theme`, `date_debut` ou `date_fin`, ce qui rejoint directement notre jalon 1.

Avantages : pragmatique, mature, facile a evaluer, tres compatible avec la tracabilite. Inconvenients : il ne resout pas seul les questions multi-hop profondes ou les syntheses globales. Le cout de construction est faible a moyen ; le cout par requete est faible si on s'arrete a BM25 + vecteur, moyen si on ajoute un reranker payant.

Mon avis : c'est la premiere amelioration que je recommanderais pour notre assistant Code du travail. Avant GraphRAG ou agent, il faut une base solide : recherche exacte d'articles, recherche semantique, filtres de fraicheur, puis reranking.

## 4. RAG agentique

Le RAG agentique transforme la recherche en boucle. Au lieu d'un pipeline fixe "query -> top-k -> generation", un LLM outille decide quoi chercher, evalue les resultats, reformule, relance une recherche, consulte plusieurs outils et s'arrete quand il estime avoir assez d'elements. Anthropic distingue les workflows, avec chemins fixes, des agents, ou le modele decide dynamiquement des outils et des etapes [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents). Self-RAG introduit retrieval et critique par auto-reflexion [Self-RAG arXiv](https://arxiv.org/abs/2310.11511). Corrective RAG ajoute un evaluateur de retrieval qui declenche des actions correctives si les documents retrouves sont mauvais [CRAG arXiv](https://arxiv.org/abs/2401.15884).

La limite adressee est le contexte fige : le RAG classique ne sait pas se corriger si le top-k est mauvais. Un agent peut faire une recherche exacte par article, puis une recherche par theme, puis verifier la date de validite, puis produire une reponse citee.

Avantages : flexible, bon pour les questions complexes, possibilite d'utiliser des outils metier. Inconvenients : latence, cout, non-determinisme, evaluation plus difficile et risque de trajectoires inutiles. Dans le juridique, il faut absolument borner l'agent : pas de recherche libre non tracee, pas de reponse sans sources, nombre d'iterations limite.

Mon avis : utile en couche avancee, pas en socle. Pour notre projet, je donnerais a l'agent des outils simples : `search_article(reference)`, `search_theme(theme)`, `filter_current_versions()`, `compare_articles()`, `show_sources()`. Je ne lui donnerais pas directement le droit de "raisonner sur tout" sans garde-fous.

## 5. Long context, cache et memoire - Graphiti, Cognee

Les grands contextes et le prompt caching changent le compromis. On peut parfois mettre beaucoup de contexte dans le prompt, surtout si le corpus est petit ou si les memes documents reviennent souvent. Anthropic decrit le prompt caching comme un mecanisme qui reutilise un prefixe identique pour reduire temps et cout, utile pour beaucoup de contexte, exemples ou conversations longues [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching). Mais cela ne supprime pas le probleme de selection : les modeles long context peuvent encore mal utiliser l'information placee au milieu du contexte, phenomene documente par "Lost in the Middle" [arXiv 2307.03172](https://arxiv.org/abs/2307.03172).

Les systemes de memoire comme Graphiti et Cognee ajoutent une autre idee : construire une memoire evolutive, souvent sous forme de graphe temporel. Graphiti gere des faits avec fenetres de validite, provenance et mises a jour incrementales [Graphiti GitHub](https://github.com/getzep/graphiti). Le papier Zep presente Graphiti comme un moteur de graphe temporel pour la memoire agentique [Zep arXiv](https://arxiv.org/abs/2501.13956). Cognee se presente comme une plateforme open source de memoire long terme avec knowledge graph auto-heberge [Cognee GitHub](https://github.com/topoteretes/cognee).

La limite adressee est le caractere statique du RAG classique. Pour notre corpus juridique, Graphiti est conceptuellement proche de notre exigence de fraicheur : garder ce qui est vrai maintenant, mais aussi ce qui etait vrai avant. Aujourd'hui nous ignorons les anciennes versions ; demain, une memoire temporelle pourrait permettre "quelle version etait applicable au 1er janvier 2022 ?".

Mon avis : long context seul n'est pas une architecture juridique suffisante, car il fragilise la tracabilite et coute cher si on injecte trop. Prompt caching peut aider en lecture repetee d'un petit corpus. La memoire temporelle est tres prometteuse pour l'historique legal, mais plus complexe que le besoin minimal du jalon 1.

## Position finale

Je ne pense pas que le RAG soit obsolete. Il devient plutot une brique d'un etage contexte plus large : retrieval hybride pour la robustesse, graphes pour les relations, hierarchie pour les syntheses, agents pour les recherches multi-etapes, cache et memoire pour les usages repetes ou temporels. Pour notre assistant Code du travail, ma trajectoire serait : hybride + metadonnees d'abord ; reranker ensuite ; puis, si le corpus s'etend a jurisprudence et conventions collectives, GraphRAG ou graphe temporel.
