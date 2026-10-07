"""Dashboard Getaround : quel délai minimum imposer entre deux locations ?"""
import altair as alt
import pandas as pd
import streamlit as st

import analysis as an

st.set_page_config(page_title="Getaround : délai minimum entre locations", page_icon="🚗", layout="wide")


@st.cache_data
def get_data() -> pd.DataFrame:
    return an.load_data()


df = get_data()

st.title("🚗 Getaround : quel délai minimum entre deux locations ?")
st.markdown(
    "Quand un conducteur rend sa voiture en retard, le conducteur suivant peut attendre, voire annuler. "
    "Une solution : imposer un **délai minimum** entre deux locations. Mais chaque location bloquée est "
    "un manque à gagner pour le propriétaire. Ce tableau de bord aide à choisir **le seuil** et **le périmètre** "
    "(toutes les voitures ou seulement celles équipées de Getaround Connect)."
)

# ------------------------------------------------------------------ Choix utilisateur
st.sidebar.header("Paramètres")
scope_label = st.sidebar.radio("Périmètre de la mesure", list(an.SCOPES), index=0)
threshold = st.sidebar.slider("Délai minimum (minutes)", 0, 720, 120, step=30)
data = an.filter_scope(df, an.SCOPES[scope_label])
k = an.kpis(data)
table = an.threshold_table(data)
row = table[table["threshold"] == threshold].iloc[0]

# ------------------------------------------------------------------ Résultat du seuil choisi
st.header(f"Avec un délai minimum de {threshold} min ({scope_label.lower()})")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Locations bloquées", f"{int(row['blocked'])}", help="Locations dont l'écart avec la précédente est inférieur au seuil")
c2.metric("Part des locations perdues", f"{row['share_blocked']:.1%}", help="Approximation de la part du revenu des propriétaires touchée (le prix de chaque location n'est pas dans les données)")
c3.metric("Cas problématiques résolus", f"{int(row['solved'])} / {k['n_problematic']}")
c4.metric("Part des problèmes résolus", f"{row['solved_share']:.0%}")

left, right = st.columns(2)
with left:
    st.subheader("Gain et coût selon le seuil")
    curve = table.set_index("threshold")[["solved_share", "share_blocked"]].rename(
        columns={"solved_share": "Problèmes résolus", "share_blocked": "Locations perdues"}
    )
    st.line_chart(curve)
    st.caption("En abscisse, le délai minimum (minutes). Plus le seuil monte, plus on résout de cas, mais plus on perd de locations.")
with right:
    st.subheader("Tableau détaillé")
    shown = table.rename(
        columns={
            "threshold": "Seuil (min)",
            "blocked": "Locations bloquées",
            "share_blocked": "Part perdue",
            "solved": "Problèmes résolus",
            "solved_share": "Part résolue",
        }
    )
    st.dataframe(
        shown.style.format({"Part perdue": "{:.1%}", "Part résolue": "{:.0%}"}),
        hide_index=True,
        use_container_width=True,
    )

# ------------------------------------------------------------------ Comparaison des périmètres
st.header("Toutes les voitures ou seulement Connect ?")
compare = []
for name, s in an.SCOPES.items():
    d = an.filter_scope(df, s)
    t = an.threshold_table(d)
    r = t[t["threshold"] == threshold].iloc[0]
    kk = an.kpis(d)
    compare.append(
        {
            "Périmètre": name,
            "Locations": kk["n_rentals"],
            "Cas problématiques": kk["n_problematic"],
            "Part perdue": r["share_blocked"],
            "Part des problèmes résolus": r["solved_share"],
        }
    )
st.dataframe(
    pd.DataFrame(compare).style.format({"Part perdue": "{:.1%}", "Part des problèmes résolus": "{:.0%}"}),
    hide_index=True,
    use_container_width=True,
)
st.caption(f"Valeurs pour un seuil de {threshold} min. Les voitures Connect ont un check-in sans contact : le retard y est moins fréquent, mais les locations s'enchaînent plus souvent.")

# ------------------------------------------------------------------ Retards
st.header("À quelle fréquence les conducteurs sont-ils en retard ?")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Locations", f"{k['n_rentals']:,}".replace(",", " "))
c2.metric("Annulées", f"{k['share_canceled']:.0%}")
c3.metric("Rendues en retard", f"{k['share_late']:.0%}", help="Part des locations terminées rendues après l'heure prévue")
c4.metric("Retard médian (si retard)", f"{k['median_delay_late']:.0f} min")

GREY, TEAL, ORANGE, DARK = "#8A99A3", "#149CA6", "#E06A2B", "#0E3449"

# Répartition des retards (suit le périmètre choisi)
buckets = an.delay_buckets(data)
buckets["Couleur"] = [GREY] + [TEAL] * (len(buckets) - 1)
base = alt.Chart(buckets).encode(
    x=alt.X("Tranche:N", sort=list(buckets["Tranche"]), title=None, axis=alt.Axis(labelAngle=0)),
    y=alt.Y("Part:Q", title="Part des locations terminées", axis=alt.Axis(format="%")),
)
bars = base.mark_bar().encode(
    color=alt.Color("Couleur:N", scale=None, legend=None),
    tooltip=["Tranche", "Nombre", alt.Tooltip("Part:Q", format=".1%")],
)
labels = base.mark_text(dy=-8).encode(text=alt.Text("Part:Q", format=".0%"))
st.subheader("Répartition des retards au rendu")
st.altair_chart(bars + labels, use_container_width=True)
st.caption("Locations terminées dont le retard est connu. Le retard est mesuré au check-out ; « à l'heure ou en avance » regroupe les retards inférieurs ou égaux à 0.")

left, right = st.columns(2)
with left:
    st.subheader("Qui est concerné par les retards ?")
    breakdown = an.delay_breakdown(data)
    cats = list(breakdown["Catégorie"])
    pie = (
        alt.Chart(breakdown)
        .mark_arc()
        .encode(
            theta="Nombre:Q",
            color=alt.Color(
                "Catégorie:N",
                scale=alt.Scale(domain=cats, range=[GREY, TEAL, ORANGE, DARK]),
                legend=alt.Legend(orient="bottom", title=None, columns=2),
            ),
            tooltip=["Catégorie", "Nombre", alt.Tooltip("Part:Q", format=".1%")],
        )
    )
    st.altair_chart(pie, use_container_width=True)
    st.caption(f"{scope_label}. Passer la souris sur une part pour voir le nombre et le pourcentage.")
with right:
    st.subheader("Part de retards par type de check-in")
    by_type = an.late_share_by_checkin(df)
    types = list(by_type["Type de check-in"])
    base_t = alt.Chart(by_type).encode(
        x=alt.X("Type de check-in:N", sort=types, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Part:Q", title="Part de retards", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
    )
    bars_t = base_t.mark_bar().encode(
        color=alt.Color("Type de check-in:N", scale=alt.Scale(domain=types, range=[DARK, TEAL, ORANGE]), legend=None),
        tooltip=["Type de check-in", alt.Tooltip("Part:Q", format=".1%")],
    )
    labels_t = base_t.mark_text(dy=-8).encode(text=alt.Text("Part:Q", format=".0%"))
    st.altair_chart(bars_t + labels_t, use_container_width=True)
    st.caption("Tous les périmètres (indépendant du filtre). Locations dont le retard n'est pas renseigné exclues.")

# ------------------------------------------------------------------ Impact sur le conducteur suivant
st.header("Quel impact sur le conducteur suivant ?")
c1, c2, c3 = st.columns(3)
c1.metric("Locations qui suivent une autre location", f"{k['n_adjacent']}", f"{k['share_adjacent']:.1%} des locations", delta_color="off")
c2.metric("Cas problématiques", f"{k['n_problematic']}", help="La location précédente a rendu la voiture après le début de celle-ci")
c3.metric("…annulés ensuite", f"{k['n_canceled_after_problem']}")
adj = an.adjacent_rentals(data)
problem = adj[adj["problematic"]]
if len(problem):
    waiting = (problem["prev_delay"] - problem["time_delta_with_previous_rental_in_minutes"]).clip(lower=0)
    st.write(
        f"Dans les cas problématiques, le conducteur suivant attend en médiane **{waiting.median():.0f} min** "
        f"(9 cas sur 10 sous {waiting.quantile(0.9):.0f} min)."
    )

with st.expander("Définitions et hypothèses"):
    st.markdown(
        """
- **Location adjacente** : location dont la voiture a été louée juste avant (l'écart avec la précédente est connu).
- **Cas problématique** : la location précédente a été rendue en retard, après le début de la suivante (retard > écart).
- **Délai minimum T** : une location est refusée si elle commence moins de T minutes après la fin de la précédente.
- **Part des locations perdues** : locations terminées bloquées / locations terminées. C'est une approximation de la part du revenu affectée, car le prix de chaque location n'est pas dans les données.
- **Cas résolus** : cas problématiques dont l'écart est inférieur à T (la location problématique n'aurait pas eu lieu).
- Limite : on suppose que les locations bloquées sont perdues (pas de report vers un autre créneau).
"""
    )
