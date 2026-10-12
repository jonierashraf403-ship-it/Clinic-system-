import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Multi-Clinic Management System", layout="wide")

# Initialize Session States
if 'patients' not in st.session_state:
    st.session_state['patients'] = pd.DataFrame(columns=[
        'Patient_ID', 'Clinic', 'Name', 'Phone', 'Medical_History', 'Dental_History', 'Notes', 'Total_Cost', 'Paid', 'Remaining'
    ])

if 'appointments' not in st.session_state:
    st.session_state['appointments'] = pd.DataFrame(columns=[
        'Clinic', 'Patient_Name', 'Phone', 'Date', 'Time', 'Procedure'
    ])

st.title("🏥 Multi-Clinic Management System")

# Sidebar Navigation
menu = st.sidebar.selectbox("Navigation", [
    "Today's Appointments & Reminders",
    "Book New Appointment",
    "All Appointments (By Date)",
    "Add New Patient / Session",
    "Patient Records & History",
    "Financial Reports"
])

today = datetime.today().date()
tomorrow = today + timedelta(days=1)

# 1. TODAY'S APPOINTMENTS & REMINDERS
if menu == "Today's Appointments & Reminders":
    st.header("📅 Today's Schedule & Tomorrow's Reminders")
    
    # Tomorrow's Reminder Banner
    if not st.session_state['appointments'].empty:
        tomorrow_apps = st.session_state['appointments'][
            st.session_state['appointments']['Date'] == str(tomorrow)
        ]
        if not tomorrow_apps.empty:
            st.warning(f"🔔 **Reminder:** You have {len(tomorrow_apps)} appointment(s) scheduled for TOMORROW ({tomorrow})!")
            with st.expander("View Tomorrow's Reminders List"):
                st.dataframe(tomorrow_apps, use_container_width=True)
        else:
            st.info("ℹ️ No appointments scheduled for tomorrow yet.")
    
    st.markdown("---")
    st.subheader(f"📌 Today's Appointments ({today})")
    
    if not st.session_state['appointments'].empty:
        today_apps = st.session_state['appointments'][
            st.session_state['appointments']['Date'] == str(today)
        ]
        if not today_apps.empty:
            st.dataframe(today_apps, use_container_width=True)
        else:
            st.info("No appointments booked for today.")
    else:
        st.info("No appointments recorded in the system.")

# 2. BOOK NEW APPOINTMENT
elif menu == "Book New Appointment":
    st.header("➕ Schedule New Appointment")
    
    with st.form("appointment_form"):
        col1, col2 = st.columns(2)
        with col1:
            clinic = st.selectbox("Clinic Branch", ["Main Branch", "Maadi Branch", "Tagamoa Branch"])
            patient_name = st.text_input("Patient Full Name")
            phone = st.text_input("Phone Number")
        with col2:
            app_date = st.date_input("Appointment Date", today)
            app_time = st.time_input("Appointment Time")
            procedure = st.text_input("Procedure / Treatment")
        
        submitted = st.form_submit_button("Book Appointment")
        if submitted and patient_name:
            new_app = pd.DataFrame({
                'Clinic': [clinic],
                'Patient_Name': [patient_name],
                'Phone': [phone],
                'Date': [str(app_date)],
                'Time': [str(app_time)],
                'Procedure': [procedure]
            })
            st.session_state['appointments'] = pd.concat([st.session_state['appointments'], new_app], ignore_index=True)
            st.success(f"Appointment successfully booked for: {patient_name} on {app_date}")

# 3. ALL APPOINTMENTS (BY DATE)
elif menu == "All Appointments (By Date)":
    st.header("📆 Appointments Filter by Date")
    
    selected_date = st.date_input("Select Date to View Schedule", today)
    
    if not st.session_state['appointments'].empty:
        filtered_apps = st.session_state['appointments'][
            st.session_state['appointments']['Date'] == str(selected_date)
        ]
        st.subheader(f"Appointments for {selected_date}")
        if not filtered_apps.empty:
            st.dataframe(filtered_apps, use_container_width=True)
        else:
            st.info(f"No appointments found for {selected_date}.")
    else:
        st.info("No appointments recorded in the system.")

# 4. ADD NEW PATIENT / SESSION
elif menu == "Add New Patient / Session":
    st.header("➕ Add Patient Record & Session Details")
    
    with st.form("patient_form"):
        clinic = st.selectbox("Clinic Branch", ["Main Branch", "Maadi Branch", "Tagamoa Branch"])
        name = st.text_input("Patient Full Name")
        phone = st.text_input("Phone Number")
        
        st.markdown("---")
        st.subheader("Medical & Behavioral History")
        medical_hist = st.text_area("General Medical History (Diabetes, BP, Allergies, etc.)")
        dental_hist = st.text_area("Dental / Specialty History")
        notes = st.text_area("Personal Notes (Preferences, Behavioral notes)")
        
        st.markdown("---")
        st.subheader("Financial & Session Details")
        col1, col2, col3 = st.columns(3)
        total_cost = col1.number_input("Total Cost", min_value=0.0, step=50.0)
        paid = col2.number_input("Amount Paid", min_value=0.0, step=50.0)
        remaining = total_cost - paid
        col3.write(f"**Remaining Balance:** {remaining} EGP")
        
        save_btn = st.form_submit_button("Save Patient & Session")
        if save_btn and name:
            patient_id = "P-" + str(len(st.session_state['patients']) + 1001)
            new_pat = pd.DataFrame({
                'Patient_ID': [patient_id],
                'Clinic': [clinic],
                'Name': [name],
                'Phone': [phone],
                'Medical_History': [medical_hist],
                'Dental_History': [dental_hist],
                'Notes': [notes],
                'Total_Cost': [total_cost],
                'Paid': [paid],
                'Remaining': [remaining]
            })
            st.session_state['patients'] = pd.concat([st.session_state['patients'], new_pat], ignore_index=True)
            st.success(f"Patient saved successfully with ID: {patient_id}")

# 5. PATIENT RECORDS & HISTORY
elif menu == "Patient Records & History":
    st.header("🗂️ Patient Database & Search")
    if not st.session_state['patients'].empty:
        search_query = st.text_input("Search by Name or Phone:")
        df = st.session_state['patients']
        if search_query:
            df = df[df['Name'].str.contains(search_query, case=False, na=False) | df['Phone'].str.contains(search_query, na=False)]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No patient records available.")

# 6. FINANCIAL REPORTS
elif menu == "Financial Reports":
    st.header("💰 Financial Summary & Revenue")
    if not st.session_state['patients'].empty:
        df = st.session_state['patients']
        total_revenue = df['Paid'].sum()
        total_remaining = df['Remaining'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Collected Revenue", f"{total_revenue} EGP")
        col2.metric("Total Outstanding Balance", f"{total_remaining} EGP")
    else:
        st.info("No financial data available yet.")
