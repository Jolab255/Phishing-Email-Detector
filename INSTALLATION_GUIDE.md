# Phishing Detector - Installation Guide

This guide details how to set up the Phishing Detector on Windows and Linux.

## Prerequisites
- **Python 3.13+** (Required)
- **Google Cloud Project** with Gemini API enabled.
- **Gmail Account** (for monitoring).

## 1. Google Cloud Setup (One-time)
Before installing, you must set up authentication:
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project and enable the **Gmail API**.
3.  Configure **OAuth Consent Screen** (add your email as a test user).
4.  Create **OAuth 2.0 Credentials** (Desktop App).
5.  Download the JSON file, rename it to `credentials.json`, and place it in the project root folder.
6.  **Important**: Get a **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/) and update `config.py`.

---

## 2. Windows Installation

### Step 1: Install Python 3.13
We recommend installing Python 3.13 via `winget` to ensure compatibility.
```powershell
winget install -e --id Python.Python.3.13 --scope user
```
*Restart your terminal after installation.*

### Step 2: Create a Virtual Environment
Open PowerShell/CMD in the project folder:
```powershell
py -3.13 -m venv .venv
```

### Step 3: Install Dependencies
```powershell
.venv\Scripts\pip install -r requirements.txt
```

### Step 4: Initialize Database
```powershell
.venv\Scripts\flask db upgrade
```

### Step 5: Run Application
```powershell
.venv\Scripts\python run.py
```
Access the app at `http://127.0.0.1:5000`.

---

## 3. Linux Installation (Ubuntu/Debian)

### Step 1: Install Python 3.13
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv
```

### Step 2: Create Virtual Environment
```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database
```bash
flask db upgrade
```

### Step 5: Run Application
```bash
python run.py
```
Access the app at `http://127.0.0.1:5000`.

---

## Troubleshooting

### "Pygame not found" Warning
This application has been patched to run without `pygame`. If you see a warning about audio alerts being disabled, you can ignore it. To enable audio alerts, install pygame manually:
```bash
pip install pygame --pre
```
*(Note: Requires specific pre-release versions for Python 3.13 compatibility)*

### Authentication Error
If `token.json` becomes invalid, delete it and restart the application to re-authenticate with Gmail.

