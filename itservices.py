import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("IT Services - Minimal Role-Based Test App")

# --- Google Sheets Authentication ---
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
client = gspread.authorize(creds)

# --- Open your Google Sheet ---
sheet_url = "https://docs.google.com/spreadsheets/d/1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g/edit#gid=0"
sheet = client.open_by_url(sheet_url)
worksheet = sheet.sheet1

# --- Role Selection ---
role = st.selectbox("Select Role", ["Customer", "Technician", "Admin"])
user_name = st.text_input("Enter your Name (for demo purposes)")

# --- Fetch Sheet Data ---
data = worksheet.get_all_records()

# --- CUSTOMER VIEW ---
if role == "Customer":
    st.subheader("Submit a New Issue")
    with st.form("customer_form"):
        issue = st.text_area("Describe your issue")
        submitted = st.form_submit_button("Submit Issue")
        if submitted:
            new_row = [user_name, "Customer", "", "", issue]
            worksheet.append_row(new_row)
            st.success("✅ Issue submitted successfully!")

    st.subheader("Your Submitted Tickets")
    user_tickets = [row for row in data if row["name"] == user_name and row["role"] == "Customer"]
    st.dataframe(user_tickets)

# --- TECHNICIAN VIEW ---
elif role == "Technician":
    st.subheader("Available Tickets to Claim")
    unassigned_tickets = [row for row in data if row["role"] == "Customer" and row["phone"] == ""]
    st.dataframe(unassigned_tickets)

    st.subheader("Claim a Ticket")
    ticket_index = st.number_input("Enter row number to claim (as shown above)", min_value=1, step=1)
    if st.button("Claim Ticket"):
        if 0 < ticket_index <= len(data):
            worksheet.update_cell(ticket_index + 1, 3, user_name)  # Assign technician name in 'role' column
            st.success(f"✅ Ticket #{ticket_index} claimed!")

# --- ADMIN VIEW ---
elif role == "Admin":
    st.subheader("All Tickets")
    st.dataframe(data)
