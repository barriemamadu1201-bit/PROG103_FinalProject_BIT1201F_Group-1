CLINIC QUEUE MANAGEMENT SYSTEM — OVERVIEW
This is a desktop application built with Python and Tkinter (no database, no web server, no OOP classes — purely procedural). It manages patient queuing at a medical clinic, from arrival to discharge.
ARCHITECTURE
All data lives in in-memory Python lists and dicts — nothing is saved to disk between sessions. When the app closes, all patient data is gone. The five core data stores are:
•	patients — list of all patient records for the day
•	doctors — the 5 doctors and their statuses
•	USERS — login accounts
•	audit_logs — every action ever taken
•	dept_counters — queue number counters per department
USER ROLES & LOGIN
There are 3 roles, each with different access:
•	Administrator — full access to everything including Settings, Audit Log, and User Management
•	Receptionist — can register patients and view reports
•	Doctor — read-only access to queue, search, and monitor
The login screen supports a "Remember Me" toggle and a password show/hide button. After login, a splash screen plays and the main layout builds.
SYSTEM SCREENS 
1. Dashboard — summary stat cards (total patients, waiting, serving, completed, emergencies, avg wait time, available doctors, max capacity), a visual queue progress bar, a recent patients table, and a doctor availability grid.
2. Register Patient — form to admit a new patient. Collects name, age, gender, phone, address, department, priority (Normal / Elderly / Emergency), and notes. On submit it assigns a queue number (e.g. G001 for General, P001 for Pediatrics), auto-assigns the best available doctor, makes a voice announcement via text-to-speech, and offers to print a PDF ticket.
3. Queue Manager — the main operational screen. Shows today's queue sorted by priority (Emergency first, then Elderly, then Normal). Staff can:
Call Next — calls the top waiting patient by voice
Mark Serving — moves patient to "Serving", marks doctor as Busy
Mark Completed — ends the visit, frees up the doctor
Cancel — removes patient from active queue
Filter by status or department, sort by any column, export a ticket
4. Search — search patients by name, queue number, phone, or department. Shows full patient details on selection.
5. Live Monitor — a big-screen display (can go fullscreen) showing the currently-called queue number, next patient up, total waiting count, and a live clock. Refreshes every 2 seconds automatically. Designed to be displayed on a waiting room TV.
6. Doctors — shows each doctor's status (Available / Busy / Offline), patients served count, and active patients. Staff can manually change a doctor's status via dropdown. Below is a per-doctor patient list.
7. Reports — two tabs: Daily Report (summary stats + department breakdown, exportable as CSV, PDF, or TXT) and Doctor Report (patients served per doctor).
8. Audit Log (Admin only) — every action logged with timestamp, user, role, action type, and detail. Exportable as CSV.
9. Settings (Admin only) — edit clinic name, max daily patients, open/close times, font size, high contrast mode, queue number prefixes per department, and voice engine settings (enable/disable, volume, speed). Also has a full User Management section to add/delete users and force-logout sessions.
KEY FEATURES
Text-to-speech announcements when patients are called (uses pyttsx3, optional)
PDF ticket export for each patient (uses reportlab, optional) — includes queue number, name, department, doctor, and time
Priority queue sorting — Emergency patients always jump to the front, then Elderly, then Normal by arrival time
Dark/Light theme toggle that rebuilds the entire UI on the fly
Keyboard shortcuts — Ctrl+D (dashboard), Ctrl+R (register), Ctrl+Q (queue), Ctrl+S (search), Ctrl+T (toggle theme), F11 (fullscreen)
Demo data seeded on startup — 7 sample patients across different departments and statuses so the app looks populated immediately
