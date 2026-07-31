# 🎉 Eventify

A web app that generates complete event plans using AI. Enter your event
details (type, date, guests, budget, location) and the app uses **Groq AI**
to produce a full plan: summary, timeline, budget breakdown, checklist,
vendor suggestions, and tips. Plans are saved to your account so you can
revisit them later.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python (Flask) |
| Database | SQLite (single file, zero setup) |
| AI | Groq API (`llama-3.3-70b-versatile`) |

## ⭐ Prompt Engineering Principle: Few-Shot Prompting

This project features **few-shot prompting**. Before sending your real
request to the AI, we include **two complete worked examples** (a birthday
party and a corporate conference), each showing an input paired with the
ideal JSON output. The model learns the exact structure and quality we want
**by example**, so it returns consistent, well-organized plans instead of
free-form text. See [`ai_service.py`](ai_service.py).

## Features

- 🔐 User accounts — register, log in, log out (passwords are securely hashed)
- 🤖 AI-generated event plans (Groq + few-shot prompting)
- 💾 Plans saved per user
- 📜 History page to view all your past plans
- 🖨️ Print / Save-as-PDF any plan
- 🗑️ Delete plans you no longer need

## Setup & Run

### 1. Install Python
Requires **Python 3.10+**. Check with:
```
python --version
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Add your Groq API key
Get a free key from https://console.groq.com (API Keys → Create).
Open the `.env` file and paste your key:
```
GROQ_API_KEY=gsk_your_key_here
```

### 4. Run the app
```
python app.py
```
Then open **http://127.0.0.1:5000** in your browser.

That's it — the SQLite database is created automatically on first run.
No database server or password needed.

## Project Structure

```
AI EVENT PLANNAR/
├── app.py            # Flask routes (auth, planner, history, API)
├── ai_service.py     # Groq integration (few-shot prompting)
├── db.py             # SQLite helpers (users + event_plans)
├── config.py         # Loads settings from .env
├── requirements.txt  # Python dependencies
├── .env              # Your secrets (Groq key) — not shared
├── schema.sql        # Reference database schema
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html         # Shared layout + nav
    ├── login.html
    ├── register.html
    ├── index.html        # Planner
    ├── history.html
    └── view_plan.html
```

## How it works (flow)

1. You register / log in.
2. On the **Planner** page you enter event details and click *Generate Plan*.
3. The browser sends the details to `/api/generate`.
4. `ai_service.py` builds a prompt with **few-shot examples** and calls Groq.
5. Groq returns a structured JSON plan, which is saved to SQLite.
6. The plan is rendered on the page and appears in your **History**.
