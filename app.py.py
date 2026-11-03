"""
Secondary Higher Education & High School Datta Khel
School management website built with Streamlit + SQLite + Groq AI.

Features:
- Public: home, online admission form, application tracking, AI assistant
- Registration & login (roles: admin, teacher, student, applicant)
- Admin: add teachers / students, manage applications, attendance, reports
- Teachers: mark student attendance, view own attendance
- Students: view own attendance
"""

import base64
import os
import secrets
import hashlib
import sqlite3
import string
from datetime import date, timedelta

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIG  (edit these to match your school)
# ----------------------------------------------------------------------------
SCHOOL_NAME = "Secondary Higher Education & High School Datta Khel"
SCHOOL_SHORT = "SHE & High School Datta Khel"
SCHOOL_ADDRESS = "Datta Khel, North Waziristan, Khyber Pakhtunkhwa, Pakistan"
SCHOOL_PHONE = "03XX-XXXXXXX"
SCHOOL_EMAIL = "info@example.com"
OFFICE_HOURS = "Monday - Saturday, 8:00 AM - 2:00 PM"
DB_PATH = "school.db"

CLASSES = ["Nursery", "Prep"] + [str(i) for i in range(1, 11)] + [
    "11 (1st Year)",
    "12 (2nd Year)",
]
ATT_STATUS = ["Present", "Absent", "Late", "Leave"]
APP_STATUS = ["Pending", "Under Review", "Approved", "Rejected", "Admitted"]

LOGO_FILES = ["logo.png", "logo.jpg", "logo.jpeg", "logo.webp"]  # put your logo next to app.py


def find_logo():
    for p in LOGO_FILES:
        if os.path.exists(p):
            return p
    return None


st.set_page_config(
    page_title=SCHOOL_NAME, page_icon=find_logo() or "🏫", layout="wide"
)


@st.cache_data
def logo_data_uri():
    p = find_logo()
    if not p:
        return None
    ext = p.rsplit(".", 1)[1].lower().replace("jpg", "jpeg")
    with open(p, "rb") as f:
        return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode()


def logo_html(size=60):
    src = logo_data_uri()
    if src:
        return (
            f'<img src="{src}" style="height:{size}px;width:auto;display:block;margin:0 auto;'
            f'filter:drop-shadow(0 2px 4px rgba(0,0,0,.25))">'
        )
    return "🏫"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

    :root {
        --g1: #0b5d3b; --g2: #138a5a; --g3: #e8f5ee; --gold: #f2b134;
        --card-bg: rgba(127,127,127,.07); --card-border: rgba(127,127,127,.22);
    }
    html, body, [class*="css"], .stMarkdown, button, input, textarea {
        font-family: 'Poppins', sans-serif !important;
    }
    /* hide default Streamlit chrome */
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    .block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1250px; }

    /* ---------- top banner ---------- */
    .school-banner {
        background: linear-gradient(120deg, var(--g1), var(--g2) 60%, #1aa36c);
        color: #fff; padding: 22px 28px; border-radius: 16px; margin-bottom: 22px;
        display: flex; align-items: center; gap: 18px;
        box-shadow: 0 8px 24px rgba(11,93,59,.25);
        border-bottom: 4px solid var(--gold);
    }
    .school-banner .logo {
        font-size: 2.4rem; min-width: 64px; min-height: 64px;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .school-banner h2 { margin: 0; color: #fff; font-size: 1.45rem; font-weight: 700; line-height: 1.25; }
    .school-banner p  { margin: 4px 0 0 0; opacity: .9; font-size: .9rem; }

    /* ---------- hero ---------- */
    .hero {
        background: linear-gradient(135deg, var(--g3), rgba(19,138,90,.12));
        border: 1px solid var(--card-border); border-radius: 18px;
        padding: 34px 32px; margin-bottom: 22px;
    }
    .hero h1 { margin: 0 0 8px 0; font-size: 2rem; font-weight: 700; }
    .hero p  { margin: 0; font-size: 1.02rem; opacity: .85; max-width: 760px; }
    .hero .tag {
        display: inline-block; background: var(--gold); color: #3a2a00;
        padding: 4px 14px; border-radius: 999px; font-size: .78rem; font-weight: 600; margin-bottom: 12px;
    }

    /* ---------- cards ---------- */
    .card {
        background: var(--card-bg); border: 1px solid var(--card-border);
        border-radius: 14px; padding: 20px 20px; height: 100%;
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,.10); }
    .card .icon { font-size: 1.9rem; }
    .card h4 { margin: 8px 0 6px 0; font-size: 1.05rem; font-weight: 600; }
    .card p  { margin: 0; font-size: .9rem; opacity: .8; }

    .stat {
        border-radius: 14px; padding: 18px 20px; color: #fff;
        box-shadow: 0 6px 16px rgba(0,0,0,.12);
    }
    .stat .num { font-size: 1.9rem; font-weight: 700; line-height: 1.1; }
    .stat .lbl { font-size: .85rem; opacity: .92; margin-top: 2px; }
    .stat.s1 { background: linear-gradient(135deg, #0b5d3b, #1aa36c); }
    .stat.s2 { background: linear-gradient(135deg, #1b5fa8, #3b8fe0); }
    .stat.s3 { background: linear-gradient(135deg, #c46a00, #f2a33a); }
    .stat.s4 { background: linear-gradient(135deg, #6a3fb0, #9a6fe0); }
    .stat.s5 { background: linear-gradient(135deg, #a8324a, #e05a77); }

    .section-title {
        font-size: 1.35rem; font-weight: 700; margin: 6px 0 14px 0;
        padding-left: 12px; border-left: 5px solid var(--gold);
    }
    .page-sub { opacity: .75; margin: -6px 0 18px 0; }

    .badge {
        display: inline-block; padding: 4px 14px; border-radius: 999px;
        font-size: .85rem; font-weight: 600; color: #fff;
    }
    .b-Pending { background: #c98a00; } .b-Under-Review { background: #1b5fa8; }
    .b-Approved { background: #138a5a; } .b-Rejected { background: #c0392b; }
    .b-Admitted { background: #6a3fb0; }

    /* ---------- sidebar ---------- */
    section[data-testid="stSidebar"] { border-right: 1px solid var(--card-border); }
    .side-brand { text-align: center; padding: 6px 0 12px 0; }
    .side-brand .logo { font-size: 2.6rem; }
    .side-brand .name { font-weight: 700; font-size: 1rem; line-height: 1.3; }
    .user-chip {
        background: var(--g3); color: #0b3d28; border-radius: 12px;
        padding: 10px 14px; margin: 8px 0 14px 0; font-size: .88rem;
    }
    .user-chip b { display: block; font-size: .95rem; }
    section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 4px; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        padding: 9px 12px; border-radius: 10px; width: 100%;
        border: 1px solid transparent; transition: background .12s;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: var(--card-bg); }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, var(--g1), var(--g2)); color: #fff;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) * { color: #fff !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }

    /* ---------- inputs & buttons ---------- */
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
        border-radius: 10px; font-weight: 600; padding: .55rem 1.3rem;
        border: 1px solid var(--g2);
    }
    .stFormSubmitButton > button, .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--g1), var(--g2)); color: #fff; border: none;
    }
    .stFormSubmitButton > button:hover { filter: brightness(1.1); color: #fff; }
    div[data-testid="stForm"] {
        border: 1px solid var(--card-border); border-radius: 16px; padding: 22px 22px 14px 22px;
        background: var(--card-bg);
    }
    div[data-testid="stMetric"] {
        background: var(--card-bg); border: 1px solid var(--card-border);
        padding: 14px 16px; border-radius: 12px;
    }
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    .login-wrap { text-align: center; margin-bottom: 6px; }
    .login-wrap .big { font-size: 3rem; }

    @media (max-width: 640px) {
        .school-banner { padding: 16px; gap: 12px; }
        .school-banner h2 { font-size: 1.05rem; }
        .school-banner .logo { min-width: 48px; min-height: 48px; font-size: 1.7rem; }
        .school-banner .logo img { height: 64px !important; }
        .hero { padding: 22px 18px; } .hero h1 { font-size: 1.4rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def title(text, sub=None):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="page-sub">{sub}</div>', unsafe_allow_html=True)


def stat_card(col, number, label, style="s1"):
    col.markdown(
        f'<div class="stat {style}"><div class="num">{number}</div><div class="lbl">{label}</div></div>',
        unsafe_allow_html=True,
    )


def info_card(col, icon, heading, text):
    col.markdown(
        f'<div class="card"><div class="icon">{icon}</div><h4>{heading}</h4><p>{text}</p></div>',
        unsafe_allow_html=True,
    )


def badge(status):
    return f'<span class="badge b-{status.replace(" ", "-")}">{status}</span>'


# ----------------------------------------------------------------------------
# SECRETS
# ----------------------------------------------------------------------------
def secret(key, default=None):
    """Read from Streamlit secrets, then environment variables."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


# ----------------------------------------------------------------------------
# DATABASE
# ----------------------------------------------------------------------------
def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def execute(sql, params=()):
    c = conn()
    try:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def bulk(sql, rows):
    c = conn()
    try:
        c.executemany(sql, rows)
        c.commit()
    finally:
        c.close()


def query(sql, params=()):
    c = conn()
    try:
        return [dict(r) for r in c.execute(sql, params).fetchall()]
    finally:
        c.close()


def one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def frame(sql, params=()):
    c = conn()
    try:
        return pd.read_sql_query(sql, c, params=params)
    finally:
        c.close()


def init_db():
    c = conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','teacher','student','applicant')),
            full_name TEXT NOT NULL,
            ref_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            father_name TEXT,
            class_name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS teachers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT,
            qualification TEXT,
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS applications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            father_name TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            applying_class TEXT NOT NULL,
            previous_school TEXT,
            phone TEXT NOT NULL,
            id_number TEXT,
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            remarks TEXT,
            applicant_user_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS student_attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            att_date TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_by TEXT,
            UNIQUE(student_id, att_date)
        );
        CREATE TABLE IF NOT EXISTS teacher_attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
            att_date TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_by TEXT,
            UNIQUE(teacher_id, att_date)
        );
        """
    )
    c.commit()
    c.close()


# ----------------------------------------------------------------------------
# AUTH HELPERS
# ----------------------------------------------------------------------------
def hash_pw(password, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 200_000
    ).hex()
    return h, salt


def username_taken(username):
    return one("SELECT id FROM users WHERE username=?", (username.strip().lower(),)) is not None


def create_user(username, password, role, full_name, ref_id=None):
    h, s = hash_pw(password)
    return execute(
        "INSERT INTO users(username,password_hash,salt,role,full_name,ref_id) VALUES(?,?,?,?,?,?)",
        (username.strip().lower(), h, s, role, full_name, ref_id),
    )


def authenticate(username, password):
    u = one("SELECT * FROM users WHERE username=?", (username.strip().lower(),))
    if not u:
        return None
    h, _ = hash_pw(password, u["salt"])
    return u if secrets.compare_digest(h, u["password_hash"]) else None


def gen_password(n=8):
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))


def next_roll():
    n = one("SELECT COALESCE(MAX(id),0)+1 AS n FROM students")["n"]
    return f"DK-{date.today().year}-{n:04d}"


def need(*values):
    return all(str(v).strip() for v in values)


@st.cache_resource
def setup():
    init_db()
    if not one("SELECT id FROM users WHERE role='admin'"):
        create_user(
            secret("ADMIN_USERNAME", "admin"),
            secret("ADMIN_PASSWORD", "admin123"),
            "admin",
            "School Administrator",
        )
    return True


def flash(msg):
    st.session_state["flash"] = msg
    st.rerun()


# ----------------------------------------------------------------------------
# PUBLIC PAGES
# ----------------------------------------------------------------------------
def page_home():
    ns = one("SELECT COUNT(*) AS n FROM students")["n"]
    nt = one("SELECT COUNT(*) AS n FROM teachers")["n"]

    st.markdown(
        f"""
        <div class="hero">
            <span class="tag">📢 Admissions Open {date.today().year}</span>
            <h1>Shaping the future of Datta Khel through quality education</h1>
            <p>{SCHOOL_NAME} offers education from Nursery up to Higher Secondary,
            with discipline, dedicated teachers and a focus on every child's success.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    stat_card(c1, ns, "Students enrolled", "s1")
    stat_card(c2, nt, "Teachers", "s2")
    stat_card(c3, "Nursery - 12", "Classes offered", "s3")

    st.write("")
    title("What you can do here")
    a, b, c, d = st.columns(4)
    info_card(a, "📝", "Apply Online", "Submit an admission application from home in a few minutes.")
    info_card(b, "🔎", "Track Application", "Check your application status with your tracking ID.")
    info_card(c, "📅", "Attendance", "Teachers mark attendance daily; students see their record.")
    info_card(d, "🤖", "AI Assistant", "Ask questions in English, Urdu or Pashto, any time.")

    st.write("")
    title("Contact us")
    a, b, c, d = st.columns(4)
    info_card(a, "📍", "Address", SCHOOL_ADDRESS)
    info_card(b, "📞", "Phone", SCHOOL_PHONE)
    info_card(c, "✉️", "Email", SCHOOL_EMAIL)
    info_card(d, "🕗", "Office hours", OFFICE_HOURS)


def page_apply():
    title("📝 Online Admission Application", "Fill in the form below. Fields marked * are required.")
    user = st.session_state.get("user")
    if not user:
        st.info("Tip: create an account (Register) before applying so you can see all your applications in one place. You can still apply without an account.")

    with st.form("apply_form"):
        st.markdown("**👦 Student information**")
        c1, c2 = st.columns(2)
        name = c1.text_input("Student full name *", placeholder="e.g. Ahmad Khan")
        father = c2.text_input("Father / guardian name *", placeholder="e.g. Gul Khan")
        dob = c1.date_input(
            "Date of birth",
            value=date(2012, 1, 1),
            min_value=date(1995, 1, 1),
            max_value=date.today(),
        )
        gender = c2.selectbox("Gender", ["Male", "Female", "Other"])
        cls = c1.selectbox("Applying for class *", CLASSES)
        prev = c2.text_input("Previous school (if any)")
        st.markdown("**📞 Contact details**")
        c3, c4 = st.columns(2)
        phone = c3.text_input("Contact phone *", placeholder="03XX-XXXXXXX")
        id_no = c4.text_input("B-Form / CNIC number (optional)")
        address = st.text_area("Home address *")
        submit = st.form_submit_button("✅ Submit application")

    if submit:
        if not need(name, father, phone, address):
            st.error("Please fill all fields marked with *.")
            return
        tracking = "APP-" + secrets.token_hex(4).upper()
        execute(
            """INSERT INTO applications(tracking_id, student_name, father_name, dob, gender,
               applying_class, previous_school, phone, id_number, address, applicant_user_id)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                tracking, name.strip(), father.strip(), dob.isoformat(), gender, cls,
                prev.strip(), phone.strip(), id_no.strip(), address.strip(),
                user["id"] if user else None,
            ),
        )
        st.balloons()
        st.success("✅ Application submitted successfully!")
        st.markdown(f"### Your tracking ID: `{tracking}`")
        st.warning("Save this ID. You need it together with your phone number to check your status.")


def page_track():
    title("🔎 Track Your Application", "Enter your tracking ID and the phone number used in the application.")
    with st.form("track"):
        tid = st.text_input("Tracking ID (e.g. APP-1A2B3C4D)")
        phone = st.text_input("Phone number used in the application")
        go = st.form_submit_button("Check status")
    if go:
        app = one(
            "SELECT * FROM applications WHERE tracking_id=? AND phone=?",
            (tid.strip().upper(), phone.strip()),
        )
        if not app:
            st.error("No application found. Check the tracking ID and phone number.")
            return
        st.markdown(
            f"""<div class="card">
            <div style="margin-bottom:10px">{badge(app['status'])}</div>
            <h4>{app['student_name']}</h4>
            <p><b>Class:</b> {app['applying_class']} &nbsp;|&nbsp; <b>Submitted:</b> {app['created_at']}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        if app["remarks"]:
            st.info(f"Remarks from school: {app['remarks']}")


def page_login():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(
            f'<div class="login-wrap"><div class="big">{logo_html(130) if logo_data_uri() else "🔐"}</div>'
            '<div class="section-title" style="border:none;padding:0">Welcome back</div>'
            '<div class="page-sub">Login to your school account</div></div>',
            unsafe_allow_html=True,
        )
        with st.form("login"):
            u = st.text_input("Username", placeholder="Enter username")
            p = st.text_input("Password", type="password", placeholder="Enter password")
            ok = st.form_submit_button("Login")
        st.caption("Students and teachers: use the login details given by the school office. Parents: use Register to create an account.")
        if ok:
            user = authenticate(u, p)
            if user:
                st.session_state["user"] = {
                    k: user[k] for k in ("id", "username", "role", "full_name", "ref_id")
                }
                st.rerun()
            else:
                st.error("Wrong username or password.")


def page_register():
    title("🧾 Create Account")
    st.caption(
        "Register to submit and track admission applications. "
        "Student and teacher accounts are created by the school office."
    )
    with st.form("register"):
        name = st.text_input("Full name *")
        username = st.text_input("Choose a username *")
        p1 = st.text_input("Password (min 6 characters) *", type="password")
        p2 = st.text_input("Confirm password *", type="password")
        ok = st.form_submit_button("Register")
    if ok:
        if not need(name, username, p1, p2):
            st.error("Please fill all fields.")
        elif len(username.strip()) < 4 or " " in username.strip():
            st.error("Username must be at least 4 characters with no spaces.")
        elif len(p1) < 6:
            st.error("Password must be at least 6 characters.")
        elif p1 != p2:
            st.error("Passwords do not match.")
        elif username_taken(username):
            st.error("This username is already taken.")
        else:
            create_user(username, p1, "applicant", name.strip())
            st.success("Account created! Go to Login from the menu.")


def page_assistant():
    title("🤖 School AI Assistant")
    st.caption("Ask about admissions, classes and general school information. Urdu, Pashto and English are supported.")
    key = secret("GROQ_API_KEY")
    if not key:
        st.warning("The AI assistant is not configured yet. Add GROQ_API_KEY to the app secrets.")
        return

    try:
        from groq import Groq
    except ImportError:
        st.error("The 'groq' package is missing. Add it to requirements.txt.")
        return

    system_prompt = f"""You are the friendly assistant of {SCHOOL_NAME}, located at {SCHOOL_ADDRESS}.
The school teaches from Nursery to Class 10 (High School) and 11-12 (Higher Secondary).
Admissions: parents apply through the 'Apply Online' page, then track the status with the
tracking ID in 'Track Application'. Contact: phone {SCHOOL_PHONE}, email {SCHOOL_EMAIL},
office hours {OFFICE_HOURS}.
Rules: answer briefly and politely in the same language the user writes in. Do NOT invent
fees, dates, results or policies; if you do not know, ask the user to contact the school office.
Help with general study tips and school-related questions only."""

    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    for m in st.session_state["chat"]:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    prompt = st.chat_input("Type your question...")
    if prompt:
        st.session_state["chat"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=key)
                resp = client.chat.completions.create(
                    model=secret("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    messages=[{"role": "system", "content": system_prompt}]
                    + st.session_state["chat"][-10:],
                    temperature=0.3,
                    max_tokens=500,
                )
                answer = resp.choices[0].message.content
            except Exception as e:
                answer = f"Sorry, the assistant is unavailable right now. ({type(e).__name__})"
            st.write(answer)
        st.session_state["chat"].append({"role": "assistant", "content": answer})


# ----------------------------------------------------------------------------
# COMMON LOGGED-IN PAGES
# ----------------------------------------------------------------------------
def page_password():
    title("🔑 Change Password")
    user = st.session_state["user"]
    with st.form("pw"):
        old = st.text_input("Current password", type="password")
        new = st.text_input("New password (min 6 characters)", type="password")
        conf = st.text_input("Confirm new password", type="password")
        ok = st.form_submit_button("Update password")
    if ok:
        if not authenticate(user["username"], old):
            st.error("Current password is wrong.")
        elif len(new) < 6:
            st.error("New password must be at least 6 characters.")
        elif new != conf:
            st.error("Passwords do not match.")
        else:
            h, s = hash_pw(new)
            execute("UPDATE users SET password_hash=?, salt=? WHERE id=?", (h, s, user["id"]))
            st.success("Password updated.")


def my_attendance(kind):
    user = st.session_state["user"]
    title("📅 My Attendance")
    if not user.get("ref_id"):
        st.info("No attendance record is linked to this account.")
        return
    table, fk = (
        ("student_attendance", "student_id") if kind == "student" else ("teacher_attendance", "teacher_id")
    )
    df = frame(
        f"SELECT att_date AS Date, status AS Status FROM {table} WHERE {fk}=? ORDER BY att_date DESC",
        (user["ref_id"],),
    )
    if df.empty:
        st.info("No attendance has been recorded yet.")
        return
    total = len(df)
    counts = df["Status"].value_counts()
    present = int(counts.get("Present", 0))
    late = int(counts.get("Late", 0))
    c = st.columns(5)
    c[0].metric("Days recorded", total)
    c[1].metric("Present", present)
    c[2].metric("Absent", int(counts.get("Absent", 0)))
    c[3].metric("Late", late)
    c[4].metric("Attendance %", f"{round((present + late) / total * 100, 1)}%")
    st.dataframe(df, hide_index=True)


# ----------------------------------------------------------------------------
# APPLICANT
# ----------------------------------------------------------------------------
def my_applications():
    title("📄 My Applications")
    user = st.session_state["user"]
    df = frame(
        """SELECT tracking_id AS "Tracking ID", student_name AS Student,
           applying_class AS Class, status AS Status, remarks AS Remarks,
           created_at AS Submitted
           FROM applications WHERE applicant_user_id=? ORDER BY id DESC""",
        (user["id"],),
    )
    if df.empty:
        st.info("You have not submitted any application yet. Use 'Apply Online'.")
    else:
        st.dataframe(df, hide_index=True)


# ----------------------------------------------------------------------------
# ADMIN PAGES
# ----------------------------------------------------------------------------
def admin_dashboard():
    title("📊 Admin Dashboard", f"Overview for {date.today().strftime('%A, %d %B %Y')}")
    today = date.today().isoformat()
    ns = one("SELECT COUNT(*) AS n FROM students")["n"]
    nt = one("SELECT COUNT(*) AS n FROM teachers")["n"]
    npend = one(
        "SELECT COUNT(*) AS n FROM applications WHERE status IN ('Pending','Under Review')"
    )["n"]
    sp = one(
        "SELECT COUNT(*) AS n FROM student_attendance WHERE att_date=? AND status IN ('Present','Late')",
        (today,),
    )["n"]
    sm = one("SELECT COUNT(*) AS n FROM student_attendance WHERE att_date=?", (today,))["n"]
    tp = one(
        "SELECT COUNT(*) AS n FROM teacher_attendance WHERE att_date=? AND status IN ('Present','Late')",
        (today,),
    )["n"]
    tm = one("SELECT COUNT(*) AS n FROM teacher_attendance WHERE att_date=?", (today,))["n"]

    c = st.columns(5)
    stat_card(c[0], ns, "Students", "s1")
    stat_card(c[1], nt, "Teachers", "s2")
    stat_card(c[2], npend, "Open applications", "s3")
    stat_card(c[3], f"{sp}/{sm}", "Students present today", "s4")
    stat_card(c[4], f"{tp}/{tm}", "Teachers present today", "s5")
    st.write("")

    left, right = st.columns(2)
    with left:
        title("Applications by status")
        df = frame("SELECT status, COUNT(*) AS count FROM applications GROUP BY status")
        if df.empty:
            st.info("No applications yet.")
        else:
            st.bar_chart(df.set_index("status"))
    with right:
        title("Students per class")
        dfc = frame("SELECT class_name AS class, COUNT(*) AS students FROM students GROUP BY class_name")
        if dfc.empty:
            st.info("No students yet.")
        else:
            dfc["class"] = pd.Categorical(dfc["class"], categories=CLASSES, ordered=True)
            st.bar_chart(dfc.sort_values("class").set_index("class"))

    title("💾 Backup")
    st.caption("Download a backup regularly. On free hosting, the local database can be reset when the app restarts.")
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            st.download_button(
                "⬇️ Download database backup", f.read(), f"school_backup_{today}.db"
            )


def admit_application(app):
    roll = next_roll()
    sid = execute(
        "INSERT INTO students(roll_no,name,father_name,class_name,phone,address) VALUES(?,?,?,?,?,?)",
        (roll, app["student_name"], app["father_name"], app["applying_class"], app["phone"], app["address"]),
    )
    username = roll.lower().replace("-", "")
    password = gen_password()
    create_user(username, password, "student", app["student_name"], sid)
    execute("UPDATE applications SET status='Admitted' WHERE id=?", (app["id"],))
    return roll, username, password


def admin_applications():
    title("📥 Admission Applications")
    df = frame("SELECT * FROM applications ORDER BY id DESC")
    if df.empty:
        st.info("No applications yet.")
        return
    status_f = st.multiselect("Filter by status", APP_STATUS, default=["Pending", "Under Review", "Approved"])
    view = df[df["status"].isin(status_f)] if status_f else df
    cols = ["tracking_id", "student_name", "father_name", "applying_class", "phone", "status", "created_at"]
    st.dataframe(view[cols], hide_index=True)
    st.download_button("⬇️ Download all as CSV", df.to_csv(index=False).encode(), "applications.csv", "text/csv")
    if view.empty:
        return

    opts = {
        f"{r.tracking_id} - {r.student_name} (Class {r.applying_class})": int(r.id)
        for r in view.itertuples()
    }
    sel = st.selectbox("Select an application", list(opts))
    app = one("SELECT * FROM applications WHERE id=?", (opts[sel],))

    st.markdown(
        f"""**Student:** {app['student_name']}  \n**Father:** {app['father_name']}  \n
**DOB:** {app['dob']}  |  **Gender:** {app['gender']}  \n
**Class:** {app['applying_class']}  |  **Previous school:** {app['previous_school'] or '-'}  \n
**Phone:** {app['phone']}  |  **B-Form/CNIC:** {app['id_number'] or '-'}  \n
**Address:** {app['address']}  \n**Current status:** {app['status']}"""
    )

    with st.form("update_app"):
        status = st.selectbox("Status", APP_STATUS, index=APP_STATUS.index(app["status"]))
        remarks = st.text_area("Remarks (visible to applicant)", value=app["remarks"] or "")
        if st.form_submit_button("Update application"):
            execute("UPDATE applications SET status=?, remarks=? WHERE id=?", (status, remarks, app["id"]))
            flash("Application updated.")

    if app["status"] == "Approved":
        if st.button("🎓 Admit as student and create login"):
            roll, username, password = admit_application(app)
            st.success("Student admitted!")
            st.code(f"Roll No: {roll}\nUsername: {username}\nPassword: {password}")
            st.warning("Copy these login details now. The password is not shown again.")


def admin_add_student():
    title("➕ Add Student")
    with st.form("add_student", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Student name *")
        father = c2.text_input("Father name")
        cls = c1.selectbox("Class *", CLASSES)
        roll = c2.text_input("Roll number (leave blank to auto-generate)")
        phone = c1.text_input("Phone")
        username = c2.text_input("Login username (leave blank to auto-generate)")
        password = c1.text_input("Login password (leave blank to auto-generate)")
        address = st.text_area("Address")
        ok = st.form_submit_button("Add student")
    if ok:
        if not need(name):
            st.error("Student name is required.")
            return
        roll = roll.strip() or next_roll()
        username = (username.strip() or roll.lower().replace("-", "")).lower()
        password = password or gen_password()
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return
        if username_taken(username):
            st.error("This username already exists.")
            return
        try:
            sid = execute(
                "INSERT INTO students(roll_no,name,father_name,class_name,phone,address) VALUES(?,?,?,?,?,?)",
                (roll, name.strip(), father.strip(), cls, phone.strip(), address.strip()),
            )
        except sqlite3.IntegrityError:
            st.error("This roll number already exists.")
            return
        create_user(username, password, "student", name.strip(), sid)
        st.success("Student added.")
        st.code(f"Roll No: {roll}\nUsername: {username}\nPassword: {password}")
        st.warning("Copy these login details now. The password is not shown again.")


def admin_add_teacher():
    title("➕ Add Teacher")
    with st.form("add_teacher", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Teacher name *")
        subject = c2.text_input("Subject")
        qual = c1.text_input("Qualification")
        phone = c2.text_input("Phone")
        username = c1.text_input("Login username (leave blank to auto-generate)")
        password = c2.text_input("Login password (leave blank to auto-generate)")
        ok = st.form_submit_button("Add teacher")
    if ok:
        if not need(name):
            st.error("Teacher name is required.")
            return
        password = password or gen_password()
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return
        if username.strip() and username_taken(username):
            st.error("This username already exists.")
            return
        tid = execute(
            "INSERT INTO teachers(name,subject,qualification,phone) VALUES(?,?,?,?)",
            (name.strip(), subject.strip(), qual.strip(), phone.strip()),
        )
        username = (username.strip() or f"teacher{tid}").lower()
        if username_taken(username):
            username = f"teacher{tid}{gen_password(3).lower()}"
        create_user(username, password, "teacher", name.strip(), tid)
        st.success("Teacher added.")
        st.code(f"Username: {username}\nPassword: {password}")
        st.warning("Copy these login details now. The password is not shown again.")


def people_page(kind):
    table = "students" if kind == "student" else "teachers"
    title("🎓 Students" if kind == "student" else "👩‍🏫 Teachers")
    df = frame(f"SELECT * FROM {table} ORDER BY id DESC")
    if df.empty:
        st.info("No records yet.")
        return
    search = st.text_input("Search")
    if search:
        mask = df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        df = df[mask]
    st.dataframe(df, hide_index=True)
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(), f"{table}.csv", "text/csv")
    if df.empty:
        return

    options = {f"{r.name} (#{r.id})": int(r.id) for r in df.itertuples()}
    sel = st.selectbox("Select a person to manage", list(options), key=f"sel_{kind}")
    pid = options[sel]
    acc = one("SELECT id, username FROM users WHERE role=? AND ref_id=?", (kind, pid))

    with st.expander("🔑 Reset login password"):
        if acc:
            st.write(f"Username: `{acc['username']}`")
            newpw = st.text_input("New password (blank = auto-generate)", key=f"npw_{kind}")
            if st.button("Reset password", key=f"rst_{kind}"):
                pw = newpw or gen_password()
                if len(pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    h, s = hash_pw(pw)
                    execute("UPDATE users SET password_hash=?, salt=? WHERE id=?", (h, s, acc["id"]))
                    st.success("Password reset.")
                    st.code(f"Username: {acc['username']}\nPassword: {pw}")
        else:
            st.info("This person has no login account.")

    with st.expander("🗑️ Delete"):
        st.warning("This permanently deletes the record, login account and all attendance.")
        confirm = st.checkbox("Yes, delete permanently", key=f"conf_{kind}")
        if st.button("Delete", key=f"del_{kind}") and confirm:
            execute("DELETE FROM users WHERE role=? AND ref_id=?", (kind, pid))
            execute(f"DELETE FROM {table} WHERE id=?", (pid,))
            flash("Record deleted.")


# ----------------------------------------------------------------------------
# ATTENDANCE
# ----------------------------------------------------------------------------
def attendance_page(kind):
    is_student = kind == "student"
    user = st.session_state["user"]
    title(
        "🧑‍🎓 Student Attendance" if is_student else "👩‍🏫 Teacher Attendance",
        "Pick the date, set each status, then press Save.",
    )

    c1, c2 = st.columns(2)
    d = c2.date_input("Date", value=date.today(), max_value=date.today(), key=f"date_{kind}")

    if is_student:
        cls = c1.selectbox("Class", CLASSES, key="att_class")
        people = frame(
            'SELECT id AS ID, roll_no AS "Roll No", name AS Name FROM students WHERE class_name=? ORDER BY roll_no',
            (cls,),
        )
        table, fk, sig = "student_attendance", "student_id", f"{cls}_{d}"
    else:
        people = frame("SELECT id AS ID, subject AS Subject, name AS Name FROM teachers ORDER BY name")
        table, fk, sig = "teacher_attendance", "teacher_id", f"t_{d}"

    if people.empty:
        st.info("No records found.")
        return

    existing = frame(f"SELECT {fk} AS pid, status FROM {table} WHERE att_date=?", (d.isoformat(),))
    emap = dict(zip(existing["pid"], existing["status"]))

    fkey = f"force_{kind}_{sig}"
    vkey = f"ver_{kind}_{sig}"
    forced = st.session_state.get(fkey)
    ver = st.session_state.get(vkey, 0)
    people["Status"] = people["ID"].map(lambda i: forced or emap.get(i, "Present"))

    if emap:
        st.caption("Attendance is already saved for this date. Saving will update it.")

    b1, b2, _ = st.columns([1, 1, 4])
    if b1.button("✅ All present", key=f"allp_{kind}"):
        st.session_state[fkey] = "Present"
        st.session_state[vkey] = ver + 1
        st.rerun()
    if b2.button("❌ All absent", key=f"alla_{kind}"):
        st.session_state[fkey] = "Absent"
        st.session_state[vkey] = ver + 1
        st.rerun()

    edited = st.data_editor(
        people,
        key=f"edit_{kind}_{sig}_{ver}",
        hide_index=True,
        disabled=[c for c in people.columns if c != "Status"],
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=ATT_STATUS, required=True)
        },
    )

    counts = edited["Status"].value_counts()
    m = st.columns(4)
    for col, s in zip(m, ATT_STATUS):
        col.metric(s, int(counts.get(s, 0)))

    if st.button("💾 Save attendance", key=f"save_{kind}", type="primary"):
        st.session_state.pop(fkey, None)
        rows = [
            (int(r["ID"]), d.isoformat(), r["Status"], user["username"])
            for _, r in edited.iterrows()
        ]
        bulk(
            f"""INSERT INTO {table}({fk}, att_date, status, marked_by) VALUES(?,?,?,?)
                ON CONFLICT({fk}, att_date)
                DO UPDATE SET status=excluded.status, marked_by=excluded.marked_by""",
            rows,
        )
        st.success(f"Attendance saved for {d.strftime('%d %b %Y')} ({len(rows)} records).")


def reports_page():
    title("📈 Attendance Reports")
    kind = st.radio("Report for", ["Students", "Teachers"], horizontal=True)
    c1, c2, c3 = st.columns(3)
    start = c1.date_input("From", value=date.today() - timedelta(days=30))
    end = c2.date_input("To", value=date.today())

    if kind == "Students":
        cls = c3.selectbox("Class", ["All"] + CLASSES)
        sql = """SELECT s.roll_no AS Roll, s.name AS Name, s.class_name AS Class,
                 a.att_date AS Date, a.status AS Status
                 FROM student_attendance a JOIN students s ON s.id = a.student_id
                 WHERE a.att_date BETWEEN ? AND ?"""
        params = [start.isoformat(), end.isoformat()]
        if cls != "All":
            sql += " AND s.class_name = ?"
            params.append(cls)
        index_cols = ["Roll", "Name", "Class"]
    else:
        sql = """SELECT t.name AS Name, t.subject AS Subject,
                 a.att_date AS Date, a.status AS Status
                 FROM teacher_attendance a JOIN teachers t ON t.id = a.teacher_id
                 WHERE a.att_date BETWEEN ? AND ?"""
        params = [start.isoformat(), end.isoformat()]
        index_cols = ["Name", "Subject"]

    df = frame(sql, tuple(params))
    if df.empty:
        st.info("No attendance data in this range.")
        return

    df["Subject"] = df["Subject"].fillna("") if "Subject" in df else ""
    summary = df.pivot_table(
        index=index_cols, columns="Status", values="Date", aggfunc="count", fill_value=0
    ).reset_index()
    for s in ATT_STATUS:
        if s not in summary.columns:
            summary[s] = 0
    summary["Total"] = summary[ATT_STATUS].sum(axis=1)
    summary["Attendance %"] = ((summary["Present"] + summary["Late"]) / summary["Total"] * 100).round(1)
    summary = summary[index_cols + ATT_STATUS + ["Total", "Attendance %"]]

    st.subheader("Summary")
    st.dataframe(summary, hide_index=True)
    st.download_button("⬇️ Download summary CSV", summary.to_csv(index=False).encode(), "attendance_summary.csv", "text/csv")
    with st.expander("Detailed records"):
        st.dataframe(df.sort_values("Date", ascending=False), hide_index=True)


# ----------------------------------------------------------------------------
# TEACHER
# ----------------------------------------------------------------------------
def teacher_students():
    title("🧑‍🎓 My Students")
    cls = st.selectbox("Class", CLASSES)
    df = frame(
        'SELECT roll_no AS "Roll No", name AS Name, father_name AS "Father Name", phone AS Phone FROM students WHERE class_name=? ORDER BY roll_no',
        (cls,),
    )
    if df.empty:
        st.info("No students in this class.")
    else:
        st.dataframe(df, hide_index=True)


# ----------------------------------------------------------------------------
# NAVIGATION
# ----------------------------------------------------------------------------
def menu_for(user):
    home = ("🏠 Home", page_home)
    ai = ("🤖 AI Assistant", page_assistant)
    pw = ("🔑 Change Password", page_password)

    if not user:
        items = [
            home,
            ("📝 Apply Online", page_apply),
            ("🔎 Track Application", page_track),
            ai,
            ("🔐 Login", page_login),
            ("🧾 Register", page_register),
        ]
    elif user["role"] == "admin":
        items = [
            ("📊 Dashboard", admin_dashboard),
            ("📥 Applications", admin_applications),
            ("➕ Add Student", admin_add_student),
            ("➕ Add Teacher", admin_add_teacher),
            ("🎓 Students", lambda: people_page("student")),
            ("👩‍🏫 Teachers", lambda: people_page("teacher")),
            ("🧑‍🎓 Student Attendance", lambda: attendance_page("student")),
            ("👩‍🏫 Teacher Attendance", lambda: attendance_page("teacher")),
            ("📈 Reports", reports_page),
            ai,
            pw,
        ]
    elif user["role"] == "teacher":
        items = [
            home,
            ("🧑‍🎓 Mark Student Attendance", lambda: attendance_page("student")),
            ("🧑‍🎓 My Students", teacher_students),
            ("📅 My Attendance", lambda: my_attendance("teacher")),
            ai,
            pw,
        ]
    elif user["role"] == "student":
        items = [home, ("📅 My Attendance", lambda: my_attendance("student")), ai, pw]
    else:  # applicant
        items = [
            home,
            ("📝 Apply Online", page_apply),
            ("📄 My Applications", my_applications),
            ai,
            pw,
        ]
    return dict(items)


def main():
    setup()
    user = st.session_state.get("user")

    st.markdown(
        f"""<div class="school-banner"><div class="logo">{logo_html(96)}</div>
        <div><h2>{SCHOOL_NAME}</h2><p>📍 {SCHOOL_ADDRESS}</p></div></div>""",
        unsafe_allow_html=True,
    )

    pages = menu_for(user)
    with st.sidebar:
        st.markdown(
            f'<div class="side-brand"><div class="logo">{logo_html(110)}</div><div class="name">{SCHOOL_SHORT}</div></div>',
            unsafe_allow_html=True,
        )
        if user:
            st.markdown(
                f'<div class="user-chip"><b>👤 {user["full_name"]}</b>{user["role"].title()}</div>',
                unsafe_allow_html=True,
            )
        choice = st.radio("Menu", list(pages.keys()), label_visibility="collapsed")
        if user and st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

    msg = st.session_state.pop("flash", None)
    if msg:
        st.success(msg)

    pages[choice]()


main()
