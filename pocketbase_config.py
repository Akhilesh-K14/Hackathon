# PocketBase Configuration
# This file will store PocketBase server configuration

# PocketBase Server URL
POCKETBASE_URL = "http://127.0.0.1:8090"

# Collections we'll need:
# 1. users - for authentication (built-in)
# 2. tasks - for farm tasks
# 3. inventory - for inventory management  
# 4. expenses - for expense tracking
# 5. journal - for farming journal entries

# PocketBase will handle user authentication and password encryption automatically
# We'll migrate from SQLite to PocketBase for better security and built-in auth
