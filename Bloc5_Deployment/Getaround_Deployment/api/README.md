---
title: Getaround Pricing API
emoji: 🚗
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Getaround Pricing API

API de prédiction du prix de location par jour d'une voiture (projet Getaround, bloc 5 : déploiement).

- `POST /predict` : prédit le prix par jour (entrée `{"input": [[...]]}`, sortie `{"prediction": [...]}`)
- `GET /docs` : documentation complète de l'API
- `GET /health` : état du service

## Lancer en local

```bash
pip install -r requirements.txt
python train.py                      # entraîne le modèle (crée model.joblib)
fastapi run app.py --port 7860       # http://127.0.0.1:7860/docs
```

Avec Docker :

```bash
docker build -t getaround-api .
docker run -p 7860:7860 getaround-api
```

## Exemple d'appel

```bash
curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input": [["Citroën", 140411, 100, "diesel", "black", "convertible", true, true, false, false, true, true, true]]}' \
  http://127.0.0.1:7860/predict
```

Réponse : `{"prediction": [105.9]}`

## Modèle

Gradient boosting (scikit-learn), entraîné sur 4 841 voitures : R² de 0,75 et erreur moyenne de 10,7 € par jour sur des voitures jamais vues (23,6 € pour une prédiction constante).
