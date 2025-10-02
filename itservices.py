import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets + Drive scopes
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit secrets
creds = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)

# Authorize client
client = gspread.authorize(creds)

# Open your Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g/edit#gid=0"
sheet = client.open_by_url(SHEET_URL)
worksheet = sheet.sheet1  # first sheet

# Streamlit app
st.title("Google Sheets Test App")

# Show first 5 rows
data = worksheet.get_all_values()
if data:
    st.write("✅ Connected to Google Sheet!")
    st.table(data[:5])
else:
    st.write("⚠️ Sheet is empty.")

# Form to add a new row
with st.form("add_row"):
    name = st.text_input("Name")
    issue = st.text_area("Issue Description")
    submitted = st.form_submit_button("Submit")

    if submitted:
        worksheet.append_row([name, issue])
        st.success(f"Row added for {name}")
