# Etudes de cas - Recommandations d'architecture

## 1. Cabinet juridique

### Recommandation

Je recommanderais une architecture hybride : BM25 + vector search + filtres de metadonnees + RRF + reranker, avec une couche optionnelle GraphRAG limitee aux relations entre dossiers, parties, notions juridiques et jurisprudences.

### Justification technique

Le besoin prioritaire est la tracabilite. Les juristes posent des questions precises avec references exactes : numero d'article, nom de decision, clause, date, partie, juridiction. Un systeme purement vectoriel est trop fragile pour ces correspondances exactes. BM25 retrouve les references, le vectoriel aide quand la question est reformulee, RRF fusionne les deux, et le reranker classe les meilleurs passages.

La fraicheur est centrale : corpus mis a jour chaque semaine. L'architecture doit filtrer sur date de validite, etat du document, version, source et date d'ingestion. C'est exactement ce qu'on a commence a faire dans notre assistant Code du travail avec `etat=VIGUEUR`, `date_debut`, `date_fin`, `legi_id` et `source_file`.

### Pourquoi les autres approches sont moins adaptees

GraphRAG complet peut etre utile, mais je ne le mettrais pas en socle car son cout d'indexation et de maintenance est eleve sur un corpus mis a jour chaque semaine. RAPTOR risque de resumer trop fortement des nuances juridiques. Le RAG agentique peut aider pour les recherches complexes, mais il doit rester encadre, car les juristes ont besoin de reponses stables. Long context seul n'est pas suffisant : il coute cher, ne garantit pas la selection du bon passage et rend la tracabilite moins propre.

## 2. Analyste d'investigation

### Recommandation

Je recommanderais GraphRAG ou GraphRAG agentique, avec knowledge graph temporel. Les entites principales seraient personnes, organisations, lieux, dates, evenements, documents, communications et relations. L'agent aurait des outils limites : recherche de voisins, chemins entre entites, timeline, recherche textuelle source, verification de preuves.

### Justification technique

Le cas est presque fait pour le graphe : "qui est lie a qui, qui a rencontre qui et quand" est une question relationnelle et multi-sauts. Un top-k vectoriel risque de retrouver des emails proches de la question sans reconstruire le reseau. Un graphe permet de parcourir les chemins, d'identifier des communautes, de visualiser les connexions et de justifier une conclusion par des documents sources.

La dimension temporelle est importante. Graphiti ou une approche inspiree de Graphiti serait pertinente pour distinguer "relation vraie a telle date" et "relation actuelle". En investigation, l'historique n'est pas un bruit : c'est souvent le coeur de l'analyse.

### Pourquoi les autres approches sont moins adaptees

Le retrieval hybride reste utile comme composant, mais insuffisant seul pour raisonner sur des chaines de relations. RAPTOR peut donner des syntheses de lots de documents, mais il ne donne pas naturellement des chemins d'entites. Long context peut aider sur un dossier court, mais devient vite couteux et peu lisible. Un agent sans graphe aurait tendance a multiplier les recherches textuelles sans structure durable.

## 3. Startup support

### Recommandation

Je recommanderais un RAG hybride simple : BM25 + vector search, filtres de version/date, reranker seulement si le budget le permet. Pas de GraphRAG au depart. L'objectif est de livrer vite, mesurer, puis ameliorer.

### Justification technique

Le corpus est petit : 300 pages de documentation. L'equipe est reduite, le budget minimal et la documentation change tous les jours. Il faut donc une architecture facile a reconstruire ou a mettre a jour automatiquement. Le retrieval hybride couvre les noms de fonctionnalites, erreurs, codes produit et formulations utilisateur. On peut ajouter un cache pour les questions frequentes.

La fraicheur doit etre geree par ingestion incrementale : `last_updated`, `version_doc`, `produit`, `langue`, `url_source`, et suppression ou desactivation des pages obsoletes. Le cas ressemble a notre projet LEGI sur la logique de fraicheur, mais avec un rythme quotidien et un corpus plus petit.

### Pourquoi les autres approches sont moins adaptees

GraphRAG est trop cher et trop long pour trois semaines. RAPTOR ajoute des resumes a maintenir tous les jours. Le RAG agentique augmente latence et cout alors que la plupart des questions support sont simples. Long context pourrait marcher si la documentation tient dans le contexte, mais il serait moins propre pour citer les pages et plus couteux a grande echelle.

## Synthese des recommandations

| Cas | Architecture recommandee | Raison principale |
|---|---|---|
| Cabinet juridique | Retrieval hybride + reranker + metadonnees, GraphRAG cible en option | Exactitude, references, fraicheur, tracabilite |
| Analyste d'investigation | GraphRAG temporel + agent encadre | Multi-hop, entites, relations, temporalite |
| Startup support | RAG hybride simple + ingestion quotidienne | Delai court, budget faible, documentation mouvante |
