"""joni-governor — Layer 9 as the sole write authority over a Hermes agent.

Hermes acts; the governor decides what counts as valid persistent state. Every memory/skill
write the agent attempts becomes a PROPOSAL: a CANDIDATE claim in the governor's own
``desi_layer9`` core (append-only, hash-chained, gate-recorded) plus a replayable payload in
``pending/``. The gate decides deterministically — auto-rules from ``policy.yaml``, the
revenant guard against re-proposing what was already rejected — or defers to the operator
(``joni-governor sheet`` / ``decide``). A rejected proposal is a corrected error: the persona
("Expertise = verdichtete Geschichte korrigierter Irrtümer") is built from day one.

Design rules inherited from the Joni testbed:
  * models are never authoritative - they propose, the gate disposes;
  * fail-closed: if the kernel state cannot load, gated tools are blocked, never silently open;
  * everything auditable: each verdict is a gate-recorded kernel op in the governor's ledger;
  * assessable, not just counted: the operator sheet shows the proposed CONTENT, not a number.
"""

from joni_governor.gate import Verdict, decide_tool_call
from joni_governor.state import GovernorState

__version__ = "0.1.0"

__all__ = ["GovernorState", "Verdict", "decide_tool_call", "__version__"]
