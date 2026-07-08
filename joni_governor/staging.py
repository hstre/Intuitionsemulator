"""Staging - the pending/ queue, the operator sheet, and the decision mechanics.

Approval deliberately does NOT have the governor re-implement Hermes' write semantics
(memory-file sections, skill layouts - fragile to mirror). Instead: approving a proposal
moves its replayable payload to ``approved/``; when Hermes retries the SAME write (exact
tool+args match), the gate lets exactly that one through, once. The agent performs its own
write - but only after the gate blessed precisely that write. Rejecting a proposal rejects
its claim through the kernel gate: it becomes a corrected error (persona food), and the
revenant rule refuses near-identical re-proposals from then on.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from joni_governor.state import GovernorState


def payload_key(tool_name: str, args: dict) -> str:
    canon = json.dumps({"tool": tool_name, "args": args or {}},
                       sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]


def approved_dir(st: GovernorState) -> Path:
    d = st.home / "approved"
    d.mkdir(parents=True, exist_ok=True)
    return d


def rejected_dir(st: GovernorState) -> Path:
    d = st.home / "rejected"
    d.mkdir(parents=True, exist_ok=True)
    return d


def consume_approval(st: GovernorState, tool_name: str, args: dict) -> bool:
    """One-shot: if this exact write was approved, consume the ticket and let it pass."""
    f = approved_dir(st) / f"{payload_key(tool_name, args)}.json"
    if f.exists():
        f.unlink()
        return True
    return False


def pending(st: GovernorState) -> list[dict]:
    out = []
    for f in sorted(st.pending_dir.glob("*.json")):
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
            p["_file"] = f
            out.append(p)
        except Exception:  # noqa: BLE001 - a garbled payload is listed as such, never crashes
            out.append({"proposal": f.stem, "tool": "?", "args": {}, "_file": f,
                        "_error": "unlesbare Payload"})
    return out


def decide(st: GovernorState, proposal_id: str, decision: str, reason: str = "") -> str:
    """Apply the operator's decision to one staged proposal. Returns a human summary.

    ``ok``     -> claim ACTIVE, payload becomes a one-shot approval ticket;
    ``nein``   -> claim REJECTED through the gate (a corrected error; revenants refused);
    anything else raises - a decision surface must never guess.
    """
    f = st.pending_dir / f"{proposal_id}.json"
    if not f.exists():
        return f"{proposal_id}: kein offener Vorschlag"
    p = json.loads(f.read_text(encoding="utf-8"))
    if decision == "ok":
        ticket = approved_dir(st) / f"{payload_key(p['tool'], p.get('args') or {})}.json"
        ticket.write_text(json.dumps({**p, "decided": "ok", "reason": reason,
                                      "ts": time.time()},
                                     ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            st.cs.activate_claim(proposal_id)
        except Exception:  # noqa: BLE001 - ticket stands even if the status op is a no-op
            pass
        f.unlink()
        st.save()
        return (f"{proposal_id}: freigegeben - Hermine darf genau diesen Schreibvorgang "
                "einmal ausführen (Ticket liegt bereit)")
    if decision == "nein":
        (rejected_dir(st) / f.name).write_text(json.dumps(
            {**p, "decided": "nein", "reason": reason, "ts": time.time()},
            ensure_ascii=False, indent=2), encoding="utf-8")
        st.cs.reject_claim(proposal_id)
        f.unlink()
        st.save()
        return f"{proposal_id}: verworfen - wird zur Persona-Lehre; Wiedergänger werden abgewiesen"
    raise ValueError(f"Entscheidung muss 'ok' oder 'nein' sein, nicht {decision!r}")


def render_sheet(st: GovernorState) -> str:
    """The operator sheet - German, content-first (assessable, not just counted)."""
    items = pending(st)
    lines = [
        "# Hermines Vorschlags-Mappe",
        "",
        "Hermes schlägt vor - der Governor entscheidet, was als gültiger Zustand zählt.",
        "Entscheiden: `joni-governor decide <P-id> ok|nein [grund]`",
        "",
        f"_{len(items)} offene(r) Vorschlag/Vorschläge._",
        "",
    ]
    if not items:
        return "\n".join([*lines, "Gerade nichts zu entscheiden."]) + "\n"
    for p in items:
        args = p.get("args") or {}
        lines += [f"## {p.get('proposal', '?')} · {p.get('tool', '?')}."
                  f"{args.get('action', '?')} · Thema: {p.get('topic', '?')}"]
        content = str(args.get("content") or args.get("instructions")
                      or args.get("patch") or args.get("new_string") or "")
        if args.get("name") or args.get("target") or args.get("file"):
            lines.append(f"- _Ziel:_ {args.get('name') or args.get('target') or args.get('file')}")
        if content:
            lines.append(f"- _Inhalt:_ {content[:400]}")
        if p.get("_error"):
            lines.append(f"- ⚠ {p['_error']}")
        lines += ["", f"```\njoni-governor decide {p.get('proposal', '?')} ok|nein <grund>\n```",
                  ""]
    return "\n".join(lines) + "\n"
