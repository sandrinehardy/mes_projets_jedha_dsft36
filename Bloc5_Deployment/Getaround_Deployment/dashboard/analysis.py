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
    - share_blocked : part des locations terminées bloquées (approximation de la part du revenu
      affectée : les données ne contiennent pas le prix de chaque location)
    - solved : cas problématiques résolus (écart < T, donc location bloquée alors qu'elle posait problème)
    - solved_share : part des cas problématiques résolus
    - solved_pct_ended : cas problématiques résolus / ensemble des locations terminées
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
                "solved_pct_ended": solved / n_ended if n_ended else np.nan,
            }
        )
    return pd.DataFrame(rows)


def delay_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Locations terminées dont le retard est connu : à l'heure / retard simple / le suivant a attendu / le suivant a annulé."""
    ended = df[(df["state"] == "ended") & df["delay_at_checkout_in_minutes"].notna()]
    n_late = int((ended["delay_at_checkout_in_minutes"] > 0).sum())
    problem = adjacent_rentals(df).query("problematic")
    canceled = int((problem["state"] == "canceled").sum())
    waited = len(problem) - canceled
    out = pd.DataFrame(
        {
            "Catégorie": ["À l'heure ou en avance", "Retard simple", "Le suivant a attendu", "Le suivant a annulé"],
            "Nombre": [len(ended) - n_late, n_late - waited - canceled, waited, canceled],
        }
    )
    out["Part"] = out["Nombre"] / out["Nombre"].sum()
    return out


def delay_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """Répartition des retards au check-out par tranche (locations terminées dont le retard est connu)."""
    delay = df.loc[df["state"] == "ended", "delay_at_checkout_in_minutes"].dropna()
    labels = ["À l'heure ou en avance", "1-30 min", "30-60 min", "60-120 min", "120-240 min", "+ de 240 min"]
    bins = pd.cut(delay, [-np.inf, 0, 30, 60, 120, 240, np.inf], labels=labels)
    out = bins.value_counts().reindex(labels).rename_axis("Tranche").reset_index(name="Nombre")
    out["Part"] = out["Nombre"] / out["Nombre"].sum()
    return out


def late_share_by_checkin(df: pd.DataFrame) -> pd.DataFrame:
    """Part de locations terminées rendues en retard, par type de check-in (retards inconnus exclus)."""
    ended = df[(df["state"] == "ended") & df["delay_at_checkout_in_minutes"].notna()]
    late = ended["delay_at_checkout_in_minutes"] > 0
    share = late.groupby(ended["checkin_type"]).mean()
    return pd.DataFrame(
        {
            "Type de check-in": ["Toutes les voitures", "Getaround Connect", "Check-in mobile"],
            "Part": [late.mean(), share["connect"], share["mobile"]],
        }
    )


GAP_CATEGORIES = [
    "Conservée : sans problème",
    "Conservée : retard problématique",
    "Bloquée : sans problème",
    "Bloquée : retard problématique",
]


def gap_histogram(df: pd.DataFrame, threshold: int, step: int = 30, max_gap: int = 720) -> pd.DataFrame:
    """Locations qui suivent une autre location, par écart avec la précédente (tranches de `step` minutes).

    Chaque location est « bloquée » si son écart est inférieur au seuil, « conservée » sinon,
    et « retard problématique » si la location précédente a été rendue après son début.
    Les écarts au-delà de `max_gap` sont regroupés dans la dernière tranche.
    """
    adj = adjacent_rentals(df)
    gap = adj["time_delta_with_previous_rental_in_minutes"]
    start = (gap // step * step).clip(upper=max_gap).astype(int)
    blocked = gap < threshold
    problem = adj["problematic"]
    category = np.select(
        [~blocked & ~problem, ~blocked & problem, blocked & ~problem],
        GAP_CATEGORIES[:3],
        default=GAP_CATEGORIES[3],
    )
    out = pd.DataFrame({"start": start.to_numpy(), "Catégorie": category})
    out = out.groupby(["start", "Catégorie"]).size().reset_index(name="Nombre")
    out["Écart"] = out["start"].map(lambda v: f"{v}+" if v >= max_gap else str(v))
    out["Ordre"] = out["Catégorie"].map({c: i for i, c in enumerate(GAP_CATEGORIES)})
    return out.drop(columns="start")


def compare_scopes(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """Pour un seuil donné : toutes les voitures, Connect, mobile."""
    rows = []
    for name, scope in SCOPES.items():
        d = filter_scope(df, scope)
        r = threshold_table(d).query("threshold == @threshold").iloc[0]
        rows.append(
            {
                "Périmètre": name,
                "Locations": len(d),
                "Cas problématiques": kpis(d)["n_problematic"],
                "Locations bloquées": int(r["blocked"]),
                "Part bloquée": r["share_blocked"],
                "Cas résolus": int(r["solved"]),
                "Part des problèmes résolus": r["solved_share"],
                "Cas résolus / locations terminées": r["solved_pct_ended"],
            }
        )
    return pd.DataFrame(rows)
