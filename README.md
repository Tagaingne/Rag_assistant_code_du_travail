# Assistant Code du travail

Ce projet construit progressivement un assistant RAG sur le Code du travail francais.

## Source des donnees

Le corpus du projet provient de la base LEGI disponible sur data.gouv.fr. Cette base contient les textes juridiques francais, dont les codes, au format XML.

Pour le jalon 1, l'option retenue est l'option B du sujet : utiliser les fichiers XML de la base LEGI et les parser avec la bibliotheque standard Python, notamment `xml.etree.ElementTree`.

Les fichiers XML utiles extraits depuis la base LEGI doivent etre places dans le dossier suivant :

```text
data/raw/legi/
```

Le projet ne telecharge pas automatiquement l'archive LEGI complete, car elle peut etre volumineuse. Si l'archive complete a deja ete telechargee, le script `src/data/extract_code_travail_from_archive.py` permet de la lire directement sans tout decompresser et d'extraire uniquement les XML utiles au jalon 1 dans `data/raw/legi/`.

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

`src/data/extract_code_travail_from_archive.py` lit une archive `.tar.gz` LEGI avec `tarfile`, parcourt les entrees sans extraction globale, repere les XML du Code du travail (`LEGITEXT000006072050`) et extrait seulement les articles des plages demandees dans `data/raw/legi/`.

`src/data/explore_legi_xml.py` parcourt recursivement `data/raw/legi/`, lit les fichiers `.xml`, compte les balises rencontrees et affiche quelques exemples de texte. Il sert a comprendre la structure LEGI avant l'extraction.

`src/data/extract_legi_corpus.py` parcourt recursivement `data/raw/legi/`, extrait les articles correspondant aux themes demandes du Code du travail, nettoie le texte et genere un JSON homogene.

### Commandes

Extraire les XML utiles depuis l'archive complete sans tout decompresser :

```bash
python src/data/extract_code_travail_from_archive.py "C:/Users/33785/Downloads/Freemium_legi_global_20250713-140000.tar.gz"
```

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

Les plages specifiques sont testees avant la plage plus large du contrat de travail. La rupture conventionnelle est aussi testee avant la plage plus large du licenciement afin de conserver ce theme specifique.

### Fraicheur juridique des donnees

Le Code du travail evolue dans le temps. Un meme article peut donc exister sous plusieurs versions successives dans LEGI. Pour eviter de repondre avec une version obsolescente, le pipeline conserve uniquement la version juridiquement en vigueur de chaque article.

La selection repose sur les metadonnees LEGI :

- `ETAT` doit etre egal a `VIGUEUR` ;
- `DATE_DEBUT` doit etre anterieure ou egale a la date d'extraction ;
- `DATE_FIN` doit etre posterieure a la date d'extraction, generalement `2999-01-01` pour une version sans fin connue ;
- si plusieurs versions courantes existent pour le meme numero d'article, la version avec la date d'entree en vigueur la plus recente est conservee.

Les anciennes versions sont ignorees dans le corpus final. Elles ne sont pas stockees dans un historique separe pour le jalon 1.

### Champs du JSON final

Chaque document extrait a la structure suivante :

```json
{
  "id": "legi_L3121-1",
  "article": "L3121-1",
  "theme": "Duree du travail et heures supplementaires",
  "title": "Article L3121-1",
  "text": "Texte nettoye de l'article...",
  "content": "Article L3121-1\nTheme : ...\nTitre : ...\nEtat juridique : VIGUEUR\nDate d'entree en vigueur : ...\nDate de fin de validite : ...\nDate de derniere modification : ...\nTexte : ...",
  "legi_id": "LEGIARTI000033020517",
  "etat": "VIGUEUR",
  "date_debut": "2016-08-10",
  "date_fin": "2999-01-01",
  "date_derniere_modification": "2016-08-08",
  "date_derniere_modification_source": "LIEN typelien=MODIFIE",
  "source": "LEGI data.gouv.fr",
  "source_file": "data/raw/legi/...",
  "date_extraction": "YYYY-MM-DD"
}
```

Le champ `content` est prepare pour la suite du projet : il rassemble l'article, le theme, le titre, les metadonnees de validite juridique et le texte dans une seule chaine qui pourra etre indexee plus tard.

### Controles qualite

Le script verifie :

- aucun id vide ;
- aucun numero d'article vide ;
- aucun texte vide ;
- aucun etat juridique vide ;
- aucune date d'entree en vigueur vide ;
- aucune date de fin de validite vide ;
- aucune version non en vigueur dans le corpus final ;
- aucun doublon d'article ;
- au moins 5 themes extraits ;
- affichage du nombre total d'articles ;
- affichage du nombre d'articles par theme ;
- affichage de 5 exemples nettoyes avec leurs dates juridiques.

Sur l'archive `Freemium_legi_global_20250713-140000.tar.gz`, l'extraction ciblee a parcouru 5 253 903 entrees, analyse 41 815 XML du Code du travail et extrait 864 versions candidates. Apres filtrage des versions non en vigueur, le corpus propre genere contient 812 documents repartis sur 8 themes. Les 52 versions non en vigueur detectees sont ignorees.

### Limites actuelles

Les XML bruts dans `data/raw/legi/` restent ignores par Git afin d'eviter de versionner les donnees sources volumineuses. Le fichier propre `data/processed/corpus_legi_clean.json` est versionne car sa taille reste raisonnable.

La lecture d'un `.tar.gz` est sequentielle : meme sans decompresser toute l'archive, le script doit parcourir les entrees de l'archive pour trouver les XML utiles.

Le jalon 1 ne fait pas encore de chunking avance, pas d'embeddings, pas de base vectorielle, pas de recherche et pas d'appel LLM. LangChain et LlamaIndex ne sont pas utilises.
