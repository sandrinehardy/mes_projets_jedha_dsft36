"""Entraîne le modèle d'optimisation des prix Getaround et le sauvegarde.

Usage :  python train.py
Produit : model.joblib (pipeline scikit-learn) et metadata.json (colonnes, métriques).
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).parent
DATA = HERE / "data" / "get_around_pricing_project.csv"

# Ordre des colonnes attendu par l'API (voir la page /docs)
FEATURES = [
    "model_key", "mileage", "engine_power", "fuel", "paint_color", "car_type",
    "private_parking_available", "has_gps", "has_air_conditioning", "automatic_car",
    "has_getaround_connect", "has_speed_regulator", "winter_tires",
]
CATEGORICAL = ["model_key", "fuel", "paint_color", "car_type"]
BOOLEAN = [
    "private_parking_available", "has_gps", "has_air_conditioning", "automatic_car",
    "has_getaround_connect", "has_speed_regulator", "winter_tires",
]
TARGET = "rental_price_per_day"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA).drop(columns=["Unnamed: 0"], errors="ignore")
    # Valeurs impossibles : kilométrage négatif ou puissance nulle
    df = df[(df["mileage"] > 0) & (df["engine_power"] > 0)].reset_index(drop=True)
    df[BOOLEAN] = df[BOOLEAN].astype(int)
    return df


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL)],
        remainder="passthrough",
    )
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=42)
    return Pipeline([("preprocessing", preprocessor), ("model", model)])


def main() -> None:
    df = load_data()
    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = build_pipeline()
    cv_r2 = cross_val_score(pipeline, X_train, y_train, cv=KFold(5, shuffle=True, random_state=42), scoring="r2").mean()
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)
    metrics = {
        "r2_cv": round(float(cv_r2), 3),
        "r2_test": round(float(r2_score(y_test, pred)), 3),
        "mae_test": round(float(mean_absolute_error(y_test, pred)), 2),
        "rmse_test": round(float(np.sqrt(mean_squared_error(y_test, pred))), 2),
        "mae_modele_constant": round(float(mean_absolute_error(y_test, [y_train.mean()] * len(y_test))), 2),
    }
    print("Métriques (jeu de test) :", metrics)

    # Modèle final réentraîné sur toutes les données
    pipeline.fit(X, y)
    joblib.dump(pipeline, HERE / "model.joblib")

    metadata = {
        "features": FEATURES,
        "categorical": CATEGORICAL,
        "boolean": BOOLEAN,
        "categories": {c: sorted(df[c].unique().tolist()) for c in CATEGORICAL},
        "metrics": metrics,
        "n_training_rows": int(len(df)),
        "sklearn_version": sklearn.__version__,
    }
    (HERE / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Modèle sauvegardé : model.joblib, metadata.json")


if __name__ == "__main__":
    main()
