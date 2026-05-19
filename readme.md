# ✦ Aria — AI Calendar Assistant

A premium AI-powered scheduling assistant built with Streamlit, Gemini, and SQLite.

---

## ✨ Features

- **Natural language scheduling** — "Schedule a team standup every Monday at 9 AM"
- **Conflict detection** — Aria warns you and suggests alternatives automatically
- **Free-time analysis** — "When am I free tomorrow?" returns real slot data
- **Interactive calendar** — Month view with day drill-down, event colors, free-slot display
- **Persistent events** — SQLite database, survives restarts
- **Premium UI** — DM Sans + DM Serif Display, glassmorphism-lite, gradient accents

---

## 🗂 Project Structure

```
ai_calendar_bot/
├── app.py               ← Main Streamlit UI
├── gemini_handler.py    ← Gemini API + JSON action executor
├── calendar_manager.py  ← SQLite CRUD layer
├── ai_scheduler.py      ← Conflict detection & free-slot logic
├── utils.py             ← Formatting helpers & color maps
├── database.db          ← Auto-created on first run
├── requirements.txt
├── .env                 ← Your API key lives here
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone / copy files
Place all files in a folder called `ai_calendar_bot/`.

### 2. Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your Gemini API key
Edit `.env`:
```
GEMINI_API_KEY=your_actual_key_here
```
Get a free key at https://aistudio.google.com/app/apikey

### 5. Run the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 💬 Example Conversations

```
You:  Schedule a project meeting tomorrow at 3 PM
Aria: ✅ Project meeting added — tomorrow, 3:00 PM – 4:00 PM

You:  When am I free tomorrow?
Aria: You are free:
      • 8:00 AM – 3:00 PM  (7h)
      • 4:00 PM – 10:00 PM (6h)

You:  Add a deadline for the design review on Friday at 5 PM
Aria: ✅ Design review deadline added — Friday, 5:00 PM – 6:00 PM

You:  Schedule a call at 3 PM tomorrow
Aria: ⚠️ Conflict detected! You already have Project meeting (3:00 PM).
      💡 Next available slot: 4:00 PM – 5:00 PM
      Would you like to reschedule?
```

---

## 🎨 Event Categories & Colors

| Category  | Color  |
|-----------|--------|
| Meeting   | Purple |
| Study     | Blue   |
| Work      | Indigo |
| Personal  | Green  |
| Deadline  | Red    |
| Health    | Pink   |
| Social    | Amber  |
| Other     | Gray   |

---

## ⚙️ Environment Variables

| Variable         | Description              |
|------------------|--------------------------|
| `GEMINI_API_KEY` | Your Google Gemini key   |

---

## 📦 Dependencies

```
streamlit==1.35.0
google-generativeai==0.7.2
python-dotenv==1.0.1
streamlit-calendar==1.3.0
pandas==2.2.2
python-dateutil==2.9.0
```

---

## 🧠 Architecture

```
User input
    │
    ▼
gemini_handler.py  ──→  Gemini 1.5 Flash (structured JSON)
    │
    ▼
ai_scheduler.py    ──→  Conflict check / free-slot calc
    │
    ▼
calendar_manager.py ──→  SQLite read/write
    │
    ▼
app.py             ──→  Streamlit UI render
```

---

## 🛠 Troubleshooting

**"API key not configured"** — Add `GEMINI_API_KEY` to `.env` and restart.

**Calendar not updating** — Click a date or send a new message; Streamlit reruns on interaction.

**Import errors** — Ensure your virtual environment is active and `pip install -r requirements.txt` completed.