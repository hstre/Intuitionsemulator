"""The governor's own epistemic core - a ``desi_layer9`` kernel, chunk-persisted.

This is deliberately NOT a new store: it is the same kernel the Joni testbed hardened
(append-only journal, hash chain, sealed on-disk chunks, transition tables, taint). The
governor holds Hermine's *epistemic* state - proposals, verdicts, corrected errors - while
Hermes holds her *operational* state (sessions, config). The two never share a write path.
"""

from __future__ import annotations

import os
from pathlib import Path

import desi_layer9 as l9
from desi_layer9 import persistence
from joni.autonomy.core_state import CoreState


def governor_home() -> Path:
    return Path(os.getenv("JONI_GOVERNOR_HOME", "~/.joni-governor")).expanduser()


class GovernorState:
    """Load-or-seed wrapper around the kernel + the file layout the governor owns.

    Layout under ``JONI_GOVERNOR_HOME``:
      layer9.json / layer9.journal/   the epistemic core (chunked, sealed)
      pending/                        replayable payloads of staged proposals (P-<claim-id>.json)
      heartbeat.json                  plugin liveness (see audit.liveness)
      policy.yaml                     the deterministic gate policy (operator-owned)
    """

    def __init__(self, home: Path | None = None) -> None:
        self.home = Path(home) if home else governor_home()
        self.core_path = self.home / "layer9.json"
        self.pending_dir = self.home / "pending"
        self.heartbeat_path = self.home / "heartbeat.json"
        self.policy_path = self.home / "policy.yaml"
        self.home.mkdir(parents=True, exist_ok=True)
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        core = persistence.load(self.core_path)
        self.cs = CoreState(core) if core is not None else CoreState(l9.Layer9())

    def save(self) -> None:
        persistence.save(self.cs.core, self.core_path)

    # -- convenience reads ---------------------------------------------------- #

    def claim(self, claim_id: str):
        return self.cs.core.get(claim_id)

    def candidates(self) -> list:
        return [c for c in self.cs.core.all(l9.ObjectType.CLAIM)
                if c.status.value == "candidate"]
