import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import uuid
from datetime import datetime

# -----------------
# Google Sheets Setup
# -----------------
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Connect to your Google Sheet
sheet = client.open("IT_Services_App")
users_ws = sheet.worksheet("Users")
tech_ws = sheet.worksheet("Technicians")
req_ws = sheet.worksheet("Requests")

# Load data into DataFrames
users_df = pd.DataFrame(users_ws.get_all_records())
tech_df = pd.DataFrame(tech_ws.get_all_records())
req_df = pd.DataFrame(req_ws.get_all_records())

# -----------------
# Streamlit UI
# -----------------
st.title("IT Support App")

# Login / Signup
menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Signup":
    st.subheader("Create an Account")
    name = st.text_input("Name")
    role = st.selectbox("Role", ["Customer", "Technician"])
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    
    if st.button("Register"):
        uid = str(uuid.uuid4())
        users_ws.append_row([uid, name, role, phone, email, "", "", False])
        st.success("Account created! Waiting for approval if Technician.")
    
elif choice == "Login":
    st.subheader("Login")
    phone = st.text_input("Enter Phone")
    
    if st.button("Login"):
        user = next((u for u in users_df.to_dict("records") if u["phone"] == phone), None)
        if user:
            st.success(f"Welcome {user['name']} ({user['role']})")
            
            # CUSTOMER FLOW
            if user['role'] == "Customer":
                st.subheader("Raise a Request")
                issue = st.text_area("Describe your issue")
                device = st.selectbox("Device", ["Laptop","Mobile","Network","Other"])
                date = st.date_input("Preferred Date")
                time = st.time_input("Preferred Time")
                if st.button("Submit Request"):
                    rid = str(uuid.uuid4())
                    req_ws.append_row([rid, user["user_id"], issue, device, str(date), str(time), "", "", "Pending", "", str(datetime.now())])
                    st.success("Request submitted!")
                
                st.subheader("My Requests")
                my_reqs = req_df[req_df["customer_id"] == user["user_id"]]
                st.dataframe(my_reqs)

            # TECHNICIAN FLOW
            elif user['role'] == "Technician":
                st.subheader("Available Requests")
                available_reqs = req_df[req_df["status"] == "Pending"]
                st.dataframe(available_reqs)
            
            # ADMIN FLOW
            elif user['role'] == "Admin":
                st.subheader("All Requests")
                st.dataframe(req_df)
                
        else:
            st.error("User not found. Please signup first.")
