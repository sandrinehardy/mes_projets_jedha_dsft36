"""Dashboard Getaround : quel délai minimum imposer entre deux locations ?"""
import altair as alt
import pandas as pd
import streamlit as st

import analysis as an
import prediction as pred

st.set_page_config(page_title="Getaround : délai minimum et prix de location", page_icon="🚗", layout="wide")
# Largeur limitée pour faciliter la lecture
st.markdown(
    "<style>.block-container, [data-testid='stMainBlockContainer'] {max-width: 1100px; margin: auto;}</style>",
    unsafe_allow_html=True,
)

GREY, TEAL, ORANGE, DARK = "#8A99A3", "#149CA6", "#E06A2B", "#0E3449"


def pct0(x: float) -> str:
    return f"{x:.0%}".replace(".", ",")


def pct1(x: float) -> str:
    return f"{x:.1%}".replace(".", ",")


@st.cache_data
def get_data() -> pd.DataFrame:
    return an.load_data()


df = get_data()

st.title("🚗 Getaround : délai minimum et prix de location")
st.markdown(
    "Quand un conducteur rend sa voiture en retard, le conducteur suivant peut attendre, voire annuler. "
    "Une solution : imposer un **délai minimum** entre deux locations. Mais chaque location bloquée est "
    "un manque à gagner pour le propriétaire. Ce tableau de bord aide à choisir **le seuil** puis à décider "
    "si la mesure s'applique à **toutes les voitures** ou seulement à celles équipées de Getaround Connect. "
    "Le second onglet suggère un **prix de location** grâce à notre API."
)

tab_delay, tab_price = st.tabs(["Délai minimum entre deux locations", "Prédiction de prix"])

with tab_delay:
    # ================================================================== 1. Analyse des retards
    st.header("1. Analyse des retards")
    k = an.kpis(df)

    st.subheader("À quelle fréquence les conducteurs sont-ils en retard ?")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", f"{k['n_rentals']:,}".replace(",", " "))
    c2.metric("Annulées", f"{k['share_canceled']:.0%}")
    c3.metric("Rendues en retard", f"{k['share_late']:.0%}", help="Part des locations terminées (retard connu) rendues après l'heure prévue")
    c4.metric("Retard médian (si retard)", f"{k['median_delay_late']:.0f} min")

    st.markdown("**Répartition des retards au rendu**")
    buckets = an.delay_buckets(df)
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
    st.altair_chart(bars + labels, use_container_width=True)
    st.caption("Locations terminées dont le retard est connu. « À l'heure ou en avance » regroupe les retards inférieurs ou égaux à 0.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Qui est concerné par les retards ?**")
        breakdown = an.delay_breakdown(df)
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
        st.caption("Passer la souris sur une part pour voir le nombre et le pourcentage.")
    with right:
        st.markdown("**Part de retards par type de check-in**")
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
        st.caption("Locations dont le retard n'est pas renseigné exclues.")

    st.subheader("Quel impact sur le conducteur suivant ?")
    c1, c2, c3 = st.columns(3)
    c1.metric("Locations qui suivent une autre location", f"{k['n_adjacent']}", f"{k['share_adjacent']:.1%} des locations", delta_color="off")
    c2.metric("Cas problématiques", f"{k['n_problematic']}", help="La location précédente a rendu la voiture après le début de celle-ci")
    c3.metric("…annulés ensuite", f"{k['n_canceled_after_problem']}")
    adj = an.adjacent_rentals(df)
    problem = adj[adj["problematic"]]
    if len(problem):
        waiting = (problem["prev_delay"] - problem["time_delta_with_previous_rental_in_minutes"]).clip(lower=0)
        st.write(
            f"Dans les cas problématiques, le conducteur suivant attend en médiane **{waiting.median():.0f} min** "
            f"(9 cas sur 10 sous {waiting.quantile(0.9):.0f} min)."
        )

    # ================================================================== 2. Choix du seuil
    st.header("2. Choisir le délai minimum")
    threshold = st.slider("Délai minimum entre deux locations (minutes)", 0, 720, 120, step=30)
    table = an.threshold_table(df)
    row = table[table["threshold"] == threshold].iloc[0]

    left, right = st.columns(2)
    with left:
        m1, m2 = st.columns(2)
        m1.metric("Locations bloquées", f"{int(row['blocked'])}", help="Locations terminées dont l'écart avec la précédente est inférieur au seuil")
        m2.metric(
            "Part des locations bloquées",
            f"{row['share_blocked']:.1%}",
            help="Locations bloquées / locations terminées. Approximation de la part du revenu des propriétaires touchée (le prix de chaque location n'est pas dans les données)",
        )
        st.metric("Cas problématiques résolus", f"{int(row['solved'])} / {k['n_problematic']}")
        m4, m5 = st.columns(2)
        m4.metric("Part des problèmes résolus", f"{row['solved_share']:.0%}")
        m5.metric(
            "Résolus / locations terminées",
            f"{row['solved_pct_ended']:.1%}".replace(".", ","),
            help="Cas problématiques résolus / locations terminées : part de l'ensemble des locations terminées dont le problème est évité grâce au seuil",
        )

        hist = an.gap_histogram(df, threshold)
        order = [f"{v}" for v in range(0, 720, 30)] + ["720+"]
        gap_chart = (
            alt.Chart(hist)
            .mark_bar()
            .encode(
                x=alt.X("Écart:N", sort=order, title="Écart avec la location précédente (min)", axis=alt.Axis(labelAngle=0, labelOverlap=True)),
                y=alt.Y("Nombre:Q", title="Nombre de locations"),
                color=alt.Color(
                    "Catégorie:N",
                    scale=alt.Scale(domain=an.GAP_CATEGORIES, range=["#C9D3D9", DARK, "#F4B183", ORANGE]),
                    legend=alt.Legend(orient="bottom", title=None, columns=2),
                ),
                order=alt.Order("Ordre:Q", sort="ascending"),
                tooltip=["Écart", "Catégorie", "Nombre"],
            )
            .properties(height=320)
        )
        st.altair_chart(gap_chart, use_container_width=True)
    with right:
        shown = pd.DataFrame(
            {
                "Seuil (min)": table["threshold"],
                "Bloquées": table["blocked"],
                "Part bloquée": table["share_blocked"].map(pct1),
                "Résolus": table["solved"],
                "Part résolue": table["solved_share"].map(pct0),
                "Résolus / terminées": table["solved_pct_ended"].map(pct1),
            }
        )

        def highlight(r):
            style = "background-color: #C3FFFC; color: #0E3449; font-weight: bold" if r["Seuil (min)"] == threshold else ""
            return [style] * len(r)

        st.dataframe(
            shown.style.apply(highlight, axis=1),
            hide_index=True,
            use_container_width=True,
            height=520,
        )

    # ================================================================== 3. Connect ou non ?
    st.header("3. Toutes les voitures ou seulement Connect ?")
    st.markdown(f"Pour un délai minimum de **{threshold} min**, effet de la mesure selon le type de check-in.")
    compare = an.compare_scopes(df, threshold)
    compare_shown = pd.DataFrame(
        {
            "Périmètre": compare["Périmètre"],
            "Locations": compare["Locations"],
            "Cas problématiques": compare["Cas problématiques"],
            "Bloquées": compare["Locations bloquées"],
            "Part bloquée": compare["Part bloquée"].map(pct1),
            "Résolus": compare["Cas résolus"],
            "Part résolue": compare["Part des problèmes résolus"].map(pct0),
            "Résolus / terminées": compare["Cas résolus / locations terminées"].map(pct1),
        }
    )
    st.dataframe(compare_shown, hide_index=True, use_container_width=True)

    st.caption(
        "Les voitures Connect ont un check-in sans contact : le retard y est moins fréquent, mais les locations s'enchaînent plus souvent, "
        "donc un même seuil bloque une plus grande part de leurs locations."
    )

    with st.expander("Définitions et hypothèses"):
        st.markdown(
            """
- **Location adjacente** : location dont la voiture a été louée juste avant (l'écart avec la précédente est connu).
- **Cas problématique** : la location précédente a été rendue en retard, après le début de la suivante (retard > écart).
- **Délai minimum T** : une location est refusée si elle commence moins de T minutes après la fin de la précédente.
- **Part des locations bloquées** : locations terminées bloquées / locations terminées. C'est une approximation de la part du revenu affectée, car le prix de chaque location n'est pas dans les données.
- **Cas résolus** : cas problématiques dont l'écart est inférieur à T (la location problématique n'aurait pas eu lieu).
- **Cas résolus / locations terminées** : cas résolus rapportés à l'ensemble des locations terminées.
- Limite : on suppose que les locations bloquées ne sont pas reportées sur un autre créneau.
            """
        )

# ================================================================== Onglet : prédiction de prix (appel à l'API)
with tab_price:
    st.header("Prédiction de prix")
    st.markdown(
        "Renseignez les caractéristiques d'une voiture : le dashboard interroge l'API de prix "
        f"([documentation de l'API]({pred.API_URL}/docs)) et affiche le prix de location suggéré par jour."
    )
    with st.form("price_form"):
        c1, c2, c3, c4 = st.columns(4)
        brand = c1.selectbox("Choisissez une marque", pred.BRANDS, index=pred.BRANDS.index("Citroën"))
        fuel = c2.selectbox("Choisissez un carburant", list(pred.FUELS), format_func=pred.FUELS.get)
        color = c3.selectbox("Choisissez une couleur", list(pred.COLORS), format_func=pred.COLORS.get, index=1)
        car_type = c4.selectbox("Choisissez un type de véhicule", list(pred.CAR_TYPES), format_func=pred.CAR_TYPES.get)
        c1, c2 = st.columns(2)
        mileage = c1.number_input("Saisissez le kilométrage", min_value=1, max_value=1_000_000, value=140_000, step=1000)
        power = c2.number_input("Saisissez la puissance du moteur (chevaux)", min_value=1, max_value=500, value=120, step=5)
        cols = st.columns(4)
        options = {
            name: cols[i % 4].checkbox(label) for i, (name, label) in enumerate(pred.OPTIONS.items())
        }
        submitted = st.form_submit_button("Prédire le prix")
    if submitted:
        car = {
            "model_key": brand, "mileage": int(mileage), "engine_power": int(power),
            "fuel": fuel, "paint_color": color, "car_type": car_type, **options,
        }
        try:
            with st.spinner("Appel de l'API (le premier appel peut prendre un moment si le service était en veille)…"):
                price = pred.predict_price(car)
            st.success(f"Prix de location suggéré : **{price:.0f} € par jour**")
            st.caption("Erreur moyenne du modèle : environ 10,7 € par jour sur des voitures jamais vues.")
        except ValueError as exc:
            st.error(f"L'API a refusé la saisie : {exc}")
        except Exception as exc:  # API injoignable, délai dépassé, etc.
            st.error(f"L'API n'a pas répondu ({type(exc).__name__}). Réessayez dans quelques instants.")
