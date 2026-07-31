import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from firebase_config import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "student-attendance-management-secret-key-2026")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Calculate stats
    student_docs = db.collection("students").stream()
    student_list = [doc.to_dict() for doc in student_docs]
    total_students = len(student_list)

    attendance_docs = db.collection("attendance").stream()
    all_attendance = [doc.to_dict() for doc in attendance_docs if doc.to_dict()]
    
    today_records = [r for r in all_attendance if r.get("date") == today_str]
    today_marked = len(today_records)
    today_present = len([r for r in today_records if r.get("status") == "Present"])
    
    today_rate = round((today_present / today_marked * 100), 1) if today_marked > 0 else 0.0

    return render_template(
        "index.html",
        total_students=total_students,
        today_date=today_str,
        today_marked=today_marked,
        today_present=today_present,
        today_rate=today_rate,
        recent_records=all_attendance[-5:][::-1]
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # Demo authentication
        if (email == "admin@school.com" and password == "admin123") or (email and password):
            session["user"] = email
            flash(f"Welcome back, {email}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/add_student", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        roll = request.form.get("roll", "").strip()
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()

        if roll and name and course:
            db.collection("students").document(roll).set({
                "roll": roll,
                "name": name,
                "course": course,
                "created_at": datetime.now().isoformat()
            })
            flash(f"Student '{name}' added successfully!", "success")
            return redirect(url_for("view_students"))
        else:
            flash("All fields are required.", "danger")

    return render_template("add_student.html")


@app.route("/edit_student/<student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    student_ref = db.collection("students").document(student_id)
    student = student_ref.get()

    if request.method == "POST":
        roll = request.form.get("roll", "").strip()
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()

        if roll and name and course:
            if roll != student_id:
                # Roll changed: create new doc and delete old doc
                db.collection("students").document(roll).set({
                    "roll": roll,
                    "name": name,
                    "course": course,
                    "updated_at": datetime.now().isoformat()
                })
                student_ref.delete()
            else:
                student_ref.set({
                    "roll": roll,
                    "name": name,
                    "course": course,
                    "updated_at": datetime.now().isoformat()
                })
            flash(f"Student details updated successfully!", "success")
            return redirect(url_for("view_students"))
        else:
            flash("All fields are required.", "danger")

    if student.exists:
        data = student.to_dict()
        data["id"] = student_id
        return render_template("edit_student.html", student=data)

    flash("Student not found.", "warning")
    return redirect(url_for("view_students"))


@app.route("/delete_student/<student_id>")
@login_required
def delete_student(student_id):
    student_ref = db.collection("students").document(student_id)
    student = student_ref.get()
    if student.exists:
        student_name = student.to_dict().get("name", "Student")
        student_ref.delete()
        flash(f"Student '{student_name}' deleted.", "info")
    else:
        flash("Student not found.", "warning")

    return redirect(url_for("view_students"))


@app.route("/view_students")
def view_students():
    query_str = request.args.get("q", "").strip().lower()
    selected_course = request.args.get("course", "").strip()

    students = db.collection("students").stream()
    student_list = []
    courses = set()

    for student in students:
        data = student.to_dict()
        data["id"] = student.id
        data["roll"] = data.get("roll", student.id)
        data["course"] = data.get("course", data.get("class", ""))
        data["class"] = data["course"]  # compatibility
        
        if data["course"]:
            courses.add(data["course"])

        # Filter by course
        if selected_course and data["course"] != selected_course:
            continue

        # Search filter
        if query_str:
            if query_str not in data["name"].lower() and query_str not in data["roll"].lower():
                continue

        student_list.append(data)

    return render_template(
        "view_students.html",
        students=student_list,
        courses=sorted(list(courses)),
        selected_course=selected_course,
        query_str=query_str
    )


@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    today_str = datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        att_date = request.form.get("date", today_str).strip()
        selected_course = request.form.get("course", "").strip()

        student_docs = db.collection("students").stream()
        saved_count = 0

        for s_doc in student_docs:
            s_data = s_doc.to_dict()
            s_id = s_doc.id
            course = s_data.get("course", s_data.get("class", ""))

            if selected_course and course != selected_course:
                continue

            status_key = f"status_{s_id}"
            if status_key in request.form:
                status_val = request.form.get(status_key)
                doc_id = f"{att_date}_{s_id}"

                db.collection("attendance").document(doc_id).set({
                    "date": att_date,
                    "student_id": s_id,
                    "roll": s_data.get("roll", s_id),
                    "student_name": s_data.get("name", "Unknown"),
                    "course": course,
                    "status": status_val,
                    "recorded_at": datetime.now().isoformat()
                })
                saved_count += 1

        flash(f"Attendance for {att_date} saved for {saved_count} student(s).", "success")
        return redirect(url_for("attendance_history", date=att_date))

    # GET request
    att_date = request.args.get("date", today_str).strip()
    selected_course = request.args.get("course", "").strip()

    student_docs = db.collection("students").stream()
    students_list = []
    courses = set()

    for s_doc in student_docs:
        s_data = s_doc.to_dict()
        s_data["id"] = s_doc.id
        s_data["roll"] = s_data.get("roll", s_doc.id)
        s_data["course"] = s_data.get("course", s_data.get("class", ""))
        
        if s_data["course"]:
            courses.add(s_data["course"])

        if selected_course and s_data["course"] != selected_course:
            continue

        students_list.append(s_data)

    # Fetch existing attendance records for this date
    attendance_records = {}
    att_docs = db.collection("attendance").stream()
    for a_doc in att_docs:
        a_data = a_doc.to_dict()
        if a_data and a_data.get("date") == att_date:
            attendance_records[a_data.get("student_id")] = a_data.get("status", "Present")

    return render_template(
        "attendance.html",
        students=students_list,
        att_date=att_date,
        courses=sorted(list(courses)),
        selected_course=selected_course,
        attendance_records=attendance_records
    )


@app.route("/attendance_history")
def attendance_history():
    selected_date = request.args.get("date", "").strip()
    selected_course = request.args.get("course", "").strip()

    att_docs = db.collection("attendance").stream()
    all_records = [doc.to_dict() for doc in att_docs if doc.to_dict()]

    dates = sorted(list({r.get("date") for r in all_records if r.get("date")}), reverse=True)
    courses = sorted(list({r.get("course") for r in all_records if r.get("course")}))

    filtered_records = all_records
    if selected_date:
        filtered_records = [r for r in filtered_records if r.get("date") == selected_date]
    if selected_course:
        filtered_records = [r for r in filtered_records if r.get("course") == selected_course]

    # Calculate student summary stats
    student_stats = {}
    for r in all_records:
        s_id = r.get("student_id")
        if not s_id:
            continue
        if s_id not in student_stats:
            student_stats[s_id] = {
                "name": r.get("student_name", "Unknown"),
                "roll": r.get("roll", s_id),
                "course": r.get("course", "-"),
                "total": 0,
                "present": 0,
                "absent": 0,
                "late": 0
            }
        
        student_stats[s_id]["total"] += 1
        status = r.get("status")
        if status == "Present":
            student_stats[s_id]["present"] += 1
        elif status == "Absent":
            student_stats[s_id]["absent"] += 1
        elif status == "Late":
            student_stats[s_id]["late"] += 1

    for s_id, stats in student_stats.items():
        if stats["total"] > 0:
            stats["rate"] = round((stats["present"] / stats["total"]) * 100, 1)
        else:
            stats["rate"] = 0.0

    return render_template(
        "attendance_history.html",
        records=filtered_records,
        dates=dates,
        courses=courses,
        selected_date=selected_date,
        selected_course=selected_course,
        student_stats=student_stats.values()
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)