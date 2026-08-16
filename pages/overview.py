import pandas as pd
import plotly.express as px
import streamlit as st

from auth_utils import ensure_authenticated
from shared import load_species_data
from utils import display_value, normalise_status, status_badge_color
from app_theme import apply_theme, decor_divider, loading_animation, status_color

# Consistent ordering for the breakdown, worst-off first.
STATUS_ORDER = [
    "Extinct",
    "Extinct In The Wild",
    "Critically Endangered",
    "Endangered",
    "Vulnerable",
    "Near Threatened",
    "Least Concern",
    "Data Deficient",
]


def _status_counts(species_df: pd.DataFrame) -> pd.DataFrame:
    """Count distinct species per normalised IUCN status."""
    counts: dict[str, int] = {}
    for _, group in species_df.groupby("species_name"):
        values = {
            str(row["feature_name"]).strip().casefold(): display_value(row.get("raw_value", row.get("value")))
            for _, row in group.iterrows()
        }
        raw_status = next(
            (values[key] for key in ("iucn status", "conservation status", "status") if key in values),
            "Data Deficient",
        )
        status = normalise_status(raw_status)
        counts[status] = counts.get(status, 0) + 1

    ordered_keys = [s for s in STATUS_ORDER if s in counts] + [s for s in counts if s not in STATUS_ORDER]
    return pd.DataFrame(
        {"status": ordered_keys, "species_count": [counts[s] for s in ordered_keys]}
    )


def render():
    if not ensure_authenticated():
        return

    apply_theme("overview")

    with loading_animation("Fetching species data..."):
        species = load_species_data()

    if species.empty:
        st.warning("No data rows were returned.")
        return

    st.title("📋 Overview")
    st.caption("Complete snapshot of the dataset in one place.")

    st.markdown('<div class="info-card-dark">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Features", int(species["feature_name"].nunique()))
    st.caption("This shows the number of distinct conservation features represented in the dataset, giving a quick sense of the breadth of the information.")
    col2.metric("Species", int(species["species_name"].nunique()))
    st.caption("This indicates how many unique endangered species are included, helping you understand the scope of the dataset.")
    col3.metric("Total value", f"{species['value'].sum():,.2f}")
    st.caption("This summarizes the combined value of all records, reflecting the overall magnitude of the dataset.")
    col4.metric("Average value", f"{species['value'].mean():,.2f}")
    st.caption("This highlights the typical value of a single record, offering a simple average-based reference point.")
    st.markdown("</div>", unsafe_allow_html=True)

    decor_divider()

    # --- New: IUCN conservation status breakdown ---
    st.subheader("Conservation status breakdown", anchor=False)
    st.caption("How many tracked species fall into each IUCN status category — from Least Concern to Critically Endangered.")

    status_df = _status_counts(species)

    st.markdown('<div class="info-card-dark">', unsafe_allow_html=True)
    badge_cols = st.columns(len(status_df)) if len(status_df) else []
    for col, (_, row) in zip(badge_cols, status_df.iterrows()):
        with col:
            color = status_color(row["status"])
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <span class="status-badge" style="background:{color};">{row['status']}</span>
                    <div style="font-size:1.6rem; font-weight:800; margin-top:0.4rem;">{row['species_count']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    fig_status = px.bar(
        status_df,
        x="status",
        y="species_count",
        title="Species by conservation status",
        color="status",
        color_discrete_map={row["status"]: status_color(row["status"]) for _, row in status_df.iterrows()},
    )
    fig_status.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f2f2f2",
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Species count",
    )
    st.plotly_chart(fig_status, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    decor_divider()

    st.subheader("Top species")
    st.caption("This section highlights the species contributing the greatest total value, making it easier to spot the most significant entries.")
    top_species = (
        species.groupby("species_name")["value"].sum().sort_values(ascending=False).head(10)
    )
    st.bar_chart(top_species)

    st.subheader("Top features")
    st.caption("This section shows the features that contribute the most value overall, helping you identify the most important categories at a glance.")
    top_features = (
        species.groupby("feature_name")["value"].sum().sort_values(ascending=False).head(10)
    )
    st.bar_chart(top_features)

    with st.expander("All records"):
        st.caption("This table displays every record in the dataset so you can review the full set of information in one place.")
        st.dataframe(
            species.sort_values("value", ascending=False),
            use_container_width=True,
            hide_index=True,
        )