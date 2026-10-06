"""Fonctions d'analyse des retards Getaround (utilisées par le dashboard et testables seules)."""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data" / "get_around_delay_analysis.xlsx"
SCOPES = {"Toutes les voitures": None, "Getaround Connect uniquement": "connect", "Check-in mobile uniquement": "mobile"}


def load_data(path=DATA) -> pd.DataFrame:
    return pd.read_excel(path)


def adjacent_rentals(df: pd.DataFrame) -> pd.DataFrame:
    """Locations précédées d'une autre location de la même voiture (écart connu).

    Ajoute `prev_delay` (retard au check-out de la location précédente, en minutes)
    et `problematic` (la précédente a rendu la voiture après le début de celle-ci).
    """
    adj = df[df["time_delta_with_previous_rental_in_minutes"].notna()].copy()
    prev = df.set_index("rental_id")["delay_at_checkout_in_minutes"]
    adj["prev_delay"] = adj["previous_ended_rental_id"].map(prev)
    gap = adj["time_delta_with_previous_rental_in_minutes"]
    adj["problematic"] = adj["prev_delay"] > gap
    adj["canceled_after_problem"] = adj["problematic"] & (adj["state"] == "canceled")
    return adj


def filter_scope(df: pd.DataFrame, scope: str | None) -> pd.DataFrame:
    return df if scope is None else df[df["checkin_type"] == scope]


def kpis(df: pd.DataFrame) -> dict:
    ended = df[df["state"] == "ended"]
    late = ended["delay_at_checkout_in_minutes"].dropna()
    adj = adjacent_rentals(df)
    return {
        "n_rentals": len(df),
        "n_ended": len(ended),
        "share_canceled": float((df["state"] == "canceled").mean()),
        "share_late": float((late > 0).mean()),
        "median_delay_late": float(late[late > 0].median()),
        "n_adjacent": len(adj),
        "share_adjacent": len(adj) / len(df),
        "n_problematic": int(adj["problematic"].sum()),
        "n_canceled_after_problem": int(adj["canceled_after_problem"].sum()),
    }


def threshold_table(df: pd.DataFrame, thresholds=range(0, 721, 30)) -> pd.DataFrame:
    """Effet d'un délai minimum T entre deux locations (T en minutes).

    - blocked : locations adjacentes dont l'écart est inférieur à T (elles n'auraient pas eu lieu)
    - share_blocked : part des locations terminées perdues (approximation de la part du revenu
      affectée : les données ne contiennent pas le prix de chaque location)
    - solved : cas problématiques résolus (écart < T, donc location bloquée alors qu'elle posait problème)
    - solved_share : part des cas problématiques résolus
    """
    adj = adjacent_rentals(df)
    n_ended = int((df["state"] == "ended").sum())
    ended_adj = adj[adj["state"] == "ended"]
    gap = ended_adj["time_delta_with_previous_rental_in_minutes"]
    n_problem = int(adj["problematic"].sum())
    rows = []
    for t in thresholds:
        blocked = int((gap < t).sum())
        solved = int((adj["problematic"] & (adj["time_delta_with_previous_rental_in_minutes"] < t)).sum())
        rows.append(
            {
                "threshold": t,
                "blocked": blocked,
                "share_blocked": blocked / n_ended if n_ended else np.nan,
                "solved": solved,
                "solved_share": solved / n_problem if n_problem else np.nan,
            }
        )
    return pd.DataFrame(rows)
