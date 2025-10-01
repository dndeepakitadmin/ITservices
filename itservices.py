import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from geopy.distance import geodesic

# -------------------- Google Sheets Setup --------------------
# Use secrets for service account
creds = Credentials.from_service_account_info(st.secrets["gcp"]["service_account_json"])
client = gspread.authorize(creds)

# Replace with your Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g/edit"
sheet = client.open_by_url(SHEET_URL)

users_ws = sheet.worksheet("Users")
techs_ws = sheet.worksheet("Technicians")
requests_ws = sheet.worksheet("Requests")

# -------------------- Helper Functions --------------------
def get_user_by_phone(phone):
    users = users_ws.get_all_records()
    for user in users:
        if str(user["Phone"]) == str(phone):
            return user
    return None

def get_technicians():
    return techs_ws.get_all_records()

def assign_nearest_technician(lat, lon):
    techs = get_technicians()
    available = [t for t in techs if t["Status"].lower() == "available"]
    if not available:
        return None
    # Find nearest
    distances = []
    for t in available:
        t_lat = float(t["Latitude"])
        t_lon = float(t["Longitude"])
        distance = geodesic((lat, lon), (t_lat, t_lon)).km
        distances.append((distance, t["Name"]))
    distances.sort()
    return distances[0][1]  # nearest tech name

# -------------------- Streamlit App --------------------
st.title("IT Services On-Demand")

# -------------------- Sign-Up / Login --------------------
st.header("Login / Sign-Up")
phone = st.text_input("Enter Mobile Number")
role = st.selectbox("Role", ["Customer", "Technician"])
login_btn = st.button("Login / Sign-Up")

if login_btn and phone:
    user = get_user_by_phone(phone)
    if user is None:
        # Register new user
        users_ws.append_row([phone, role])
        st.success(f"New {role} registered with phone {phone}")
    else:
        st.success(f"Welcome back, {role}")

# -------------------- Customer Flow --------------------
if role == "Customer" and phone:
    st.subheader("Raise a New IT Request")
    issue = st.text_area("Describe your issue")
    lat = st.number_input("Your Latitude", format="%.6f")
    lon = st.number_input("Your Longitude", format="%.6f")
    submit_btn = st.button("Submit Request")

    if submit_btn:
        assigned_tech = assign_nearest_technician(lat, lon)
        if not assigned_tech:
            assigned_tech = "Pending"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        requests_ws.append_row([phone, issue, lat, lon, assigned_tech, now, "Pending"])
        st.success(f"Request submitted. Assigned Technician: {assigned_tech}")

# -------------------- Technician Flow --------------------
if role == "Technician" and phone:
    st.subheader("Available Requests")
    requests = requests_ws.get_all_records()
    for idx, req in enumerate(requests):
        if req["Technician"] in ["Pending", ""] or req["Technician"] == get_user_by_phone(phone)["Phone"]:
            st.markdown(f"**Request {idx+1}:** {req['Issue']}")
            st.markdown(f"Location: {req['Latitude']}, {req['Longitude']}")
            assign_btn = st.button(f"Assign to Me - Request {idx+1}", key=f"assign_{idx}")
            if assign_btn:
                requests_ws.update_cell(idx + 2, 5, get_user_by_phone(phone)["Phone"])  # Column 5 = Technician
                st.success(f"Request {idx+1} assigned to you!")

# -------------------- Admin Flow --------------------
if role == "Admin" and phone:
    st.subheader("All Requests Overview")
    all_requests = requests_ws.get_all_records()
    st.dataframe(all_requests)
