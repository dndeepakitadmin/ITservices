import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from pprint import pprint

st.title("Google Sheets Test - IT Services Minimal App")

# --- Google Sheets Authentication ---
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
client = gspread.authorize(creds)

# --- Open your Google Sheet by URL ---
sheet_url = "https://docs.google.com/spreadsheets/d/1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g/edit#gid=0"
sheet = client.open_by_url(sheet_url)
worksheet = sheet.sheet1  # First sheet

# --- Display existing data ---
st.subheader("Current Google Sheet Data")
data = worksheet.get_all_records()
st.dataframe(data)

# --- Simple form to add a new row ---
st.subheader("Add a Test Row")
with st.form("add_row_form"):
    name = st.text_input("Name")
    role = st.selectbox("Role", ["Customer", "Technician", "Admin"])
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    issue = st.text_area("Issue Description")
    submitted = st.form_submit_button("Add Row")
    
    if submitted:
        new_row = [name, role, phone, email, issue]
        worksheet.append_row(new_row)
        st.success("✅ Row added successfully!")
