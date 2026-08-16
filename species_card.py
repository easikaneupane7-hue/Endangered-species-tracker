"""
species_card.py

Renders a species' data as a visually structured profile — image, status
badge, description block, then alternating "section title + content" blocks
— instead of a flat st.dataframe of rows and columns.

Usage (e.g. inside show_home() in app.py, or in pages/search.py):

    from species_card import render_species_profile

    render_species_profile(
        species_name=selected_species,
        feature_lookup=feature_lookup,   # dict: lower-cased feature name -> display value
        image_source=image_source,       # url or local path, already resolved
        dark=False,                      # True for a glass/dark card on busy backgrounds
    )
"""

import streamlit as st
from app_theme import status_color, decor_divider

# Which feature keys map to which section, and how sections are titled.
# Anything not matched here falls into "Additional details" automatically.
SECTION_MAP = [
    ("Conservation Status", ["iucn status", "status", "conservation status"]),
    ("Population", ["population", "population size", "population trend"]),
    ("Habitat", ["habitat", "range", "distribution", "region"]),
    ("Threats", ["threats", "threat", "risk factors"]),
    ("Diet & Behavior", ["diet", "behavior", "behaviour", "feeding"]),
]

IGNORE_KEYS = {"description", "image url", "image", "image link", "photo", "photo url", "image_url"}


def _find_status(feature_lookup: dict) -> str | None:
    for key in ("iucn status", "status", "conservation status"):
        if feature_lookup.get(key):
            return feature_lookup[key]
    return None


def render_species_profile(species_name: str, feature_lookup: dict, image_source: str | None, dark: bool = False):
    card_class = "info-card-dark" if dark else "info-card"
    status = _find_status(feature_lookup)
    description = feature_lookup.get("description")

    # --- Header: image + name + status badge, side by side ---
    header_col, image_col = st.columns([2, 1], vertical_alignment="center")
    with header_col:
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        st.markdown(f"### {species_name}")
        if status:
            color = status_color(status)
            st.markdown(
                f'<span class="status-badge" style="background:{color};">{status}</span>',
                unsafe_allow_html=True,
            )
        if description and description != "Data Not Available":
            st.markdown(f"<p style='margin-top:0.8rem;'>{description}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with image_col:
        if image_source:
            st.image(image_source, width="stretch")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    decor_divider()

    # --- Alternating section blocks ---
    used_keys = {"description", *sum([keys for _, keys in SECTION_MAP], [])}
    shown_any = False

    for title, keys in SECTION_MAP:
        value = next((feature_lookup[k] for k in keys if feature_lookup.get(k)), None)
        if not value:
            continue
        shown_any = True
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        st.markdown(f'<div class="info-card-title">{title}</div>', unsafe_allow_html=True)
        st.write(value)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Anything left over goes into a final "Additional details" card ---
    leftover = {
        k: v for k, v in feature_lookup.items()
        if k not in used_keys and k not in IGNORE_KEYS and v
    }
    if leftover:
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        st.markdown('<div class="info-card-title">Additional details</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (key, value) in enumerate(leftover.items()):
            with cols[i % 2]:
                st.markdown(f"**{key.title()}**")
                st.caption(value)
        st.markdown("</div>", unsafe_allow_html=True)
        shown_any = True

    if not shown_any and not description:
        st.caption("No further details are available for this species.")