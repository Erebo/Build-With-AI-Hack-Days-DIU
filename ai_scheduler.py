"""
ai_scheduler.py — Conflict detection, free-time calculation, smart suggestions.
"""

from __future__ import annotations
from typing import Optional
import calendar_manager as cm
from utils import time_to_minutes, minutes_to_time, format_time_12h, minutes_to_hhmm

# Work day bounds (minutes from midnight)
DAY_START = 8 * 60    # 08:00
DAY_END   = 22 * 60   # 22:00


# ─── Conflict Detection ───────────────────────────────────────────────────────

def has_conflict(date_str: str, start_time: str, end_time: str,
                 exclude_id: int | None = None) -> list[dict]:
    """Return list of events that overlap with the proposed slot."""
    new_start = time_to_minutes(start_time)
    new_end   = time_to_minutes(end_time)
    events = cm.get_events_for_date(date_str)
    conflicts = []
    for ev in events:
        if exclude_id and ev["id"] == exclude_id:
            continue
        es = time_to_minutes(ev["start_time"])
        ee = time_to_minutes(ev["end_time"])
        # Overlap when intervals are not strictly separated
        if new_start < ee and new_end > es:
            conflicts.append(ev)
    return conflicts


# ─── Free Slots ───────────────────────────────────────────────────────────────

def get_free_slots(date_str: str, duration_minutes: int = 60) -> list[dict]:
    """Return free slots ≥ duration_minutes within DAY_START–DAY_END."""
    events = cm.get_events_for_date(date_str)
    busy = sorted(
        [(time_to_minutes(e["start_time"]), time_to_minutes(e["end_time"]))
         for e in events]
    )

    # Merge overlapping busy intervals
    merged: list[tuple[int, int]] = []
    for s, e in busy:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Find gaps
    free = []
    cursor = DAY_START
    for s, e in merged:
        if s > cursor:
            gap = s - cursor
            if gap >= duration_minutes:
                free.append({
                    "start": minutes_to_time(cursor),
                    "end":   minutes_to_time(s),
                    "duration_minutes": gap,
                })
        cursor = max(cursor, e)

    if DAY_END > cursor:
        gap = DAY_END - cursor
        if gap >= duration_minutes:
            free.append({
                "start": minutes_to_time(cursor),
                "end":   minutes_to_time(DAY_END),
                "duration_minutes": gap,
            })

    return free


def suggest_next_free_slot(date_str: str, duration_minutes: int = 60) -> dict | None:
    """Return the first free slot that fits the desired duration."""
    slots = get_free_slots(date_str, duration_minutes)
    return slots[0] if slots else None


# ─── Day Summary ─────────────────────────────────────────────────────────────

def get_day_summary(date_str: str) -> dict:
    events = cm.get_events_for_date(date_str)
    total_busy = sum(
        time_to_minutes(e["end_time"]) - time_to_minutes(e["start_time"])
        for e in events
    )
    total_day   = DAY_END - DAY_START
    total_free  = max(0, total_day - total_busy)
    free_slots  = get_free_slots(date_str)

    overloaded  = total_busy >= total_day * 0.8

    return {
        "event_count":    len(events),
        "busy_minutes":   total_busy,
        "free_minutes":   total_free,
        "free_slots":     free_slots,
        "overloaded":     overloaded,
        "total_day_mins": total_day,
    }


# ─── Human-readable Helpers ───────────────────────────────────────────────────

def free_slots_text(date_str: str) -> str:
    slots = get_free_slots(date_str)
    if not slots:
        return "You have no free time on that day during working hours (8 AM – 10 PM)."
    lines = [
        f"• {format_time_12h(s['start'])} – {format_time_12h(s['end'])}  ({minutes_to_hhmm(s['duration_minutes'])})"
        for s in slots
    ]
    return "You are free:\n" + "\n".join(lines)


def conflict_text(conflicts: list[dict]) -> str:
    if not conflicts:
        return ""
    lines = []
    for c in conflicts:
        lines.append(
            f"**{c['title']}** ({format_time_12h(c['start_time'])} – {format_time_12h(c['end_time'])})"
        )
    return "⚠️ Conflict with: " + ", ".join(lines)