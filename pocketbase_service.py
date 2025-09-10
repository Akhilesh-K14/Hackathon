"""
PocketBase Service for Farm Management System
Handles authentication and data management with encrypted passwords
"""

from pocketbase import PocketBase
import json
from datetime import datetime

class FarmPocketBaseService:
    def __init__(self, url="http://127.0.0.1:8091"):
        """Initialize PocketBase client"""
        self.pb = PocketBase("http://127.0.0.1:8090")
        self.url = url
        print(f"🔗 PocketBase client initialized: {url}")
    
    def test_connection(self):
        """Test connection to PocketBase server"""
        try:
            # Try to get collections - simpler than health check
            collections = self.pb.collections.get_list()
            print(f"✅ PocketBase server is accessible")
            return True
        except Exception as e:
            print(f"❌ PocketBase connection failed: {e}")
            return False
    
    def authenticate_user(self, username, password):
        """
        Authenticate user with PocketBase
        PocketBase handles password encryption automatically
        """
        try:
            # PocketBase auth with email/username and password
            auth_data = self.pb.collection("users").auth_with_password(username, password)
            
            user_data = {
                'id': auth_data.record.id,
                'username': auth_data.record.username,
                'email': auth_data.record.email,
                'token': auth_data.token
            }
            
            print(f"✅ User '{username}' authenticated successfully")
            return {'success': True, 'user': user_data}
            
        except Exception as e:
            print(f"❌ Authentication failed for '{username}': {e}")
            return {'success': False, 'error': str(e)}
    
    def register_user(self, username, email, password):
        """
        Register new user with PocketBase
        PocketBase automatically encrypts the password
        """
        try:
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "passwordConfirm": password
            }
            
            # Create new user - PocketBase handles password encryption
            new_user = self.pb.collection("users").create(user_data)
            
            print(f"✅ User '{username}' registered successfully with encrypted password")
            return {'success': True, 'user_id': new_user.id}
            
        except Exception as e:
            print(f"❌ Registration failed for '{username}': {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_tasks(self, user_id):
        """Get all tasks for a user"""
        try:
            tasks = self.pb.collection("tasks").get_list(
                query_params={
                    "filter": f"user_id='{user_id}'",
                    "sort": "-created"
                }
            )
            return {'success': True, 'tasks': tasks.items}
        except Exception as e:
            print(f"❌ Failed to get tasks: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_task(self, user_id, title, date, notes=""):
        """Create a new task"""
        try:
            task_data = {
                "user_id": user_id,
                "title": title,
                "date": date,
                "notes": notes,
                "completed": False
            }
            
            task = self.pb.collection("tasks").create(task_data)
            return {'success': True, 'task': task}
        except Exception as e:
            print(f"❌ Failed to create task: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_inventory(self, user_id):
        """Get all inventory items for a user"""
        try:
            inventory = self.pb.collection("inventory").get_list(
                query_params={
                    "filter": f"user_id='{user_id}'",
                    "sort": "item"
                }
            )
            return {'success': True, 'inventory': inventory.items}
        except Exception as e:
            print(f"❌ Failed to get inventory: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_inventory_item(self, user_id, item, quantity):
        """Add or update inventory item"""
        try:
            # Check if item already exists
            existing = self.pb.collection("inventory").get_list(
                query_params={
                    "filter": f"user_id='{user_id}' && item='{item}'"
                }
            )
            
            if existing.items:
                # Update existing item
                existing_item = existing.items[0]
                updated_data = {
                    "quantity": existing_item.quantity + quantity
                }
                updated_item = self.pb.collection("inventory").update(existing_item.id, updated_data)
                return {'success': True, 'inventory': updated_item, 'action': 'updated'}
            else:
                # Create new item
                inventory_data = {
                    "user_id": user_id,
                    "item": item,
                    "quantity": quantity
                }
                new_item = self.pb.collection("inventory").create(inventory_data)
                return {'success': True, 'inventory': new_item, 'action': 'created'}
                
        except Exception as e:
            print(f"❌ Failed to add inventory item: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_expenses(self, user_id):
        """Get all expenses for a user"""
        try:
            expenses = self.pb.collection("expenses").get_list(
                query_params={
                    "filter": f"user_id='{user_id}'",
                    "sort": "-created"
                }
            )
            return {'success': True, 'expenses': expenses.items}
        except Exception as e:
            print(f"❌ Failed to get expenses: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_expense(self, user_id, item, amount, season):
        """Add a new expense"""
        try:
            expense_data = {
                "user_id": user_id,
                "item": item,
                "amount": amount,
                "season": season
            }
            
            expense = self.pb.collection("expenses").create(expense_data)
            return {'success': True, 'expense': expense}
        except Exception as e:
            print(f"❌ Failed to add expense: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_journal(self, user_id):
        """Get all journal entries for a user"""
        try:
            journal = self.pb.collection("journal").get_list(
                query_params={
                    "filter": f"user_id='{user_id}'",
                    "sort": "-date"
                }
            )
            return {'success': True, 'journal': journal.items}
        except Exception as e:
            print(f"❌ Failed to get journal: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_journal_entry(self, user_id, activity, activity_details, date):
        """Add a new journal entry"""
        try:
            journal_data = {
                "user_id": user_id,
                "activity": activity,
                "activity_details": activity_details,
                "date": date
            }
            
            entry = self.pb.collection("journal").create(journal_data)
            return {'success': True, 'journal': entry}
        except Exception as e:
            print(f"❌ Failed to add journal entry: {e}")
            return {'success': False, 'error': str(e)}

# Global PocketBase service instance
pb_service = FarmPocketBaseService()

print(f"🛡️ POCKETBASE SERVICE INITIALIZED")
print(f"Automatic Password Encryption: ✅ Enabled")
print(f"Secure Authentication: ✅ Built-in")
print(f"Developer-Safe: ✅ Passwords encrypted by PocketBase")
print(f"========================================\n")
