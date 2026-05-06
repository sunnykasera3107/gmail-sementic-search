# Gmail API Setup Guide (Step-by-Step)

This guide walks you through setting up the Gmail API and downloading your `credentials.json` file for use in applications like Django or Python scripts.

---

## 1) Create a Project in Google Cloud Console

1. Go to Google Cloud Console  
2. Click **"Select Project" → "New Project"**  
3. Enter a project name  
4. Click **Create**

---

## 2) Enable Gmail API

1. Navigate to **APIs & Services → Library**  
2. Search for **Gmail API**  
3. Click on it and press **Enable**

---

## 3) Configure OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**  
2. Select:
   - **External** (for testing)  

3. Fill required fields:
   - App name  
   - User support email  

### Add Scopes (based on your use case):

- Read emails:
https://www.googleapis.com/auth/gmail.readonly


4. Add **Test Users** (your email)  
5. Click **Save**

---

## 4) Create Credentials

1. Go to **APIs & Services → Credentials**  
2. Click **"Create Credentials" → "OAuth client ID"**

### Choose Application Type:

- **Desktop app** → for local scripts / testing  
- **Web application** → for Django or web apps  

### For Web Application, add Redirect URI:

http://localhost:8000/ingest/

---

## 5) Download `credentials.json`

## 6) Add `credentials.json` file to `secrets` folder in project directory

1. After creating credentials  
2. Click **Download JSON**  

You will get: credentials.json

# Installation & Running Application

from root directory run the following cmd to install dependencies:
```
pip install -r requirements.txt

cd sementicsearchemails

uvicorn sementicsearchemails.asgi:application --reload
```
