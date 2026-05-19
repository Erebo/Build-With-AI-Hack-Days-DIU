"""
gemini_handler.py — Groq API integration with structured JSON extraction.
(Replaces the original Gemini backend; all action logic below is unchanged.)
"""

from __future__ import annotations
import json
import os
from datetime import date, timedelta

from groq import Groq
from dotenv import load_dotenv

import calendar_manager as cm
import ai_scheduler as sched
from utils import (
    clean_json_response, format_time_12h, format_date_human,
    today_str, infer_end_time,
)

load_dotenv()

# ─── Groq Setup ───────────────────────────────────────────────────────────────

_API_KEY    = os.getenv("GROQ_API_KEY", "")
_MODEL_NAME = "llama-3.3-70b-versatile"   # fast, free-tier friendly

def _client() -> Groq:
    return Groq(api_key=_API_KEY)


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aria, an elegant AI calendar and scheduling assistant.
You help users manage their schedule by understanding natural language requests.

TODAY is {today}.

Your job is to understand what the user wants and return a JSON object.
Return ONLY valid JSON — no explanation, no markdown, no extra text.

Possible intents and their JSON shapes:

1. create_event
{{
  "intent": "create_event",
  "title": "string",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "category": "meeting|study|personal|deadline|health|social|work|other",
  "note": "string or empty"
}}

2. delete_event
{{
  "intent": "delete_event",
  "event_id": number,
  "title": "string (if known)"
}}

3. query_free_time
{{
  "intent": "query_free_time",
  "date": "YYYY-MM-DD"
}}

4. query_events
{{
  "intent": "query_events",
  "date": "YYYY-MM-DD",
  "period": "day|week|month"
}}

5. update_event
{{
  "intent": "update_event",
  "event_id": number,
  "fields": {{ ... updated fields ... }}
}}

6. general_chat
{{
  "intent": "general_chat",
  "reply": "Your conversational response here"
}}

7. clarify
{{
  "intent": "clarify",
  "question": "What you need to ask the user"
}}

IMPORTANT RULES — follow these strictly:

TITLE HANDLING:
- If the user provides ANY words that could serve as a title, use them directly. Do NOT ask for a title.
- If no clear title is apparent, generate a sensible one from context (e.g. "Meeting", "Appointment", "Task").
- NEVER ask for a title. Always invent one if needed.
- Examples: "fix a meeting at 2pm fkgf" → title="fkgf meeting"; "schedule something at 3pm" → title="Appointment"

DATE HANDLING:
- Resolve relative dates: "today" = {today}, "tomorrow" = {tomorrow}, "next Monday" etc.
- If no date is mentioned, assume today: {today}.

TIME HANDLING:
- If duration is implied (e.g. "1-hour meeting") set end_time = start_time + duration.
- Default duration is 60 minutes if not specified.

CLARIFY intent:
- Only use "clarify" if BOTH the date AND time are completely missing and cannot be inferred.
- NEVER use "clarify" just because the title seems unusual or gibberish. Accept any title.
- NEVER use "clarify" to ask about meeting purpose or details — just pick "other" as category.

CATEGORY:
- Pick the most fitting category from: meeting, study, personal, deadline, health, social, work, other.
- When in doubt, use "meeting" for appointments and "other" for anything else.

OTHER:
- For greetings or off-topic messages, use "general_chat".
- Always return ONLY the JSON object. Nothing else.

Existing events context (for conflict awareness):
{events_context}
"""


def _build_system_prompt() -> str:
    today = today_str()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    start = today
    end = (date.today() + timedelta(days=7)).isoformat()
    upcoming = cm.get_events_in_range(start, end)
    if upcoming:
        lines = [
            f"- [{e['id']}] {e['title']} on {e['date']} {e['start_time']}–{e['end_time']}"
            for e in upcoming[:20]
        ]
        events_ctx = "\n".join(lines)
    else:
        events_ctx = "No upcoming events."

    return SYSTEM_PROMPT.format(
        today=today,
        tomorrow=tomorrow,
        events_context=events_ctx,
    )


# ─── Main Entry ───────────────────────────────────────────────────────────────

def chat_with_gemini(user_message: str, history: list[dict]) -> tuple[str, dict | None]:
    """
    Send user_message to Groq, parse structured JSON, execute action.
    Returns (display_message_to_user, parsed_action_dict_or_None).
    (Function name kept as chat_with_gemini so app.py needs no changes.)
    """
    if not _API_KEY:
        return (
            "⚠️ **API key not configured.** Please add your `GROQ_API_KEY` to the `.env` file and restart.",
            None,
        )

    system = _build_system_prompt()

    # Build OpenAI-compatible message list for Groq
    messages: list[dict] = [{"role": "system", "content": system}]
    for msg in history[-12:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = _client().chat.completions.create(
            model=_MODEL_NAME,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Groq error: {str(e)}", None

    # Parse JSON
    try:
        cleaned = clean_json_response(raw)
        action = json.loads(cleaned)
    except json.JSONDecodeError:
        return raw, {"intent": "general_chat", "reply": raw}

    reply, enriched = _execute_action(action)
    return reply, enriched


# ─── Action Executor ──────────────────────────────────────────────────────────

def _execute_action(action: dict) -> tuple[str, dict]:
    intent = action.get("intent", "general_chat")

    # ── create_event ──────────────────────────────────────────────────────────
    if intent == "create_event":
        title      = action.get("title") or "Untitled"
        date_str   = action.get("date", today_str())
        start_time = action.get("start_time", "09:00")
        end_time   = action.get("end_time") or infer_end_time(start_time, 60)
        category   = action.get("category", "other")
        note       = action.get("note", "")

        # Conflict check
        conflicts = sched.has_conflict(date_str, start_time, end_time)
        if conflicts:
            conflict_names = ", ".join(
                f"**{c['title']}** ({format_time_12h(c['start_time'])})" for c in conflicts
            )
            suggestion = sched.suggest_next_free_slot(date_str, 60)
            suggest_text = ""
            if suggestion:
                suggest_text = (
                    f"\n\n💡 Next available slot: "
                    f"**{format_time_12h(suggestion['start'])} – {format_time_12h(suggestion['end'])}**"
                )
            reply = (
                f"⚠️ **Conflict detected!** You already have {conflict_names} at that time.{suggest_text}\n\n"
                f"Would you like to reschedule, or should I book it at the suggested time?"
            )
            action["_conflict"] = conflicts
            return reply, action

        event_id = cm.add_event(title, date_str, start_time, end_time, category, note)
        action["id"] = event_id

        date_human = format_date_human(date_str)
        reply = (
            f"✅ **{title}** has been added to your calendar!\n\n"
            f"📅 **{date_human}**  "
            f"🕐 {format_time_12h(start_time)} – {format_time_12h(end_time)}"
        )
        if note:
            reply += f"\n📝 *{note}*"
        return reply, action

    # ── delete_event ──────────────────────────────────────────────────────────
    elif intent == "delete_event":
        event_id = action.get("event_id")
        if event_id:
            ev = cm.get_event_by_id(event_id)
            if ev and cm.delete_event(event_id):
                return f"🗑️ **{ev['title']}** has been removed from your calendar.", action
        return "I couldn't find that event. Could you be more specific?", action

    # ── query_free_time ───────────────────────────────────────────────────────
    elif intent == "query_free_time":
        date_str = action.get("date", today_str())
        text = sched.free_slots_text(date_str)
        summary = sched.get_day_summary(date_str)
        date_human = format_date_human(date_str)
        reply = f"📅 **{date_human}**\n\n{text}"
        if summary["overloaded"]:
            reply += "\n\n⚠️ This day is heavily scheduled — consider spreading events out."
        return reply, action

    # ── query_events ──────────────────────────────────────────────────────────
    elif intent == "query_events":
        date_str = action.get("date", today_str())
        events   = cm.get_events_for_date(date_str)
        date_human = format_date_human(date_str)

        if not events:
            return f"📅 **{date_human}** — No events scheduled.", action

        lines = [f"📅 **{date_human}** — {len(events)} event(s):\n"]
        for e in events:
            lines.append(
                f"• **{e['title']}** · {format_time_12h(e['start_time'])} – {format_time_12h(e['end_time'])}"
                + (f" · *{e['note']}*" if e.get("note") else "")
            )
        return "\n".join(lines), action

    # ── update_event ──────────────────────────────────────────────────────────
    elif intent == "update_event":
        event_id = action.get("event_id")
        fields   = action.get("fields", {})
        if event_id and fields:
            ev = cm.get_event_by_id(event_id)
            if ev and cm.update_event(event_id, **fields):
                return f"✏️ **{ev['title']}** has been updated.", action
        return "I couldn't update that event. Could you clarify?", action

    # ── clarify ───────────────────────────────────────────────────────────────
    elif intent == "clarify":
        return action.get("question", "Could you please provide more details?"), action

    # ── general_chat ──────────────────────────────────────────────────────────
    else:
        return action.get("reply", "How can I help you today?"), action