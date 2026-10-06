---
title: Getaround Delay Dashboard
emoji: 🚗
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Getaround : dashboard sur le délai minimum entre deux locations

Tableau de bord Streamlit qui aide à choisir un délai minimum entre deux locations (seuil et périmètre : toutes les voitures ou Getaround Connect seulement).

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Avec Docker :

```bash
docker build -t getaround-dashboard .
docker run -p 7860:7860 getaround-dashboard
```

Puis ouvrir http://localhost:7860.
