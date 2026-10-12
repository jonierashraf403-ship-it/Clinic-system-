import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SaaS Multi-Clinic Management System", layout="wide")

# Initialize Global Session States
if 'users' not in st.session_state:
    st.session_state['users'] = pd.DataFrame({
        'Username': ['doctor_main', 'doctor_maadi', 'admin'],
        'Password': ['1234', '1234', 'admin123'],
        'Clinic': ['Main Branch', 'Maadi Branch', 'All Clinics'],
        'Role': ['Doctor', 'Doctor', 'Super Admin'],
        'Staff_Can_View_Finance': [False, False, True]
    })

if 'pricing_plans' not in st.session_state:
    st.session_state['pricing_plans'] = {
        '1 Month': 500,
        '3 Months': 1400,
        '6 Months': 2700,
        '9 Months': 3800,
        '1 Year': 5000
    }

if 'subscriptions' not in st.session_state:
    st.session_state['subscriptions'] = pd.DataFrame({
        'Clinic': ['Main Branch', 'Maadi Branch'],
        'Plan': ['1 Month', '3 Months'],
        'Status': ['Active', 'Active'],
        'Expiry_Date': [str(datetime.today().date() + timedelta(days=30)), str(datetime.today().date() + timedelta(days=90))]
    })

if 'patients' not in st.session_state:
    st.session_state['patients'] = pd.DataFrame({
        'Patient_ID': ['P-1001'],
        'Clinic': ['Main Branch'],
        'Name': ['Ahmed Ali'],
        'Phone': ['0123456789'],
        'Medical_History': ['None'],
        'Dental_History': ['Checkup'],
        'Notes': ['Regular'],
        'Total_Cost': [500.0],
        'Paid': [500.0],
        'Remaining': [0.0],
        'Date': [str(datetime.today().date())]
    })

if 'appointments' not in st.session_state:
    st.session_state['appointments'] = pd.DataFrame(columns=[
        'Clinic', 'Patient_Name', 'Phone', 'Date', 'Time', 'Procedure'
    ])

# Expenses & Salaries Table (Stored with positive numbers, system handles calculation)
if 'expenses' not in st.session_state:
    st.session_state['expenses'] = pd.DataFrame(columns=[
        'Clinic', 'Category', 'Description', 'Amount', 'Date', 'Month', 'Year'
    ])

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['clinic'] = ""
    st.session_state['role'] = ""
    st.session_state['staff_finance'] = False

# --- AUTHENTICATION & PORTAL ---
if not st.session_state['logged_in']:
    st.title("🔐 Multi-Clinic SaaS Portal")
    
    auth_mode = st.selectbox("Choose Action", ["Login", "Register New Clinic & Choose Plan", "Reset Password"])
    
    if auth_mode == "Login":
        st.subheader("Login to your Dashboard")
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
                    st.session_state['staff_finance'] = user_match.iloc[0]['Staff_Can_View_Finance']
                    st.success("Login successful! Loading dashboard...")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    elif auth_mode == "Register New Clinic & Choose Plan":
        st.subheader("Create a New Account & Select Subscription Plan")
        st.info("📦 Available Subscription Plans & Prices (EGP):")
        plans_df = pd.DataFrame(list(st.session_state['pricing_plans'].items()), columns=['Plan Duration', 'Price (EGP)'])
        st.table(plans_df)
        
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            new_clinic_name = st.text_input("Clinic / Branch Name")
            selected_plan = st.selectbox("Select Subscription Package", list(st.session_state['pricing_plans'].keys()))
            role_choice = st.selectbox("Account Type", ["Doctor (Clinic Owner)", "Staff / Receptionist"])
            
            reg_btn = st.form_submit_button("Proceed & Register")
            
            if reg_btn:
                if new_username and new_password and new_clinic_name:
                    users_df = st.session_state['users']
                    if new_username in users_df['Username'].values:
                        st.error("Username already exists.")
                    else:
                        days_map = {'1 Month': 30, '3 Months': 90, '6 Months': 180, '9 Months': 270, '1 Year': 365}
                        expiry_date = datetime.today().date() + timedelta(days=days_map[selected_plan])
                        
                        new_user_row = pd.DataFrame({
                            'Username': [new_username],
                            'Password': [new_password],
                            'Clinic': [new_clinic_name],
                            'Role': [role_choice],
                            'Staff_Can_View_Finance': [False]
                        })
                        st.session_state['users'] = pd.concat([users_df, new_user_row], ignore_index=True)
                        
                        subs = st.session_state['subscriptions']
                        new_sub_row = pd.DataFrame({
                            'Clinic': [new_clinic_name],
                            'Plan': [selected_plan],
                            'Status': ['Active'],
                            'Expiry_Date': [str(expiry_date)]
                        })
                        st.session_state['subscriptions'] = pd.concat([subs, new_sub_row], ignore_index=True)
                        st.success(f"Registered successfully! Please log in now.")
                else:
                    st.warning("Please fill in all required fields.")

    elif auth_mode == "Reset Password":
        st.subheader("Reset Your Password")
        with st.form("reset_form"):
            reset_username = st.text_input("Enter your Username")
            new_pass1 = st.text_input("New Password", type="password")
            new_pass2 = st.text_input("Confirm New Password", type="password")
            reset_btn = st.form_submit_button("Update Password")
            
            if reset_btn:
                users_df = st.session_state['users']
                if reset_username in users_df['Username'].values:
                    if new_pass1 == new_pass2 and new_pass1 != "":
                        st.session_state['users'].loc[st.session_state['users']['Username'] == reset_username, 'Password'] = new_pass1
                        st.success("Password updated successfully!")
                    else:
                        st.error("Passwords do not match.")
                else:
                    st.error("Username not found.")
                    
    st.stop()

# --- MAIN APP (AFTER LOGIN) ---
current_clinic = st.session_state['clinic']
current_role = st.session_state['role']
staff_can_view_finance = st.session_state['staff_finance']

st.sidebar.markdown(f"👤 **User:** {st.session_state['username']}")
st.sidebar.markdown(f"🏥 **Clinic:** {current_clinic}")
st.sidebar.markdown(f"🛡️ **Role:** {current_role}")

if st.sidebar.button("Log out"):
    st.session_state['logged_in'] = False
    st.rerun()

st.title(f"🏥 Multi-Clinic SaaS Platform - [{current_clinic}]")

menu_options = [
    "Today's Appointments & Reminders",
    "Book New Appointment",
    "All Appointments (By Date)",
    "Add New Patient / Session",
    "Patient Records & History (Secured)",
]

if current_role == "Super Admin" or "Doctor" in current_role or staff_can_view_finance:
    menu_options.append("Financial Reports & Debts Tracking")
    menu_options.append("📊 Expenses & Monthly/Annual P&L")

if current_role == "Super Admin":
    menu_options.append("👑 Super Admin: Manage Plans & Subscriptions")
elif "Doctor" in current_role:
    menu_options.append("⚙️ Doctor Settings: Staff Permissions")

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
                'Remaining': [remaining],
                'Date': [str(today)]
            })
            st.session_state['patients'] = pd.concat([st.session_state['patients'], new_pat], ignore_index=True)
            st.success(f"Patient saved securely with ID: {patient_id}")

# 5. PATIENT RECORDS & HISTORY (SECURED)
elif menu == "Patient Records & History (Secured)":
    st.header("🗂️ Patient Database & Data Protection")
    patients_df = filter_by_clinic(st.session_state['patients'])
    
    if not patients_df.empty:
        search_query = st.text_input("Search by Name or Phone:")
        df = patients_df.copy()
        if "Staff" in current_role and not staff_can_view_finance:
            df['Phone'] = df['Phone'].apply(lambda x: x[:4] + '****' + x[-2:] if len(str(x))>6 else '****')
            
        if search_query:
            df = df[df['Name'].str.contains(search_query, case=False, na=False) | df['Phone'].str.contains(search_query, na=False)]
        
        st.dataframe(df, use_container_width=True)
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
        st.subheader("📋 List of Patients with Remaining Balance (Debts)")
        debtors_df = patients_df[patients_df['Remaining'] > 0][['Patient_ID', 'Name', 'Phone', 'Clinic', 'Total_Cost', 'Paid', 'Remaining']]
        if not debtors_df.empty:
            st.dataframe(debtors_df, use_container_width=True)
        else:
            st.success("🎉 Excellent! There are no unpaid balances.")
    else:
        st.info("No financial data available.")

# 7. EXPENSES & MONTHLY/ANNUAL P&L
elif menu == "📊 Expenses & Monthly/Annual P&L":
    st.header("📊 Clinic Expenses, Salaries & Net Profit Summary")
    
    # Add Expense Form
    with st.form("expense_form"):
        st.subheader("➕ Record New Expense or Salary")
        col1, col2 = st.columns(2)
        with col1:
            if current_role == "Super Admin":
                exp_clinic = st.selectbox("Clinic Branch", ["Main Branch", "Maadi Branch", "Tagamoa Branch"])
            else:
                exp_clinic = current_clinic
            exp_category = st.selectbox("Expense Category", ["Staff Salaries", "Clinic Rent", "Medical Supplies & Tools", "Utilities (Water/Electricity)", "Maintenance & Cleaning", "Other Expenses"])
            exp_desc = st.text_input("Description / Notes (e.g., Nurse Salary, Dental Fillings)")
        with col2:
            exp_amount = st.number_input("Amount (EGP)", min_value=0.0, step=100.0)
            exp_date = st.date_input("Date", today)
            
        save_exp = st.form_submit_button("Save Expense")
        if save_exp and exp_amount > 0:
            exp_month = exp_date.strftime("%Y-%m")
            exp_year = str(exp_date.year)
            
            new_exp = pd.DataFrame({
                'Clinic': [exp_clinic],
                'Category': [exp_category],
                'Description': [exp_desc],
                'Amount': [exp_amount], # Stored as positive value
                'Date': [str(exp_date)],
                'Month': [exp_month],
                'Year': [exp_year]
            })
            st.session_state['expenses'] = pd.concat([st.session_state['expenses'], new_exp], ignore_index=True)
            st.success("Expense recorded successfully!")

    st.markdown("---")
    st.subheader("📈 Monthly Net Profit Calculation (Revenues - Expenses)")
    
    patients_df = filter_by_clinic(st.session_state['patients'])
    expenses_df = filter_by_clinic(st.session_state['expenses'])
    
    # Prepare Revenues by Month
    if not patients_df.empty and 'Date' in patients_df.columns:
        patients_df['Date'] = pd.to_datetime(patients_df['Date'], errors='coerce')
        patients_df['Month'] = patients_df['Date'].dt.strftime('%Y-%m')
        rev_summary = patients_df.groupby('Month')['Paid'].sum().reset_index()
        rev_summary.rename(columns={'Paid': 'Total Revenues'}, inplace=True)
    else:
        rev_summary = pd.DataFrame(columns=['Month', 'Total Revenues'])

    # Prepare Expenses by Month
    if not expenses_df.empty:
        exp_summary = expenses_df.groupby('Month')['Amount'].sum().reset_index()
        exp_summary.rename(columns={'Amount': 'Total Expenses'}, inplace=True)
    else:
        exp_summary = pd.DataFrame(columns=['Month', 'Total Expenses'])
        
    # Merge and calculate Net Profit
    if not rev_summary.empty or not exp_summary.empty:
        pnl_df = pd.merge(rev_summary, exp_summary, on='Month', how='outer').fillna(0)
        # Net Profit = Total Revenues minus Total Expenses
        pnl_df['Net Profit'] = pnl_df['Total Revenues'] - pnl_df['Total Expenses']
        
        st.dataframe(pnl_df, use_container_width=True)
    else:
        st.info("No financial data found for monthly calculation yet.")

    # Detailed Expenses Table
    st.markdown("---")
    st.subheader("📋 Recorded Expenses & Salaries List")
    if not expenses_df.empty:
        st.dataframe(expenses_df, use_container_width=True)
    else:
        st.info("No expenses recorded yet.")

# 8. SUPER ADMIN: MANAGE PLANS & SUBSCRIPTIONS
elif menu == "👑 Super Admin: Manage Plans & Subscriptions":
    st.header("👑 SaaS Pricing Plans & Subscriptions Control")
    st.dataframe(st.session_state['subscriptions'], use_container_width=True)

# 9. DOCTOR SETTINGS: STAFF PERMISSIONS
elif menu == "⚙️ Doctor Settings: Staff Permissions":
    st.header("⚙️ Doctor Settings & Staff Controls")
    with st.form("staff_perms_form"):
        allow_finance = st.checkbox("Allow Staff to View Financial Reports & Debts", value=staff_can_view_finance)
        save_perms = st.form_submit_button("Save Permissions")
        if save_perms:
            st.session_state['staff_finance'] = allow_finance
            st.success("Staff permissions updated successfully!")
            st.rerun()
