"""
Farm Management System Routes with PocketBase Authentication
Secure password encryption handled automatically by PocketBase
"""

from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file
from datetime import datetime, date
from collections import defaultdict, Counter
from statistics import mean
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import PocketBase service
from pocketbase_service import pb_service

# Import the original app and models for compatibility
from app import app

# Keep the PDF generation and other utilities from the original routes
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO

print(f"🛡️ POCKETBASE AUTHENTICATION SYSTEM LOADED")
print(f"Password Security: ✅ Automatic encryption by PocketBase")
print(f"Developer Safety: ✅ No access to plain text passwords")
print(f"========================================\n")

@app.route("/")
def home():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("loginName")
        password = request.form.get("loginMeta")
        
        print(f"\n🔐 POCKETBASE LOGIN ATTEMPT:")
        print(f"   Username: '{username}'")
        print(f"   Password: [HIDDEN - Protected by PocketBase]")
        
        # Authenticate with PocketBase
        auth_result = pb_service.authenticate_user(username, password)
        
        if auth_result['success']:
            # Store user info in session
            session["user_id"] = auth_result['user']['id']
            session["username"] = auth_result['user']['username']
            session["pb_token"] = auth_result['user']['token']
            
            flash("Login successful!", "success")
            print(f"✅ User '{username}' logged in successfully with PocketBase")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
            print(f"❌ Failed login attempt for username: '{username}' - {auth_result['error']}")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("signupName")
    password = request.form.get("signupPassword")
    confirm = request.form.get("signupConfirm")
    
    # Validation checks
    if not username or not password or not confirm:
        flash("Please fill all fields", "danger")
        return render_template("login.html")
    
    if password != confirm:
        flash("Passwords do not match", "danger")
        return render_template("login.html")
    
    if len(password) < 6:
        flash("Password must be at least 6 characters long", "danger")
        return render_template("login.html")
    
    # Create email from username (PocketBase requires email)
    email = f"{username}@farmmanager.local"
    
    print(f"\n📝 POCKETBASE REGISTRATION:")
    print(f"   Username: '{username}'")
    print(f"   Email: '{email}'")
    print(f"   Password: [HIDDEN - Will be encrypted by PocketBase]")
    
    # Register with PocketBase
    reg_result = pb_service.register_user(username, email, password)
    
    if reg_result['success']:
        flash("Registration successful! Please log in.", "success")
        print(f"✅ User '{username}' registered successfully with encrypted password")
        return redirect(url_for("login"))
    else:
        flash(f"Registration failed: {reg_result['error']}", "danger")
        print(f"❌ Registration failed for '{username}': {reg_result['error']}")
        return render_template("login.html")

@app.route("/logout")
def logout():
    if "username" in session:
        username = session["username"]
        print(f"👋 User '{username}' logged out")
    
    # Clear session
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access the dashboard", "danger")
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    username = session.get("username", "User")
    
    # Get user data from PocketBase
    tasks_result = pb_service.get_user_tasks(user_id)
    inventory_result = pb_service.get_user_inventory(user_id)
    expenses_result = pb_service.get_user_expenses(user_id)
    
    tasks = tasks_result.get('tasks', []) if tasks_result['success'] else []
    inventory = inventory_result.get('inventory', []) if inventory_result['success'] else []
    expenses = expenses_result.get('expenses', []) if expenses_result['success'] else []
    
    return render_template(
        "dashboard.html",
        username=username,
        tasks=tasks,
        inventory=inventory,
        expenses=expenses
    )

# API Routes for tasks
@app.route("/add_task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        flash("You must be logged in to add a task.", "danger")
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    title = request.form.get("taskTitle")
    date = request.form.get("taskDate")
    notes = request.form.get("taskNotes", "")
    
    if not title or not date:
        flash("Title and date are required.", "danger")
        return redirect(url_for("dashboard"))
    
    # Create task in PocketBase
    result = pb_service.create_task(user_id, title, date, notes)
    
    if result['success']:
        flash("Task added successfully!", "success")
    else:
        flash(f"Failed to add task: {result['error']}", "danger")
    
    return redirect(url_for("dashboard"))

@app.route("/api/inventory", methods=["POST"])
def api_add_or_update_inventory():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user_id = session["user_id"]
    data = request.get_json()
    item = data.get("item") if data else None
    quantity = data.get("quantity") if data else None
    
    if not item or quantity is None:
        return jsonify({"success": False, "error": "Item and quantity required"}), 400
    
    # Add inventory item in PocketBase
    result = pb_service.add_inventory_item(user_id, item, quantity)
    
    if result['success']:
        inventory_item = result['inventory']
        return jsonify({
            "success": True,
            result['action']: True,
            "id": inventory_item.id,
            "item": inventory_item.item,
            "quantity": inventory_item.quantity
        })
    else:
        return jsonify({"success": False, "error": result['error']}), 500

@app.route("/api/expense", methods=["POST"])
def api_add_expense():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user_id = session["user_id"]
    data = request.get_json()
    item = data.get("item") if data else None
    amount = data.get("amount") if data else None
    season = data.get("season") if data else None
    
    if not item or amount is None or not season:
        return jsonify({"success": False, "error": "Item, amount, and season required"}), 400
    
    # Add expense in PocketBase
    result = pb_service.add_expense(user_id, item, amount, season)
    
    if result['success']:
        expense = result['expense']
        return jsonify({
            "success": True,
            "created": True,
            "id": expense.id,
            "item": expense.item,
            "amount": expense.amount,
            "season": expense.season
        })
    else:
        return jsonify({"success": False, "error": result['error']}), 500

@app.route("/api/journal", methods=["POST"])
def api_add_journal_entry():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user_id = session["user_id"]
    data = request.get_json()
    activity = data.get("activity") if data else None
    activity_details = data.get("activity_details") if data else None
    date = data.get("date") if data else None
    
    if not activity or not activity_details or not date:
        return jsonify({"success": False, "error": "Activity, details, and date required"}), 400
    
    # Validate activity type
    valid_activities = ["planting", "watering", "fertilizing", "pest-control", "harvesting", "soil-prep"]
    if activity.lower() not in valid_activities:
        return jsonify({"success": False, "error": "Invalid activity type"}), 400
    
    # Add journal entry in PocketBase
    result = pb_service.add_journal_entry(user_id, activity, activity_details, date)
    
    if result['success']:
        entry = result['journal']
        return jsonify({
            "success": True,
            "created": True,
            "id": entry.id,
            "activity": entry.activity,
            "activity_details": entry.activity_details,
            "date": entry.date
        })
    else:
        return jsonify({"success": False, "error": result['error']}), 500

@app.route("/api/journal", methods=["GET"])
def api_get_journal_entries():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user_id = session["user_id"]
    
    # Get journal entries from PocketBase
    result = pb_service.get_user_journal(user_id)
    
    if result['success']:
        entries_data = []
        for entry in result['journal']:
            entries_data.append({
                "id": entry.id,
                "activity": entry.activity,
                "activity_details": entry.activity_details,
                "date": entry.date
            })
        
        return jsonify({"success": True, "entries": entries_data})
    else:
        return jsonify({"success": False, "error": result['error']}), 500

# Additional routes can be added here for other functionality
# Seasonal reports, crop planning, etc. can be implemented similarly

@app.route("/seasonal_report")
def seasonal_report_page():
    if "user_id" not in session:
        flash("You must be logged in to view the seasonal report.", "danger")
        return redirect(url_for("login"))
    
    return render_template("seasonal_report.html")

@app.route("/crop_planning")
def crop_planning_page():
    if "user_id" not in session:
        flash("You must be logged in to view crop planning.", "danger")
        return redirect(url_for("login"))
    
    return render_template("crop_planning.html")

# Test PocketBase connection on startup
if pb_service.test_connection():
    print("🎉 PocketBase authentication system ready!")
    print("🔒 All passwords are automatically encrypted and secure!")
else:
    print("⚠️ Warning: PocketBase server not accessible. Please start PocketBase server.")
    print("   Run: ./pocketbase.exe serve --http=127.0.0.1:8091")
