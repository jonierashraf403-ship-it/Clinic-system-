import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="SaaS Multi-Clinic Management System", layout="wide")

# Initialize Global Session States for Multi-Clinic SaaS Simulation
if 'users' not in st.session_state:
    st.session_state['users'] = pd.DataFrame({
        'Username': ['doctor_main', 'doctor_maadi', 'admin'],
        'Password': ['1234', '1234', 'admin123'],
        'Clinic': ['Main Branch', 'Maadi Branch', 'All Clinics'],
        'Role': ['Doctor', 'Doctor', 'Super Admin']
    })

# Subscriptions Table for Super Admin
if 'subscriptions' not in st.session_state:
    st.session_state['subscriptions'] = pd.DataFrame({
        'Clinic': ['Main Branch', 'Maadi Branch'],
        'Status': ['Active', 'Active'],
        'Expiry_Date': [str(datetime.today().date() + timedelta(days=30)), str(datetime.today().date() + timedelta(days=15))]
    })

if 'patients' not in st.session_state:
    st.session_state['patients'] = pd.DataFrame(columns=[
        'Patient_ID', 'Clinic', 'Name', 'Phone', 'Medical_History', 'Dental_History', 'Notes', 'Total_Cost', 'Paid', 'Remaining'
    ])

if 'appointments' not in st.session_state:
    st.session_state['appointments'] = pd.DataFrame(columns=[
        'Clinic', 'Patient_Name', 'Phone', 'Date', 'Time', 'Procedure'
    ])

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['clinic'] = ""
    st.session_state['role'] = ""

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.title("🔐 Multi-Clinic SaaS - Secure Login")
    st.markdown("Please log in with your clinic credentials to access your dashboard.")
    
    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
        
        if login_btn:
            users_df = st.session_state['users']
            user_match = users_df[(users_df['Username'] == username_input) & (users_df['Password'] == password_input)]
            
            if not user_match.empty:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_match.iloc[0]['Username']
                st.session_state['clinic'] = user_match.iloc[0]['Clinic']
                st.session_state['role'] = user_match.iloc[0]['Role']
                st.success("Login successful! Loading dashboard...")
                st.rerun()
            else:
                st.error("Invalid username or password. Try (admin / admin123 or doctor_main / 1234)")
                
    st.stop()

# --- MAIN APP (AFTER LOGIN) ---
current_clinic = st.session_state['clinic']
current_role = st.session_state['role']

st.sidebar.markdown(f"👤 **Logged in as:** {st.session_state['username']}")
st.sidebar.markdown(f"🏥 **Clinic:** {current_clinic}")
st.sidebar.markdown(f"🛡️ **Role:** {current_role}")

if st.sidebar.button("Log out"):
    st.session_state['logged_in'] = False
    st.rerun()

st.title(f"🏥 Multi-Clinic Management System - [{current_clinic}]")

# Dynamic Menu based on Role
menu_options = [
    "Today's Appointments & Reminders",
    "Book New Appointment",
    "All Appointments (By Date)",
    "Add New Patient / Session",
    "Patient Records & History",
    "Financial Reports & Debts Tracking"
]

if current_role == "Super Admin":
    menu_options.append("👑 Super Admin: Manage Subscriptions")

menu = st.sidebar.selectbox("Navigation", menu_options)

today = datetime.today().date()
tomorrow = today + timedelta(days=1)

def filter_by_clinic(df):
    if current_role == "Super Admin" or current_clinic == "All Clinics":
        return df
    else:
        return df[df['Clinic'] == current_clinic]

# 1. TODAY'S APPOINTMENTS & REMINDERS
if menu == "Today's Appointments & Reminders":
    st.header("📅 Today's Schedule & Tomorrow's Reminders")
    appointments_df = filter_by_clinic(st.session_state['appointments'])
    
    if not appointments_df.empty:
        tomorrow_apps = appointments_df[appointments_df['Date'] == str(tomorrow)]
        if not tomorrow_apps.empty:
            st.warning(f"🔔 **Reminder:** You have {len(tomorrow_apps)} appointment(s) scheduled for TOMORROW ({tomorrow})!")
            with st.expander("View Tomorrow's Reminders List"):
                st.dataframe(tomorrow_apps, use_container_width=True)
        else:
            st.info("ℹ️ No appointments scheduled for tomorrow yet.")
    
    st.markdown("---")
    st.subheader(f"📌 Today's Appointments ({today})")
    
    if not appointments_df.empty:
        today_apps = appointments_df[appointments_df['Date'] == str(today)]
        if not today_apps.empty:
            st.dataframe(today_apps, use_container_width=True)
        else:
            st.info("No appointments booked for today.")
    else:
        st.info("No appointments recorded.")

# 2. BOOK NEW APPOINTMENT
elif menu == "Book New Appointment":
    st.header("➕ Schedule New Appointment")
    with st.form("appointment_form"):
        col1, col2 = st.columns(2)
        with col1:
            if current_role == "Super Admin":
                clinic = st.selectbox("Clinic Branch", ["Main Branch", "Maadi Branch", "Tagamoa Branch"])
            else:
                clinic = current_clinic
                st.info(f"Booking for Clinic: **{clinic}**")
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
            st.success(f"Appointment successfully booked for: {patient_name}")

# 3. ALL APPOINTMENTS (BY DATE)
elif menu == "All Appointments (By Date)":
    st.header("📆 Appointments Filter by Date")
    selected_date = st.date_input("Select Date to View Schedule", today)
    appointments_df = filter_by_clinic(st.session_state['appointments'])
    
    if not appointments_df.empty:
        filtered_apps = appointments_df[appointments_df['Date'] == str(selected_date)]
        st.subheader(f"Appointments for {selected_date}")
        if not filtered_apps.empty:
            st.dataframe(filtered_apps, use_container_width=True)
        else:
            st.info(f"No appointments found for {selected_date}.")
    else:
        st.info("No appointments recorded.")

# 4. ADD NEW PATIENT / SESSION
elif menu == "Add New Patient / Session":
    st.header("➕ Add Patient Record & Session Details")
    with st.form("patient_form"):
        if current_role == "Super Admin":
            clinic = st.selectbox("Clinic Branch", ["Main Branch", "Maadi Branch", "Tagamoa Branch"])
        else:
            clinic = current_clinic
            st.info(f"Adding record to Clinic: **{clinic}**")
            
        name = st.text_input("Patient Full Name")
        phone = st.text_input("Phone Number")
        
        st.markdown("---")
        st.subheader("Medical & Behavioral History")
        medical_hist = st.text_area("General Medical History")
        dental_hist = st.text_area("Dental / Specialty History")
        notes = st.text_area("Personal Notes")
        
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

# 5. PATIENT RECORDS & HISTORY (WITH CSV/REPORT EXPORT)
elif menu == "Patient Records & History":
    st.header("🗂️ Patient Database & Export Reports")
    patients_df = filter_by_clinic(st.session_state['patients'])
    
    if not patients_df.empty:
        search_query = st.text_input("Search by Name or Phone:")
        df = patients_df
        if search_query:
            df = df[df['Name'].str.contains(search_query, case=False, na=False) | df['Phone'].str.contains(search_query, na=False)]
        
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📥 Export Patient Data / Report")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Filtered Patients Report (CSV/Excel)",
            data=csv_data,
            file_name=f"patients_report_{current_clinic}.csv",
            mime="text/csv"
        )
    else:
        st.info("No patient records available.")

# 6. FINANCIAL REPORTS & DEBTS TRACKING
elif menu == "Financial Reports & Debts Tracking":
    st.header("💰 Financial Summary & Outstanding Balances")
    patients_df = filter_by_clinic(st.session_state['patients'])
    
    if not patients_df.empty:
        total_revenue = patients_df['Paid'].sum()
        total_remaining = patients_df['Remaining'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue Collected", f"{total_revenue} EGP")
        col2.metric("Total Unpaid / Outstanding Balance", f"{total_remaining} EGP")
        
        st.markdown("---")
        st.subheader("🔍 Search Patient Debt / Balance")
        search_name = st.text_input("Enter Patient Name or Phone:")
        
        if search_name:
            filtered_df = patients_df[patients_df['Name'].str.contains(search_name, case=False, na=False) | patients_df['Phone'].str.contains(search_name, na=False)]
            if not filtered_df.empty:
                for idx, row in filtered_df.iterrows():
                    st.write(f"### 👤 Patient: **{row['Name']}** ({row['Phone']})")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Cost", f"{row['Total_Cost']} EGP")
                    c2.metric("Paid", f"{row['Paid']} EGP")
                    c3.metric("Remaining Debt", f"{row['Remaining']} EGP", delta_color="inverse")
                    st.markdown("---")
            else:
                st.warning("No matching patient found.")
        
        st.subheader("📋 List of Patients with Remaining Balance (Debts)")
        debtors_df = patients_df[patients_df['Remaining'] > 0][['Patient_ID', 'Name', 'Phone', 'Clinic', 'Total_Cost', 'Paid', 'Remaining']]
        if not debtors_df.empty:
            st.dataframe(debtors_df, use_container_width=True)
        else:
            st.success("🎉 Excellent! There are no unpaid balances.")
    else:
        st.info("No financial data available.")

# 7. SUPER ADMIN: MANAGE SUBSCRIPTIONS
elif menu == "👑 Super Admin: Manage Subscriptions":
    st.header("👑 SaaS Subscriptions Management (Super Admin Only)")
    st.markdown("Manage client clinics, renewal dates, and active subscription status.")
    
    st.dataframe(st.session_state['subscriptions'], use_container_width=True)
    
    with st.form("add_sub_form"):
        st.subheader("Add or Update Clinic Subscription")
        new_clinic_name = st.text_input("Clinic Name")
        new_status = st.selectbox("Status", ["Active", "Suspended", "Expired"])
        expiry_input = st.date_input("Expiry Date", today + timedelta(days=30))
        
        sub_btn = st.form_submit_button("Save Subscription")
        if sub_btn and new_clinic_name:
            # Update or append
            subs = st.session_state['subscriptions']
            if new_clinic_name in subs['Clinic'].values:
                subs.loc[subs['Clinic'] == new_clinic_name, 'Status'] = new_status
                subs.loc[subs['Clinic'] == new_clinic_name, 'Expiry_Date'] = str(expiry_input)
            else:
                new_row = pd.DataFrame({'Clinic': [new_clinic_name], 'Status': [new_status], 'Expiry_Date': [str(expiry_input)]})
                st.session_state['subscriptions'] = pd.concat([subs, new_row], ignore_index=True)
            st.success(f"Subscription updated successfully for {new_clinic_name}!")
            st.rerun()
