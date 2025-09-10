


from flask import jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

from app import app
from app.models import User, Task, Inventory, Expense
# API route to add or update inventory for the logged-in user

from flask import render_template, request, redirect, url_for, flash, session
from flask import render_template

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "iamakhilyt2005@gmail.com"
SENDER_PASSWORD = "fwwnckpgduuknunh"
RECEIVER_EMAIL = "akhilesh112606@gmail.com"

def send_task_reminder_email(user, tasks_today):
    """Send email notification for tasks due today"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"Farm Task Reminder - {len(tasks_today)} Task(s) Due Today"
        
        # Create email body
        body = f"""
Hello {user.username},

You have {len(tasks_today)} task(s) due today ({date.today().strftime('%Y-%m-%d')}):

"""
        for task in tasks_today:
            body += f"• {task.title}"
            if task.notes:
                body += f" - {task.notes}"
            body += "\n"
        
        body += """
Please log in to your Farm Task & Inventory Manager to manage your tasks.

Best regards,
Farm Management System
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Setup SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        server.quit()
        
        print(f"Task reminder email sent successfully to {RECEIVER_EMAIL}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

@app.route("/")
def home():
    return render_template("landing.html")


# Route to render the login page

# Dashboard route
@app.route("/dashboard")
def dashboard():
    user = None
    tasks = []
    inventory = []
    expenses = []
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user:
            tasks = Task.query.filter_by(user_id=user.id).all()
            inventory = Inventory.query.filter_by(user_id=user.id).all()
            expenses = Expense.query.filter_by(user_id=user.id).all()
            
            # Check for tasks due today and send email notification
            today = date.today().strftime('%Y-%m-%d')
            tasks_today = [task for task in tasks if task.date == today]
            
            if tasks_today:
                # Send email notification
                email_sent = send_task_reminder_email(user, tasks_today)
                if email_sent:
                    flash(f"Email notification sent! You have {len(tasks_today)} task(s) due today.", "info")
                else:
                    flash(f"You have {len(tasks_today)} task(s) due today. (Email notification failed)", "warning")
    
    return render_template(
        "dashboard.html",
        username=user.username if user else None,
        tasks=tasks,
        inventory=inventory,
        expenses=expenses
    )
# API route to add an expense for the logged-in user
@app.route("/api/expense", methods=["POST"])
def api_add_expense():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json()
    item = data.get("item") if data else None
    amount = data.get("amount") if data else None
    season = data.get("season") if data else None
    if not item or amount is None or not season:
        return jsonify({"success": False, "error": "Item, amount, and season required"}), 400
    from app import db
    new_exp = Expense(item=item, amount=amount, season=season, user_id=user.id)
    db.session.add(new_exp)
    db.session.commit()
    return jsonify({"success": True, "created": True, "id": new_exp.id, "item": new_exp.item, "amount": new_exp.amount, "season": new_exp.season})

# API route to delete an expense for the logged-in user
@app.route("/api/delete_expense", methods=["POST"])
def api_delete_expense():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json()
    exp_id = data.get("exp_id") if data else None
    if not exp_id:
        return jsonify({"success": False, "error": "No expense specified"}), 400
    from app import db
    expense = Expense.query.filter_by(id=exp_id, user_id=user.id).first()
    if not expense:
        return jsonify({"success": False, "error": "Expense not found or not authorized"}), 404
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"success": True})

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

@app.route("/api/inventory", methods=["POST"])
def api_add_or_update_inventory():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json()
    item = data.get("item") if data else None
    quantity = data.get("quantity") if data else None
    if not item or quantity is None:
        return jsonify({"success": False, "error": "Item and quantity required"}), 400
    from app import db
    inv = Inventory.query.filter_by(user_id=user.id, item=item).first()
    if inv:
        # Add to existing quantity instead of replacing
        inv.quantity += quantity
        db.session.commit()
        return jsonify({"success": True, "updated": True, "id": inv.id, "item": inv.item, "quantity": inv.quantity})
    else:
        new_inv = Inventory(item=item, quantity=quantity, user_id=user.id)
        db.session.add(new_inv)
        db.session.commit()
        return jsonify({"success": True, "created": True, "id": new_inv.id, "item": new_inv.item, "quantity": new_inv.quantity})

# API route to delete an inventory item for the logged-in user (AJAX/JS)
@app.route("/api/delete_inventory", methods=["POST"])
def api_delete_inventory():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json()
    inv_id = data.get("inv_id") if data else None
    if not inv_id:
        return jsonify({"success": False, "error": "No inventory item specified"}), 400
    from app import db
    inv = Inventory.query.filter_by(id=inv_id, user_id=user.id).first()
    if not inv:
        return jsonify({"success": False, "error": "Inventory item not found or not authorized"}), 404
    db.session.delete(inv)
    db.session.commit()
    return jsonify({"success": True})

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
    # Check if a task with the same title exists for this user
    existing_task = Task.query.filter_by(user_id=user.id, title=title).first()
    if existing_task:
        existing_task.date = date
        existing_task.notes = notes
        db.session.commit()
        flash("Task updated successfully!", "success")
    else:
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

# API route to manually send task reminders
@app.route("/api/send_reminder", methods=["POST"])
def api_send_reminder():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    # Get all tasks for the user
    tasks = Task.query.filter_by(user_id=user.id).all()
    today = date.today().strftime('%Y-%m-%d')
    tasks_today = [task for task in tasks if task.date == today]
    
    if not tasks_today:
        return jsonify({"success": True, "message": "No tasks due today"})
    
    # Send email notification
    email_sent = send_task_reminder_email(user, tasks_today)
    
    if email_sent:
        return jsonify({"success": True, "message": f"Reminder email sent for {len(tasks_today)} task(s) due today"})
    else:
        return jsonify({"success": False, "error": "Failed to send reminder email"})

# API route to get seasonal report data
@app.route("/api/seasonal_report", methods=["GET"])
def api_seasonal_report():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    # Get all user data
    tasks = Task.query.filter_by(user_id=user.id).all()
    inventory = Inventory.query.filter_by(user_id=user.id).all()
    expenses = Expense.query.filter_by(user_id=user.id).all()
    
    # Process tasks data
    tasks_data = []
    tasks_by_status = {"pending": 0, "completed": 0}
    for task in tasks:
        task_data = {
            "id": task.id,
            "title": task.title,
            "date": task.date,
            "notes": task.notes or ""
        }
        tasks_data.append(task_data)
        
        # Check if task is overdue or due today
        task_date = datetime.strptime(task.date, '%Y-%m-%d').date()
        if task_date <= date.today():
            tasks_by_status["completed"] += 1
        else:
            tasks_by_status["pending"] += 1
    
    # Process inventory data
    inventory_data = []
    total_inventory_items = 0
    for inv in inventory:
        inventory_data.append({
            "id": inv.id,
            "item": inv.item,
            "quantity": inv.quantity
        })
        total_inventory_items += inv.quantity
    
    # Process expenses data
    expenses_data = []
    expenses_by_season = {"kharif": 0, "rabi": 0, "zaid": 0}
    total_expenses = 0
    for expense in expenses:
        expense_data = {
            "id": expense.id,
            "item": expense.item,
            "amount": expense.amount,
            "season": expense.season
        }
        expenses_data.append(expense_data)
        expenses_by_season[expense.season] += expense.amount
        total_expenses += expense.amount
    
    # Create comprehensive report
    report_data = {
        "user_info": {
            "username": user.username,
            "user_id": user.id
        },
        "summary": {
            "total_tasks": len(tasks_data),
            "pending_tasks": tasks_by_status["pending"],
            "completed_tasks": tasks_by_status["completed"],
            "total_inventory_items": len(inventory_data),
            "total_inventory_quantity": total_inventory_items,
            "total_expenses": total_expenses,
            "expenses_by_season": expenses_by_season
        },
        "tasks": tasks_data,
        "inventory": inventory_data,
        "expenses": expenses_data,
        "generated_on": date.today().strftime('%Y-%m-%d'),
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return jsonify({"success": True, "data": report_data})

# Route to display seasonal report page
@app.route("/seasonal_report")
def seasonal_report_page():
    if "user_id" not in session:
        flash("You must be logged in to view the seasonal report.", "danger")
        return redirect(url_for("login"))
    
    return render_template("seasonal_report.html")

# Route to display crop planning page
@app.route("/crop_planning")
def crop_planning_page():
    if "user_id" not in session:
        flash("You must be logged in to view the crop planning guide.", "danger")
        return redirect(url_for("login"))
    
    return render_template("crop_planning.html")



