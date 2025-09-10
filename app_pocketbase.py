"""
Farm Management System with PocketBase Authentication
Secure, encrypted password handling
"""

from flask import Flask
import os

# Create Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session secret

# Configure Flask settings
app.config['SECRET_KEY'] = os.urandom(24)

print(f"🌾 FARM MANAGEMENT SYSTEM - POCKETBASE EDITION")
print(f"🔐 Authentication: PocketBase (Automatic Encryption)")
print(f"🛡️ Password Security: Developer-Safe")
print(f"=" * 50)

# Import routes after app creation
from routes_pocketbase import *

if __name__ == "__main__":
    app.run(debug=True, port=5000)
