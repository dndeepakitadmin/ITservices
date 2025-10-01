import streamlit as st
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
from geopy.distance import geodesic

st.set_page_config(page_title="IT Services On-Demand", layout="wide")

# --- Google Sheets Setup ---
# Load service account info from secrets
service_account_info = json.loads(st.secrets["gcp"]["service_account_json"])
creds = Credentials.from_service_account_info(service_account_info)
client = gspread.authorize(creds)

# Open your Google Sheet
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g/edit#gid=0")

# Worksheets
users_ws = sheet.worksheet("Users")
techs_ws = sheet.worksheet("Technicians")
requests_ws = sheet.worksheet("Requests")

# --- Helper Functions ---
def get_all_users():
    return users_ws.get_all_records()

def get_all_techs():
    return techs_ws.get_all_records()

def get_all_requests():
    return requests_ws.get_all_records()

def add_user(name, mobile, role):
    users_ws.append_row([name, mobile, role, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending" if role=="Technician" else "Approved"])

def add_request(customer_name, issue, device, location_lat, location_lon, preferred_tech=""):
    requests_ws.append_row([customer_name, issue, device, location_lat, location_lon, preferred_tech, "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending"])

def assign_nearest_tech(request):
    techs = get_all_techs()
    min_dist = float("inf")
    assigned = ""
    req_lat = float(request["Latitude"])
    req_lon = float(request["Longitude"])
    
    for tech in techs:
        if tech["Status"] != "Approved":
            continue
        tech_lat = float(tech["Latitude"])
        tech_lon = float(tech["Longitude"])
        distance = geodesic((req_lat, req_lon), (tech_lat, tech_lon)).km
        if distance < min_dist:
            min_dist = distance
            assigned = tech["Name"]
    return assigned

# --- App Interface ---
st.title("IT Services On-Demand")

menu = ["Sign Up", "Submit Request", "Admin Panel"]
choice = st.sidebar.selectbox("Menu", menu)

# --- Sign Up ---
if choice == "Sign Up":
    st.subheader("Create Account")
    name = st.text_input("Full Name")
    mobile = st.text_input("Mobile Number")
    role = st.selectbox("Role", ["Customer", "Technician"])
    
    if st.button("Sign Up"):
        add_user(name, mobile, role)
        st.success(f"{role} account created. {'Pending approval from admin.' if role=='Technician' else 'You can login immediately.'}")

# --- Submit Request ---
elif choice == "Submit Request":
    st.subheader("Submit IT Request")
    customer_name = st.text_input("Your Name")
    issue = st.text_area("Issue Description")
    device = st.text_input("Device / Category")
    location_lat = st.text_input("Your Latitude")
    location_lon = st.text_input("Your Longitude")
    
    if st.button("Submit Request"):
        assigned_tech = assign_nearest_tech({
            "Latitude": location_lat,
            "Longitude": location_lon
        })
        add_request(customer_name, issue, device, location_lat, location_lon, assigned_tech)
        st.success(f"Request submitted. Assigned Technician: {assigned_tech if assigned_tech else 'Pending assignment'}")

# --- Admin Panel ---
elif choice == "Admin Panel":
    st.subheader("Admin Controls")
    
    st.write("### Pending Technician Approvals")
    techs = get_all_techs()
    for tech in techs:
        if tech["Status"] == "Pending":
            if st.button(f"Approve {tech['Name']}"):
                cell = techs_ws.find(tech["Name"])
                techs_ws.update_cell(cell.row, 4, "Approved")
                st.success(f"{tech['Name']} approved")
    
    st.write("### Pending Requests")
    requests = get_all_requests()
    for req in requests:
        if req["Status"] == "Pending":
            st.write(f"{req['Customer Name']} - {req['Issue']}")
            if st.button(f"Assign manually to technician"):
                assigned = assign_nearest_tech(req)
                cell = requests_ws.find(req["Customer Name"])
                requests_ws.update_cell(cell.row, 6, assigned)
                requests_ws.update_cell(cell.row, 8, "Assigned")
                st.success(f"Request assigned to {assigned}")
