"""The deterministic gate policy - operator-owned, file-based, fail-safe defaults.

``policy.yaml`` (in ``JONI_GOVERNOR_HOME``) is read fresh per decision; absent or unreadable
means DEFAULTS, which are the strict MVP rules: every memory/skill write stages, nothing
auto-approves. Loosening is an explicit operator act, tightening never requires one.

Parsed with a deliberately tiny reader (flat ``section.key: value`` YAML subset) so the
governor keeps zero third-party dependencies - the same reason the kernel is stdlib-only.
"""

from __future__ import annotations

from pathlib import Path

# Tools whose calls carry persistent self-modification - the governor's business. Everything
# else passes ungated (rule 3: tools the policy allows). Names per Hermes v0.18 tool schema.
GATED_TOOLS = ("memory", "skill_manage")

DEFAULTS = {
    # every gated write stages for a decision; nothing silently persists
    "memory.auto_allow_actions": (),           # e.g. () or ("add",) if the operator loosens
    "skills.auto_allow_actions": (),
    # a proposal near-duplicating an already-REJECTED one is refused outright (revenant rule);
    # it may be re-staged only after the operator clears the original from the record
    "revenant.auto_reject": True,
    # fail-closed wording shown to the model when the kernel is unavailable
    "fail_closed": True,
}


def _parse_flat_yaml(text: str) -> dict:
    """`section:\n  key: value` and `section.key: value` - strings, bools, comma lists."""
    out: dict = {}
    section = ""
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        val = val.strip()
        if not _:
            continue
        if indent == 0 and not val:
            section = key.strip()
            continue
        full = f"{section}.{key.strip()}" if (indent > 0 and section) else key.strip()
        if val.lower() in ("true", "yes", "on"):
            out[full] = True
        elif val.lower() in ("false", "no", "off"):
            out[full] = False
        elif "," in val:
            out[full] = tuple(v.strip() for v in val.split(",") if v.strip())
        elif val:
            out[full] = val
    return out


def load_policy(path: Path) -> dict:
    policy = dict(DEFAULTS)
    try:
        if path.exists():
            parsed = _parse_flat_yaml(path.read_text(encoding="utf-8"))
            for k in DEFAULTS:
                if k in parsed:
                    v = parsed[k]
                    if k.endswith("auto_allow_actions") and isinstance(v, str):
                        v = (v,)
                    policy[k] = v
    except Exception:  # noqa: BLE001 - an unreadable policy means DEFAULTS (strict), never a crash
        return dict(DEFAULTS)
    return policy
