# AT&T : détecteur de spams par deep learning

Lien GitHub du projet : https://github.com/sandrinehardy/mes_projets_jedha_dsft36/tree/main/Bloc4_Deep_Learning/ATT_Deep_Learning

## Objectif

AT&T veut protéger ses utilisateurs des SMS indésirables. Le projet construit un détecteur qui classe automatiquement un SMS en spam ou ham (message normal), à partir de son seul contenu.

## Données

5 572 SMS étiquetés (`spam.csv`), dont 403 doublons supprimés : il reste 5 169 SMS, dont 12,6 % de spams. Les classes sont déséquilibrées : un modèle qui répondrait toujours « ham » aurait déjà 87 % de bonnes réponses.

## Résultats

Résultats du modèle retenu (réseau PyTorch avec une couche d'embedding), mesurés sur le jeu de test de 776 SMS :

| Métrique | Valeur |
| --- | --- |
| Accuracy | 97,7 % (référence « toujours ham » : 87,4 %) |
| Precision (spam) | 93,5 % : sur 92 SMS signalés spam, 86 le sont vraiment |
| Recall (spam) | 87,8 % : sur 98 vrais spams, 86 sont détectés |
| F1-score (spam) | 0,905 |

Au total, 6 SMS normaux sont classés à tort en spam et 12 spams ne sont pas détectés.

## Fichiers

- `ATT_Spam_Detector.ipynb` : notebook complet (préparation, entraînement, évaluation, analyse des erreurs)
- `spam.csv` : données

## Lancer le notebook

```bash
conda create -n jedha-att python=3.12 -y
conda activate jedha-att
pip install torch tiktoken pandas numpy matplotlib scikit-learn ipykernel
jupyter notebook ATT_Spam_Detector.ipynb
```
