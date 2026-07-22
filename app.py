from flask import Flask, render_template, request, redirect, url_for

from firebase_config import db

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll = request.form.get("roll")
        name = request.form.get("name")
        course = request.form.get("course")

        if roll and name and course:
            db.collection("students").document(roll).set({
                "roll": roll,
                "name": name,
                "course": course,
            })

        return redirect(url_for("view_students"))

    return render_template("add_student.html")


@app.route("/edit_student/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    student_ref = db.collection("students").document(student_id)
    student = student_ref.get()

    if request.method == "POST":
        roll = request.form.get("roll")
        name = request.form.get("name")
        course = request.form.get("course")

        if roll and name and course:
            student_ref.set({
                "roll": roll,
                "name": name,
                "course": course,
            })
        return redirect(url_for("view_students"))

    if student.exists:
        data = student.to_dict()
        data["id"] = student_id
        return render_template("edit_student.html", student=data)

    return redirect(url_for("view_students"))


@app.route("/delete_student/<student_id>")
def delete_student(student_id):
    db.collection("students").document(student_id).delete()
    return redirect(url_for("view_students"))


@app.route("/view_students")
def view_students():
    students = db.collection("students").stream()

    student_list = []

    for student in students:
        data = student.to_dict()
        data["id"] = student.id
        data["roll"] = data.get("roll", student.id)
        data["class"] = data.get("course", "")
        student_list.append(data)

    return render_template("view_students.html", students=student_list)


if __name__ == "__main__":
    app.run(debug=True)