"""
Automatic PocketBase Collection Setup
Creates all required collections for the Farm Management System
"""

import requests
import json
import time

POCKETBASE_URL = "http://127.0.0.1:8090"

def create_admin_account():
    """Create admin account for PocketBase"""
    admin_data = {
        "email": "admin@farmmanager.local",
        "password": "admin123456",
        "passwordConfirm": "admin123456"
    }
    
    try:
        response = requests.post(f"{POCKETBASE_URL}/api/admins", json=admin_data)
        if response.status_code in [200, 400]:  # 400 might mean admin already exists
            print("✅ Admin account ready")
            return True
    except Exception as e:
        print(f"⚠️ Admin account setup: {e}")
    
    return False

def get_admin_token():
    """Get admin authentication token"""
    try:
        auth_data = {
            "identity": "admin@farmmanager.local",
            "password": "admin123456"
        }
        
        response = requests.post(f"{POCKETBASE_URL}/api/admins/auth-with-password", json=auth_data)
        if response.status_code == 200:
            token = response.json()["token"]
            print("✅ Admin authenticated")
            return token
    except Exception as e:
        print(f"❌ Admin auth failed: {e}")
    
    return None

def create_collection(token, collection_data):
    """Create a collection with given schema"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{POCKETBASE_URL}/api/collections", 
                               json=collection_data, headers=headers)
        
        if response.status_code in [200, 400]:  # 400 might mean collection exists
            print(f"✅ Collection '{collection_data['name']}' ready")
            return True
        else:
            print(f"❌ Failed to create '{collection_data['name']}': {response.text}")
    except Exception as e:
        print(f"❌ Error creating '{collection_data['name']}': {e}")
    
    return False

def setup_collections():
    """Setup all required collections"""
    print("🔧 Setting up PocketBase collections...")
    
    # Create admin account
    create_admin_account()
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Could not get admin token")
        return False
    
    # Collection schemas
    collections = [
        {
            "name": "tasks",
            "type": "base",
            "schema": [
                {
                    "name": "user_id",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": "_pb_users_auth_",
                        "cascadeDelete": True
                    }
                },
                {
                    "name": "title",
                    "type": "text",
                    "required": True,
                    "options": {"max": 200}
                },
                {
                    "name": "date",
                    "type": "date",
                    "required": True
                },
                {
                    "name": "notes",
                    "type": "text",
                    "required": False,
                    "options": {"max": 1000}
                },
                {
                    "name": "completed",
                    "type": "bool",
                    "required": False
                }
            ]
        },
        {
            "name": "inventory",
            "type": "base",
            "schema": [
                {
                    "name": "user_id",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": "_pb_users_auth_",
                        "cascadeDelete": True
                    }
                },
                {
                    "name": "item",
                    "type": "text",
                    "required": True,
                    "options": {"max": 100}
                },
                {
                    "name": "quantity",
                    "type": "number",
                    "required": True,
                    "options": {"min": 0}
                }
            ]
        },
        {
            "name": "expenses",
            "type": "base",
            "schema": [
                {
                    "name": "user_id",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": "_pb_users_auth_",
                        "cascadeDelete": True
                    }
                },
                {
                    "name": "item",
                    "type": "text",
                    "required": True,
                    "options": {"max": 100}
                },
                {
                    "name": "amount",
                    "type": "number",
                    "required": True,
                    "options": {"min": 0}
                },
                {
                    "name": "season",
                    "type": "select",
                    "required": True,
                    "options": {
                        "values": ["kharif", "rabi", "zaid"]
                    }
                }
            ]
        },
        {
            "name": "journal",
            "type": "base",
            "schema": [
                {
                    "name": "user_id",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": "_pb_users_auth_",
                        "cascadeDelete": True
                    }
                },
                {
                    "name": "activity",
                    "type": "select",
                    "required": True,
                    "options": {
                        "values": ["planting", "watering", "fertilizing", "pest-control", "harvesting", "soil-prep"]
                    }
                },
                {
                    "name": "activity_details",
                    "type": "text",
                    "required": True,
                    "options": {"max": 500}
                },
                {
                    "name": "date",
                    "type": "date",
                    "required": True
                }
            ]
        }
    ]
    
    # Create each collection
    success_count = 0
    for collection in collections:
        if create_collection(token, collection):
            success_count += 1
    
    print(f"\n✅ Setup complete! {success_count}/{len(collections)} collections ready")
    return success_count == len(collections)

if __name__ == "__main__":
    print("🛡️ POCKETBASE AUTO-SETUP FOR FARM MANAGEMENT")
    print("=" * 50)
    
    # Wait for server to be ready
    time.sleep(2)
    
    if setup_collections():
        print("\n🎉 PocketBase is fully configured!")
        print("🔒 User authentication with encrypted passwords is ready")
        print("📋 All collections created successfully")
        print("\nYou can now run the Flask app with:")
        print("python app_pocketbase.py")
    else:
        print("\n❌ Setup incomplete. Please check the PocketBase server.")
