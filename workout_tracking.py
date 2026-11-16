"""Server-side workout ledger and deterministic progression for VIRTUS FIT.

All database calls use the server-side Supabase client. Do not import this module
from the public Mini App; browser writes require a separately authenticated API.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from statistics import median
from typing import Any


MUSCLE_GROUPS = {"chest", "back", "legs", "arms", "shoulders", "core"}


def canonical_muscle_group(value: Any) -> str:
    """Map common RU/UA/EN labels to the six supported muscle groups."""
    raw = str(value or "").strip().casefold()
    aliases = {
        "chest": ("chest", "груд", "грудн"),
        "back": ("back", "спин"),
        "legs": ("legs", "leg", "ног", "квадриц", "бицепс бедра"),
        "arms": ("arms", "arm", "рук", "бицеп", "трицеп"),
        "shoulders": ("shoulders", "shoulder", "плеч", "дельт"),
        "core": ("core", "abs", "пресс", "кор", "живот"),
    }
    for group, fragments in aliases.items():
        if any(fragment in raw for fragment in fragments):
            return group
    return "core"


def canonical_exercise_key(sys_id: Any, exercise_name: Any) -> str:
    """Prefer stable asset sys_id; fall back to a Unicode-safe normalized name."""
    candidate = str(sys_id or "").strip().casefold()
    if not candidate:
        candidate = str(exercise_name or "").strip().casefold()
    candidate = re.sub(r"[^\w]+", "_", candidate, flags=re.UNICODE).strip("_")
    return candidate[:120] or "unknown_exercise"


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return default
        if isinstance(value, (int, float)):
            return max(0, int(value))
        match = re.search(r"-?\d+", str(value))
        return max(0, int(match.group())) if match else default
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(str(value).replace(",", "."))
        if not math.isfinite(parsed) or parsed < 0:
            return default
        return round(parsed, 2)
    except (TypeError, ValueError):
        return default


def create_workout_session(
    db: Any,
    user_id: int,
    source: str = "bot",
    program_id: int | None = None,
) -> str:
    """Create a session and return its UUID string."""
    if source not in {"bot", "miniapp"}:
        raise ValueError("Unsupported workout source")
    payload = {"user_id": int(user_id), "source": source, "status": "active"}
    if program_id is not None:
        payload["program_id"] = int(program_id)
    result = (
        db.table("workout_sessions")
        .insert(payload)
        .select("id")
        .single()
        .execute()
    )
    if not result.data or not result.data.get("id"):
        raise RuntimeError("Supabase did not return the workout session id")
    return str(result.data["id"])


def record_completed_set(
    db: Any,
    *,
    session_id: str,
    exercise_order: int,
    set_index: int,
    exercise_key: str,
    exercise_name: str,
    muscle_group: Any,
    reps: Any,
    weight_kg: Any,
    rir: int | None = None,
    set_type: str = "working",
) -> bool:
    """Persist one actually completed set. Return False for an already-recorded set."""
    safe_reps = _as_int(reps)
    safe_weight = _as_float(weight_kg)
    if safe_reps <= 0:
        raise ValueError("Completed set must contain at least one repetition")
    if set_type not in {"warmup", "working", "drop"}:
        raise ValueError("Invalid set_type")
    if rir is not None and not 0 <= int(rir) <= 5:
        raise ValueError("RIR must be between 0 and 5")

    payload = {
        "session_id": str(session_id),
        "exercise_order": int(exercise_order),
        "set_index": int(set_index),
        "exercise_key": canonical_exercise_key(exercise_key, exercise_name),
        "exercise_name": str(exercise_name or "Exercise").strip()[:160],
        "muscle_group": canonical_muscle_group(muscle_group),
        "set_type": set_type,
        "reps": safe_reps,
        "weight_kg": safe_weight,
        "rir": rir,
        "completed": True,
    }
    try:
        db.table("workout_sets").insert(payload).execute()
        return True
    except Exception:
        # The unique constraint is the final guard against Telegram double-clicks.
        existing = (
            db.table("workout_sets")
            .select("id")
            .eq("session_id", str(session_id))
            .eq("exercise_order", int(exercise_order))
            .eq("set_index", int(set_index))
            .limit(1)
            .execute()
        )
        if existing.data:
            return False
        raise


def calculate_progression(
    *,
    working_sets: list[dict[str, Any]],
    previous_streak: int = 0,
    increment_kg: float = 2.5,
    target_min: int = 8,
    target_max: int = 12,
) -> dict[str, Any]:
    """Pure double-progression rule; returns the next load and failure streak."""
    valid = [
        item for item in working_sets
        if item.get("completed") is True
        and item.get("set_type", "working") == "working"
        and _as_int(item.get("reps")) > 0
    ]
    if not valid:
        return {"next_weight": None, "failed_streak": previous_streak, "decision": "no_sets"}

    weights = [_as_float(item.get("weight_kg")) for item in valid]
    current_weight = float(median(weights))
    step = max(0.5, _as_float(increment_kg, 2.5))
    reps_values = [_as_int(item.get("reps")) for item in valid]

    # Bodyweight/no-external-load exercises need a separate rep/band progression.
    if current_weight <= 0:
        return {"next_weight": 0.0, "failed_streak": 0, "decision": "bodyweight"}

    if all(reps >= target_max for reps in reps_values):
        return {
            "next_weight": round(current_weight + step, 2),
            "failed_streak": 0,
            "decision": "increase",
        }

    failed_count = sum(reps < target_min for reps in reps_values)
    if failed_count >= math.ceil(len(reps_values) / 2):
        streak = int(previous_streak) + 1
        if streak >= 2:
            return {
                "next_weight": round(max(0.0, current_weight - step), 2),
                "failed_streak": 0,
                "decision": "decrease",
            }
        return {
            "next_weight": current_weight,
            "failed_streak": streak,
            "decision": "hold_after_first_failure",
        }

    return {"next_weight": current_weight, "failed_streak": 0, "decision": "hold"}


def _update_exercise_progression(
    db: Any,
    *,
    user_id: int,
    session_id: str,
    exercise_key: str,
    exercise_name: str,
    muscle_group: str,
    working_sets: list[dict[str, Any]],
) -> float | None:
    existing_result = (
        db.table("exercise_progression")
        .select("*")
        .eq("user_id", int(user_id))
        .eq("exercise_key", exercise_key)
        .limit(1)
        .execute()
    )
    existing = existing_result.data[0] if existing_result.data else {}
    decision = calculate_progression(
        working_sets=working_sets,
        previous_streak=_as_int(existing.get("failed_sessions_streak")),
        increment_kg=_as_float(existing.get("increment_kg"), 2.5) or 2.5,
        target_min=_as_int(existing.get("target_reps_min"), 8) or 8,
        target_max=_as_int(existing.get("target_reps_max"), 12) or 12,
    )
    if decision["next_weight"] is None:
        return None

    valid = [
        item for item in working_sets
        if item.get("completed") is True
        and item.get("set_type", "working") == "working"
    ]
    last_weight = (
        float(median([_as_float(item.get("weight_kg")) for item in valid]))
        if valid else None
    )
    payload = {
        "user_id": int(user_id),
        "exercise_key": exercise_key,
        "exercise_name": str(exercise_name)[:160],
        "muscle_group": canonical_muscle_group(muscle_group),
        "last_session_id": str(session_id),
        "last_weight": last_weight,
        "target_reps_min": _as_int(existing.get("target_reps_min"), 8) or 8,
        "target_reps_max": _as_int(existing.get("target_reps_max"), 12) or 12,
        "increment_kg": _as_float(existing.get("increment_kg"), 2.5) or 2.5,
        "next_suggested_weight": decision["next_weight"],
        "failed_sessions_streak": decision["failed_streak"],
        "updated_at": "now()",
    }
    # Omit updated_at: PostgREST expects a timestamp value, and the DB can default it.
    payload.pop("updated_at")
    db.table("exercise_progression").upsert(
        payload, on_conflict="user_id,exercise_key"
    ).execute()
    return float(decision["next_weight"])


def get_suggested_weight(db: Any, user_id: int, exercise_key: str) -> float | None:
    result = (
        db.table("exercise_progression")
        .select("next_suggested_weight")
        .eq("user_id", int(user_id))
        .eq("exercise_key", exercise_key)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    value = result.data[0].get("next_suggested_weight")
    return None if value is None else _as_float(value)


def finalize_workout_session(
    db: Any,
    *,
    session_id: str,
    user_id: int,
    completed: bool,
) -> dict[str, Any]:
    """Finalize one session from recorded facts and maintain legacy dashboard aggregates."""
    session_result = (
        db.table("workout_sessions")
        .select("id,status")
        .eq("id", str(session_id))
        .eq("user_id", int(user_id))
        .limit(1)
        .execute()
    )
    if not session_result.data:
        raise RuntimeError("Workout session not found for this user")
    if session_result.data[0].get("status") != "active":
        return {"sets": [], "total_reps": 0, "calories": 0, "already_finalized": True}

    set_result = (
        db.table("workout_sets")
        .select("*")
        .eq("session_id", str(session_id))
        .eq("completed", True)
        .order("exercise_order")
        .order("set_index")
        .execute()
    )
    rows = set_result.data or []
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    names: dict[tuple[int, str], str] = {}
    muscles: dict[tuple[int, str], str] = {}
    for row in rows:
        key = (int(row["exercise_order"]), str(row["exercise_key"]))
        grouped[key].append(row)
        names[key] = str(row.get("exercise_name") or row["exercise_key"])
        muscles[key] = canonical_muscle_group(row.get("muscle_group"))

    total_reps = sum(_as_int(row.get("reps")) for row in rows)
    total_calories = int(round(total_reps * 0.5))
    suggestions: dict[str, float] = {}

    for (exercise_order, exercise_key), exercise_rows in grouped.items():
        working = [r for r in exercise_rows if r.get("set_type") == "working"]
        reps_sum = sum(_as_int(r.get("reps")) for r in exercise_rows)
        weights = [_as_float(r.get("weight_kg")) for r in exercise_rows]
        total_volume = sum(
            _as_float(r.get("weight_kg")) * _as_int(r.get("reps"))
            for r in exercise_rows
        )
        average_weight = (
            total_volume / reps_sum if reps_sum > 0
            else (sum(weights) / len(weights) if weights else 0.0)
        )

        # Keep the legacy aggregate for existing Dashboard queries.
        db.table("workouts_strength").insert({
            "user_id": int(user_id),
            "exercise_name": names[(exercise_order, exercise_key)],
            "sets": len(exercise_rows),
            "reps": int(round(reps_sum / max(1, len(exercise_rows)))),
            "weight_kg": round(average_weight, 2),
            "muscle_group": muscles[(exercise_order, exercise_key)],
            "calories_burned": int(round(sum(_as_int(r.get("reps")) for r in exercise_rows) * 0.5)),
        }).execute()

        if completed and working:
            suggestion = _update_exercise_progression(
                db,
                user_id=user_id,
                session_id=session_id,
                exercise_key=exercise_key,
                exercise_name=names[(exercise_order, exercise_key)],
                muscle_group=muscles[(exercise_order, exercise_key)],
                working_sets=working,
            )
            if suggestion is not None:
                suggestions[exercise_key] = suggestion

    db.table("workout_sessions").update({
        "status": "completed" if completed else "abandoned",
        "finished_at": "now()",
    }).eq("id", str(session_id)).eq("user_id", int(user_id)).execute()

    return {
        "sets": rows,
        "total_reps": total_reps,
        "calories": total_calories,
        "suggestions": suggestions,
        "already_finalized": False,
    }
