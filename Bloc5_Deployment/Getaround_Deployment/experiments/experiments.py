"""Compare plusieurs modèles de prix avec MLflow (suivi des expériences).

Usage (depuis le dossier experiments/) :
    pip install -r requirements.txt
    python experiments.py
    mlflow ui --backend-store-uri sqlite:///mlflow.db     # puis http://127.0.0.1:5000

Chaque modèle est un "run" : paramètres, R² en validation croisée, R² et erreur moyenne sur le jeu de test.
Pour envoyer les résultats vers un serveur MLflow distant, définir la variable d'environnement MLFLOW_TRACKING_URI.
"""
import os
import sys
import time
from pathlib import Path

import mlflow
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# On réutilise les données et les colonnes du script d'entraînement de l'API
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
import train  # noqa: E402

MODELS = {
    "linear_regression": LinearRegression(),
    "ridge": Ridge(alpha=1.0),
    "random_forest": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    "gradient_boosting": HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=42),
}


def make_pipeline(regressor) -> Pipeline:
    preprocessor = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), train.CATEGORICAL)],
        remainder="passthrough",
    )
    return Pipeline([("preprocessing", preprocessor), ("model", regressor)])


if __name__ == "__main__":
    # Par défaut : suivi local dans le fichier mlflow.db (sinon MLFLOW_TRACKING_URI)
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("getaround_pricing")

    # Enregistre automatiquement les paramètres et le modèle de chaque entraînement
    mlflow.sklearn.autolog()

    df = train.load_data()
    X, y = df[train.FEATURES], df[train.TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    for name, regressor in MODELS.items():
        print(f"entraînement : {name}")
        start = time.time()
        with mlflow.start_run(run_name=name):
            pipeline = make_pipeline(regressor)
            cv_r2 = cross_val_score(pipeline, X_train, y_train, cv=KFold(5, shuffle=True, random_state=42), scoring="r2").mean()
            pipeline.fit(X_train, y_train)
            pred = pipeline.predict(X_test)

            mlflow.log_param("model_name", name)
            mlflow.log_metric("r2_cv", cv_r2)
            mlflow.log_metric("r2_test", r2_score(y_test, pred))
            mlflow.log_metric("mae_test", mean_absolute_error(y_test, pred))
            mlflow.log_metric("rmse_test", float(np.sqrt(mean_squared_error(y_test, pred))))
            mlflow.log_metric("training_time_s", time.time() - start)
    print("terminé : lance 'mlflow ui --backend-store-uri sqlite:///mlflow.db' pour voir les résultats")
