# ElitePrep - CSS & PPSC AI Portal | Complete Setup Guide

Welcome! This guide will help you set up and run the **ElitePrep Portal** on a new device. Follow the steps carefully and you'll have the application running locally.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Environment Configuration](#environment-configuration)
5. [Running the Application](#running-the-application)
6. [Accessing the Portal](#accessing-the-portal)
7. [Project Structure](#project-structure)
8. [Troubleshooting](#troubleshooting)
9. [Additional Services](#additional-services)

---

## 📦 Prerequisites

Before starting, ensure you have the following installed on your device:

### Required Software

- **Python 3.8 or higher** — [Download here](https://www.python.org/downloads/)
- **Git** (optional, for cloning the repo) — [Download here](https://git-scm.com/)
- **Text Editor/IDE** — VS Code recommended

### Verify Installation

Open your terminal/command prompt and run:

```bash
python --version          # Should show Python 3.8+
pip --version             # Should show pip version
```

**If not installed, download Python from the official website and run the installer.**

> **⚠️ Important (Windows users):** During Python installation, check the option **"Add Python to PATH"**

---

## 💻 System Requirements

- **OS:** Windows 10+, macOS, or Linux
- **RAM:** Minimum 4GB (8GB recommended)
- **Storage:** At least 5GB free space
- **Internet:** Required for initial setup and API calls

---

## 🚀 Installation Steps

### Step 1: Clone or Download the Project

**Option A: Using Git (Recommended)**
```bash
git clone <repository-url>
cd "css - Copy - Copy"
```

**Option B: Manual Download**
- Download the project as ZIP
- Extract it to your desired location
- Open terminal in the extracted folder

### Step 2: Create Virtual Environment

A virtual environment keeps dependencies isolated from your system.

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ **Success:** You should see `(venv)` at the start of your terminal line

### Step 3: Install Python Dependencies

With the virtual environment activated, install all required packages:

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- SQLAlchemy (database ORM)
- ChromaDB (vector database)
- Sentence Transformers (AI embeddings)
- OpenAI (GPT integration)
- And other dependencies...

> ⏱️ **Note:** This may take 5-10 minutes on first installation

---

## 🔐 Environment Configuration

### Step 1: Create `.env` File

In the project root directory, create a file named `.env` (with no extension)

### Step 2: Add the Following Configuration

Copy and paste this template into your `.env` file:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# SMTP Email Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=ElitePrep
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here
```

### Step 3: Configure Each Service

#### 🔑 **OpenAI API Key**

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to **API Keys** section
4. Create a new API key
5. Copy and paste it in `.env`

#### 📧 **Gmail SMTP Configuration**

1. Enable **2-Factor Authentication** in your Gmail account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Select "Mail" and "Windows Computer" (or your device)
4. Google will generate a 16-character password
5. Copy this password to `SMTP_PASSWORD` in `.env`

#### 🔐 **JWT Secret**

Generate a strong random string for `JWT_SECRET`:

**Windows PowerShell:**
```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

**macOS/Linux/Windows Git Bash:**
```bash
openssl rand -base64 32
```

---

## ▶️ Running the Application

### Option 1: Using PowerShell Script (Windows - Easiest)

```powershell
.\run.ps1
```

The script will:
- Create virtual environment (if needed)
- Activate it
- Load environment variables
- Start the Flask server

### Option 2: Manual Steps

**1. Activate Virtual Environment**

Windows:
```powershell
.\venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source venv/bin/activate
```

**2. Navigate to Backend**

```bash
cd backend
```

**3. Start Flask Server**

```bash
python main.py
```

Or alternatively:
```bash
flask run
```

### Expected Output

```
 * Serving Flask app 'main'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

---

## 🌐 Accessing the Portal

Once the server is running, open your browser:

### Main Pages

- **Home/Login:** [http://localhost:5000/](http://localhost:5000/)
- **Dashboard:** [http://localhost:5000/dashboard](http://localhost:5000/dashboard)
- **Exam Practice:** [http://localhost:5000/exam.html](http://localhost:5000/exam.html)
- **Results:** [http://localhost:5000/view-results.html](http://localhost:5000/view-results.html)

### API Endpoints (Backend)

**Authentication:**
- `POST` `/api/auth/register` — Register new user
- `POST` `/api/auth/login` — Login user
- `POST` `/api/auth/verify-email` — Verify email code
- `POST` `/api/auth/forget-password` — Request password reset
- `POST` `/api/auth/reset-password` — Reset password with code

**Profile:**
- `POST` `/api/auth/profile` — Update user profile
- `POST` `/api/auth/profile/photo` — Upload profile photo

**Preparation:**
- `POST` `/api/prep/select-exam` — Select exam target (CSS/PMS)
- `GET` `/api/prep/subjects` — Get available subjects
- `POST` `/api/prep/practice` — Get practice questions

**Chat:**
- `POST` `/api/chat` — Chat with AI mentor
- `POST` `/api/expert-chat` — Chat with expert (GPT-4o-mini)

---

## 📁 Project Structure

```
css - Copy - Copy/
├── frontend/                 # HTML/CSS/JavaScript UI
│   ├── index.html           # Login page
│   ├── dashboard.html       # Main dashboard
│   ├── exam.html            # Exam practice interface
│   ├── login.html           # Login page
│   ├── view-results.html    # Results viewer
│   └── assets/
│       ├── css/             # Stylesheets
│       ├── js/              # Frontend scripts
│       └── images/          # Images
│
├── backend/                  # Flask backend
│   ├── main.py              # Flask app entry point
│   ├── seed.py              # Database seeding script
│   ├── app/
│   │   ├── models/          # Database models
│   │   │   └── models.py    # User, Course, Progress models
│   │   ├── api/             # API routes
│   │   │   └── routers/
│   │   │       ├── auth.py  # Authentication endpoints
│   │   │       ├── prep.py  # Preparation endpoints
│   │   │       └── mocktest.py  # Mock test endpoints
│   │   └── services/        # Business logic
│   │       ├── essay_service.py
│   │       ├── evaluator_service.py
│   │       ├── vector_store.py    # ChromaDB integration
│   │       └── openai_service.py
│   └── requirements.txt      # Python dependencies
│
├── chroma_db_v2/            # Vector database (created automatically)
│   └── chroma.sqlite3       # Embedded database
│
├── subjective/              # Past paper data
├── CSS_Banks/               # CSS question banks
├── english essay/           # Essay samples
├── scripts/                 # Utility scripts
├── .env                     # Environment variables (create this)
├── requirements.txt         # Dependencies list
├── run.ps1                  # Windows startup script
├── run.sh                   # Linux/macOS startup script
└── START.md                 # This file

```

---

## 🔧 Troubleshooting

### ❌ "Python not found"
- Python is not installed or not in PATH
- **Solution:** Reinstall Python and check "Add Python to PATH"

### ❌ "ModuleNotFoundError: No module named 'flask'"
- Dependencies not installed
- **Solution:** Run `pip install -r requirements.txt` with venv activated

### ❌ "Port 5000 already in use"
- Another application is using port 5000
- **Solutions:**
  - Option 1: Close other applications
  - Option 2: Change port in `backend/main.py`:
    ```python
    if __name__ == '__main__':
        app.run(debug=True, port=5001)  # Use 5001 instead
    ```

### ❌ ".env file not found or API key error"
- Environment file missing or improperly configured
- **Solution:** 
  - Verify `.env` exists in project root
  - Check all required variables are present
  - No quotes needed around values

### ❌ "Connection refused" or "Cannot connect to localhost:5000"
- Flask server not running
- **Solution:** Run the server again using Step 1 or 2 of [Running the Application](#running-the-application)

### ❌ "Email verification not working"
- SMTP credentials incorrect
- **Solution:**
  - Verify Gmail credentials in `.env`
  - Ensure App Password is used (not regular password)
  - Check 2FA is enabled on Gmail

### ❌ Database Lock or SQLite Errors
- Database is corrupted or locked
- **Solution:**
  - Delete `backend/instance/` folder if it exists
  - Delete `portal.db` file
  - Restart the application (it will recreate the database)

### ❌ "OpenAI API error: Invalid API key"
- API key is incorrect or expired
- **Solution:**
  - Generate a new API key from OpenAI dashboard
  - Update `.env` file with the new key
  - Restart the server

---

## ⚙️ Additional Services

### Optional: Ollama (Local LLM)

For local AI model support without OpenAI:

1. **Install Ollama:** [Download here](https://ollama.ai/)
2. **Start Ollama:**
   ```bash
   ollama serve
   ```
3. **Pull a model:**
   ```bash
   ollama pull mistral
   ```

The backend will automatically use Ollama if available, otherwise falls back to OpenAI.

### Optional: Update Vector Database

To re-index documents in ChromaDB:

```bash
cd backend
python ingest_enhanced.py
```

---

## ✅ Verification Checklist

Before considering setup complete:

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with all credentials
- [ ] OpenAI API key added to `.env`
- [ ] Gmail SMTP configured (or alternative email service)
- [ ] Flask server starts without errors
- [ ] Can access http://localhost:5000 in browser
- [ ] Can register a test account
- [ ] Can verify email (if SMTP working)
- [ ] Can log in successfully

---

## 🎯 Quick Start Summary

For experienced developers, here's the quick version:

```bash
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure .env with API keys

# 4. Run the server
cd backend
python main.py

# 5. Open browser
# http://localhost:5000
```

---

## 📞 Support & Resources

If you encounter issues:

1. **Check Troubleshooting** section above
2. **Review console error messages** carefully
3. **Verify all credentials** in `.env`
4. **Check internet connection** for API calls
5. **Ensure ports are available** (5000 for Flask, 11434 for Ollama)

---

## 🎓 Next Steps

Once the application is running:

1. **Register** a new account at http://localhost:5000
2. **Verify email** by entering the code sent to your email
3. **Log in** with your credentials
4. **Complete profile** with exam target and date
5. **Start practicing** with available subjects and questions
6. **Use AI Chat** for personalized mentoring

---

## 📝 Notes

- **First load may be slow** as ChromaDB creates embeddings
- **Keep `.env` file secure** and never commit it to version control
- **Delete `venv` folder before sharing** project (it's large)
- **Run `pip freeze > requirements.txt`** after adding new packages

---

**Happy Learning! 🚀**

For more information, see `README.md` for full project documentation.
