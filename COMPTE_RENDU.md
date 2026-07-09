# Compte rendu — Assistant Code du travail (RAG)

## Difficultés rencontrées

**Intégration entre parties développées en parallèle.** Le travail était réparti par jalons sur des branches séparées (corpus, chunking/indexation, génération/interface). À la fusion, `src/config.py` a été écrasé plutôt que fusionné (constantes du jalon 2/3 disparues), les deux parties utilisaient des styles d'import incompatibles (`sys.path.insert` vs imports de package), un module `VectorDB` attendu par la génération n'avait jamais été livré, et un bug silencieux faisait utiliser le modèle de génération à la place du modèle de modération dédié. Résolu via une branche `fix/integration` dédiée, avec un adaptateur (`VectorDB`) réutilisant les classes existantes plutôt que d'en dupliquer la logique.

**Bug de chunking sur les références de loi.** Le découpage par phrases coupait à tort après les abréviations d'article (« L. 1233-63 »), produisant des chunks commençant en plein milieu d'une énumération. Trouvé par relecture manuelle des chunks (contrôle qualité imposé au jalon 2), corrigé en exigeant qu'une majuscule suive la ponctuation pour valider une coupure.

**Choix du modèle d'embedding sous-estimé au départ.** Trois modèles comparés en conditions réelles sur 5 questions de test : `paraphrase-multilingual-MiniLM` (2/5), `distiluse-base-multilingual` (4/5), `multilingual-e5-base` (5/5, retenu). Le premier choix, recommandé par défaut, était nettement insuffisant pour discriminer des articles juridiques lexicalement proches.

**Bugs révélés uniquement en usage réel.** Les tests automatisés (jeu de 5 questions, suite de tests avec chunks factices) ne suffisaient pas : en utilisant l'interface dans le navigateur, on a découvert des sources non pertinentes affichées sur des messages hors-sujet (« hello »), un refus alors que l'information existait (un article long redécoupé polluait le top-k avec des doublons, évinçant le bon article), et HyDE qui dégradait le retrieval sur les questions chiffrées (le prompt interdit volontairement d'inventer des chiffres précis, ce qui éloigne sémantiquement le texte hypothétique de l'article donnant la réponse exacte).

**Quota Groq (tier gratuit).** Le test de 45 questions de challenge a épuisé le quota quotidien (100 000 tokens/jour) après une dizaine de questions ; changer de clé API n'a rien débloqué, la nouvelle clé appartenant à la même organisation. Le test complet n'a pas pu être terminé.

**Setup Docker non finalisé.** Docker Desktop est resté bloqué en démarrage plus de 10 minutes sur la machine de développement ; le `Dockerfile`/`docker-compose.yml` sont écrits et syntaxiquement valides mais le build n'a jamais pu être validé de bout en bout.

## Décisions de conception

- **Chunking par article**, jamais par section : traçabilité prioritaire (un chunk = un numéro d'article citable sans ambiguïté), avec découpage secondaire uniquement pour les articles dépassant 1500 caractères (seuil calibré sur le corpus réel, pas arbitraire).
- **Traçabilité en trois couches** : métadonnées comme source de vérité, prompt strict interdisant toute connaissance hors contexte, et vérification post-génération (extraction des numéros d'articles réellement cités dans la réponse, sources affichées filtrées en conséquence) — ce filet de sécurité, initialement documenté sans être implémenté, a été construit après avoir observé le bug des sources non pertinentes.
- **Agent formateur de question en trois étapes** (nettoyage par règles, décomposition LLM, HyDE), avec recherche combinant systématiquement la sous-question brute et sa version HyDE plutôt que HyDE seul, pour ne pas sacrifier les questions factuelles chiffrées.
- **Agent récupérateur de référence (API Légifrance)** en complément optionnel et non bloquant du corpus statique : vérifie en direct si un article cité est toujours à jour, sans jamais faire échouer la génération si l'API est indisponible ou non configurée.
- **Workflow Git strict** : une branche par fonctionnalité, jamais de commit direct sur `main`/`dev`, pull request systématique — y compris pour les correctifs d'intégration entre jalons.

## Ce que nous ferions avec plus de temps

- Implémenter l'historique de conversation, déjà nécessaire architecturalement du fait du choix de clarification active (Q4).
- Ajouter une recherche hybride (BM25 + vectoriel) pour rattraper un cas confirmé en test réel : une question citant un numéro d'article exact (« que dit L3121-1 ? ») échoue en recherche purement sémantique alors que l'article existe dans le corpus.
- Terminer et valider réellement le déploiement Docker.
- Finir le test de challenge (45 questions) avec un compte Groq séparé ou un tier payant.
- Afficher la date de fraîcheur du corpus dans chaque réponse (le champ existe déjà en métadonnées mais n'était jamais lu par les interfaces).
- Automatiser la réindexation périodique : aujourd'hui, toute évolution du Code du travail nécessite un re-téléchargement et une reconstruction manuelle complète de la base, sans mécanisme incrémental ni historique des changements.
