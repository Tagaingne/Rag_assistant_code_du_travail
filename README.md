# Assistant Code du travail

Ce projet construit progressivement un assistant RAG sur le Code du travail francais.

## Source des donnees

Le corpus du projet provient de la base LEGI disponible sur data.gouv.fr. Cette base contient les textes juridiques francais, dont les codes, au format XML.

Pour le jalon 1, l'option retenue est l'option B du sujet : utiliser les fichiers XML de la base LEGI et les parser avec la bibliotheque standard Python, notamment `xml.etree.ElementTree`.

Les fichiers XML telecharges depuis la base LEGI doivent etre places dans le dossier suivant :

```text
data/raw/legi/
```

Le projet ne telecharge pas automatiquement l'archive LEGI complete, car elle peut etre volumineuse. Il faut donc recuperer les fichiers utiles depuis data.gouv.fr, les extraire localement, puis les placer dans `data/raw/legi/` avant de lancer les scripts de preparation.

## Jalon 1 - Preparation des donnees LEGI

### Pourquoi l'option B

L'option B est retenue parce qu'elle donne un corpus officiel, public et structure sans dependre d'une API au moment de l'indexation. Les fichiers XML de la base LEGI permettent d'extraire les articles avec leurs metadonnees et de garder une trace du fichier source.

Cette option est un bon compromis pour le projet : elle est plus robuste qu'un corpus copie manuellement, mais elle reste developpable avec la bibliotheque standard Python.

### Role des dossiers

`data/raw/legi/` contient les fichiers XML bruts issus de la base LEGI. Ces fichiers peuvent etre volumineux et ne doivent pas etre ajoutes au depot Git.

`data/processed/` contient les fichiers propres generes par les scripts, notamment :

```text
data/processed/corpus_legi_clean.json
```

### Scripts disponibles

`src/data/explore_legi_xml.py` parcourt recursivement `data/raw/legi/`, lit les fichiers `.xml`, compte les balises rencontrees et affiche quelques exemples de texte. Il sert a comprendre la structure LEGI avant l'extraction.

`src/data/extract_legi_corpus.py` parcourt recursivement `data/raw/legi/`, extrait les articles correspondant aux themes demandes du Code du travail, nettoie le texte et genere un JSON homogene.

### Commandes

Explorer les XML :

```bash
python src/data/explore_legi_xml.py
```

Generer le corpus propre :

```bash
python src/data/extract_legi_corpus.py
```

### Themes filtres

Le script filtre les articles par plages pour couvrir les themes du sujet :

- Duree du travail et heures supplementaires : `L3121-1` a `L3121-36`
- Conges payes : `L3141-1` a `L3141-32`
- Contrat de travail CDI/CDD : `L1221-1` a `L1248-11`
- Licenciement : `L1231-1` a `L1237-20`
- Rupture conventionnelle : `L1237-11` a `L1237-19`
- Salaire minimum SMIC : `L3231-1` a `L3232-9`
- Representation du personnel : `L2311-1` a `L2316-26`
- Harcelement et discrimination : `L1152-1` a `L1155-2`

La rupture conventionnelle est testee avant la plage plus large du licenciement afin de conserver ce theme specifique.

### Champs du JSON final

Chaque document extrait a la structure suivante :

```json
{
  "id": "legi_L3121-1",
  "article": "L3121-1",
  "theme": "Duree du travail et heures supplementaires",
  "title": "Article L3121-1",
  "text": "Texte nettoye de l'article...",
  "content": "Article L3121-1\nTheme : ...\nTitre : ...\nTexte : ...",
  "source": "LEGI data.gouv.fr",
  "source_file": "data/raw/legi/...",
  "date_extraction": "YYYY-MM-DD"
}
```

Le champ `content` est prepare pour la suite du projet : il rassemble l'article, le theme, le titre et le texte dans une seule chaine qui pourra etre indexee plus tard.

### Controles qualite

Le script verifie :

- aucun id vide ;
- aucun numero d'article vide ;
- aucun texte vide ;
- aucun doublon d'article ;
- au moins 5 themes extraits ;
- affichage du nombre total d'articles ;
- affichage du nombre d'articles par theme ;
- affichage de 5 exemples nettoyes.

### Limites actuelles

Le depot ne contient pas encore les fichiers XML LEGI. Tant que `data/raw/legi/` ne contient que `.gitkeep`, la generation de `data/processed/corpus_legi_clean.json` echoue volontairement avec un message clair.

Le jalon 1 ne fait pas encore de chunking avance, pas d'embeddings, pas de base vectorielle, pas de recherche et pas d'appel LLM. LangChain et LlamaIndex ne sont pas utilises.
