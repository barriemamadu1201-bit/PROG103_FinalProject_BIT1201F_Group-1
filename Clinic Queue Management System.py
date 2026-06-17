import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import csv
import os
import threading

# Optional pyttsx3 (Text-to-Speech)
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None  # type: ignore[assignment]
    TTS_AVAILABLE = False

# ReportLab for PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    A4 = None  # type: ignore[assignment]
    rl_canvas = None  # type: ignore[assignment]
    colors = None  # type: ignore[assignment]
    SimpleDocTemplate = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    TableStyle = None  # type: ignore[assignment]
    Paragraph = None  # type: ignore[assignment]
    Spacer = None  # type: ignore[assignment]
    getSampleStyleSheet = None  # type: ignore[assignment]
    REPORTLAB_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════
#  GLOBAL DATA STORAGE
# ═══════════════════════════════════════════════════════════════

# ── User Accounts ──────────────────────────────────────────────
USERS = {
    "admin":     {"password": "admin123",     "role": "Administrator", "name": "Admin User"},
    "reception": {"password": "reception123", "role": "Receptionist",  "name": "Mary Kamara"},  # spellchecker: disable-line
    "doctor":    {"password": "doctor123",    "role": "Doctor",        "name": "Dr. Sesay"},  # spellchecker: disable-line
}

# ── Session State ──────────────────────────────────────────────
current_user: dict = {"username": None, "role": None, "name": None}
remember_me_user = {"username": "", "password": ""}

# ── Doctors ────────────────────────────────────────────────────
doctors = [
    {"id": "D001", "name": "Dr. Kamara",  "dept": "General Consultation", "status": "Available", "patients_served": 0},  # spellchecker: disable-line
    {"id": "D002", "name": "Dr. Bangura", "dept": "Pediatrics",           "status": "Available", "patients_served": 0},  # spellchecker: disable-line
    {"id": "D003", "name": "Dr. Koroma",  "dept": "Maternity",            "status": "Busy",      "patients_served": 2},  # spellchecker: disable-line
    {"id": "D004", "name": "Dr. Sesay",   "dept": "Dental",               "status": "Available", "patients_served": 0},  # spellchecker: disable-line
    {"id": "D005", "name": "Dr. Turay",   "dept": "Laboratory",           "status": "Offline",   "patients_served": 4},  # spellchecker: disable-line
]

# ── Department Queue Counters ──────────────────────────────────
dept_counters = {
    "General Consultation": 0,
    "Pediatrics":           0,
    "Maternity":            0,
    "Laboratory":           0,
    "Dental":               0,
    "Pharmacy":             0,
}

dept_prefix = {
    "General Consultation": "G",
    "Pediatrics":           "P",
    "Maternity":            "M",
    "Laboratory":           "L",
    "Dental":               "D",
    "Pharmacy":             "PH",
}

# ── Patient Queue ──────────────────────────────────────────────
patients = []          # list of dicts
patient_id_counter = [1]

# ── Audit Log ─────────────────────────────────────────────────
audit_logs = []

# ── Voice Settings ────────────────────────────────────────────
voice_settings = {
    "enabled": True,
    "volume":  0.9,
    "rate":    150,
    "history": [],
}

# ── Clinic Settings ───────────────────────────────────────────
clinic_settings = {
    "name":          "City Health Clinic",
    "max_daily":     200,
    "open_time":     "08:00",
    "close_time":    "17:00",
    "font_size":     12,
    "high_contrast": False,
}

# ── Theme ─────────────────────────────────────────────────────
dark_mode = [False]

LIGHT = {
    "bg":         "#F0F4F8",
    "card":       "#FFFFFF",
    "sidebar":    "#1A3C6B",
    "sidebar_fg": "#FFFFFF",
    "accent":     "#0D7377",
    "accent2":    "#14BDAC",  # spellchecker: disable-line
    "text":       "#1A202C",
    "text_muted": "#718096",
    "border":     "#E2E8F0",
    "success":    "#38A169",
    "warning":    "#D69E2E",
    "error":      "#E53E3E",
    "info":       "#3182CE",
    "btn_fg":     "#FFFFFF",
    "entry_bg":   "#FFFFFF",
    "entry_fg":   "#1A202C",
    "tree_bg":    "#FFFFFF",
    "tree_fg":    "#1A202C",
    "tree_sel":   "#BEE3F8",
    "header_bg":  "#EBF8FF",
}

DARK = {
    "bg":         "#1A202C",
    "card":       "#2D3748",
    "sidebar":    "#0F1923",
    "sidebar_fg": "#E2E8F0",
    "accent":     "#14BDAC",  # spellchecker: disable-line
    "accent2":    "#0D7377",
    "text":       "#F7FAFC",  # spellchecker: disable-line
    "text_muted": "#A0AEC0",
    "border":     "#4A5568",
    "success":    "#48BB78",
    "warning":    "#ECC94B",
    "error":      "#FC8181",
    "info":       "#63B3ED",
    "btn_fg":     "#FFFFFF",
    "entry_bg":   "#4A5568",
    "entry_fg":   "#F7FAFC",  # spellchecker: disable-line
    "tree_bg":    "#2D3748",
    "tree_fg":    "#F7FAFC",  # spellchecker: disable-line
    "tree_sel":   "#2B6CB0",
    "header_bg":  "#2A4365",
}

def theme():
    """Return current theme dict."""
    return DARK if dark_mode[0] else LIGHT

def speak(text):
    """Speak text in background thread."""
    if not voice_settings["enabled"] or not TTS_AVAILABLE:
        return
    voice_settings["history"].append({"time": now_str(), "text": text})
    def _run():
        try:
            eng = pyttsx3.init()
            eng.setProperty("volume", voice_settings["volume"])
            eng.setProperty("rate",   voice_settings["rate"])
            eng.say(text)
            eng.runAndWait()
        except (RuntimeError, OSError):  # pyttsx3 driver errors are non-critical
            pass
    threading.Thread(target=_run, daemon=True).start()

# ── Helpers ───────────────────────────────────────────────────
def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def time_str():
    return datetime.datetime.now().strftime("%H:%M:%S")

def add_audit(action, detail=""):
    audit_logs.append({
        "time":   now_str(),
        "user":   current_user["username"] or "system",
        "role":   current_user["role"]     or "—",
        "action": action,
        "detail": detail,
    })

def get_next_queue_number(dept):
    dept_counters[dept] += 1
    prefix = dept_prefix.get(dept, "X")
    return f"{prefix}{dept_counters[dept]:03d}"

def get_available_doctor(dept):
    for d in doctors:
        if d["dept"] == dept and d["status"] == "Available":
            return d["name"]
    for d in doctors:
        if d["status"] == "Available":
            return d["name"]
    return "Unassigned"

def today_patients():
    today = today_str()
    return [p for p in patients if p["date"] == today]

def priority_sort_key(p):
    order = {"Emergency": 0, "Elderly": 1, "Normal": 2}
    return order.get(p["priority"], 3), p["arrival_time"]

# ═══════════════════════════════════════════════════════════════
#  MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════

root = tk.Tk()
root.withdraw()
root.title(f"{clinic_settings['name']} — Queue Management System")
root.minsize(1200, 800)
root.geometry("1400x900")

# Widget reference dicts (used for theme reloading via build_main_layout)
_frames  = {}
_labels  = {}

# Current page frame
current_frame = [None]  # type: list
sidebar_buttons = []
btn_pages = {}          # maps sidebar button widget → page name
active_nav_buttons = set()  # tracks which nav button is currently active

# ═══════════════════════════════════════════════════════════════
#  SPLASH / LOADING SCREEN
# ═══════════════════════════════════════════════════════════════

def show_splash():
    splash = tk.Toplevel()
    splash.overrideredirect(True)
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    w, h = 520, 340
    splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    splash.configure(bg="#1A3C6B")

    tk.Label(splash, text="🏥", font=("Segoe UI", 48), bg="#1A3C6B", fg="#14BDAC").pack(pady=(40,8))  # spellchecker: disable-line
    tk.Label(splash, text=clinic_settings["name"], font=("Segoe UI", 22, "bold"),
             bg="#1A3C6B", fg="white").pack()
    tk.Label(splash, text="Queue Management System", font=("Segoe UI", 13),
             bg="#1A3C6B", fg="#A0C4FF").pack(pady=(4,20))

    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(splash, variable=progress_var, maximum=100,
                                length=380, mode="determinate")
    progress.pack()
    status_lbl = tk.Label(splash, text="Initializing...", font=("Segoe UI", 10),
                          bg="#1A3C6B", fg="#A0C4FF")
    status_lbl.pack(pady=8)

    steps = [
        (20,  "Loading modules..."),
        (45,  "Setting up interface..."),
        (70,  "Configuring voice engine..."),
        (90,  "Preparing dashboard..."),
        (100, "Ready!"),
    ]

    def animate(i=0):
        if i < len(steps):
            val, msg = steps[i]
            progress_var.set(val)
            status_lbl.config(text=msg)
            splash.after(350, animate, i + 1)
        else:
            splash.after(300, _finish_splash, splash)

    def _finish_splash(s):
        s.destroy()
        show_login()

    splash.after(200, animate, 0)
    root.wait_window(splash)


# ═══════════════════════════════════════════════════════════════
#  LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════

login_win: list = [None]

def show_login():
    global login_win
    root.withdraw()

    lw = tk.Toplevel()
    lw.title("Login — " + clinic_settings["name"])
    lw.geometry("460x580")
    lw.resizable(True, True)
    lw.minsize(380, 500)
    lw.maxsize(700, 900)
    lw.configure(bg=theme()["bg"])
    login_win[0] = lw

    sw = lw.winfo_screenwidth()
    sh = lw.winfo_screenheight()
    lw.geometry(f"460x580+{(sw-460)//2}+{(sh-580)//2}")

    # Header
    header = tk.Frame(lw, bg="#1A3C6B", height=140)
    header.pack(fill="x")
    tk.Label(header, text="🏥", font=("Segoe UI", 36), bg="#1A3C6B", fg="#14BDAC").pack(pady=(18,4))  # spellchecker: disable-line
    tk.Label(header, text=clinic_settings["name"], font=("Segoe UI", 16, "bold"),
             bg="#1A3C6B", fg="white").pack()
    tk.Label(header, text="Queue Management System", font=("Segoe UI", 10),
             bg="#1A3C6B", fg="#A0C4FF").pack(pady=(2,14))

    body = tk.Frame(lw, bg=theme()["bg"], padx=40)
    body.pack(fill="both", expand=True)

    tk.Label(body, text="Sign In to Continue", font=("Segoe UI", 14, "bold"),
             bg=theme()["bg"], fg=theme()["text"]).pack(pady=(24,4))
    tk.Label(body, text="Enter your credentials below", font=("Segoe UI", 10),
             bg=theme()["bg"], fg=theme()["text_muted"]).pack(pady=(0,20))

    # Username
    tk.Label(body, text="Username", font=("Segoe UI", 10, "bold"),
             bg=theme()["bg"], fg=theme()["text"], anchor="w").pack(fill="x")
    user_var = tk.StringVar(value=remember_me_user["username"])
    user_entry = tk.Entry(body, textvariable=user_var, font=("Segoe UI", 12),
                          bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                          relief="flat", bd=0, highlightthickness=2,
                          highlightbackground=theme()["border"],
                          highlightcolor=theme()["accent"])
    user_entry.pack(fill="x", ipady=8, pady=(4,14))

    # Password
    tk.Label(body, text="Password", font=("Segoe UI", 10, "bold"),
             bg=theme()["bg"], fg=theme()["text"], anchor="w").pack(fill="x")
    pass_var = tk.StringVar(value=remember_me_user["password"])
    pass_row = tk.Frame(body, bg=theme()["bg"])
    pass_row.pack(fill="x", pady=(4,4))
    pass_entry = tk.Entry(pass_row, textvariable=pass_var, font=("Segoe UI", 12),
                          show="•", bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                          relief="flat", bd=0, highlightthickness=2,
                          highlightbackground=theme()["border"],
                          highlightcolor=theme()["accent"])
    pass_entry.pack(side="left", fill="x", expand=True, ipady=8)

    def toggle_pass():
        if pass_entry.cget("show") == "•":
            pass_entry.config(show="")
            eye_btn.config(text="🙈")
        else:
            pass_entry.config(show="•")
            eye_btn.config(text="👁")

    eye_btn = tk.Button(pass_row, text="👁", font=("Segoe UI", 12),
                        bg=theme()["entry_bg"], fg=theme()["text_muted"],
                        relief="flat", cursor="hand2", command=toggle_pass)
    eye_btn.pack(side="left", padx=4)

    # Remember Me
    rem_var = tk.BooleanVar()
    rem_row = tk.Frame(body, bg=theme()["bg"])
    rem_row.pack(fill="x", pady=8)
    tk.Checkbutton(rem_row, text="Remember Me", variable=rem_var,
                   bg=theme()["bg"], fg=theme()["text"], activebackground=theme()["bg"],
                   font=("Segoe UI", 10)).pack(side="left")
    tk.Button(rem_row, text="Forgot Password?", font=("Segoe UI", 10),
              bg=theme()["bg"], fg=theme()["accent"], relief="flat", cursor="hand2",
              command=lambda: messagebox.showinfo("Forgot Password",
                  "Please contact the system administrator.\n\nDefault credentials:\n"
                  "Admin: admin / admin123\nReception: reception / reception123\nDoctor: doctor / doctor123")
              ).pack(side="right")

    error_lbl = tk.Label(body, text="", font=("Segoe UI", 10),
                         bg=theme()["bg"], fg=theme()["error"])
    error_lbl.pack()

    def do_login(*_):  # event arg from key binding is ignored
        login_uname = user_var.get().strip()
        pwd         = pass_var.get().strip()
        if not login_uname or not pwd:
            error_lbl.config(text="⚠ Please enter username and password.")
            return
        if login_uname in USERS and USERS[login_uname]["password"] == pwd:
            current_user["username"] = login_uname
            current_user["role"]     = USERS[login_uname]["role"]
            current_user["name"]     = USERS[login_uname]["name"]
            if rem_var.get():
                remember_me_user["username"] = login_uname
                remember_me_user["password"] = pwd
            else:
                remember_me_user["username"] = ""
                remember_me_user["password"] = ""
            add_audit("LOGIN", f"User '{login_uname}' logged in as {current_user['role']}")
            lw.destroy()
            open_main_app()
        else:
            error_lbl.config(text="✗ Invalid username or password.")

    login_btn = tk.Button(body, text="  Sign In  ", font=("Segoe UI", 12, "bold"),
                          bg=theme()["accent"], fg="white", relief="flat",
                          cursor="hand2", pady=10, command=do_login)
    login_btn.pack(fill="x", pady=12)

    # Quick login hints
    hint_frame = tk.Frame(body, bg=theme()["border"], pady=8, padx=10)
    hint_frame.pack(fill="x", pady=(8,0))
    tk.Label(hint_frame, text="Quick Login:", font=("Segoe UI", 9, "bold"),
             bg=theme()["border"], fg=theme()["text"]).pack(anchor="w")
    for uname, info in USERS.items():
        def make_quick(u, p):
            return lambda: (user_var.set(u), pass_var.set(p))
        tk.Button(hint_frame, text=f"{info['role']}: {uname}",
                  font=("Segoe UI", 9), bg=theme()["border"], fg=theme()["accent"],
                  relief="flat", cursor="hand2",
                  command=make_quick(uname, info["password"])
                  ).pack(anchor="w")

    user_entry.bind("<Return>", lambda _e: pass_entry.focus())
    pass_entry.bind("<Return>", do_login)
    user_entry.focus()

    lw.protocol("WM_DELETE_WINDOW", lambda: root.quit())


# ═══════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════

def open_main_app():
    root.deiconify()
    root.state("zoomed") if os.name == "nt" else root.attributes("-zoomed", True)
    build_main_layout()
    setup_shortcuts()
    show_page("dashboard")
    start_clock()


def build_main_layout():
    """Build sidebar + content area."""
    for w in root.winfo_children():
        w.destroy()

    root.configure(bg=theme()["bg"])

    main_container = tk.Frame(root, bg=theme()["bg"])
    main_container.pack(fill="both", expand=True)

    # ── Sidebar ───────────────────────────────────────────────
    sidebar = tk.Frame(main_container, bg=theme()["sidebar"], width=220)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)
    _frames["sidebar"] = sidebar

    # Logo
    logo_frame = tk.Frame(sidebar, bg=theme()["sidebar"], pady=16)
    logo_frame.pack(fill="x")
    tk.Label(logo_frame, text="🏥", font=("Segoe UI", 28), bg=theme()["sidebar"],
             fg=theme()["accent2"]).pack()
    tk.Label(logo_frame, text=clinic_settings["name"], font=("Segoe UI", 11, "bold"),
             bg=theme()["sidebar"], fg="white", wraplength=180).pack()
    tk.Frame(logo_frame, bg=theme()["accent2"], height=2).pack(fill="x", pady=(10,0), padx=20)

    # User info
    user_frame = tk.Frame(sidebar, bg=theme()["sidebar"], pady=10)
    user_frame.pack(fill="x", padx=16)
    tk.Label(user_frame, text=f"👤 {current_user['name'] or ''}",  # type: ignore[str-bytes-safe]
             font=("Segoe UI", 10, "bold"), bg=theme()["sidebar"],
             fg="white", anchor="w").pack(fill="x")
    tk.Label(user_frame, text=str(current_user["role"] or ""),
             font=("Segoe UI", 9), bg=theme()["sidebar"],
             fg=theme()["accent2"], anchor="w").pack(fill="x")
    tk.Frame(sidebar, bg=theme()["border"], height=1).pack(fill="x", padx=16, pady=6)

    # Nav items
    role = current_user["role"]
    nav_items = [("🏠", "Dashboard", "dashboard", True)]
    if role in ("Administrator", "Receptionist"):
        nav_items.append(("📋", "Register Patient", "register", True))
    nav_items += [
        ("📊", "Queue Manager",  "queue",   True),
        ("🔍", "Search",         "search",  True),
        ("🖥",  "Live Monitor",   "monitor", True),
        ("👨‍⚕️", "Doctors",      "doctors", True),
    ]
    if role in ("Administrator", "Receptionist"):
        nav_items.append(("📈", "Reports", "reports", True))
    if role == "Administrator":
        nav_items += [
            ("📝", "Audit Log", "audit",    True),
            ("⚙",  "Settings",  "settings", True),
        ]

    global sidebar_buttons
    global btn_pages
    global active_nav_buttons
    sidebar_buttons = []
    btn_pages = {}  # maps button widget → page name
    active_nav_buttons = set()
    nav_container = tk.Frame(sidebar, bg=theme()["sidebar"])
    nav_container.pack(fill="x")

    def make_nav_cmd(nav_page):
        return lambda: show_page(nav_page)

    for icon, label, page, _ in nav_items:
        btn = tk.Button(
            nav_container, text=f"  {icon}  {label}",
            font=("Segoe UI", 11), bg=theme()["sidebar"], fg=theme()["sidebar_fg"],
            relief="flat", anchor="w", padx=12, pady=10,
            cursor="hand2", activebackground=theme()["accent"],
            activeforeground="white",
            command=make_nav_cmd(page)
        )
        btn.pack(fill="x")
        sidebar_buttons.append(btn)
        btn_pages[btn] = page

        def on_enter(_e, b=btn):
            if b in active_nav_buttons: return
            b.config(bg=theme()["accent2"])
        def on_leave(_e, b=btn):
            if b in active_nav_buttons: return
            b.config(bg=theme()["sidebar"])
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    # Bottom buttons
    bottom = tk.Frame(sidebar, bg=theme()["sidebar"])
    bottom.pack(side="bottom", fill="x", pady=10)

    theme_btn = tk.Button(bottom, text="🌙 Dark Mode" if not dark_mode[0] else "☀ Light Mode",
                          font=("Segoe UI", 10), bg=theme()["sidebar"], fg=theme()["sidebar_fg"],
                          relief="flat", anchor="w", padx=16, pady=8, cursor="hand2",
                          command=toggle_theme)
    theme_btn.pack(fill="x")

    tk.Button(bottom, text="🚪 Logout", font=("Segoe UI", 10),
              bg=theme()["sidebar"], fg=theme()["error"],
              relief="flat", anchor="w", padx=16, pady=8, cursor="hand2",
              command=do_logout).pack(fill="x")

    # ── Content Area ──────────────────────────────────────────
    content_wrap = tk.Frame(main_container, bg=theme()["bg"])
    content_wrap.pack(side="left", fill="both", expand=True)
    _frames["content_wrap"] = content_wrap

    # Top bar
    topbar = tk.Frame(content_wrap, bg=theme()["card"], height=52)
    topbar.pack(fill="x")
    topbar.pack_propagate(False)
    _frames["topbar"] = topbar

    _labels["topbar_title"] = tk.Label(topbar, text="Dashboard",
                                        font=("Segoe UI", 16, "bold"),
                                        bg=theme()["card"], fg=theme()["text"])
    _labels["topbar_title"].pack(side="left", padx=20, pady=14)

    _labels["clock"] = tk.Label(topbar, text="", font=("Segoe UI", 11),
                                 bg=theme()["card"], fg=theme()["text_muted"])
    _labels["clock"].pack(side="right", padx=20)

    # Content canvas
    content_area = tk.Frame(content_wrap, bg=theme()["bg"])
    content_area.pack(fill="both", expand=True)
    _frames["content"] = content_area


def set_active_nav(page):
    for btn in sidebar_buttons:
        if btn_pages.get(btn) == page:
            btn.config(bg=theme()["accent"], fg="white")
            active_nav_buttons.add(btn)
        else:
            btn.config(bg=theme()["sidebar"], fg=theme()["sidebar_fg"])
            active_nav_buttons.discard(btn)


def show_page(page):
    if current_frame[0]:  # type: ignore[index]
        current_frame[0].destroy()  # type: ignore[union-attr]

    set_active_nav(page)
    _labels["topbar_title"].config(text=page.replace("_"," ").title())

    content = _frames["content"]
    frame = tk.Frame(content, bg=theme()["bg"])
    frame.pack(fill="both", expand=True)
    current_frame[0] = frame  # type: ignore[index]

    pages = {
        "dashboard": build_dashboard,
        "register":  build_register,
        "queue":     build_queue,
        "search":    build_search,
        "monitor":   build_monitor,
        "doctors":   build_doctors,
        "reports":   build_reports,
        "audit":     build_audit,
        "settings":  build_settings,
    }
    if page in pages:
        pages[page](frame)


def start_clock():
    def update():
        if "clock" in _labels and _labels["clock"].winfo_exists():
            _labels["clock"].config(
                text=f"📅 {datetime.datetime.now().strftime('%A, %d %B %Y   🕐 %H:%M:%S')}"
            )
        root.after(1000, update)  # type: ignore[arg-type]
    update()


# ═══════════════════════════════════════════════════════════════
#  THEME TOGGLE
# ═══════════════════════════════════════════════════════════════

def toggle_theme():
    dark_mode[0] = not dark_mode[0]
    page = None
    for btn in sidebar_buttons:
        if btn in active_nav_buttons:
            page = btn_pages.get(btn)
            break
    build_main_layout()
    if page:
        show_page(page)


# ═══════════════════════════════════════════════════════════════
#  LOGOUT
# ═══════════════════════════════════════════════════════════════

def do_logout():
    if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
        add_audit("LOGOUT", f"User '{current_user['username']}' logged out")
        current_user["username"] = None
        current_user["role"]     = None
        current_user["name"]     = None
        root.withdraw()
        show_login()


# ═══════════════════════════════════════════════════════════════
#  HELPER UI COMPONENTS
# ═══════════════════════════════════════════════════════════════

def make_card(parent, title="", padx=16, pady=16, width=None):
    outer = tk.Frame(parent, bg=theme()["card"],
                     highlightbackground=theme()["border"], highlightthickness=1)
    if width:
        outer.config(width=width)
    inner = tk.Frame(outer, bg=theme()["card"], padx=padx, pady=pady)
    inner.pack(fill="both", expand=True)
    if title:
        tk.Label(inner, text=title, font=("Segoe UI", 12, "bold"),
                 bg=theme()["card"], fg=theme()["text"]).pack(anchor="w", pady=(0,10))
    return outer, inner


def make_btn(parent, text, command, color=None, width=None, pady=8):
    c = color or theme()["accent"]
    cfg = dict(text=text, font=("Segoe UI", 10, "bold"),
               bg=c, fg="white", relief="flat", cursor="hand2",
               pady=pady, command=command, padx=16)
    if width:
        cfg["width"] = width
    btn = tk.Button(parent, **cfg)
    btn.bind("<Enter>", lambda _e: btn.config(bg=darken(c)))
    btn.bind("<Leave>", lambda _e: btn.config(bg=c))
    return btn


def darken(hex_color):
    """Return slightly darkened hex color."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        r = max(0, r-30); g = max(0, g-30); b = max(0, b-30)
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return hex_color


def stat_card(parent, label, value, color, icon):
    card = tk.Frame(parent, bg=color, padx=16, pady=14,
                    highlightbackground=theme()["border"], highlightthickness=1)
    top = tk.Frame(card, bg=color)
    top.pack(fill="x")
    tk.Label(top, text=icon, font=("Segoe UI", 22), bg=color, fg="white").pack(side="left")
    tk.Label(top, text=str(value), font=("Segoe UI", 28, "bold"),
             bg=color, fg="white").pack(side="right")
    tk.Label(card, text=label, font=("Segoe UI", 10),
             bg=color, fg="#E0E0E0").pack(anchor="w")
    return card


def make_treeview(parent, columns, heights=14):
    tv_style = ttk.Style()
    tv_style.theme_use("clam")
    tv_style.configure("Custom.Treeview",
                    background=theme()["tree_bg"],
                    foreground=theme()["tree_fg"],
                    fieldbackground=theme()["tree_bg"],
                    rowheight=30,
                    font=("Segoe UI", 10))
    tv_style.configure("Custom.Treeview.Heading",
                    background=theme()["header_bg"],
                    foreground=theme()["text"],
                    font=("Segoe UI", 10, "bold"),
                    relief="flat")
    tv_style.map("Custom.Treeview",
              background=[("selected", theme()["tree_sel"])],
              foreground=[("selected", theme()["text"])])

    frame = tk.Frame(parent, bg=theme()["bg"])
    tree = ttk.Treeview(frame, columns=columns, show="headings",
                         style="Custom.Treeview", height=heights)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    return frame, tree


def show_notification(type_, title, msg):
    fns = {
        "success": messagebox.showinfo,
        "warning": messagebox.showwarning,
        "error":   messagebox.showerror,
        "info":    messagebox.showinfo,
    }
    fns.get(type_, messagebox.showinfo)(title, msg)


# ═══════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════

def build_dashboard(parent):
    canvas_frame = tk.Frame(parent, bg=theme()["bg"])
    canvas_frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(canvas_frame, bg=theme()["bg"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = tk.Frame(canvas, bg=theme()["bg"], padx=24, pady=20)
    canvas_win = canvas.create_window((0, 0), window=inner, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_win, width=event.width)
    canvas.bind("<Configure>", on_configure)
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

    # ── Title row ─────────────────────────────────────────────
    title_row = tk.Frame(inner, bg=theme()["bg"])
    title_row.pack(fill="x", pady=(0,16))
    tk.Label(title_row, text="📊 Dashboard Overview",
             font=("Segoe UI", 18, "bold"), bg=theme()["bg"], fg=theme()["text"]).pack(side="left")
    # Logout button — prominent, top-right of dashboard
    logout_frame = tk.Frame(title_row, bg=theme()["bg"])
    logout_frame.pack(side="right")
    tk.Label(logout_frame,
             text=f"👤 {current_user['name'] or ''} ({current_user['role'] or ''})",
             font=("Segoe UI", 9), bg=theme()["bg"], fg=theme()["text_muted"]
             ).pack(side="left", padx=(0, 8))
    logout_dash_btn = tk.Button(
        logout_frame, text="🚪 Logout",
        font=("Segoe UI", 10, "bold"),
        bg=theme()["error"], fg="white",
        relief="flat", cursor="hand2",
        padx=14, pady=6,
        command=do_logout
    )
    logout_dash_btn.pack(side="left")
    logout_dash_btn.bind("<Enter>", lambda _e: logout_dash_btn.config(bg=darken(theme()["error"])))
    logout_dash_btn.bind("<Leave>", lambda _e: logout_dash_btn.config(bg=theme()["error"]))
    tk.Label(title_row, text=f"Today: {datetime.datetime.now().strftime('%A, %d %B %Y')}",
             font=("Segoe UI", 11), bg=theme()["bg"], fg=theme()["text_muted"]).pack(side="right", padx=(0,16))

    # ── Stat cards ────────────────────────────────────────────
    tp = today_patients()
    waiting   = [p for p in tp if p["status"] == "Waiting"]
    serving   = [p for p in tp if p["status"] == "Serving"]
    completed = [p for p in tp if p["status"] == "Completed"]
    emergency = [p for p in tp if p["priority"] == "Emergency"]
    avail_doc = sum(1 for d in doctors if d["status"] == "Available")

    # Avg wait time
    avg_wait = 0
    if completed:
        total_wait = 0
        for p in completed:
            try:
                arr = datetime.datetime.strptime(p["arrival_time"], "%H:%M:%S")
                end = datetime.datetime.strptime(p.get("end_time", time_str()), "%H:%M:%S")
                total_wait += max(0, (end - arr).seconds // 60)
            except ValueError:
                pass
        avg_wait = total_wait // len(completed) if completed else 0

    stats = [
        ("Total Patients Today", len(tp),        "#3182CE", "👥"),
        ("Waiting",              len(waiting),    "#D69E2E", "⏳"),
        ("Currently Serving",   len(serving),    "#38A169", "🩺"),
        ("Completed",           len(completed),  "#6B46C1", "✅"),
        ("Emergency",           len(emergency),  "#E53E3E", "🚨"),
        ("Avg Wait (min)",      avg_wait,        "#0D7377", "⏱"),
        ("Available Doctors",   avail_doc,       "#2B6CB0", "👨‍⚕️"),
        ("Max Daily Capacity",  clinic_settings["max_daily"], "#744210", "📋"),
    ]

    grid = tk.Frame(inner, bg=theme()["bg"])
    grid.pack(fill="x", pady=(0,20))
    for i, (lbl, val, col, ico) in enumerate(stats):
        card = stat_card(grid, lbl, val, col, ico)
        card.grid(row=i//4, column=i%4, padx=6, pady=6, sticky="ew")
    for c in range(4):
        grid.columnconfigure(c, weight=1)

    # ── Queue Progress ────────────────────────────────────────
    prog_card, prog_inner = make_card(inner, "📈 Queue Progress Today")
    prog_card.pack(fill="x", pady=(0,16))

    total = len(tp) or 1
    progress_items = [
        ("Waiting",   len(waiting),   theme()["warning"]),
        ("Serving",   len(serving),   theme()["success"]),
        ("Completed", len(completed), theme()["info"]),
        ("Emergency", len(emergency), theme()["error"]),
    ]
    for lbl, count, color in progress_items:
        row = tk.Frame(prog_inner, bg=theme()["card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=f"{lbl}:", font=("Segoe UI", 10),
                 bg=theme()["card"], fg=theme()["text"], width=12, anchor="w").pack(side="left")
        bar_bg = tk.Frame(row, bg=theme()["border"], height=18, width=340)
        bar_bg.pack(side="left", padx=8)
        bar_bg.pack_propagate(False)
        pct = int(count / total * 100)
        bar = tk.Frame(bar_bg, bg=color, height=18, width=max(4, int(340 * pct / 100)))
        bar.place(x=0, y=0, relheight=1)
        tk.Label(row, text=f"{count}  ({pct}%)", font=("Segoe UI", 10),
                 bg=theme()["card"], fg=theme()["text"]).pack(side="left")

    # ── Recent Patients ───────────────────────────────────────
    rec_card, rec_inner = make_card(inner, "🕐 Recent Patients")
    rec_card.pack(fill="x", pady=(0,16))

    cols = ("Queue No", "Name", "Department", "Priority", "Status", "Arrival")
    tf, tree = make_treeview(rec_inner, cols, heights=8)
    tf.pack(fill="x")

    col_widths = [90, 160, 180, 90, 90, 90]
    for col, w in zip(cols, col_widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, minwidth=60)

    recent = sorted(tp, key=lambda x: x["arrival_time"], reverse=True)[:15]
    for p in recent:
        tree.insert("", "end", values=(
            p["queue_no"], p["name"], p["department"],
            p["priority"], p["status"], p["arrival_time"]
        ), tags=(p["priority"],))
    tree.tag_configure("Emergency", background="#FFE0E0")
    tree.tag_configure("Elderly",   background="#FFF3CD")

    # ── Doctor Availability ───────────────────────────────────
    doc_card, doc_inner = make_card(inner, "👨‍⚕️ Doctor Availability")
    doc_card.pack(fill="x", pady=(0,16))

    doc_grid = tk.Frame(doc_inner, bg=theme()["card"])
    doc_grid.pack(fill="x")
    status_colors_dash = {"Available": theme()["success"], "Busy": theme()["warning"], "Offline": theme()["text_muted"]}
    for i, d in enumerate(doctors):
        color = status_colors_dash.get(d["status"], theme()["text_muted"])
        dc = tk.Frame(doc_grid, bg=theme()["card"], padx=10, pady=8,
                      highlightbackground=theme()["border"], highlightthickness=1)
        dc.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
        tk.Label(dc, text="👨‍⚕️", font=("Segoe UI", 18), bg=theme()["card"]).pack()
        tk.Label(dc, text=d["name"], font=("Segoe UI", 10, "bold"),
                 bg=theme()["card"], fg=theme()["text"]).pack()
        tk.Label(dc, text=d["dept"], font=("Segoe UI", 8),
                 bg=theme()["card"], fg=theme()["text_muted"], wraplength=120).pack()
        badge = tk.Label(dc, text=d["status"], font=("Segoe UI", 9, "bold"),
                         bg=color, fg="white", padx=8, pady=2)
        badge.pack(pady=4)
        tk.Label(dc, text=f"Served: {d['patients_served']}",
                 font=("Segoe UI", 9), bg=theme()["card"], fg=theme()["text_muted"]).pack()
    for c in range(len(doctors)):
        doc_grid.columnconfigure(c, weight=1)

    # Refresh button
    make_btn(inner, "🔄 Refresh Dashboard",
             lambda: show_page("dashboard"), theme()["accent"]).pack(pady=10)


# ═══════════════════════════════════════════════════════════════
#  PAGE: PATIENT REGISTRATION
# ═══════════════════════════════════════════════════════════════

def build_register(parent):
    tk.Label(parent, text="📋 Register New Patient",
             font=("Segoe UI", 16, "bold"), bg=theme()["bg"], fg=theme()["text"]
             ).pack(anchor="w", padx=24, pady=(16,0))

    scroll_canvas = tk.Canvas(parent, bg=theme()["bg"], highlightthickness=0)
    sb = ttk.Scrollbar(parent, orient="vertical", command=scroll_canvas.yview)
    scroll_canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    scroll_canvas.pack(fill="both", expand=True, padx=24, pady=12)

    inner = tk.Frame(scroll_canvas, bg=theme()["bg"])
    win = scroll_canvas.create_window((0,0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
    scroll_canvas.bind("<Configure>", lambda e: scroll_canvas.itemconfig(win, width=e.width))

    outer, body = make_card(inner, padx=24, pady=20)
    outer.pack(fill="x", pady=(0,12))

    # Form vars (notes is a Text widget handled separately as notes_txt)
    vars_ = {
        "name":     tk.StringVar(),
        "age":      tk.StringVar(),
        "gender":   tk.StringVar(value="Male"),
        "phone":    tk.StringVar(),
        "address":  tk.StringVar(),
        "dept":     tk.StringVar(value="General Consultation"),
        "priority": tk.StringVar(value="Normal"),
    }

    def field_row(fr_parent, label, var, widget_type="entry", values=None):
        frame = tk.Frame(fr_parent, bg=theme()["card"])
        tk.Label(frame, text=label, font=("Segoe UI", 10, "bold"),
                 bg=theme()["card"], fg=theme()["text"], anchor="w").pack(fill="x", pady=(0,4))
        if widget_type == "entry":
            tk.Entry(frame, textvariable=var, font=("Segoe UI", 11),
                     bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                     relief="flat", highlightthickness=1,
                     highlightbackground=theme()["border"],
                     highlightcolor=theme()["accent"]).pack(fill="x", ipady=7)
        elif widget_type == "combo":
            ttk.Combobox(frame, textvariable=var, values=values,
                         font=("Segoe UI", 11), state="readonly").pack(fill="x", ipady=4)
        return frame

    # Grid layout
    grid = tk.Frame(body, bg=theme()["card"])
    grid.pack(fill="x")

    def add_field(label, var, r, col_n, wtype="entry", vals=None, span=1):
        f = field_row(grid, label, var, wtype, vals)
        f.grid(row=r, column=col_n, columnspan=span, padx=8, pady=8, sticky="ew")

    add_field("Patient Name *", vars_["name"],     0, 0, span=2)
    add_field("Age *",          vars_["age"],      0, 2)
    add_field("Gender",         vars_["gender"],   0, 3, "combo", ["Male","Female","Other"])
    add_field("Phone Number *", vars_["phone"],    1, 0)
    add_field("Address",        vars_["address"],  1, 1, span=2)
    add_field("Department *",   vars_["dept"],     1, 3, "combo",
              list(dept_counters.keys()))
    add_field("Priority Level", vars_["priority"], 2, 0, "combo",
              ["Normal","Elderly","Emergency"])

    for c in range(4):
        grid.columnconfigure(c, weight=1)

    # Notes
    notes_frame = tk.Frame(body, bg=theme()["card"])
    notes_frame.pack(fill="x", padx=8, pady=8)
    tk.Label(notes_frame, text="Notes / Symptoms", font=("Segoe UI", 10, "bold"),
             bg=theme()["card"], fg=theme()["text"], anchor="w").pack(fill="x", pady=(0,4))
    notes_txt = tk.Text(notes_frame, height=4, font=("Segoe UI", 11),
                        bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                        relief="flat", highlightthickness=1,
                        highlightbackground=theme()["border"],
                        wrap="word")
    notes_txt.pack(fill="x")

    # Error label
    err_lbl = tk.Label(body, text="", font=("Segoe UI", 10),
                       bg=theme()["card"], fg=theme()["error"])
    err_lbl.pack(pady=(8,0))

    def register():
        name  = vars_["name"].get().strip()
        age   = vars_["age"].get().strip()
        phone = vars_["phone"].get().strip()
        dept  = vars_["dept"].get()
        priority = vars_["priority"].get()
        notes = notes_txt.get("1.0", "end").strip()

        if not name:
            err_lbl.config(text="⚠ Patient name is required.")
            return
        if not age.isdigit() or not (0 < int(age) < 130):
            err_lbl.config(text="⚠ Please enter a valid age.")
            return
        if not phone:
            err_lbl.config(text="⚠ Phone number is required.")
            return

        err_lbl.config(text="")
        qno = get_next_queue_number(dept)
        doc = get_available_doctor(dept)

        patient = {
            "id":           patient_id_counter[0],
            "queue_no":     qno,
            "name":         name,
            "age":          age,
            "gender":       vars_["gender"].get(),
            "phone":        phone,
            "address":      vars_["address"].get(),
            "department":   dept,
            "priority":     priority,
            "notes":        notes,
            "arrival_time": time_str(),
            "date":         today_str(),
            "doctor":       doc,
            "status":       "Waiting",
            "end_time":     "",
        }
        patients.append(patient)
        patient_id_counter[0] += 1

        # Mark doctor busy if was available
        for d in doctors:
            if d["name"] == doc and d["status"] == "Available":
                if priority == "Emergency":
                    d["status"] = "Busy"
                break

        add_audit("REGISTER", f"Registered {name} | Queue: {qno} | Dept: {dept} | Priority: {priority}")

        # Voice announcement
        dept_room = {"General Consultation":"Consultation Room One",
                     "Pediatrics":"Pediatrics Room",
                     "Maternity":"Maternity Suite",
                     "Laboratory":"Laboratory",
                     "Dental":"Dental Room",
                     "Pharmacy":"Pharmacy Counter"}
        if priority == "Emergency":
            speak(f"Attention! Emergency patient {name} has been registered. Please prepare immediately.")
        else:
            speak(f"Patient {name} has been registered. Queue number {qno}. Please proceed to {dept_room.get(dept,'the waiting area')}.")

        show_notification("success", "Patient Registered",
            f"✅ Patient registered successfully!\n\n"
            f"Queue Number: {qno}\n"
            f"Name: {name}\n"
            f"Department: {dept}\n"
            f"Assigned Doctor: {doc}\n"
            f"Priority: {priority}")

        # Ask to print ticket
        if messagebox.askyesno("Print Ticket", "Would you like to print/export a queue ticket?"):
            export_ticket(patient)

        clear_form()

    def clear_form():
        defaults = {"gender": "Male", "dept": "General Consultation", "priority": "Normal"}
        for key, var in vars_.items():
            var.set(defaults.get(key, ""))
        notes_txt.delete("1.0", "end")
        err_lbl.config(text="")

    # Buttons
    btn_row = tk.Frame(body, bg=theme()["card"])
    btn_row.pack(pady=16)
    make_btn(btn_row, "✅ Register Patient", register, theme()["success"]).pack(side="left", padx=6)
    make_btn(btn_row, "🗑 Clear Form", clear_form, theme()["warning"]).pack(side="left", padx=6)
    make_btn(btn_row, "✗ Cancel", lambda: show_page("dashboard"), theme()["error"]).pack(side="left", padx=6)


# ═══════════════════════════════════════════════════════════════
#  TICKET EXPORT
# ═══════════════════════════════════════════════════════════════

def export_ticket(patient):
    if not REPORTLAB_AVAILABLE:
        messagebox.showinfo("Export", "ReportLab not installed. Showing ticket preview:\n\n" + format_ticket_text(patient))
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files","*.pdf"),("All","*.*")],
        initialfile=f"ticket_{patient['queue_no']}.pdf"
    )
    if not path:
        return

    try:
        c = rl_canvas.Canvas(path, pagesize=(220, 320))
        w, h = 220, 320

        # Header
        c.setFillColor(colors.HexColor("#1A3C6B"))
        c.rect(0, h-80, w, 80, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(w/2, h-30, clinic_settings["name"])
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h-48, "Queue Management System")

        # Queue number highlight
        c.setFillColor(colors.HexColor("#14BDAC"))  # spellchecker: disable-line
        c.rect(20, h-130, w-40, 42, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(w/2, h-112, patient["queue_no"])

        # Details
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        details = [
            ("Name",       patient["name"]),
            ("Age/Gender", f"{patient['age']} / {patient['gender']}"),
            ("Department", patient["department"]),
            ("Priority",   patient["priority"]),
            ("Doctor",     patient["doctor"]),
            ("Date",       patient["date"]),
            ("Time",       patient["arrival_time"]),
        ]
        y = h - 155
        for label, val in details:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(20, y, f"{label}:")
            c.setFont("Helvetica", 8)
            c.drawString(90, y, str(val))
            y -= 16

        # Footer
        c.setFillColor(colors.HexColor("#1A3C6B"))
        c.setFont("Helvetica", 8)
        c.drawCentredString(w/2, 20, "Please wait for your number to be called.")
        c.drawCentredString(w/2, 10, "Thank you for choosing " + clinic_settings["name"])

        c.save()
        add_audit("TICKET_EXPORT", f"Ticket exported for {patient['queue_no']} — {patient['name']}")
        show_notification("success", "Ticket Exported", f"Ticket saved to:\n{path}")
    except Exception as e:  # catches OSError, ReportLab errors, and unexpected failures
        messagebox.showerror("Export Error", str(e))


def format_ticket_text(p):
    return (f"{'='*30}\n"
            f"  {clinic_settings['name']}\n"
            f"  Queue Ticket\n"
            f"{'='*30}\n"
            f"  Queue No : {p['queue_no']}\n"
            f"  Name     : {p['name']}\n"
            f"  Dept     : {p['department']}\n"
            f"  Priority : {p['priority']}\n"
            f"  Doctor   : {p['doctor']}\n"
            f"  Date     : {p['date']}\n"
            f"  Time     : {p['arrival_time']}\n"
            f"{'='*30}")


# ═══════════════════════════════════════════════════════════════
#  PAGE: QUEUE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def build_queue(parent):
    header = tk.Frame(parent, bg=theme()["bg"])
    header.pack(fill="x", padx=24, pady=(16,8))
    tk.Label(header, text="📊 Queue Management",
             font=("Segoe UI", 16, "bold"), bg=theme()["bg"], fg=theme()["text"]).pack(side="left")

    filter_var = tk.StringVar(value="All")
    dept_var   = tk.StringVar(value="All")

    # ── Filter bar ─────────────────────────────────────────────────────────
    filter_frame = tk.Frame(parent, bg=theme()["card"], padx=16, pady=10)
    filter_frame.pack(fill="x", padx=24, pady=(0,6))

    # ── Action buttons (packed BEFORE treeview so they are never hidden) ───
    btn_frame = tk.Frame(parent, bg=theme()["bg"], padx=24, pady=6)
    btn_frame.pack(fill="x")

    # ── Voice panel (also above the expanding treeview) ────────────────────
    voice_frame = tk.Frame(parent, bg=theme()["card"], padx=16, pady=8)
    voice_frame.pack(fill="x", padx=24, pady=(0,6))

    # ── Treeview (packed last — expand=True fills only the remaining space) ─
    cols = ("Queue No","Name","Department","Priority","Arrival","Doctor","Status")
    tf, tree = make_treeview(parent, cols, heights=10)
    tf.pack(fill="both", expand=True, padx=24, pady=(0,8))

    widths = [90, 160, 170, 90, 80, 130, 90]
    for col, w in zip(cols, widths):
        tree.column(col, width=w, minwidth=60)

    tree.tag_configure("Emergency", background="#FFE0E0", foreground="#C53030")
    tree.tag_configure("Elderly",   background="#FEFCBF", foreground="#744210")
    tree.tag_configure("Completed", foreground=theme()["text_muted"])
    tree.tag_configure("Cancelled", foreground=theme()["text_muted"])

    # ── Inner functions ─────────────────────────────────────────────────────

    def refresh_queue():
        tree.delete(*tree.get_children())
        status_f = filter_var.get()
        dept_f   = dept_var.get()
        pts = sorted(today_patients(), key=priority_sort_key)
        for p in pts:
            if status_f != "All" and p["status"] != status_f:
                continue
            if dept_f != "All" and p["department"] != dept_f:
                continue
            tags = []
            if p["priority"] == "Emergency":
                tags.append("Emergency")
            elif p["priority"] == "Elderly":
                tags.append("Elderly")
            if p["status"] in ("Completed", "Cancelled"):
                tags.append(p["status"])
            tree.insert("", "end", iid=p["queue_no"], tags=tuple(tags),
                        values=(p["queue_no"], p["name"], p["department"],
                                p["priority"], p["arrival_time"], p["doctor"], p["status"]))

    def sort_tree(tv, sort_col, reverse):
        data = [(tv.set(k, sort_col), k) for k in tv.get_children("")]
        data.sort(reverse=reverse)
        for idx, (_, k) in enumerate(data):
            tv.move(k, "", idx)
        tv.heading(sort_col, command=lambda: sort_tree(tv, sort_col, not reverse))

    def get_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a patient from the queue.")
            return None
        qno = sel[0]
        for p in patients:
            if p["queue_no"] == qno:
                return p
        return None

    def call_next():
        waiting = [p for p in today_patients() if p["status"] == "Waiting"]
        if not waiting:
            show_notification("info", "Queue Empty", "No patients currently waiting in the queue.")
            return
        waiting_sorted = sorted(waiting, key=priority_sort_key)
        p = waiting_sorted[0]
        p["status"] = "Called"
        dept_room = {
            "General Consultation": "Consultation Room One",
            "Pediatrics":           "Pediatrics Room",
            "Maternity":            "Maternity Suite",
            "Laboratory":           "Laboratory",
            "Dental":               "Dental Room",
            "Pharmacy":             "Pharmacy Counter",
        }
        room = dept_room.get(p["department"], "the clinic")
        msg = (f"Attention please. Queue Number {p['queue_no']}, "
               f"{p['name']}, please proceed to {room}. "
               f"Your doctor is {p['doctor']}. Thank you.")
        speak(msg)
        add_audit("CALL_NEXT", f"Called {p['queue_no']} — {p['name']} → {room}")
        refresh_queue()
        try:
            tree.selection_set(p["queue_no"])
            tree.see(p["queue_no"])
        except tk.TclError:
            pass
        remaining = len([x for x in today_patients() if x["status"] == "Waiting"])
        show_notification(
            "info",
            "✅ Patient Called",
            f"Called:  {p['queue_no']} — {p['name']}\n"
            f"Dept:    {p['department']}\n"
            f"Room:    {room}\n"
            f"Doctor:  {p['doctor']}\n\n"
            f"Still waiting: {remaining} patient(s)\n\n"
            "Tip: Click 'Mark Serving' once the patient enters the room."
        )

    def mark_serving():
        p = get_selected()
        if not p:
            return
        if p["status"] not in ("Waiting", "Called"):
            show_notification("warning", "Action Error",
                              f"Cannot mark as Serving from status: {p['status']}")
            return
        p["status"] = "Serving"
        for d in doctors:
            if d["name"] == p["doctor"]:
                d["status"] = "Busy"
                break
        add_audit("SERVING", f"{p['queue_no']} — {p['name']} now Serving")
        speak(f"Patient {p['name']}, queue number {p['queue_no']}, "
              f"is now being served by {p['doctor']}.")
        refresh_queue()

    def mark_completed():
        p = get_selected()
        if not p:
            return
        if p["status"] not in ("Waiting", "Called", "Serving"):
            show_notification("warning", "Action Error",
                              f"Cannot complete from status: {p['status']}")
            return
        p["status"]   = "Completed"
        p["end_time"] = time_str()
        for d in doctors:
            if d["name"] == p["doctor"]:
                d["patients_served"] += 1
                still_serving = [x for x in today_patients()
                                 if x["doctor"] == d["name"] and x["status"] == "Serving"]
                if not still_serving:
                    d["status"] = "Available"
                break
        add_audit("COMPLETED", f"{p['queue_no']} — {p['name']} Completed")
        refresh_queue()
        show_notification("success", "Completed",
                          f"Patient {p['name']} consultation completed.")

    def cancel_queue():
        p = get_selected()
        if not p:
            return
        if p["status"] in ("Completed", "Cancelled"):
            show_notification("warning", "Cannot Cancel",
                              "Patient already completed or cancelled.")
            return
        if messagebox.askyesno("Confirm",
                               f"Cancel queue for {p['name']} ({p['queue_no']})?"):
            p["status"] = "Cancelled"
            add_audit("CANCELLED", f"{p['queue_no']} — {p['name']} Cancelled")
            refresh_queue()
            show_notification("info", "Cancelled",
                              f"Queue for {p['name']} has been cancelled.")

    def print_selected():
        p = get_selected()
        if p:
            export_ticket(p)

    # ── Populate filter bar now that functions exist ────────────────────────
    tk.Label(filter_frame, text="Filter:", font=("Segoe UI",10,"bold"),
             bg=theme()["card"], fg=theme()["text"]).pack(side="left", padx=(0,8))
    for opt in ["All","Waiting","Called","Serving","Completed","Cancelled"]:
        tk.Radiobutton(filter_frame, text=opt, variable=filter_var, value=opt,
                       bg=theme()["card"], fg=theme()["text"],
                       activebackground=theme()["card"],
                       font=("Segoe UI",10),
                       command=refresh_queue).pack(side="left", padx=4)

    tk.Label(filter_frame, text="|", bg=theme()["card"], fg=theme()["border"]).pack(side="left", padx=8)
    tk.Label(filter_frame, text="Dept:", font=("Segoe UI",10,"bold"),
             bg=theme()["card"], fg=theme()["text"]).pack(side="left")
    dept_combo = ttk.Combobox(filter_frame, textvariable=dept_var,
                               values=["All"]+list(dept_counters.keys()),
                               state="readonly", width=20)
    dept_combo.pack(side="left", padx=6)
    dept_combo.bind("<<ComboboxSelected>>", lambda _e: refresh_queue())

    # ── Populate action buttons ─────────────────────────────────────────────
    for text, cmd, color in [
        ("📢 Call Next",    call_next,      theme()["info"]),
        ("🩺 Mark Serving", mark_serving,   theme()["success"]),
        ("✅ Complete",      mark_completed, theme()["accent"]),
        ("✗ Cancel Queue",  cancel_queue,   theme()["error"]),
        ("🔄 Refresh",      refresh_queue,  theme()["accent2"]),
        ("🖨 Print Ticket", print_selected, "#6B46C1"),
    ]:
        make_btn(btn_frame, text, cmd, color).pack(side="left", padx=4)

    # ── Populate voice panel ────────────────────────────────────────────────
    tk.Label(voice_frame, text="🔊 Voice:",
             font=("Segoe UI",10,"bold"), bg=theme()["card"], fg=theme()["text"]).pack(side="left")

    voice_var = tk.BooleanVar(value=voice_settings["enabled"])
    tk.Checkbutton(voice_frame, text="Enable",
                   variable=voice_var, bg=theme()["card"], fg=theme()["text"],
                   activebackground=theme()["card"],
                   command=lambda: voice_settings.update(
                       {"enabled": voice_var.get()})).pack(side="left", padx=8)

    tk.Label(voice_frame, text="Volume:", bg=theme()["card"], fg=theme()["text"],
             font=("Segoe UI",9)).pack(side="left", padx=(8,4))
    vol_var = tk.DoubleVar(value=voice_settings["volume"] * 100)
    ttk.Scale(voice_frame, from_=0, to=100, variable=vol_var,
              orient="horizontal", length=90,
              command=lambda v: voice_settings.update(
                  {"volume": float(v)/100})).pack(side="left")

    tk.Label(voice_frame, text="Rate:", bg=theme()["card"], fg=theme()["text"],
             font=("Segoe UI",9)).pack(side="left", padx=(8,4))
    rate_var = tk.IntVar(value=voice_settings["rate"])
    ttk.Scale(voice_frame, from_=50, to=300, variable=rate_var,
              orient="horizontal", length=90,
              command=lambda v: voice_settings.update(
                  {"rate": int(float(v))})).pack(side="left")

    if TTS_AVAILABLE:
        make_btn(voice_frame, "🔊 Test",
                 lambda: speak(
                     f"Welcome to {clinic_settings['name']} Queue Management System."),
                 theme()["accent2"]).pack(side="left", padx=8)
    else:
        tk.Label(voice_frame, text="(pyttsx3 not installed)",
                 font=("Segoe UI",9), bg=theme()["card"],
                 fg=theme()["text_muted"]).pack(side="left", padx=8)

    # ── Set column headings now that sort_tree is defined ───────────────────
    for col, w in zip(cols, widths):
        tree.heading(col, text=col, command=lambda sc=col: sort_tree(tree, sc, False))

    refresh_queue()


# ═══════════════════════════════════════════════════════════════
#  PAGE: SEARCH
# ═══════════════════════════════════════════════════════════════

def build_search(parent):
    tk.Label(parent, text="🔍 Search Patients",
             font=("Segoe UI",16,"bold"), bg=theme()["bg"], fg=theme()["text"]
             ).pack(anchor="w", padx=24, pady=(16,8))

    search_card, search_inner = make_card(parent, padx=20, pady=16)
    search_card.pack(fill="x", padx=24, pady=(0,12))

    row = tk.Frame(search_inner, bg=theme()["card"])
    row.pack(fill="x")

    tk.Label(row, text="Search by:", font=("Segoe UI",10,"bold"),
             bg=theme()["card"], fg=theme()["text"]).pack(side="left", padx=(0,8))
    by_var = tk.StringVar(value="Name")
    for opt in ["Name","Queue No","Phone"]:
        tk.Radiobutton(row, text=opt, variable=by_var, value=opt,
                       bg=theme()["card"], fg=theme()["text"], activebackground=theme()["card"],
                       font=("Segoe UI",10)).pack(side="left", padx=4)

    tk.Label(search_inner, text=" ", bg=theme()["card"]).pack()
    q_row = tk.Frame(search_inner, bg=theme()["card"])
    q_row.pack(fill="x")
    q_var = tk.StringVar()
    q_entry = tk.Entry(q_row, textvariable=q_var, font=("Segoe UI",13),
                       bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                       relief="flat", highlightthickness=1,
                       highlightbackground=theme()["border"],
                       highlightcolor=theme()["accent"])
    q_entry.pack(side="left", fill="x", expand=True, ipady=8)
    q_entry.focus()

    cols = ("Queue No","Name","Age","Gender","Phone","Department","Priority","Status","Doctor","Arrival")
    tf, tree = make_treeview(parent, cols, heights=14)
    tf.pack(fill="both", expand=True, padx=24)
    widths = [90,150,50,70,110,160,90,90,130,90]
    for col, w in zip(cols, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w)

    detail_lbl = tk.Label(parent, text="", font=("Segoe UI",10),
                          bg=theme()["bg"], fg=theme()["text_muted"])
    detail_lbl.pack(padx=24, pady=4, anchor="w")

    def do_search(*_):  # called by StringVar trace (name, index, mode) — args ignored
        q   = q_var.get().strip().lower()
        by  = by_var.get()
        tree.delete(*tree.get_children())

        results = []
        for p in patients:
            if by == "Name" and q in p["name"].lower():
                results.append(p)
            elif by == "Queue No" and q in p["queue_no"].lower():
                results.append(p)
            elif by == "Phone" and q in p["phone"].lower():
                results.append(p)

        for p in results:
            tree.insert("", "end", values=(
                p["queue_no"], p["name"], p["age"], p["gender"], p["phone"],
                p["department"], p["priority"], p["status"], p["doctor"], p["arrival_time"]
            ))
        detail_lbl.config(text=f"Found {len(results)} record(s)." if q else "")

    q_var.trace("w", do_search)
    make_btn(q_row, "🔍 Search", do_search, theme()["accent"]).pack(side="left", padx=8)
    make_btn(q_row, "✗ Clear",
             lambda: (q_var.set(""), tree.delete(*tree.get_children())),
             theme()["warning"]).pack(side="left")


# ═══════════════════════════════════════════════════════════════
#  PAGE: LIVE QUEUE MONITOR
# ═══════════════════════════════════════════════════════════════

def build_monitor(parent):
    outer = tk.Frame(parent, bg="#0D1B2A")
    outer.pack(fill="both", expand=True)

    # Header
    hdr = tk.Frame(outer, bg="#1A3C6B", pady=14)
    hdr.pack(fill="x")
    tk.Label(hdr, text="🏥 " + clinic_settings["name"],
             font=("Segoe UI",24,"bold"), bg="#1A3C6B", fg="white").pack()
    tk.Label(hdr, text="LIVE QUEUE MONITOR",
             font=("Segoe UI",12), bg="#1A3C6B", fg="#14BDAC").pack()  # spellchecker: disable-line

    clock_lbl = tk.Label(hdr, text="", font=("Segoe UI",16,"bold"),
                         bg="#1A3C6B", fg="#A0C4FF")
    clock_lbl.pack()

    body = tk.Frame(outer, bg="#0D1B2A")
    body.pack(fill="both", expand=True, padx=20, pady=20)

    # Now Serving card
    serving_card = tk.Frame(body, bg="#14BDAC", padx=30, pady=20)  # spellchecker: disable-line
    serving_card.pack(side="left", fill="both", expand=True, padx=10)

    tk.Label(serving_card, text="NOW SERVING",
             font=("Segoe UI",16,"bold"), bg="#14BDAC", fg="white").pack()  # spellchecker: disable-line
    now_lbl = tk.Label(serving_card, text="—",
                       font=("Segoe UI",72,"bold"), bg="#14BDAC", fg="white")  # spellchecker: disable-line
    now_lbl.pack()
    now_name_lbl = tk.Label(serving_card, text="",
                            font=("Segoe UI",16), bg="#14BDAC", fg="white")  # spellchecker: disable-line
    now_name_lbl.pack()
    doc_lbl = tk.Label(serving_card, text="",
                       font=("Segoe UI",13), bg="#14BDAC", fg="#E0F7F5")  # spellchecker: disable-line
    doc_lbl.pack(pady=6)

    # Queue info card
    info_card = tk.Frame(body, bg="#1A3C6B", padx=30, pady=20)
    info_card.pack(side="left", fill="both", expand=True, padx=10)

    tk.Label(info_card, text="NEXT UP",
             font=("Segoe UI",16,"bold"), bg="#1A3C6B", fg="#A0C4FF").pack()
    next_lbl = tk.Label(info_card, text="—",
                        font=("Segoe UI",48,"bold"), bg="#1A3C6B", fg="white")
    next_lbl.pack()
    next_name_lbl = tk.Label(info_card, text="",
                             font=("Segoe UI",13), bg="#1A3C6B", fg="#A0C4FF")
    next_name_lbl.pack(pady=4)

    tk.Frame(info_card, bg="#14BDAC", height=2).pack(fill="x", pady=14)  # spellchecker: disable-line

    tk.Label(info_card, text="WAITING PATIENTS",
             font=("Segoe UI",13,"bold"), bg="#1A3C6B", fg="#A0C4FF").pack()
    wait_lbl = tk.Label(info_card, text="0",
                        font=("Segoe UI",48,"bold"), bg="#1A3C6B", fg="#ECC94B")
    wait_lbl.pack()

    # Waiting list
    list_card = tk.Frame(outer, bg="#111827", padx=20, pady=12)
    list_card.pack(fill="x", padx=20, pady=(0,20))
    tk.Label(list_card, text="QUEUE LIST", font=("Segoe UI",12,"bold"),
             bg="#111827", fg="#A0C4FF").pack(anchor="w")

    wait_list_frame = tk.Frame(list_card, bg="#111827")
    wait_list_frame.pack(fill="x")

    def refresh_monitor():
        tp = today_patients()
        serving = [p for p in tp if p["status"] == "Serving"]
        waiting = sorted([p for p in tp if p["status"] in ("Waiting","Called")],
                         key=priority_sort_key)

        if serving:
            p = serving[-1]
            now_lbl.config(text=p["queue_no"])
            now_name_lbl.config(text=p["name"])
            doc_lbl.config(text=f"Doctor: {p['doctor']}")
        else:
            called = [p for p in tp if p["status"] == "Called"]
            if called:
                p = called[-1]
                now_lbl.config(text=p["queue_no"])
                now_name_lbl.config(text=p["name"])
                doc_lbl.config(text=f"Doctor: {p['doctor']}")
            else:
                now_lbl.config(text="—")
                now_name_lbl.config(text="")
                doc_lbl.config(text="")

        if waiting:
            next_lbl.config(text=waiting[0]["queue_no"])
            next_name_lbl.config(text=waiting[0]["name"])
        else:
            next_lbl.config(text="—")
            next_name_lbl.config(text="")

        wait_lbl.config(text=str(len(waiting)))
        clock_lbl.config(text=datetime.datetime.now().strftime("🕐 %H:%M:%S"))

        # Queue list
        for w in wait_list_frame.winfo_children():
            w.destroy()
        for i, p in enumerate(waiting[:12]):
            color = "#E53E3E" if p["priority"]=="Emergency" else "#ECC94B" if p["priority"]=="Elderly" else "#4A5568"
            item = tk.Frame(wait_list_frame, bg=color, padx=10, pady=6)
            item.grid(row=0, column=i, padx=4, pady=2)
            tk.Label(item, text=p["queue_no"], font=("Segoe UI",14,"bold"),
                     bg=color, fg="white").pack()
            tk.Label(item, text=p["name"][:12], font=("Segoe UI",9),
                     bg=color, fg="white").pack()

        if outer.winfo_exists():
            outer.after(2000, refresh_monitor)  # type: ignore[arg-type]

    def open_fullscreen():
        win = tk.Toplevel()
        win.title("Live Monitor — " + clinic_settings["name"])
        win.attributes("-fullscreen", True)
        win.configure(bg="#0D1B2A")
        tk.Button(win, text="✗ Close", font=("Segoe UI",11),
                  bg="#E53E3E", fg="white", relief="flat", command=win.destroy
                  ).place(relx=1, rely=0, anchor="ne", x=-10, y=10)
        build_monitor(win)

    btn_row = tk.Frame(outer, bg="#0D1B2A")
    btn_row.pack(pady=8)
    make_btn(btn_row, "⛶ Open Fullscreen", open_fullscreen, "#1A3C6B").pack(side="left", padx=6)
    make_btn(btn_row, "🔄 Refresh Now", refresh_monitor, "#14BDAC").pack(side="left", padx=6)  # spellchecker: disable-line

    refresh_monitor()


# ═══════════════════════════════════════════════════════════════
#  PAGE: DOCTOR MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def build_doctors(parent):
    tk.Label(parent, text="👨‍⚕️ Doctor Management",
             font=("Segoe UI",16,"bold"), bg=theme()["bg"], fg=theme()["text"]
             ).pack(anchor="w", padx=24, pady=(16,8))

    doc_card, doc_inner = make_card(parent, "Doctor Roster", padx=20, pady=16)
    doc_card.pack(fill="x", padx=24, pady=(0,16))

    grid = tk.Frame(doc_inner, bg=theme()["card"])
    grid.pack(fill="x")

    def refresh_doctors():
        for w in grid.winfo_children():
            w.destroy()
        status_colors = {"Available":theme()["success"],"Busy":theme()["warning"],"Offline":theme()["text_muted"]}

        for i, d in enumerate(doctors):
            col_frame = tk.Frame(grid, bg=theme()["card"], padx=12, pady=12,
                                 highlightbackground=theme()["border"], highlightthickness=1)
            col_frame.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")

            tk.Label(col_frame, text="👨‍⚕️", font=("Segoe UI",28),
                     bg=theme()["card"]).pack()
            tk.Label(col_frame, text=d["name"], font=("Segoe UI",12,"bold"),
                     bg=theme()["card"], fg=theme()["text"]).pack()
            tk.Label(col_frame, text=d["dept"], font=("Segoe UI",9),
                     bg=theme()["card"], fg=theme()["text_muted"], wraplength=140).pack()
            tk.Label(col_frame, text=d["id"], font=("Segoe UI",9),
                     bg=theme()["card"], fg=theme()["text_muted"]).pack(pady=2)

            sc = status_colors.get(d["status"], theme()["text_muted"])
            badge = tk.Label(col_frame, text=f"● {d['status']}",
                             font=("Segoe UI",10,"bold"), bg=sc, fg="white",
                             padx=10, pady=3)
            badge.pack(pady=6)

            # Status changer
            sv = tk.StringVar(value=d["status"])
            combo = ttk.Combobox(col_frame, textvariable=sv,
                                  values=["Available","Busy","Offline"],
                                  state="readonly", width=12)
            combo.pack()

            def make_change(doc, var):
                def change(_e):
                    old = doc["status"]
                    doc["status"] = var.get()
                    add_audit("DOCTOR_STATUS", f"{doc['name']} status: {old} → {doc['status']}")
                    refresh_doctors()
                return change
            combo.bind("<<ComboboxSelected>>", make_change(d, sv))

            tk.Label(col_frame, text=f"Patients Served: {d['patients_served']}",
                     font=("Segoe UI",10), bg=theme()["card"], fg=theme()["text"]).pack(pady=4)

            # Patients assigned
            assigned = [p for p in today_patients() if p["doctor"]==d["name"] and p["status"] not in ("Completed","Cancelled")]
            tk.Label(col_frame, text=f"Active: {len(assigned)}",
                     font=("Segoe UI",9), bg=theme()["card"], fg=theme()["accent"]).pack()

        for c in range(len(doctors)):
            grid.columnconfigure(c, weight=1)

    refresh_doctors()

    # Doctor patient list
    sel_card, sel_inner = make_card(parent, "Patients by Doctor", padx=16, pady=16)
    sel_card.pack(fill="both", expand=True, padx=24, pady=(0,16))

    row = tk.Frame(sel_inner, bg=theme()["card"])
    row.pack(fill="x", pady=(0,10))
    tk.Label(row, text="Select Doctor:", font=("Segoe UI",10,"bold"),
             bg=theme()["card"], fg=theme()["text"]).pack(side="left")
    doc_sel_var = tk.StringVar(value=doctors[0]["name"])
    doc_combo = ttk.Combobox(row, textvariable=doc_sel_var,
                              values=[d["name"] for d in doctors],
                              state="readonly", width=20)
    doc_combo.pack(side="left", padx=8)

    cols = ("Queue No","Name","Department","Priority","Status","Arrival")
    df, dtree = make_treeview(sel_inner, cols, heights=8)
    df.pack(fill="both", expand=True)
    for col in cols:
        dtree.heading(col, text=col)
        dtree.column(col, width=130)

    def load_doc_patients(*_):  # event arg from ComboboxSelected is ignored
        dtree.delete(*dtree.get_children())
        sel_doc = doc_sel_var.get()
        for p in today_patients():
            if p["doctor"] == sel_doc:
                dtree.insert("","end", values=(
                    p["queue_no"], p["name"], p["department"],
                    p["priority"], p["status"], p["arrival_time"]
                ))

    doc_combo.bind("<<ComboboxSelected>>", load_doc_patients)
    load_doc_patients()
    make_btn(row, "🔄 Refresh", lambda: (refresh_doctors(), load_doc_patients()), theme()["accent"]).pack(side="right")


# ═══════════════════════════════════════════════════════════════
#  PAGE: REPORTS
# ═══════════════════════════════════════════════════════════════

def build_reports(parent):
    tk.Label(parent, text="📈 Reports Dashboard",
             font=("Segoe UI",16,"bold"), bg=theme()["bg"], fg=theme()["text"]
             ).pack(anchor="w", padx=24, pady=(16,8))

    notebook = ttk.Notebook(parent)
    notebook.pack(fill="both", expand=True, padx=24, pady=8)

    # ── Daily Report tab ──────────────────────────────────────
    daily_frame = tk.Frame(notebook, bg=theme()["bg"])
    notebook.add(daily_frame, text="📅 Daily Report")

    def build_daily(frame):
        daily_tp  = today_patients()
        waiting   = [p for p in daily_tp if p["status"] == "Waiting"]
        serving   = [p for p in daily_tp if p["status"] == "Serving"]
        completed = [p for p in daily_tp if p["status"] == "Completed"]
        cancelled = [p for p in daily_tp if p["status"] == "Cancelled"]
        emergency = [p for p in daily_tp if p["priority"] == "Emergency"]

        sum_card, sum_inner = make_card(frame, f"Daily Summary — {today_str()}", 20, 16)
        sum_card.pack(fill="x", padx=16, pady=12)

        stats = [
            ("Total Patients",    len(daily_tp),  theme()["accent"]),
            ("Waiting",           len(waiting),   theme()["warning"]),
            ("Serving",           len(serving),   theme()["success"]),
            ("Completed",         len(completed), theme()["info"]),
            ("Cancelled",         len(cancelled), theme()["text_muted"]),
            ("Emergency",         len(emergency), theme()["error"]),
        ]
        row = tk.Frame(sum_inner, bg=theme()["card"])
        row.pack(fill="x")
        for lbl, val, col in stats:
            card = tk.Frame(row, bg=col, padx=14, pady=10)
            card.pack(side="left", padx=6, expand=True, fill="x")
            tk.Label(card, text=str(val), font=("Segoe UI",24,"bold"),
                     bg=col, fg="white").pack()
            tk.Label(card, text=lbl, font=("Segoe UI",9),
                     bg=col, fg="white").pack()

        # Dept breakdown
        dept_card, dept_inner = make_card(frame, "Department Breakdown", 20, 16)
        dept_card.pack(fill="x", padx=16, pady=(0,12))
        dept_data = {}
        for p in daily_tp:
            dept_data[p["department"]] = dept_data.get(p["department"], 0) + 1
        for dept, count in sorted(dept_data.items(), key=lambda x: -x[1]):
            dr = tk.Frame(dept_inner, bg=theme()["card"])
            dr.pack(fill="x", pady=2)
            tk.Label(dr, text=dept, font=("Segoe UI",10),
                     bg=theme()["card"], fg=theme()["text"], width=22, anchor="w").pack(side="left")
            bar_bg = tk.Frame(dr, bg=theme()["border"], height=16, width=280)
            bar_bg.pack(side="left", padx=8)
            bar_bg.pack_propagate(False)
            pct = int(count/max(len(daily_tp),1)*100)
            tk.Frame(bar_bg, bg=theme()["accent"], height=16,
                     width=max(4, int(280*pct/100))).place(x=0,y=0,relheight=1)
            tk.Label(dr, text=f"{count}", font=("Segoe UI",10),
                     bg=theme()["card"], fg=theme()["text"]).pack(side="left")

        # Export buttons
        btn_row = tk.Frame(frame, bg=theme()["bg"], padx=16, pady=8)
        btn_row.pack(fill="x")
        make_btn(btn_row, "📥 Export CSV", lambda: export_report_csv(daily_tp), theme()["success"]).pack(side="left", padx=4)
        make_btn(btn_row, "📄 Export PDF", lambda: export_report_pdf(daily_tp), theme()["info"]).pack(side="left", padx=4)
        make_btn(btn_row, "📝 Export TXT", lambda: export_report_txt(daily_tp), theme()["accent2"]).pack(side="left", padx=4)

    build_daily(daily_frame)

    # ── Doctor Report tab ─────────────────────────────────────
    doc_frame = tk.Frame(notebook, bg=theme()["bg"])
    notebook.add(doc_frame, text="👨‍⚕️ Doctor Report")

    doc_card, doc_inner = make_card(doc_frame, "Patients Served per Doctor", 20, 16)
    doc_card.pack(fill="x", padx=16, pady=12)
    cols = ("Doctor ID","Name","Department","Status","Patients Served","Active Patients")
    df, dtree = make_treeview(doc_inner, cols, heights=8)
    df.pack(fill="both", expand=True)
    for dcol in cols:
        dtree.heading(dcol, text=dcol)
        dtree.column(dcol, width=130)
    tp = today_patients()
    for d in doctors:
        active = sum(1 for p in tp if p["doctor"]==d["name"] and p["status"] not in ("Completed","Cancelled"))
        dtree.insert("","end", values=(d["id"],d["name"],d["dept"],d["status"],d["patients_served"],active))


def export_report_csv(data):
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV","*.csv")],
        initialfile=f"report_{today_str()}.csv"
    )
    if not path: return
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)
        add_audit("EXPORT_CSV", f"Exported {len(data)} records to {path}")
        show_notification("success","Exported",f"CSV saved to:\n{path}")
    except Exception as e:  # catches OSError, ReportLab errors, and unexpected failures
        messagebox.showerror("Error", str(e))


def export_report_txt(data):
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text","*.txt")],
        initialfile=f"report_{today_str()}.txt"
    )
    if not path: return
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{clinic_settings['name']} — Daily Report\n")
            f.write(f"Date: {today_str()}\n")
            f.write(f"Total Records: {len(data)}\n\n")
            f.write("-"*80+"\n")
            for p in data:
                f.write(f"[{p['queue_no']}] {p['name']} | {p['department']} | {p['priority']} | {p['status']} | {p['arrival_time']}\n")
        add_audit("EXPORT_TXT", f"Exported TXT to {path}")
        show_notification("success","Exported",f"TXT saved to:\n{path}")
    except Exception as e:  # catches OSError, ReportLab errors, and unexpected failures
        messagebox.showerror("Error", str(e))


def export_report_pdf(data):
    if not REPORTLAB_AVAILABLE:
        messagebox.showinfo("PDF Export","ReportLab not available. Please install it:\npip install reportlab")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF","*.pdf")],
        initialfile=f"report_{today_str()}.pdf"
    )
    if not path: return
    try:
        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        headers = ["Queue No","Name","Department","Priority","Status","Arrival","Doctor"]
        table_data = [headers] + [
            [p.get("queue_no",""), p.get("name",""), p.get("department",""),
             p.get("priority",""), p.get("status",""),
             p.get("arrival_time",""), p.get("doctor","")]
            for p in data
        ]
        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1A3C6B")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#EBF8FF")]),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ("ALIGN",      (0,0), (-1,-1), "LEFT"),
            ("LEFTPADDING",(0,0), (-1,-1), 6),
        ]))
        story = [
            Paragraph(f"{clinic_settings['name']} — Daily Patient Report", styles["Title"]),
            Paragraph(f"Date: {today_str()}  |  Total: {len(data)}", styles["Normal"]),
            Spacer(1, 12),
            t,
        ]
        doc.build(story)
        add_audit("EXPORT_PDF", f"Exported PDF report to {path}")
        show_notification("success","Exported",f"PDF saved to:\n{path}")
    except Exception as e:  # catches OSError, ReportLab errors, and unexpected failures
        messagebox.showerror("Error", str(e))


# ═══════════════════════════════════════════════════════════════
#  PAGE: AUDIT LOG
# ═══════════════════════════════════════════════════════════════

def build_audit(parent):
    if current_user["role"] != "Administrator":
        tk.Label(parent, text="⚠ Access Denied — Administrators Only",
                 font=("Segoe UI",16), bg=theme()["bg"], fg=theme()["error"]).pack(pady=40)
        return

    tk.Label(parent, text="📝 Audit Log",
             font=("Segoe UI",16,"bold"), bg=theme()["bg"], fg=theme()["text"]
             ).pack(anchor="w", padx=24, pady=(16,8))

    btn_row = tk.Frame(parent, bg=theme()["bg"], padx=24)
    btn_row.pack(fill="x", pady=(0,8))

    cols = ("Time","User","Role","Action","Detail")
    tf, tree = make_treeview(parent, cols, heights=22)
    tf.pack(fill="both", expand=True, padx=24)
    widths = [150, 100, 120, 130, 350]
    for col, w in zip(cols, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w)

    def load_logs():
        tree.delete(*tree.get_children())
        for log in reversed(audit_logs):
            tree.insert("","end", values=(
                log["time"], log["user"], log["role"], log["action"], log["detail"]
            ))

    def export_audit():
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv")],
            initialfile=f"audit_log_{today_str()}.csv"
        )
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["time","user","role","action","detail"])
            writer.writeheader()
            writer.writerows(audit_logs)
        show_notification("success","Exported",f"Audit log saved to:\n{path}")

    make_btn(btn_row, "🔄 Refresh", load_logs, theme()["accent"]).pack(side="left", padx=4)
    make_btn(btn_row, "📥 Export CSV", export_audit, theme()["success"]).pack(side="left", padx=4)
    tk.Label(btn_row, text=f"Total entries: {len(audit_logs)}",
             font=("Segoe UI",10), bg=theme()["bg"], fg=theme()["text_muted"]).pack(side="right", padx=8)

    load_logs()


# ═══════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════

def build_settings(parent):
    if current_user["role"] != "Administrator":
        tk.Label(parent, text="⚠ Access Denied — Administrators Only",
                 font=("Segoe UI",16), bg=theme()["bg"], fg=theme()["error"]).pack(pady=40)
        return

    tk.Label(parent, text="⚙ Settings",
             font=("Segoe UI",16,"bold"), bg=theme()["bg"], fg=theme()["text"]
             ).pack(anchor="w", padx=24, pady=(16,8))

    scroll = tk.Canvas(parent, bg=theme()["bg"], highlightthickness=0)
    sb = ttk.Scrollbar(parent, orient="vertical", command=scroll.yview)
    scroll.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    scroll.pack(fill="both", expand=True, padx=24, pady=8)
    inner = tk.Frame(scroll, bg=theme()["bg"])
    win = scroll.create_window((0,0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: scroll.configure(scrollregion=scroll.bbox("all")))
    scroll.bind("<Configure>", lambda e: scroll.itemconfig(win, width=e.width))

    # Clinic Settings
    c_card, c_inner = make_card(inner, "🏥 Clinic Settings", 20, 16)
    c_card.pack(fill="x", pady=(0,12))

    def setting_row(sr_parent, label, var, wtype="entry", values=None):
        sr_row = tk.Frame(sr_parent, bg=theme()["card"])
        sr_row.pack(fill="x", pady=6)
        tk.Label(sr_row, text=label, font=("Segoe UI",10,"bold"),
                 bg=theme()["card"], fg=theme()["text"], width=22, anchor="w").pack(side="left")
        if wtype == "entry":
            tk.Entry(sr_row, textvariable=var, font=("Segoe UI",11),
                     bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                     relief="flat", highlightthickness=1,
                     highlightbackground=theme()["border"], width=30).pack(side="left", ipady=5)
        elif wtype == "combo":
            ttk.Combobox(sr_row, textvariable=var, values=values,
                         font=("Segoe UI",11), width=28, state="readonly").pack(side="left")
        elif wtype == "check":
            tk.Checkbutton(sr_row, variable=var, bg=theme()["card"], fg=theme()["text"],
                           activebackground=theme()["card"]).pack(side="left")

    name_var  = tk.StringVar(value=clinic_settings["name"])
    max_var   = tk.StringVar(value=str(clinic_settings["max_daily"]))
    open_var  = tk.StringVar(value=clinic_settings["open_time"])
    close_var = tk.StringVar(value=clinic_settings["close_time"])
    font_var  = tk.StringVar(value=str(clinic_settings["font_size"]))
    hc_var    = tk.BooleanVar(value=clinic_settings["high_contrast"])

    setting_row(c_inner, "Clinic Name:",      name_var)
    setting_row(c_inner, "Max Daily Patients:", max_var)
    setting_row(c_inner, "Opening Time:",     open_var)
    setting_row(c_inner, "Closing Time:",     close_var)
    setting_row(c_inner, "Base Font Size:",   font_var, "combo", ["10","11","12","13","14","15","16"])
    setting_row(c_inner, "High Contrast Mode:", hc_var, "check")

    # Queue Prefix settings
    p_card, p_inner = make_card(inner, "🏷 Queue Prefix Settings", 20, 16)
    p_card.pack(fill="x", pady=(0,12))
    prefix_vars = {}
    for dept, prefix in dept_prefix.items():
        row = tk.Frame(p_inner, bg=theme()["card"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=dept+":", font=("Segoe UI",10,"bold"),
                 bg=theme()["card"], fg=theme()["text"], width=22, anchor="w").pack(side="left")
        pv = tk.StringVar(value=prefix)
        prefix_vars[dept] = pv
        tk.Entry(row, textvariable=pv, font=("Segoe UI",11),
                 bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                 relief="flat", highlightthickness=1, width=8,
                 highlightbackground=theme()["border"]).pack(side="left", ipady=4)

    # Voice Settings
    v_card, v_inner = make_card(inner, "🔊 Voice Settings", 20, 16)
    v_card.pack(fill="x", pady=(0,12))
    v_enabled = tk.BooleanVar(value=voice_settings["enabled"])
    v_vol     = tk.DoubleVar(value=voice_settings["volume"]*100)
    v_rate    = tk.IntVar(value=voice_settings["rate"])
    setting_row(v_inner, "Voice Enabled:", v_enabled, "check")
    row = tk.Frame(v_inner, bg=theme()["card"])
    row.pack(fill="x", pady=6)
    tk.Label(row, text="Volume:", font=("Segoe UI",10,"bold"),
             bg=theme()["card"], fg=theme()["text"], width=22, anchor="w").pack(side="left")
    ttk.Scale(row, from_=0, to=100, variable=v_vol, orient="horizontal", length=200).pack(side="left")
    row2 = tk.Frame(v_inner, bg=theme()["card"])
    row2.pack(fill="x", pady=6)
    tk.Label(row2, text="Speech Rate:", font=("Segoe UI",10,"bold"),
             bg=theme()["card"], fg=theme()["text"], width=22, anchor="w").pack(side="left")
    ttk.Scale(row2, from_=50, to=300, variable=v_rate, orient="horizontal", length=200).pack(side="left")

    def save_settings():
        clinic_settings["name"]          = name_var.get().strip() or clinic_settings["name"]
        clinic_settings["max_daily"]     = int(max_var.get()) if max_var.get().isdigit() else clinic_settings["max_daily"]
        clinic_settings["open_time"]     = open_var.get()
        clinic_settings["close_time"]    = close_var.get()
        clinic_settings["font_size"]     = int(font_var.get()) if font_var.get().isdigit() else 12
        clinic_settings["high_contrast"] = hc_var.get()
        voice_settings["enabled"] = v_enabled.get()
        voice_settings["volume"]  = v_vol.get() / 100
        voice_settings["rate"]    = int(v_rate.get())
        for dept_key, prefix_var in prefix_vars.items():
            if prefix_var.get().strip():
                dept_prefix[dept_key] = prefix_var.get().strip().upper()
        add_audit("SETTINGS_CHANGED", f"Settings updated by {current_user['username']}")
        root.title(f"{clinic_settings['name']} — Queue Management System")
        show_notification("success","Settings Saved","All settings have been saved successfully.")

    make_btn(inner, "💾 Save Settings", save_settings, theme()["success"]).pack(pady=12)

    # ── User Management ───────────────────────────────────────
    u_card, u_inner = make_card(inner, "👥 User Management", 20, 16)
    u_card.pack(fill="x", pady=(0,12))

    # Table header
    hdr_row = tk.Frame(u_inner, bg=theme()["header_bg"])
    hdr_row.pack(fill="x", pady=(0,4))
    for col_text, col_w in [("Username", 16), ("Role", 20), ("Full Name", 24), ("Actions", 20)]:
        tk.Label(hdr_row, text=col_text, font=("Segoe UI", 10, "bold"),
                 bg=theme()["header_bg"], fg=theme()["text"],
                 width=col_w, anchor="w", padx=6, pady=6).pack(side="left")

    user_rows_frame = tk.Frame(u_inner, bg=theme()["card"])
    user_rows_frame.pack(fill="x")

    def refresh_user_table():
        for w in user_rows_frame.winfo_children():
            w.destroy()

        for uname, info in list(USERS.items()):
            is_self = (uname == current_user["username"])
            row_bg  = theme()["card"]

            row_fr = tk.Frame(user_rows_frame, bg=row_bg,
                              highlightbackground=theme()["border"], highlightthickness=1)
            row_fr.pack(fill="x", pady=2)

            tk.Label(row_fr, text=uname, font=("Segoe UI", 10, "bold"),
                     bg=row_bg, fg=theme()["accent"], width=16, anchor="w", padx=6).pack(side="left")
            tk.Label(row_fr, text=info["role"], font=("Segoe UI", 10),
                     bg=row_bg, fg=theme()["text"], width=20, anchor="w", padx=6).pack(side="left")
            tk.Label(row_fr, text=info["name"], font=("Segoe UI", 10),
                     bg=row_bg, fg=theme()["text_muted"], width=24, anchor="w", padx=6).pack(side="left")

            action_fr = tk.Frame(row_fr, bg=row_bg)
            action_fr.pack(side="left", padx=6, pady=4)

            # Force Logout button
            def make_logout_cmd(u, self_flag):
                def do_force_logout():
                    if self_flag:
                        show_notification("warning", "Cannot Logout Self",
                                          "You cannot force-logout your own active session.\n"
                                          "Use the Logout button in the sidebar instead.")
                        return
                    if messagebox.askyesno("Force Logout",
                                           f"Force logout user '{u}'?\n\n"
                                           "Their session will be invalidated immediately."):
                        # If that user is currently logged in, clear the session
                        if current_user["username"] == u:
                            current_user["username"] = None
                            current_user["role"]     = None
                            current_user["name"]     = None
                        add_audit("FORCE_LOGOUT", f"Admin force-logged-out user '{u}'")
                        show_notification("success", "Logged Out",
                                          f"User '{u}' has been logged out successfully.")
                return do_force_logout

            logout_btn = tk.Button(
                action_fr,
                text="🔒 Force Logout",
                font=("Segoe UI", 9, "bold"),
                bg=theme()["warning"], fg="white",
                relief="flat", cursor="hand2", padx=8, pady=4,
                command=make_logout_cmd(uname, is_self),
                state="disabled" if is_self else "normal",
            )
            logout_btn.pack(side="left", padx=(0, 6))

            # Delete User button
            def make_delete_cmd(u, role, self_flag):
                def do_delete():
                    if self_flag:
                        show_notification("error", "Cannot Delete Self",
                                          "You cannot delete your own account while logged in.")
                        return
                    if role == "Administrator":
                        # Count remaining admins
                        admin_count = sum(
                            1 for info_ in USERS.values()
                            if info_["role"] == "Administrator"
                        )
                        if admin_count <= 1:
                            show_notification("error", "Cannot Delete",
                                              "There must be at least one Administrator account.\n"
                                              "Create another admin first before deleting this one.")
                            return
                    if messagebox.askyesno(
                        "Delete User",
                        f"Permanently delete user '{u}' ({role})?\n\n"
                        "⚠ This action cannot be undone.",
                        icon="warning"
                    ):
                        del USERS[u]
                        add_audit("DELETE_USER", f"Admin deleted user '{u}' (role: {role})")
                        show_notification("success", "User Deleted",
                                          f"User '{u}' has been permanently deleted.")
                        refresh_user_table()
                return do_delete

            delete_btn = tk.Button(
                action_fr,
                text="🗑 Delete User",
                font=("Segoe UI", 9, "bold"),
                bg=theme()["error"], fg="white",
                relief="flat", cursor="hand2", padx=8, pady=4,
                command=make_delete_cmd(uname, info["role"], is_self),
                state="disabled" if is_self else "normal",
            )
            delete_btn.pack(side="left")

            if is_self:
                tk.Label(action_fr, text="  ← you", font=("Segoe UI", 9, "italic"),
                         bg=row_bg, fg=theme()["text_muted"]).pack(side="left", padx=4)

    refresh_user_table()

    # Add New User subsection
    new_card, new_inner = make_card(inner, "➕ Add New User", 20, 16)
    new_card.pack(fill="x", pady=(0, 12))

    def labeled_entry(le_parent, label, show=""):
        fr = tk.Frame(le_parent, bg=theme()["card"])
        fr.pack(side="left", padx=8)
        tk.Label(fr, text=label, font=("Segoe UI", 9, "bold"),
                 bg=theme()["card"], fg=theme()["text"], anchor="w").pack(fill="x")
        var = tk.StringVar()
        ent = tk.Entry(fr, textvariable=var, font=("Segoe UI", 11),
                       bg=theme()["entry_bg"], fg=theme()["entry_fg"],
                       relief="flat", highlightthickness=1,
                       highlightbackground=theme()["border"],
                       show=show, width=16)
        ent.pack(ipady=5)
        return var

    fields_row = tk.Frame(new_inner, bg=theme()["card"])
    fields_row.pack(fill="x", pady=(0, 8))

    nu_user_var  = labeled_entry(fields_row, "Username")
    nu_pass_var  = labeled_entry(fields_row, "Password", show="•")
    nu_name_var  = labeled_entry(fields_row, "Full Name")

    role_fr = tk.Frame(fields_row, bg=theme()["card"])
    role_fr.pack(side="left", padx=8)
    tk.Label(role_fr, text="Role", font=("Segoe UI", 9, "bold"),
             bg=theme()["card"], fg=theme()["text"], anchor="w").pack(fill="x")
    nu_role_var = tk.StringVar(value="Receptionist")
    ttk.Combobox(role_fr, textvariable=nu_role_var,
                 values=["Administrator", "Receptionist", "Doctor"],
                 state="readonly", width=16,
                 font=("Segoe UI", 11)).pack(ipady=4)

    nu_err_lbl = tk.Label(new_inner, text="", font=("Segoe UI", 9),
                          bg=theme()["card"], fg=theme()["error"])
    nu_err_lbl.pack(anchor="w")

    def add_new_user():
        uname = nu_user_var.get().strip().lower()
        pwd   = nu_pass_var.get().strip()
        name  = nu_name_var.get().strip()
        role  = nu_role_var.get()

        if not uname:
            nu_err_lbl.config(text="⚠ Username is required.")
            return
        if not pwd or len(pwd) < 4:
            nu_err_lbl.config(text="⚠ Password must be at least 4 characters.")
            return
        if not name:
            nu_err_lbl.config(text="⚠ Full name is required.")
            return
        if uname in USERS:
            nu_err_lbl.config(text=f"⚠ Username '{uname}' already exists.")
            return

        USERS[uname] = {"password": pwd, "role": role, "name": name}
        add_audit("ADD_USER", f"Admin created new user '{uname}' with role '{role}'")
        nu_err_lbl.config(text="")
        nu_user_var.set("")
        nu_pass_var.set("")
        nu_name_var.set("")
        nu_role_var.set("Receptionist")
        refresh_user_table()
        show_notification("success", "User Created",
                          f"✅ New user '{uname}' created successfully!\n"
                          f"Role: {role}\nName: {name}")

    make_btn(new_inner, "➕ Add User", add_new_user, theme()["success"]).pack(anchor="w", pady=(4, 0))


# ═══════════════════════════════════════════════════════════════
#  KEYBOARD SHORTCUTS
# ═══════════════════════════════════════════════════════════════

def setup_shortcuts():
    root.bind("<Control-d>", lambda _e: show_page("dashboard"))
    root.bind("<Control-r>", lambda _e: show_page("register") if current_user["role"] in ("Administrator","Receptionist") else None)
    root.bind("<Control-q>", lambda _e: show_page("queue"))
    root.bind("<Control-s>", lambda _e: show_page("search"))
    root.bind("<Control-m>", lambda _e: show_page("monitor"))
    root.bind("<Control-t>", lambda _e: toggle_theme())
    root.bind("<F11>",       lambda _e: root.attributes("-fullscreen", not root.attributes("-fullscreen")))
    root.bind("<Escape>",    lambda _e: root.attributes("-fullscreen", False))


# ═══════════════════════════════════════════════════════════════
#  SEED DEMO DATA  (optional, helps for demonstration)
# ═══════════════════════════════════════════════════════════════

def seed_demo_data():
    demo = [
        ("Aminata Koroma",  "32","Female","077-001-001","General Consultation","Normal"),  # spellchecker: disable-line
        ("Ibrahim Bangura", "67","Male",  "077-002-002","Pediatrics",          "Elderly"),  # spellchecker: disable-line
        ("Fatima Sesay",    "24","Female","077-003-003","Maternity",           "Normal"),  # spellchecker: disable-line
        ("Mohamed Kamara",  "45","Male",  "077-004-004","Dental",              "Emergency"),  # spellchecker: disable-line
        ("Mariama Turay",   "8", "Female","077-005-005","Pediatrics",          "Normal"),  # spellchecker: disable-line
        ("Sorie Conteh",    "55","Male",  "077-006-006","Laboratory",          "Normal"),  # spellchecker: disable-line
        ("Hawa Jalloh",     "30","Female","077-007-007","General Consultation","Normal"),  # spellchecker: disable-line
    ]
    statuses = ["Waiting","Waiting","Waiting","Serving","Called","Completed","Waiting"]
    for i, (name, age, gender, phone, dept, priority) in enumerate(demo):
        qno = get_next_queue_number(dept)
        doc = get_available_doctor(dept)
        p = {
            "id":           patient_id_counter[0],
            "queue_no":     qno,
            "name":         name,
            "age":          age,
            "gender":       gender,
            "phone":        phone,
            "address":      "Freetown, Sierra Leone",
            "department":   dept,
            "priority":     priority,
            "notes":        "",
            "arrival_time": f"{8+i:02d}:00:00",
            "date":         today_str(),
            "doctor":       doc,
            "status":       statuses[i],
            "end_time":     "09:00:00" if statuses[i]=="Completed" else "",
        }
        patients.append(p)
        patient_id_counter[0] += 1

    # Add demo audit logs
    add_audit("SYSTEM_START", "Application initialized with demo data")


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    seed_demo_data()

    # Configure root
    root.configure(bg="#1A3C6B")
    try:
        root.iconbitmap(default="")  # Use default icon
    except tk.TclError:
        pass

    # Style ttk
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    show_splash()
    root.mainloop()
