# Setup Fresh Repository - Step by Step Guide

## Steps to Create a Clean Repository

### 1. Remove Git History
```bash
# Navigate to your project
cd /d/Hackathon_Project/Hackathon

# Remove the old git repository
rm -rf .git
```

### 2. Clean Up Sensitive Files
```bash
# Delete all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Delete .pyc files
find . -type f -name "*.pyc" -delete

# Delete database files (you'll recreate them)
rm -f instance/app.db app/login.db
```

### 3. Initialize Fresh Git Repository
```bash
# Initialize new git repository
git init

# Add all files (respecting .gitignore)
git add .

# Create first commit
git commit -m "Initial commit: Farm Management System"
```

### 4. Create New GitHub Repository
1. Go to https://github.com/new
2. Create a new repository (e.g., "Farm-Management-System")
3. **DO NOT** initialize with README, .gitignore, or license
4. Copy the repository URL

### 5. Push to New Repository
```bash
# Add the new remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPO.git

# Push to new repository
git branch -M main
git push -u origin main
```

## Important: Before Pushing

Make sure your `.env` file is listed in `.gitignore` and contains:
- .env
- __pycache__/
- *.db
- instance/

## After Setup

1. **Rotate ALL API Keys** - Your old keys were exposed:
   - OpenAI API Key
   - Twilio credentials
   - Email passwords
   - Create new keys and update your `.env` file

2. **Share `.env.example`** - This template helps collaborators set up their environment

3. **Recreate Database**:
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

## Security Checklist
- [ ] Old repository deleted or archived
- [ ] All API keys rotated
- [ ] New `.env` file created with new keys
- [ ] `.gitignore` properly configured
- [ ] Database recreated
- [ ] Application tested with new setup
