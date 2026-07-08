"""joni-governor Hermes plugin - the pre-persistence gate.

Rides the generic ``pre_tool_call`` hook (which Hermes fires for EVERY tool, including the
special-cased ``memory`` and ``skill_manage``) because Hermes has no dedicated memory/skill
write hook. Returning ``{"action": "block", "message": ...}`` vetoes the call before any
file is written; the message carries the proposal id so the model knows its write became a
pending proposal rather than vanishing.

Every invocation stamps a heartbeat: both built-in Hermes write gates fail OPEN, so the
governor must be able to prove it was actually running (``joni-governor liveness``).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _governor():
    from joni_governor import audit, gate
    from joni_governor.state import GovernorState
    return gate, audit, GovernorState


def _on_pre_tool_call(tool_name: str = "", args: Any = None,
                      **_: Any) -> Optional[Dict[str, str]]:
    try:
        gate, audit, GovernorState = _governor()
        st = GovernorState()
        audit.beat(st, source=f"pre_tool_call:{tool_name}")
        verdict = gate.decide_tool_call(tool_name, args or {}, state=st)
    except Exception as exc:  # noqa: BLE001 - fail-CLOSED for gated tools, silent for the rest
        if tool_name in ("memory", "skill_manage"):
            return {"action": "block",
                    "message": f"joni-governor unavailable ({type(exc).__name__}) - "
                               "persistent self-modification is locked without the "
                               "epistemic gate (fail-closed)."}
        return None
    if verdict.blocked:
        return {"action": "block", "message": verdict.reason}
    return None


def _on_session_start(**_: Any) -> None:
    try:
        _gate, audit, GovernorState = _governor()
        audit.beat(GovernorState(), source="session_start")
    except Exception:  # noqa: BLE001 - a heartbeat must never break a session
        logger.debug("joni-governor heartbeat failed on session start", exc_info=True)


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_hook("on_session_start", _on_session_start)
