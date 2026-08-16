import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

@st.cache_data
def connect_to_google_sheet():
    try:
        # Load credentials from Streamlit secrets or local credentials.json
        if "gcp_service_account" in st.secrets:
            credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        else:
            credentials = Credentials.from_service_account_file('credentials.json')

        # Connect to Google Sheets
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error("Failed to connect to Google Sheets. Please check your credentials.")
        raise e

@st.cache_data
def load_google_sheet_data(spreadsheet_id):
    try:
        client = connect_to_google_sheet()
        sheet = client.open_by_key(spreadsheet_id).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error("Failed to load data from Google Sheets. Please check the spreadsheet ID and permissions.")
        raise e

def transpose_workbook_data(df):
    return df.transpose()