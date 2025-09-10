"""
Farm Management System with PocketBase Authentication
🔒 Secure password encryption - developers cannot access plain text passwords
"""

from flask import Flask, request, render_template, redirect, url_for, session, jsonify, make_response
import os
from datetime import datetime

# Create Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

print("🌾 FARM MANAGEMENT SYSTEM - POCKETBASE EDITION")
print("🔐 Authentication: PocketBase (Automatic Encryption)")
print("🛡️ Password Security: Developer-Safe")
print("=" * 50)

# Import PocketBase service
from pocketbase_service import pb_service

print("🚀 System ready with encrypted authentication!")

@app.route("/")
def landing():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("loginName")
        password = request.form.get("loginMeta")
        
        print(f"\n🔐 POCKETBASE LOGIN ATTEMPT:")
        print(f"   Username: '{username}'")
        print(f"   Password: [HIDDEN - Protected by PocketBase]")
        
        # Authenticate with PocketBase
        user = pb_service.authenticate_user(username, password)
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            print(f"✅ Login successful for user: {username}")
            return redirect(url_for('dashboard'))
        else:
            print(f"❌ Login failed for user: {username}")
            return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        print(f"\n📝 POCKETBASE REGISTRATION ATTEMPT:")
        print(f"   Username: '{username}'")
        print(f"   Email: '{email}'")
        print(f"   Password: [HIDDEN - Will be encrypted by PocketBase]")
        
        # Register with PocketBase
        user = pb_service.register_user(username, email, password)
        
        if user:
            print(f"✅ Registration successful for user: {username}")
            return redirect(url_for('login'))
        else:
            print(f"❌ Registration failed for user: {username}")
            return render_template("register.html", error="Registration failed")
    
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user data from PocketBase
    tasks = pb_service.get_user_tasks(user_id)
    inventory = pb_service.get_user_inventory(user_id)
    expenses = pb_service.get_user_expenses(user_id)
    journal = pb_service.get_user_journal(user_id)
    
    return render_template('index.html', 
                         tasks=tasks, 
                         inventory=inventory,
                         expenses=expenses,
                         journal=journal)

@app.route("/logout")
def logout():
    session.clear()
    print("🚪 User logged out")
    return redirect(url_for('login'))

@app.route("/add_task", methods=["POST"])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    title = request.form.get("title")
    date = request.form.get("date")
    notes = request.form.get("notes", "")
    
    task = pb_service.create_task(user_id, title, date, notes)
    
    if task:
        print(f"✅ Task created: {title}")
    else:
        print(f"❌ Failed to create task: {title}")
    
    return redirect(url_for('dashboard'))

@app.route("/add_inventory", methods=["POST"])
def add_inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    item = request.form.get("item")
    quantity = request.form.get("quantity")
    
    inventory_item = pb_service.add_inventory_item(user_id, item, int(quantity))
    
    if inventory_item:
        print(f"✅ Inventory added: {item} x{quantity}")
    else:
        print(f"❌ Failed to add inventory: {item}")
    
    return redirect(url_for('dashboard'))

@app.route("/add_expense", methods=["POST"])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    item = request.form.get("item")
    amount = request.form.get("amount")
    season = request.form.get("season")
    
    expense = pb_service.add_expense(user_id, item, float(amount), season)
    
    if expense:
        print(f"✅ Expense added: {item} - ₹{amount}")
    else:
        print(f"❌ Failed to add expense: {item}")
    
    return redirect(url_for('dashboard'))

@app.route("/add_journal", methods=["POST"])
def add_journal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    activity = request.form.get("activity")
    activity_details = request.form.get("activity_details")
    date = request.form.get("date")
    
    journal_entry = pb_service.add_journal_entry(user_id, activity, activity_details, date)
    
    if journal_entry:
        print(f"✅ Journal entry added: {activity}")
    else:
        print(f"❌ Failed to add journal entry: {activity}")
    
    return redirect(url_for('dashboard'))

# PDF Routes (keeping from original system)
@app.route("/download_seasonal_report")
def download_seasonal_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    expenses = pb_service.get_user_expenses(user_id)
    
    # Generate PDF with expenses data
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # PDF generation logic here
    p.drawString(100, 750, "🌾 Seasonal Expense Report")
    p.drawString(100, 720, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    y_pos = 680
    total = 0
    for expense in expenses:
        p.drawString(100, y_pos, f"{expense.item}: ₹{expense.amount} ({expense.season})")
        total += expense.amount
        y_pos -= 20
    
    p.drawString(100, y_pos - 20, f"Total: ₹{total}")
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=seasonal_report.pdf'
    
    return response

if __name__ == "__main__":
    print("\n🚀 Starting Farm Management System...")
    print("🔗 Access at: http://localhost:5000")
    print("🔒 Login system: PocketBase with encrypted passwords")
    print("🛡️ Developer-safe: No access to plain text passwords")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
