import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="White-Label SaaS Clinic Platform", layout="wide", page_icon="🏥")

today = datetime.today().date()

# --- GLOBAL SESSION STATES ---
if 'users' not in st.session_state:
    st.session_state['users'] = pd.DataFrame({
        'Username': ['doctor_main', 'doctor_maadi', 'admin'],
        'Password': ['1234', '1234', 'admin123'],
        'Clinic': ['Main Branch', 'Maadi Branch', 'All Clinics'],
        'Role': ['Doctor', 'Doctor', 'Super Admin'],
        'Staff_Can_View_Finance': [False, False, True],
        'Enable_Online_Booking': [True, True, True],
        'Brand_Color': ['#007BFF', '#28A745', '#17A2B8'], # Custom theme per clinic
        'Logo_URL': ['', '', '']
    })

if 'pricing_plans' not in st.session_state:
    st.session_state['pricing_plans'] = {
        '1 Month': 20.0,
        '3 Months': 55.0,
        '6 Months': 100.0,
        '9 Months': 140.0,
        '1 Year': 180.0
    }

if 'subscriptions' not in st.session_state:
    st.session_state['subscriptions'] = pd.DataFrame({
        'Clinic': ['Main Branch', 'Maadi Branch'],
        'Plan': ['1 Month', '3 Months'],
        'Status': ['Active', 'Active'],
        'Expiry_Date': [str(today + timedelta(days=30)), str(today + timedelta(days=90))]
    })

if 'clinic_drugs' not in st.session_state:
    st.session_state['clinic_drugs'] = pd.DataFrame({
        'Drug_Name': ['Amoxicillin 500mg', 'Panadol Extra', 'Cataflam 50mg', 'Augmentin 1g'],
        'Default_Dosage': ['1 capsule every 8 hours', '1 tablet when needed', '1 tablet after meals', '1 tablet every 12 hours']
    })

if 'patients' not in st.session_state:
    st.session_state['patients'] = pd.DataFrame({
        'Patient_ID': ['P-1001'],
        'Clinic': ['Main Branch'],
        'Name': ['Ahmed Ali'],
        'Phone': ['201234567890'],
        'Medical_History': ['Penicillin Allergy'],
        'Dental_History': ['Root Canal'],
        'Notes': ['Regular Checkup'],
        'Prescription': ['Amoxicillin 500mg - 1 capsule every 8 hours'],
        'Total_Cost': [500.0],
        'Paid': [500.0],
        'Remaining': [0.0],
        'Date': [str(today)]
    })

if 'appointments' not in st.session_state:
    st.session_state['appointments'] = pd.DataFrame(columns=[
        'Clinic', 'Patient_Name', 'Phone', 'Date', 'Time', 'Procedure'
    ])

if 'expenses' not in st.session_state:
    st.session_state['expenses'] = pd.DataFrame(columns=[
        'Clinic', 'Category', 'Description', 'Amount', 'Date', 'Month', 'Year'
    ])

if 'currency' not in st.session_state:
    st.session_state['currency'] = "USD $"

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['clinic'] = ""
    st.session_state['role'] = ""
    st.session_state['staff_finance'] = False
    st.session_state['online_booking_enabled'] = True
    st.session_state['brand_color'] = "#007BFF"

# --- SIDEBAR GLOBAL CONTROLS ---
st.sidebar.markdown("### 🌐 Global Settings")
currency_option = st.sidebar.selectbox("Select Currency", ["USD $", "EGP", "SAR", "AED", "EUR €"], index=0)
st.session_state['currency'] = currency_option

# Apply Dynamic Clinic Branding CSS (White-Labeling)
if st.session_state['logged_in']:
    custom_color = st.session_state.get('brand_color', '#007BFF')
    st.markdown(f"""
        <style>
        .stButton>button {{
            background-color: {custom_color} !important;
            color: white !important;
            border-radius: 8px !important;
        }}
        h1, h2, h3 {{
            color: {custom_color} !important;
        }}
        .css-1d331aa {{
            background-color: {custom_color}10 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION & PORTAL ---
if not st.session_state['logged_in']:
    st.title("🌐 Global SaaS Multi-Clinic Portal")
    
    portal_actions = ["Login", "Register New Clinic & Subscription"]
    if any(st.session_state['users']['Enable_Online_Booking']):
        portal_actions.append("Online Patient Self-Booking Portal")
    portal_actions.append("Reset Password")
    
    auth_mode = st.selectbox("Choose Action / Portal", portal_actions)
    
    # 1. LOGIN
    if auth_mode == "Login":
        st.subheader("🔐 Clinic Staff Login")
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                users_df = st.session_state['users']
                user_match = users_df[(users_df['Username'] == username_input) & (users_df['Password'] == password_input)]
                
                if not user_match.empty:
                    clinic_name = user_match.iloc[0]['Clinic']
                    role_val = user_match.iloc[0]['Role']
                    
                    if role_val != "Super Admin":
                        subs_df = st.session_state['subscriptions']
                        clinic_sub = subs_df[subs_df['Clinic'] == clinic_name]
                        
                        if not clinic_sub.empty:
                            expiry_str = clinic_sub.iloc[0]['Expiry_Date']
                            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                            
                            if today > expiry_date:
                                st.error(f"❌ Your subscription for '{clinic_name}' expired on {expiry_date}. Please renew your plan.")
                                st.stop()
                        else:
                            st.warning("⚠️ No active subscription found.")
                            st.stop()
                    
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user_match.iloc[0]['Username']
                    st.session_state['clinic'] = clinic_name
                    st.session_state['role'] = role_val
                    st.session_state['staff_finance'] = user_match.iloc[0]['Staff_Can_View_Finance']
                    st.session_state['online_booking_enabled'] = user_match.iloc[0]['Enable_Online_Booking']
                    st.session_state['brand_color'] = user_match.iloc[0].get('Brand_Color', '#007BFF')
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    # 2. ONLINE PATIENT SELF-BOOKING PORTAL
    elif auth_mode == "Online Patient Self-Booking Portal":
        st.subheader("📅 Online Appointment Booking (Public Portal)")
        enabled_users = st.session_state['users'][st.session_state['users']['Enable_Online_Booking'] == True]
        available_clinics = [c for c in enabled_users['Clinic'].unique().tolist() if c != "All Clinics"]
        
        if available_clinics:
            with st.form("public_booking_form"):
                selected_clinic = st.selectbox("Select Clinic Branch", available_clinics)
                p_name = st.text_input("Your Full Name")
                p_phone = st.text_input("WhatsApp Phone Number (with Country Code)")
                p_date = st.date_input("Preferred Date", today)
                p_time = st.time_input("Preferred Time")
                p_reason = st.text_input("Reason for Visit / Treatment")
                
                book_btn = st.form_submit_button("Confirm Online Booking")
                if book_btn and p_name and p_phone:
                    new_app = pd.DataFrame({
                        'Clinic': [selected_clinic],
                        'Patient_Name': [p_name],
                        'Phone': [p_phone],
                        'Date': [str(p_date)],
                        'Time': [str(p_time)],
                        'Procedure': [p_reason]
                    })
                    st.session_state['appointments'] = pd.concat([st.session_state['appointments'], new_app], ignore_index=True)
                    st.success(f"🎉 Appointment successfully requested for {p_date} at {selected_clinic}!")
        else:
            st.info("Online patient booking is currently disabled by clinics.")

    # 3. REGISTER & ONLINE PAYMENT GATEWAY
    elif auth_mode == "Register New Clinic & Subscription":
        st.subheader("💳 Register & Online Payment Gateway")
        st.info(f"📦 Subscription Plans ({st.session_state['currency']}):")
        plans_df = pd.DataFrame(list(st.session_state['pricing_plans'].items()), columns=['Plan Duration', f'Price ({st.session_state["currency"]})'])
        st.table(plans_df)
        
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            new_clinic_name = st.text_input("Clinic / Practice Name")
            selected_plan = st.selectbox("Select Package", list(st.session_state['pricing_plans'].keys()))
            card_number = st.text_input("Credit / Debit Card Number")
            
            reg_btn = st.form_submit_button("Pay Online & Activate Account")
            if reg_btn:
                if new_username and new_password and new_clinic_name and card_number:
                    days_map = {'1 Month': 30, '3 Months': 90, '6 Months': 180, '9 Months': 270, '1 Year': 365}
                    expiry_date = today + timedelta(days=days_map[selected_plan])
                    
                    new_user_row = pd.DataFrame({
                        'Username': [new_username],
                        'Password': [new_password],
                        'Clinic': [new_clinic_name],
                        'Role': ['Doctor'],
                        'Staff_Can_View_Finance': [False],
                        'Enable_Online_Booking': [True],
                        'Brand_Color': ['#007BFF'],
                        'Logo_URL': ['']
                    })
                    st.session_state['users'] = pd.concat([st.session_state['users'], new_user_row], ignore_index=True)
                    
                    subs = st.session_state['subscriptions']
                    new_sub_row = pd.DataFrame({
                        'Clinic': [new_clinic_name],
                        'Plan': [selected_plan],
                        'Status': ['Active'],
                        'Expiry_Date': [str(expiry_date)]
                    })
                    st.session_state['subscriptions'] = pd.concat([subs, new_sub_row], ignore_index=True)
                    st.success(f"🎉 Payment Approved! Subscription Active until {expiry_date}. Please Login.")
                else:
                    st.warning("Please complete all details.")

    # 4. RESET PASSWORD
    elif auth_mode == "Reset Password":
        st.subheader("Reset Password")
        with st.form("reset_form"):
            reset_username = st.text_input("Enter Username")
            new_pass1 = st.text_input("New Password", type="password")
            new_pass2 = st.text_input("Confirm Password", type="password")
            reset_btn = st.form_submit_button("Reset")
            if reset_btn and new_pass1 == new_pass2:
                st.session_state['users'].loc[st.session_state['users']['Username'] == reset_username, 'Password'] = new_pass1
                st.success("Password updated successfully.")
                
    st.stop()

# --- MAIN DASHBOARD (AFTER LOGIN) ---
current_clinic = st.session_state['clinic']
current_role = st.session_state['role']
staff_can_view_finance = st.session_state['staff_finance']
online_booking_enabled = st.session_state['online_booking_enabled']
curr_symbol = st.session_state['currency']

st.sidebar.markdown(f"👤 **User:** {st.session_state['username']}")
st.sidebar.markdown(f"🏥 **Clinic:** {current_clinic}")
st.sidebar.markdown(f"🛡️ **Role:** {current_role}")

if st.sidebar.button("Log out"):
    st.session_state['logged_in'] = False
    st.rerun()

st.title(f"🏥 {current_clinic} - Management Portal")

menu_options = [
    "Today's Appointments & WhatsApp Reminders",
    "Book New Appointment",
    "All Appointments (By Date)",
    "Patient E-Prescription & Files (Medical History)",
    "💊 Doctor's Drug List (Clinic Master List)",
]

if current_role == "Super Admin" or "Doctor" in current_role or staff_can_view_finance:
    menu_options.append("Financial Reports & Outstanding Balances")
    menu_options.append("📊 Expenses & Net P&L Summary")

if current_role == "Super Admin":
    menu_options.append("👑 Super Admin: Global Plans & Subscriptions")
elif "Doctor" in current_role:
    menu_options.append("🎨 Clinic Branding & Custom Theme (White-Label)")
    menu_options.append("⚙️ Doctor Settings: Feature Controls")

menu = st.sidebar.selectbox("Navigation", menu_options)
tomorrow = today + timedelta(days=1)

def filter_by_clinic(df):
    if current_role == "Super Admin" or current_clinic == "All Clinics":
        return df
    else:
        return df[df['Clinic'] == current_clinic]

# 1. TODAY'S SCHEDULE & AUTOMATED WHATSAPP REMINDERS
if menu == "Today's Appointments & WhatsApp Reminders":
    st.header("📅 Today's Appointments & Automated WhatsApp Reminders")
    appointments_df = filter_by_clinic(st.session_state['appointments'])
    
    st.subheader(f"📌 Schedule for ({today})")
    if not appointments_df.empty:
        today_apps = appointments_df[appointments_df['Date'] == str(today)]
        if not today_apps.empty:
            for idx, row in today_apps.iterrows():
                col_info, col_wa = st.columns([3, 1])
                col_info.write(f"⏰ **{row['Time']}** - Patient: **{row['Patient_Name']}** ({row['Phone']}) - Procedure: {row['Procedure']}")
                
                wa_message = urllib.parse.quote(f"Hello {row['Patient_Name']}, this is a friendly reminder for your appointment today at {row['Time']} ({row['Clinic']}).")
                wa_url = f"https://wa.me/{row['Phone']}?text={wa_message}"
                col_wa.markdown(f"[📲 Send WhatsApp Reminder]({wa_url})", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No appointments for today.")
    else:
        st.info("No appointments recorded.")

# 2. BOOK NEW APPOINTMENT
elif menu == "Book New Appointment":
    st.header("➕ Schedule New Appointment")
    with st.form("appointment_form"):
        col1, col2 = st.columns(2)
        with col1:
            clinic = current_clinic if current_role != "Super Admin" else st.selectbox("Clinic Branch", ["Main Branch", "Maadi Branch", "Tagamoa Branch"])
            patient_name = st.text_input("Patient Full Name")
            phone = st.text_input("Phone Number (with Country Code)")
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
            st.success("Appointment booked successfully!")

# 3. ALL APPOINTMENTS (BY DATE)
elif menu == "All Appointments (By Date)":
    st.header("📆 Appointments Filter by Date")
    selected_date = st.date_input("Select Date", today)
    appointments_df = filter_by_clinic(st.session_state['appointments'])
    if not appointments_df.empty:
        filtered_apps = appointments_df[appointments_df['Date'] == str(selected_date)]
        st.dataframe(filtered_apps, use_container_width=True)
    else:
        st.info("No appointments found.")

# 4. PATIENT E-PRESCRIPTION & FILE ATTACHMENTS
elif menu == "Patient E-Prescription & Files (Medical History)":
    st.header("🗂️ Patient Medical Records & Digital Prescriptions")
    drug_options = st.session_state['clinic_drugs']['Drug_Name'].tolist() if not st.session_state['clinic_drugs'].empty else []
    
    with st.form("add_patient_e_presc"):
        st.subheader("➕ Create Patient Record & Manual Prescription")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Patient Name")
            phone = st.text_input("WhatsApp Phone")
            medical_hist = st.text_area("Medical History / Allergies")
        with c2:
            selected_drug = st.selectbox("Select Drug from Master List (Optional)", ["-- Custom / Other --"] + drug_options)
            custom_presc = st.text_area("Write Prescription Details & Instructions")
            uploaded_file = st.file_uploader("Upload X-Rays / Photos (PNG, JPG, PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])
            total_cost = st.number_input(f"Total Cost ({curr_symbol})", min_value=0.0)
            paid = st.number_input(f"Paid ({curr_symbol})", min_value=0.0)
            
        save_p = st.form_submit_button("Save Record & Prescription")
        if save_p and name:
            presc_text = custom_presc
            if selected_drug != "-- Custom / Other --":
                presc_text = f"[{selected_drug}] - " + custom_presc
                
            patient_id = "P-" + str(len(st.session_state['patients']) + 1001)
            new_pat = pd.DataFrame({
                'Patient_ID': [patient_id],
                'Clinic': [current_clinic],
                'Name': [name],
                'Phone': [phone],
                'Medical_History': [medical_hist],
                'Dental_History': ['Checkup'],
                'Notes': ['Added via Dashboard'],
                'Prescription': [presc_text],
                'Total_Cost': [total_cost],
                'Paid': [paid],
                'Remaining': [total_cost - paid],
                'Date': [str(today)]
            })
            st.session_state['patients'] = pd.concat([st.session_state['patients'], new_pat], ignore_index=True)
            st.success(f"Record saved! ID: {patient_id}")

    st.markdown("---")
    st.subheader("📋 Patient Database & E-Prescription Sharing")
    patients_df = filter_by_clinic(st.session_state['patients'])
    
    if not patients_df.empty:
        for idx, row in patients_df.iterrows():
            with st.expander(f"👤 Patient: {row['Name']} ({row['Phone']})"):
                st.write(f"**Medical History / Allergies:** {row['Medical_History']}")
                st.write(f"**E-Prescription:** {row['Prescription']}")
                st.write(f"**Financials:** Paid: {row['Paid']} {curr_symbol} | Remaining: {row['Remaining']} {curr_symbol}")
                
                msg = urllib.parse.quote(f"Hello {row['Name']},\nHere is your prescription from {row['Clinic']}:\n{row['Prescription']}")
                st.markdown(f"[📲 Send Prescription via WhatsApp](https://wa.me/{row['Phone']}?text={msg})")

# 5. DOCTOR'S DRUG LIST
elif menu == "💊 Doctor's Drug List (Clinic Master List)":
    st.header("💊 Clinic Drug Master List (Doctor's Custom Database)")
    st.dataframe(st.session_state['clinic_drugs'], use_container_width=True)
    
    with st.form("add_drug_form"):
        st.subheader("➕ Add New Medication to Clinic Database")
        new_drug_name = st.text_input("Medication Name & Strength")
        new_default_dose = st.text_input("Default Dosage Instructions")
        
        save_drug = st.form_submit_button("Add to Master Drug List")
        if save_drug and new_drug_name:
            new_drug_row = pd.DataFrame({
                'Drug_Name': [new_drug_name],
                'Default_Dosage': [new_default_dose]
            })
            st.session_state['clinic_drugs'] = pd.concat([st.session_state['clinic_drugs'], new_drug_row], ignore_index=True)
            st.success(f"Medication '{new_drug_name}' added successfully!")
            st.rerun()

# 6. FINANCIAL REPORTS & OUTSTANDING BALANCES
elif menu == "Financial Reports & Outstanding Balances":
    st.header(f"💰 Financial Reports ({curr_symbol})")
    patients_df = filter_by_clinic(st.session_state['patients'])
    if not patients_df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue Collected", f"{patients_df['Paid'].sum()} {curr_symbol}")
        col2.metric("Total Outstanding Debt", f"{patients_df['Remaining'].sum()} {curr_symbol}")
        st.dataframe(patients_df[['Patient_ID', 'Name', 'Phone', 'Total_Cost', 'Paid', 'Remaining']], use_container_width=True)

# 7. EXPENSES & NET P&L SUMMARY
elif menu == "📊 Expenses & Net P&L Summary":
    st.header(f"📊 Expenses & Profit/Loss ({curr_symbol})")
    patients_df = filter_by_clinic(st.session_state['patients'])
    expenses_df = filter_by_clinic(st.session_state['expenses'])
    
    rev = patients_df['Paid'].sum() if not patients_df.empty else 0
    exp = expenses_df['Amount'].sum() if not expenses_df.empty else 0
    net = rev - exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenues", f"{rev} {curr_symbol}")
    c2.metric("Total Expenses & Salaries", f"{exp} {curr_symbol}")
    c3.metric("Net Profit", f"{net} {curr_symbol}", delta=f"{net} {curr_symbol}")

# 8. CLINIC BRANDING & CUSTOM THEME (WHITE-LABELING)
elif menu == "🎨 Clinic Branding & Custom Theme (White-Label)":
    st.header("🎨 White-Labeling & Clinic Branding Customization")
    st.markdown("Customize your platform appearance to match your clinic's brand identity.")
    
    with st.form("branding_form"):
        st.subheader("1. Select Brand Primary Color")
        chosen_color = st.color_picker("Choose Main Accent Color", st.session_state['brand_color'])
        
        st.subheader("2. Upload Clinic Logo")
        logo_file = st.file_uploader("Upload Clinic Logo (PNG, JPG)", type=['png', 'jpg', 'jpeg'])
        
        save_brand = st.form_submit_button("Apply Branding & Save Theme")
        if save_brand:
            st.session_state['brand_color'] = chosen_color
            st.session_state['users'].loc[st.session_state['users']['Username'] == st.session_state['username'], 'Brand_Color'] = chosen_color
            st.success("🎉 Clinic Branding and Color Theme updated successfully!")
            st.rerun()

# 9. SUPER ADMIN CONTROL
elif menu == "👑 Super Admin: Global Plans & Subscriptions":
    st.header("👑 Super Admin Control")
    st.dataframe(st.session_state['subscriptions'], use_container_width=True)

# 10. DOCTOR SETTINGS
elif menu == "⚙️ Doctor Settings: Feature Controls":
    st.header("⚙️ Doctor Settings & Feature Controls")
    with st.form("doctor_settings_form"):
        allow_f = st.checkbox("Allow Staff to View Financial Reports", value=staff_can_view_finance)
        enable_online_b = st.checkbox("Enable Online Patient Self-Booking Portal", value=online_booking_enabled)
        
        save_settings = st.form_submit_button("Save Clinic Settings")
        if save_settings:
            st.session_state['staff_finance'] = allow_f
            st.session_state['online_booking_enabled'] = enable_online_b
            st.session_state['users'].loc[st.session_state['users']['Username'] == st.session_state['username'], 'Staff_Can_View_Finance'] = allow_f
            st.session_state['users'].loc[st.session_state['users']['Username'] == st.session_state['username'], 'Enable_Online_Booking'] = enable_online_b
            st.success("Settings updated successfully!")
            st.rerun()
