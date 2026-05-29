from functools import wraps
import json
import os
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_from_directory, session, url_for

from algorithm import buildGraduationPlan
from graph import study_plan_graph


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
COURSES_FILE = DATA_DIR / "courses.json"
STUDENTS_FILE = DATA_DIR / "students.json"


def load_json(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_courses():
    return load_json(COURSES_FILE)


def load_students():
    return load_json(STUDENTS_FILE)


def find_student(student_number):
    for student in load_students():
        if student.get("student_number") == student_number:
            return student
    return None


def render_login(error=None, student_number=""):
    return render_template(
        "login.html",
        error=error,
        student_number=student_number,
    )


def normalize_student_for_algorithm(student, selected_courses=None):
    in_progress = selected_courses
    if in_progress is None:
        in_progress = student.get("in_progress_courses", [])

    return {
        "current_year": student.get("year_level", 1),
        "semester": student.get("current_semester", "1st"),
        "completed_courses": student.get("completed_courses", []),
        "in_progress_courses": in_progress,
    }


def prerequisites_completed(course, completed_courses):
    for prereq in course.get("prerequisites", []):
        if prereq not in completed_courses:
            return False
    return True


def eligible_courses_for_student(student, courses):
    completed_courses = set(student.get("completed_courses", []))
    in_progress_courses = set(student.get("in_progress_courses", []))
    
    projected_completed = completed_courses | in_progress_courses

    current_semester = student.get("current_semester", "1st")
    target_semester = "2nd" if current_semester == "1st" else "1st"

    eligible = []
    for course in courses:
        code = course.get("course_code")
        
        if not code or code in projected_completed:
            continue
            
        if target_semester not in course.get("semester_availability", []):
            continue
            
        if not prerequisites_completed(course, projected_completed):
            continue
            
        eligible.append(course)
        
    return eligible


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "student_number" not in session:
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapped_view


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
application = app


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    student_number = request.form.get("student-number", "").strip()
    password = request.form.get("password", "")

    student = find_student(student_number)
    if not student:
        return render_login("No student found.", student_number)

    if student.get("password") != password:
        return render_login("Incorrect password.", student_number)

    session.clear()
    session["student_number"] = student_number
    session["selected_courses"] = []
    return redirect(url_for("proposal"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/proposal", methods=["GET", "POST"])
@login_required
def proposal():
    student = find_student(session["student_number"])
    if student is None:
        session.clear()
        return redirect(url_for("index"))

    courses = load_courses()
    eligible_courses = eligible_courses_for_student(student, courses)

    if request.method == "POST":
        selected_courses = request.form.getlist("selected_courses")
        eligible_codes = {course["course_code"] for course in eligible_courses}
        selected_courses = [code for code in selected_courses if code in eligible_codes]
        session["selected_courses"] = selected_courses
        return redirect(url_for("dashboard"))

    return render_template(
        "proposal.html",
        student=student,
        eligible_courses=eligible_courses,
        selected_courses=session.get("selected_courses", []),
    )


@app.route("/dashboard")
@login_required
def dashboard():
    student = find_student(session["student_number"])
    if student is None:
        session.clear()
        return redirect(url_for("index"))

    selected_courses = session.get("selected_courses") or None
    courses = load_courses()
    algorithm_input = normalize_student_for_algorithm(student, selected_courses=selected_courses)
    result = buildGraduationPlan(courses, algorithm_input)
    
    study_plan_graph(
        courses,
        student.get("completed_courses", []),
        student.get("in_progress_courses", []),
        session.get("selected_courses", []),
    )

    return render_template(
        "dashboard.html",
        student=student,
        selected_courses=session.get("selected_courses", []),
        result=result,
        courses=courses
    )


@app.route("/plan")
@login_required
def plan_redirect():
    return redirect(url_for("proposal"))


@app.route("/<path:filename>")
def template_assets(filename):
    asset_path = BASE_DIR / "templates" / filename
    if asset_path.exists() and asset_path.is_file():
        return send_from_directory(BASE_DIR / "templates", filename)
    return ("Not Found", 404)


if __name__ == "__main__":
    app.run(debug=True)
