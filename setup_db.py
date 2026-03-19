import sqlite3, hashlib, os
DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def setup():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, role TEXT NOT NULL, student_roll_no INTEGER)''')

    c.execute('''CREATE TABLE student (st_id INTEGER PRIMARY KEY AUTOINCREMENT, st_roll_no INTEGER UNIQUE,
        st_name TEXT, st_father_name TEXT, st_department TEXT, st_semester TEXT, st_attendance REAL,
        st_fees_status TEXT, st_gpa REAL, st_course_enrollment TEXT, st_email TEXT, st_phone TEXT,
        st_address TEXT, st_photo TEXT DEFAULT '', st_blood_group TEXT DEFAULT '',
        st_dob TEXT DEFAULT '', st_cnic TEXT DEFAULT '', st_nationality TEXT DEFAULT 'Pakistani',
        st_religion TEXT DEFAULT 'Islam', st_guardian_phone TEXT DEFAULT '',
        st_emergency_contact TEXT DEFAULT '', st_bio TEXT DEFAULT '')''')

    c.execute('''CREATE TABLE student_marks (st_id INTEGER PRIMARY KEY AUTOINCREMENT,
        st_roll_no INTEGER UNIQUE, st_name TEXT, english REAL DEFAULT 0, urdu REAL DEFAULT 0,
        math REAL DEFAULT 0, biology REAL DEFAULT 0, physics REAL DEFAULT 0,
        total_marks REAL DEFAULT 0, cgpa REAL DEFAULT 0,
        FOREIGN KEY(st_roll_no) REFERENCES student(st_roll_no))''')

    c.execute('''CREATE TABLE announcements (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT,
        priority TEXT DEFAULT 'normal', author TEXT, created_at TEXT)''')

    c.execute('''CREATE TABLE timetable (id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, time_slot TEXT,
        subject TEXT, teacher TEXT, room TEXT, department TEXT, semester TEXT)''')

    c.execute('''CREATE TABLE library (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, author TEXT,
        category TEXT, isbn TEXT, total INTEGER DEFAULT 1, available INTEGER DEFAULT 1,
        location TEXT, price REAL DEFAULT 0)''')

    c.execute('''CREATE TABLE library_loans (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER,
        st_roll_no INTEGER, borrowed_at TEXT, due_date TEXT, returned INTEGER DEFAULT 0,
        returned_at TEXT DEFAULT '', fine_amount REAL DEFAULT 0)''')

    c.execute('''CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT,
        event_date TEXT, event_type TEXT, venue TEXT)''')

    c.execute('''CREATE TABLE complaints (id INTEGER PRIMARY KEY AUTOINCREMENT, st_roll_no INTEGER,
        username TEXT, category TEXT, subject TEXT, body TEXT, status TEXT DEFAULT 'Open',
        response TEXT DEFAULT '', created_at TEXT)''')

    c.execute('''CREATE TABLE fee_receipts (id INTEGER PRIMARY KEY AUTOINCREMENT, st_roll_no INTEGER,
        amount REAL, semester TEXT, fee_type TEXT, paid_on TEXT, receipt_no TEXT,
        status TEXT DEFAULT 'Paid')''')

    c.execute('''CREATE TABLE notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT,
        role TEXT, st_roll_no INTEGER, created_at TEXT)''')

    c.execute('''CREATE TABLE certificate_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, st_roll_no INTEGER,
        cert_type TEXT, purpose TEXT, status TEXT DEFAULT 'Pending', requested_at TEXT)''')

    c.execute('''CREATE TABLE login_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        username TEXT, role TEXT, login_time TEXT)''')

    c.execute('''CREATE TABLE attendance_log (id INTEGER PRIMARY KEY AUTOINCREMENT, st_roll_no INTEGER,
        att_date TEXT, subject TEXT, status TEXT)''')

    # NEW: Messages from teacher to students
    c.execute('''CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, student_roll_no INTEGER,
        sender TEXT, subject TEXT, body TEXT, sent_at TEXT, is_read INTEGER DEFAULT 0)''')

    # Teacher account
    c.execute("INSERT INTO users (username,password_hash,role) VALUES (?,?,?)",
              ("Hxrry", hash_password("Haris@123"), "teacher"))

    students = [
        (101,"Ahsan Raza","Raza Khan","Computer Science","3rd",88.5,"Paid",3.52,"OOP, Calculus-I, Physics","ahsan@comstest.edu.pk","0300-1234567","House 12, Abbottabad","B+","2002-03-15","42301-1234567-1"),
        (102,"Bilal Ahmed","Ahmed Nawaz","Computer Science","3rd",76.0,"Paid",3.10,"OOP, Calculus-I, Physics","bilal@comstest.edu.pk","0301-2345678","Street 5, Mansehra","A+","2002-05-20","42301-2345678-2"),
        (103,"Zara Malik","Tariq Malik","Mathematics","3rd",92.0,"Paid",3.78,"Algebra, Calculus-II, Stats","zara@comstest.edu.pk","0302-3456789","Colony 3, Haripur","O+","2001-11-10","42301-3456789-3"),
        (104,"Usman Tariq","Tariq Shah","Physics","3rd",65.5,"Unpaid",2.40,"Waves, Optics, Thermodynamics","usman@comstest.edu.pk","0303-4567890","Block B, Nowshera","A-","2002-07-22","42301-4567890-4"),
        (105,"Nadia Hussain","Hussain Bakhsh","English","4th",81.0,"Paid",3.25,"Literature, Linguistics, Grammar","nadia@comstest.edu.pk","0304-5678901","Sector 7, Peshawar","B-","2001-09-05","42301-5678901-5"),
        (106,"Hamza Sheikh","Sheikh Babar","Computer Science","4th",90.0,"Paid",3.85,"AI, DSA, Networks","hamza@comstest.edu.pk","0305-6789012","House 44, Rawalpindi","AB+","2001-02-28","42301-6789012-6"),
        (107,"Sana Qadir","Qadir Hussain","Biology","2nd",79.5,"Paid",3.00,"Botany, Zoology, Biochem","sana@comstest.edu.pk","0306-7890123","G-10, Islamabad","O-","2003-06-14","42301-7890123-7"),
        (108,"Faisal Mehmood","Mehmood Anwar","Mathematics","2nd",55.0,"Unpaid",2.10,"Calc-I, Geometry, Discrete Math","faisal@comstest.edu.pk","0307-8901234","Model Town, Lahore","B+","2003-01-30","42301-8901234-8"),
        (109,"Ayesha Noor","Noor Alam","Computer Science","5th",95.0,"Paid",3.95,"Machine Learning, FYP, Cloud","ayesha@comstest.edu.pk","0308-9012345","DHA Phase 2, Karachi","A+","2000-12-18","42301-9012345-9"),
        (110,"Kamran Ali","Ali Rehman","Physics","1st",60.0,"Paid",2.60,"Mechanics, Calculus-I, English","kamran@comstest.edu.pk","0309-0123456","Hayatabad, Peshawar","O+","2004-04-02","42301-0123456-0"),
        (111,"Maryam Shahid","Shahid Iqbal","English","5th",88.0,"Paid",3.60,"Advanced Grammar, Literature, FYP","maryam@comstest.edu.pk","0310-1234567","Clifton, Karachi","AB-","2000-08-25","42301-1234567-11"),
        (112,"Saad Farooq","Farooq Azam","Computer Science","2nd",73.0,"Paid",2.90,"Programming, Math, English","saad@comstest.edu.pk","0311-2345678","Gulberg, Lahore","B+","2003-10-12","42301-2345678-12"),
        (113,"Hira Baig","Baig Sarwar","Biology","4th",84.0,"Paid",3.40,"Genetics, Physiology, Biochem","hira@comstest.edu.pk","0312-3456789","F-8, Islamabad","A+","2001-03-07","42301-3456789-13"),
        (114,"Talha Waqas","Waqas Javed","Mathematics","1st",50.0,"Unpaid",1.95,"Pre-Calc, English, Physics","talha@comstest.edu.pk","0313-4567890","Satellite Town, RWP","O+","2004-07-19","42301-4567890-14"),
        (115,"Rabia Saleem","Saleem Chaudhry","Computer Science","3rd",87.0,"Paid",3.48,"OOP, DBMS, Networks","rabia@comstest.edu.pk","0314-5678901","Bahria Town, Islamabad","B-","2002-02-11","42301-5678901-15"),
        (116,"Omar Khalid","Khalid Mahmood","Physics","4th",78.0,"Paid",3.15,"Electromagnetism, Optics, Quantum","omar@comstest.edu.pk","0315-6789012","Township, Multan","A-","2001-05-29","42301-6789012-16"),
        (117,"Maira Aslam","Aslam Gul","English","2nd",91.5,"Paid",3.80,"Grammar, Composition, Lit-I","maira@comstest.edu.pk","0316-7890123","University Town, Peshawar","AB+","2003-11-03","42301-7890123-17"),
        (118,"Danial Khan","Khan Zaman","Computer Science","1st",68.0,"Paid",2.72,"Intro CS, Math, English","danial@comstest.edu.pk","0317-8901234","Ring Road, Peshawar","O-","2004-09-16","42301-8901234-18"),
        (119,"Amna Riaz","Riaz Ahmad","Biology","3rd",83.5,"Paid",3.35,"Cell Biology, Genetics, Chemistry","amna@comstest.edu.pk","0318-9012345","Cantt Area, Quetta","B+","2002-04-23","42301-9012345-19"),
        (120,"Yasir Iqbal","Iqbal Zafar","Mathematics","5th",70.0,"Unpaid",2.80,"Real Analysis, Topology, FYP","yasir@comstest.edu.pk","0319-0123456","Johar Town, Lahore","A+","2000-06-08","42301-0123456-20"),
    ]
    marks_data = [
        (101,"Ahsan Raza",85,78,90,82,88),(102,"Bilal Ahmed",72,68,74,70,76),
        (103,"Zara Malik",91,88,95,85,90),(104,"Usman Tariq",55,60,50,58,62),
        (105,"Nadia Hussain",80,85,75,78,82),(106,"Hamza Sheikh",92,88,95,90,87),
        (107,"Sana Qadir",76,80,72,78,74),(108,"Faisal Mehmood",48,55,52,50,46),
        (109,"Ayesha Noor",96,94,98,93,95),(110,"Kamran Ali",60,62,58,64,56),
        (111,"Maryam Shahid",88,90,84,86,89),(112,"Saad Farooq",70,74,68,72,76),
        (113,"Hira Baig",82,86,80,84,88),(114,"Talha Waqas",45,52,48,50,44),
        (115,"Rabia Saleem",84,80,88,86,82),(116,"Omar Khalid",76,78,74,72,80),
        (117,"Maira Aslam",90,94,88,92,86),(118,"Danial Khan",65,68,62,70,60),
        (119,"Amna Riaz",80,84,78,82,86),(120,"Yasir Iqbal",68,72,66,70,74),
    ]
    for s in students:
        roll,name,father,dept,sem,att,fees,gpa,courses,email,phone,addr,blood,dob,cnic = s
        c.execute('''INSERT INTO student (st_roll_no,st_name,st_father_name,st_department,st_semester,
            st_attendance,st_fees_status,st_gpa,st_course_enrollment,st_email,st_phone,st_address,
            st_blood_group,st_dob,st_cnic) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (roll,name,father,dept,sem,att,fees,gpa,courses,email,phone,addr,blood,dob,cnic))
    for m in marks_data:
        roll,name,eng,urdu,math,bio,phy = m
        total=eng+urdu+math+bio+phy; cgpa=round(total/500*4,2)
        c.execute("INSERT INTO student_marks (st_roll_no,st_name,english,urdu,math,biology,physics,total_marks,cgpa) VALUES (?,?,?,?,?,?,?,?,?)",
                  (roll,name,eng,urdu,math,bio,phy,total,cgpa))

    logins = [(101,"ahsan_101","Ahsan@101"),(102,"bilal_102","Bilal@102"),(103,"zara_103","Zara@103"),
              (104,"usman_104","Usman@104"),(105,"nadia_105","Nadia@105"),(106,"hamza_106","Hamza@106"),
              (107,"sana_107","Sana@107"),(108,"faisal_108","Faisal@108"),(109,"ayesha_109","Ayesha@109"),
              (110,"kamran_110","Kamran@110"),(111,"maryam_111","Maryam@111"),(112,"saad_112","Saad@112"),
              (113,"hira_113","Hira@113"),(114,"talha_114","Talha@114"),(115,"rabia_115","Rabia@115"),
              (116,"omar_116","Omar@116"),(117,"maira_117","Maira@117"),(118,"danial_118","Danial@118"),
              (119,"amna_119","Amna@119"),(120,"yasir_120","Yasir@120")]
    for roll,uname,pwd in logins:
        c.execute("INSERT INTO users (username,password_hash,role,student_roll_no) VALUES (?,?,?,?)",
                  (uname,hash_password(pwd),"student",roll))

    announcements = [
        ("📅 Mid-Term Exams Schedule","Mid-term examinations for all departments will be held from July 14-18, 2025. Students must bring their university ID cards.","urgent","Hxrry"),
        ("🏫 New Computer Lab Inauguration","The state-of-the-art Computer Lab C-205 has been inaugurated with 40 workstations. Students can book slots through the portal.","high","Hxrry"),
        ("📚 Library Extended Hours","Library will remain open until 9 PM during exam season. Digital resources are now accessible 24/7.","normal","Hxrry"),
        ("🎓 Convocation Ceremony 2025","Annual convocation ceremony will be held on August 10, 2025. All graduating students must register by July 30.","high","Hxrry"),
        ("💉 Free Health Camp","A free health camp is organized on July 5, 2025 in the university auditorium.","normal","Hxrry"),
    ]
    for title,body,priority,author in announcements:
        c.execute("INSERT INTO announcements (title,body,priority,author,created_at) VALUES (?,?,?,?,?)",
                  (title,body,priority,author,"2025-06-28T09:00:00"))

    timetable = [
        ("Monday","08:00-09:30","Object Oriented Programming","Dr. Hassan Ali","CS-101","Computer Science","3rd"),
        ("Monday","09:45-11:15","Calculus-I","Dr. Sadia Naz","MATH-201","Computer Science","3rd"),
        ("Monday","11:30-13:00","Physics Lab","Dr. Rashid Khan","PHY-LAB","Computer Science","3rd"),
        ("Tuesday","08:00-09:30","Data Structures","Prof. Imran Sher","CS-102","Computer Science","3rd"),
        ("Tuesday","09:45-11:15","English Communication","Ms. Amina Bukhari","ENG-101","Computer Science","3rd"),
        ("Wednesday","08:00-09:30","Object Oriented Programming","Dr. Hassan Ali","CS-101","Computer Science","3rd"),
        ("Wednesday","09:45-11:15","Discrete Mathematics","Dr. Sadia Naz","MATH-202","Computer Science","3rd"),
        ("Thursday","08:00-09:30","Data Structures","Prof. Imran Sher","CS-102","Computer Science","3rd"),
        ("Thursday","09:45-11:15","Physics","Dr. Rashid Khan","PHY-201","Computer Science","3rd"),
        ("Friday","08:00-09:30","CS Lab","Prof. Imran Sher","CS-LAB","Computer Science","3rd"),
        ("Friday","09:45-11:15","Islamic Studies","Prof. Zafar","ISL-101","Computer Science","3rd"),
        ("Monday","08:00-09:30","Algebra","Dr. Khalid Mehmood","MATH-101","Mathematics","3rd"),
        ("Tuesday","08:00-09:30","Calculus-II","Dr. Sadia Naz","MATH-202","Mathematics","3rd"),
        ("Wednesday","08:00-09:30","Statistics","Prof. Raheela","STAT-101","Mathematics","3rd"),
    ]
    for row in timetable:
        c.execute("INSERT INTO timetable (day,time_slot,subject,teacher,room,department,semester) VALUES (?,?,?,?,?,?,?)",row)

    books = [
        ("Introduction to Algorithms","Cormen, Leiserson","Computer Science","978-0-262-03384-8",5,4,"CS Section A",1200),
        ("Data Structures Using C","Tanenbaum","Computer Science","978-0-13-301009-6",3,3,"CS Section B",950),
        ("Calculus: Early Transcendentals","James Stewart","Mathematics","978-1-285-74155-0",4,2,"Math Section",1500),
        ("University Physics","Young & Freedman","Physics","978-0-133-97200-4",6,5,"Physics Section",1800),
        ("English Grammar in Use","Raymond Murphy","English","978-0-521-18906-4",8,7,"English Section",600),
        ("Artificial Intelligence","Russell & Norvig","Computer Science","978-0-136-04259-4",3,2,"CS Section A",2200),
        ("Operating System Concepts","Silberschatz","Computer Science","978-1-119-32091-3",4,3,"CS Section B",1600),
        ("Linear Algebra","Gilbert Strang","Mathematics","978-0-980-23272-4",3,3,"Math Section",1100),
        ("Molecular Biology of the Cell","Alberts et al.","Biology","978-0-815-34464-5",4,4,"Bio Section",2500),
        ("Pakistan Studies","Dr. Muhammad Sarwar","Social Sciences","978-9-694-08067-3",10,9,"Ref Section",400),
        ("Islamic Studies","Dr. Hamid","Islamic Studies","978-9-697-27034-5",6,6,"Ref Section",350),
        ("Thermodynamics","Cengel & Boles","Physics","978-0-073-39174-7",3,2,"Physics Section",1900),
    ]
    for b in books:
        c.execute("INSERT INTO library (title,author,category,isbn,total,available,location,price) VALUES (?,?,?,?,?,?,?,?)",b)

    events = [
        ("Annual Sports Week","Inter-department sports competition","2025-07-15","sports","University Sports Complex"),
        ("Tech Fest 2025","Annual technology festival with project exhibitions","2025-07-22","academic","Main Auditorium"),
        ("Seminar: AI in Healthcare","Guest lecture by Dr. Fahad Mirza from NUST","2025-07-08","seminar","Lecture Hall B"),
        ("Result Announcement - Spring 2025","Spring semester results will be announced","2025-07-01","academic","Online Portal"),
        ("Last Date: Fee Submission","Last date for summer semester fee submission","2025-07-05","deadline","Finance Office"),
        ("National Day Celebration","Pakistan Independence Day celebration","2025-08-14","cultural","Main Ground"),
    ]
    for e in events:
        c.execute("INSERT INTO events (title,description,event_date,event_type,venue) VALUES (?,?,?,?,?)",e)

    paid_rolls = [101,102,103,105,106,107,109,110,111,112,113,115,116,117,118,119]
    for i,roll in enumerate(paid_rolls):
        c.execute("INSERT INTO fee_receipts (st_roll_no,amount,semester,fee_type,paid_on,receipt_no,status) VALUES (?,?,?,?,?,?,?)",
                  (roll,25000,"Spring 2025","Tuition","2025-01-15",f"REC-2025-{1000+i}","Paid"))

    notifs = [
        ("🔔 Portal Update","New features added: Messages, Library fines, Online fee payment now live!","all",None),
        ("⚠️ Fee Reminder","Students with unpaid fees must clear dues before July 10, 2025.","student",None),
        ("📋 Attendance Alert","Students below 75% attendance will not be allowed in exams.","student",None),
        ("📝 Staff Meeting","Monthly staff meeting scheduled for July 3, 2025 at 10 AM.","teacher",None),
    ]
    for title,body,role,roll in notifs:
        c.execute("INSERT INTO notifications (title,body,role,st_roll_no,created_at) VALUES (?,?,?,?,?)",
                  (title,body,role,roll,"2025-06-28T08:00:00"))

    # Seed sample messages from teacher to students
    messages = [
        (101,"Hxrry","Exam Reminder","Dear Ahsan, your mid-term exam for OOP is on July 14. Please prepare Chapter 5-8."),
        (109,"Hxrry","FYP Meeting","Dear Ayesha, your FYP presentation is scheduled for July 20 at 10 AM in Room CS-301."),
        (104,"Hxrry","Fee Notice","Dear Usman, your semester fee is still unpaid. Please clear it before July 10 to avoid fine."),
        (108,"Hxrry","Academic Warning","Dear Faisal, your attendance is below 75% in Math. Attend all classes to be eligible for exams."),
        (114,"Hxrry","Fee Notice","Dear Talha, please submit your fee before the deadline to continue enrollment."),
    ]
    for roll,sender,subject,body in messages:
        c.execute("INSERT INTO messages (student_roll_no,sender,subject,body,sent_at,is_read) VALUES (?,?,?,?,?,0)",
                  (roll,sender,subject,body,"2025-06-28T10:00:00"))

    # Seed some attendance
    import datetime as dt
    subjects = ["OOP","Calculus-I","Physics","Data Structures","English"]
    for roll in [101,102,106,115,109]:
        for i,subj in enumerate(subjects):
            for day_offset in range(10):
                att_date = (dt.date(2025,6,20) + dt.timedelta(days=day_offset)).isoformat()
                status = "Present" if (day_offset + i) % 5 != 0 else "Absent"
                c.execute("INSERT INTO attendance_log (st_roll_no,att_date,subject,status) VALUES (?,?,?,?)",
                          (roll,att_date,subj,status))

    conn.commit()
    conn.close()
    print("✅ COMSTEST University portal v4 database ready!")

if __name__ == "__main__":
    setup()

def add_new_tables():
    """Add v5 tables if not exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS message_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        sender_role TEXT NOT NULL,
        body TEXT NOT NULL,
        sent_at TEXT NOT NULL,
        FOREIGN KEY(message_id) REFERENCES messages(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        full_name TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        department TEXT DEFAULT 'Computer Science',
        qualification TEXT DEFAULT '',
        specialization TEXT DEFAULT '',
        office_room TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        experience_years INTEGER DEFAULT 0,
        subjects_taught TEXT DEFAULT '',
        photo TEXT DEFAULT '')''')
    conn.commit()
    conn.close()

def add_new_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS message_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INTEGER NOT NULL,
        sender TEXT NOT NULL, sender_role TEXT NOT NULL,
        body TEXT NOT NULL, sent_at TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE,
        username TEXT, full_name TEXT DEFAULT '', email TEXT DEFAULT '',
        phone TEXT DEFAULT '', department TEXT DEFAULT 'Computer Science',
        qualification TEXT DEFAULT '', specialization TEXT DEFAULT '',
        office_room TEXT DEFAULT '', bio TEXT DEFAULT '',
        experience_years INTEGER DEFAULT 0, subjects_taught TEXT DEFAULT '',
        photo TEXT DEFAULT '')''')
    conn.commit(); conn.close()
    print("✅ v5 tables added!")

if __name__ == "__main__":
    setup()
    add_new_tables()
