import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- GCP Service Account & Google Sheets setup ---
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
client = gspread.authorize(creds)

# --- Sheet References ---
sheet_customers = client.worksheet("Customers")
sheet_technicians = client.worksheet("Technicians")
sheet_tickets = client.worksheet("Tickets")

# --- Streamlit App ---
st.title("IT Support Minimal App")

# Role selection (for demo purposes)
role = st.selectbox("Select Role", ["Customer", "Technician", "Admin"])

# --- CUSTOMER FLOW ---
if role == "Customer":
    st.header("Submit a Ticket")
    customer_name = st.text_input("Your Name")
    phone = st.text_input("Phone Number")
    issue = st.text_area("Issue Description")
    location = st.text_input("Location")
    device = st.text_input("Device")
    preferred_date = st.date_input("Preferred Date")

    if st.button("Submit Ticket"):
        # Auto ID = next row number (starting after header)
        next_id = len(sheet_tickets.get_all_values())
        sheet_tickets.append_row([
            next_id, customer_name, issue, location, device, str(preferred_date), ""
        ])
        st.success("✅ Ticket submitted successfully!")

    # View your tickets
    st.subheader("Your Tickets")
    all_tickets = sheet_tickets.get_all_records()
    my_tickets = [t for t in all_tickets if t["customer_name"] == customer_name]
    st.table(my_tickets)

# --- TECHNICIAN FLOW ---
elif role == "Technician":
    st.header("Unassigned Tickets")
    tech_name = st.text_input("Your Name")
    all_tickets = sheet_tickets.get_all_records()
    unassigned = [t for t in all_tickets if t["assigned_tech"] == ""]

    if unassigned:
        for idx, ticket in enumerate(unassigned):
            st.write(f"**Ticket ID:** {ticket['id']}, Issue: {ticket['issue']}, Customer: {ticket['customer_name']}")
            claim = st.button(f"Claim Ticket {ticket['id']}", key=f"claim_{ticket['id']}")
            if claim:
                # Update assigned_tech in the sheet
                row_number = idx + 2  # +2 because gspread counts header row as 1
                sheet_tickets.update_cell(row_number, 7, tech_name)
                st.success(f"✅ Ticket {ticket['id']} claimed by {tech_name}!")
                st.experimental_rerun()
    else:
        st.info("No unassigned tickets currently.")

# --- ADMIN FLOW ---
elif role == "Admin":
    st.header("All Sheets Overview")

    st.subheader("Customers")
    customers_data = sheet_customers.get_all_records()
    st.table(customers_data)

    st.subheader("Technicians")
    tech_data = sheet_technicians.get_all_records()
    st.table(tech_data)

    st.subheader("Tickets")
    tickets_data = sheet_tickets.get_all_records()
    st.table(tickets_data)
