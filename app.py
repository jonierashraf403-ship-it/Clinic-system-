import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="شامل - منصة إدارة العيادات", layout="wide", page_icon="🏥")

today = datetime.today().date()

# --- DATABASE SETUP & CONNECTION ---
def init_db():
    conn = sqlite3.connect('shamel_clinics.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            clinic TEXT,
            role TEXT,
            staff_finance INTEGER,
            enable_booking INTEGER,
            brand_color TEXT,
            logo_url TEXT
        )
    ''')
    
    # Subscriptions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            clinic TEXT PRIMARY KEY,
            plan TEXT,
            status TEXT,
            expiry_date TEXT
        )
    ''')
    
    # Clinic Drugs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinic_drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic TEXT,
            drug_name TEXT,
            default_dosage TEXT
        )
    ''')
    
    # Patients Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            clinic TEXT,
            name TEXT,
            phone TEXT,
            medical_history TEXT,
            dental_history TEXT,
            notes TEXT,
            prescription TEXT,
            total_cost REAL,
            paid REAL,
            remaining REAL,
            date TEXT
        )
    ''')
    
    # Appointments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic TEXT,
            patient_name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT,
            procedure TEXT
        )
    ''')
    
    # Expenses Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            date TEXT,
            month TEXT,
            year TEXT
        )
    ''')
    
    # Insert Super Admin & Default Doctors
    default_users = [
        ('doctor_main', '1234', 'Main Branch', 'Doctor', 0, 1, '#007BFF', ''),
        ('doctor_maadi', '1234', 'Maadi Branch', 'Doctor', 0, 1, '#28A745', ''),
        ('jony ashraf', 'jony 7890', 'All Clinics', 'Super Admin', 1, 1, '#17A2B8', '')
    ]
    for user in default_users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, clinic, role, staff_finance, enable_booking, brand_color, logo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', user)
    
    # Seed Initial Subscriptions if empty
    cursor.execute('SELECT COUNT(*) FROM subscriptions')
    if cursor.fetchone()[0] == 0:
        default_subs = [
            ('Main Branch', '1 Month', 'Active', str(today + timedelta(days=30))),
            ('Maadi Branch', '3 Months', 'Active', str(today + timedelta(days=90)))
        ]
        cursor.executemany('INSERT INTO subscriptions VALUES (?, ?, ?, ?)', default_subs)
        
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect('shamel_clinics.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        data = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()
        return pd.DataFrame(data, columns=column_names)
    else:
        conn.commit()
        conn.close()

# Initialize Session State Variables for Login State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['clinic'] = ""
    st.session_state['role'] = ""
    st.session_state['staff_finance'] = False
    st.session_state['online_booking_enabled'] = True
    st.session_state['brand_color'] = "#007BFF"

if 'currency' not in st.session_state:
    st.session_state['currency'] = "USD $"

# --- SIDEBAR GLOBAL CONTROLS ---
st.sidebar.markdown("### 🌐 Global Settings")
currency_option = st.sidebar.selectbox("Select Currency", ["USD $", "EGP", "SAR", "AED", "EUR €"], index=0)
st.session_state['currency'] = currency_option

# Apply Dynamic Clinic Branding CSS
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
        </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION & PORTAL ---
if not st.session_state['logged_in']:
    st.title("🏥 شامل - منصة إدارة العيادات")
    
    users_df = run_query("SELECT * FROM users", fetch=True)
    pricing_plans = {
        '1 Month': 20.0,
        '3 Months': 55.0,
        '6 Months': 100.0,
        '9 Months': 140.0,
        '1 Year': 180.0
    }
    
    portal_actions = ["Login", "Register New Clinic & Subscription"]
    if not users_df.empty and (users_df['enable_booking'] == 1).any():
        portal_actions.append("Online Patient Self-Booking Portal")
    portal_actions.append("Reset Password")
    
    auth_mode = st.selectbox("Choose Action / Portal", portal_actions)
    
    # 1. LOGIN
    if auth_mode == "Login":
        st.subheader("🔐 Clinic Staff & Super Admin Login")
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                user_match = users_df[(users_df['username'] == username_input) & (users_df['password'] == password_input)]
                
                if not user_match.empty:
                    clinic_name = user_match.iloc[0]['clinic']
                    role_val = user_match.iloc[0]['role']
                    
                    if role_val != "Super Admin":
                        subs_df = run_query("SELECT * FROM subscriptions WHERE clinic = ?", (clinic_name,), fetch=True)
                        if not subs_df.empty:
                            expiry_str = subs_df.iloc[0]['expiry_date']
                            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                            
                            if today > expiry_date:
                                st.error(f"❌ Your subscription for '{clinic_name}' expired on {expiry_date}. Please renew your plan.")
                                st.stop()
                        else:
                            st.warning("⚠️ No active subscription found.")
                            st.stop()
                    
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user_match.iloc[0]['username']
                    st.session_state['clinic'] = clinic_name
                    st.session_state['role'] = role_val
                    st.session_state['staff_finance'] = bool(user_match.iloc[0]['staff_finance'])
                    st.session_state['online_booking_enabled'] = bool(user_match.iloc[0]['enable_booking'])
                    st.session_state['brand_color'] = user_match.iloc[0]['brand_color'] or '#007BFF'
                    st.success("تم تسجيل الدخول بنجاح! جاري التوجيه...")
                    st.rerun()
                else:
                    st.error("خطأ في اسم المستخدم أو كلمة المرور.")

    # 2. ONLINE PATIENT SELF-BOOKING PORTAL
    elif auth_mode == "Online Patient Self-Booking Portal":
        st.subheader("📅 Online Appointment Booking (Public Portal)")
        enabled_users = users_df[users_df['enable_booking'] == 1]
        available_clinics = [c for c in enabled_users['clinic'].unique().tolist() if c != "All Clinics"]
        
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
                    run_query(
                        "INSERT INTO appointments (clinic, patient_name, phone, date, time, procedure) VALUES (?, ?, ?, ?, ?, ?)",
                        (selected_clinic, p_name, p_phone, str(p_date), str(p_time), p_reason)
                    )
                    st.success(f"🎉 Appointment successfully requested for {p_date} at {selected_clinic}!")
        else:
            st.info("Online patient booking is currently disabled by clinics.")

    # 3. REGISTER & ONLINE PAYMENT GATEWAY
    elif auth_mode == "Register New Clinic & Subscription":
        st.subheader("💳 Register & Online Payment Gateway")
        st.info(f"📦 Subscription Plans ({st.session_state['currency']}):")
        plans_df = pd.DataFrame(list(pricing_plans.items()), columns=['Plan Duration', f'Price ({st.session_state["currency"]})'])
        st.table(plans_df)
        
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            new_clinic_name = st.text_input("Clinic / Practice Name")
            selected_plan = st.selectbox("Select Package", list(pricing_plans.keys()))
            card_number = st.text_input("Credit / Debit Card Number")
            
            reg_btn = st.form_submit_button("Pay Online & Activate Account")
            if reg_btn:
                if new_username and new_password and new_clinic_name and card_number:
                    if new_username in users_df['username'].values:
                        st.error("Username already exists.")
                    else:
                        days_map = {'1 Month': 30, '3 Months': 90, '6 Months': 180, '9 Months': 270, '1 Year': 365}
                        expiry_date = today + timedelta(days=days_map[selected_plan])
                        
                        run_query(
                            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (new_username, new_password, new_clinic_name, 'Doctor', 0, 1, '#007BFF', '')
                        )
                        run_query(
                            "INSERT INTO subscriptions VALUES (?, ?, ?, ?)",
                            (new_clinic_name, selected_plan, 'Active', str(expiry_date))
                        )
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
                if reset_username in users_df['username'].values:
                    run_query("UPDATE users SET password = ? WHERE username = ?", (new_pass1, reset_username))
                    st.success("Password updated successfully. You can now login.")
                else:
                    st.error("Username not found.")
                
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

st.title(f"🏥 شامل - [{current_clinic}]")

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

def filter_by_clinic(df, col_name='Clinic'):
    if current_role == "Super Admin" or current_clinic == "All Clinics":
        return df
    else:
        return df[df[col_name] == current_clinic]

# 1. TODAY'S SCHEDULE & AUTOMATED WHATSAPP REMINDERS
if menu == "Today's Appointments & WhatsApp Reminders":
    st.header("📅 Today's Appointments & Automated WhatsApp Reminders")
    appointments_df = run_query("SELECT * FROM appointments", fetch=True)
    appointments_df = filter_by_clinic(appointments_df, 'clinic')
    
    st.subheader(f"📌 Schedule for ({today})")
    if not appointments_df.empty:
        today_apps = appointments_df[appointments_df['date'] == str(today)]
        if not today_apps.empty:
            for idx, row in today_apps.iterrows():
                col_info, col_wa = st.columns([3, 1])
                col_info.write(f"⏰ **{row['time']}** - Patient: **{row['patient_name']}** ({row['phone']}) - Procedure: {row['procedure']}")
                
                wa_message = urllib.parse.quote(f"Hello {row['patient_name']}, this is a friendly reminder for your appointment today at {row['time']} ({row['clinic']}).")
                wa_url = f"https://wa.me/{row['phone']}?text={wa_message}"
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
            run_query(
                "INSERT INTO appointments (clinic, patient_name, phone, date, time, procedure) VALUES (?, ?, ?, ?, ?, ?)",
                (clinic, patient_name, phone, str(app_date), str(app_time), procedure)
            )
            st.success("Appointment booked successfully!")

# 3. ALL APPOINTMENTS (BY DATE)
elif menu == "All Appointments (By Date)":
    st.header("📆 Appointments Filter by Date")
    selected_date = st.date_input("Select Date", today)
    appointments_df = run_query("SELECT * FROM appointments", fetch=True)
    appointments_df = filter_by_clinic(appointments_df, 'clinic')
    if not appointments_df.empty:
        filtered_apps = appointments_df[appointments_df['date'] == str(selected_date)]
        st.dataframe(filtered_apps, use_container_width=True)
    else:
        st.info("No appointments found.")

# 4. PATIENT E-PRESCRIPTION & FILE ATTACHMENTS
elif menu == "Patient E-Prescription & Files (Medical History)":
    st.header("🗂️ Patient Medical Records & Digital Prescriptions")
    drugs_df = run_query("SELECT * FROM clinic_drugs WHERE clinic = ? OR clinic = 'Main Branch'", (current_clinic,), fetch=True)
    drug_options = drugs_df['drug_name'].tolist() if not drugs_df.empty else []
    
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
                
            patients_count = len(run_query("SELECT * FROM patients", fetch=True))
            patient_id = "P-" + str(patients_count + 1001)
            remaining = total_cost - paid
            
            run_query(
                "INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, current_clinic, name, phone, medical_hist, 'Checkup', 'Added via Dashboard', presc_text, total_cost, paid, remaining, str(today))
            )
            st.success(f"Record saved! ID: {patient_id}")

    st.markdown("---")
    st.subheader("📋 Patient Database & E-Prescription Sharing")
    patients_df = run_query("SELECT * FROM patients", fetch=True)
    patients_df = filter_by_clinic(patients_df, 'clinic')
    
    if not patients_df.empty:
        for idx, row in patients_df.iterrows():
            with st.expander(f"👤 Patient: {row['name']} ({row['phone']})"):
                st.write(f"**Medical History / Allergies:** {row['medical_history']}")
                st.write(f"**E-Prescription:** {row['prescription']}")
                st.write(f"**Financials:** Paid: {row['paid']} {curr_symbol} | Remaining: {row['remaining']} {curr_symbol}")
                
                msg = urllib.parse.quote(f"Hello {row['name']},\nHere is your prescription from {row['clinic']}:\n{row['prescription']}")
                st.markdown(f"[📲 Send Prescription via WhatsApp](https://wa.me/{row['phone']}?text={msg})")

# 5. DOCTOR'S DRUG LIST
elif menu == "💊 Doctor's Drug List (Clinic Master List)":
    st.header("💊 Clinic Drug Master List (Doctor's Custom Database)")
    drugs_df = run_query("SELECT drug_name, default_dosage FROM clinic_drugs WHERE clinic = ?", (current_clinic,), fetch=True)
    st.dataframe(drugs_df, use_container_width=True)
    
    with st.form("add_drug_form"):
        st.subheader("➕ Add New Medication to Clinic Database")
        new_drug_name = st.text_input("Medication Name & Strength")
        new_default_dose = st.text_input("Default Dosage Instructions")
        
        save_drug = st.form_submit_button("Add to Master Drug List")
        if save_drug and new_drug_name:
            run_query(
                "INSERT INTO clinic_drugs (clinic, drug_name, default_dosage) VALUES (?, ?, ?)",
                (current_clinic, new_drug_name, new_default_dose)
            )
            st.success(f"Medication '{new_drug_name}' added successfully!")
            st.rerun()

# 6. FINANCIAL REPORTS & OUTSTANDING BALANCES
elif menu == "Financial Reports & Outstanding Balances":
    st.header(f"💰 Financial Reports ({curr_symbol})")
    patients_df = run_query("SELECT * FROM patients", fetch=True)
    patients_df = filter_by_clinic(patients_df, 'clinic')
    if not patients_df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue Collected", f"{patients_df['paid'].sum()} {curr_symbol}")
        col2.metric("Total Outstanding Debt", f"{patients_df['remaining'].sum()} {curr_symbol}")
        st.dataframe(patients_df[['patient_id', 'name', 'phone', 'total_cost', 'paid', 'remaining']], use_container_width=True)
    else:
        st.info("No financial data found.")

# 7. EXPENSES & NET P&L SUMMARY
elif menu == "📊 Expenses & Net P&L Summary":
    st.header(f"📊 Expenses & Profit/Loss ({curr_symbol})")
    
    with st.form("expense_form"):
        st.subheader("➕ Record New Expense or Salary")
        col1, col2 = st.columns(2)
        with col1:
            exp_clinic = current_clinic if current_role != "Super Admin" else st.selectbox("Clinic Branch", ["Main Branch", "Maadi Branch", "Tagamoa Branch"])
            exp_category = st.selectbox("Expense Category", ["Staff Salaries", "Clinic Rent", "Medical Supplies & Tools", "Utilities", "Maintenance", "Other"])
            exp_desc = st.text_input("Description / Notes")
        with col2:
            exp_amount = st.number_input("Amount", min_value=0.0, step=50.0)
            exp_date = st.date_input("Date", today)
            
        save_exp = st.form_submit_button("Save Expense")
        if save_exp and exp_amount > 0:
            exp_month = exp_date.strftime("%Y-%m")
            run_query(
                "INSERT INTO expenses (clinic, category, description, amount, date, month, year) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (exp_clinic, exp_category, exp_desc, exp_amount, str(exp_date), exp_month, str(exp_date.year))
            )
            st.success("Expense recorded successfully!")
            st.rerun()

    st.markdown("---")
    patients_df = run_query("SELECT * FROM patients", fetch=True)
    patients_df = filter_by_clinic(patients_df, 'clinic')
    expenses_df = run_query("SELECT * FROM expenses", fetch=True)
    expenses_df = filter_by_clinic(expenses_df, 'clinic')
    
    rev = patients_df['paid'].sum() if not patients_df.empty else 0
    exp = expenses_df['amount'].sum() if not expenses_df.empty else 0
    net = rev - exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenues", f"{rev} {curr_symbol}")
    c2.metric("Total Expenses & Salaries", f"{exp} {curr_symbol}")
    c3.metric("Net Profit", f"{net} {curr_symbol}", delta=f"{net} {curr_symbol}")
    
    st.subheader("📋 Recorded Expenses List")
    if not expenses_df.empty:
        st.dataframe(expenses_df, use_container_width=True)

# 8. CLINIC BRANDING & CUSTOM THEME (WHITE-LABEL)
elif menu == "🎨 Clinic Branding & Custom Theme (White-Label)":
    st.header("🎨 White-Labeling & Clinic Branding Customization")
    with st.form("branding_form"):
        st.subheader("1. Select Brand Primary Color")
        chosen_color = st.color_picker("Choose Main Accent Color", st.session_state['brand_color'])
        
        st.subheader("2. Upload Clinic Logo")
        logo_file = st.file_uploader("Upload Clinic Logo (PNG, JPG)", type=['png', 'jpg', 'jpeg'])
        
        save_brand = st.form_submit_button("Apply Branding & Save Theme")
        if save_brand:
            st.session_state['brand_color'] = chosen_color
            run_query("UPDATE users SET brand_color = ? WHERE username = ?", (chosen_color, st.session_state['username']))
            st.success("🎉 Clinic Branding and Color Theme updated successfully!")
            st.rerun()

# 9. SUPER ADMIN CONTROL
elif menu == "👑 Super Admin: Global Plans & Subscriptions":
    st.header("👑 Super Admin Control")
    subs_df = run_query("SELECT * FROM subscriptions", fetch=True)
    st.dataframe(subs_df, use_container_width=True)

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
            run_query(
                "UPDATE users SET staff_finance = ?, enable_booking = ? WHERE username = ?",
                (int(allow_f), int(enable_online_b), st.session_state['username'])
            )
            st.success("Settings updated successfully!")
            st.rerun()
