import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "Student_Management_System5.db"

# ==========================================
# 2. DATABASE INITIALIZATION
# ==========================================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            semester INTEGER NOT NULL
        )
    ''')
    
    # Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            subject TEXT,
            date TEXT,
            status TEXT,
            FOREIGN KEY(roll_no) REFERENCES students(roll_no)
        )
    ''')
    
    # Internal Marks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS internal_marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            subject TEXT,
            marks_obtained REAL,
            max_marks REAL,
            FOREIGN KEY(roll_no) REFERENCES students(roll_no)
        )
    ''')
    
    # Practical & Viva Marks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practical_marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            subject TEXT,
            marks_obtained REAL,
            max_marks REAL,
            FOREIGN KEY(roll_no) REFERENCES students(roll_no)
        )
    ''')
    
    # Fees Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fees (
            roll_no TEXT PRIMARY KEY,
            total_fee REAL,
            paid_fee REAL,
            FOREIGN KEY(roll_no) REFERENCES students(roll_no)
        )
    ''')
    
    conn.commit()
    conn.close()

init_database()

# ==========================================
# 3. HELPER FUNCTIONS & SUBJECT RESOLVER
# ==========================================
def get_subjects_for_course_sem(course, sem):
    subjects_map = {
        "BCA": {
            1: ["C Programming", "Mathematical Foundation", "Digital Electronics"],
            2: ["Data Structures", "OOP with C++", "Database Management System"],
            3: ["Java Programming", "Web Technologies", "Operating Systems"],
            4: ["Python Programming", "Software Engineering", "Computer Networks"]
        },
        "B.Tech": {
            1: ["Engineering Physics", "Mathematics I", "Basic Electrical"],
            2: ["Engineering Chemistry", "Mathematics II", "C Programming"]
        },
        "B.Com": {
            1: ["Financial Accounting", "Business Economics", "Business Org"],
            2: ["Corporate Accounting", "Business Law", "Business Statistics"]
        },
        "MCA": {
            1: ["Advanced Java", "Operating Systems", "Data Structures"],
            2: ["Cloud Computing", "Machine Learning", "Software Architecture"]
        }
    }
    return subjects_map.get(course, {}).get(sem, ["Subject 1", "Subject 2", "Subject 3"])

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🎓 Management Portal")
st.sidebar.markdown("---")

menu_choice = st.sidebar.radio(
    "Navigate to Module:",
    [
        "👨‍🎓 Student Roster",
        "📝 Internal Marks",
        "🧪 Practical & Viva Marks",
        "📅 Attendance Tracking",
        "📊 Analytics & Defaulters",
        "🔍 Full Assessment Search"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Database**: `Student_Management_System5.db` connected.")

# ==========================================
# MODULE 1: STUDENT ROSTER MANAGEMENT
# ==========================================
if menu_choice == "👨‍🎓 Student Roster":
    st.header("👨‍🎓 Student Registration & Roster")
    
    tab1, tab2 = st.tabs(["Add New Student", "View / Manage Students"])
    
    with tab1:
        with st.form("add_student_form", clear_on_submit=True):
            st.subheader("Register Student")
            c1, c2 = st.columns(2)
            with c1:
                roll_no = st.text_input("Roll Number")
                name = st.text_input("Student Name")
            with c2:
                course = st.selectbox("Course", ["BCA", "B.Tech", "B.Com", "BBA", "B.Sc", "MCA", "MBA"])
                sem = st.number_input("Semester", min_value=1, max_value=8, step=1)
                
            submitted = st.form_submit_button("Add Student")
            if submitted:
                if roll_no and name:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO students VALUES (?, ?, ?, ?)", (roll_no.strip(), name.strip(), course, sem))
                        cursor.execute("INSERT OR IGNORE INTO fees VALUES (?, ?, ?)", (roll_no.strip(), 50000.0, 0.0))
                        conn.commit()
                        conn.close()
                        st.success(f"Student '{name}' successfully registered!")
                    except sqlite3.IntegrityError:
                        st.error("Roll Number already exists!")
                else:
                    st.warning("Please fill all required fields.")

    with tab2:
        conn = get_connection()
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        conn.close()
        
        st.subheader("Current Student Records")
        if not df_students.empty:
            st.dataframe(df_students, use_container_width=True)
            
            # Delete Option
            with st.expander("🗑️ Delete Student Record"):
                student_to_del = st.selectbox("Select Student to Remove", df_students["roll_no"] + " - " + df_students["name"])
                if st.button("Delete Student", type="primary"):
                    r_no = student_to_del.split(" - ")[0]
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM students WHERE roll_no=?", (r_no,))
                    conn.commit()
                    conn.close()
                    st.success("Student removed successfully!")
                    st.rerun()
        else:
            st.info("No students found in the database.")

# ==========================================
# MODULE 2: INTERNAL MARKS MANAGEMENT
# ==========================================
elif menu_choice == "📝 Internal Marks":
    st.header("📝 Internal Marks Management")
    
    col1, col2 = st.columns(2)
    with col1:
        sel_course = st.selectbox("Select Course", ["BCA", "B.Tech", "B.Com", "MCA"])
    with col2:
        sel_sem = st.number_input("Select Semester", min_value=1, max_value=8, value=1)

    subjects = get_subjects_for_course_sem(sel_course, sel_sem)
    sel_subject = st.selectbox("Select Subject", subjects)

    conn = get_connection()
    students_df = pd.read_sql_query("SELECT roll_no, name FROM students WHERE course=? AND semester=?", 
                                    conn, params=(sel_course, sel_sem))
    conn.close()

    if not students_df.empty:
        st.subheader(f"Marks Entry for {sel_subject} ({sel_course} Sem {sel_sem})")
        with st.form("internal_marks_form"):
            student_choice = st.selectbox("Select Student", students_df["roll_no"] + " - " + students_df["name"])
            marks_obt = st.number_input("Marks Obtained", min_value=0.0, max_value=100.0, value=0.0)
            max_marks = st.number_input("Max Marks", min_value=1.0, max_value=100.0, value=30.0)
            
            save_marks = st.form_submit_button("Save Internal Marks")
            if save_marks:
                r_no = student_choice.split(" - ")[0]
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO internal_marks (roll_no, subject, marks_obtained, max_marks) VALUES (?, ?, ?, ?)",
                    (r_no, sel_subject, marks_obt, max_marks)
                )
                conn.commit()
                conn.close()
                st.success("Internal marks recorded!")

        st.subheader("Existing Marks Records")
        conn = get_connection()
        marks_df = pd.read_sql_query(
            "SELECT im.id, im.roll_no, s.name, im.subject, im.marks_obtained, im.max_marks FROM internal_marks im JOIN students s ON im.roll_no = s.roll_no WHERE im.subject=?", 
            conn, params=(sel_subject,)
        )
        conn.close()
        st.dataframe(marks_df, use_container_width=True)
    else:
        st.info("No students registered in this course and semester.")

# ==========================================
# MODULE 3: PRACTICAL & VIVA MARKS
# ==========================================
elif menu_choice == "🧪 Practical & Viva Marks":
    st.header("🧪 Practical & Viva Assessment")
    
    c1, c2 = st.columns(2)
    with c1:
        sel_course = st.selectbox("Course", ["BCA", "B.Tech", "B.Com", "MCA"], key="prac_course")
    with c2:
        sel_sem = st.number_input("Semester", min_value=1, max_value=8, value=1, key="prac_sem")

    subjects = get_subjects_for_course_sem(sel_course, sel_sem)
    sel_subject = st.selectbox("Practical Subject", subjects, key="prac_subj")

    with st.form("practical_form"):
        conn = get_connection()
        students_df = pd.read_sql_query("SELECT roll_no, name FROM students WHERE course=? AND semester=?", 
                                        conn, params=(sel_course, sel_sem))
        conn.close()
        
        if not students_df.empty:
            selected_stu = st.selectbox("Select Student", students_df["roll_no"] + " - " + students_df["name"])
            practical_marks = st.number_input("Practical/Viva Marks Obtained", min_value=0.0, max_value=50.0, value=0.0)
            max_practical = st.number_input("Max Practical Marks", min_value=1.0, max_value=100.0, value=50.0)
            
            if st.form_submit_button("Submit Practical Marks"):
                r_no = selected_stu.split(" - ")[0]
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO practical_marks (roll_no, subject, marks_obtained, max_marks) VALUES (?, ?, ?, ?)",
                    (r_no, sel_subject, practical_marks, max_practical)
                )
                conn.commit()
                conn.close()
                st.success("Practical marks updated successfully!")
        else:
            st.warning("No students found for entry.")

    conn = get_connection()
    prac_df = pd.read_sql_query(
        "SELECT pm.id, pm.roll_no, s.name, pm.subject, pm.marks_obtained, pm.max_marks FROM practical_marks pm JOIN students s ON pm.roll_no = s.roll_no WHERE pm.subject=?", 
        conn, params=(sel_subject,)
    )
    conn.close()
    st.subheader("Saved Practical Marks")
    st.dataframe(prac_df, use_container_width=True)

# ==========================================
# MODULE 4: ATTENDANCE TRACKING
# ==========================================
elif menu_choice == "📅 Attendance Tracking":
    st.header("📅 Daily & Lab Attendance Tracking")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        att_course = st.selectbox("Course", ["BCA", "B.Tech", "B.Com", "MCA"], key="att_c")
    with col2:
        att_sem = st.number_input("Semester", min_value=1, max_value=8, value=1, key="att_s")
    with col3:
        att_date = st.date_input("Attendance Date")

    subjects = get_subjects_for_course_sem(att_course, att_sem)
    att_subject = st.selectbox("Subject/Lab", subjects, key="att_sub")

    conn = get_connection()
    students = pd.read_sql_query("SELECT roll_no, name FROM students WHERE course=? AND semester=?", 
                                 conn, params=(att_course, att_sem))
    conn.close()

    if not students.empty:
        st.subheader("Mark Attendance Roster")
        attendance_data = {}
        
        # Display roster with radio buttons for Present/Absent
        for idx, row in students.iterrows():
            c_name, c_status = st.columns([3, 2])
            with c_name:
                st.write(f"**{row['roll_no']}** - {row['name']}")
            with c_status:
                attendance_data[row['roll_no']] = st.radio(
                    "Status", ["Present", "Absent"], key=f"att_{row['roll_no']}", horizontal=True, label_visibility="collapsed"
                )
        
        if st.button("Save Batch Attendance", type="primary"):
            conn = get_connection()
            cursor = conn.cursor()
            for r_no, status in attendance_data.items():
                cursor.execute(
                    "INSERT INTO attendance (roll_no, subject, date, status) VALUES (?, ?, ?, ?)",
                    (r_no, att_subject, str(att_date), status)
                )
            conn.commit()
            conn.close()
            st.success("Attendance saved successfully for all students!")
    else:
        st.info("No students found for selected course/semester.")

# ==========================================
# MODULE 5: ANALYTICS & DEFAULTERS
# ==========================================
elif menu_choice == "📊 Analytics & Defaulters":
    st.header("📊 Attendance Analytics & Defaulters Report")
    
    tab1, tab2 = st.tabs(["⚠️ Defaulters List (<75%)", "📈 Attendance Trends Plot"])
    
    with tab1:
        threshold = st.slider("Select Defaulter Attendance Threshold (%)", min_value=50, max_value=90, value=75)
        
        conn = get_connection()
        query = """
            SELECT a.roll_no, s.name, s.course, s.semester,
                   COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present_count,
                   COUNT(*) as total_classes,
                   (COUNT(CASE WHEN a.status = 'Present' THEN 1 END) * 100.0 / COUNT(*)) as percentage
            FROM attendance a
            JOIN students s ON a.roll_no = s.roll_no
            GROUP BY a.roll_no
            HAVING percentage < ?
        """
        defaulters_df = pd.read_sql_query(query, conn, params=(threshold,))
        conn.close()

        if not defaulters_df.empty:
            defaulters_df["percentage"] = defaulters_df["percentage"].round(2).astype(str) + "%"
            st.warning(f"Found {len(defaulters_df)} student(s) below {threshold}% attendance threshold!")
            st.dataframe(defaulters_df, use_container_width=True)
        else:
            st.success(f"No defaulters found below {threshold}% attendance threshold.")

    with tab2:
        st.subheader("Course Attendance Distribution")
        conn = get_connection()
        summary_df = pd.read_sql_query("""
            SELECT status, COUNT(*) as count 
            FROM attendance 
            GROUP BY status
        """, conn)
        conn.close()

        if not summary_df.empty:
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.bar(summary_df["status"], summary_df["count"], color=["#10B981", "#EF4444"])
            ax.set_ylabel("Count")
            ax.set_title("Overall Attendance Ratio")
            st.pyplot(fig)
        else:
            st.info("Insufficient attendance data to display chart.")

# ==========================================
# MODULE 6: FULL ASSESSMENT SEARCH
# ==========================================
elif menu_choice == "🔍 Full Assessment Search":
    st.header("🔍 Student Full Assessment Search")
    
    search_query = st.text_input("Enter Student Roll Number or Name:")
    
    if search_query:
        conn = get_connection()
        student_info = pd.read_sql_query(
            "SELECT * FROM students WHERE roll_no LIKE ? OR name LIKE ?", 
            conn, params=(f"%{search_query}%", f"%{search_query}%")
        )
        
        if not student_info.empty:
            st.success("Student Record Found!")
            roll = student_info.iloc[0]["roll_no"]
            
            # Key Details Summary Card
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Roll No", student_info.iloc[0]["roll_no"])
            col2.metric("Name", student_info.iloc[0]["name"])
            col3.metric("Course", student_info.iloc[0]["course"])
            col4.metric("Semester", student_info.iloc[0]["semester"])
            
            st.markdown("---")
            
            # Attendance Summary Calculation
            att_df = pd.read_sql_query("SELECT status FROM attendance WHERE roll_no=?", conn, params=(roll,))
            total_att = len(att_df)
            present_att = len(att_df[att_df["status"] == "Present"])
            att_pct = round((present_att / total_att * 100), 2) if total_att > 0 else 0.0
            
            # Internal & Practical Data
            int_df = pd.read_sql_query("SELECT subject, marks_obtained, max_marks FROM internal_marks WHERE roll_no=?", conn, params=(roll,))
            prac_df = pd.read_sql_query("SELECT subject, marks_obtained, max_marks FROM practical_marks WHERE roll_no=?", conn, params=(roll,))
            
            # Display Breakdown Tabs
            t1, t2, t3 = st.tabs(["📊 Attendance Overview", "📝 Internal Assessment", "🧪 Practical Marks"])
            
            with t1:
                st.metric("Attendance Percentage", f"{att_pct}%", f"{present_att}/{total_att} Classes Attended")
            
            with t2:
                if not int_df.empty:
                    st.dataframe(int_df, use_container_width=True)
                else:
                    st.info("No internal marks records found.")
                    
            with t3:
                if not prac_df.empty:
                    st.dataframe(prac_df, use_container_width=True)
                else:
                    st.info("No practical marks records found.")
            
        else:
            st.error("No student matching the query was found.")
        
        conn.close()

        
