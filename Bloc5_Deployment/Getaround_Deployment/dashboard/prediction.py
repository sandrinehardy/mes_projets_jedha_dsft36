"""Appel de l'API de prédiction de prix (utilisé par l'onglet « Prédiction de prix » du dashboard)."""
import os

import requests

API_URL = os.environ.get("API_URL", "https://sandrine-dsfs36-getaround-api.hf.space").rstrip("/")

# Ordre des colonnes attendu par l'API (voir la page /docs de l'API)
FEATURES = [
    "model_key", "mileage", "engine_power", "fuel", "paint_color", "car_type",
    "private_parking_available", "has_gps", "has_air_conditioning", "automatic_car",
    "has_getaround_connect", "has_speed_regulator", "winter_tires",
]

# Valeurs vues à l'entraînement du modèle (voir api/metadata.json) : valeur API -> libellé affiché
BRANDS = [
    "Alfa Romeo", "Audi", "BMW", "Citroën", "Ferrari", "Fiat", "Ford", "Honda", "KIA Motors", "Lamborghini",
    "Lexus", "Maserati", "Mazda", "Mercedes", "Mini", "Mitsubishi", "Nissan", "Opel", "PGO", "Peugeot",
    "Porsche", "Renault", "SEAT", "Subaru", "Suzuki", "Toyota", "Volkswagen", "Yamaha",
]
FUELS = {"diesel": "Diesel", "petrol": "Essence", "hybrid_petrol": "Hybride", "electro": "Électrique"}
COLORS = {
    "beige": "Beige", "black": "Noir", "blue": "Bleu", "brown": "Marron", "green": "Vert",
    "grey": "Gris", "orange": "Orange", "red": "Rouge", "silver": "Argent", "white": "Blanc",
}
CAR_TYPES = {
    "convertible": "Cabriolet", "coupe": "Coupé", "estate": "Break", "hatchback": "Compacte",
    "sedan": "Berline", "subcompact": "Citadine", "suv": "SUV", "van": "Monospace / utilitaire",
}
OPTIONS = {
    "private_parking_available": "Parking privé disponible",
    "has_gps": "GPS",
    "has_air_conditioning": "Climatisation",
    "automatic_car": "Boîte automatique",
    "has_getaround_connect": "Getaround Connect",
    "has_speed_regulator": "Régulateur de vitesse",
    "winter_tires": "Pneus hiver",
}


def predict_price(car: dict, timeout: float = 60.0) -> float:
    """Envoie une voiture (dictionnaire colonne -> valeur) à l'API et renvoie le prix prédit (€/jour).

    Lève `requests.RequestException` si l'API ne répond pas (le Space gratuit peut être en veille)
    ou `ValueError` si elle refuse l'entrée.
    """
    row = [car[name] for name in FEATURES]
    response = requests.post(f"{API_URL}/predict", json={"input": [row]}, timeout=timeout)
    if response.status_code == 422:
        raise ValueError(response.json().get("detail", "entrée refusée par l'API"))
    response.raise_for_status()
    return float(response.json()["prediction"][0])
