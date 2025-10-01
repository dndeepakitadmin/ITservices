import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import uuid

# --- Page configuration ---
st.set_page_config(page_title="IT Services App", page_icon="🛠️", layout="wide")

# --- Authentication for Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Load service account credentials from Streamlit Secrets
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open the spreadsheet by key (from the URL)
SPREADSHEET_ID = "1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g"
spreadsheet = client.open_by_key(SPREADSHEET_ID)

users_ws = spreadsheet.worksheet("Users")
techs_ws = spreadsheet.worksheet("Technicians")
req_ws = spreadsheet.worksheet("Requests")

# Utility to read a worksheet into a DataFrame
def read_ws(ws):
    records = ws.get_all_records()
    return pd.DataFrame(records)

# Utility to append a row (list) to a worksheet
def append_ws(ws, row_list):
    ws.append_row(row_list)

# --- UI / App Flow ---
st.title("IT Services App")

menu = ["Signup / Login", "Raise Request", "My Requests", "Technicians", "Admin"]
choice = st.sidebar.radio("Menu", menu)

# Load dataframes
users_df = read_ws(users_ws)
techs_df = read_ws(techs_ws)
req_df = read_ws(req_ws)

# --- Signup / Login ---
if choice == "Signup / Login":
    st.subheader("Signup / Login")
    with st.form("auth_form"):
        user_name = st.text_input("Name")
        user_phone = st.text_input("Phone")
        user_email = st.text_input("Email")
        role = st.selectbox("Role", ["Customer", "Technician"])
        auth_btn = st.form_submit_button("Submit")
    if auth_btn:
        # Check if user already exists by phone or email
        existing = users_df[(users_df["phone"] == user_phone) | (users_df["email"] == user_email)]
        if not existing.empty:
            st.info("User already exists. Welcome back!")
        else:
            new_id = str(uuid.uuid4())
            append_ws(users_ws, [new_id, user_name, role, user_phone, user_email])
            st.success("Registered successfully as " + role)

elif choice == "Raise Request":
    st.subheader("Raise IT Support Request")
    with st.form("req_form"):
        cname = st.text_input("Your Name")
        issue = st.text_area("Describe the issue")
        device = st.selectbox("Device Type", ["Laptop", "Desktop", "Mobile", "Other"])
        loc = st.text_input("Location (address or area)")
        pref_date = st.date_input("Preferred Date")
        submit = st.form_submit_button("Submit Request")
    if submit:
        new_id = str(uuid.uuid4())
        append_ws(req_ws, [new_id, cname, issue, loc, device, pref_date.strftime("%Y-%m-%d"), "", "Pending"])
        st.success("Request created. You will be notified when assigned.")

elif choice == "My Requests":
    st.subheader("Your Requests")
    phone = st.text_input("Enter your phone to view your requests")
    if st.button("Show"):
        filtered = req_df[req_df["customer_name"] == users_df[users_df["phone"] == phone]["name"].values[0]] \
                   if not users_df[users_df["phone"] == phone].empty else pd.DataFrame()
        st.dataframe(filtered)

elif choice == "Technicians":
    st.subheader("Available Technicians")
    st.dataframe(techs_df)

elif choice == "Admin":
    st.subheader("All Requests (Admin View)")
    st.dataframe(req_df)

    st.subheader("Assign a Technician")
    req_options = req_df[req_df["status"] == "Pending"]["id"].tolist()
    tech_options = techs_df["name"].tolist()
    chosen_req = st.selectbox("Select Request ID", req_options)
    chosen_tech = st.selectbox("Select Technician", tech_options)
    if st.button("Assign"):
        # find row index in worksheet
        all_vals = req_ws.get_all_values()
        # search for the row index of the chosen_req in column 1
        row_idx = None
        for i, row in enumerate(all_vals):
            if row[0] == chosen_req:
                row_idx = i + 1  # worksheet rows are 1-indexed
                break
        if row_idx:
            req_ws.update_cell(row_idx, 7, chosen_tech)  # column 7 is assigned_tech
            req_ws.update_cell(row_idx, 8, "Assigned")
            st.success(f"Request {chosen_req} assigned to {chosen_tech}")

