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
