import plotly.express as px
import streamlit as st

from auth_utils import ensure_authenticated
from shared import load_species_data
from app_theme import apply_theme


def render():
    if not ensure_authenticated():
        return

    apply_theme("dashboard")

    species = load_species_data()

    if species.empty:
        st.warning("No data rows were returned.")
        return

    st.title("📊 Dashboard")
    st.caption("Visual summary of species and feature values.")

    display_species = species.copy()

    with st.sidebar:
        st.header("Filters")
        search_term = st.text_input("Search feature", placeholder="e.g. forest")
        available_species = sorted(species["species_name"].dropna().astype(str).unique())
        selected_species = st.multiselect("Species", options=available_species, default=[])

        if search_term:
            display_species = display_species[
                display_species["feature_name"].astype(str).str.contains(search_term, case=False, na=False)
            ]

        if selected_species:
            display_species = display_species[
                display_species["species_name"].astype(str).isin(selected_species)
            ]

        st.divider()
        st.metric("Visible features", int(display_species["feature_name"].nunique()))
        st.metric("Visible species", int(display_species["species_name"].nunique()))
        st.metric("Visible total", f"{display_species['value'].sum():,.2f}")

    if display_species.empty:
        st.warning("No rows match your current filters.")
        return

    # --- Headline metrics inside a glass card instead of bare st.metric row ---
    st.markdown('<div class="info-card-dark">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Features tracked", int(display_species["feature_name"].nunique()))
    c2.metric("Species tracked", int(display_species["species_name"].nunique()))
    c3.metric("Total value", f"{display_species['value'].sum():,.2f}")
    c4.metric("Average value", f"{display_species['value'].mean():,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

    top_species = (
        display_species.groupby("species_name")["value"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    top_species_df = top_species.reset_index()
    top_species_df.columns = ["species_name", "total_value"]

    top_features = (
        display_species.groupby("feature_name")["value"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    top_features_df = top_features.reset_index()
    top_features_df.columns = ["feature_name", "total_value"]

    # Transparent chart backgrounds + light text so charts sit naturally on
    # the dark starfield theme instead of showing a white box.
    chart_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f2f2f2",
        legend=dict(font=dict(color="#f2f2f2")),
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="info-card-dark">', unsafe_allow_html=True)
        fig_species_pie = px.pie(
            top_species_df,
            names="species_name",
            values="total_value",
            title="Top species by total value",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues,
        )
        fig_species_pie.update_layout(**chart_layout)
        st.plotly_chart(fig_species_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="info-card-dark">', unsafe_allow_html=True)
        fig_features_pie = px.pie(
            top_features_df,
            names="feature_name",
            values="total_value",
            title="Top features by total value",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Purples,
        )
        fig_features_pie.update_layout(**chart_layout)
        st.plotly_chart(fig_features_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)