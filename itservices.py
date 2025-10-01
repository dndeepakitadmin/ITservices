import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime
from geopy.distance import geodesic

# --- Google Sheets Setup ---
# Access your secret exactly as pasted
creds_dict = json.loads(st.secrets["gcp"]["service_account_json"])
creds = Credentials.from_service_account_info(creds_dict)
client = gspread.authorize(creds)

# Open your Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g/edit#gid=788082122"
sheet = client.open_by_url(sheet_url)

# Worksheets
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
    status = "Pending" if role=="Technician" else "Approved"
    users_ws.append_row([name, phone, role, now, status])
    if role=="Technician":
        techs_ws.append_row([name, "Yes", 0.0, 0.0])  # Name, Available, Latitude, Longitude

def update_tech_location(name, lat, lng):
    techs = techs_ws.get_all_records()
    for idx, t in enumerate(techs, start=2):
        if t["Name"] == name:
            techs_ws.update_cell(idx, 3, lat)
            techs_ws.update_cell(idx, 4, lng)
            return

def submit_request(customer_phone, device_type, issue, preferred_date, lat, lng, photo_url=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    requests_ws.append_row([customer_phone, device_type, issue, preferred_date, photo_url, "", now, "Pending", lat, lng])

def get_pending_requests():
    return [r for r in requests_ws.get_all_records() if r["Assigned Technician"] == ""]

def auto_assign_requests():
    requests = get_pending_requests()
    techs = [t for t in techs_ws.get_all_records() if t["Available"]=="Yes"]
    for r in requests:
        req_loc = (float(r["Latitude"]), float(r["Longitude"]))
        nearest_tech = None
        min_dist = float('inf')
        for t in techs:
            tech_loc = (float(t["Latitude"]), float(t["Longitude"]))
            distance = geodesic(req_loc, tech_loc).km
            if distance < min_dist:
                min_dist = distance
                nearest_tech = t
        if nearest_tech:
            row_idx = requests_ws.find(r["Customer Phone"]).row
            requests_ws.update_cell(row_idx, 6, nearest_tech["Name"])
            requests_ws.update_cell(row_idx, 8, "Assigned")
            tech_row = techs_ws.find(nearest_tech["Name"]).row
            techs_ws.update_cell(tech_row, 2, "No")

# --- Streamlit UI ---
st.title("IT Services On-Demand App")

# --- Sidebar Login / Signup ---
st.sidebar.header("Login / Signup")
phone = st.sidebar.text_input("Enter your mobile number")
role = st.sidebar.selectbox("I am a", ["Customer", "Technician", "Admin"])

if st.sidebar.button("Login / Signup"):
    user = user_exists(phone)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome back, {user['Name']} ({user['Role']})")
    else:
        name = st.sidebar.text_input("Enter your name")
        if name:
            create_user(name, phone, role)
            st.success(f"User created! {('Pending approval' if role=='Technician' else 'You can start now')}")
            st.session_state["user"] = {"Name": name, "Phone": phone, "Role": role, "Status": "Pending" if role=="Technician" else "Approved"}

# --- Customer View ---
if "user" in st.session_state and st.session_state["user"]["Role"]=="Customer":
    st.header("Submit a Service Request")
    device_type = st.text_input("Device Type / Category")
    issue = st.text_area("Describe the issue")
    preferred_date = st.date_input("Preferred Date")
    photo_url = st.text_input("Photo URL (optional)")

    lat = st.number_input("Your Latitude", format="%.6f")
    lng = st.number_input("Your Longitude", format="%.6f")

    if st.button("Submit Request"):
        submit_request(st.session_state["user"]["Phone"], device_type, issue, preferred_date, lat, lng, photo_url)
        st.success("Request submitted successfully!")

# --- Technician View ---
if "user" in st.session_state and st.session_state["user"]["Role"]=="Technician":
    if st.session_state["user"]["Status"] != "Approved":
        st.warning("Technician account pending admin approval")
    else:
        st.header("Update Your Location")
        lat = st.number_input("Your Latitude", format="%.6f", key="tech_lat")
        lng = st.number_input("Your Longitude", format="%.6f", key="tech_lng")
        if st.button("Update Location"):
            update_tech_location(st.session_state["user"]["Name"], lat, lng)
            st.success("Location updated!")

        st.header("Available Requests Nearby")
        pending = get_pending_requests()
        for r in pending:
            req_loc = (float(r["Latitude"]), float(r["Longitude"]))
            tech_loc = (lat, lng)
            distance = geodesic(req_loc, tech_loc).km
            if distance <= 10:
                st.write(f"Customer: {r['Customer Phone']}, Issue: {r['Issue']}, Preferred Date: {r['Preferred Date']}, Distance: {distance:.2f} km")
                if st.button(f"Assign to me: {r['Customer Phone']}"):
                    row_idx = requests_ws.find(r["Customer Phone"]).row
                    requests_ws.update_cell(row_idx, 6, st.session_state["user"]["Name"])
                    requests_ws.update_cell(row_idx, 8, "Assigned")
                    st.success("Assigned to you!")

# --- Admin View ---
if "user" in st.session_state and st.session_state["user"]["Role"]=="Admin":
    st.header("Admin Panel")
    if st.button("Auto-Assign Pending Requests Based on Location"):
        auto_assign_requests()
        st.success("Auto-assignment completed!")

    st.subheader("Approve Technicians")
    users = users_ws.get_all_records()
    for u in users:
        if u["Role"]=="Technician" and u["Status"]=="Pending":
            st.write(f"{u['Name']} ({u['Phone']})")
            if st.button(f"Approve {u['Name']}"):
                row_idx = users_ws.find(u["Phone"]).row
                users_ws.update_cell(row_idx, 5, "Approved")
                st.success(f"{u['Name']} approved!")

st.info("Notifications and AI Chatbot integration coming soon.")
