"""
app.py — Main Streamlit application for Aria AI Calendar Assistant.
"""

import streamlit as st
from datetime import datetime, date, timedelta
import calendar_manager as cm
import ai_scheduler as sched
import gemini_handler as gh
from utils import (
    format_time_12h, format_date_human, format_date_short,
    today_str, get_category_color, get_fc_color,
)

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Aria · AI Calendar",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Session State Init ───────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm **Aria**, your AI scheduling assistant. ✦\n\n"
                "I can help you:\n"
                "- 📅 Schedule meetings and events\n"
                "- 🔍 Find free time slots\n"
                "- ⚠️ Detect and resolve conflicts\n"
                "- 📝 Add notes to events\n\n"
                "Try saying: *\"Schedule a team meeting tomorrow at 2 PM\"*"
            ),
            "ts": datetime.now().strftime("%H:%M"),
        }
    ]

if "selected_date" not in st.session_state:
    st.session_state.selected_date = today_str()

if "calendar_view" not in st.session_state:
    st.session_state.calendar_view = "month"

if "cal_year" not in st.session_state:
    st.session_state.cal_year = date.today().year

if "cal_month" not in st.session_state:
    st.session_state.cal_month = date.today().month

if "show_day_panel" not in st.session_state:
    st.session_state.show_day_panel = False


# ─── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Import Fonts ────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300;1,9..40,400&family=DM+Serif+Display:ital@0;1&display=swap');

/* ── Global Reset ────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #1a1a2e;
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { display: none !important; }
.stDeployButton { display: none !important; }

/* ── App Shell ───────────────────────────────────────────────── */
.app-shell {
    display: flex;
    height: 100vh;
    background: #f6f7fb;
    overflow: hidden;
}

/* ── Left Sidebar (branding + mini nav) ─────────────────────── */
.left-rail {
    width: 72px;
    background: #ffffff;
    border-right: 1px solid #ebebf0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 0;
    gap: 24px;
    flex-shrink: 0;
    z-index: 10;
}

.rail-logo {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #7C3AED, #2563EB);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: white;
    box-shadow: 0 4px 12px rgba(124,58,237,0.3);
    cursor: pointer;
}

.rail-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: #9ca3af;
    cursor: pointer;
    transition: all 0.15s;
}
.rail-icon:hover { background: #f3f4f6; color: #7C3AED; }
.rail-icon.active { background: #EDE9FE; color: #7C3AED; }

/* ── Main Chat Area ──────────────────────────────────────────── */
.chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: #f6f7fb;
}

.chat-header {
    background: white;
    border-bottom: 1px solid #ebebf0;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
}

.chat-header-title {
    display: flex;
    align-items: center;
    gap: 12px;
}

.aria-avatar {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #7C3AED, #2563EB);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: white;
}

.aria-name {
    font-size: 15px;
    font-weight: 600;
    color: #0f0f1a;
}

.aria-status {
    font-size: 12px;
    color: #6b7280;
    display: flex;
    align-items: center;
    gap: 4px;
}

.status-dot {
    width: 7px;
    height: 7px;
    background: #10b981;
    border-radius: 50%;
    display: inline-block;
}

/* ── Messages ────────────────────────────────────────────────── */
.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.messages-container::-webkit-scrollbar { width: 4px; }
.messages-container::-webkit-scrollbar-track { background: transparent; }
.messages-container::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }

.msg-row {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    animation: fadeSlideIn 0.25s ease;
}

.msg-row.user { flex-direction: row-reverse; }

@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
}

.msg-avatar.ai {
    background: linear-gradient(135deg, #7C3AED, #2563EB);
    color: white;
}

.msg-avatar.user {
    background: #1a1a2e;
    color: white;
}

.msg-bubble {
    max-width: 480px;
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.6;
}

.msg-bubble.ai {
    background: white;
    border: 1px solid #ebebf0;
    border-bottom-left-radius: 4px;
    color: #1a1a2e;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.msg-bubble.user {
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    border-bottom-right-radius: 4px;
    color: white;
    box-shadow: 0 4px 12px rgba(124,58,237,0.25);
}

.msg-ts {
    font-size: 10px;
    color: #9ca3af;
    margin-top: 2px;
    text-align: right;
}

.msg-row.user .msg-ts { text-align: left; }

/* ── Input Area ──────────────────────────────────────────────── */
.input-area {
    background: white;
    border-top: 1px solid #ebebf0;
    padding: 16px 32px;
    flex-shrink: 0;
}

/* ── Calendar Panel ──────────────────────────────────────────── */
.cal-panel {
    width: 380px;
    background: white;
    border-left: 1px solid #ebebf0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex-shrink: 0;
}

.cal-panel-header {
    padding: 20px 20px 0;
    border-bottom: 1px solid #ebebf0;
}

.cal-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.cal-month-label {
    font-family: 'DM Serif Display', serif;
    font-size: 18px;
    color: #0f0f1a;
}

.cal-nav-btn {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    border: 1px solid #ebebf0;
    background: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #6b7280;
    transition: all 0.15s;
}
.cal-nav-btn:hover { background: #f3f4f6; color: #0f0f1a; }

.cal-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
    padding: 12px 0;
}

.cal-dow {
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 4px 0;
}

.cal-day {
    aspect-ratio: 1;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    color: #374151;
    transition: all 0.15s;
    position: relative;
    gap: 2px;
}

.cal-day:hover { background: #f3f4f6; }
.cal-day.other-month { color: #d1d5db; }
.cal-day.today { background: #EDE9FE; color: #7C3AED; font-weight: 700; }
.cal-day.selected { background: linear-gradient(135deg, #7C3AED, #4F46E5); color: white !important; }
.cal-day.selected:hover { opacity: 0.9; }
.cal-day.has-events::after {
    content: '';
    width: 4px;
    height: 4px;
    background: #7C3AED;
    border-radius: 50%;
    position: absolute;
    bottom: 3px;
}
.cal-day.selected::after { background: white; }
.cal-day.today.has-events::after { background: #7C3AED; }

/* ── Day Events Panel ────────────────────────────────────────── */
.day-panel {
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
}

.day-panel::-webkit-scrollbar { width: 4px; }
.day-panel::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 2px; }

.day-panel-title {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.event-card {
    background: #f9fafb;
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 8px;
    border-left: 3px solid;
    transition: all 0.15s;
    cursor: default;
}
.event-card:hover { transform: translateX(2px); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

.event-title {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 2px;
}

.event-time {
    font-size: 11px;
    color: #6b7280;
    margin-bottom: 4px;
}

.event-note {
    font-size: 11px;
    color: #9ca3af;
    font-style: italic;
}

.event-category-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-top: 4px;
}

.free-slot {
    background: #f0fdf4;
    border: 1px dashed #86efac;
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 11px;
    color: #059669;
    display: flex;
    align-items: center;
    gap: 6px;
}

.no-events {
    text-align: center;
    padding: 24px 0;
    color: #9ca3af;
    font-size: 13px;
}

/* ── Stats Strip ─────────────────────────────────────────────── */
.stats-strip {
    display: flex;
    gap: 8px;
    padding: 12px 20px;
    border-top: 1px solid #ebebf0;
    border-bottom: 1px solid #ebebf0;
    background: #fafafa;
    flex-shrink: 0;
}

.stat-pill {
    flex: 1;
    background: white;
    border: 1px solid #ebebf0;
    border-radius: 8px;
    padding: 8px 10px;
    text-align: center;
}

.stat-num {
    font-size: 18px;
    font-weight: 700;
    color: #7C3AED;
    line-height: 1;
}

.stat-lbl {
    font-size: 10px;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-top: 2px;
}

/* ── Streamlit Widget Overrides ──────────────────────────────── */
div[data-testid="stTextInput"] > div > div > input {
    background: #f6f7fb !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #1a1a2e !important;
    box-shadow: none !important;
    transition: border-color 0.15s;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
}

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    box-shadow: 0 4px 12px rgba(124,58,237,0.3) !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(124,58,237,0.4) !important;
}

/* Secondary buttons */
div[data-testid="stButton"]:nth-child(n) > button.secondary {
    background: white !important;
    color: #374151 !important;
    border: 1px solid #e5e7eb !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}

div[data-testid="stSelectbox"] > div > div {
    border-radius: 8px !important;
    border-color: #e5e7eb !important;
    font-size: 13px !important;
}

/* Columns spacing */
div[data-testid="column"] { padding: 0 !important; }

/* Collapse sidebar */
div[data-testid="collapsedControl"] { display: none; }

/* Remove default padding from containers */
div[data-testid="stVerticalBlock"] { gap: 0 !important; }

/* Scrollable message container hack */
.stMarkdown { max-width: 100%; }

/* ── Typing Indicator ────────────────────────────────────────── */
.typing-dots {
    display: flex;
    gap: 4px;
    padding: 4px 0;
}
.typing-dots span {
    width: 6px; height: 6px;
    background: #9ca3af;
    border-radius: 50%;
    animation: bounce 1.2s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30%            { transform: translateY(-6px); }
}

/* ── Scrollbar hide for main content ─────────────────────────── */
section.main { overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _render_message(msg: dict):
    role = msg["role"]
    content = msg["content"]
    ts = msg.get("ts", "")
    is_user = role == "user"

    row_class = "msg-row user" if is_user else "msg-row"
    bubble_class = "msg-bubble user" if is_user else "msg-bubble ai"
    avatar_class = "msg-avatar user" if is_user else "msg-avatar ai"
    avatar_icon = "U" if is_user else "✦"

    st.markdown(f"""
    <div class="{row_class}">
        <div class="{avatar_class}">{avatar_icon}</div>
        <div>
            <div class="{bubble_class}">{_md_to_html(content)}</div>
            <div class="msg-ts">{ts}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _md_to_html(text: str) -> str:
    """Very light markdown → HTML for bubble content."""
    import re
    # bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # newlines
    text = text.replace('\n', '<br>')
    # bullet lines
    text = re.sub(r'• (.+?)(<br>|$)', r'<span style="display:block;padding-left:12px">• \1</span>', text)
    return text


def _build_calendar_html(year: int, month: int, events_by_date: set, selected: str) -> str:
    import calendar
    cal = calendar.monthcalendar(year, month)
    today = date.today()
    month_name = date(year, month, 1).strftime("%B %Y")

    rows = ""
    dow_row = "".join(f'<div class="cal-dow">{d}</div>' for d in ["Su","Mo","Tu","We","Th","Fr","Sa"])

    for week in cal:
        for day in week:
            if day == 0:
                rows += '<div class="cal-day other-month"></div>'
            else:
                d = date(year, month, day)
                d_str = d.isoformat()
                classes = "cal-day"
                if d == today:
                    classes += " today"
                if d_str == selected:
                    classes += " selected"
                if d_str in events_by_date:
                    classes += " has-events"
                if d.month != month:
                    classes += " other-month"
                rows += f'<div class="{classes}" onclick="window.location.href=\'?date={d_str}\'">{day}</div>'

    return f"""
    <div class="cal-grid">
        {dow_row}
        {rows}
    </div>
    """


def _day_summary_stats(date_str: str) -> dict:
    return sched.get_day_summary(date_str)


# ─── Calendar Date Navigation (uses query params via URL or buttons) ──────────

def _prev_month():
    m, y = st.session_state.cal_month, st.session_state.cal_year
    if m == 1:
        st.session_state.cal_month = 12
        st.session_state.cal_year = y - 1
    else:
        st.session_state.cal_month = m - 1

def _next_month():
    m, y = st.session_state.cal_month, st.session_state.cal_year
    if m == 12:
        st.session_state.cal_month = 1
        st.session_state.cal_year = y + 1
    else:
        st.session_state.cal_month = m + 1


# ─── Layout ──────────────────────────────────────────────────────────────────

# Use Streamlit columns to approximate our layout
# Col ratio: [thin rail] [chat] [calendar panel]
col_rail, col_chat, col_cal = st.columns([1, 8, 4], gap="small")

# ── Left Rail ─────────────────────────────────────────────────────────────────
with col_rail:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
                padding:16px 0;gap:16px;height:100vh;
                border-right:1px solid #ebebf0;background:white;">
        <div class="rail-logo">✦</div>
        <div class="rail-icon active" title="Calendar">📅</div>
        <div class="rail-icon" title="Tasks">✓</div>
        <div class="rail-icon" title="Settings">⚙</div>
    </div>
    """, unsafe_allow_html=True)


# ── Chat Panel ────────────────────────────────────────────────────────────────
with col_chat:
    # Header
    st.markdown("""
    <div class="chat-header">
        <div class="chat-header-title">
            <div class="aria-avatar">✦</div>
            <div>
                <div class="aria-name">Aria</div>
                <div class="aria-status">
                    <span class="status-dot"></span> AI Scheduling Assistant
                </div>
            </div>
        </div>
        <div style="font-size:12px;color:#9ca3af;">
            Today · {today}
        </div>
    </div>
    """.format(today=format_date_short(today_str())), unsafe_allow_html=True)

    # Messages
    with st.container():
        st.markdown('<div class="messages-container" id="chat-messages">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            _render_message(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input row
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    input_col, btn_col = st.columns([10, 1], gap="small")
    with input_col:
        user_input = st.text_input(
            "message",
            placeholder='Ask Aria to schedule something, find free time, or chat…',
            label_visibility="collapsed",
            key="chat_input",
        )
    with btn_col:
        send_clicked = st.button("↑", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Quick suggestion chips
    chip_cols = st.columns(4, gap="small")
    chips = [
        "📅 Schedule a meeting",
        "🕐 Find free time today",
        "📋 Show today's events",
        "⚡ Add a deadline",
    ]
    selected_chip = None
    for i, chip in enumerate(chips):
        with chip_cols[i]:
            if st.button(chip, key=f"chip_{i}", use_container_width=True):
                selected_chip = chip.split(" ", 1)[1]  # strip emoji

    # Process input
    message_to_send = None
    if send_clicked and user_input.strip():
        message_to_send = user_input.strip()
    elif selected_chip:
        message_to_send = selected_chip

    if message_to_send:
        ts = datetime.now().strftime("%H:%M")

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": message_to_send,
            "ts": ts,
        })

        # Get AI response
        with st.spinner(""):
            reply, action = gh.chat_with_gemini(
                message_to_send,
                st.session_state.messages[:-1],
            )

        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "ts": datetime.now().strftime("%H:%M"),
        })

        # If an event was created, update selected date to show it
        if action and action.get("intent") == "create_event" and action.get("id"):
            st.session_state.selected_date = action.get("date", today_str())

        st.rerun()


# ── Calendar Panel ────────────────────────────────────────────────────────────
with col_cal:
    year  = st.session_state.cal_year
    month = st.session_state.cal_month
    selected = st.session_state.selected_date

    # Fetch events for dot markers
    month_events = cm.get_events_for_month(year, month)
    event_dates  = {e["date"] for e in month_events}

    # Header
    month_label = date(year, month, 1).strftime("%B %Y")
    st.markdown(f"""
    <div style="background:white;border-bottom:1px solid #ebebf0;padding:16px 20px 0;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <span style="font-family:'DM Serif Display',serif;font-size:18px;color:#0f0f1a;">{month_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Month nav buttons
    nav_l, nav_r, nav_today = st.columns([1, 1, 2], gap="small")
    with nav_l:
        if st.button("‹", key="prev_month", use_container_width=True):
            _prev_month()
            st.rerun()
    with nav_r:
        if st.button("›", key="next_month", use_container_width=True):
            _next_month()
            st.rerun()
    with nav_today:
        if st.button("Today", key="today_btn", use_container_width=True):
            st.session_state.cal_year = date.today().year
            st.session_state.cal_month = date.today().month
            st.session_state.selected_date = today_str()
            st.rerun()

    # Calendar grid
    import calendar as cal_mod
    cal_obj = cal_mod.monthcalendar(year, month)
    today_d = date.today()

    # Day-of-week headers
    dow_cols = st.columns(7, gap="small")
    for i, d in enumerate(["Su","Mo","Tu","We","Th","Fr","Sa"]):
        with dow_cols[i]:
            st.markdown(f'<div style="text-align:center;font-size:10px;font-weight:600;'
                        f'color:#9ca3af;letter-spacing:0.5px;padding:4px 0;">{d}</div>',
                        unsafe_allow_html=True)

    # Day cells
    for week in cal_obj:
        week_cols = st.columns(7, gap="small")
        for i, day in enumerate(week):
            with week_cols[i]:
                if day == 0:
                    st.markdown('<div style="aspect-ratio:1;"></div>', unsafe_allow_html=True)
                else:
                    d_obj = date(year, month, day)
                    d_str = d_obj.isoformat()
                    is_today    = (d_obj == today_d)
                    is_selected = (d_str == selected)
                    has_events  = (d_str in event_dates)

                    # Style
                    if is_selected:
                        bg = "linear-gradient(135deg,#7C3AED,#4F46E5)"
                        color = "white"
                        fw = "700"
                    elif is_today:
                        bg = "#EDE9FE"
                        color = "#7C3AED"
                        fw = "700"
                    else:
                        bg = "transparent"
                        color = "#374151"
                        fw = "500"

                    dot = ""
                    if has_events:
                        dot_color = "white" if is_selected else "#7C3AED"
                        dot = f'<div style="width:4px;height:4px;background:{dot_color};border-radius:50%;margin:0 auto;"></div>'

                    label = st.markdown(
                        f'<div style="aspect-ratio:1;background:{bg};border-radius:8px;'
                        f'display:flex;flex-direction:column;align-items:center;justify-content:center;'
                        f'cursor:pointer;font-size:12px;font-weight:{fw};color:{color};gap:2px;">'
                        f'{day}{dot}</div>',
                        unsafe_allow_html=True
                    )

                    if st.button(str(day), key=f"day_{d_str}", use_container_width=True,
                                 help=f"View {d_str}"):
                        st.session_state.selected_date = d_str
                        st.rerun()

    st.markdown("---")

    # ── Day Detail Panel ──────────────────────────────────────────────────────
    sel_date  = st.session_state.selected_date
    day_evts  = cm.get_events_for_date(sel_date)
    summary   = sched.get_day_summary(sel_date)
    free_slots = sched.get_free_slots(sel_date)

    # Stats strip
    busy_h = summary["busy_minutes"] // 60
    free_h = summary["free_minutes"] // 60

    stat_c1, stat_c2, stat_c3 = st.columns(3, gap="small")
    with stat_c1:
        st.markdown(f"""
        <div class="stat-pill">
            <div class="stat-num">{len(day_evts)}</div>
            <div class="stat-lbl">Events</div>
        </div>""", unsafe_allow_html=True)
    with stat_c2:
        st.markdown(f"""
        <div class="stat-pill">
            <div class="stat-num">{busy_h}h</div>
            <div class="stat-lbl">Busy</div>
        </div>""", unsafe_allow_html=True)
    with stat_c3:
        st.markdown(f"""
        <div class="stat-pill">
            <div class="stat-num">{free_h}h</div>
            <div class="stat-lbl">Free</div>
        </div>""", unsafe_allow_html=True)

    # Selected date label
    st.markdown(
        f'<div style="font-size:13px;font-weight:600;color:#374151;'
        f'padding:12px 0 8px;">{format_date_human(sel_date)}</div>',
        unsafe_allow_html=True
    )

    if summary["overloaded"]:
        st.markdown("""
        <div style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:8px;
                    padding:8px 12px;font-size:12px;color:#92400E;margin-bottom:8px;">
            ⚠️ This day is heavily scheduled
        </div>""", unsafe_allow_html=True)

    # Events list
    if not day_evts:
        st.markdown("""
        <div class="no-events">
            <div style="font-size:28px;margin-bottom:8px;">🌿</div>
            <div>No events scheduled</div>
            <div style="font-size:11px;margin-top:4px;">Ask Aria to add one!</div>
        </div>""", unsafe_allow_html=True)
    else:
        for ev in day_evts:
            colors = get_category_color(ev.get("category", "other"))
            note_html = f'<div class="event-note">📝 {ev["note"]}</div>' if ev.get("note") else ""
            cat = (ev.get("category") or "other").capitalize()

            st.markdown(f"""
            <div class="event-card" style="border-left-color:{colors['border']};">
                <div class="event-title" style="color:{colors['text']};">{ev['title']}</div>
                <div class="event-time">🕐 {format_time_12h(ev['start_time'])} – {format_time_12h(ev['end_time'])}</div>
                {note_html}
                <span class="event-category-badge"
                      style="background:{colors['bg']};color:{colors['text']};">{cat}</span>
            </div>
            """, unsafe_allow_html=True)

            # Delete button per event
            if st.button(f"🗑 Delete", key=f"del_{ev['id']}", help=f"Delete {ev['title']}"):
                cm.delete_event(ev["id"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"🗑️ **{ev['title']}** has been removed.",
                    "ts": datetime.now().strftime("%H:%M"),
                })
                st.rerun()

    # Free slots
    if free_slots:
        st.markdown('<div style="margin-top:8px;font-size:11px;font-weight:600;'
                    'color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;'
                    'margin-bottom:6px;">Free Slots</div>', unsafe_allow_html=True)
        for slot in free_slots[:4]:
            from utils import minutes_to_hhmm
            dur = minutes_to_hhmm(slot["duration_minutes"])
            st.markdown(f"""
            <div class="free-slot">
                ✓ {format_time_12h(slot['start'])} – {format_time_12h(slot['end'])}
                <span style="color:#6b7280;margin-left:auto;">{dur}</span>
            </div>""", unsafe_allow_html=True)


# ── Auto-scroll chat to bottom ────────────────────────────────────────────────
st.markdown("""
<script>
    const container = document.getElementById('chat-messages');
    if (container) container.scrollTop = container.scrollHeight;

    // Hide streamlit day number buttons — we only show HTML visual
    document.querySelectorAll('[data-testid="stButton"]').forEach(btn => {
        const txt = btn.innerText.trim();
        if (txt.length <= 2 && !isNaN(parseInt(txt)) && parseInt(txt) > 0) {
            btn.style.cssText = 'position:absolute;opacity:0;width:100%;height:100%;top:0;left:0;cursor:pointer;z-index:1;';
        }
    });
</script>
""", unsafe_allow_html=True)