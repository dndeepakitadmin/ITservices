import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Google Sheets Setup ---
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
client = gspread.authorize(creds)

# Open your Google Sheet
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0")
users_ws = sheet.worksheet("Users")
techs_ws = sheet.worksheet("Technicians")
requests_ws = sheet.worksheet("Requests")

# --- Utility Functions ---
def user_exists(phone):
    users = users_ws.get_all_records()
    for user in users:
        if user["Phone"] == phone:
            return user
    return None

def create_user(name, phone, role):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users_ws.append_row([name, phone, role, now, "Pending" if role=="Technician" else "Approved"])

def submit_request(customer_phone, device_type, issue, preferred_date, photo_url=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    requests_ws.append_row([customer_phone, device_type, issue, preferred_date, photo_url, "", now, "Pending"])

def get_pending_requests():
    return [r for r in requests_ws.get_all_records() if r["Assigned Technician"] == ""]

def auto_assign_requests():
    requests = get_pending_requests()
    techs = [t for t in techs_ws.get_all_records() if t["Available"]=="Yes"]
    for r in requests:
        if techs:
            tech = techs[0]  # simplest auto-assign: first available tech
            row_idx = requests_ws.find(r["Customer Phone"]).row
            requests_ws.update_cell(row_idx, 6, tech["Name"])
            # Optionally mark tech as busy
            tech_row = techs_ws.find(tech["Name"]).row
            techs_ws.update_cell(tech_row, 2, "No")

# --- Streamlit UI ---
st.title("IT Services On-Demand")

# --- Sign-up / Login ---
st.sidebar.header("Login / Signup")
phone = st.sidebar.text_input("Enter your mobile number")
role = st.sidebar.selectbox("I am a", ["Customer", "Technician"])

if st.sidebar.button("Login / Signup"):
    user = user_exists(phone)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome back, {user['Name']} ({user['Role']})")
    else:
        name = st.sidebar.text_input("Enter your name")
        if name:
            create_user(name, phone, role)
            st.success(f"User created successfully! {('Pending approval' if role=='Technician' else 'You can start now')}")
            st.session_state["user"] = {"Name": name, "Phone": phone, "Role": role, "Status": "Pending" if role=="Technician" else "Approved"}

# --- Customer View ---
if "user" in st.session_state and st.session_state["user"]["Role"]=="Customer":
    st.header("Submit a Service Request")
    device_type = st.text_input("Device Type / Category")
    issue = st.text_area("Describe the issue")
    preferred_date = st.date_input("Preferred Date")
    photo_url = st.text_input("Photo URL (optional)")

    if st.button("Submit Request"):
        submit_request(st.session_state["user"]["Phone"], device_type, issue, preferred_date, photo_url)
        st.success("Request submitted successfully!")

# --- Technician View ---
if "user" in st.session_state and st.session_state["user"]["Role"]=="Technician":
    if st.session_state["user"]["Status"] != "Approved":
        st.warning("Technician account pending admin approval")
    else:
        st.header("Available Requests")
        pending = get_pending_requests()
        if pending:
            for r in pending:
                st.write(f"Customer: {r['Customer Phone']}, Issue: {r['Issue']}, Preferred Date: {r['Preferred Date']}")
                if st.button(f"Assign to me: {r['Customer Phone']}"):
                    row_idx = requests_ws.find(r["Customer Phone"]).row
                    requests_ws.update_cell(row_idx, 6, st.session_state["user"]["Name"])
                    st.success(f"Assigned to you!")
        else:
            st.info("No pending requests currently.")

# --- Admin View ---
if "user" in st.session_state and st.session_state["user"]["Role"]=="Admin":
    st.header("Admin Panel")
    if st.button("Auto-Assign Pending Requests"):
        auto_assign_requests()
        st.success("Auto-assignment completed!")
