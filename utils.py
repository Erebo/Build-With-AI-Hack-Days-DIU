"""
utils.py — Helper functions for time/date formatting, color mapping, parsing.
"""

from datetime import datetime, date, time
import re


# ─── Color Mapping ────────────────────────────────────────────────────────────

CATEGORY_COLORS = {
    "meeting":   {"bg": "#EDE9FE", "border": "#7C3AED", "text": "#5B21B6", "dot": "#7C3AED"},
    "study":     {"bg": "#DBEAFE", "border": "#2563EB", "text": "#1D4ED8", "dot": "#2563EB"},
    "personal":  {"bg": "#D1FAE5", "border": "#059669", "text": "#065F46", "dot": "#059669"},
    "deadline":  {"bg": "#FEE2E2", "border": "#DC2626", "text": "#991B1B", "dot": "#DC2626"},
    "health":    {"bg": "#FCE7F3", "border": "#DB2777", "text": "#9D174D", "dot": "#DB2777"},
    "social":    {"bg": "#FEF3C7", "border": "#D97706", "text": "#92400E", "dot": "#D97706"},
    "work":      {"bg": "#E0E7FF", "border": "#4F46E5", "text": "#3730A3", "dot": "#4F46E5"},
    "other":     {"bg": "#F3F4F6", "border": "#6B7280", "text": "#374151", "dot": "#6B7280"},
}

FULLCALENDAR_COLORS = {
    "meeting":  "#7C3AED",
    "study":    "#2563EB",
    "personal": "#059669",
    "deadline": "#DC2626",
    "health":   "#DB2777",
    "social":   "#D97706",
    "work":     "#4F46E5",
    "other":    "#6B7280",
}


def get_category_color(category: str) -> dict:
    cat = (category or "other").lower().strip()
    return CATEGORY_COLORS.get(cat, CATEGORY_COLORS["other"])


def get_fc_color(category: str) -> str:
    cat = (category or "other").lower().strip()
    return FULLCALENDAR_COLORS.get(cat, FULLCALENDAR_COLORS["other"])


# ─── Time & Date Formatting ───────────────────────────────────────────────────

def format_time_12h(time_str: str) -> str:
    """Convert 'HH:MM' or 'HH:MM:SS' → '3:00 PM'."""
    if not time_str:
        return ""
    try:
        t = datetime.strptime(time_str[:5], "%H:%M")
        return t.strftime("%-I:%M %p")
    except Exception:
        return time_str


def format_date_human(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' → 'Monday, May 19, 2026'."""
    if not date_str:
        return ""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%A, %B %-d, %Y")
    except Exception:
        return date_str


def format_date_short(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' → 'May 19'."""
    if not date_str:
        return ""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%b %-d")
    except Exception:
        return date_str


def today_str() -> str:
    return date.today().isoformat()


def now_str() -> str:
    return datetime.now().strftime("%H:%M")


def minutes_to_hhmm(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if h and m else (f"{h}h" if h else f"{m}m")


def time_to_minutes(time_str: str) -> int:
    """'HH:MM' → total minutes from midnight."""
    try:
        parts = time_str[:5].split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0


def minutes_to_time(minutes: int) -> str:
    """Total minutes from midnight → 'HH:MM'."""
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


# ─── Parsing Helpers ──────────────────────────────────────────────────────────

def parse_relative_date(phrase: str) -> str | None:
    """Resolve 'today', 'tomorrow', 'next monday', etc. → 'YYYY-MM-DD'."""
    from datetime import timedelta
    import calendar as cal_mod

    phrase = phrase.lower().strip()
    today = date.today()

    if phrase == "today":
        return today.isoformat()
    if phrase == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    if phrase == "yesterday":
        return (today - timedelta(days=1)).isoformat()

    # "next <weekday>"
    days_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6}
    m = re.match(r"next\s+(\w+)", phrase)
    if m and m.group(1) in days_map:
        target = days_map[m.group(1)]
        current = today.weekday()
        delta = (target - current + 7) % 7 or 7
        return (today + timedelta(days=delta)).isoformat()

    return None


def clean_json_response(raw: str) -> str:
    """Strip markdown code fences from a JSON string."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw)
    raw = re.sub(r"```$", "", raw)
    return raw.strip()


def infer_end_time(start_time: str, duration_minutes: int = 60) -> str:
    """Given start 'HH:MM' and duration in minutes, return end 'HH:MM'."""
    start_mins = time_to_minutes(start_time)
    return minutes_to_time(start_mins + duration_minutes)