

from flask import jsonify


from app import app
from app.models import User, Task
from flask import render_template, request, redirect, url_for, flash, session
from flask import render_template
@app.route("/")
def home():
    return "Hello, Hackathon!"


# Route to render the login page

# Dashboard route
@app.route("/dashboard")
def dashboard():
    user = None
    tasks = []
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user:
            tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template("dashboard.html", username=user.username if user else None, tasks=tasks)

# Route to delete a task for the logged-in user
@app.route("/delete_task", methods=["POST"])
def delete_task():
    if "user_id" not in session:
        flash("You must be logged in to delete a task.", "danger")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))
    task_id = request.form.get("task_id")
    if not task_id:
        flash("No task specified.", "danger")
        return redirect(url_for("dashboard"))
    from app import db
    task = Task.query.filter_by(id=task_id, user_id=user.id).first()
    if not task:
        flash("Task not found or not authorized.", "danger")
        return redirect(url_for("dashboard"))
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully!", "success")
    return redirect(url_for("dashboard"))

# API route to delete a task for the logged-in user (AJAX/JS)
@app.route("/api/delete_task", methods=["POST"])
def api_delete_task():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json()
    task_id = data.get("task_id") if data else None
    if not task_id:
        return jsonify({"success": False, "error": "No task specified"}), 400
    from app import db
    task = Task.query.filter_by(id=task_id, user_id=user.id).first()
    if not task:
        return jsonify({"success": False, "error": "Task not found or not authorized"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"success": True})

# Route to add a task for the logged-in user
@app.route("/add_task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        flash("You must be logged in to add a task.", "danger")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))
    title = request.form.get("taskTitle")
    date = request.form.get("taskDate")
    notes = request.form.get("taskNotes")
    if not title or not date:
        flash("Title and date are required.", "danger")
        return redirect(url_for("dashboard"))
    from app import db
    new_task = Task(title=title, date=date, notes=notes, user_id=user.id)
    db.session.add(new_task)
    db.session.commit()
    flash("Task added successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("loginName")
        password = request.form.get("loginMeta")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
            return render_template("login.html")
    return render_template("login.html")

# Route to get all tasks for the logged-in user (GET request, returns JSON)
@app.route("/get_tasks", methods=["GET"])
def get_tasks():
    print("-------Here-----")
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    tasks = Task.query.filter_by(user_id=user.id).all()
    tasks_data = [
        {"id": t.id, "title": t.title, "date": t.date, "notes": t.notes}
        for t in tasks
    ]
    return jsonify({"tasks": tasks_data})

# Register route for sign up form
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("signupName")
    password = request.form.get("signupPassword")
    confirm = request.form.get("signupConfirm")
    if not username or not password or not confirm:
        flash("Please fill all fields", "danger")
        return render_template("login.html")
    if password != confirm:
        flash("Passwords do not match", "danger")
        return render_template("login.html")
    existing = User.query.filter_by(username=username).first()
    if existing:
        flash("Username already exists", "danger")
        return render_template("login.html")
    user = User(username=username, password=password)
    from app import db
    db.session.add(user)
    db.session.commit()
    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("login"))


