"""
app.py — Aria AI Calendar Assistant · Premium Redesign (Fixed + Colorful)
"""

import streamlit as st
from datetime import datetime, date, timedelta
import calendar_manager as cm
import ai_scheduler as sched
import gemini_handler as gh
from utils import (
    format_time_12h, format_date_human, format_date_short,
    today_str, get_category_color, get_fc_color, minutes_to_hhmm,
)

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Aria · AI Calendar",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Session State ────────────────────────────────────────────────────────────

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
if "cal_year" not in st.session_state:
    st.session_state.cal_year = date.today().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = date.today().month

# ── FIX: Key counter to clear input after submit ──────────────────────────────
if "input_key" not in st.session_state:
    st.session_state.input_key = 0


# ─── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Fonts ───────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;1,500&display=swap');

/* ── Root Variables ──────────────────────────────────────────── */
:root {
    --bg:         #F0EFF8;
    --surface:    rgba(255,255,255,0.85);
    --surface2:   rgba(255,255,255,0.6);
    --glass:      rgba(255,255,255,0.72);
    --border:     rgba(124,58,237,0.10);
    --border2:    rgba(0,0,0,0.06);
    --accent:     #6D28D9;
    --accent2:    #4F46E5;
    --accent-lt:  #EDE9FE;
    --accent-grd: linear-gradient(135deg, #6D28D9 0%, #4F46E5 100%);
    --text:       #18181B;
    --text2:      #52525B;
    --text3:      #A1A1AA;
    --green:      #059669;
    --red:        #DC2626;
    --orange:     #D97706;
    --shadow:     0 8px 32px rgba(109,40,217,0.10);
    --shadow2:    0 2px 12px rgba(0,0,0,0.07);
    --radius:     16px;
    --radius-sm:  10px;
    --font:       'Outfit', sans-serif;
}

/* ── Reset ───────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: var(--font) !important;
    color: var(--text);
    margin: 0;
    padding: 0;
}

/* ── Hide Streamlit chrome ───────────────────────────────────── */
#MainMenu, footer, header,
.stDeployButton,
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }

/* ── Page background ─────────────────────────────────────────── */
.stApp {
    background:
        radial-gradient(ellipse 80% 60% at 10% 0%, rgba(139,92,246,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 100%, rgba(99,102,241,0.15) 0%, transparent 60%),
        radial-gradient(ellipse 40% 40% at 50% 50%, rgba(236,72,153,0.05) 0%, transparent 60%),
        #EEF0FB !important;
    min-height: 100vh;
}

/* Remove default padding */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    overflow: hidden;
}
section.main { overflow: hidden !important; }
div[data-testid="stVerticalBlock"] { gap: 0 !important; }
div[data-testid="column"] { padding: 0 !important; }
.stMarkdown { max-width: 100%; }

/* ── Rail ────────────────────────────────────────────────────── */
.rail-logo {
    width: 42px; height: 42px;
    background: var(--accent-grd);
    border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; color: white;
    box-shadow: 0 4px 16px rgba(109,40,217,0.40);
    margin-bottom: 18px;
    letter-spacing: -0.5px;
    font-weight: 800;
}
.rail-item {
    width: 44px; height: 44px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    color: var(--text3);
    cursor: pointer;
    transition: all 0.18s ease;
}
.rail-item:hover { background: rgba(109,40,217,0.08); color: var(--accent); }
.rail-item.active {
    background: var(--accent-lt);
    color: var(--accent);
    box-shadow: 0 2px 10px rgba(109,40,217,0.15);
}
.rail-spacer { flex: 1; }

/* ── Chat Header ─────────────────────────────────────────────── */
.chat-hdr {
    background: linear-gradient(135deg, rgba(109,40,217,0.08) 0%, rgba(79,70,229,0.06) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(109,40,217,0.12);
    padding: 14px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
}
.aria-id { display: flex; align-items: center; gap: 12px; }
.aria-avatar {
    width: 40px; height: 40px;
    background: var(--accent-grd);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; color: white;
    box-shadow: 0 3px 12px rgba(109,40,217,0.40);
    font-weight: 700;
}
.aria-name-lbl {
    font-size: 15px; font-weight: 700;
    color: var(--text); letter-spacing: -0.2px;
}
.aria-status-lbl {
    font-size: 11px; color: var(--text3);
    display: flex; align-items: center; gap: 5px; margin-top: 1px;
}
.online-dot {
    width: 7px; height: 7px;
    background: #10B981; border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 2px rgba(16,185,129,0.30),
                0 0 8px rgba(16,185,129,0.4);
    animation: pulse-green 2s infinite;
}
@keyframes pulse-green {
    0%, 100% { box-shadow: 0 0 0 2px rgba(16,185,129,0.3); }
    50%       { box-shadow: 0 0 0 4px rgba(16,185,129,0.15); }
}
.hdr-date {
    font-size: 12px;
    color: var(--accent);
    background: var(--accent-lt);
    padding: 5px 14px;
    border-radius: 20px;
    font-weight: 600;
    border: 1px solid rgba(109,40,217,0.15);
}

/* ── Messages ────────────────────────────────────────────────── */
.msgs-wrap {
    flex: 1;
    overflow-y: auto;
    padding: 20px 28px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    scroll-behavior: smooth;
}
.msgs-wrap::-webkit-scrollbar { width: 4px; }
.msgs-wrap::-webkit-scrollbar-track { background: transparent; }
.msgs-wrap::-webkit-scrollbar-thumb { background: rgba(109,40,217,0.2); border-radius: 2px; }

.mrow {
    display: flex;
    align-items: flex-end;
    gap: 9px;
    animation: msgIn 0.22s cubic-bezier(.2,.8,.3,1) both;
}
.mrow.user { flex-direction: row-reverse; }
@keyframes msgIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.mavatar {
    width: 28px; height: 28px;
    border-radius: 50%;
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
}
.mavatar.ai  { background: var(--accent-grd); color: white; }
.mavatar.user { background: #18181B; color: white; }

.mbubble {
    max-width: 500px;
    padding: 11px 15px;
    border-radius: 18px;
    font-size: 13.5px;
    line-height: 1.65;
    font-weight: 400;
}
.mbubble.ai {
    background: white;
    border: 1px solid rgba(109,40,217,0.10);
    border-bottom-left-radius: 4px;
    color: var(--text);
    box-shadow: 0 2px 16px rgba(109,40,217,0.08);
}
.mbubble.user {
    background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%);
    border-bottom-right-radius: 4px;
    color: white;
    box-shadow: 0 4px 18px rgba(109,40,217,0.35);
}
.mts { font-size: 9.5px; color: var(--text3); margin-top: 3px; padding: 0 2px; }
.mrow.user .mts { text-align: right; }

/* ── Input Zone ──────────────────────────────────────────────── */
.input-zone {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top: 1px solid rgba(109,40,217,0.10);
    padding: 14px 28px 12px;
    flex-shrink: 0;
}

/* ── Quick Chips ─────────────────────────────────────────────── */
.chip-row { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }

/* ── Calendar Panel Header ───────────────────────────────────── */
.cal-hdr {
    padding: 16px 18px 0;
    flex-shrink: 0;
    background: linear-gradient(135deg, rgba(109,40,217,0.07) 0%, rgba(79,70,229,0.05) 100%);
    border-bottom: 1px solid rgba(109,40,217,0.08);
}
.cal-month-row {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 14px;
}
.cal-month-lbl {
    font-family: 'Playfair Display', serif;
    font-size: 17px; color: var(--text); font-weight: 600;
}
.cal-dow {
    text-align: center; font-size: 9.5px; font-weight: 700;
    color: var(--accent); text-transform: uppercase;
    letter-spacing: 0.6px; padding: 4px 0 8px;
}
.cal-day {
    aspect-ratio: 1; border-radius: 9px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-size: 12.5px; font-weight: 500;
    color: var(--text2); position: relative; gap: 2px;
    transition: all 0.14s;
}
.cal-day:hover { background: rgba(109,40,217,0.10); color: var(--accent); }
.cal-day.today {
    background: var(--accent-lt);
    color: var(--accent); font-weight: 700;
    box-shadow: inset 0 0 0 1.5px rgba(109,40,217,0.25);
}
.cal-day.selected {
    background: linear-gradient(135deg,#7C3AED,#4F46E5) !important;
    color: white !important; font-weight: 700;
    box-shadow: 0 4px 14px rgba(109,40,217,0.40);
}
.cal-day.selected:hover { opacity: 0.92; }
.cal-day.blank { color: transparent; }
.cal-dot { width: 4px; height: 4px; border-radius: 50%; background: #7C3AED; }
.cal-day.selected .cal-dot { background: rgba(255,255,255,0.75); }
.cal-day.today .cal-dot { background: var(--accent); }

/* ── Day Panel ───────────────────────────────────────────────── */
.day-panel {
    flex: 1; overflow-y: auto;
    padding: 12px 18px 16px;
    border-top: 1px solid rgba(109,40,217,0.08);
}
.day-panel::-webkit-scrollbar { width: 3px; }
.day-panel::-webkit-scrollbar-thumb { background: rgba(109,40,217,0.2); border-radius: 2px; }

.day-hdr {
    font-size: 12px; font-weight: 700; color: var(--text);
    margin-bottom: 10px; display: flex; align-items: center;
    justify-content: space-between;
}
.day-date-lbl { font-size: 11px; font-weight: 600; color: var(--text3); }

/* ── Colorful Stat Chips ─────────────────────────────────────── */
.stat-row { display: flex; gap: 7px; margin-bottom: 12px; }
.stat-chip {
    flex: 1; border-radius: 11px;
    padding: 9px 6px; text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
.stat-chip.events {
    background: linear-gradient(135deg, #EDE9FE, #DDD6FE);
    border: 1px solid rgba(109,40,217,0.18);
}
.stat-chip.busy {
    background: linear-gradient(135deg, #FEF3C7, #FDE68A);
    border: 1px solid rgba(217,119,6,0.20);
}
.stat-chip.free {
    background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
    border: 1px solid rgba(5,150,105,0.20);
}
.stat-n {
    font-size: 17px; font-weight: 800; line-height: 1;
}
.stat-chip.events .stat-n { color: #6D28D9; }
.stat-chip.busy   .stat-n { color: #B45309; }
.stat-chip.free   .stat-n { color: #065F46; }
.stat-l {
    font-size: 9px; text-transform: uppercase;
    letter-spacing: 0.4px; margin-top: 2px; font-weight: 600;
}
.stat-chip.events .stat-l { color: #7C3AED; }
.stat-chip.busy   .stat-l { color: #92400E; }
.stat-chip.free   .stat-l { color: #059669; }

/* ── Event Cards ─────────────────────────────────────────────── */
.ev-card {
    border-radius: 12px;
    padding: 10px 12px; margin-bottom: 8px;
    border-left: 4px solid;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    transition: transform 0.14s, box-shadow 0.14s;
    position: relative;
}
.ev-card:hover { transform: translateX(3px); box-shadow: 0 4px 18px rgba(0,0,0,0.10); }
.ev-title { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
.ev-time  { font-size: 11px; color: #555; margin-bottom: 3px; }
.ev-note  { font-size: 10.5px; color: #777; font-style: italic; margin-top: 2px; }
.ev-badge {
    display: inline-block; padding: 2px 8px; border-radius: 6px;
    font-size: 9.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px; margin-top: 5px;
}

/* ── Free Slots ──────────────────────────────────────────────── */
.free-slot {
    background: linear-gradient(135deg, #F0FDF4, #ECFDF5);
    border: 1px dashed #6EE7B7;
    border-radius: 9px; padding: 7px 10px;
    margin-bottom: 6px; font-size: 11px;
    color: #065F46; display: flex; align-items: center; gap: 6px;
    font-weight: 500;
}
.free-dur { margin-left: auto; color: #059669; font-weight: 600; }

/* ── No events ───────────────────────────────────────────────── */
.no-events-msg {
    text-align: center; padding: 24px 8px;
    color: var(--text3); font-size: 12.5px;
}
.no-events-icon { font-size: 30px; margin-bottom: 6px; }

.section-lbl {
    font-size: 10px; font-weight: 700; color: var(--text3);
    text-transform: uppercase; letter-spacing: 0.6px; margin: 10px 0 6px;
}

.overload-warn {
    background: linear-gradient(135deg,#FEF3C7,#FDE68A);
    border: 1px solid #F59E0B; border-radius: 9px;
    padding: 8px 12px; font-size: 11px;
    color: #78350F; margin-bottom: 8px; font-weight: 600;
}

/* ── Streamlit widget overrides ──────────────────────────────── */
div[data-testid="stTextInput"] > div > div > input {
    background: rgba(255,255,255,0.95) !important;
    border: 1.5px solid rgba(109,40,217,0.18) !important;
    border-radius: 14px !important;
    padding: 11px 16px !important;
    font-size: 13.5px !important;
    font-family: var(--font) !important;
    color: var(--text) !important;
    box-shadow: 0 2px 8px rgba(109,40,217,0.06) !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(109,40,217,0.12) !important;
    outline: none !important;
}
div[data-testid="stTextInput"] > div > div > input::placeholder {
    color: var(--text3) !important; font-size: 13px !important;
}

/* Primary buttons (send, etc.) */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%) !important;
    color: white !important; border: none !important;
    border-radius: 13px !important; padding: 11px 20px !important;
    font-size: 13px !important; font-weight: 600 !important;
    font-family: var(--font) !important; cursor: pointer !important;
    transition: all 0.16s !important;
    box-shadow: 0 4px 14px rgba(109,40,217,0.30) !important;
    letter-spacing: 0.1px !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 22px rgba(109,40,217,0.42) !important;
}
div[data-testid="stButton"] > button:active { transform: translateY(0) !important; }

/* Nav buttons */
.nav-btn-wrap div[data-testid="stButton"] > button {
    background: white !important; color: var(--text2) !important;
    border: 1px solid var(--border2) !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
}
.nav-btn-wrap div[data-testid="stButton"] > button:hover {
    background: var(--accent-lt) !important;
    color: var(--accent) !important;
    border-color: rgba(109,40,217,0.25) !important;
    transform: none !important;
}

/* Delete button */
.del-btn-wrap div[data-testid="stButton"] > button {
    background: #FEF2F2 !important; color: #DC2626 !important;
    border: 1px solid #FECACA !important;
    box-shadow: none !important; padding: 5px 10px !important;
    font-size: 11px !important; border-radius: 7px !important;
    font-weight: 600 !important;
}
.del-btn-wrap div[data-testid="stButton"] > button:hover {
    background: #FEE2E2 !important; transform: none !important;
    box-shadow: none !important;
}

/* Chip buttons — colorful row of 4 */
.chip-btn-wrap:nth-of-type(1) div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#EDE9FE,#DDD6FE) !important;
    color: #6D28D9 !important;
    border: 1px solid rgba(109,40,217,0.20) !important;
    border-radius: 20px !important; padding: 5px 14px !important;
    font-size: 12px !important; font-weight: 600 !important;
    box-shadow: none !important;
}
.chip-btn-wrap:nth-of-type(2) div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#D1FAE5,#A7F3D0) !important;
    color: #065F46 !important;
    border: 1px solid rgba(5,150,105,0.20) !important;
    border-radius: 20px !important; padding: 5px 14px !important;
    font-size: 12px !important; font-weight: 600 !important;
    box-shadow: none !important;
}
.chip-btn-wrap:nth-of-type(3) div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#DBEAFE,#BFDBFE) !important;
    color: #1D4ED8 !important;
    border: 1px solid rgba(37,99,235,0.20) !important;
    border-radius: 20px !important; padding: 5px 14px !important;
    font-size: 12px !important; font-weight: 600 !important;
    box-shadow: none !important;
}
.chip-btn-wrap:nth-of-type(4) div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#FEE2E2,#FECACA) !important;
    color: #DC2626 !important;
    border: 1px solid rgba(220,38,38,0.20) !important;
    border-radius: 20px !important; padding: 5px 14px !important;
    font-size: 12px !important; font-weight: 600 !important;
    box-shadow: none !important;
}
.chip-btn-wrap div[data-testid="stButton"] > button:hover {
    filter: brightness(0.95) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.10) !important;
}

/* Spinner */
div[data-testid="stSpinner"] { display: none !important; }

/* ── Typing dots ─────────────────────────────────────────────── */
.typing-dots { display: flex; gap: 4px; padding: 4px 0; }
.typing-dots span {
    width: 6px; height: 6px;
    background: var(--accent); border-radius: 50%;
    animation: tdot 1.2s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes tdot {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
    30% { transform: translateY(-5px); opacity: 1; }
}

/* Pulse send button when input has content */
@keyframes pulse-send {
    0%, 100% { box-shadow: 0 4px 14px rgba(109,40,217,0.30); }
    50%       { box-shadow: 0 6px 22px rgba(109,40,217,0.55); }
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _prev_month():
    m, y = st.session_state.cal_month, st.session_state.cal_year
    if m == 1:
        st.session_state.cal_month = 12; st.session_state.cal_year = y - 1
    else:
        st.session_state.cal_month = m - 1

def _next_month():
    m, y = st.session_state.cal_month, st.session_state.cal_year
    if m == 12:
        st.session_state.cal_month = 1; st.session_state.cal_year = y + 1
    else:
        st.session_state.cal_month = m + 1


def _md_to_html(text: str) -> str:
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = text.replace('\n', '<br>')
    text = re.sub(r'• (.+?)(<br>|$)', r'<span style="display:block;padding-left:12px">• \1</span>', text)
    return text


def _render_message(msg: dict):
    role = msg["role"]
    is_user = role == "user"
    row_cls = "mrow user" if is_user else "mrow"
    bub_cls = "mbubble user" if is_user else "mbubble ai"
    av_cls  = "mavatar user" if is_user else "mavatar ai"
    av_icon = "U" if is_user else "✦"
    ts = msg.get("ts", "")
    st.markdown(f"""
    <div class="{row_cls}">
        <div class="{av_cls}">{av_icon}</div>
        <div>
            <div class="{bub_cls}">{_md_to_html(msg["content"])}</div>
            <div class="mts">{ts}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Layout: 3 columns ───────────────────────────────────────────────────────

col_rail, col_chat, col_cal = st.columns([1, 8, 5], gap="small")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT RAIL
# ══════════════════════════════════════════════════════════════════════════════
with col_rail:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
                height:100vh;padding:18px 0 20px;gap:6px;
                background:rgba(255,255,255,0.72);backdrop-filter:blur(20px);
                border-right:1px solid rgba(109,40,217,0.10);">
        <div class="rail-logo">✦</div>
        <div class="rail-item active" title="Chat">💬</div>
        <div class="rail-item" title="Calendar">📅</div>
        <div class="rail-item" title="Analytics">📊</div>
        <div class="rail-spacer" style="flex:1;"></div>
        <div class="rail-item" title="Settings">⚙️</div>
        <div class="rail-item" style="font-size:14px;font-weight:800;background:linear-gradient(135deg,#6D28D9,#4F46E5);color:white;box-shadow:0 2px 8px rgba(109,40,217,0.3);border-radius:12px;" title="You">A</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CHAT PANEL
# ══════════════════════════════════════════════════════════════════════════════
with col_chat:
    # Header
    st.markdown(f"""
    <div class="chat-hdr">
        <div class="aria-id">
            <div class="aria-avatar">✦</div>
            <div>
                <div class="aria-name-lbl">Aria</div>
                <div class="aria-status-lbl">
                    <span class="online-dot"></span>
                    AI Scheduling Assistant
                </div>
            </div>
        </div>
        <div class="hdr-date">📅 {format_date_short(today_str())}</div>
    </div>
    """, unsafe_allow_html=True)

    # Messages
    st.markdown('<div class="msgs-wrap" id="aria-msgs">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        _render_message(msg)
    st.markdown('</div>', unsafe_allow_html=True)

    # Input zone
    st.markdown('<div class="input-zone">', unsafe_allow_html=True)

    # Quick chips — colorful
    chips = [
        ("📅", "Schedule a meeting"),
        ("🕐", "Find free time today"),
        ("📋", "Show today's events"),
        ("⚡", "Add a deadline"),
    ]
    chip_cols = st.columns(len(chips), gap="small")
    selected_chip = None
    for i, (emoji, label) in enumerate(chips):
        with chip_cols[i]:
            st.markdown('<div class="chip-btn-wrap">', unsafe_allow_html=True)
            if st.button(f"{emoji} {label}", key=f"chip_{i}", use_container_width=True):
                selected_chip = label
            st.markdown('</div>', unsafe_allow_html=True)

    # Input + send — BUG FIX: use rotating key so field clears after submit
    input_col, btn_col = st.columns([11, 1], gap="small")
    with input_col:
        user_input = st.text_input(
            "msg",
            placeholder="Ask Aria to schedule something, find free time, or chat…",
            label_visibility="collapsed",
            key=f"chat_input_{st.session_state.input_key}",
        )
    with btn_col:
        send_clicked = st.button("↑", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Process input
    message_to_send = None
    if send_clicked and user_input.strip():
        message_to_send = user_input.strip()
    elif selected_chip:
        message_to_send = selected_chip

    if message_to_send:
        ts = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "user", "content": message_to_send, "ts": ts})
        with st.spinner(""):
            reply, action = gh.chat_with_gemini(message_to_send, st.session_state.messages[:-1])
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "ts": datetime.now().strftime("%H:%M"),
        })
        if action and action.get("intent") == "create_event" and action.get("id"):
            st.session_state.selected_date = action.get("date", today_str())

        # ── FIX: rotate key to clear the text input ──────────────────────────
        st.session_state.input_key += 1
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR PANEL
# ══════════════════════════════════════════════════════════════════════════════
with col_cal:
    year  = st.session_state.cal_year
    month = st.session_state.cal_month
    selected = st.session_state.selected_date

    month_events = cm.get_events_for_month(year, month)
    event_dates  = {e["date"] for e in month_events}
    today_d      = date.today()
    month_label  = date(year, month, 1).strftime("%B %Y")

    st.markdown(f"""
    <div class="cal-hdr">
        <div class="cal-month-row">
            <span class="cal-month-lbl">{month_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Nav row
    nav_cols = st.columns([1, 1, 2], gap="small")
    st.markdown('<div class="nav-btn-wrap">', unsafe_allow_html=True)
    with nav_cols[0]:
        if st.button("‹", key="prev_m", use_container_width=True):
            _prev_month(); st.rerun()
    with nav_cols[1]:
        if st.button("›", key="next_m", use_container_width=True):
            _next_month(); st.rerun()
    with nav_cols[2]:
        if st.button("Today", key="today_btn", use_container_width=True):
            st.session_state.cal_year = date.today().year
            st.session_state.cal_month = date.today().month
            st.session_state.selected_date = today_str()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Calendar grid header
    dow_cols = st.columns(7, gap="small")
    for i, d in enumerate(["Su","Mo","Tu","We","Th","Fr","Sa"]):
        with dow_cols[i]:
            st.markdown(f'<div class="cal-dow">{d}</div>', unsafe_allow_html=True)

    # Day cells
    import calendar as cal_mod
    cal_obj = cal_mod.monthcalendar(year, month)

    for week in cal_obj:
        wcols = st.columns(7, gap="small")
        for i, day in enumerate(week):
            with wcols[i]:
                if day == 0:
                    st.markdown('<div class="cal-day blank"></div>', unsafe_allow_html=True)
                else:
                    d_obj = date(year, month, day)
                    d_str = d_obj.isoformat()
                    is_today    = (d_obj == today_d)
                    is_selected = (d_str == selected)
                    has_events  = (d_str in event_dates)

                    cls = "cal-day"
                    if is_selected: cls += " selected"
                    elif is_today:  cls += " today"

                    dot = '<div class="cal-dot"></div>' if has_events else ""
                    st.markdown(f'<div class="{cls}">{day}{dot}</div>', unsafe_allow_html=True)
                    if st.button(str(day), key=f"day_{d_str}", use_container_width=True, help=d_str):
                        st.session_state.selected_date = d_str
                        st.rerun()

    # ── Day detail panel ──────────────────────────────────────────────────────
    sel_date   = st.session_state.selected_date
    day_evts   = cm.get_events_for_date(sel_date)
    summary    = sched.get_day_summary(sel_date)
    free_slots = sched.get_free_slots(sel_date)

    busy_h = summary["busy_minutes"] // 60
    free_h = summary["free_minutes"] // 60
    date_human = format_date_human(sel_date)

    st.markdown(f"""
    <div class="day-panel">
        <div class="day-hdr">
            <span>Schedule</span>
            <span class="day-date-lbl">{date_human}</span>
        </div>
        <div class="stat-row">
            <div class="stat-chip events">
                <div class="stat-n">{len(day_evts)}</div>
                <div class="stat-l">Events</div>
            </div>
            <div class="stat-chip busy">
                <div class="stat-n">{busy_h}h</div>
                <div class="stat-l">Busy</div>
            </div>
            <div class="stat-chip free">
                <div class="stat-n">{free_h}h</div>
                <div class="stat-l">Free</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if summary["overloaded"]:
        st.markdown('<div class="overload-warn">⚠️ This day is heavily scheduled — consider spreading out.</div>', unsafe_allow_html=True)

    # Events
    if not day_evts:
        st.markdown("""
        <div class="no-events-msg">
            <div class="no-events-icon">🌿</div>
            <div>No events scheduled</div>
            <div style="font-size:11px;margin-top:4px;color:#A1A1AA;">Ask Aria to add one!</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-lbl">Events</div>', unsafe_allow_html=True)
        for ev in day_evts:
            colors  = get_category_color(ev.get("category", "other"))
            cat_lbl = (ev.get("category") or "other").capitalize()
            note_html = f'<div class="ev-note">📝 {ev["note"]}</div>' if ev.get("note") else ""

            # Build as a single-line string — avoids markdown treating
            # indented content after blank line as a code block
            _card = (
                '<div class="ev-card" style="border-left-color:'
                + colors['border'] + ';background:' + colors['bg'] + ';">'
                + '<div class="ev-title" style="color:' + colors['text'] + ';">'
                + ev['title'] + '</div>'
                + '<div class="ev-time">🕐 '
                + format_time_12h(ev['start_time']) + ' – '
                + format_time_12h(ev['end_time']) + '</div>'
                + note_html
                + '<div><span class="ev-badge" style="background:white;color:'
                + colors['text'] + ';border:1px solid ' + colors['border'] + ';">'
                + cat_lbl + '</span></div></div>'
            )
            st.markdown(_card, unsafe_allow_html=True)

            st.markdown('<div class="del-btn-wrap">', unsafe_allow_html=True)
            if st.button(f"🗑 Delete", key=f"del_{ev['id']}", help=f"Delete {ev['title']}"):
                cm.delete_event(ev["id"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"🗑️ **{ev['title']}** has been removed.",
                    "ts": datetime.now().strftime("%H:%M"),
                })
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Free slots
    if free_slots:
        st.markdown('<div class="section-lbl">Free Slots</div>', unsafe_allow_html=True)
        for slot in free_slots[:4]:
            dur = minutes_to_hhmm(slot["duration_minutes"])
            st.markdown(f"""
            <div class="free-slot">
                ✓ {format_time_12h(slot['start'])} – {format_time_12h(slot['end'])}
                <span class="free-dur">{dur}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close day-panel


# ── Auto-scroll + transparent calendar day-buttons ───────────────────────────
st.markdown("""
<script>
(function() {
    function scrollChat() {
        const c = document.getElementById('aria-msgs');
        if (c) c.scrollTop = c.scrollHeight;
    }
    function styleCalBtns() {
        document.querySelectorAll('[data-testid="stButton"] button').forEach(btn => {
            const t = btn.innerText.trim();
            if (t.length <= 2 && !isNaN(parseInt(t)) && parseInt(t) > 0) {
                btn.style.cssText = `
                    position:absolute;opacity:0;width:100%;height:100%;
                    top:0;left:0;cursor:pointer;z-index:2;margin:0;padding:0;
                    border:none;background:none;box-shadow:none;transform:none;
                `;
                const parent = btn.closest('[data-testid="stButton"]');
                if (parent) parent.style.cssText = 'position:relative;padding:0;margin:0;';
            }
        });
    }
    setTimeout(() => { scrollChat(); styleCalBtns(); }, 150);
    const obs = new MutationObserver(() => { scrollChat(); styleCalBtns(); });
    obs.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)