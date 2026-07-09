# Restitution orale - 10 minutes

## Objectif de l'oral

Mon objectif n'est pas de reciter cinq definitions. Je veux montrer que je sais choisir une architecture selon un besoin : type de question, cout, fraicheur, tracabilite et maturite.

## Plan minute par minute

### 0:00 - 1:00 - Introduction

Dire : "Le RAG classique reste une bonne base, mais il a quatre limites : questions multi-sauts, questions globales, references exactes et contexte fige."

Transition : "Les cinq approches que j'ai etudiees ne remplacent pas toutes le RAG ; elles corrigent chacune une faiblesse precise."

### 1:00 - 2:20 - GraphRAG

Idees principales :

- On construit un graphe : entites, relations, communautes, resumes.
- Fort pour relier des informations et comprendre un corpus globalement.
- Cout d'indexation eleve, surtout avec extraction LLM et resumes.
- Variantes plus recentes : LazyGraphRAG et LightRAG cherchent a reduire ce cout.

Lien projet : utile plus tard si on ajoute jurisprudence, conventions collectives ou relations entre notions.

Transition : "Si le graphe modelise les relations, RAPTOR choisit plutot de modeliser les niveaux de resume."

### 2:20 - 3:30 - RAPTOR

Idees principales :

- Arbre de chunks et de resumes.
- Repond bien aux questions globales ou semi-globales.
- Plus simple qu'un graphe, mais les resumes peuvent perdre des nuances.
- Les mises a jour sont sensibles : si un article change, les resumes parents peuvent devenir faux.

Lien projet : utile pour des syntheses par theme, mais pas comme source juridique finale.

Transition : "Avant ces architectures complexes, l'amelioration la plus pragmatique est souvent le retrieval hybride."

### 3:30 - 5:00 - Retrieval hybride

Idees principales :

- BM25 pour les mots exacts, vecteur pour le sens, RRF pour fusionner, reranker pour reclasser.
- Tres fort sur references exactes : articles de loi, sigles, codes produits.
- Compatible avec metadonnees : version, date, source, theme.
- Cout raisonnable et maturite forte.

Lien projet : c'est mon choix prioritaire pour l'assistant Code du travail, car on doit retrouver `L3121-1` exactement et filtrer `etat=VIGUEUR`.

Transition : "Quand une seule recherche ne suffit plus, on peut donner des outils a un agent."

### 5:00 - 6:20 - RAG agentique

Idees principales :

- L'agent cherche, evalue, reformule, relance et croise plusieurs sources.
- Utile pour questions complexes.
- Cout, latence et non-determinisme plus eleves.
- Il faut des garde-fous et des outils bien definis.

Lien projet : un agent juridique pourrait appeler `search_article`, `search_theme`, `compare_articles`, `verify_current_version`.

Transition : "Derniere piste : et si on mettait beaucoup plus de contexte, ou une memoire durable ?"

### 6:20 - 7:40 - Long context, cache, memoire

Idees principales :

- Long contexte utile pour dossiers courts ou repetes.
- Prompt caching reduit cout et latence quand le prefixe est identique.
- Attention au probleme "lost in the middle".
- Graphiti et Cognee ajoutent une memoire graphe, parfois temporelle.

Lien projet : Graphiti est conceptuellement interessant pour l'historique des versions LEGI : "vrai maintenant" vs "vrai a une date donnee".

Transition : "Pour finir, j'applique cette grille aux trois cas."

### 7:40 - 9:20 - Trois etudes de cas

Cabinet juridique :

- Choix : hybride + reranker + metadonnees, GraphRAG cible en option.
- Raison : references exactes, tracabilite, corpus mis a jour chaque semaine.

Analyste d'investigation :

- Choix : GraphRAG temporel + agent encadre.
- Raison : presque toutes les questions sont multi-sauts et relationnelles.

Startup support :

- Choix : RAG hybride simple.
- Raison : petit corpus, budget faible, delai de trois semaines, mises a jour quotidiennes.

Transition : "La conclusion est donc moins spectaculaire qu'un buzzword, mais plus utile architecturalement."

### 9:20 - 10:00 - Conclusion

Conclusion :

"Le RAG n'est pas mort. Il devient une brique d'un systeme de contexte plus large. Mon choix depend du risque : dans un projet juridique, je privilegie d'abord retrieval hybride, metadonnees de fraicheur et citations. Les graphes et agents viennent ensuite, seulement quand les questions exigent des relations ou plusieurs etapes."

Phrase finale possible :

"Pour notre assistant Code du travail, la prochaine evolution raisonnable serait donc : recherche hybride avec filtres juridiques, reranker, puis eventuellement graphe temporel si on doit gerer l'historique des versions ou croiser avec la jurisprudence."

## Questions possibles du professeur

### Pourquoi ne pas choisir GraphRAG directement pour le Code du travail ?

Parce que notre corpus actuel est deja structure par articles et metadonnees. Le besoin prioritaire est de retrouver le bon article en vigueur, pas de construire un graphe couteux. GraphRAG deviendra plus pertinent avec jurisprudence, conventions collectives ou questions multi-hop.

### Pourquoi l'hybride est-il meilleur que le vectoriel seul ?

Parce qu'en droit, les references exactes sont critiques. Un article `L3121-1` ne doit pas etre "a peu pres" retrouve par similarite. BM25 capte l'exact, le vectoriel capte la reformulation.

### Pourquoi le long context ne suffit pas ?

Parce qu'il coute cher, n'assure pas toujours que le modele utilise la bonne information, et rend la tracabilite plus difficile. Dans un contexte juridique, je prefere recuperer moins de passages, mais mieux justifies et cites.
