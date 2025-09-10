"""
Initialize PocketBase with required collections for Farm Management System
"""

import time
import subprocess
import sys
from pocketbase_service import pb_service

def start_pocketbase_server():
    """Start PocketBase server in background"""
    print("🚀 Starting PocketBase server...")
    try:
        # Start PocketBase server
        process = subprocess.Popen(
            ["./pocketbase.exe", "serve", "--http=127.0.0.1:8090"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Test connection
        if pb_service.test_connection():
            print("✅ PocketBase server started successfully!")
            return process
        else:
            print("❌ Failed to connect to PocketBase server")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start PocketBase: {e}")
        return None

def setup_collections():
    """Setup required collections via PocketBase admin"""
    print("\n📋 COLLECTION SETUP INSTRUCTIONS:")
    print("=" * 50)
    print("1. Open http://127.0.0.1:8090/_/ in your browser")
    print("2. Create an admin account")
    print("3. Create these collections:")
    print("")
    print("🔸 Collection: 'tasks'")
    print("   Fields:")
    print("   - user_id (Relation to users)")
    print("   - title (Text)")
    print("   - date (Date)")
    print("   - notes (Text)")
    print("   - completed (Bool)")
    print("")
    print("🔸 Collection: 'inventory'")
    print("   Fields:")
    print("   - user_id (Relation to users)")
    print("   - item (Text)")
    print("   - quantity (Number)")
    print("")
    print("🔸 Collection: 'expenses'")
    print("   Fields:")
    print("   - user_id (Relation to users)")
    print("   - item (Text)")
    print("   - amount (Number)")
    print("   - season (Text)")
    print("")
    print("🔸 Collection: 'journal'")
    print("   Fields:")
    print("   - user_id (Relation to users)")
    print("   - activity (Text)")
    print("   - activity_details (Text)")
    print("   - date (Date)")
    print("")
    print("Note: 'users' collection is built-in with automatic password encryption!")

if __name__ == "__main__":
    print("🛡️ POCKETBASE SETUP FOR FARM MANAGEMENT SYSTEM")
    print("=" * 60)
    
    # Start PocketBase server
    server_process = start_pocketbase_server()
    
    if server_process:
        setup_collections()
        
        print("\n✅ PocketBase is ready!")
        print("🔒 Password encryption is handled automatically by PocketBase")
        print("🛡️ Even developers cannot see plain text passwords")
        print("\nPress Ctrl+C to stop the server when you're done setting up...")
        
        try:
            # Keep the server running
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping PocketBase server...")
            server_process.terminate()
            print("✅ Server stopped")
    else:
        print("❌ Could not start PocketBase server")
        sys.exit(1)
