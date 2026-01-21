import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Attendance System",
    page_icon="🕒",
    layout="centered"
)

# ---------------- UI STYLING (FINAL POLISH) ----------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #eef4ff, #f8fbff);
    font-family: 'Segoe UI', sans-serif;
}

/* Card */
.card {
    background: #ffffff;
    padding: 45px;
    border-radius: 22px;
    box-shadow: 0px 20px 45px rgba(31,60,136,0.15);
    margin-top: 20px;
}

/* Title */
.main-title {
    text-align: center;
    font-size: 36px;
    font-weight: 800;
    color: #2563eb;
}

/* Subtitle */
.sub-title {
    text-align: center;
    font-size: 16px;
    color: #4b5563;
    margin-bottom: 30px;
}

/* EMAIL INPUT – clean blue only */
div[data-baseweb="input"] > div {
    border: 2px solid #2563eb !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}

div[data-baseweb="input"][aria-invalid="true"] > div {
    border-color: #2563eb !important;
}

div[data-baseweb="input"]:focus-within > div {
    border-color: #2563eb !important;
}

/* Buttons */
.stButton > button {
    width: 240px;
    background: linear-gradient(90deg, #2563eb, #22c55e);
    color: white;
    font-size: 16px;
    font-weight: 600;
    border-radius: 999px;
    padding: 12px;
    border: none;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: scale(1.04);
}

/* SUCCESS MESSAGE – FIX SQUARE LOOK */
div[data-testid="stAlert"] {
    max-width: 420px;
    margin: 12px auto;
    border-radius: 999px !important;
    text-align: center;
}

/* Footer */
.footer {
    text-align: center;
    font-size: 12px;
    color: #6b7280;
    margin-top: 30px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- CARD START ----------------
st.markdown("""
<div class="card">
    <div class="main-title">Welcome to Attendance Portal</div>
    <div class="sub-title">Secure Employee Attendance Portal</div>
""", unsafe_allow_html=True)

# ---------------- ORIGINAL LOGIC (UNCHANGED) ----------------
tz = pytz.timezone("Asia/Kolkata")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(creds)

sheet = client.open("Remote_Attendance_System")

employees_ws = sheet.worksheet("Employees")
attendance_ws = sheet.worksheet("Attendance_Log")
shift_ws = sheet.worksheet("Shift_Rules")

employees_df = pd.DataFrame(employees_ws.get_all_records())
attendance_df = pd.DataFrame(attendance_ws.get_all_records())
shift_df = pd.DataFrame(shift_ws.get_all_records())

email = st.text_input("Enter your company email")

if email:
    employee = employees_df[employees_df["Email"] == email]

    if employee.empty:
        st.error("❌ Email not found. Contact HR.")
        st.stop()

    if employee.iloc[0]["Status"] != "Active":
        st.error("❌ Your account is inactive.")
        st.stop()

    st.success(f"Welcome {employee.iloc[0]['Employee_Name']} 👋")

today = datetime.now(tz).date()

attendance_df["Date_parsed"] = pd.to_datetime(
    attendance_df["Date"],
    errors="coerce",
    format="mixed"
).dt.date

today_record = attendance_df[
    (attendance_df["Email"] == email) &
    (attendance_df["Date_parsed"] == today)
]

if not today_record.empty:
    st.info("📌 Today's Attendance Status")
    st.write(today_record[
        ["Punch_In", "Punch_Out", "Work_Hours", "Attendance_Status"]
    ])

# ---------------- PUNCH IN (CENTER) ----------------
if today_record.empty and email:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ Punch In"):
            now = datetime.now(tz)
            attendance_ws.append_row([
                "",
                today.strftime("%Y-%m-%d"),
                employee.iloc[0]["Employee_ID"],
                employee.iloc[0]["Employee_Name"],
                email,
                employee.iloc[0]["Shift_Name"],
                now.strftime("%Y-%m-%d %H:%M:%S"),
                "", "", "", "", "", "", ""
            ])
            st.success("🎉 Punch In successful")
            st.rerun()

# ---------------- PUNCH OUT (CENTER) ----------------
if not today_record.empty and today_record.iloc[0]["Punch_Out"] == "":
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("⏹ Punch Out"):
            now = datetime.now(tz)
            row_index = today_record.index[0] + 2

            punch_in_time = pd.to_datetime(today_record.iloc[0]["Punch_In"])
            punch_in_time = tz.localize(punch_in_time)

            work_hours = round((now - punch_in_time).total_seconds() / 3600, 2)

            shift = shift_df[shift_df["Shift_Name"] == employee.iloc[0]["Shift_Name"]]
            full_day = float(shift.iloc[0]["Full_Day_Hrs"])
            half_day = float(shift.iloc[0]["Half_Day_Hrs"])

            status = "Present" if work_hours >= full_day else "Half Day" if work_hours >= half_day else "Absent"

            attendance_ws.update_cell(row_index, 8, now.strftime("%Y-%m-%d %H:%M:%S"))
            attendance_ws.update_cell(row_index, 9, work_hours)
            attendance_ws.update_cell(row_index, 10, status)

            st.success("⏹ Punch Out successful")
            st.rerun()

# ---------------- CARD END ----------------
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown("""
<div class="footer">
© 2026 | HR Attendance System | Powered by Streamlit
</div>
""", unsafe_allow_html=True)

# ---------------- LOGO (CENTER) ----------------
c1, c2, c3 = st.columns([4, 1, 4])
with c2:
    st.image("logo.png", width=70)
