"""API Getaround : prédiction du prix de location par jour (FastAPI).

Endpoints :
    GET  /          message de bienvenue
    GET  /health    état du service
    GET  /docs      documentation de l'API (page HTML)
    POST /predict   prédiction du prix par jour pour une ou plusieurs voitures
"""
import html
import json
from pathlib import Path
from typing import List, Union

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

HERE = Path(__file__).parent
MODEL = joblib.load(HERE / "model.joblib")
META = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))

FEATURES = META["features"]
CATEGORICAL = META["categorical"]
BOOLEAN = META["boolean"]
NUMERIC = ["mileage", "engine_power"]

EXAMPLE_ROW = ["Citroën", 140411, 100, "diesel", "black", "convertible", True, True, False, False, True, True, True]


class InputError(ValueError):
    """Entrée invalide : renvoyée au client avec le code 422."""


def _to_bool(value, name, row_index):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in (0, 1):
        return int(value)
    raise InputError(f"ligne {row_index}: '{name}' doit être true/false (ou 1/0), reçu {value!r}")


def _check_row(row, row_index):
    """Valide une ligne (liste ordonnée ou dictionnaire) et renvoie un dict colonne -> valeur."""
    if isinstance(row, dict):
        missing = [f for f in FEATURES if f not in row]
        if missing:
            raise InputError(f"ligne {row_index}: colonnes manquantes {missing}")
        values = {f: row[f] for f in FEATURES}
    elif isinstance(row, list):
        if len(row) != len(FEATURES):
            raise InputError(f"ligne {row_index}: {len(FEATURES)} valeurs attendues, {len(row)} reçues")
        values = dict(zip(FEATURES, row))
    else:
        raise InputError(f"ligne {row_index}: une liste de {len(FEATURES)} valeurs ou un objet est attendu")

    for name in CATEGORICAL:
        if not isinstance(values[name], str):
            raise InputError(f"ligne {row_index}: '{name}' doit être un texte, reçu {values[name]!r}")
    for name in NUMERIC:
        v = values[name]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise InputError(f"ligne {row_index}: '{name}' doit être un nombre, reçu {v!r}")
    for name in BOOLEAN:
        values[name] = _to_bool(values[name], name, row_index)
    return values


def predict_prices(rows):
    """Renvoie la liste des prix prédits (€/jour) pour une liste de lignes valides."""
    checked = [_check_row(row, i) for i, row in enumerate(rows)]
    frame = pd.DataFrame(checked, columns=FEATURES)
    return [round(float(p), 2) for p in MODEL.predict(frame)]


class PredictionFeatures(BaseModel):
    input: List[List[Union[str, int, float, bool]]]


# docs_url=None : on remplace la page /docs par défaut par notre propre page HTML
app = FastAPI(docs_url=None, redoc_url=None)


@app.get("/")
async def index():
    """Renvoie un message de bienvenue."""
    return "Bienvenue sur l'API de prix Getaround. La documentation est sur /docs"


@app.get("/health")
async def health():
    """État du service et métriques du modèle."""
    return {"status": "ok", "model_rows": META["n_training_rows"], "metrics": META["metrics"]}


@app.post("/predict")
async def predict(predictionFeatures: PredictionFeatures):
    """Prédit le prix de location par jour pour chaque voiture de la liste `input`."""
    if not predictionFeatures.input:
        raise HTTPException(status_code=422, detail="Au moins une voiture est attendue dans 'input'.")
    try:
        prediction = predict_prices(predictionFeatures.input)
    except InputError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"prediction": prediction}


def _feature_rows() -> str:
    descriptions = {
        "model_key": "Marque du véhicule (texte)",
        "mileage": "Kilométrage (nombre)",
        "engine_power": "Puissance du moteur en chevaux (nombre)",
        "fuel": "Carburant (texte)",
        "paint_color": "Couleur (texte)",
        "car_type": "Type de carrosserie (texte)",
        "private_parking_available": "Parking privé disponible (true/false)",
        "has_gps": "GPS (true/false)",
        "has_air_conditioning": "Climatisation (true/false)",
        "automatic_car": "Boîte automatique (true/false)",
        "has_getaround_connect": "Équipée Getaround Connect (true/false)",
        "has_speed_regulator": "Régulateur de vitesse (true/false)",
        "winter_tires": "Pneus hiver (true/false)",
    }
    rows = []
    for position, name in enumerate(FEATURES, start=1):
        extra = ""
        if name in META["categories"]:
            values = ", ".join(html.escape(v) for v in META["categories"][name])
            extra = f"<br><small>Valeurs vues à l'entraînement : {values}</small>"
        rows.append(
            f"<tr><td>{position}</td><td><code>{name}</code></td><td>{descriptions[name]}{extra}</td></tr>"
        )
    return "\n".join(rows)


@app.get("/docs", response_class=HTMLResponse)
async def docs(request: Request):
    base = html.escape(str(request.base_url).rstrip("/"))
    example_json = json.dumps({"input": [EXAMPLE_ROW]}, ensure_ascii=False)
    example_one = json.dumps({"input": [EXAMPLE_ROW]}, ensure_ascii=False)
    example_two = json.dumps({"input": [EXAMPLE_ROW, ["BMW", 50000, 150, "petrol", "grey", "sedan", True, True, True, True, False, True, False]]}, ensure_ascii=False)
    page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Getaround Pricing API : documentation</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 880px; margin: 2rem auto; padding: 0 1rem; line-height: 1.55; color: #1b1b1b; }}
  h1 {{ margin-bottom: .2rem; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid #ddd; padding-bottom: .25rem; }}
  pre {{ background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
  code {{ background: #f1f5f9; padding: 1px 5px; border-radius: 4px; }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: .45rem .6rem; text-align: left; vertical-align: top; }}
  th {{ background: #f1f5f9; }}
  .tag {{ display: inline-block; background: #0b57d0; color: #fff; border-radius: 4px; padding: 0 .5rem; font-weight: 600; }}
</style>
</head>
<body>
<h1>Getaround Pricing API</h1>
<p>Cette API prédit le <strong>prix de location par jour (en €)</strong> d'une voiture à partir de ses caractéristiques,
avec un modèle de machine learning (gradient boosting) entraîné sur {META["n_training_rows"]} voitures.
Erreur moyenne sur des voitures jamais vues : environ {META["metrics"]["mae_test"]} € par jour.</p>

<h2>Endpoints</h2>
<table>
<tr><th>Nom</th><th>Méthode</th><th>Description</th></tr>
<tr><td><code>/predict</code></td><td>POST</td><td>Prédit le prix par jour pour une ou plusieurs voitures</td></tr>
<tr><td><code>/health</code></td><td>GET</td><td>État du service et métriques du modèle</td></tr>
<tr><td><code>/docs</code></td><td>GET</td><td>Cette page</td></tr>
</table>

<h2><span class="tag">POST</span> <code>/predict</code></h2>
<p>Corps de la requête : du JSON avec une clé <code>input</code> contenant une liste de voitures.
Chaque voiture est une liste de {len(FEATURES)} valeurs, <strong>dans l'ordre du tableau ci-dessous</strong>
(un objet avec les noms de colonnes est aussi accepté).</p>
<table>
<tr><th>#</th><th>Colonne</th><th>Description</th></tr>
{_feature_rows()}
</table>

<h3>Exemple d'entrée</h3>
<pre><code>{html.escape(example_json)}</code></pre>

<h3>Sortie</h3>
<p>Un JSON avec une clé <code>prediction</code> : la liste des prix prédits (en €/jour), dans le même ordre que l'entrée.</p>
<pre><code>{{"prediction": [105.9]}}</code></pre>

<h3>Appel avec curl</h3>
<pre><code>curl -i -H "Content-Type: application/json" -X POST -d '{html.escape(example_two)}' {base}/predict</code></pre>

<h3>Appel avec Python</h3>
<pre><code>import requests

response = requests.post("{base}/predict", json={html.escape(example_one)})
print(response.json())</code></pre>

<h3>Erreurs</h3>
<table>
<tr><th>Code</th><th>Cause</th></tr>
<tr><td>422</td><td>Format incorrect (JSON invalide, clé <code>input</code> absente, mauvais nombre de valeurs, type invalide). Le message <code>detail</code> indique la cause.</td></tr>
</table>
<pre><code>{{"detail": "ligne 0: 13 valeurs attendues, 12 reçues"}}</code></pre>
</body>
</html>"""
    return page
