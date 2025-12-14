"""Custom reducer functions for LangGraph state management."""

from typing import Any

from src.agents.state.models import AgentNote, AgentScratchpad


def _to_dict(obj: Any) -> dict:
    """Convert Pydantic model or dict to dict."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return dict(obj)


def _get_note_key(note: Any) -> tuple:
    """Get a unique key for a note (works with dicts and objects)."""
    if isinstance(note, dict):
        return (note.get("content"), note.get("timestamp"))
    return (note.content, note.timestamp)


def merge_scratchpads(
    existing: dict[str, Any] | None,
    new: dict[str, Any] | None,
) -> dict[str, dict]:
    """
    Custom reducer for merging agent scratchpads.

    This ensures that when multiple agents write to the state,
    their scratchpads are merged correctly rather than overwritten.
    Works with both dicts and Pydantic models, outputs dicts.
    """
    if existing is None:
        existing = {}
    if new is None:
        return existing

    # Convert existing values to dicts
    result = {}
    for agent_id, value in existing.items():
        result[agent_id] = _to_dict(value)

    for agent_id, scratchpad_data in new.items():
        scratchpad = _to_dict(scratchpad_data)

        if agent_id in result:
            # Merge notes from both scratchpads
            existing_scratchpad = result[agent_id]
            existing_notes = existing_scratchpad.get("notes", [])
            existing_note_keys = {_get_note_key(n) for n in existing_notes}

            new_notes = scratchpad.get("notes", [])
            for note in new_notes:
                note_dict = _to_dict(note)
                if _get_note_key(note_dict) not in existing_note_keys:
                    existing_notes.append(note_dict)

            # Update last action and iteration count
            if scratchpad.get("last_action"):
                existing_scratchpad["last_action"] = scratchpad["last_action"]
            existing_scratchpad["iteration_contributions"] = (
                existing_scratchpad.get("iteration_contributions", 0) + 1
            )
        else:
            result[agent_id] = scratchpad

    return result


def append_notes(
    existing: list[Any] | None,
    new: list[Any] | None,
) -> list[dict]:
    """
    Reducer for appending notes to a list.
    Ensures no duplicates based on content and timestamp.
    Works with both dicts and Pydantic models, outputs dicts.
    """
    if existing is None:
        existing = []
    if new is None:
        return existing

    # Convert existing items to dicts
    result = [_to_dict(item) for item in existing]
    existing_keys = {_get_note_key(n) for n in result}

    for note_data in new:
        note_dict = _to_dict(note_data)
        note_key = _get_note_key(note_dict)

        if note_key not in existing_keys:
            result.append(note_dict)
            existing_keys.add(note_key)

    return result


def merge_quality_metrics(existing: dict | None, new: dict | None) -> dict:
    """
    Reducer for merging quality metrics.
    Takes the latest values while preserving history.
    """
    if existing is None:
        return new or {}
    if new is None:
        return existing

    result = existing.copy()

    # Deep merge for nested structures
    for key, value in new.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = {**result[key], **value}
        else:
            result[key] = value

    return result
