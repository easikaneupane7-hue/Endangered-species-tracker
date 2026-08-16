"""Display helpers shared by the Streamlit interface and search module."""

from math import isnan
from pathlib import Path

import pandas as pd


PLACEHOLDER_IMAGE = Path(__file__).resolve().parent / "assets" / "wildlife-placeholder.svg"
ASSETS_DIRECTORY = PLACEHOLDER_IMAGE.parent.resolve()

MISSING_TEXT = "Data Not Available"
MISSING_VALUES = {"", "nan", "none", "null", "n/a", "na"}

STATUS_NAMES = {
    "lc": "Least Concern", "leastconcern": "Least Concern",
    "vu": "Vulnerable", "vulnerable": "Vulnerable",
    "en": "Endangered", "endangered": "Endangered",
    "cr": "Critically Endangered", "criticallyendangered": "Critically Endangered",
    "nt": "Near Threatened", "nearthreatened": "Near Threatened",
    "ew": "Extinct in the Wild", "extinctinthewild": "Extinct in the Wild",
    "ex": "Extinct", "extinct": "Extinct",
    "re": "Regionally Extinct", "regionallyextinct": "Regionally Extinct",
    "ne": "Not Evaluated", "notevaluated": "Not Evaluated",
    "dd": "Data Deficient", "datadeficient": "Data Deficient",
}

STATUS_COLORS = {
    "Least Concern": "green", "Vulnerable": "yellow", "Endangered": "orange",
    "Critically Endangered": "red", "Extinct in the Wild": "gray",
    "Extinct": "gray", "Regionally Extinct": "gray", "Near Threatened": "blue",
    "Data Deficient": "blue", "Not Evaluated": "gray",
}


def display_value(value: object) -> str:
    """Return a friendly replacement for a missing value from the source data."""
    if value is None or pd.isna(value):
        return MISSING_TEXT
    text = str(value).strip()
    return MISSING_TEXT if text.casefold() in MISSING_VALUES else text


def get_value(species: pd.Series, field: str) -> object:
    """Read a field safely so incomplete workbooks do not break the page."""
    return species.get(field, pd.NA)


def normalise_status(value: object) -> str:
    """Convert IUCN abbreviations such as CR into readable names."""
    status = display_value(value)
    key = "".join(character for character in status.casefold() if character.isalnum())
    return STATUS_NAMES.get(key, status)


def status_badge_color(status: object) -> str:
    """Choose a badge colour for a recognised IUCN status."""
    return STATUS_COLORS.get(normalise_status(status), "gray")


def as_number(value: object) -> float | None:
    """Convert source text or numbers to a float, returning None when unavailable."""
    if value is None or pd.isna(value):
        return None
    try:
        text = str(value).replace(",", "").replace("%", "").strip()
        number = float(text)
        return None if isnan(number) else number
    except (TypeError, ValueError):
        return None


def resolve_image_path(value: object) -> str | None:
    """Return a local image under assets/; deliberately never fetch remote URLs."""
    text = display_value(value)
    if text == MISSING_TEXT or text.startswith(("https://", "http://", "file://")):
        return None
def resolve_display_image(value: object) -> str | None:
    """Return an image source for st.image(): a safe local asset path if one
    exists, otherwise a direct remote URL from the spreadsheet (the browser
    fetches it — nothing happens server-side, so this is safe to allow)."""
    text = display_value(value)
    if text == MISSING_TEXT:
        return None

    if text.startswith(("https://", "http://")):
        return text

    return resolve_image_path(text)
    try:
        candidate = Path(text)
        if not candidate.is_absolute():
            candidate = ASSETS_DIRECTORY.parent / candidate
        candidate = candidate.resolve()
        if candidate.is_file() and candidate.is_relative_to(ASSETS_DIRECTORY):
            return str(candidate)
    except (OSError, ValueError):
        return None
    return None