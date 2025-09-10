


from flask import jsonify, send_file
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import requests
from collections import defaultdict, Counter
from statistics import mean
import numpy as np
import pickle
import openai
import google.generativeai as genai
import hashlib
import secrets
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import json

from app import app
from app.models import User, Task, Inventory, Expense, Journal

from flask import render_template, request, redirect, url_for, flash, session

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "iamakhilyt2005@gmail.com"
SENDER_PASSWORD = "fwwnckpgduuknunh"
RECEIVER_EMAIL = "akhilesh112606@gmail.com"

# OpenAI configuration
OPENAI_API_KEY = "AIzaSyDDwBz6W4X5ZN-DovooMfVRJTsMFOy0c3A"

# Initialize OpenAI client
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Google Gemini AI configuration
GEMINI_API_KEY = "AIzaSyDDwBz6W4X5ZN-DovooMfVRJTsMFOy0c3A"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

print(f"🤖 AI INTEGRATIONS INITIALIZED:")
print(f"OpenAI Client: ✅ Configured")
print(f"Google Gemini: ✅ Configured (gemini-1.5-flash)")
print(f"========================================\n")

# Simple Password Security Functions
def hash_password(password):
    """Hash a password with a random salt using SHA-256"""
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Create hash with salt
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    # Return salt and hash combined
    return f"{salt}${password_hash}"

def verify_password(password, stored_hash):
    """Verify a password against a stored hash"""
    try:
        # Handle different formats for backward compatibility
        if '$' in stored_hash:
            # Standard format: salt$hash
            salt, password_hash = stored_hash.split('$')
            new_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return new_hash == password_hash
        else:
            # Plain text password (very old format - for backward compatibility only)
            print(f"⚠️ WARNING: Plain text password detected! User should update password.")
            return password == stored_hash
    except ValueError:
        # If split fails, it might be plain text
        print(f"⚠️ WARNING: Plain text password detected! User should update password.")
        return password == stored_hash
    except Exception as e:
        print(f"⚠️ Password verification error: {e}")
        return False

print(f"🔐 PASSWORD SECURITY INITIALIZED")
print(f"Hashing Algorithm: SHA-256 with random salt")
print(f"========================================\n")

# Additional Security Functions
def is_strong_password(password):
    """Check if password meets strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    if not has_lower:
        return False, "Password must contain at least one lowercase letter"
    if not has_digit:
        return False, "Password must contain at least one number"
    if not has_special:
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def generate_seasonal_report_pdf(report_data):
    """Generate a PDF report from seasonal report data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkgreen
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Title
    story.append(Paragraph("🌾 Farm Management System - Seasonal Report", title_style))
    story.append(Spacer(1, 20))
    
    # User Information
    user_info = report_data['user_info']
    story.append(Paragraph("👤 Farmer Information", heading_style))
    story.append(Paragraph(f"<b>Farmer Name:</b> {user_info['username']}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Generated:</b> {report_data['generated_at']}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Summary Section
    summary = report_data['summary']
    story.append(Paragraph("📊 Farm Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Count'],
        ['Total Tasks', str(summary['total_tasks'])],
        ['Pending Tasks', str(summary['pending_tasks'])],
        ['Completed Tasks', str(summary['completed_tasks'])],
        ['Inventory Items', str(summary['total_inventory_items'])],
        ['Total Inventory Quantity', str(summary['total_inventory_quantity'])],
        ['Total Expenses', f"₹{summary['total_expenses']:.2f}"],
        ['Journal Entries', str(summary['total_journal_entries'])]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Seasonal Expenses
    story.append(Paragraph("💰 Seasonal Expenses Breakdown", heading_style))
    expenses_by_season = summary['expenses_by_season']
    
    expense_data = [
        ['Season', 'Amount (₹)'],
        ['Kharif', f"₹{expenses_by_season['kharif']:.2f}"],
        ['Rabi', f"₹{expenses_by_season['rabi']:.2f}"],
        ['Zaid', f"₹{expenses_by_season['zaid']:.2f}"]
    ]
    
    expense_table = Table(expense_data, colWidths=[2.5*inch, 2.5*inch])
    expense_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(expense_table)
    story.append(Spacer(1, 20))
    
    # Activities Summary
    if summary['activities_count']:
        story.append(Paragraph("🚜 Farming Activities Summary", heading_style))
        activities_data = [['Activity', 'Count']]
        for activity, count in summary['activities_count'].items():
            activities_data.append([activity.title(), str(count)])
        
        activities_table = Table(activities_data, colWidths=[3*inch, 2*inch])
        activities_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(activities_table)
        story.append(PageBreak())
    
    # Detailed Tasks
    if report_data['tasks']:
        story.append(Paragraph("📋 Task Details", heading_style))
        tasks_data = [['Task Title', 'Date', 'Notes']]
        for task in report_data['tasks'][:10]:  # Limit to first 10 tasks
            notes = task['notes'][:50] + "..." if len(task['notes']) > 50 else task['notes']
            tasks_data.append([task['title'], task['date'], notes])
        
        tasks_table = Table(tasks_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        tasks_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.mistyrose),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(tasks_table)
        story.append(Spacer(1, 20))
    
    # Inventory Details
    if report_data['inventory']:
        story.append(Paragraph("📦 Current Inventory", heading_style))
        inventory_data = [['Item', 'Quantity']]
        for item in report_data['inventory'][:15]:  # Limit to first 15 items
            inventory_data.append([item['item'], str(item['quantity'])])
        
        inventory_table = Table(inventory_data, colWidths=[3*inch, 2*inch])
        inventory_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.papayawhip),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(inventory_table)
        story.append(Spacer(1, 20))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Generated by Farm Management System", 
                          ParagraphStyle('Footer', parent=styles['Normal'], 
                                       alignment=TA_CENTER, fontSize=10, 
                                       textColor=colors.grey)))
    story.append(Paragraph(f"Report Date: {report_data['generated_on']}", 
                          ParagraphStyle('Footer', parent=styles['Normal'], 
                                       alignment=TA_CENTER, fontSize=10, 
                                       textColor=colors.grey)))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_crop_recommendations_pdf(recommendations_data, market_data=None):
    """Generate a PDF report for crop recommendations and market insights"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkgreen
    )
    
    story.append(Paragraph("🌱 Smart Crop Recommendations Report", title_style))
    story.append(Spacer(1, 20))
    
    # Weather Data
    if recommendations_data.get('weather_data'):
        weather = recommendations_data['weather_data']
        story.append(Paragraph("🌤️ Weather Analysis", styles['Heading2']))
        story.append(Paragraph(f"<b>Location:</b> {weather.get('location', 'Unknown')}", styles['Normal']))
        story.append(Paragraph(f"<b>Temperature:</b> {weather['temperature']}°C", styles['Normal']))
        story.append(Paragraph(f"<b>Humidity:</b> {weather['humidity']}%", styles['Normal']))
        story.append(Paragraph(f"<b>Rainfall:</b> {weather['rainfall']}mm", styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Crop Recommendations
    if recommendations_data.get('recommendations'):
        story.append(Paragraph("🌾 AI-Powered Crop Recommendations", styles['Heading2']))
        
        crops_data = [['Rank', 'Crop', 'Suitability Score', 'Recommendation']]
        for i, (crop, confidence) in enumerate(recommendations_data['recommendations'], 1):
            confidence_pct = f"{confidence*100:.1f}%"
            recommendation = "Highly Recommended" if confidence > 0.85 else "Recommended" if confidence > 0.75 else "Consider"
            crops_data.append([str(i), crop, confidence_pct, recommendation])
        
        crops_table = Table(crops_data, colWidths=[0.8*inch, 2*inch, 1.5*inch, 2*inch])
        crops_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(crops_table)
        story.append(Spacer(1, 20))
    
    # Market Insights
    if market_data and market_data.get('crops'):
        story.append(Paragraph("💰 Market Insights", styles['Heading2']))
        
        market_table_data = [['Crop', 'Price/Quintal', 'Trend', 'Demand', 'Market Tip']]
        for crop in market_data['crops']:
            tip = crop['market_tip'][:40] + "..." if len(crop['market_tip']) > 40 else crop['market_tip']
            market_table_data.append([
                crop['name'],
                crop['price'],
                crop['trend_percentage'],
                crop['demand'],
                tip
            ])
        
        market_table = Table(market_table_data, colWidths=[1.2*inch, 1.2*inch, 1*inch, 1*inch, 2*inch])
        market_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(market_table)
        story.append(Spacer(1, 15))
        
        if market_data.get('general_tip'):
            story.append(Paragraph("💡 General Market Advice", styles['Heading3']))
            story.append(Paragraph(market_data['general_tip'], styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Generated by Farm Management System - AI-Powered Recommendations", 
                          ParagraphStyle('Footer', parent=styles['Normal'], 
                                       alignment=TA_CENTER, fontSize=10, 
                                       textColor=colors.grey)))
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                          ParagraphStyle('Footer', parent=styles['Normal'], 
                                       alignment=TA_CENTER, fontSize=10, 
                                       textColor=colors.grey)))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

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

def generate_market_insights(top_crops, location="India"):
    """Generate market insights for top 3 crops using OpenAI API"""
    try:
        print(f"\n💰 GENERATING MARKET INSIGHTS")
        print(f"Top crops: {[crop[0] for crop in top_crops]}")
        print(f"Location: {location}")
        
        crop_names = [crop[0] for crop in top_crops]
        
        prompt = f"""Generate current market insights for these top 3 crops in {location}: {', '.join(crop_names)}

For each crop, provide:
1. Current market price (in ₹/quintal for Indian market)
2. Price trend (up/down/stable with percentage change)
3. Market demand (High/Medium/Low)
4. A brief market tip or insight

Format the response as JSON with this structure:
{{
  "crops": [
    {{
      "name": "Crop Name",
      "price": "₹X,XXX/quintal",
      "trend": "up/down/stable",
      "trend_percentage": "+/-X%",
      "demand": "High/Medium/Low",
      "market_tip": "Brief insight about market conditions"
    }}
  ],
  "general_tip": "Overall market advice for farmers"
}}

Make the data realistic for current Indian agricultural market conditions."""

        # Using OpenAI ChatCompletion API with new client format
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert agricultural market analyst with deep knowledge of Indian crop markets, pricing trends, and farming economics."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extract and parse the response
        content = response.choices[0].message.content
        print(f"OpenAI Response: {content}")
        
        # Parse JSON response
        market_data = json.loads(content)
        
        print(f"✅ Market insights generated successfully!")
        return {"success": True, "data": market_data}
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        return {"success": False, "error": "Failed to parse market data"}
    except Exception as e:
        print(f"❌ Error generating market insights: {str(e)}")
        return {"success": False, "error": f"Market API error: {str(e)}"}

def get_fallback_market_data(top_crops):
    """Fallback market data if OpenAI API fails"""
    fallback_data = {
        "Rice": {"price": "₹1,850", "trend": "stable", "trend_percentage": "±0%", "demand": "Medium"},
        "Wheat": {"price": "₹2,200", "trend": "up", "trend_percentage": "+5%", "demand": "High"},
        "Cotton": {"price": "₹5,500", "trend": "up", "trend_percentage": "+3%", "demand": "High"},
        "Sugarcane": {"price": "₹350", "trend": "down", "trend_percentage": "-2%", "demand": "Low"},
        "Maize": {"price": "₹1,950", "trend": "stable", "trend_percentage": "±0%", "demand": "Medium"},
        "Pulses": {"price": "₹3,800", "trend": "up", "trend_percentage": "+7%", "demand": "High"},
        "Mustard": {"price": "₹4,200", "trend": "up", "trend_percentage": "+4%", "demand": "Medium"},
        "Barley": {"price": "₹1,600", "trend": "stable", "trend_percentage": "±0%", "demand": "Low"}
    }
    
    crops_data = []
    for crop_name, _ in top_crops:
        if crop_name in fallback_data:
            data = fallback_data[crop_name]
            crops_data.append({
                "name": crop_name,
                "price": data["price"] + "/quintal",
                "trend": data["trend"],
                "trend_percentage": data["trend_percentage"],
                "demand": data["demand"],
                "market_tip": f"Consider {crop_name.lower()} cultivation based on current market conditions"
            })
    
    return {
        "success": True,
        "data": {
            "crops": crops_data,
            "general_tip": "Market conditions are favorable for diversified crop production. Monitor price trends regularly."
        }
    }

def generate_farming_alerts(journal_entries):
    """Generate AI-powered alerts and reminders based on farming journal entries using OpenAI"""
    alerts = []
    today = date.today()
    
    print(f"\n🚨 GENERATING AI-POWERED FARMING ALERTS")
    print(f"Processing {len(journal_entries)} journal entries with OpenAI")
    
    try:
        # Prepare journal data for OpenAI analysis
        journal_summary = []
        activity_counts = {}
        
        for entry in journal_entries:
            try:
                entry_date = datetime.strptime(entry.date, '%Y-%m-%d').date()
                days_ago = (today - entry_date).days
                
                # Include recent entries (last 60 days) for analysis
                if days_ago <= 60:
                    journal_summary.append({
                        'date': entry.date,
                        'activity': entry.activity,
                        'details': entry.activity_details,
                        'days_ago': days_ago
                    })
                    
                    # Count activities
                    activity_counts[entry.activity] = activity_counts.get(entry.activity, 0) + 1
                    
            except ValueError:
                continue
        
        # Create prompt for OpenAI
        current_month = today.strftime('%B')
        current_date = today.strftime('%Y-%m-%d')
        
        prompt = f"""You are an expert agricultural advisor analyzing a farmer's activity journal for {current_date} (current date: {current_month}). 

Recent farming activities (last 60 days):
{json.dumps(journal_summary, indent=2)}

Activity summary:
{json.dumps(activity_counts, indent=2)}

Based on this farming journal, generate 4-6 personalized alerts and reminders. Consider:
- Timing of last activities (watering, fertilizing, pest control, etc.)
- Seasonal farming patterns for {current_month}
- Crop growth cycles and harvest timing
- Preventive measures and best practices
- Specific recommendations based on their farming patterns

For each alert, provide:
1. Type: "warning", "info", "success", or "error"
2. Icon: appropriate farming emoji
3. Title: short descriptive title
4. Message: detailed, actionable message
5. Priority: "high", "medium", or "low"

Return ONLY a valid JSON array of alerts, no other text:
[
  {{
    "type": "warning",
    "icon": "�",
    "title": "Alert Title",
    "message": "Detailed message with specific recommendations",
    "priority": "high"
  }}
]"""

        print("Sending journal data to OpenAI for intelligent analysis...")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert agricultural advisor specializing in personalized farming recommendations. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        # Parse OpenAI response
        ai_response = response.choices[0].message.content.strip()
        print(f"OpenAI response received: {len(ai_response)} characters")
        
        # Clean and parse JSON response
        if ai_response.startswith('```json'):
            ai_response = ai_response.replace('```json', '').replace('```', '').strip()
        
        try:
            ai_alerts = json.loads(ai_response)
            
            if isinstance(ai_alerts, list):
                alerts.extend(ai_alerts)
                print(f"✅ Successfully generated {len(ai_alerts)} AI-powered alerts")
            else:
                print("⚠️ AI response was not a list, using fallback alerts")
                alerts = get_fallback_farming_alerts(journal_entries)
                
        except json.JSONDecodeError as je:
            print(f"⚠️ JSON decode error: {je}")
            print(f"Raw AI response: {ai_response[:200]}...")
            alerts = get_fallback_farming_alerts(journal_entries)
            
    except Exception as e:
        print(f"⚠️ OpenAI API error: {e}")
        alerts = get_fallback_farming_alerts(journal_entries)
    
    # Add a few basic alerts if AI didn't generate enough
    if len(alerts) < 3:
        basic_alerts = get_enhanced_basic_farming_alerts(journal_entries, activity_counts)
        alerts.extend(basic_alerts)
    
    # Sort alerts by priority
    priority_order = {"high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
    
    print(f"🎯 Final result: {len(alerts)} personalized farming alerts generated")
    return alerts[:8]  # Limit to 8 alerts

def get_fallback_farming_alerts(journal_entries):
    """Fallback alerts when OpenAI is unavailable"""
    alerts = []
    today = date.today()
    
    # Basic analysis for fallback
    activity_dates = {}
    for entry in journal_entries:
        try:
            entry_date = datetime.strptime(entry.date, '%Y-%m-%d').date()
            activity = entry.activity.lower()
            
            if activity not in activity_dates:
                activity_dates[activity] = []
            activity_dates[activity].append(entry_date)
        except ValueError:
            continue
    
    # Generate basic alerts
    if 'watering' in activity_dates:
        last_watering = max(activity_dates['watering'])
        days_since = (today - last_watering).days
        if days_since >= 3:
            alerts.append({
                "type": "warning",
                "icon": "💧",
                "title": "Watering Schedule",
                "message": f"Last watering was {days_since} days ago. Check soil moisture and water if needed.",
                "priority": "high" if days_since >= 5 else "medium"
            })
    
    if 'fertilizing' in activity_dates:
        last_fertilizing = max(activity_dates['fertilizing'])
        days_since = (today - last_fertilizing).days
        if days_since >= 21:
            alerts.append({
                "type": "info",
                "icon": "🧪",
                "title": "Fertilizer Application",
                "message": f"Consider next fertilizer application. Last applied {days_since} days ago.",
                "priority": "medium"
            })
    
    return alerts

def get_enhanced_basic_farming_alerts(journal_entries, activity_counts):
    """Enhanced basic alerts to supplement AI-generated ones"""
    alerts = []
    current_month = date.today().month
    current_date = date.today()
    
    # Enhanced seasonal alerts based on current month
    seasonal_alerts = {
        9: [  # September
            {
                "type": "warning",
                "icon": "�",
                "title": "Rabi Season Preparation",
                "message": "September is ideal for preparing fields for Rabi crops like wheat, barley, and mustard. Start soil preparation and seed selection.",
                "priority": "high"
            },
            {
                "type": "info",
                "icon": "🌧️",
                "title": "Monsoon End Planning",
                "message": "As monsoon season ends, plan drainage systems and assess crop damage. Prepare for post-monsoon activities.",
                "priority": "medium"
            }
        ],
        10: [  # October
            {
                "type": "success",
                "icon": "🌱",
                "title": "Optimal Sowing Time",
                "message": "October is the best time for sowing Rabi crops. Ensure proper seed treatment and optimal spacing.",
                "priority": "high"
            }
        ],
        11: [  # November
            {
                "type": "info",
                "icon": "💧",
                "title": "Irrigation Management",
                "message": "Monitor soil moisture levels for newly sown Rabi crops. Provide adequate but not excessive irrigation.",
                "priority": "medium"
            }
        ]
    }
    
    # Add seasonal alerts
    if current_month in seasonal_alerts:
        alerts.extend(seasonal_alerts[current_month])
    
    # Activity-based intelligent alerts
    if activity_counts:
        total_activities = sum(activity_counts.values())
        
        if 'watering' in activity_counts:
            watering_freq = activity_counts['watering']
            if watering_freq < total_activities * 0.3:  # Less than 30% watering
                alerts.append({
                    "type": "warning",
                    "icon": "💧",
                    "title": "Irrigation Frequency Check",
                    "message": f"Your watering frequency ({watering_freq} times) seems low. Consider increasing irrigation based on crop needs and soil moisture.",
                    "priority": "medium"
                })
        
        if 'fertilizing' in activity_counts:
            fert_freq = activity_counts['fertilizing']
            if fert_freq == 0:
                alerts.append({
                    "type": "error",
                    "icon": "🌱",
                    "title": "Fertilization Missing",
                    "message": "No fertilization activities recorded. Proper nutrition is essential for healthy crop growth.",
                    "priority": "high"
                })
        
        if 'pest-control' not in activity_counts:
            alerts.append({
                "type": "warning",
                "icon": "🔍",
                "title": "Pest Monitoring Needed",
                "message": "No pest control activities recorded. Regular monitoring and preventive measures are crucial for crop protection.",
                "priority": "medium"
            })
    
    # Always include general farming tips
    general_alerts = [
        {
            "type": "info",
            "icon": "�️",
            "title": "Weather Monitoring",
            "message": "Check weather forecasts daily for planning irrigation and field activities. Stay updated on seasonal patterns.",
            "priority": "low"
        },
        {
            "type": "success",
            "icon": "📊",
            "title": "Record Keeping",
            "message": "Continue maintaining detailed farming records. This data helps in making informed decisions and tracking progress.",
            "priority": "low"
        }
    ]
    
    alerts.extend(general_alerts)
    return alerts[:4]  # Limit enhanced basic alerts

def generate_gemini_enhanced_calendar_activities(top_crops, current_month):
    """Use Google Gemini to generate intelligent calendar activities based on top crops"""
    try:
        crops_str = ", ".join(top_crops)
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        current_month_name = month_names[current_month - 1]
        
        calendar_prompt = f"""You are an expert agricultural calendar advisor for Indian farming conditions.

TASK: Generate specific farming activities for {current_month_name} (month {current_month}) for these top recommended crops: {crops_str}

REQUIREMENTS:
- Focus on activities specific to {current_month_name} in India
- Consider seasonal patterns (Kharif, Rabi, Zaid seasons)
- Include timing-specific activities (planting, harvesting, maintenance)
- Make activities actionable and date-specific

OUTPUT FORMAT: Return ONLY a valid JSON object with this structure:
{{
  "month": {current_month},
  "month_name": "{current_month_name}",
  "activities": [
    {{
      "crop": "Rice",
      "activity": "Land preparation",
      "dates": [5, 10, 15],
      "priority": "high",
      "description": "Prepare fields for transplanting by plowing and leveling"
    }}
  ]
}}

Generate 8-12 activities covering all 3 crops with specific dates and priorities."""

        print(f"🗓️ Generating calendar activities for {current_month_name} using Gemini...")
        
        response = gemini_model.generate_content(calendar_prompt)
        calendar_text = response.text.strip()
        
        # Clean response
        if calendar_text.startswith('```json'):
            calendar_text = calendar_text[7:-3].strip()
        elif calendar_text.startswith('```'):
            calendar_text = calendar_text[3:-3].strip()
        
        calendar_data = json.loads(calendar_text)
        print(f"✅ Generated {len(calendar_data.get('activities', []))} calendar activities")
        return calendar_data
        
    except Exception as e:
        print(f"⚠️ Gemini calendar generation error: {e}")
        return None

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
        
        print(f"\n🔐 LOGIN ATTEMPT DEBUG:")
        print(f"   Username received: '{username}'")
        print(f"   Password received: '{password}'")
        print(f"   Form data: {dict(request.form)}")
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ User '{username}' not found in database")
            flash("Invalid username or password", "danger")
            return render_template("login.html")
        
        print(f"✅ User found: {user.username}")
        print(f"   Stored password hash: {user.password}")
        
        # Verify password
        try:
            password_valid = verify_password(password, user.password)
            print(f"   Password verification result: {password_valid}")
            
            if password_valid:
                # Check if user needs password migration to new secure format
                needs_migration = False
                if ':' not in user.password or user.password.count(':') < 2:
                    # User has old format password, migrate to new secure format
                    needs_migration = True
                    print(f"🔄 Migrating password for user '{username}' to advanced security")
                    
                    # Hash password with new advanced method
                    new_hash = hash_password(password)
                    user.password = new_hash
                    
                    # Save to database
                    from app import db
                    db.session.commit()
                    print(f"✅ Password migration completed for user '{username}'")
                
                session["user_id"] = user.id
                flash("Login successful!", "success")
                print(f"✅ User '{username}' logged in successfully{' (password migrated)' if needs_migration else ''}")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password", "danger")
                print(f"❌ Failed login attempt for username: '{username}' - Invalid password")
                return render_template("login.html")
                
        except Exception as e:
            print(f"❌ Exception during password verification: {e}")
            import traceback
            traceback.print_exc()
            flash("Login error occurred", "danger")
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
    
    # Validation checks
    if not username or not password or not confirm:
        flash("Please fill all fields", "danger")
        return render_template("login.html")
    
    if password != confirm:
        flash("Passwords do not match", "danger")
        return render_template("login.html")
    
    # Password strength validation
    if len(password) < 6:
        flash("Password must be at least 6 characters long", "danger")
        return render_template("login.html")
    
    # Check if username already exists
    existing = User.query.filter_by(username=username).first()
    if existing:
        flash("Username already exists", "danger")
        return render_template("login.html")
    
    # Hash the password before storing
    hashed_password = hash_password(password)
    
    # Create new user with hashed password
    user = User(username=username, password=hashed_password)
    from app import db
    db.session.add(user)
    db.session.commit()
    
    print(f"✅ New user '{username}' registered with hashed password")
    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("login"))

# API route to change password for logged-in user
@app.route("/api/change_password", methods=["POST"])
def api_change_password():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")
    
    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "error": "All password fields are required"}), 400
    
    # Verify current password
    if not verify_password(current_password, user.password):
        return jsonify({"success": False, "error": "Current password is incorrect"}), 400
    
    # Check if new passwords match
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "New passwords do not match"}), 400
    
    # Validate new password strength (optional - you can enable this for stronger security)
    # is_valid, message = is_strong_password(new_password)
    # if not is_valid:
    #     return jsonify({"success": False, "error": message}), 400
    
    # Basic validation
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters long"}), 400
    
    # Hash and update password
    from app import db
    user.password = hash_password(new_password)
    db.session.commit()
    
    print(f"✅ Password changed successfully for user '{user.username}'")
    return jsonify({"success": True, "message": "Password changed successfully"})

# Logout route
@app.route("/logout")
def logout():
    if "user_id" in session:
        user_id = session["user_id"]
        session.clear()
        print(f"✅ User (ID: {user_id}) logged out successfully")
        flash("You have been logged out successfully.", "info")
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

# API route to download seasonal report as PDF
@app.route("/api/seasonal_report_pdf", methods=["GET"])
def api_seasonal_report_pdf():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    try:
        # Get all user data (same as seasonal_report)
        tasks = Task.query.filter_by(user_id=user.id).all()
        inventory = Inventory.query.filter_by(user_id=user.id).all()
        expenses = Expense.query.filter_by(user_id=user.id).all()
        journal_entries = Journal.query.filter_by(user_id=user.id).order_by(Journal.date.desc()).all()
        
        # Process data (same logic as seasonal_report)
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
            
            task_date = datetime.strptime(task.date, '%Y-%m-%d').date()
            if task_date <= date.today():
                tasks_by_status["completed"] += 1
            else:
                tasks_by_status["pending"] += 1
        
        inventory_data = []
        total_inventory_items = 0
        for inv in inventory:
            inventory_data.append({
                "id": inv.id,
                "item": inv.item,
                "quantity": inv.quantity
            })
            total_inventory_items += inv.quantity
        
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
            
            if entry.activity in activities_count:
                activities_count[entry.activity] += 1
            else:
                activities_count[entry.activity] = 1
        
        # Create report data
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
        
        # Generate PDF
        pdf_buffer = generate_seasonal_report_pdf(report_data)
        
        # Create filename with current date
        filename = f"farm_report_{user.username}_{date.today().strftime('%Y-%m-%d')}.pdf"
        
        print(f"✅ PDF report generated successfully for user '{user.username}'")
        
        # Return PDF as download
        from flask import send_file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error generating PDF report: {str(e)}")
        return jsonify({"success": False, "error": f"Failed to generate PDF: {str(e)}"}), 500

# API route to download crop recommendations as PDF
@app.route("/api/crop_recommendations_pdf", methods=["GET"])
def api_crop_recommendations_pdf():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    try:
        # Get location parameters
        lat = request.args.get('lat', '16.5449')
        lon = request.args.get('lon', '81.5212')
        location_name = request.args.get('location', 'India')
        
        # Get weather data and crop recommendations (same logic as crop_recommendations)
        API_KEY = "a1b2394289828346d954d42d376a1033"
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
        
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            weather_data = r.json()
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            rainfall = weather_data.get('rain', {}).get('1h', 0) * 24 * 30
            
            if rainfall == 0:
                current_month = datetime.now().month
                seasonal_rainfall = {9: 150, 10: 50, 11: 30, 12: 20, 1: 25, 2: 30}
                rainfall = seasonal_rainfall.get(current_month, 100)
            
            predictions = predict_crops_mock(temperature, humidity, rainfall)
            
            recommendations_data = {
                "recommendations": predictions,
                "weather_data": {
                    "temperature": temperature,
                    "humidity": humidity,
                    "rainfall": rainfall,
                    "location": weather_data.get('name', location_name)
                }
            }
            
            # Try to get market insights
            market_data = None
            try:
                market_result = generate_market_insights(predictions, location_name)
                if market_result["success"]:
                    market_data = market_result["data"]
                else:
                    market_data = get_fallback_market_data(predictions)["data"]
            except:
                market_data = get_fallback_market_data(predictions)["data"]
            
            # Generate PDF
            pdf_buffer = generate_crop_recommendations_pdf(recommendations_data, market_data)
            
            # Create filename
            filename = f"crop_recommendations_{location_name}_{date.today().strftime('%Y-%m-%d')}.pdf"
            
            print(f"✅ Crop recommendations PDF generated successfully for location: {location_name}")
            
            # Return PDF as download
            from flask import send_file
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        else:
            return jsonify({"success": False, "error": "Weather data unavailable"}), 500
            
    except Exception as e:
        print(f"❌ Error generating crop recommendations PDF: {str(e)}")
        return jsonify({"success": False, "error": f"Failed to generate PDF: {str(e)}"}), 500

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

# API route to get market insights for top crops
@app.route("/api/market_insights", methods=["GET"])
def api_market_insights():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    # Get location parameters
    lat = request.args.get('lat', '16.5449')
    lon = request.args.get('lon', '81.5212')
    location_name = request.args.get('location', 'India')
    
    print(f"\n📊 FETCHING MARKET INSIGHTS")
    print(f"Location: {location_name} (Lat {lat}, Lon {lon})")
    
    try:
        # First get the crop recommendations
        API_KEY = "a1b2394289828346d954d42d376a1033"
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
        
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            weather_data = r.json()
            
            # Extract weather parameters
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            
            # Calculate rainfall
            rainfall = weather_data.get('rain', {}).get('1h', 0) * 24 * 30
            if rainfall == 0:
                current_month = datetime.now().month
                if current_month in [6, 7, 8, 9]:
                    rainfall = 200
                elif current_month in [10, 11, 12, 1, 2]:
                    rainfall = 50
                else:
                    rainfall = 30
            
            # Get crop predictions
            top_crops = predict_crops_mock(temperature, humidity, rainfall)
            
            # Generate market insights using OpenAI
            market_result = generate_market_insights(top_crops, location_name)
            
            if not market_result["success"]:
                # Use fallback data if OpenAI fails
                print("Using fallback market data...")
                market_result = get_fallback_market_data(top_crops)
            
            print(f"✅ Market insights generated successfully!")
            
            return jsonify({
                "success": True,
                "market_data": market_result["data"],
                "top_crops": top_crops,
                "location": location_name
            })
        else:
            print(f"❌ Weather API Error: {r.status_code}")
            return jsonify({"success": False, "error": f"Weather API Error: {r.status_code}"}), 500
            
    except Exception as e:
        print(f"❌ Error getting market insights: {str(e)}")
        # Return fallback data in case of any error
        fallback_crops = [("Wheat", 0.91), ("Rice", 0.85), ("Cotton", 0.78)]
        fallback_market = get_fallback_market_data(fallback_crops)
        
        return jsonify({
            "success": True,
            "market_data": fallback_market["data"],
            "top_crops": fallback_crops,
            "location": location_name,
            "note": "Using fallback data due to API limitations"
        })

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

# API route to get dynamic alerts and reminders based on journal entries
@app.route("/api/farming_alerts", methods=["GET"])
def api_farming_alerts():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    print(f"\n🚨 FETCHING FARMING ALERTS")
    print(f"User: {user.username}")
    
    try:
        # Get all journal entries for the user
        journal_entries = Journal.query.filter_by(user_id=user.id).order_by(Journal.date.desc()).all()
        
        # Generate alerts based on journal analysis
        alerts = generate_farming_alerts(journal_entries)
        
        print(f"✅ Generated {len(alerts)} alerts successfully!")
        
        return jsonify({
            "success": True,
            "alerts": alerts,
            "total_entries_analyzed": len(journal_entries),
            "ai_powered": True,
            "sources": ["Google Gemini", "OpenAI", "Smart Logic"],
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"❌ Error generating farming alerts: {str(e)}")
        
        # Return fallback alerts in case of error
        fallback_alerts = [
            {
                "type": "info",
                "icon": "📅",
                "title": "Farm Management",
                "message": "Keep track of your farming activities in the journal for personalized recommendations.",
                "priority": "low"
            },
            {
                "type": "warning",
                "icon": "🌧️",
                "title": "Weather Monitoring",
                "message": "Check weather forecasts regularly to plan your farming activities.",
                "priority": "medium"
            }
        ]
        
        return jsonify({
            "success": True,
            "alerts": fallback_alerts,
            "total_entries_analyzed": 0,
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "note": "Using fallback alerts due to system limitations"
        })

# Route to display crop planning page
@app.route("/crop_planning")
def crop_planning_page():
    if "user_id" not in session:
        flash("You must be logged in to view the crop planning guide.", "danger")
        return redirect(url_for("login"))
    
    return render_template("crop_planning.html")

# API route to get intelligent calendar activities based on top crops
@app.route("/api/smart_calendar", methods=["GET"])
def api_smart_calendar():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "User not logged in"})
    
    # Get parameters
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    top_crops = request.args.getlist('crops')  # List of top crop names
    
    if not top_crops:
        top_crops = ['Rice', 'Wheat', 'Cotton']  # Default crops
    
    print(f"\n📅 GENERATING SMART CALENDAR")
    print(f"Month: {month}, Year: {year}")
    print(f"Top Crops: {top_crops}")
    
    try:
        # Generate calendar activities using Gemini
        calendar_data = generate_gemini_enhanced_calendar_activities(top_crops, month)
        
        if calendar_data:
            return jsonify({
                "success": True,
                "calendar_data": calendar_data,
                "ai_generated": True,
                "month": month,
                "year": year,
                "crops_analyzed": top_crops
            })
        else:
            # Fallback to basic calendar data
            fallback_data = get_fallback_calendar_data(top_crops, month)
            return jsonify({
                "success": True,
                "calendar_data": fallback_data,
                "ai_generated": False,
                "month": month,
                "year": year,
                "crops_analyzed": top_crops
            })
            
    except Exception as e:
        print(f"❌ Calendar generation error: {e}")
        return jsonify({
            "success": False,
            "error": f"Calendar generation failed: {str(e)}"
        })

def get_fallback_calendar_data(top_crops, month):
    """Fallback calendar data when AI generation fails"""
    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    # Basic crop schedule patterns
    basic_activities = {
        'Rice': {
            5: [{"activity": "Land preparation", "dates": [5, 10], "priority": "high"}],
            6: [{"activity": "Transplanting", "dates": [1, 15], "priority": "high"}],
            9: [{"activity": "Harvesting prep", "dates": [20, 25], "priority": "medium"}],
            10: [{"activity": "Harvesting", "dates": [5, 15], "priority": "high"}]
        },
        'Wheat': {
            10: [{"activity": "Field preparation", "dates": [1, 10], "priority": "high"}],
            11: [{"activity": "Sowing", "dates": [1, 15], "priority": "high"}],
            3: [{"activity": "Harvesting", "dates": [15, 30], "priority": "high"}]
        },
        'Cotton': {
            4: [{"activity": "Field preparation", "dates": [1, 15], "priority": "high"}],
            5: [{"activity": "Sowing", "dates": [1, 20], "priority": "high"}],
            9: [{"activity": "First picking", "dates": [10, 25], "priority": "medium"}]
        }
    }
    
    activities = []
    for crop in top_crops:
        if crop in basic_activities and month in basic_activities[crop]:
            for activity_data in basic_activities[crop][month]:
                activities.append({
                    "crop": crop,
                    "activity": activity_data["activity"],
                    "dates": activity_data["dates"],
                    "priority": activity_data["priority"],
                    "description": f"Basic {activity_data['activity'].lower()} activities for {crop}"
                })
    
    return {
        "month": month,
        "month_name": month_names[month - 1],
        "activities": activities
    }



