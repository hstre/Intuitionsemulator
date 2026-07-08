"""The gate - every persistent self-modification becomes a kernel proposal, before it persists.

Called by the Hermes plugin's ``pre_tool_call`` hook. Verdicts:

  * ``allow``  - not the governor's business (ungated tool) or an explicit auto-allow rule;
  * ``stage``  - the write is BLOCKED for now; it lives on as a CANDIDATE claim in the
    governor's core plus a replayable payload in ``pending/`` - the operator (or an auto rule
    in a later cycle) decides; the block message tells the model its proposal id;
  * ``reject`` - refused outright: a revenant of an already-rejected proposal (the corrected
    error must not re-enter unexamined), or the kernel is unavailable (fail-closed).

The claim TEXT is a deterministic, human-assessable rendering of the attempted write - the
operator sheet shows what would change, not that "something" would.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from joni_governor import policy as policy_mod
from joni_governor.state import GovernorState


@dataclass(frozen=True)
class Verdict:
    action: str                 # "allow" | "stage" | "reject"
    reason: str = ""
    proposal_id: str = ""       # the CANDIDATE claim id when staged

    @property
    def blocked(self) -> bool:
        return self.action in ("stage", "reject")


def _render_proposal(tool_name: str, args: dict) -> tuple[str, str]:
    """(topic, text) for the kernel claim - deterministic, content-first, bounded."""
    args = args or {}
    action = str(args.get("action", "?"))
    if tool_name == "memory":
        target = str(args.get("target") or args.get("file") or "memory")
        content = str(args.get("content") or args.get("new_string") or "")[:600]
        return (f"memory:{target}",
                f"[memory {action} -> {target}] {content}".strip())
    name = str(args.get("name", "?"))
    content = str(args.get("content") or args.get("instructions")
                  or args.get("patch") or "")[:600]
    return (f"skill:{name}", f"[skill_manage {action} -> {name}] {content}".strip())


def decide_tool_call(tool_name: str, args: dict, *, state: GovernorState | None = None) -> Verdict:
    """The single decision point. Deterministic; never raises (a gate that crashes is a gate
    that silently opens - errors become fail-closed rejections instead)."""
    if tool_name not in policy_mod.GATED_TOOLS:
        return Verdict("allow")
    try:
        st = state or GovernorState()
        pol = policy_mod.load_policy(st.policy_path)
        args = args or {}
        action = str(args.get("action", ""))

        allow_key = ("memory.auto_allow_actions" if tool_name == "memory"
                     else "skills.auto_allow_actions")
        if action and action in tuple(pol.get(allow_key) or ()):
            return Verdict("allow", reason=f"policy auto-allow: {tool_name}.{action}")

        # A one-shot approval ticket: the operator blessed EXACTLY this write - it passes
        # once, then the ticket is consumed (staging.decide 'ok' issues it).
        from joni_governor import staging
        if staging.consume_approval(st, tool_name, args):
            return Verdict("allow", reason="einmalige Freigabe des Governors eingelöst")

        # idempotent: retrying a write that is ALREADY pending re-points at the same
        # proposal instead of minting a twin per retry.
        pkey = staging.payload_key(tool_name, args)
        for p in staging.pending(st):
            if staging.payload_key(p.get("tool", ""), p.get("args") or {}) == pkey:
                return Verdict(
                    "stage", proposal_id=str(p.get("proposal", "")),
                    reason=(f"Bereits als Vorschlag {p.get('proposal')} eingereicht - die "
                            "Entscheidung steht noch aus."))

        topic, text = _render_proposal(tool_name, args)

        # Revenant rule: a proposal near-duplicating one already REJECTED does not re-enter
        # unexamined - the corrected error binds the future (Persona v3, inherited).
        twin = st.cs.corrected_twin(text)
        if twin and pol.get("revenant.auto_reject", True):
            return Verdict(
                "reject",
                reason=(f"Wiedergänger von {twin}: dieser Vorschlag wurde bereits verworfen. "
                        "Er wird nicht erneut vorgelegt; wenn du ihn für richtig hältst, "
                        "begründe NEU, was sich seit der Verwerfung geändert hat."))

        # Stage: mint the CANDIDATE claim + persist the replayable payload.
        cid = st.cs.hypothesize(text, topic, origin=f"hermes:{tool_name}")
        payload = {"proposal": cid, "tool": tool_name, "args": args, "topic": topic}
        (st.pending_dir / f"{cid}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        st.save()
        return Verdict(
            "stage", proposal_id=cid,
            reason=(f"Als Vorschlag {cid} eingereicht - persistente Selbstveränderung wird vom "
                    "Governor entschieden, nicht direkt geschrieben. Arbeite ohne die "
                    "Speicherung weiter; nach Freigabe darf genau dieser Schreibvorgang "
                    "einmal wiederholt werden."))
    except Exception as exc:  # noqa: BLE001 - fail-CLOSED: a broken gate never waves through
        return Verdict(
            "reject",
            reason=(f"Governor nicht verfügbar ({type(exc).__name__}) - persistente "
                    "Selbstveränderung ist ohne epistemisches Gate gesperrt (fail-closed)."))
