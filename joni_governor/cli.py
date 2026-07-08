"""Operator CLI - the Mappe pattern, on the laptop.

    joni-governor status              counts + liveness one-liner
    joni-governor sheet               the proposal sheet (content-first, assessable)
    joni-governor decide P-3 ok grund approve (one-shot ticket) or reject ('nein')
    joni-governor liveness            is the gate actually firing when Hermes runs?
"""

from __future__ import annotations

import sys

from joni_governor import audit, staging
from joni_governor.state import GovernorState


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "status"
    st = GovernorState()
    if cmd == "status":
        pend = staging.pending(st)
        live = audit.liveness(st)
        claims = st.cs.core.all(__import__("desi_layer9").ObjectType.CLAIM)
        by = {}
        for c in claims:
            by[c.status.value] = by.get(c.status.value, 0) + 1
        print(f"Vorschläge offen: {len(pend)} · Kernel-Claims: {dict(sorted(by.items()))}")
        print(f"Liveness: {live['verdict']}")
        return 0
    if cmd == "sheet":
        print(staging.render_sheet(st), end="")
        return 0
    if cmd == "decide":
        if len(args) < 3:
            print("usage: joni-governor decide <P-id> ok|nein [grund]", file=sys.stderr)
            return 2
        print(staging.decide(st, args[1], args[2], " ".join(args[3:])))
        return 0
    if cmd == "liveness":
        for k, v in audit.liveness(st).items():
            print(f"{k}: {v}")
        return 0
    print(__doc__)
    return 0 if cmd in ("help", "-h", "--help") else 2


if __name__ == "__main__":
    raise SystemExit(main())
