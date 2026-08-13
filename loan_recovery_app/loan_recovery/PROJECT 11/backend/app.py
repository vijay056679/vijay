import os
import json
import datetime
import re
import csv
import io
import sqlite3
import urllib.error
import urllib.request
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import numpy as np

# NLP and ML Libraries
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_environment_file(path):
    """Load simple KEY=value pairs without adding a runtime dependency."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_environment_file(os.path.join(os.path.dirname(BASE_DIR), '.env'))
KB_PATH = os.path.join(BASE_DIR, 'kb.json')
DB_PATH = os.path.join(BASE_DIR, 'database.json')
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'college_enquiry.db')

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(BASE_DIR), 'frontend'), static_url_path='')
CORS(app)  # Enable Cross-Origin Resource Sharing

COURSE_SPECIFIC_KB = [
    {
        "question": "When do admissions start for MCA?",
        "answer": "MCA admissions start on July 1. Students should complete entrance/CAP registration and document verification as per the university admission schedule.",
        "category": "MCA Course Details"
    },
    {
        "question": "What is the admission procedure for the MCA course?",
        "answer": "MCA admission is handled through the applicable entrance/CAP process. Candidates should register online, submit entrance details, upload documents, attend counseling if required, and confirm admission by paying the prescribed fees.",
        "category": "MCA Course Details"
    },
    {
        "question": "What are the eligibility criteria for MCA admissions?",
        "answer": "For MCA, candidates must have a relevant bachelor's degree such as BCA, BSc IT, BSc CS, or equivalent, with the required minimum percentage, and Mathematics at 10+2 or graduation level as per university norms.",
        "category": "MCA Course Details"
    },
    {
        "question": "What core subjects are covered in the MCA curriculum?",
        "answer": "The MCA curriculum focuses on application development, advanced programming, database management, web technologies, software engineering, cloud computing, AI, and project work.",
        "category": "MCA Course Details"
    },
    {
        "question": "What is the fee structure for the MCA program?",
        "answer": "The MCA fee structure is maintained separately from MSc(Cs). Students should check the latest MCA tuition, examination, laboratory, and development fees with the department or accounts office before admission.",
        "category": "MCA Course Details"
    },
    {
        "question": "What are the placement statistics for MCA graduates?",
        "answer": "MCA placement information is tracked separately because the course has its own recruitment profile. MCA students are usually considered for software development, application engineering, database, QA, and IT support roles.",
        "category": "MCA Course Details"
    },
    {
        "question": "When do admissions start for MSc(Cs)?",
        "answer": "MSc(Cs) admissions start on June 15. Students should follow the MSc(Cs) department admission notice because its admission dates and process can differ from MCA.",
        "category": "MSc(Cs) Course Details"
    },
    {
        "question": "What is the admission procedure for MSc(Cs)?",
        "answer": "MSc(Cs) admission is processed separately from MCA. Applicants should submit the MSc(Cs) application form, required marksheets and certificates, complete department verification, and confirm admission according to the MSc(Cs) schedule.",
        "category": "MSc(Cs) Course Details"
    },
    {
        "question": "What are the eligibility criteria for MSc(Cs) admissions?",
        "answer": "For MSc(Cs), candidates usually need a bachelor's degree with Computer Science, Computer Applications, IT, Mathematics, or another approved related subject, with the minimum percentage required by the university.",
        "category": "MSc(Cs) Course Details"
    },
    {
        "question": "What core subjects are covered in the MSc(Cs) curriculum?",
        "answer": "The MSc(Cs) curriculum focuses on computer science foundations, algorithms, operating systems, database systems, networks, software engineering, data science electives, and research/project work.",
        "category": "MSc(Cs) Course Details"
    },
    {
        "question": "What is the fee structure for MSc(Cs)?",
        "answer": "The MSc(Cs) fee structure is separate from MCA. Students should check the latest MSc(Cs) tuition, examination, laboratory, and development fees with the department or accounts office before admission.",
        "category": "MSc(Cs) Course Details"
    },
    {
        "question": "What are the placement statistics for MSc(Cs) graduates?",
        "answer": "MSc(Cs) placement information is tracked separately from MCA. MSc(Cs) students are usually considered for software development, data analysis, testing, teaching assistantship, research, and IT support roles.",
        "category": "MSc(Cs) Course Details"
    },
    {
        "question": "What are the documents required for MCA admission?",
        "answer": "The documents required for MCA admission include: 1. Entrance Exam Score Card (CAP/PGCET/etc.), 2. 10th and 12th Marksheets and Passing Certificates, 3. Graduation Marksheets and Degree Certificate, 4. Transfer Certificate (TC) and Migration Certificate, 5. Caste/Category Certificate (if applicable), 6. Passport-size photographs and Identity Proof (Aadhaar/PAN).",
        "category": "MCA Course Details",
        "kannada_question": "MCA ಪ್ರವೇಶಕ್ಕೆ ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು ಯಾವುವು?",
        "kannada_answer": "MCA ಪ್ರವೇಶಕ್ಕೆ ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು: 1. ಪ್ರವೇಶ ಪರೀಕ್ಷೆಯ ಅಂಕಪಟ್ಟಿ (CAP/PGCET/ಇತ್ಯಾದಿ), 2. 10ನೇ ಮತ್ತು 12ನೇ ತರಗತಿಯ ಅಂಕಪಟ್ಟಿಗಳು ಮತ್ತು ಉತ್ತೀರ್ಣ ಪ್ರಮಾಣಪತ್ರಗಳು, 3. ಪದವಿ ಅಂಕಪಟ್ಟಿಗಳು ಮತ್ತು ಪದವಿ ಪ್ರಮಾಣಪತ್ರ, 4. ವರ್ಗಾವಣೆ ಪ್ರಮಾಣಪತ್ರ (TC) ಮತ್ತು ವಲಸೆ ಪ್ರಮಾಣಪತ್ರ, 5. ಜಾತಿ/ವರ್ಗ ಪ್ರಮಾಣಪತ್ರ (ಅನ್ವಯಿಸಿದರೆ), 6. ಪಾಸ್‌ಪೋರ್ಟ್ ಅಳತೆಯ ಭಾವಚಿತ್ರಗಳು ಮತ್ತು ಗುರುತಿನ ಚೀಟಿ (ಆಧಾರ್/ಪ್ಯಾನ್)."
    },
    {
        "question": "What are the documents required for MSc(Cs) admission?",
        "answer": "The documents required for MSc(Cs) admission include: 1. Graduation Marksheets (BSc CS/BCA/etc. marksheets), 2. 10th and 12th Marksheets and Passing Certificates, 3. Transfer Certificate (TC) and Migration Certificate, 4. Caste/Category Certificate (if applicable), 5. Passport-size photographs and Identity Proof (Aadhaar/PAN).",
        "category": "MSc(Cs) Course Details",
        "kannada_question": "MSc(Cs) ಪ್ರವೇಶಕ್ಕೆ ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು ಯಾವುವು?",
        "kannada_answer": "MSc(Cs) ಪ್ರವೇಶಕ್ಕೆ ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು: 1. ಪದವಿ ಅಂಕಪಟ್ಟಿಗಳು (BSc CS/BCA/ಇತ್ಯಾದಿ ಅಂಕಪಟ್ಟಿಗಳು), 2. 10ನೇ ಮತ್ತು 12ನೇ ತರಗತಿಯ ಅಂಕಪಟ್ಟಿಗಳು ಮತ್ತು ಉತ್ತೀರ್ಣ ಪ್ರಮಾಣಪತ್ರಗಳು, 3. ವರ್ಗಾವಣೆ ಪ್ರಮಾಣಪತ್ರ (TC) ಮತ್ತು ವಲಸೆ ಪ್ರಮಾಣಪತ್ರ, 4. ಜಾತಿ/ವರ್ಗ ಪ್ರಮಾಣಪತ್ರ (ಅನ್ವಯಿಸಿದರೆ), 5. ಪಾಸ್‌ಪೋರ್ಟ್ ಅಳತೆಯ ಭಾವಚಿತ್ರಗಳು ಮತ್ತು ಗುರುತಿನ ಚೀಟಿ (ಆಧಾರ್/ಪ್ಯಾನ್)."
    }
]

@app.route('/')
def index():
    return app.send_static_file('home1.html')

@app.route('/dashboard')
def dashboard():
    return app.send_static_file('index.html')

@app.route('/admin-login')
def admin_login_page():
    return app.send_static_file('admin_login.html')

#  required NLTK packages
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except Exception as e:
    print(f"Warning: NLTK downloading or importing failed: {e}. Using manual fallback.")
    NLTK_AVAILABLE = False

# Fallback stop words list
FALLBACK_STOPWORDS = {
    "what", "is", "the", "for", "of", "a", "an", "to", "in", "on", "at", 
    "how", "do", "i", "can", "you", "we", "are", "about", "any", "please", "query",
    "me", "my", "this", "that", "it", "there", "their", "them", "then", "with", "have"
}

# Multilingual Kannada Dictionary Mapping
KANNADA_DICT = {
    "ಪ್ರವೇಶ": "admission",
    "ಅರ್ಹತೆ": "eligibility",
    "ಶುಲ್ಕ": "fee",
    "ಶುಲ್ಕಗಳು": "fees",
    "ಉದ್ಯೋಗ": "placement",
    "ವಸತಿ": "hostel",
    "ಹಾಸ್ಟೆಲ್": "hostel",
    "ಗ್ರಂಥಾಲಯ": "library",
    "ಶಿಕ್ಷಕರು": "faculty",
    "ಪರೀಕ್ಷೆ": "exam",
    "ಪರೀಕ್ಷೆಗಳು": "exams",
    "ಸಂಪರ್ಕ": "contact",
    "ವಿಷಯಗಳು": "subjects",
    "ಅವಧಿ": "duration",
    "ಸ್ಕಾಲರ್‌ಶಿಪ್": "scholarship",
    "ಸ್ಕಾಲರ್‌ಶಿಪ್‌ಗಳು": "scholarships",
    "ವೇಳಾಪಟ್ಟಿ": "calendar",
    "ಊಟ": "mess",
    "ಹಣ": "fees",
    "ಮಾಹಿತಿ": "information",
    "ಕೊಠಡಿ": "room",
    "ಕೊಠಡಿಗಳು": "rooms",
    "ರಚನೆ": "structure",
    "ಪ್ರಕ್ರಿಯೆ": "procedure",
    "ಅವಕಾಶ": "placements",
    "ಕಾಲೇಜು": "college",
    "ಕೋರ್ಸ್": "course",
    "ಕೋರ್ಸ್‌ಗಳು": "courses",
    "ಶೈಕ್ಷಣಿಕ": "academic",
    "ಕಛೇರಿ": "office",
    "ದೂರವಾಣಿ": "number",
    "ಫೋನ್": "phone",
    "ಇಮೇಲ್": "email"
}

# Synonym Handling mappings
SYNONYMS = {
    "fee": ["fees", "charge", "charges", "cost", "costs", "price", "prices", "expense", "expenses", "tuition", "payment", "payments"],
    "admission": ["admissions", "admit", "apply", "applying", "entry", "join", "joining", "registration", "register", "enroll", "enrollment"],
    "placement": ["placements", "job", "jobs", "recruit", "recruiter", "recruiters", "recruitment", "hire", "hiring", "company", "companies", "salary", "package", "packages"],
    "hostel": ["hostels", "accommodation", "room", "rooms", "stay", "mess", "canteen", "lodging"],
    "course": ["courses", "syllabus", "subject", "subjects", "curriculum", "study", "program", "programme"],
    "scholarship": ["scholarships", "concession", "financial", "aid", "merit"],
    "library": ["libraries", "book", "books", "journal", "journals", "reading"],
    "faculty": ["faculties", "teacher", "teachers", "professor", "professors", "staff", "hod"],
    "exam": ["exams", "examination", "examinations", "test", "tests", "date", "dates"],
    "contact": ["contacts", "call", "phone", "email", "address", "number", "numbers", "office", "location"]
}

# Flattened synonym map for quick O(1) lookup
SYNONYM_MAP = {}
for canonical, variants in SYNONYMS.items():
    for v in variants:
        SYNONYM_MAP[v] = canonical

# Global edit distance vocab
VOCABULARY = set()

# Helper for edit distance
def get_edit_distance(s1, s2):
    if NLTK_AVAILABLE:
        try:
            return nltk.edit_distance(s1, s2)
        except Exception:
            pass
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

# ----------------- NLP Helper Functions -----------------

def preprocess_text(text):
    if not text:
        return ""
    
    text = text.lower()
    
    tokens = []
    if NLTK_AVAILABLE:
        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = re.findall(r'\b\w+\b', text)
    else:
        tokens = re.findall(r'\b\w+\b', text)
        
    stop_words = set()
    if NLTK_AVAILABLE:
        try:
            stop_words = set(stopwords.words('english'))
        except Exception:
            stop_words = FALLBACK_STOPWORDS
    else:
        stop_words = FALLBACK_STOPWORDS
        
    filtered_tokens = [w for w in tokens if w not in stop_words and w.isalnum()]
    
    if VOCABULARY:
        corrected_tokens = []
        for w in filtered_tokens:
            if w.isalpha() and w not in VOCABULARY and len(w) >= 3:
                best_match = w
                min_dist = 3
                for vw in VOCABULARY:
                    if abs(len(vw) - len(w)) <= 2:
                        dist = get_edit_distance(w, vw)
                        if dist < min_dist:
                            min_dist = dist
                            best_match = vw
                corrected_tokens.append(best_match)
            else:
                corrected_tokens.append(w)
        filtered_tokens = corrected_tokens

    mapped_tokens = []
    for w in filtered_tokens:
        if w in SYNONYM_MAP:
            mapped_tokens.append(SYNONYM_MAP[w])
        else:
            mapped_tokens.append(w)
    filtered_tokens = mapped_tokens

    lemmatized_tokens = []
    if NLTK_AVAILABLE:
        try:
            lemmatizer = WordNetLemmatizer()
            lemmatized_tokens = [lemmatizer.lemmatize(w) for w in filtered_tokens]
        except Exception:
            for w in filtered_tokens:
                if len(w) > 4 and w.endswith('s') and not w.endswith('ss'):
                    w = w[:-1]
                elif len(w) > 5 and w.endswith('ing'):
                    w = w[:-3]
                elif len(w) > 5 and w.endswith('ed'):
                    w = w[:-2]
                lemmatized_tokens.append(w)
    else:
        for w in filtered_tokens:
            if len(w) > 4 and w.endswith('s') and not w.endswith('ss'):
                w = w[:-1]
            elif len(w) > 5 and w.endswith('ing'):
                w = w[:-3]
            elif len(w) > 5 and w.endswith('ed'):
                w = w[:-2]
            lemmatized_tokens.append(w)
            
    return " ".join(lemmatized_tokens)

# ----------------- SQLite Database Support -----------------

def get_db_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Admin Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Admin (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # 2. Questions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        category TEXT NOT NULL,
        kannada_question TEXT,
        kannada_answer TEXT
    )
    ''')
    
    # 3. Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL DEFAULT 'student123',
        platform TEXT NOT NULL,
        last_active TEXT,
        queries_count INTEGER DEFAULT 0,
        accuracy_rate REAL DEFAULT 100.0,
        status TEXT DEFAULT 'Offline'
    )
    ''')
    
    # Migration check: add password if table existed without it
    cursor.execute("PRAGMA table_info(Users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'password' not in columns:
        try:
            cursor.execute("ALTER TABLE Users ADD COLUMN password TEXT NOT NULL DEFAULT 'student123'")
            print("Migrated database: Added 'password' column to Users table.")
        except Exception as e:
            print(f"Error adding password column to Users table during migration: {e}")
            
    # 4. ChatHistory Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ChatHistory (
        chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        query TEXT NOT NULL,
        response TEXT NOT NULL,
        similarity REAL DEFAULT 0.0,
        category TEXT DEFAULT 'General',
        timestamp TEXT NOT NULL,
        is_resolved INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
    ''')
    
    # 5. Feedback Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (chat_id) REFERENCES ChatHistory(chat_id) ON DELETE CASCADE
    )
    ''')
    
    # 6. Notices Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Notices (
        notice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')
    
    # 7. GeneralFeedback Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS GeneralFeedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        rating INTEGER NOT NULL,
        comments TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()

    # Seed mock notices if empty
    cursor.execute("SELECT COUNT(*) FROM Notices")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.datetime.now().isoformat()
        cursor.execute("INSERT INTO Notices (title, content, timestamp) VALUES (?, ?, ?)",
                       ("Semester Registration Open", "MCA Semester registration for the upcoming academic term begins on July 1st. Please submit your elective choice forms by June 30th to avoid late fees.", now_str))
        cursor.execute("INSERT INTO Notices (title, content, timestamp) VALUES (?, ?, ?)",
                       ("MCA Campus Recruitment Drive", "Infosys is conducting a campus recruitment drive for final-year MCA students on July 10th. Pre-placement talk starts at 10:00 AM in the main auditorium.", now_str))
        cursor.execute("INSERT INTO Notices (title, content, timestamp) VALUES (?, ?, ?)",
                       ("Extended Library Hours for Examinations", "To support preparation for the upcoming semester examinations, the central library will remain open until 10:00 PM on weekdays.", now_str))
        conn.commit()
        print("Mock notices successfully seeded.")
    
    # Seed default admin if empty
    cursor.execute("SELECT COUNT(*) FROM Admin")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Admin (username, password) VALUES ('admin', 'admin123')")
        conn.commit()
        print("Default admin 'admin'/'admin123' created.")

    # Migrate Questions if empty
    cursor.execute("SELECT COUNT(*) FROM Questions")
    if cursor.fetchone()[0] == 0 and os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            for item in kb_data:
                cursor.execute('''
                INSERT INTO Questions (question_id, question, answer, category, kannada_question, kannada_answer)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    item.get("id"),
                    item.get("question"),
                    item.get("answer"),
                    item.get("category"),
                    item.get("kannada_question"),
                    item.get("kannada_answer")
                ))
            conn.commit()
            print(f"Migrated {len(kb_data)} Q&A items to Questions table.")
        except Exception as e:
            print(f"Failed to migrate kb.json: {e}")

    # Keep MCA and MSc(Cs) knowledge separated even for existing databases.
    for item in COURSE_SPECIFIC_KB:
        cursor.execute("SELECT question_id FROM Questions WHERE question = ?", (item["question"],))
        existing = cursor.fetchone()
        kn_q = item.get("kannada_question")
        kn_a = item.get("kannada_answer")
        if existing:
            if kn_q and kn_a:
                cursor.execute('''
                    UPDATE Questions
                    SET answer = ?, category = ?, kannada_question = ?, kannada_answer = ?
                    WHERE question_id = ?
                ''', (item["answer"], item["category"], kn_q, kn_a, existing["question_id"]))
            else:
                cursor.execute('''
                    UPDATE Questions
                    SET answer = ?, category = ?
                    WHERE question_id = ?
                ''', (item["answer"], item["category"], existing["question_id"]))
        else:
            cursor.execute('''
                INSERT INTO Questions (question, answer, category, kannada_question, kannada_answer)
                VALUES (?, ?, ?, ?, ?)
            ''', (item["question"], item["answer"], item["category"], kn_q, kn_a))
    conn.commit()

    # Migrate Users, Chat History, Feedback if empty
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0 and os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
            
            users_migrated = 0
            for u in db_data.get("users", []):
                uid = u.get("id")
                name = u.get("name")
                email = f"{name.replace(' ', '').lower()}@example.com"
                platform = u.get("platform", "Web Widget")
                last_active = u.get("last_active")
                queries_count = u.get("queries_count", 0)
                accuracy_rate = u.get("accuracy_rate", 100.0)
                status = u.get("status", "Offline")
                
                cursor.execute('''
                INSERT OR REPLACE INTO Users (user_id, name, email, platform, last_active, queries_count, accuracy_rate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (uid, name, email, platform, last_active, queries_count, accuracy_rate, status))
                
                history = u.get("history", [])
                last_user_query = None
                for msg in history:
                    if msg.get("sender") == "user":
                        last_user_query = msg
                    elif msg.get("sender") == "bot":
                        query_text = last_user_query.get("message") if last_user_query else "Hello"
                        query_time = last_user_query.get("timestamp") if last_user_query else msg.get("timestamp")
                        
                        response_text = msg.get("message")
                        similarity = msg.get("similarity", 0.0)
                        category = msg.get("category", "General")
                        is_resolved = 1 if similarity >= 0.30 else 0
                        
                        cursor.execute('''
                        INSERT INTO ChatHistory (user_id, query, response, similarity, category, timestamp, is_resolved)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (uid, query_text, response_text, similarity, category, query_time, is_resolved))
                        
                        chat_id = cursor.lastrowid
                        
                        feedback_status = msg.get("feedback")
                        if feedback_status:
                            rating = 5 if feedback_status == 'up' else 1
                            cursor.execute('''
                            INSERT INTO Feedback (chat_id, rating, timestamp)
                            VALUES (?, ?, ?)
                            ''', (chat_id, rating, msg.get("timestamp")))
                            
                users_migrated += 1
                
            for un in db_data.get("unanswered", []):
                uid = un.get("user_id", "USR-TEMP")
                q_text = un.get("question")
                q_time = un.get("timestamp")
                cat = un.get("category", "Admissions")
                
                cursor.execute("SELECT COUNT(*) FROM Users WHERE user_id = ?", (uid,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                    INSERT INTO Users (user_id, name, email, platform, last_active, queries_count, status)
                    VALUES (?, ?, ?, ?, ?, 1, 'Offline')
                    ''', (uid, un.get("user_name", "Unregistered User"), f"user_{uid.lower()}@example.com", "Web Widget", q_time))
                
                cursor.execute('''
                INSERT INTO ChatHistory (user_id, query, response, similarity, category, timestamp, is_resolved)
                VALUES (?, ?, ?, 0.0, ?, ?, 0)
                ''', (uid, q_text, "I am sorry, I couldn't find a matching answer for your question. A support operator has been notified to look into this.", cat, q_time))
            
            conn.commit()
            print(f"Migrated {users_migrated} user profiles and chat transcript logs.")
        except Exception as e:
            print(f"Failed to migrate database.json: {e}")
            
    conn.close()

# Category detection function
def detect_query_category(query):
    query_lower = query.lower()
    if any(kw in query_lower for kw in ["admission", "admissions", "apply", "applying", "enroll", "enrollment", "register", "registration", "process", "date", "calendar", "document", "documents", "eligibility", "qualification", "qualifications", "percentage"]):
        return "Admission"
    if any(kw in query_lower for kw in ["fee", "fees", "charge", "charges", "cost", "costs", "price", "prices", "expense", "expenses", "tuition", "payment", "payments"]):
        return "Fees"
    if any(kw in query_lower for kw in ["hostel", "hostels", "accommodation", "room", "rooms", "stay", "mess", "canteen", "lodging", "wi-fi", "wifi"]):
        return "Hostel"
    if any(kw in query_lower for kw in ["scholarship", "scholarships", "concession", "financial", "aid", "merit"]):
        return "Scholarship"
    if any(kw in query_lower for kw in ["course", "courses", "syllabus", "subject", "subjects", "curriculum", "mca", "msc", "msc(cs)", "m.sc", "ug", "pg", "duration", "intake", "cse", "ece", "mechanical", "civil", "mba"]):
        return "Courses"
    return "Courses"

# ----------------- Vectorizer and Matching Engine -----------------

class NLPMatchingEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.kb_data = []
        self.preprocessed_questions = []
        self.tfidf_matrix = None
        self.load_knowledge_base()

    def load_knowledge_base(self):
        global VOCABULARY
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT question_id as id, question, answer, category, kannada_question, kannada_answer FROM Questions")
            rows = cursor.fetchall()
            self.kb_data = [dict(row) for row in rows]
            conn.close()
        except Exception as e:
            print(f"Error loading KB from SQLite: {e}")
            self.kb_data = []
            
        VOCABULARY = set()
        for item in self.kb_data:
            q_words = re.findall(r'\b\w+\b', item['question'].lower())
            VOCABULARY.update(q_words)
            
        self.preprocessed_questions = [
            preprocess_text(item['question']) for item in self.kb_data
        ]
        
        if self.preprocessed_questions and any(self.preprocessed_questions):
            self.vectorizer = TfidfVectorizer()
            self.tfidf_matrix = self.vectorizer.fit_transform(self.preprocessed_questions)
        else:
            self.tfidf_matrix = None

    def find_best_match(self, user_query, last_category=None):
        if not self.kb_data or self.tfidf_matrix is None:
            return None, 0.0, False
            
        is_kannada = bool(re.search(r'[\u0c80-\u0cff]', user_query))
        
        if is_kannada:
            words = re.findall(r'\b\w+\b', user_query)
            translated = []
            for w in words:
                matched = False
                if w in KANNADA_DICT:
                    translated.append(KANNADA_DICT[w])
                    matched = True
                else:
                    for k, val in KANNADA_DICT.items():
                        if w.startswith(k):
                            translated.append(val)
                            matched = True
                            break
                if not matched:
                    translated.append(w)
            english_query = " ".join(translated)
        else:
            english_query = user_query
            
        preprocessed_query = preprocess_text(english_query)
        if not preprocessed_query.strip():
            return None, 0.0, is_kannada

        try:
            query_vector = self.vectorizer.transform([preprocessed_query])
            raw_similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

            # If there's an extremely strong direct match, prioritize it without categories biasing it
            best_raw_idx = int(np.argmax(raw_similarities))
            if raw_similarities[best_raw_idx] >= 0.90:
                return self.kb_data[best_raw_idx], float(raw_similarities[best_raw_idx]), is_kannada

            similarities = raw_similarities.copy()
            if last_category and last_category not in ["General", "Unclassified"]:
                for idx, item in enumerate(self.kb_data):
                    if item.get("category") == last_category:
                        similarities[idx] *= 1.35

            best_match_idx = int(np.argmax(similarities))
            best_similarity = min(float(similarities[best_match_idx]), 1.0)
            return self.kb_data[best_match_idx], best_similarity, is_kannada
        except Exception as e:
            print(f"Error during cosine similarity matching: {e}")
            return None, 0.0, is_kannada

    def get_relevant_matches(self, user_query, limit=4, minimum_score=0.08):
        """Return KB entries for LLM grounding, rather than one forced answer."""
        if not self.kb_data or self.tfidf_matrix is None:
            return []

        query = user_query
        if re.search(r'[\u0c80-\u0cff]', user_query):
            translated = []
            for word in re.findall(r'\b\w+\b', user_query):
                translated.append(KANNADA_DICT.get(word, word))
            query = " ".join(translated)

        processed_query = preprocess_text(query)
        if not processed_query:
            return []

        try:
            query_vector = self.vectorizer.transform([processed_query])
            scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            indices = np.argsort(scores)[::-1]
            return [
                (self.kb_data[int(index)], float(scores[index]))
                for index in indices[:limit]
                if scores[index] >= minimum_score
            ]
        except Exception as e:
            print(f"Error retrieving LLM context: {e}")
            return []

    def get_suggestions(self, user_query, limit=3, is_kannada=False):
        is_query_kn = is_kannada or bool(re.search(r'[\u0c80-\u0cff]', user_query))
        if is_query_kn:
            words = re.findall(r'\b\w+\b', user_query)
            translated = []
            for w in words:
                matched = False
                if w in KANNADA_DICT:
                    translated.append(KANNADA_DICT[w])
                    matched = True
                else:
                    for k, val in KANNADA_DICT.items():
                        if w.startswith(k):
                            translated.append(val)
                            matched = True
                            break
                if not matched:
                    translated.append(w)
            english_query = " ".join(translated)
        else:
            english_query = user_query
            
        preprocessed = preprocess_text(english_query)
        if not preprocessed.strip() or self.tfidf_matrix is None:
            if is_query_kn:
                return [
                    "MCA ಕೋರ್ಸ್ ಪ್ರವೇಶ ಪ್ರಕ್ರಿಯೆ ಏನು?",
                    "MCA ಕಾರ್ಯಕ್ರಮದ ಶುಲ್ಕ ರಚನೆ ಏನು?",
                    "MCA ಪದವೀಧರರ ಉದ್ಯೋಗ ನಿಯೋಜನೆ (ಪ್ಲೇಸ್‌ಮೆಂಟ್) ಅಂಕಿಅಂಶಗಳು ಯಾವುವು?"
                ]
            return [
                "What is the admission procedure for the MCA course?",
                "What is the fee structure for the MCA program?",
                "What are the placement statistics for MCA graduates?"
            ]
            
        try:
            query_vector = self.vectorizer.transform([preprocessed])
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            sorted_indices = np.argsort(similarities)[::-1]
            suggestions = []
            for idx in sorted_indices:
                if similarities[idx] > 0.05:
                    item = self.kb_data[idx]
                    q_text = item["kannada_question"] if (is_query_kn and "kannada_question" in item) else item["question"]
                    if q_text not in suggestions:
                        suggestions.append(q_text)
                    if len(suggestions) >= limit:
                        break
            return suggestions
        except Exception:
            return []

# Initialize Engine
engine = NLPMatchingEngine()


def get_chat_history(cursor, user_id, limit=6):
    """Read a small recent transcript so follow-up questions have context."""
    cursor.execute('''
        SELECT query, response FROM ChatHistory
        WHERE user_id = ?
        ORDER BY timestamp DESC, chat_id DESC
        LIMIT ?
    ''', (user_id, limit))
    rows = list(reversed(cursor.fetchall()))
    return "\n".join(
        f"Student: {row['query']}\nAssistant: {row['response']}" for row in rows
    )


def generate_llm_response(cursor, user_id, message):
    """Generate a grounded response. Returns None when LLM mode is unavailable."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, [], 0.0

    matches = engine.get_relevant_matches(message)
    knowledge = "\n\n".join(
        f"[{item.get('category', 'General')}]\nQuestion: {item['question']}\nAnswer: {item['answer']}"
        for item, _ in matches
    ) or "No relevant verified knowledge-base entry was found."
    history = get_chat_history(cursor, user_id)

    system_prompt = """You are Dept. CsBot, a helpful college enquiry assistant.
Answer the student naturally and concisely. Use only the VERIFIED KNOWLEDGE BASE
and the supplied conversation history. Do not invent fees, dates, policies,
placement statistics, contacts, or eligibility rules. If the information is not
in the verified knowledge base, clearly say you do not have verified information
and suggest contacting the college office. Respect the user's language."""
    user_prompt = f"""VERIFIED KNOWLEDGE BASE:
{knowledge}

RECENT CONVERSATION:
{history or '(No previous conversation.)'}

CURRENT STUDENT MESSAGE:
{message}"""
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]}
        ],
        "max_output_tokens": 400
    }

    try:
        request_data = json.dumps(payload).encode("utf-8")
        api_request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=request_data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(api_request, timeout=30) as api_response:
            response_data = json.loads(api_response.read().decode("utf-8"))

        answer = response_data.get("output_text", "").strip()
        if not answer:
            for output in response_data.get("output", []):
                for content in output.get("content", []):
                    if content.get("type") == "output_text":
                        answer += content.get("text", "")
        answer = answer.strip()
        return (answer or None), matches, (matches[0][1] if matches else 0.0)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        # Keep the existing offline chatbot usable if the LLM service is unavailable.
        print(f"LLM request failed; using FAQ fallback: {e}")
        return None, matches, (matches[0][1] if matches else 0.0)

# Helper to recalculate user accuracy rate
def update_user_accuracy_rate(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, similarity FROM ChatHistory WHERE user_id = ?", (user_id,))
    chat_rows = cursor.fetchall()
    
    total_bot_responses = len(chat_rows)
    if total_bot_responses == 0:
        return
        
    positive_count = 0
    for row in chat_rows:
        chat_id = row['chat_id']
        similarity = row['similarity']
        
        cursor.execute("SELECT rating FROM Feedback WHERE chat_id = ?", (chat_id,))
        fb_row = cursor.fetchone()
        
        if fb_row:
            rating = fb_row['rating']
            if rating >= 4:
                positive_count += 1
        else:
            if similarity >= 0.30:
                positive_count += 1
                
    accuracy_rate = round((positive_count / total_bot_responses) * 100, 1)
    cursor.execute("UPDATE Users SET accuracy_rate = ? WHERE user_id = ?", (accuracy_rate, user_id))
    conn.commit()

# ----------------- Student User Registration & Login Endpoints -----------------

@app.route('/api/register', methods=['POST'])
def user_register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    platform = data.get("platform", "Web Widget").strip()
    
    if not name or not email or not password:
        return jsonify({"success": False, "error": "All fields (name, email, password) are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return jsonify({"success": False, "error": "Email is already registered"}), 409
        
    # Generate user_id (e.g. USR-XXXX)
    import random
    user_id = f"USR-{random.randint(1000, 9999)}"
    # Ensure uniqueness of user_id
    while True:
        cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            break
        user_id = f"USR-{random.randint(1000, 9999)}"
        
    timestamp = datetime.datetime.now().isoformat()
    
    # Insert new user
    cursor.execute('''
        INSERT INTO Users (user_id, name, email, password, platform, last_active, queries_count, accuracy_rate, status)
        VALUES (?, ?, ?, ?, ?, ?, 0, 100.0, 'Offline')
    ''', (user_id, name, email, password, platform, timestamp))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "User registered successfully",
        "user": {
            "user_id": user_id,
            "name": name,
            "email": email
        }
    })

@app.route('/api/user/login', methods=['POST'])
def user_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email = ? AND password = ?", (email, password))
    user_row = cursor.fetchone()
    
    if user_row:
        user_data = dict(user_row)
        # Update user status to online and last active timestamp
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute("UPDATE Users SET status = 'Online', last_active = ? WHERE user_id = ?", (timestamp, user_data["user_id"]))
        conn.commit()
        conn.close()
        
        # Remove sensitive information like password
        if "password" in user_data:
            del user_data["password"]
            
        return jsonify({
            "success": True,
            "token": "user-mock-session-token",
            "user": user_data,
            "message": "Login successful"
        })
        
    conn.close()
    return jsonify({"success": False, "error": "Invalid email or password credentials"}), 401


# ----------------- Notices Management Endpoints -----------------

@app.route('/api/notices', methods=['GET'])
def get_notices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Notices ORDER BY timestamp DESC")
    notices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(notices)

@app.route('/api/notices', methods=['POST'])
def create_notice():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    
    if not title or not content:
        return jsonify({"success": False, "error": "Title and content are required"}), 400
        
    timestamp = datetime.datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Notices (title, content, timestamp) VALUES (?, ?, ?)", (title, content, timestamp))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Notice added successfully"})

@app.route('/api/notices/<int:notice_id>', methods=['DELETE'])
def delete_notice(notice_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Notices WHERE notice_id = ?", (notice_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Notice deleted successfully"})


# ----------------- General Feedback Endpoints -----------------

@app.route('/api/general-feedback', methods=['POST'])
def submit_general_feedback():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    rating = data.get("rating")
    comments = data.get("comments", "").strip()
    
    if not user_id or not rating or not comments:
        return jsonify({"success": False, "error": "Missing required fields (user_id, rating, comments)"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user name
    cursor.execute("SELECT name FROM Users WHERE user_id = ?", (user_id,))
    user_row = cursor.fetchone()
    name = user_row['name'] if user_row else "Anonymous Student"
    
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO GeneralFeedback (user_id, name, rating, comments, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, name, int(rating), comments, timestamp))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Feedback submitted successfully"})

@app.route('/api/general-feedback', methods=['GET'])
def get_general_feedbacks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM GeneralFeedback ORDER BY timestamp DESC")
    feedbacks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(feedbacks)

@app.route('/api/general-feedback/<int:feedback_id>', methods=['DELETE'])
def delete_general_feedback(feedback_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM GeneralFeedback WHERE feedback_id = ?", (feedback_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Feedback deleted successfully"})


# ----------------- Admin REST API Login -----------------

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Admin WHERE username = ? AND password = ?", (username, password))
    admin_row = cursor.fetchone()
    conn.close()
    
    if admin_row:
        return jsonify({
            "success": True,
            "token": "admin-mock-session-token",
            "username": username,
            "message": "Login successful"
        })
    return jsonify({"success": False, "error": "Invalid administrative credentials"}), 401

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. KPI Cards data
    cursor.execute("SELECT COUNT(*) FROM Users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ChatHistory")
    total_queries = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(accuracy_rate) FROM Users WHERE queries_count > 0")
    avg_accuracy_row = cursor.fetchone()[0]
    avg_accuracy = round(avg_accuracy_row, 1) if avg_accuracy_row is not None else 100.0
    
    cursor.execute("SELECT COUNT(*) FROM ChatHistory WHERE is_resolved = 0")
    pending_questions = cursor.fetchone()[0]
    
    # 2. Dynamic activity feed logs using UNION SQL query
    cursor.execute("""
        SELECT type, message, timestamp FROM (
            SELECT 'chat' as type, 'User ' || name || ' asked about ' || lower(ChatHistory.category) || '.' as message, timestamp
            FROM ChatHistory JOIN Users ON ChatHistory.user_id = Users.user_id
            UNION ALL
            SELECT 'unanswered' as type, 'New unanswered query flagged: ' || substr(query, 1, 40) || '...' as message, timestamp
            FROM ChatHistory WHERE is_resolved = 0
            UNION ALL
            SELECT 'resolve' as type, 'User ' || name || ' rated response ' || rating || ' stars.' as message, Feedback.timestamp as timestamp
            FROM Feedback JOIN ChatHistory ON Feedback.chat_id = ChatHistory.chat_id JOIN Users ON ChatHistory.user_id = Users.user_id
        ) ORDER BY timestamp DESC LIMIT 10
    """)
    activities = [dict(row) for row in cursor.fetchall()]
    
    # 3. Category distribution (Volume)
    cursor.execute("SELECT category, COUNT(*) as count FROM ChatHistory GROUP BY category")
    category_distribution = {row['category']: row['count'] for row in cursor.fetchall()}
    
    # 4. Feedback positive / negative tallies (4-5 vs 1-2 stars)
    cursor.execute("SELECT COUNT(*) FROM Feedback WHERE rating >= 4")
    total_positives = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Feedback WHERE rating <= 2")
    total_negatives = cursor.fetchone()[0]
    
    # 5. Charts Metrics - Daily query usage counts (last 7 days)
    cursor.execute('''
        SELECT date(timestamp) as day, COUNT(*) as count 
        FROM ChatHistory 
        GROUP BY day 
        ORDER BY day DESC 
        LIMIT 7
    ''')
    daily_usage = [dict(row) for row in cursor.fetchall()]
    daily_usage.reverse()  # chronological order
    
    # 6. FAQ Management - Most searched/common queries
    cursor.execute('''
        SELECT query as question, COUNT(*) as count 
        FROM ChatHistory 
        GROUP BY query 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    top_queries = [dict(row) for row in cursor.fetchall()]
    
    # 7. User Activity count grouped by Platform channel
    cursor.execute('''
        SELECT platform, COUNT(*) as count 
        FROM ChatHistory JOIN Users ON ChatHistory.user_id = Users.user_id
        GROUP BY platform
    ''')
    user_activity = {row['platform']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return jsonify({
        "total_users": total_users,
        "total_queries": total_queries,
        "accuracy_rate": avg_accuracy,
        "pending_questions": pending_questions,
        "activities": activities,
        "category_distribution": category_distribution,
        "positive_feedbacks": total_positives,
        "negative_feedbacks": total_negatives,
        "daily_usage": daily_usage,
        "top_queries": top_queries,
        "user_activity": user_activity
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Users")
    users = [dict(row) for row in cursor.fetchall()]
    
    for u in users:
        uid = u['user_id']
        u['id'] = uid  # front-end mapping compatibility
        
        cursor.execute('''
            SELECT chat_id, query, response, similarity, category, timestamp, is_resolved
            FROM ChatHistory 
            WHERE user_id = ? 
            ORDER BY timestamp ASC
        ''', (uid,))
        chat_rows = cursor.fetchall()
        
        history = []
        for row in chat_rows:
            history.append({
                "sender": "user",
                "message": row["query"],
                "timestamp": row["timestamp"]
            })
            
            fb_rating = None
            cursor.execute("SELECT rating FROM Feedback WHERE chat_id = ?", (row["chat_id"],))
            fb_row = cursor.fetchone()
            if fb_row:
                fb_rating = fb_row["rating"]
                
            history.append({
                "sender": "bot",
                "message": row["response"],
                "timestamp": row["timestamp"],
                "similarity": row["similarity"],
                "category": row["category"],
                "feedback_rating": fb_rating,
                "feedback": "up" if fb_rating and fb_rating >= 4 else ("down" if fb_rating and fb_rating <= 2 else None)
            })
        u['history'] = history
        
    conn.close()
    return jsonify(users)

@app.route('/api/unanswered', methods=['GET'])
def get_unanswered():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ChatHistory.chat_id as id, ChatHistory.user_id, Users.name as user_name,
               ChatHistory.query as question, ChatHistory.timestamp, ChatHistory.category
        FROM ChatHistory 
        JOIN Users ON ChatHistory.user_id = Users.user_id 
        WHERE ChatHistory.is_resolved = 0
        ORDER BY ChatHistory.timestamp DESC
    ''')
    unanswered = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(unanswered)

@app.route('/api/history', methods=['GET'])
def get_user_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id, query, response, similarity, category, timestamp, is_resolved
        FROM ChatHistory 
        WHERE user_id = ? 
        ORDER BY timestamp ASC
    ''', (user_id,))
    chat_rows = cursor.fetchall()
    
    history = []
    for row in chat_rows:
        history.append({
            "sender": "user",
            "message": row["query"],
            "timestamp": row["timestamp"]
        })
        
        fb_rating = None
        cursor.execute("SELECT rating FROM Feedback WHERE chat_id = ?", (row["chat_id"],))
        fb_row = cursor.fetchone()
        if fb_row:
            fb_rating = fb_row["rating"]
            
        history.append({
            "chat_id": row["chat_id"],
            "sender": "bot",
            "message": row["response"],
            "timestamp": row["timestamp"],
            "similarity": row["similarity"],
            "category": row["category"],
            "feedback_rating": fb_rating,
            "feedback": "up" if fb_rating and fb_rating >= 4 else ("down" if fb_rating and fb_rating <= 2 else None)
        })
        
    conn.close()
    return jsonify(history)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_id = data.get("user_id", "USR-TEMP")
    user_name = data.get("name", "Guest User")
    email = data.get("email", f"{user_name.replace(' ', '').lower()}@example.com").strip()
    platform = data.get("platform", "Web Widget")
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
        
    timestamp = datetime.datetime.now().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify or create User Persona
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
    user_profile = cursor.fetchone()
    
    if not user_profile:
        cursor.execute('''
            INSERT INTO Users (user_id, name, email, platform, last_active, queries_count, accuracy_rate, status)
            VALUES (?, ?, ?, ?, ?, 1, 100.0, 'Online')
        ''', (user_id, user_name, email, platform, timestamp))
    else:
        cursor.execute('''
            UPDATE Users 
            SET name = ?, email = ?, platform = ?, last_active = ?, queries_count = queries_count + 1, status = 'Online'
            WHERE user_id = ?
        ''', (user_name, email, platform, timestamp, user_id))
    
    conn.commit()
    
    # Check if the query is a dynamic live-data request
    is_kannada = bool(re.search(r'[\u0c80-\u0cff]', message))
    msg_lower = message.lower()
    
    # 1. Greetings / Gratitude Handler
    greetings = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "yo", "hola", "namaste", "ನಮಸ್ಕಾರ", "ಹಲೋ", "ಹಾಯ್"}
    thanks_keywords = {"thanks", "thank you", "thankyou", "dhanyavada", "ಧನ್ಯವಾದ", "ಧನ್ಯವಾದಗಳು"}
    clean_msg = message.lower().strip().replace("?", "").replace(".", "").replace("!", "")
    
    threshold = 0.30
    suggestions = []
    similarity = 0.0
    
    if clean_msg in greetings:
        if is_kannada:
            response_text = "ಹಲೋ! ನಾನು ಡೆಪ್ಟ್ ಸಿಎಸ್ ಬಾಟ್ (Dept. CsBot). ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
        else:
            response_text = "Hello! I am Dept. CsBot. How can I help you today?"
        is_answered = 1
        similarity = 1.0
        match_category = "General"
        
    elif clean_msg in thanks_keywords:
        if is_kannada:
            response_text = "ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಂತೋಷವಾಗಿದೆ! ನಿಮಗೆ ಇನ್ನೇನಾದರೂ ಸಹಾಯ ಬೇಕೇ?"
        else:
            response_text = "You're welcome! Let me know if you need anything else."
        is_answered = 1
        similarity = 1.0
        match_category = "General"
        
    else:
        # 2. Intent Detection for Live Data
        notices_keywords = ["notice", "notices", "announcement", "announcements", "update", "updates", "board", "alert", "alerts"]
        kannada_notices_keywords = ["ಸೂಚನೆ", "ಪ್ರಕಟಣೆ", "ಅಪ್ಡೇಟ್", "ಎಚ್ಚರಿಕೆ"]
        is_notices_query = any(kw in msg_lower for kw in kannada_notices_keywords) if is_kannada else any(kw in msg_lower for kw in notices_keywords)
        
        profile_keywords = ["profile", "my stats", "my queries", "query count", "my account", "my status", "accuracy rate", "queries sent"]
        kannada_profile_keywords = ["ಪ್ರೊಫೈಲ್", "ನನ್ನ ಖಾತೆ", "ನನ್ನ ಪ್ರಶ್ನೆಗಳು", "ಅಂಕಿಅಂಶ"]
        is_profile_query = any(kw in msg_lower for kw in kannada_profile_keywords) if is_kannada else any(kw in msg_lower for kw in profile_keywords)

        if is_notices_query:
            cursor.execute("SELECT title, content, timestamp FROM Notices ORDER BY timestamp DESC LIMIT 3")
            rows = cursor.fetchall()
            
            if rows:
                if is_kannada:
                    response_text = "ಇತ್ತೀಚಿನ ಕಾಲೇಜು ಸೂಚನೆಗಳು ಮತ್ತು ಪ್ರಕಟಣೆಗಳು ಇಲ್ಲಿವೆ:\n"
                    for idx, row in enumerate(rows, 1):
                        dt_str = row['timestamp']
                        try:
                            dt = datetime.datetime.fromisoformat(dt_str)
                            dt_formatted = dt.strftime('%d-%m-%Y')
                        except Exception:
                            dt_formatted = dt_str
                        response_text += f"{idx}. **{row['title']}** ({dt_formatted}):\n{row['content']}\n\n"
                else:
                    response_text = "Here are the latest college notices and announcements:\n"
                    for idx, row in enumerate(rows, 1):
                        dt_str = row['timestamp']
                        try:
                            dt = datetime.datetime.fromisoformat(dt_str)
                            dt_formatted = dt.strftime('%d-%m-%Y')
                        except Exception:
                            dt_formatted = dt_str
                        response_text += f"{idx}. **{row['title']}** ({dt_formatted}):\n{row['content']}\n\n"
            else:
                response_text = "ಪ್ರಸ್ತುತ ಸೂಚನಾ ಫಲಕದಲ್ಲಿ ಯಾವುದೇ ಹೊಸ ಪ್ರಕಟಣೆಗಳು ಇಲ್ಲ." if is_kannada else "There are currently no active notices on the notice board."
                
            is_answered = 1
            similarity = 1.0
            match_category = "Notices"
            
        elif is_profile_query:
            cursor.execute("SELECT name, email, platform, queries_count, accuracy_rate, status FROM Users WHERE user_id = ?", (user_id,))
            user_row = cursor.fetchone()
            
            if user_row:
                if is_kannada:
                    response_text = f"ನಿಮ್ಮ ವಿವರಗಳು ಮತ್ತು ಅಂಕಿಅಂಶಗಳು ಇಲ್ಲಿವೆ:\n" \
                                    f"- **ಹೆಸರು**: {user_row['name']}\n" \
                                    f"- **ಬಳಕೆದಾರ ID**: {user_id}\n" \
                                    f"- **ಇಮೇಲ್**: {user_row['email']}\n" \
                                    f"- **ಪ್ಲಾಟ್‌ಫಾರ್ಮ್**: {user_row['platform']}\n" \
                                    f"- **ಕಳುಹಿಸಿದ ಪ್ರಶ್ನೆಗಳು**: {user_row['queries_count']}\n" \
                                    f"- **ನಿಖರತೆ ದರ**: {user_row['accuracy_rate']}%\n" \
                                    f"- **ಸ್ಥಿತಿ**: {user_row['status']}"
                else:
                    response_text = f"Here is your student profile and chatbot statistics:\n" \
                                    f"- **Name**: {user_row['name']}\n" \
                                    f"- **User ID**: {user_id}\n" \
                                    f"- **Email**: {user_row['email']}\n" \
                                    f"- **Platform**: {user_row['platform']}\n" \
                                    f"- **Queries Sent**: {user_row['queries_count']}\n" \
                                    f"- **Accuracy Rate**: {user_row['accuracy_rate']}%\n" \
                                    f"- **Status**: {user_row['status']}"
            else:
                response_text = "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಬಳಕೆದಾರ ವಿವರಗಳನ್ನು ಪತ್ತೆಹಚ್ಚಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ." if is_kannada else "Sorry, I could not find your user profile statistics."
                
            is_answered = 1
            similarity = 1.0
            match_category = "Profile"
            
        else:
            # Fall back to standard static matching
            cursor.execute("SELECT category FROM ChatHistory WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
            last_cat_row = cursor.fetchone()
            last_category = last_cat_row['category'] if last_cat_row else None
            
            best_match, similarity, is_kannada = engine.find_best_match(message, last_category)
            if best_match and similarity >= threshold:
                response_text = best_match["kannada_answer"] if (is_kannada and "kannada_answer" in best_match) else best_match["answer"]
                is_answered = 1
                match_category = best_match.get("category", "General")
            else:
                if is_kannada:
                    response_text = "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಹೊಂದಾಣಿಕೆಯಾಗುವ ಉತ್ತರವನ್ನು ಕಂಡುಹಿಡಿಯಲಾಗಲಿಲ್ಲ. ಸಹಾಯ ಆಪರೇಟರ್‌ಗೆ ತಿಳಿಸಲಾಗಿದೆ."
                else:
                    response_text = "I am sorry, I couldn't find a matching answer for your question. A support operator has been notified to look into this."
                is_answered = 0
                match_category = detect_query_category(message)
                suggestions = engine.get_suggestions(message, limit=3, is_kannada=is_kannada)

            # When LLM mode is configured, replace the forced intent answer with
            # a grounded, history-aware answer. The static matcher remains the
            # offline fallback when no key is configured or the request fails.
            llm_response, llm_matches, llm_similarity = generate_llm_response(cursor, user_id, message)
            if llm_response:
                response_text = llm_response
                similarity = llm_similarity
                is_answered = 1 if llm_matches else 0
                match_category = llm_matches[0][0].get("category", "General") if llm_matches else detect_query_category(message)
                suggestions = [] if llm_matches else engine.get_suggestions(message, limit=3, is_kannada=is_kannada)
            
    # Write to ChatHistory
    cursor.execute('''
        INSERT INTO ChatHistory (user_id, query, response, similarity, category, timestamp, is_resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, message, response_text, round(similarity, 2), match_category, timestamp, is_answered))
    chat_id = cursor.lastrowid
    conn.commit()
    
    # Recalculate user accuracy metrics
    update_user_accuracy_rate(conn, user_id)
    
    conn.close()
    
    return jsonify({
        "chat_id": chat_id,
        "answer": response_text,
        "similarity": round(similarity, 2),
        "is_answered": bool(is_answered),
        "category": match_category,
        "suggestions": suggestions
    })

@app.route('/api/suggestions', methods=['GET'])
def get_autocomplete_suggestions():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search in both English and Kannada questions
    cursor.execute('''
        SELECT DISTINCT question FROM Questions WHERE question LIKE ?
        UNION
        SELECT DISTINCT kannada_question FROM Questions WHERE kannada_question LIKE ? AND kannada_question IS NOT NULL
        LIMIT 5
    ''', (f"%{q}%", f"%{q}%"))
    
    suggestions = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return jsonify(suggestions)

@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    data = request.get_json() or {}
    chat_id = data.get("chat_id")
    rating = data.get("rating")  # Integer 1-5 stars
    
    if not chat_id or not rating:
        return jsonify({"error": "Missing required fields"}), 400
        
    timestamp = datetime.datetime.now().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Save feedback rating
    cursor.execute('''
        INSERT OR REPLACE INTO Feedback (chat_id, rating, timestamp)
        VALUES (?, ?, ?)
    ''', (chat_id, rating, timestamp))
    conn.commit()
    
    # Retrieve user_id of this chat session
    cursor.execute("SELECT user_id FROM ChatHistory WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if row:
        user_id = row['user_id']
        update_user_accuracy_rate(conn, user_id)
        
        cursor.execute("SELECT accuracy_rate FROM Users WHERE user_id = ?", (user_id,))
        accuracy_rate = cursor.fetchone()['accuracy_rate']
    else:
        accuracy_rate = 100.0
        
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Feedback score updated successfully",
        "new_accuracy": accuracy_rate
    })

@app.route('/api/unanswered/resolve', methods=['POST'])
def resolve_unanswered():
    data = request.get_json() or {}
    unanswered_id = data.get("id")  # chat_id
    operator_answer = data.get("answer", "").strip()
    category = data.get("category", "General Enquiry")
    kannada_answer = data.get("kannada_answer", "").strip()
    
    if not unanswered_id or not operator_answer:
        return jsonify({"error": "Missing query ID or answer"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify unanswered query exists
    cursor.execute("SELECT * FROM ChatHistory WHERE chat_id = ? AND is_resolved = 0", (unanswered_id,))
    unanswered_query = cursor.fetchone()
    
    if not unanswered_query:
        conn.close()
        return jsonify({"error": "Query ID not found or already resolved"}), 404
        
    question_text = unanswered_query['query']
    user_id = unanswered_query['user_id']
    
    # Save the answer to the Questions database
    kn_q = KANNADA_DICT.get(question_text, question_text)
    kn_a = kannada_answer if kannada_answer else operator_answer
    
    cursor.execute('''
        INSERT INTO Questions (question, answer, category, kannada_question, kannada_answer)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (question_text, operator_answer, category, kn_q, kn_a))
    conn.commit()
    
    # Mark the ChatHistory entry as resolved and correct the response
    cursor.execute('''
        UPDATE ChatHistory 
        SET response = ?, similarity = 1.0, category = ?, is_resolved = 1 
        WHERE chat_id = ?
    ''', (operator_answer, category, unanswered_id))
    conn.commit()
    
    # Reload matching engine
    engine.load_knowledge_base()
    
    # Recalculate accuracy rate
    update_user_accuracy_rate(conn, user_id)
    
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Answer successfully added to FAQ and question resolved."
    })

# ----------------- Knowledge Base CRUD -----------------

@app.route('/api/kb', methods=['GET'])
def get_kb():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT question_id as id, question, answer, category, kannada_question, kannada_answer FROM Questions ORDER BY category, question_id")
    kb_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(kb_list)

@app.route('/api/kb', methods=['POST'])
def add_kb_item():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    category = data.get("category", "General").strip()
    kannada_question = data.get("kannada_question", "").strip() or None
    kannada_answer = data.get("kannada_answer", "").strip() or None
    
    if not question or not answer or not category:
        return jsonify({"error": "Question, answer, and category are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Questions (question, answer, category, kannada_question, kannada_answer)
        VALUES (?, ?, ?, ?, ?)
    ''', (question, answer, category, kannada_question, kannada_answer))
    conn.commit()
    conn.close()
    
    engine.load_knowledge_base()
    return jsonify({"success": True, "message": "Knowledge base item added successfully"})

@app.route('/api/kb/<int:question_id>', methods=['PUT'])
def update_kb_item(question_id):
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    category = data.get("category", "").strip()
    kannada_question = data.get("kannada_question", "").strip() or None
    kannada_answer = data.get("kannada_answer", "").strip() or None
    
    if not question or not answer or not category:
        return jsonify({"error": "Question, answer, and category are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Questions 
        SET question = ?, answer = ?, category = ?, kannada_question = ?, kannada_answer = ?
        WHERE question_id = ?
    ''', (question, answer, category, kannada_question, kannada_answer, question_id))
    conn.commit()
    conn.close()
    
    engine.load_knowledge_base()
    return jsonify({"success": True, "message": "Knowledge base item updated successfully"})

@app.route('/api/kb/<int:question_id>', methods=['DELETE'])
def delete_kb_item(question_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Questions WHERE question_id = ?", (question_id,))
    conn.commit()
    conn.close()
    
    engine.load_knowledge_base()
    return jsonify({"success": True, "message": "Knowledge base item deleted successfully"})

# ----------------- CSV Report Exports -----------------

@app.route('/api/export/queries', methods=['GET'])
def export_queries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ChatHistory.chat_id, ChatHistory.user_id, Users.name, ChatHistory.query,
               ChatHistory.response, ChatHistory.similarity, ChatHistory.category,
               Feedback.rating, ChatHistory.timestamp
        FROM ChatHistory
        JOIN Users ON ChatHistory.user_id = Users.user_id
        LEFT JOIN Feedback ON ChatHistory.chat_id = Feedback.chat_id
        ORDER BY ChatHistory.timestamp DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Chat ID", "User ID", "User Name", "Query/Question", "Bot Response", "Similarity Score", "Category", "Feedback Stars Rating", "Timestamp"])
    for row in rows:
        writer.writerow(list(row))
        
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=chatbot_query_reports.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

@app.route('/api/export/users', methods=['GET'])
def export_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, email, platform, queries_count, accuracy_rate, status, last_active FROM Users")
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "Name", "Email", "Platform", "Queries Sent", "Accuracy Rate (%)", "Status", "Last Active"])
    for row in rows:
        writer.writerow(list(row))
        
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=chatbot_user_reports.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

@app.route('/api/export/faq', methods=['GET'])
def export_faq():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT question_id, category, question, answer, kannada_question, kannada_answer FROM Questions")
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question ID", "Category", "Question (English)", "Answer (English)", "Question (Kannada)", "Answer (Kannada)"])
    for row in rows:
        writer.writerow(list(row))
        
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=chatbot_faq_reports.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

if __name__ == '__main__':
    # Initialize the database and run migration routines
    init_db()
    
    # Reload engine knowledge base from SQLite
    engine.load_knowledge_base()
            
    print("Flask Server running on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
