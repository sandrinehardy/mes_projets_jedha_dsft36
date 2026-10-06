# Getaround : analyse des retards et API de prix (déploiement)

Lien GitHub du projet : https://github.com/sandrinehardy/mes_projets_jedha_dsft36/tree/main/Bloc5_Deployment/Getaround_Deployment

Projet du bloc 5 (déploiement). Deux applications en ligne :

| Application | Rôle | URL |
| --- | --- | --- |
| Dashboard | Choisir le délai minimum entre deux locations (seuil, périmètre, impact) | https://sandrine-dsfs36-getaround-dashboard.hf.space |
| API de prix | `POST /predict` : prix de location par jour d'une voiture, documentation sur `/docs` | https://sandrine-dsfs36-getaround-api.hf.space (documentation : https://sandrine-dsfs36-getaround-api.hf.space/docs) |

## Contenu

- `dashboard/` : application Streamlit et analyse des retards (`analysis.py`)
- `api/` : API de prédiction (FastAPI), entraînement du modèle (`train.py`)
- `experiments/` : comparaison de 4 modèles de prix avec MLflow

Chaque dossier contient son `Dockerfile` et son `README.md`.

## Lancer en local

Dashboard :

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

API :

```bash
cd api
pip install -r requirements.txt
python train.py
fastapi run app.py --port 7860
```

Documentation de l'API : http://127.0.0.1:7860/docs

## Résultats

- Un délai minimum de 90 à 120 minutes résout environ 80 % des cas problématiques pour environ 3 % de locations bloquées.
- Le modèle de prix (gradient boosting) a une erreur moyenne de 10,7 € par jour, contre 23,6 € pour une prédiction constante. Il a été choisi après comparaison de 4 modèles suivis avec MLflow (voir `experiments/`).
