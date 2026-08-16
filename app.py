import importlib
import sys

import pandas as pd
import streamlit as st

from auth_utils import ensure_authenticated
from shared import (
    extract_population_locations,
    get_estimated_habitat_location,
    get_iucn_nepal_country_marker,
    load_species_data,
)
from utils import PLACEHOLDER_IMAGE, display_value, resolve_display_image
from app_theme import show_splash, apply_theme, loading_animation, decor_divider
from species_card import render_species_profile


st.set_page_config(
    page_title="Endangered Species Tracker",
    page_icon=":material/public:",
    layout="wide",
)

if not ensure_authenticated():
    st.stop()

# One-time animated opening screen for this browser session
show_splash()


IMAGE_FEATURES = ("image url", "image", "image link", "photo", "photo url", "image_url")


def show_home():
    apply_theme("home")

    st.title("Endangered Species Tracker", anchor=False)
    st.caption("Explore species data, monitor conservation signals, and protect what remains.")

    with loading_animation("Fetching species data..."):
        species = load_species_data()
    if species.empty:
        st.warning("No species data is available right now.", icon=":material/info:")
        return

    total_species = int(species["species_name"].nunique())
    total_features = int(species["feature_name"].nunique())
    image_rows = species[
        species["feature_name"].astype(str).str.strip().str.casefold().isin(IMAGE_FEATURES)
    ]
    metrics = st.columns(3)
    metrics[0].metric("Species tracked", total_species)
    metrics[1].metric("Conservation features", total_features)
    metrics[2].metric("Profiles with images", int(image_rows["species_name"].nunique()))

    st.subheader("Featured species", anchor=False)
    image_species = image_rows["species_name"].dropna().astype(str).str.strip().unique()
    sample_species = sorted(image_species)[:8]
    if not sample_species:
        sample_species = sorted(species["species_name"].dropna().astype(str).unique())[:8]

    if not sample_species:
        st.caption("No named species are available in the current dataset.")
        return

    st.caption("Choose a species to inspect its conservation records and image.")
    cols = st.columns(min(4, len(sample_species)))
    for index, species_name in enumerate(sample_species):
        with cols[index % len(cols)]:
            if st.button(species_name, key=f"species_suggestion_{index}", width="stretch"):
                st.session_state["selected_species_profile"] = species_name

    selected_species = st.session_state.get("selected_species_profile")
    if not selected_species:
        return

    selected_data = species[species["species_name"].astype(str) == selected_species]
    if selected_data.empty:
        st.info("No matching records were found for this species.", icon=":material/info:")
        return

    st.subheader(f"{selected_species} profile", anchor=False)
    decor_divider()
    feature_lookup = {}
    for _, row in selected_data.iterrows():
        feature_key = str(row["feature_name"]).strip().casefold()
        feature_lookup[feature_key] = display_value(row.get("raw_value", row.get("value", pd.NA)))

    image_url = next((feature_lookup[key] for key in IMAGE_FEATURES if feature_lookup.get(key)), None)
    image_source = resolve_display_image(image_url) or str(PLACEHOLDER_IMAGE)

    # --- New: presentable, IUCN-style profile card instead of raw table ---
    render_species_profile(selected_species, feature_lookup, image_source, dark=True)

    st.markdown("#### Distribution map")
    locations = extract_population_locations(selected_data)
    if locations.empty:
        estimated_habitat = get_estimated_habitat_location(selected_species)
        if not estimated_habitat.empty:
            st.map(estimated_habitat, latitude="latitude", longitude="longitude", size="marker_size", zoom=6, height=320)
            st.warning("Estimated habitat location — not a population survey point.", icon=":material/info:")
            st.dataframe(
                estimated_habitat[["area", "estimate_note"]],
                column_config={"area": "Estimated habitat area", "estimate_note": "Map note"},
                hide_index=True,
                width="stretch",
            )
        else:
            country_marker = get_iucn_nepal_country_marker(selected_species)
            if country_marker.empty:
                st.caption("No map record is available for this species yet.")
            else:
                st.map(country_marker, latitude="latitude", longitude="longitude", size="marker_size", zoom=6, height=320)
                st.caption("Nepal country-level Red List reference. It is not a population observation.")
    else:
        st.map(
            locations,
            latitude="latitude",
            longitude="longitude",
            size="marker_size",
            zoom=5,
            height=320,
        )
        st.caption("Larger markers represent more individuals recorded at that location.")
        st.dataframe(
            locations[["Area", "Count"]].sort_values("Count", ascending=False),
            column_config={"Count": st.column_config.NumberColumn("Individuals recorded", format="%.0f")},
            hide_index=True,
            width="stretch",
        )

    with st.expander("Full raw records"):
        st.markdown("#### Related features")
        feature_summary = (
            selected_data.groupby("feature_name")["value"].sum().sort_values(ascending=False).reset_index()
        )
        st.dataframe(feature_summary, width="stretch", hide_index=True)
        st.markdown("#### Full records")
        st.dataframe(selected_data.sort_values("value", ascending=False), width="stretch", hide_index=True)


def load_page(module_name: str):
    if module_name in sys.modules:
        module = importlib.reload(sys.modules[module_name])
    else:
        module = importlib.import_module(module_name)
    return getattr(module, "render")


page = st.sidebar.radio(
    "Navigate",
    ["Home", "Dashboard", "Search", "Overview", "Feedback", "Settings", "Policies"],
    key="page_nav",
)

if st.session_state.get("_last_page") != page:
    st.session_state.pop("selected_species_profile", None)
    st.session_state["_last_page"] = page

if page == "Home":
    show_home()
elif page == "Dashboard":
    load_page("pages.dashboard")()
elif page == "Search":
    load_page("pages.search")()
elif page == "Overview":
    load_page("pages.overview")()
elif page == "Feedback":
    load_page("pages.feedback")()
elif page == "Settings":
    load_page("pages.settings")()
elif page == "Policies":
    load_page("pages.policies")()

st.sidebar.caption(f"Signed in as: {st.session_state.get('current_user', 'user')}")

from floating_chat import render_floating_chat
render_floating_chat()