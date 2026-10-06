# The North Face ecommerce

## Contexte
Le service marketing de The North Face veut augmenter les ventes sur son site web. Deux pistes : un système de recommandation (« vous pourriez aussi aimer ») sur chaque page produit, et une meilleure structure du catalogue grâce à des méthodes non supervisées qui font apparaître de nouvelles catégories de produits.

## Données
`sample-data.csv` : les descriptions de 500 produits.

## Méthodologie
1. Prétraitement du texte : suppression des balises HTML (BeautifulSoup), tokenisation et lemmatisation (spaCy), encodage TF-IDF.
2. Partie 1, clustering : DBSCAN pour regrouper les produits aux descriptions proches (eps et min_samples choisis pour obtenir entre 10 et 20 groupes avec peu d'outliers).
3. Partie 2, recommandation : pour un produit, le système propose jusqu'à 5 produits du même cluster.
4. Partie 3, topic modeling : extraction de sujets avec TruncatedSVD, puis interprétation à partir des mots dominants.

## Résultats
À partir des seules descriptions des 500 produits :
- 20 groupes de produits aux descriptions proches.
- Des recommandations sur chaque fiche produit : jusqu'à 5 articles de la même famille.
- Les grands thèmes du catalogue : matières (mérinos, polaire, coton bio), usages (protection solaire, imperméabilité) et types de produits (sacs, chaussettes, maillots).
- 41 produits atypiques (8 % du catalogue), qui ne ressemblent à aucun autre : ils peuvent être retravaillés ou mis en avant comme « uniques ».

**Limites** : le premier cluster est trop large (183 produits, 37 % du catalogue), donc ses recommandations sont peu précises. Les 41 produits atypiques n'ont aucune recommandation. Les suggestions sont tirées au hasard dans le cluster : on pourrait recommander les produits les plus proches. Certains thèmes se recoupent.

## Contenu du dossier
- `SHY_The_North_Face_ecommerce.ipynb` : notebook complet
- `sample-data.csv` : données

## Technologies
Python, pandas, BeautifulSoup, spaCy, scikit-learn (TF-IDF, DBSCAN, TruncatedSVD, NearestNeighbors), WordCloud, matplotlib.