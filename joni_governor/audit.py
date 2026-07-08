"""Liveness - a guard that silently is not running is worse than none (Joni lesson, metric 9).

The plugin stamps a heartbeat on every hook invocation and session start. The CLI's
``liveness`` check compares that stamp against Hermes' own session activity: sessions that
ran without the governor firing mean the plugin is not loaded - the single most dangerous
silent state this system can be in, because both built-in Hermes write gates fail OPEN.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from joni_governor.state import GovernorState


def beat(st: GovernorState, *, source: str) -> None:
    try:
        st.heartbeat_path.write_text(json.dumps(
            {"ts": time.time(), "source": source}), encoding="utf-8")
    except Exception:  # noqa: BLE001 - the heartbeat must never break a tool call
        pass


def last_beat(st: GovernorState) -> float | None:
    try:
        return float(json.loads(st.heartbeat_path.read_text(encoding="utf-8"))["ts"])
    except Exception:  # noqa: BLE001
        return None


def liveness(st: GovernorState, *, hermes_home: Path | None = None) -> dict:
    """Compare the governor's last heartbeat with Hermes' session store mtime."""
    hb = last_beat(st)
    hh = hermes_home or Path("~/.hermes").expanduser()
    state_db = hh / "state.db"
    hermes_active = state_db.stat().st_mtime if state_db.exists() else None
    verdict = "ok"
    if hermes_active and (hb is None or hermes_active - hb > 3600):
        verdict = "ALARM: Hermes lief, ohne dass das Gate feuerte - Plugin nicht geladen?"
    elif hb is None:
        verdict = "noch kein Herzschlag (Hermine lief noch nicht mit Governor)"
    return {"heartbeat": hb, "hermes_state_mtime": hermes_active, "verdict": verdict}
