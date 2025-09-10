


from flask import jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import requests
from collections import defaultdict, Counter
from statistics import mean
import numpy as np
import pickle

from app import app
from app.models import User, Task, Inventory, Expense, Journal
# API route to add or update inventory for the logged-in user

from flask import render_template, request, redirect, url_for, flash, session
from flask import render_template

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "iamakhilyt2005@gmail.com"
SENDER_PASSWORD = "fwwnckpgduuknunh"
RECEIVER_EMAIL = "akhilesh112606@gmail.com"

# Mock ML model data (replace with actual trained model loading)
# For demonstration, we'll use a simple rule-based system
def load_ml_model():
    """Mock function to simulate loading ML model and scaler"""
    # In a real implementation, you would load your trained model here:
    # model = pickle.load(open('crop_model.pkl', 'rb'))
    # scaler = pickle.load(open('scaler.pkl', 'rb'))
    
    # Mock targets (crop names)
    targets = ['Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Maize', 'Pulses', 'Mustard', 'Barley']
    return None, None, targets

# Load model (mock for now)
model, scaler, targets = load_ml_model()

# Debug print for model loading
print(f"\n🚀 FARM MANAGEMENT SYSTEM - ML MODULE INITIALIZED")
print(f"Model loaded: {'✅ Yes' if model is not None else '❌ No (using mock predictions)'}")
print(f"Scaler loaded: {'✅ Yes' if scaler is not None else '❌ No (using mock predictions)'}")
print(f"Available crop targets: {targets}")
print(f"=================================================\n")

def predict_crops_mock(temperature, humidity, rainfall):
    """Mock ML prediction based on weather conditions"""
    predictions = []
    
    # Debug print for input parameters
    print(f"\n=== ML PREDICTION DEBUG ===")
    print(f"Input Weather Data:")
    print(f"  Temperature: {temperature}°C")
    print(f"  Humidity: {humidity}%")
    print(f"  Rainfall: {rainfall}mm")
    
    # Rule-based mock predictions based on weather conditions
    if temperature > 30 and humidity > 70 and rainfall > 150:
        # Hot, humid, high rainfall - good for rice
        predictions = [
            ("Rice", 0.92),
            ("Sugarcane", 0.85),
            ("Cotton", 0.78)
        ]
        print(f"Condition: Hot, humid, high rainfall")
    elif temperature < 25 and rainfall < 100:
        # Cool, low rainfall - good for wheat
        predictions = [
            ("Wheat", 0.91),
            ("Barley", 0.83),
            ("Mustard", 0.76)
        ]
        print(f"Condition: Cool, low rainfall")
    elif temperature > 25 and humidity < 60:
        # Moderate temp, low humidity
        predictions = [
            ("Cotton", 0.87),
            ("Maize", 0.82),
            ("Pulses", 0.74)
        ]
        print(f"Condition: Moderate temp, low humidity")
    else:
        # Default predictions
        predictions = [
            ("Maize", 0.85),
            ("Pulses", 0.80),
            ("Rice", 0.75)
        ]
        print(f"Condition: Default predictions")
    
    # Debug print for predictions
    print(f"\nTop 3 Crop Predictions:")
    for i, (crop, confidence) in enumerate(predictions, 1):
        print(f"  {i}. {crop}: {confidence*100:.1f}% confidence")
    print(f"========================\n")
    
    return predictions

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
    journal_entries = Journal.query.filter_by(user_id=user.id).order_by(Journal.date.desc()).all()
    
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
    
    # Process journal entries data
    journal_data = []
    activities_count = {}
    for entry in journal_entries:
        journal_entry = {
            "id": entry.id,
            "activity": entry.activity,
            "activity_details": entry.activity_details,
            "date": entry.date
        }
        journal_data.append(journal_entry)
        
        # Count activities
        if entry.activity in activities_count:
            activities_count[entry.activity] += 1
        else:
            activities_count[entry.activity] = 1
    
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
            "expenses_by_season": expenses_by_season,
            "total_journal_entries": len(journal_data),
            "activities_count": activities_count
        },
        "tasks": tasks_data,
        "inventory": inventory_data,
        "expenses": expenses_data,
        "journal": journal_data,
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

# API route to get weather forecast data
@app.route("/api/weather_forecast", methods=["GET"])
def api_weather_forecast():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    # Get location parameters from request
    lat = request.args.get('lat', '16.5449')  # Default to Bhimavaram
    lon = request.args.get('lon', '81.5212')
    location_name = request.args.get('location', 'Bhimavaram')
    
    API_KEY = "a1b2394289828346d954d42d376a1033"  # Your OpenWeatherMap API key
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Group entries by date
            days = defaultdict(list)
            for entry in data["list"]:
                date_str = entry["dt_txt"].split()[0]
                days[date_str].append(entry)
            
            # Process next 4 days
            forecast_data = []
            for i, (date_str, entries) in enumerate(list(days.items())[:4], 1):
                temps = [e["main"]["temp"] for e in entries]
                avg_temp = round(mean(temps), 1)
                
                # Most common weather description
                weather_descs = [e["weather"][0]["description"] for e in entries]
                most_common_weather = Counter(weather_descs).most_common(1)[0][0]
                
                # Rain probability: use max pop (probability of precipitation) for the day
                pops = [e.get("pop", 0) for e in entries]
                rain_percent = round(max(pops) * 100) if pops else 0
                
                # Get weather icon
                weather_icons = [e["weather"][0]["icon"] for e in entries]
                most_common_icon = Counter(weather_icons).most_common(1)[0][0]
                
                # Format date for display
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%b %d')
                day_name = date_obj.strftime('%A')
                
                forecast_data.append({
                    "day": i,
                    "date": formatted_date,
                    "day_name": day_name,
                    "avg_temp": avg_temp,
                    "weather": most_common_weather.title(),
                    "rain_percent": rain_percent,
                    "icon": most_common_icon
                })
            
            return jsonify({
                "success": True, 
                "forecast": forecast_data,
                "location": location_name,
                "coordinates": {"lat": float(lat), "lon": float(lon)}
            })
        else:
            return jsonify({"success": False, "error": f"API Error: {r.status_code}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Request failed: {str(e)}"}), 500

# API route to get coordinates from city name
@app.route("/api/geocode", methods=["GET"])
def api_geocode():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    city_name = request.args.get('city')
    if not city_name:
        return jsonify({"success": False, "error": "City name required"}), 400
    
    API_KEY = "a1b2394289828346d954d42d376a1033"  # Your OpenWeatherMap API key
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city_name, "limit": 1, "appid": API_KEY}
    
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                location = data[0]
                return jsonify({
                    "success": True,
                    "location": {
                        "name": location.get("name"),
                        "state": location.get("state", ""),
                        "country": location.get("country", ""),
                        "lat": location.get("lat"),
                        "lon": location.get("lon")
                    }
                })
            else:
                return jsonify({"success": False, "error": "Location not found"}), 404
        else:
            return jsonify({"success": False, "error": f"Geocoding API Error: {r.status_code}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Geocoding failed: {str(e)}"}), 500

# ML Prediction route
@app.route('/api/predict', methods=['POST'])
def predict():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    # Get data from request
    data = request.get_json()
    
    print(f"\n🤖 ML PREDICTION API CALLED")
    print(f"Request data: {data}")
    
    # Validate required fields
    if not data or 'temperature' not in data or 'humidity' not in data or 'rainfall' not in data:
        print(f"❌ Missing required fields in request")
        return jsonify({"success": False, "error": "Temperature, humidity, and rainfall required"}), 400
    
    try:
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        rainfall = float(data['rainfall'])
        
        print(f"Parsed input values:")
        print(f"  Temperature: {temperature}")
        print(f"  Humidity: {humidity}")
        print(f"  Rainfall: {rainfall}")
        
        # For now, use mock prediction (replace with actual ML model)
        if model is not None and scaler is not None:
            # Real ML prediction code (when you have trained model)
            print(f"Using trained ML model...")
            input_data = np.array([[temperature, humidity, rainfall]])
            input_scaled = scaler.transform(input_data)
            probs = model.predict_proba(input_scaled)[0]
            top3_idx = probs.argsort()[-3:][::-1]
            top3_crops = [(targets[i], float(probs[i])) for i in top3_idx]
        else:
            # Mock prediction for demonstration
            print(f"Using mock ML prediction (no trained model loaded)...")
            top3_crops = predict_crops_mock(temperature, humidity, rainfall)
        
        print(f"✅ Prediction completed successfully!")
        print(f"Returning top 3 crops: {top3_crops}")
        
        return jsonify({
            "success": True,
            "top3_crops": top3_crops,
            "weather_data": {
                "temperature": temperature,
                "humidity": humidity,
                "rainfall": rainfall
            }
        })
        
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        return jsonify({"success": False, "error": f"Invalid numeric values: {str(e)}"}), 400
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return jsonify({"success": False, "error": f"Prediction failed: {str(e)}"}), 500

# API route to get ML predictions based on current weather
@app.route("/api/crop_recommendations", methods=["GET"])
def api_crop_recommendations():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    # Get location parameters
    lat = request.args.get('lat', '16.5449')
    lon = request.args.get('lon', '81.5212')
    
    print(f"\n🌍 FETCHING CROP RECOMMENDATIONS")
    print(f"Location: Lat {lat}, Lon {lon}")
    
    API_KEY = "a1b2394289828346d954d42d376a1033"
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    
    try:
        # Get current weather data
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            weather_data = r.json()
            
            # Extract weather parameters
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            
            # For rainfall, we'll use a default or recent rainfall data
            # In a real app, you might want to get historical rainfall data
            rainfall = weather_data.get('rain', {}).get('1h', 0) * 24 * 30  # Convert to monthly estimate
            if rainfall == 0:
                # Default rainfall based on season/location
                current_month = datetime.now().month
                if current_month in [6, 7, 8, 9]:  # Monsoon months
                    rainfall = 200
                elif current_month in [10, 11, 12, 1, 2]:  # Winter months
                    rainfall = 50
                else:  # Summer months
                    rainfall = 30
            
            print(f"Weather API Response:")
            print(f"  Location: {weather_data.get('name', 'Unknown')}")
            print(f"  Temperature: {temperature}°C")
            print(f"  Humidity: {humidity}%")
            print(f"  Calculated Rainfall: {rainfall}mm (Season-based)")
            
            # Get ML predictions
            predictions = predict_crops_mock(temperature, humidity, rainfall)
            
            print(f"✅ Crop recommendations generated successfully!")
            
            return jsonify({
                "success": True,
                "recommendations": predictions,
                "weather_data": {
                    "temperature": temperature,
                    "humidity": humidity,
                    "rainfall": rainfall,
                    "location": weather_data.get('name', 'Unknown')
                }
            })
        else:
            print(f"❌ Weather API Error: {r.status_code}")
            return jsonify({"success": False, "error": f"Weather API Error: {r.status_code}"}), 500
            
    except Exception as e:
        print(f"❌ Error getting crop recommendations: {str(e)}")
        return jsonify({"success": False, "error": f"Failed to get recommendations: {str(e)}"}), 500

# API route to add a journal entry for the logged-in user
@app.route("/api/journal", methods=["POST"])
def api_add_journal_entry():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    data = request.get_json()
    activity = data.get("activity") if data else None
    activity_details = data.get("activity_details") if data else None
    date = data.get("date") if data else None
    
    if not activity or not activity_details or not date:
        return jsonify({"success": False, "error": "Activity, activity details, and date required"}), 400
    
    # Validate activity type
    valid_activities = ["planting", "watering", "fertilizing", "pest-control", "harvesting", "soil-prep"]
    if activity.lower() not in valid_activities:
        return jsonify({"success": False, "error": "Invalid activity type"}), 400
    
    from app import db
    new_entry = Journal(
        activity=activity, 
        activity_details=activity_details, 
        date=date, 
        user_id=user.id
    )
    db.session.add(new_entry)
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "created": True, 
        "id": new_entry.id, 
        "activity": new_entry.activity, 
        "activity_details": new_entry.activity_details,
        "date": new_entry.date
    })

# API route to get all journal entries for the logged-in user
@app.route("/api/journal", methods=["GET"])
def api_get_journal_entries():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    # Get all journal entries for the user, ordered by date descending
    entries = Journal.query.filter_by(user_id=user.id).order_by(Journal.date.desc()).all()
    
    entries_data = [
        {
            "id": entry.id,
            "activity": entry.activity,
            "activity_details": entry.activity_details,
            "date": entry.date
        }
        for entry in entries
    ]
    
    return jsonify({"success": True, "entries": entries_data})

# API route to delete a journal entry for the logged-in user
@app.route("/api/delete_journal", methods=["POST"])
def api_delete_journal_entry():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    data = request.get_json()
    entry_id = data.get("entry_id") if data else None
    
    if not entry_id:
        return jsonify({"success": False, "error": "No journal entry specified"}), 400
    
    from app import db
    entry = Journal.query.filter_by(id=entry_id, user_id=user.id).first()
    
    if not entry:
        return jsonify({"success": False, "error": "Journal entry not found or not authorized"}), 404
    
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({"success": True})

# Route to display crop planning page
@app.route("/crop_planning")
def crop_planning_page():
    if "user_id" not in session:
        flash("You must be logged in to view the crop planning guide.", "danger")
        return redirect(url_for("login"))
    
    return render_template("crop_planning.html")



