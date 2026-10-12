import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="نظام إدارة العيادات", layout="wide")

if 'patients' not in st.session_state:
    st.session_state['patients'] = pd.DataFrame(columns=[
        'Patient_ID', 'Clinic', 'Name', 'Phone', 'Medical_History', 'Dental_History', 'Notes', 'Total_Cost', 'Paid', 'Remaining'
    ])

if 'appointments' not in st.session_state:
    st.session_state['appointments'] = pd.DataFrame(columns=[
        'Clinic', 'Patient_Name', 'Phone', 'Date', 'Time', 'Procedure'
    ])

st.title("🏥 نظام إدارة العيادات المتكامل (نسخة تجريبية)")

menu = st.sidebar.selectbox("اختر القسم", ["إدارة المواعيد", "ملفات المرضى والتاريخ المرضي", "إضافة مريض/جلسة جديدة", "التقارير المالية"])

if menu == "إدارة المواعيد":
    st.header("📅 إدارة ومتابعة المواعيد")
    
    with st.form("appointment_form"):
        col1, col2 = st.columns(2)
        with col1:
            clinic = st.selectbox("العيادة / الفرع", ["الفرع الرئيسي", "فرع المعادي", "فرع التجمع"])
            patient_name = st.text_input("اسم المريض")
            phone = st.text_input("رقم الهاتف")
        with col2:
            app_date = st.date_input("تاريخ الموعد", datetime.today())
            app_time = st.time_input("ساعة الموعد")
            procedure = st.text_input("الإجراء الطبي المستهدف")
        
        submitted = st.form_submit_button("حجز الموعد")
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

    st.subheader("جدول المواعيد المسجلة")
    if not st.session_state['appointments'].empty:
        st.dataframe(st.session_state['appointments'], use_container_width=True)
    else:
        st.info("لا توجد مواعيد مسجلة حتى الآن.")

elif menu == "إضافة مريض/جلسة جديدة":
    st.header("➕ إضافة ملف مريض جديد وتسجيل جلسة")
    
    with st.form("patient_form"):
        clinic = st.selectbox("العيادة", ["الفرع الرئيسي", "فرع المعادي", "فرع التجمع"])
        name = st.text_input("اسم المريض الرباعي")
        phone = st.text_input("رقم الهاتف")
        
        st.markdown("---")
        st.subheader("التاريخ الطبي والسلوكي")
        medical_hist = st.text_area("التاريخ المرضي العام (ضغط، سكر، سيولة، حساسية أدوية)")
        dental_hist = st.text_area("التاريخ التخصصي/الأسنان (حساسيات، تفاصيل سابقة)")
        notes = st.text_area("ملاحظات شخصية (مثل: يكره الانتظار، لا يفضل الموسيقى)")
        
        st.markdown("---")
        st.subheader("الماليات وتفاصيل الجلسة")
        col1, col2, col3 = st.columns(3)
        total_cost = col1.number_input("التكلفة الإجمالية", min_value=0.0, step=50.0)
        paid = col2.number_input("المبلغ المدفوع", min_value=0.0, step=50.0)
        remaining = total_cost - paid
        col3.write(f"**المبلغ الباقي:** {remaining} ج.م")
        
        save_btn = st.form_submit_button("حفظ ملف المريض والجلسة")
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

elif menu == "ملفات المرضى والتاريخ المرضي":
    st.header("🗂️ سجلات المرضى والبحث")
    if not st.session_state['patients'].empty:
        search_query = st.text_input("بحث بالاسم أو رقم التليفون:")
        df = st.session_state['patients']
        if search_query:
            df = df[df['Name'].str.contains(search_query, na=False) | df['Phone'].str.contains(search_query, na=False)]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لم يتم تسجيل أي مرضى حتى الآن.")

elif menu == "التقارير المالية":
    st.header("💰 الملخص المالي والإيرادات")
    if not st.session_state['patients'].empty:
        df = st.session_state['patients']
        total_revenue = df['Paid'].sum()
        total_remaining = df['Remaining'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("إجمالي التحصيلات (الدخل)", f"{total_revenue} ج.م")
        col2.metric("إجمالي المبالغ المتبقية على المرضى", f"{total_remaining} ج.م")
    else:
        st.info("لا توجد بيانات مالية متاحة حالياً.")
