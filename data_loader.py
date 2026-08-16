import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _find_credentials_file() -> Optional[str]:
    search_roots = [
        Path(__file__).resolve().parent,
        Path.cwd(),
        Path(__file__).resolve().parent.parent,
    ]

    seen = set()

    for root in search_roots:
        for candidate in [root, root / ".streamlit"]:
            path = candidate / "credentials.json"
            key = str(path)
            if key not in seen and path.exists():
                return str(path)
            seen.add(key)

    env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.exists(env_path):
        return env_path

    return None


def _load_local_secrets() -> dict:
    candidates = [
        Path(__file__).resolve().parent / ".streamlit" / "secrets.toml",
        Path.cwd() / ".streamlit" / "secrets.toml",
        Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml",
    ]

    for path in candidates:
        if path.exists():
            try:
                with path.open("rb") as fh:
                    return tomllib.load(fh)
            except Exception:
                continue

    return {}


def _get_secret_value(*keys):
    try:
        secrets_dict = st.secrets.to_dict()
    except Exception:
        secrets_dict = {}

    if not secrets_dict:
        secrets_dict = _load_local_secrets()

    current = secrets_dict
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
        if current is None:
            return None
    return current


def _get_service_account_info() -> Optional[dict]:
    try:
        secrets_dict = st.secrets.to_dict()
    except Exception:
        secrets_dict = {}

    if not secrets_dict:
        secrets_dict = _load_local_secrets()

    if "gcp_service_account" in secrets_dict:
        info = dict(secrets_dict["gcp_service_account"])
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        return info

    connections = secrets_dict.get("connections", {})
    if isinstance(connections, dict):
        gsheets = connections.get("gsheets", {})
        if isinstance(gsheets, dict):
            allowed_keys = {
                "type",
                "project_id",
                "private_key_id",
                "private_key",
                "client_email",
                "client_id",
                "auth_uri",
                "token_uri",
                "auth_provider_x509_cert_url",
                "client_x509_cert_url",
                "universe_domain",
            }
            info = {k: v for k, v in gsheets.items() if k in allowed_keys}
            if info:
                if "private_key" in info and isinstance(info["private_key"], str):
                    info["private_key"] = info["private_key"].replace("\\n", "\n")
                return info

    return None


def _get_credentials() -> Credentials:
    try:
        service_account_info = _get_service_account_info()
        if service_account_info:
            return Credentials.from_service_account_info(
                service_account_info,
                scopes=SCOPES,
            )

        credentials_path = _find_credentials_file()
        if not credentials_path:
            raise FileNotFoundError(
                "No credentials.json file was found. Place it in the project folder "
                "or set GOOGLE_APPLICATION_CREDENTIALS."
            )

        return Credentials.from_service_account_file(
            credentials_path,
            scopes=SCOPES,
        )
    except Exception as exc:
        st.error(f"Google authentication failed: {exc}")
        raise


def connect_to_google_sheet():
    try:
        credentials = _get_credentials()
        return gspread.authorize(credentials)
    except Exception as exc:
        st.error(f"Could not initialize the Google Sheets client: {exc}")
        raise


def _normalize_spreadsheet_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None

    match = re.search(r"/d/([a-zA-Z0-9-_]+)", value)
    if match:
        return match.group(1)

    return value


def _get_spreadsheet_id(spreadsheet_id: Optional[str] = None) -> str:
    if spreadsheet_id:
        return _normalize_spreadsheet_id(spreadsheet_id) or ""

    spreadsheet_value = _get_secret_value("connections", "gsheets", "spreadsheet")
    if spreadsheet_value:
        return _normalize_spreadsheet_id(spreadsheet_value) or ""

    spreadsheet_id_value = _get_secret_value("google_sheet", "spreadsheet_id")
    if spreadsheet_id_value:
        return _normalize_spreadsheet_id(spreadsheet_id_value) or ""

    env_id = os.getenv("SPREADSHEET_ID")
    if env_id:
        return _normalize_spreadsheet_id(env_id) or ""

    raise ValueError("Spreadsheet ID is missing. Set it in .streamlit/secrets.toml or as SPREADSHEET_ID.")


@st.cache_data(ttl=30)
def load_google_sheet_data(
    spreadsheet_id: Optional[str] = None, sheet_name: Optional[str] = None
) -> pd.DataFrame:
    try:
        client = connect_to_google_sheet()
        resolved_spreadsheet_id = _get_spreadsheet_id(spreadsheet_id)
        spreadsheet = client.open_by_key(resolved_spreadsheet_id)
    except ValueError as exc:
        st.error(f"Google Sheets configuration error: {exc}")
        raise
    except Exception as exc:
        st.error(
            f"Could not open spreadsheet '{spreadsheet_id or 'unknown'}'. "
            f"Check that the Spreadsheet ID is correct and that the service account "
            f"has access to the file: {exc}"
        )
        raise

    try:
        worksheet = spreadsheet.worksheet(sheet_name) if sheet_name else spreadsheet.get_worksheet(0)
    except Exception as exc:
        target = f"worksheet '{sheet_name}'" if sheet_name else "the first worksheet"
        st.error(f"Could not access {target} in spreadsheet '{resolved_spreadsheet_id}': {exc}")
        raise

    try:
        values = worksheet.get_all_values()
    except Exception as exc:
        st.error(f"Could not read values from the worksheet: {exc}")
        raise

    if not values:
        return pd.DataFrame(columns=["feature_name", "species_name", "value"])

    raw_df = pd.DataFrame(values)
    return transpose_workbook_data(raw_df)


def transpose_workbook_data(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["feature_name", "species_name", "value"])

    if df.shape[1] < 2:
        return pd.DataFrame(columns=["feature_name", "species_name", "value"])

    def _is_non_numeric(value) -> bool:
        text = str(value).strip()
        if not text:
            return False
        try:
            float(text)
            return False
        except ValueError:
            return True

    first_row_values = [str(x).strip() for x in df.iloc[0, 1:].tolist()]
    non_blank_values = [v for v in first_row_values if v]
    use_header = bool(non_blank_values) and all(_is_non_numeric(v) for v in non_blank_values)

    if use_header:
        species_names = [v if v else f"Species {i}" for i, v in enumerate(first_row_values, start=1)]
        data_rows = df.iloc[1:, :]
    else:
        species_names = [f"Species {i}" for i in range(1, df.shape[1])]
        data_rows = df

    if data_rows.empty:
        return pd.DataFrame(columns=["feature_name", "species_name", "value"])

    records = []

    for _, row in data_rows.iterrows():
        feature_name = row.iloc[0] if len(row) > 0 else ""
        if pd.isna(feature_name) or str(feature_name).strip() == "":
            continue

        feature_name = str(feature_name).strip()

        for idx, species_name in enumerate(species_names):
            if idx + 1 >= len(row):
                break

            raw_value = row.iloc[idx + 1]
            if pd.isna(raw_value) or str(raw_value).strip() == "":
                continue

            records.append(
                {
                    "feature_name": feature_name,
                    "species_name": str(species_name).strip(),
                    "value": raw_value,
                }
            )

    return pd.DataFrame(records)


def load_sheet(sheet_name: Optional[str] = None):
    return load_google_sheet_data(sheet_name=sheet_name)