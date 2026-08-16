from pathlib import Path
import re

import pandas as pd
import streamlit as st

from data_loader import load_google_sheet_data


DISTRIBUTION_FIELDS = {
    "nepal locations",
    "nepal distribution",
    "location counts",
    "distribution records",
    "population locations",
    "population distribution",
    "distribution locations",
}

IUCN_NEPAL_DATA_PATH = Path(__file__).resolve().parent / "assets" / "data" / "iucn_nepal_red_list.csv"
ESTIMATED_HABITAT_DATA_PATH = Path(__file__).resolve().parent / "assets" / "data" / "estimated_nepal_habitats.csv"


def _normalise_species_name(value: object) -> str:
    """Create a forgiving match key for spreadsheet and Red List species names."""
    text = re.sub(r"\([^)]*\)", "", str(value)).casefold()
    return "".join(character for character in text if character.isalnum())


@st.cache_data
def load_iucn_nepal_map_source() -> pd.DataFrame:
    """Load the Red List CSV only as a country-level map reference source."""
    if not IUCN_NEPAL_DATA_PATH.exists():
        return pd.DataFrame()

    source = pd.read_csv(IUCN_NEPAL_DATA_PATH)
    required_columns = {"Species or Taxon", "Common Names", "Countries", "Scope", "Year Assessed"}
    if not required_columns.issubset(source.columns):
        raise ValueError("The IUCN Nepal CSV does not have the expected Red List columns.")

    source = source[source["Countries"].astype(str).str.contains("Nepal", case=False, na=False)].copy()
    source["_is_national"] = source["Scope"].astype(str).str.strip().eq("National")
    source["_year"] = pd.to_numeric(source["Year Assessed"], errors="coerce").fillna(0)
    source = source.sort_values(["_is_national", "_year"], ascending=[False, False])
    aliases = []
    for _, row in source.iterrows():
        names = [row["Species or Taxon"], *str(row.get("Common Names", "")).split(";")]
        for name in names:
            match_key = _normalise_species_name(name)
            if match_key:
                aliases.append({"match_key": match_key, "Status": row.get("Status", ""), "Year Assessed": row["Year Assessed"], "Scope": row["Scope"]})
    return pd.DataFrame(aliases).drop_duplicates("match_key", keep="first")


def get_iucn_nepal_country_marker(species_name: str) -> pd.DataFrame:
    """Return one Nepal marker when a spreadsheet species matches the Red List CSV.

    The CSV has country presence but no observation coordinates or population counts,
    so this marker represents Nepal only and is never presented as a population point.
    """
    source = load_iucn_nepal_map_source()
    if source.empty:
        return pd.DataFrame(columns=["latitude", "longitude", "marker_size", "map_scope"])

    matched = source[source["match_key"] == _normalise_species_name(species_name)]
    map_scope = "IUCN Red List Nepal presence" if not matched.empty else "Nepal reference map"
    status = str(matched.iloc[0]["Status"]).strip().splitlines()[0] if not matched.empty else "No exact Red List match"
    assessment_year = matched.iloc[0]["Year Assessed"] if not matched.empty else pd.NA
    return pd.DataFrame(
        [{
            "latitude": 28.3949,
            "longitude": 84.1240,
            "marker_size": 20_000,
            "map_scope": map_scope,
            "iucn_status": status,
            "assessment_year": assessment_year,
        }]
    )


@st.cache_data
def load_estimated_habitat_locations() -> pd.DataFrame:
    """Load the separate, non-census Nepal habitat reference points."""
    if not ESTIMATED_HABITAT_DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(ESTIMATED_HABITAT_DATA_PATH)


def get_estimated_habitat_location(species_name: str) -> pd.DataFrame:
    """Return the estimated habitat marker for a spreadsheet species, if available."""
    habitats = load_estimated_habitat_locations()
    if habitats.empty:
        return pd.DataFrame(columns=["latitude", "longitude", "marker_size"])

    match_key = _normalise_species_name(species_name)
    matching = habitats[habitats["species_name"].map(_normalise_species_name) == match_key]
    if matching.empty:
        return pd.DataFrame(columns=["latitude", "longitude", "marker_size"])

    marker = matching.iloc[[0]].copy()
    marker["marker_size"] = 14_000
    return marker


def load_species_data():
    try:
        species = load_google_sheet_data()
    except Exception as exc:
        st.error(f"Unable to load the Google Sheet: {exc}")
        st.stop()
        return pd.DataFrame(columns=["feature_name", "species_name", "value"])

    if species.empty:
        return species

    expected_columns = {"feature_name", "species_name", "value"}
    if not expected_columns.issubset(species.columns):
        if {"feature", "species", "value"}.issubset(species.columns):
            species = species.rename(columns={"feature": "feature_name", "species": "species_name"})
        else:
            st.error("The data loader returned an unexpected column structure.")
            st.stop()

    species = species.copy()
    if "value" in species.columns:
        species["raw_value"] = species["value"]
        species["value"] = pd.to_numeric(species["value"], errors="coerce")
    else:
        species["raw_value"] = pd.NA
        species["value"] = pd.NA

    return species


def extract_population_locations(records: pd.DataFrame) -> pd.DataFrame:
    """Return valid population observations stored in species profile fields.

    Values use: ``Place | latitude | longitude | individuals``. Separate
    multiple places with semicolons. For example:
    ``Chitwan | 27.5291 | 84.3542 | 22; Mustang | 28.9985 | 83.8473 | 5``.
    """
    observations = []
    for _, row in records.iterrows():
        if str(row.get("feature_name", "")).strip().casefold() not in DISTRIBUTION_FIELDS:
            continue

        for entry in str(row.get("raw_value", row.get("value", ""))).split(";"):
            parts = [part.strip() for part in entry.split("|")]
            if len(parts) != 4:
                continue
            try:
                latitude, longitude, count = float(parts[1]), float(parts[2]), float(parts[3])
            except ValueError:
                continue

            if -90 <= latitude <= 90 and -180 <= longitude <= 180 and count >= 0:
                observations.append(
                    {
                        "Area": parts[0] or "Unnamed area",
                        "latitude": latitude,
                        "longitude": longitude,
                        "Count": count,
                    }
                )

    locations = pd.DataFrame(observations)
    if not locations.empty:
        highest_count = locations["Count"].max() or 1
        # ``st.map`` sizes are measured in metres. These values keep population
        # markers visible at a country-level Nepal zoom while still showing scale.
        locations["marker_size"] = 4_000 + (locations["Count"] / highest_count * 20_000)
    return locations
