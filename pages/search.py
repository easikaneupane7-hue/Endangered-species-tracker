import pandas as pd
import streamlit as st

from auth_utils import ensure_authenticated
from shared import (
    extract_population_locations,
    get_estimated_habitat_location,
    get_iucn_nepal_country_marker,
    load_species_data,
)
from utils import display_value, normalise_status, resolve_display_image, status_badge_color
from app_theme import decor_divider, loading_animation
from species_card import render_species_profile

PAGE_STYLE = """
<style>

.stApp {
    background: #0c1210;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 10% 12%, rgba(115, 224, 163, 0.16), transparent 28rem),
        radial-gradient(circle at 90% 4%, rgba(235, 154, 83, 0.14), transparent 25rem),
        linear-gradient(145deg, #0b1411 0%, #10271d 52%, #0a1814 100%);
    min-height: 100vh;
    overflow: hidden;
}
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    z-index: 0;
    border-radius: 999px;
    filter: blur(10px);
    pointer-events: none;
    animation: drift 14s ease-in-out infinite alternate;
}
[data-testid="stAppViewContainer"]::before {
    width: 24rem; height: 24rem; right: -8rem; top: 30%;
    background: rgba(57, 166, 111, 0.15);
}
[data-testid="stAppViewContainer"]::after {
    width: 17rem; height: 17rem; left: -7rem; bottom: 5%;
    background: rgba(203, 126, 67, 0.12);
    animation-delay: -7s;
}
[data-testid="stMainBlockContainer"] {
    position: relative;
    z-index: 1;
}
@keyframes drift {
    from { transform: translate3d(-14px, -10px, 0) scale(0.96); }
    to { transform: translate3d(22px, 20px, 0) scale(1.08); }
}
.iucn-hero {
    background: linear-gradient(120deg, rgba(21, 70, 48, 0.96), rgba(38, 116, 72, 0.92) 58%, rgba(91, 148, 86, 0.9));
    border: 1px solid rgba(210, 255, 216, 0.28);
    border-radius: 24px;
    color: white;
    padding: 2rem 2.2rem;
    margin: 0.2rem 0 1.5rem;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
    animation: hero-enter 600ms ease-out both;
}
.iucn-hero h1 { color: white; font-size: 2.1rem; margin: 0 0 0.35rem; }
.iucn-hero p { color: #e6f3e9; font-size: 1.02rem; margin: 0; }
@keyframes hero-enter {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, rgba(22, 49, 35, 0.96), rgba(15, 35, 25, 0.96));
    border: 1px solid rgba(126, 218, 153, 0.32);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.16);
    transition: transform 180ms ease, box-shadow 180ms ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 34px rgba(0, 0, 0, 0.22);
}
.stButton > button {
    transition: transform 160ms ease, box-shadow 160ms ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(17, 77, 43, 0.22);
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: 1ms !important; transition-duration: 1ms !important; }
}
</style>
"""
IMAGE_FEATURES = ("image url", "image", "image link", "photo", "photo url", "image_url")

def _matches_query(data: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query.strip():
        return data
    term = query.strip()
    return data[
        data["feature_name"].astype(str).str.contains(term, case=False, regex=False, na=False)
        | data["species_name"].astype(str).str.contains(term, case=False, regex=False, na=False)
        | data["raw_value"].astype(str).str.contains(term, case=False, regex=False, na=False)
    ]


def _profile_data(data: pd.DataFrame) -> list[dict[str, str]]:
    profiles = []
    for name, group in data.groupby("species_name", sort=True):
        values = {
            str(row["feature_name"]).strip().casefold(): display_value(row["raw_value"])
            for _, row in group.iterrows()
        }
        status = next(
            (values[key] for key in ("iucn status", "conservation status", "status") if key in values),
            "Data Deficient",
        )
        profiles.append(
            {
                "name": str(name),
                "status": normalise_status(status),
                "scientific": next((values[key] for key in ("scientific name", "scientific_name") if key in values), "Scientific name not recorded"),
                "habitat": values.get("habitat", "Habitat not recorded"),
                "population": next((values[key] for key in ("population", "population estimate", "current population") if key in values), "Population not recorded"),
            }
        )
    return profiles


def _open_profile(species_name: str) -> None:
    st.session_state["selected_species_profile"] = species_name


def _close_profile() -> None:
    st.session_state.pop("selected_species_profile", None)


@st.dialog("Species profile", width="large", icon=":material/pets:")
def _show_profile_dialog(species_name: str, records: pd.DataFrame) -> None:
    # Build a display-ready feature lookup, same shape the home page card
    # component expects — so the profile looks the same everywhere it opens.
    feature_lookup = {
        str(row["feature_name"]).strip().casefold(): display_value(row["raw_value"])
        for _, row in records.iterrows()
    }
    image_value = next((feature_lookup[key] for key in IMAGE_FEATURES if feature_lookup.get(key)), None)
    image_source = resolve_display_image(image_value) if image_value else None

    # --- Presentable, IUCN-style card (same component the home page uses) ---
    render_species_profile(species_name, feature_lookup, image_source, dark=True)
    decor_divider()

    st.markdown("#### Distribution map")
    locations = extract_population_locations(records)
    if locations.empty:
        estimated_habitat = get_estimated_habitat_location(species_name)
        if not estimated_habitat.empty:
            st.map(estimated_habitat, latitude="latitude", longitude="longitude", size="marker_size", zoom=6, height=340)
            st.warning("Estimated habitat location — not a population survey point.", icon=":material/info:")
            st.dataframe(
                estimated_habitat[["area", "estimate_note"]],
                column_config={"area": "Estimated habitat area", "estimate_note": "Map note"},
                hide_index=True,
                width="stretch",
            )
        else:
            country_marker = get_iucn_nepal_country_marker(species_name)
            if country_marker.empty:
                st.caption("No map record is available for this species yet.")
                st.code("Add `Population locations`: Chitwan | 27.5291 | 84.3542 | 22; Mustang | 28.9985 | 83.8473 | 5", language=None)
            else:
                st.map(country_marker, latitude="latitude", longitude="longitude", size="marker_size", zoom=6, height=340)
                st.caption("Nepal country-level Red List reference. It is not a population observation.")
    else:
        st.map(
            locations,
            latitude="latitude",
            longitude="longitude",
            size="marker_size",
            zoom=6,
            height=340,
        )
        st.caption("Marker size represents the number found in each recorded Nepal area.")
        st.dataframe(
            locations[["Area", "Count"]].sort_values("Count", ascending=False),
            column_config={"Count": st.column_config.NumberColumn("Individuals recorded", format="%.0f")},
            hide_index=True,
            width="stretch",
        )

    with st.expander("Full conservation records"):
        details = records[["feature_name", "raw_value"]].copy()
        details.columns = ["Conservation field", "Recorded detail"]
        st.dataframe(
            details.sort_values("Conservation field"),
            column_config={
                "Conservation field": st.column_config.TextColumn(pinned=True),
                "Recorded detail": st.column_config.TextColumn(width="large"),
            },
            hide_index=True,
            width="stretch",
            height=420,
        )
    if st.button("Close profile", icon=":material/close:"):
        _close_profile()
        st.rerun()


def render():
    if not ensure_authenticated():
        return

    with loading_animation("Fetching species data..."):
        species = load_species_data()
    if species.empty:
        st.warning("No data rows were returned.", icon=":material/info:")
        return

    st.markdown(PAGE_STYLE, unsafe_allow_html=True)
    st.markdown(
        """<section class="iucn-hero"><h1>Species explorer</h1>
        <p>Search, compare, and understand the conservation records in your tracker.</p></section>""",
        unsafe_allow_html=True,
    )

    st.session_state.setdefault("global_species_query", "")
    st.session_state.setdefault("recent_species_searches", [])
    species_options = sorted(species["species_name"].dropna().astype(str).unique())

    st.markdown("#### Quick search")
    suggestion = st.pills(
        "Quick species search",
        species_options[:6],
        selection_mode="single",
        key="quick_species_search",
        label_visibility="collapsed",
    )
    if suggestion:
        st.session_state["global_species_query"] = suggestion
        st.session_state["selected_species_profile"] = suggestion

    query = st.text_input(
        "Search the tracker",
        key="global_species_query",
        placeholder="Try a species name, habitat, threat, or status",
        icon=":material/search:",
    )
    selected_species = st.multiselect("Limit to species", species_options, placeholder="All species")

    filtered = _matches_query(species, query)
    if selected_species:
        filtered = filtered[filtered["species_name"].astype(str).isin(selected_species)]

    if query.strip() and not selected_species and query.strip() not in st.session_state["recent_species_searches"]:
        st.session_state["recent_species_searches"] = [query.strip(), *st.session_state["recent_species_searches"]][:5]
    if st.session_state["recent_species_searches"]:
        st.caption("Recent: " + "  •  ".join(st.session_state["recent_species_searches"]))

    metrics = st.columns(3)
    metrics[0].metric("Matching records", int(len(filtered)))
    metrics[1].metric("Species found", int(filtered["species_name"].nunique()))
    metrics[2].metric("Conservation features", int(filtered["feature_name"].nunique()))

    st.markdown("#### IUCN status guide")
    legend = st.columns(5)
    for column, (label, color) in zip(
        legend,
        [("Least Concern", "green"), ("Vulnerable", "yellow"), ("Endangered", "orange"), ("Critically Endangered", "red"), ("Extinct", "gray")],
    ):
        with column:
            st.badge(label, color=color)

    if filtered.empty:
        st.info("No matching records. Try a shorter or different term.", icon=":material/search_off:")
        return

    st.subheader("Species profiles", anchor=False)
    profiles = _profile_data(filtered)
    profile_limit = 20
    shown_profiles = profiles[:profile_limit]
    for start in range(0, len(shown_profiles), 2):
        columns = st.columns(2)
        for column, profile in zip(columns, shown_profiles[start : start + 2]):
            with column.container(border=True):
                st.markdown(f"#### {profile['name']}")
                st.badge(profile["status"], color=status_badge_color(profile["status"]))
                st.caption(profile["scientific"])
                st.write(f":material/forest: **Habitat:** {profile['habitat']}")
                st.write(f":material/groups: **Population:** {profile['population']}")
                st.button(
                    "Open full profile",
                    key=f"open_profile_{profile['name']}",
                    icon=":material/visibility:",
                    width="stretch",
                    on_click=_open_profile,
                    args=(profile["name"],),
                )

    if len(profiles) > profile_limit:
        st.caption(
            f"Showing {profile_limit} of {len(profiles)} matching species — "
            "narrow your search to see the rest."
        )

    selected_profile = st.session_state.get("selected_species_profile")
    if selected_profile:
        full_profile = species[species["species_name"].astype(str) == selected_profile]
        if not full_profile.empty:
            _show_profile_dialog(selected_profile, full_profile)

    st.subheader("Conservation records", anchor=False)
    display_records = filtered[["species_name", "feature_name", "raw_value"]].copy()
    display_records.columns = ["Species", "Feature", "Recorded detail"]
    st.dataframe(
        display_records.sort_values(["Species", "Feature"]),
        column_config={
            "Species": st.column_config.TextColumn(pinned=True),
            "Feature": st.column_config.TextColumn(),
            "Recorded detail": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        width="stretch",
        height=420,
    )