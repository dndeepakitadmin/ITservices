import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- GCP Service Account ---
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
client = gspread.authorize(creds)

# --- Open Spreadsheet ---
SPREADSHEET_ID = "1g_8yhPTc_Mecjlflnp3XMjg5QZLuCO2ogIJH5PoZZ0g"
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet_customers = spreadsheet.worksheet("Customers")
sheet_tickets = spreadsheet.worksheet("Tickets")
sheet_technicians = spreadsheet.worksheet("Technicians")

st.title("IT Services App")

# --- Role Selection ---
role = st.selectbox("Select your role", ["Customer", "Technician", "Admin"])

# ---------------- CUSTOMER FLOW ----------------
if role == "Customer":
    st.header("Submit a Support Ticket")

    customer_name = st.text_input("Your Name")
    phone = st.text_input("Phone Number")
    location = st.text_input("Location (Address or Google Maps link)")
    laptop_model = st.text_input("Laptop Model")
    serial_number = st.text_input("Serial Number")
    device_type = st.selectbox("Device Type", ["Laptop", "Desktop", "Other"])
    issue = st.text_area("Describe the Issue")
    preferred_date = st.date_input("Preferred Date")
    photo = st.file_uploader("Upload Photo of Issue", type=["png", "jpg", "jpeg"])
    video = st.file_uploader("Upload Video of Issue", type=["mp4", "webm"])

    if st.button("Submit Ticket"):
        # Auto ID
        all_tickets = sheet_tickets.get_all_values()
        next_id = len(all_tickets)

        # File names (for now, store names)
        photo_name = photo.name if photo else ""
        video_name = video.name if video else ""

        sheet_tickets.append_row([
            next_id,
            customer_name,
            phone,
            location,
            laptop_model,
            serial_number,
            device_type,
            issue,
            str(preferred_date),
            photo_name,
            video_name,
            ""  # assigned_tech
        ])

        st.success("✅ Ticket submitted successfully!")

    # Show customer tickets
    st.subheader("Your Tickets")
    all_tickets = sheet_tickets.get_all_records()
    my_tickets = [t for t in all_tickets if t["customer_name"] == customer_name]
    st.table(my_tickets)

# ---------------- TECHNICIAN FLOW ----------------
elif role == "Technician":
    st.header("Technician Dashboard")
    # Later: show unassigned tickets and option to claim

# ---------------- ADMIN FLOW ----------------
else:
    st.header("Admin Dashboard")
    # Later: show all tickets, assign technicians, etc.
