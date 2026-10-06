# Conversion rate challenge

## Contexte
Prédire si un visiteur d'un site web va convertir (`converted`), à partir de 5 variables : `country`, `age`, `new_user`, `source`, `total_pages_visited`. Métrique du challenge : le score F1.

## Données
- `conversion_data_train.csv` : environ 284 600 lignes avec la cible.
- `conversion_data_test.csv` : 31 620 lignes sans la cible.

## Méthodologie
1. Exploration du jeu d'entraînement et nettoyage (suppression des 2 âges aberrants supérieurs à 100 ans).
2. Quatre modèles comparés : M0 (baseline, 1 variable), M1 (régression logistique, 5 variables), M2 (Ridge), M3 (XGBoost).
3. Réglage du seuil de décision pour optimiser le F1.
4. Prédictions sur le fichier de test avec le modèle retenu, réentraîné sur toutes les données avec cible.

## Résultats

| Modèle | F1 test | Precision | Recall |
| --- | --- | --- | --- |
| M0 : 1 variable | 0.677 | 0.806 | 0.584 |
| M1 : régression logistique, 5 variables | 0.759 | 0.771 | 0.746 |
| M2 : Ridge | 0.759 | 0.771 | 0.746 |
| M3 : XGBoost | 0.757 | 0.815 | 0.706 |

## Contenu du dossier
- `SHY_Conversion_Rate.ipynb` : notebook complet
- `SHY_modeles_challenge.csv` : tableau récapitulatif des modèles
- `conversion_data_train.csv`, `conversion_data_test.csv` : données
- `conversion_data_test_predictions_Sandrine-M1.csv` : prédictions du modèle M1

## Technologies
Python, pandas, scikit-learn, XGBoost.