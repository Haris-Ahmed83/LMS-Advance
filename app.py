from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_from_directory
import sqlite3, hashlib, os, base64, uuid
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "comsets_portal_secret_2025_v4"
DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def teacher_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "teacher":
            return jsonify({"error": "Unauthorized"}), 403
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username","").strip()
        password = data.get("password","")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password_hash=?",
                          (username, hash_password(password))).fetchone()
        if user:
            db.execute("INSERT INTO login_logs (user_id,username,role,login_time) VALUES (?,?,?,?)",
                       (user["id"],user["username"],user["role"],datetime.now().isoformat()))
            db.commit()
            db.close()
            session.update({"user_id":user["id"],"username":user["username"],
                            "role":user["role"],"student_roll_no":user["student_roll_no"]})
            return jsonify({"success":True,"role":user["role"]})
        db.close()
        return jsonify({"success":False,"message":"Invalid username or password"})
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", role=session["role"], username=session["username"])

# ── Photo Upload ──────────────────────────────────────────────────────────────
@app.route("/api/student/<int:roll>/upload_photo", methods=["POST"])
@login_required
def upload_photo(roll):
    if session["role"] == "student" and session["student_roll_no"] != roll:
        return jsonify({"error":"Unauthorized"}), 403
    data = request.get_json()
    img_data = data.get("image_data","")
    if not img_data: return jsonify({"error":"No image"}), 400
    filename = f"profile_{roll}.jpg"
    if "," in img_data: img_data = img_data.split(",")[1]
    with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as f:
        f.write(base64.b64decode(img_data))
    db = get_db()
    db.execute("UPDATE student SET st_photo=? WHERE st_roll_no=?", (filename, roll))
    db.commit(); db.close()
    return jsonify({"success":True,"filename":filename})

@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ── Students ──────────────────────────────────────────────────────────────────
@app.route("/api/students")
@login_required
def api_students():
    db = get_db()
    # Teachers see all; students see all (read-only list for directory)
    rows = db.execute("SELECT * FROM student ORDER BY st_roll_no").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/student/<int:roll>")
@login_required
def api_student(roll):
    # Students can only get their own full data
    if session["role"] == "student" and session["student_roll_no"] != roll:
        return jsonify({"error":"Unauthorized"}), 403
    db = get_db()
    s = db.execute("SELECT * FROM student WHERE st_roll_no=?", (roll,)).fetchone()
    m = db.execute("SELECT * FROM student_marks WHERE st_roll_no=?", (roll,)).fetchone()
    db.close()
    if not s: return jsonify({"error":"Not found"}), 404
    return jsonify({"student":dict(s),"marks":dict(m) if m else {}})

@app.route("/api/student/<int:roll>/profile", methods=["PUT"])
@login_required
def api_update_profile(roll):
    # Students can only edit their own limited fields
    if session["role"] == "student" and session["student_roll_no"] != roll:
        return jsonify({"error":"Unauthorized"}), 403
    data = request.get_json()
    if session["role"] == "student":
        allowed = ["st_email","st_phone","st_address","st_bio","st_guardian_phone","st_emergency_contact"]
    else:
        allowed = ["st_name","st_father_name","st_department","st_semester","st_attendance",
                   "st_fees_status","st_gpa","st_course_enrollment","st_email","st_phone",
                   "st_address","st_blood_group","st_dob","st_cnic","st_nationality","st_religion",
                   "st_guardian_phone","st_emergency_contact","st_bio"]
    sets = ", ".join(f"{k}=?" for k in data if k in allowed)
    vals = [data[k] for k in data if k in allowed]
    if not sets: return jsonify({"error":"No valid fields"}), 400
    vals.append(roll)
    db = get_db()
    db.execute(f"UPDATE student SET {sets} WHERE st_roll_no=?", vals)
    db.commit(); db.close()
    return jsonify({"success":True})

@app.route("/api/student", methods=["POST"])
@login_required
@teacher_required
def api_add_student():
    data = request.get_json()
    db = get_db()
    try:
        db.execute('''INSERT INTO student (st_roll_no,st_name,st_father_name,st_department,st_semester,
            st_attendance,st_fees_status,st_gpa,st_course_enrollment,st_email,st_phone,st_address,
            st_blood_group,st_dob,st_cnic,st_nationality,st_religion,st_guardian_phone,st_emergency_contact)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (data["st_roll_no"],data["st_name"],data.get("st_father_name",""),data["st_department"],
             data["st_semester"],data.get("st_attendance",0),data.get("st_fees_status","Unpaid"),
             0,data.get("st_course_enrollment",""),data.get("st_email",""),data.get("st_phone",""),
             data.get("st_address",""),data.get("st_blood_group",""),data.get("st_dob",""),
             data.get("st_cnic",""),data.get("st_nationality","Pakistani"),data.get("st_religion","Islam"),
             data.get("st_guardian_phone",""),data.get("st_emergency_contact","")))
        db.execute("INSERT INTO student_marks (st_roll_no,st_name,english,urdu,math,biology,physics,total_marks,cgpa) VALUES (?,?,0,0,0,0,0,0,0)",
                   (data["st_roll_no"],data["st_name"]))
        first = data["st_name"].split()[0]
        username = f"{first.lower()}_{data['st_roll_no']}"
        password = f"{first}@{data['st_roll_no']}"
        db.execute("INSERT INTO users (username,password_hash,role,student_roll_no) VALUES (?,?,?,?)",
                   (username, hash_password(password), "student", data["st_roll_no"]))
        db.commit(); db.close()
        return jsonify({"success":True,"username":username,"password":password})
    except Exception as e:
        db.close()
        return jsonify({"error":str(e)}), 400

@app.route("/api/student/<int:roll>", methods=["DELETE"])
@login_required
@teacher_required
def api_delete_student(roll):
    db = get_db()
    for tbl in ["student","student_marks","users","library_loans","complaints",
                "fee_receipts","certificate_requests","attendance_log","messages"]:
        col = "student_roll_no" if tbl in ["users","library_loans","fee_receipts","certificate_requests","messages"] else "st_roll_no"
        if tbl == "users": col = "student_roll_no"
        db.execute(f"DELETE FROM {tbl} WHERE {col}=?", (roll,))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Marks ─────────────────────────────────────────────────────────────────────
@app.route("/api/marks")
@login_required
def api_all_marks():
    db = get_db()
    rows = db.execute("SELECT * FROM student_marks ORDER BY cgpa DESC").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/marks/<int:roll>", methods=["PUT"])
@login_required
@teacher_required
def api_update_marks(roll):
    data = request.get_json()
    eng=float(data.get("english",0)); urdu=float(data.get("urdu",0))
    math=float(data.get("math",0)); bio=float(data.get("biology",0)); phy=float(data.get("physics",0))
    total=eng+urdu+math+bio+phy; cgpa=round(total/500*4,2)
    db = get_db()
    db.execute("UPDATE student_marks SET english=?,urdu=?,math=?,biology=?,physics=?,total_marks=?,cgpa=? WHERE st_roll_no=?",
               (eng,urdu,math,bio,phy,total,cgpa,roll))
    db.execute("UPDATE student SET st_gpa=? WHERE st_roll_no=?", (cgpa,roll))
    db.commit(); db.close()
    return jsonify({"success":True,"total":total,"cgpa":cgpa})

# ── Stats ─────────────────────────────────────────────────────────────────────
@app.route("/api/stats")
@login_required
def api_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM student").fetchone()[0]
    paid = db.execute("SELECT COUNT(*) FROM student WHERE st_fees_status='Paid'").fetchone()[0]
    avg_cgpa = db.execute("SELECT AVG(cgpa) FROM student_marks").fetchone()[0] or 0
    avg_att = db.execute("SELECT AVG(st_attendance) FROM student").fetchone()[0] or 0
    top = db.execute("SELECT sm.st_name, sm.cgpa, s.st_department FROM student_marks sm JOIN student s ON sm.st_roll_no=s.st_roll_no ORDER BY sm.cgpa DESC LIMIT 5").fetchall()
    dept_counts = db.execute("SELECT st_department, COUNT(*) as cnt FROM student GROUP BY st_department").fetchall()
    recent_loans = db.execute("SELECT COUNT(*) FROM library_loans WHERE returned=0").fetchone()[0]
    open_complaints = db.execute("SELECT COUNT(*) FROM complaints WHERE status='Open'").fetchone()[0]
    pending_certs = db.execute("SELECT COUNT(*) FROM certificate_requests WHERE status='Pending'").fetchone()[0]
    unread_msgs = 0
    if session.get("role") == "student":
        roll = session.get("student_roll_no")
        unread_msgs = db.execute("SELECT COUNT(*) FROM messages WHERE student_roll_no=? AND is_read=0", (roll,)).fetchone()[0]
    db.close()
    return jsonify({"total_students":total,"fees_paid":paid,"fees_unpaid":total-paid,
                    "avg_cgpa":round(avg_cgpa,2),"avg_attendance":round(avg_att,1),
                    "top_students":[dict(r) for r in top],
                    "dept_counts":[dict(r) for r in dept_counts],
                    "active_loans":recent_loans,"open_complaints":open_complaints,
                    "pending_certs":pending_certs,"unread_messages":unread_msgs})

@app.route("/api/my_info")
@login_required
def api_my_info():
    if session["role"] == "teacher":
        return jsonify({"role":"teacher","username":session["username"]})
    roll = session["student_roll_no"]
    db = get_db()
    s = db.execute("SELECT * FROM student WHERE st_roll_no=?", (roll,)).fetchone()
    m = db.execute("SELECT * FROM student_marks WHERE st_roll_no=?", (roll,)).fetchone()
    unread = db.execute("SELECT COUNT(*) FROM messages WHERE student_roll_no=? AND is_read=0", (roll,)).fetchone()[0]
    db.close()
    return jsonify({"role":"student","student":dict(s) if s else {},"marks":dict(m) if m else {},"unread_messages":unread})

# ── Announcements ─────────────────────────────────────────────────────────────
@app.route("/api/announcements", methods=["GET","POST"])
@login_required
def api_announcements():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        db.execute("INSERT INTO announcements (title,body,priority,author,created_at) VALUES (?,?,?,?,?)",
                   (data["title"],data["body"],data.get("priority","normal"),session["username"],datetime.now().isoformat()))
        db.commit(); db.close()
        return jsonify({"success":True})
    rows = db.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 20").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/announcements/<int:aid>", methods=["DELETE"])
@login_required
@teacher_required
def api_delete_announcement(aid):
    db = get_db()
    db.execute("DELETE FROM announcements WHERE id=?", (aid,))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Timetable ─────────────────────────────────────────────────────────────────
@app.route("/api/timetable", methods=["GET","POST"])
@login_required
def api_timetable():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        db.execute("INSERT INTO timetable (day,time_slot,subject,teacher,room,department,semester) VALUES (?,?,?,?,?,?,?)",
                   (data["day"],data["time_slot"],data["subject"],data["teacher"],data.get("room",""),data["department"],data["semester"]))
        db.commit(); db.close()
        return jsonify({"success":True})
    dept = request.args.get("dept",""); sem = request.args.get("sem","")
    query = "SELECT * FROM timetable WHERE 1=1"; params = []
    if dept: query += " AND department=?"; params.append(dept)
    if sem: query += " AND semester=?"; params.append(sem)
    query += " ORDER BY CASE day WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 ELSE 6 END, time_slot"
    rows = db.execute(query, params).fetchall(); db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/timetable/<int:tid>", methods=["DELETE"])
@login_required
@teacher_required
def api_delete_timetable(tid):
    db = get_db()
    db.execute("DELETE FROM timetable WHERE id=?", (tid,))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Library ───────────────────────────────────────────────────────────────────
@app.route("/api/library", methods=["GET","POST"])
@login_required
def api_library():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        db.execute("INSERT INTO library (title,author,category,isbn,total,available,location,price) VALUES (?,?,?,?,?,?,?,?)",
                   (data["title"],data["author"],data.get("category","General"),data.get("isbn",""),
                    int(data.get("total",1)),int(data.get("total",1)),data.get("location",""),float(data.get("price",0))))
        db.commit(); db.close()
        return jsonify({"success":True})
    q = request.args.get("q","")
    if q:
        rows = db.execute("SELECT * FROM library WHERE title LIKE ? OR author LIKE ? OR category LIKE ?",
                          (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    else:
        rows = db.execute("SELECT * FROM library ORDER BY title").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/library/<int:book_id>", methods=["DELETE"])
@login_required
@teacher_required
def api_delete_book(book_id):
    db = get_db()
    db.execute("DELETE FROM library WHERE id=?", (book_id,))
    db.commit(); db.close()
    return jsonify({"success":True})

@app.route("/api/library/borrow/<int:book_id>", methods=["POST"])
@login_required
def api_borrow_book(book_id):
    roll = session.get("student_roll_no")
    if not roll: return jsonify({"error":"Students only"}), 403
    db = get_db()
    book = db.execute("SELECT * FROM library WHERE id=?", (book_id,)).fetchone()
    if not book or book["available"] == 0:
        db.close(); return jsonify({"error":"Book not available"}), 400
    # Check if student has unpaid library fine
    data = request.get_json() or {}
    db.execute("UPDATE library SET available=available-1 WHERE id=?", (book_id,))
    import datetime as dt
    due = (dt.date.today() + dt.timedelta(days=14)).isoformat()
    db.execute("INSERT INTO library_loans (book_id,st_roll_no,borrowed_at,due_date,fine_amount) VALUES (?,?,?,?,0)",
               (book_id, roll, date.today().isoformat(), due))
    db.commit(); db.close()
    return jsonify({"success":True,"due_date":due})

@app.route("/api/library/return/<int:loan_id>", methods=["POST"])
@login_required
def api_return_book(loan_id):
    roll = session.get("student_roll_no")
    db = get_db()
    loan = db.execute("SELECT * FROM library_loans WHERE id=?", (loan_id,)).fetchone()
    if not loan: db.close(); return jsonify({"error":"Loan not found"}), 404
    if session["role"] == "student" and loan["st_roll_no"] != roll:
        db.close(); return jsonify({"error":"Unauthorized"}), 403
    # Calculate fine if overdue
    import datetime as dt
    today = dt.date.today()
    due = dt.date.fromisoformat(loan["due_date"])
    fine = max(0, (today - due).days * 10)  # Rs.10/day fine
    db.execute("UPDATE library_loans SET returned=1, returned_at=?, fine_amount=? WHERE id=?",
               (today.isoformat(), fine, loan_id))
    db.execute("UPDATE library SET available=available+1 WHERE id=?", (loan["book_id"],))
    if fine > 0:
        # Add fine as pending payment
        db.execute("INSERT INTO fee_receipts (st_roll_no,amount,semester,fee_type,paid_on,receipt_no,status) VALUES (?,?,?,?,?,?,?)",
                   (loan["st_roll_no"], fine, "Current", "Library Fine",
                    today.isoformat(), f"FINE-{today.strftime('%Y%m%d')}-{loan_id}", "Pending"))
    db.commit(); db.close()
    return jsonify({"success":True,"fine":fine})

@app.route("/api/library/my_loans")
@login_required
def api_my_loans():
    roll = session.get("student_roll_no")
    if not roll: return jsonify([])
    db = get_db()
    rows = db.execute("SELECT ll.*,l.title,l.author,l.price FROM library_loans ll JOIN library l ON ll.book_id=l.id WHERE ll.st_roll_no=? AND ll.returned=0",
                      (roll,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/library/all_loans")
@login_required
@teacher_required
def api_all_loans():
    db = get_db()
    rows = db.execute("""SELECT ll.*,l.title,s.st_name FROM library_loans ll 
                         JOIN library l ON ll.book_id=l.id 
                         JOIN student s ON ll.st_roll_no=s.st_roll_no 
                         ORDER BY ll.borrowed_at DESC LIMIT 50""").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Library Fee Payment ───────────────────────────────────────────────────────
@app.route("/api/library/pay_fine/<int:loan_id>", methods=["POST"])
@login_required
def api_pay_fine(loan_id):
    roll = session.get("student_roll_no")
    db = get_db()
    db.execute("UPDATE fee_receipts SET status='Paid',paid_on=? WHERE receipt_no LIKE ? AND st_roll_no=?",
               (date.today().isoformat(), f"FINE-%-{loan_id}", roll))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Events ────────────────────────────────────────────────────────────────────
@app.route("/api/events", methods=["GET","POST"])
@login_required
def api_events():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        db.execute("INSERT INTO events (title,description,event_date,event_type,venue) VALUES (?,?,?,?,?)",
                   (data["title"],data.get("description",""),data["event_date"],data.get("event_type","general"),data.get("venue","")))
        db.commit(); db.close()
        return jsonify({"success":True})
    rows = db.execute("SELECT * FROM events ORDER BY event_date ASC").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Complaints ────────────────────────────────────────────────────────────────
@app.route("/api/complaints", methods=["GET","POST"])
@login_required
def api_complaints():
    db = get_db()
    if request.method == "POST":
        data = request.get_json()
        roll = session.get("student_roll_no")
        db.execute("INSERT INTO complaints (st_roll_no,username,category,subject,body,status,created_at) VALUES (?,?,?,?,?,?,?)",
                   (roll,session["username"],data.get("category","General"),data["subject"],data["body"],"Open",datetime.now().isoformat()))
        db.commit(); db.close()
        return jsonify({"success":True})
    if session["role"] == "teacher":
        rows = db.execute("SELECT c.*,s.st_name FROM complaints c LEFT JOIN student s ON c.st_roll_no=s.st_roll_no ORDER BY c.created_at DESC").fetchall()
    else:
        rows = db.execute("SELECT * FROM complaints WHERE st_roll_no=? ORDER BY created_at DESC",
                          (session.get("student_roll_no"),)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/complaints/<int:cid>/resolve", methods=["PUT"])
@login_required
@teacher_required
def api_resolve_complaint(cid):
    data = request.get_json()
    db = get_db()
    db.execute("UPDATE complaints SET status='Resolved',response=? WHERE id=?", (data.get("response",""), cid))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Fee Receipts ──────────────────────────────────────────────────────────────
@app.route("/api/fee_receipts", methods=["GET","POST"])
@login_required
def api_fee_receipts():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        receipt_no = data.get("receipt_no", f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        db.execute("INSERT INTO fee_receipts (st_roll_no,amount,semester,fee_type,paid_on,receipt_no,status) VALUES (?,?,?,?,?,?,?)",
                   (data["st_roll_no"],data["amount"],data["semester"],data.get("fee_type","Tuition"),
                    data.get("paid_on",date.today().isoformat()), receipt_no, "Paid"))
        db.execute("UPDATE student SET st_fees_status='Paid' WHERE st_roll_no=?", (data["st_roll_no"],))
        db.commit(); db.close()
        return jsonify({"success":True})
    if session["role"] == "teacher":
        rows = db.execute("SELECT fr.*,s.st_name FROM fee_receipts fr JOIN student s ON fr.st_roll_no=s.st_roll_no ORDER BY fr.paid_on DESC").fetchall()
    else:
        rows = db.execute("SELECT * FROM fee_receipts WHERE st_roll_no=? ORDER BY paid_on DESC",
                          (session.get("student_roll_no"),)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Student pays fee online ───────────────────────────────────────────────────
@app.route("/api/fee/pay", methods=["POST"])
@login_required
def api_pay_fee():
    roll = session.get("student_roll_no")
    if not roll: return jsonify({"error":"Students only"}), 403
    data = request.get_json()
    db = get_db()
    # Check existing unpaid
    existing = db.execute("SELECT id FROM fee_receipts WHERE st_roll_no=? AND semester=? AND fee_type=? AND status='Pending'",
                          (roll, data.get("semester",""), data.get("fee_type","Tuition"))).fetchone()
    if existing:
        db.execute("UPDATE fee_receipts SET status='Paid',paid_on=? WHERE id=?",
                   (date.today().isoformat(), existing["id"]))
    else:
        receipt_no = f"ONL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db.execute("INSERT INTO fee_receipts (st_roll_no,amount,semester,fee_type,paid_on,receipt_no,status) VALUES (?,?,?,?,?,?,?)",
                   (roll,data.get("amount",25000),data.get("semester","Current"),
                    data.get("fee_type","Tuition"),date.today().isoformat(),receipt_no,"Paid"))
    db.execute("UPDATE student SET st_fees_status='Paid' WHERE st_roll_no=?", (roll,))
    db.commit(); db.close()
    return jsonify({"success":True,"receipt_no":f"ONL-{datetime.now().strftime('%Y%m%d%H%M%S')}"})

# ── Messages (Teacher → Student) ──────────────────────────────────────────────
@app.route("/api/messages", methods=["GET","POST"])
@login_required
def api_messages():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        rolls = data.get("student_roll_nos", [])
        if not rolls:
            # Broadcast to all students
            rolls = [r["st_roll_no"] for r in db.execute("SELECT st_roll_no FROM student").fetchall()]
        for roll in rolls:
            db.execute("INSERT INTO messages (student_roll_no,sender,subject,body,sent_at,is_read) VALUES (?,?,?,?,?,0)",
                       (roll, session["username"], data.get("subject",""), data["body"], datetime.now().isoformat()))
        db.commit(); db.close()
        return jsonify({"success":True,"sent_to":len(rolls)})
    # GET
    if session["role"] == "teacher":
        rows = db.execute("SELECT m.*,s.st_name FROM messages m JOIN student s ON m.student_roll_no=s.st_roll_no ORDER BY m.sent_at DESC LIMIT 50").fetchall()
    else:
        roll = session.get("student_roll_no")
        rows = db.execute("SELECT * FROM messages WHERE student_roll_no=? ORDER BY sent_at DESC", (roll,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/messages/<int:mid>/read", methods=["PUT"])
@login_required
def api_mark_message_read(mid):
    db = get_db()
    db.execute("UPDATE messages SET is_read=1 WHERE id=?", (mid,))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Notifications ─────────────────────────────────────────────────────────────
@app.route("/api/notifications", methods=["GET","POST"])
@login_required
def api_notifications():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        db.execute("INSERT INTO notifications (title,body,role,st_roll_no,created_at) VALUES (?,?,?,?,?)",
                   (data["title"],data["body"],data.get("role","all"),data.get("st_roll_no"),datetime.now().isoformat()))
        db.commit(); db.close()
        return jsonify({"success":True})
    roll = session.get("student_roll_no")
    if session["role"] == "teacher":
        rows = db.execute("SELECT * FROM notifications WHERE role IN ('teacher','all') ORDER BY created_at DESC LIMIT 20").fetchall()
    else:
        rows = db.execute("SELECT * FROM notifications WHERE role IN ('student','all') ORDER BY created_at DESC LIMIT 20").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Certificates ──────────────────────────────────────────────────────────────
@app.route("/api/certificates", methods=["GET","POST"])
@login_required
def api_certificates():
    db = get_db()
    if request.method == "POST":
        roll = session.get("student_roll_no")
        if not roll: db.close(); return jsonify({"error":"Students only"}), 403
        data = request.get_json()
        db.execute("INSERT INTO certificate_requests (st_roll_no,cert_type,purpose,status,requested_at) VALUES (?,?,?,?,?)",
                   (roll, data["cert_type"], data.get("purpose",""), "Pending", datetime.now().isoformat()))
        db.commit(); db.close()
        return jsonify({"success":True})
    if session["role"] == "teacher":
        rows = db.execute("SELECT cr.*,s.st_name FROM certificate_requests cr JOIN student s ON cr.st_roll_no=s.st_roll_no ORDER BY cr.requested_at DESC").fetchall()
    else:
        rows = db.execute("SELECT * FROM certificate_requests WHERE st_roll_no=? ORDER BY requested_at DESC",
                          (session.get("student_roll_no"),)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/certificates/<int:cid>/approve", methods=["PUT"])
@login_required
@teacher_required
def api_approve_certificate(cid):
    db = get_db()
    db.execute("UPDATE certificate_requests SET status='Approved' WHERE id=?", (cid,))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Change Password ───────────────────────────────────────────────────────────
@app.route("/api/change_password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json()
    old_pw = data.get("old_password",""); new_pw = data.get("new_password","")
    if len(new_pw) < 6: return jsonify({"error":"Password too short"}), 400
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=? AND password_hash=?",
                      (session["user_id"], hash_password(old_pw))).fetchone()
    if not user: db.close(); return jsonify({"error":"Current password is incorrect"}), 400
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_pw), session["user_id"]))
    db.commit(); db.close()
    return jsonify({"success":True})

# ── Search ────────────────────────────────────────────────────────────────────
@app.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q","").strip()
    if len(q) < 2: return jsonify([])
    db = get_db()
    rows = db.execute("SELECT st_roll_no,st_name,st_department,st_semester FROM student WHERE st_name LIKE ? OR CAST(st_roll_no AS TEXT) LIKE ? LIMIT 8",
                      (f"%{q}%",f"%{q}%")).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Login Logs ────────────────────────────────────────────────────────────────
@app.route("/api/login_logs")
@login_required
@teacher_required
def api_login_logs():
    db = get_db()
    rows = db.execute("SELECT * FROM login_logs ORDER BY login_time DESC LIMIT 50").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Attendance ────────────────────────────────────────────────────────────────
@app.route("/api/attendance_log", methods=["GET","POST"])
@login_required
def api_attendance_log():
    db = get_db()
    if request.method == "POST":
        if session["role"] != "teacher": db.close(); return jsonify({"error":"Unauthorized"}), 403
        data = request.get_json()
        for entry in data.get("entries",[]):
            existing = db.execute("SELECT id FROM attendance_log WHERE st_roll_no=? AND att_date=? AND subject=?",
                                  (entry["roll"],entry["date"],entry["subject"])).fetchone()
            if existing:
                db.execute("UPDATE attendance_log SET status=? WHERE id=?", (entry["status"],existing["id"]))
            else:
                db.execute("INSERT INTO attendance_log (st_roll_no,att_date,subject,status) VALUES (?,?,?,?)",
                           (entry["roll"],entry["date"],entry["subject"],entry["status"]))
        db.commit(); db.close()
        return jsonify({"success":True})
    roll = request.args.get("roll", session.get("student_roll_no"))
    if session["role"] == "student":
        roll = session.get("student_roll_no")
    rows = db.execute("SELECT * FROM attendance_log WHERE st_roll_no=? ORDER BY att_date DESC LIMIT 50", (roll,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── Grades / Report Card ──────────────────────────────────────────────────────
@app.route("/api/report_card/<int:roll>")
@login_required
def api_report_card(roll):
    if session["role"] == "student" and session["student_roll_no"] != roll:
        return jsonify({"error":"Unauthorized"}), 403
    db = get_db()
    s = db.execute("SELECT * FROM student WHERE st_roll_no=?", (roll,)).fetchone()
    m = db.execute("SELECT * FROM student_marks WHERE st_roll_no=?", (roll,)).fetchone()
    att = db.execute("SELECT subject, COUNT(*) as total, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present FROM attendance_log WHERE st_roll_no=? GROUP BY subject", (roll,)).fetchall()
    db.close()
    return jsonify({"student":dict(s),"marks":dict(m) if m else {},"attendance_by_subject":[dict(a) for a in att]})

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        import setup_db
        setup_db.setup()
    app.run(debug=True, port=5000)

# ── Message Replies ──────────────────────────────────────────────────────────
@app.route("/api/messages/<int:mid>/replies", methods=["GET","POST"])
@login_required
def api_message_replies(mid):
    db = get_db()
    if request.method == "POST":
        data = request.get_json()
        body = data.get("body","").strip()
        if not body: db.close(); return jsonify({"error":"Empty reply"}), 400
        if session["role"] == "student":
            msg = db.execute("SELECT * FROM messages WHERE id=?", (mid,)).fetchone()
            if not msg or msg["student_roll_no"] != session.get("student_roll_no"):
                db.close(); return jsonify({"error":"Unauthorized"}), 403
        db.execute("INSERT INTO message_replies (message_id,sender,sender_role,body,sent_at) VALUES (?,?,?,?,?)",
                   (mid, session["username"], session["role"], body, datetime.now().isoformat()))
        if session["role"] == "student":
            db.execute("UPDATE messages SET is_read=1 WHERE id=?", (mid,))
        db.commit(); db.close()
        return jsonify({"success":True})
    replies = db.execute("SELECT * FROM message_replies WHERE message_id=? ORDER BY sent_at ASC", (mid,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in replies])

# ── Teacher Profile ──────────────────────────────────────────────────────────
@app.route("/api/teacher_profile", methods=["GET","PUT"])
@login_required
@teacher_required
def api_teacher_profile():
    db = get_db()
    if request.method == "PUT":
        data = request.get_json()
        allowed = ["full_name","email","phone","department","qualification","specialization",
                   "office_room","bio","experience_years","subjects_taught"]
        sets = ", ".join(f"{k}=?" for k in data if k in allowed)
        vals = [data[k] for k in data if k in allowed]
        if sets:
            vals.append(session["user_id"])
            existing = db.execute("SELECT id FROM teacher_profile WHERE user_id=?", (session["user_id"],)).fetchone()
            if existing:
                db.execute(f"UPDATE teacher_profile SET {sets} WHERE user_id=?", vals)
            else:
                db.execute("INSERT INTO teacher_profile (user_id,username) VALUES (?,?)",
                           (session["user_id"], session["username"]))
                db.execute(f"UPDATE teacher_profile SET {sets} WHERE user_id=?", vals)
        db.commit(); db.close()
        return jsonify({"success":True})
    profile = db.execute("SELECT * FROM teacher_profile WHERE user_id=?", (session["user_id"],)).fetchone()
    db.close()
    return jsonify(dict(profile) if profile else {"username": session["username"]})

@app.route("/api/teacher_profile/photo", methods=["POST"])
@login_required
@teacher_required
def api_teacher_photo():
    data = request.get_json()
    img_data = data.get("image_data","")
    if not img_data: return jsonify({"error":"No image"}), 400
    filename = f"teacher_{session['user_id']}.jpg"
    if "," in img_data: img_data = img_data.split(",")[1]
    with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as f:
        f.write(base64.b64decode(img_data))
    db = get_db()
    existing = db.execute("SELECT id FROM teacher_profile WHERE user_id=?", (session["user_id"],)).fetchone()
    if existing:
        db.execute("UPDATE teacher_profile SET photo=? WHERE user_id=?", (filename, session["user_id"]))
    else:
        db.execute("INSERT INTO teacher_profile (user_id,username,photo) VALUES (?,?,?)",
                   (session["user_id"], session["username"], filename))
    db.commit(); db.close()
    return jsonify({"success":True,"filename":filename})

# ── Student Public Profile (Teacher access) ──────────────────────────────────
@app.route("/api/student/<int:roll>/full_profile")
@login_required
@teacher_required
def api_student_full_profile(roll):
    db = get_db()
    s = db.execute("SELECT * FROM student WHERE st_roll_no=?", (roll,)).fetchone()
    m = db.execute("SELECT * FROM student_marks WHERE st_roll_no=?", (roll,)).fetchone()
    att = db.execute("SELECT subject, COUNT(*) as total, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present FROM attendance_log WHERE st_roll_no=? GROUP BY subject", (roll,)).fetchall()
    loans = db.execute("SELECT ll.*,l.title FROM library_loans ll JOIN library l ON ll.book_id=l.id WHERE ll.st_roll_no=? AND ll.returned=0", (roll,)).fetchall()
    complaints_count = db.execute("SELECT COUNT(*) FROM complaints WHERE st_roll_no=?", (roll,)).fetchone()[0]
    msgs = db.execute("SELECT * FROM messages WHERE student_roll_no=? ORDER BY sent_at DESC LIMIT 5", (roll,)).fetchall()
    db.close()
    if not s: return jsonify({"error":"Not found"}), 404
    return jsonify({"student":dict(s),"marks":dict(m) if m else {},"attendance":[dict(a) for a in att],
                    "active_loans":[dict(l) for l in loans],"complaints_count":complaints_count,
                    "recent_messages":[dict(m) for m in msgs]})
