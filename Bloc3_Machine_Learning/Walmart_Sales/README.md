# Walmart : prédire les ventes hebdomadaires

## Contexte
Le service marketing de Walmart veut estimer les ventes hebdomadaires de ses magasins à partir de la température, du prix du carburant, du CPI (inflation), du taux de chômage et de la présence d'un jour férié. Objectif : un modèle de régression qui prédit `Weekly_Sales` et identifie les variables les plus influentes.

## Données
`Walmart_Store_sales.csv` : 150 lignes, beaucoup de valeurs manquantes. Après suppression des lignes sans cible, 131 lignes.

## Méthodologie
1. Exploration et préparation des données (pandas).
2. Pipeline Scikit-Learn : imputation (médiane / valeur la plus fréquente), encodage, normalisation.
3. Modèle de base : régression linéaire.
4. Régularisation : Ridge et Lasso.

## Résultats

On peut prédire les ventes hebdomadaires d'un magasin avec une erreur moyenne d'environ 124 000 \$ par semaine, soit environ 10 % de ses ventes moyennes (1,26 million \$).

Pour mieux prédire, on pourrait ajouter des variables sur les magasins eux-mêmes (superficie, nb de references...), ou entraîner un modèle par magasin avec plus d'historique.

## Contenu du dossier
- `SHY_Walmart_Sales.ipynb` : notebook complet
- `Walmart_Store_sales.csv` : données

## Technologies
Python, pandas, scikit-learn (régression linéaire, Ridge, Lasso).