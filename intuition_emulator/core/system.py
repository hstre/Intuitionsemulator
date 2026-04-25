from __future__ import annotations
from typing import List, Dict, Any, Callable, Optional
import yaml
from pathlib import Path
from .claim import ClaimState
from .dynamics import update_claim
from .verifier import RuleVerifier


_DEFAULT_PARAMS_PATH = Path(__file__).parent.parent / "config" / "params_default.yaml"


def load_params(path: Path | str | None = None) -> dict:
    p = Path(path) if path else _DEFAULT_PARAMS_PATH
    with open(p) as f:
        return yaml.safe_load(f)


class IntuitionSystem:
    """
    Central simulation loop.

    mode: "main" | "baseline_a" | "baseline_b" | "baseline_c"
          | "baseline_a_prime" | "baseline_c_prime"
          | "persistence_only" | "feedback_only_h8" | "feedback_only_h12"

    Mechanism path aliases (explicit labels for existing mode variants):
    ┌────────────────────┬──────────────────┬─────────────┬─────────────┐
    │ Mechanism label    │ Mode string      │ H           │ F           │
    ├────────────────────┼──────────────────┼─────────────┼─────────────┤
    │ combined_main      │ "main"           │ f(P)        │ active      │
    │ persistence_only   │ "persistence_only│ f(P)        │ 0           │
    │                    │  " = baseline_b  │             │             │
    │ feedback_only_h8   │ "feedback_only_h8│ constant 8  │ active      │
    │                    │  " = baseline_c  │             │             │
    │ feedback_only_h12  │ "feedback_only_h1│ constant 12 │ active      │
    │                    │  2" = baseline_c'│             │             │
    │ persistence_h8     │ "baseline_a"     │ constant 8  │ 0           │
    │ persistence_h12    │ "baseline_a_prime│ constant 12 │ 0           │
    │                    │  "               │             │             │
    └────────────────────┴──────────────────┴─────────────┴─────────────┘

    These aliases are labels only — no new code paths. The dynamics are determined
    entirely by the H computation (compute_half_life) and F computation
    (compute_feedback) in dynamics.py based on the mode string.
    """

    def __init__(
        self,
        claims: List[ClaimState],
        params: dict,
        mode: str = "main",
        verifier: Optional[RuleVerifier] = None,
        competition_matrix: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        self.claims: List[ClaimState] = claims
        self.params = params
        self.mode = mode
        self.verifier = verifier
        self.competition_matrix = competition_matrix or {}
        self.step_count = 0
        self.history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Input helpers

    def _get_claim_by_id(self, cid: str) -> Optional[ClaimState]:
        for c in self.claims:
            if c.claim_id == cid:
                return c
        return None

    def _compute_K(self, claim: ClaimState) -> float:
        """Context signal: average R of active neighbors."""
        if not claim.neighbor_ids:
            return 0.0
        vals = []
        for nid in claim.neighbor_ids:
            n = self._get_claim_by_id(nid)
            if n and n.status == "aktiv":
                vals.append(n.R)
        return float(sum(vals) / len(vals)) if vals else 0.0

    def _compute_N(self, claim: ClaimState) -> float:
        """Lateral inhibition from competition matrix (optional)."""
        if claim.claim_id not in self.competition_matrix:
            return 0.0
        total = 0.0
        for other_id, strength in self.competition_matrix[claim.claim_id].items():
            other = self._get_claim_by_id(other_id)
            if other and other.status == "aktiv":
                total += strength * other.A
        return min(1.0, total)

    # ------------------------------------------------------------------
    # Step

    def step(
        self,
        external_inputs: Dict[str, float],  # claim_id -> E value
        noise_inputs: Optional[Dict[str, float]] = None,
        override_K: Optional[Dict[str, float]] = None,
    ):
        """Advance all claims by one time step."""
        noise_inputs = noise_inputs or {}

        # Snapshot active claims with FROZEN A values so sequential updates
        # within one step don't affect each other's verifier decisions.
        active_claims = [c for c in self.claims if c.status == "aktiv"]

        # Pre-compute all verifier signals before any update mutates claim state.
        verifier_signals: Dict[str, tuple] = {}
        for claim in self.claims:
            if self.verifier is not None and claim.status != "verworfen" and not claim.verifier_exempt:
                verifier_signals[claim.claim_id] = self.verifier.verify(claim.tags, active_claims)
            else:
                verifier_signals[claim.claim_id] = (0, False)

        snapshot = {}
        for claim in self.claims:
            E = external_inputs.get(claim.claim_id, 0.0)
            K = override_K[claim.claim_id] if (override_K and claim.claim_id in override_K) else self._compute_K(claim)
            N = noise_inputs.get(claim.claim_id, 0.0)
            context_signal = K  # reactivation context uses same K

            V, hard = verifier_signals[claim.claim_id]

            update_claim(claim, E, K, N, V, hard, context_signal, self.params, self.mode)

            snapshot[claim.claim_id] = {
                "R": claim.R,
                "P": claim.P,
                "A": claim.A,
                "H": claim.H,
                "status": claim.status,
                "stability": claim.stability,
                "projection_ready": claim.is_projection_ready(self.params),
            }

        self.history.append(snapshot)
        self.step_count += 1

    def run(
        self,
        steps: int,
        input_fn: Callable[[int, List[ClaimState]], Dict[str, Any]],
    ):
        """Run for `steps` steps. input_fn(step, claims) -> dict with keys:
        'external', optional 'noise', optional 'override_K'.
        """
        for t in range(steps):
            inputs = input_fn(t, self.claims)
            self.step(
                external_inputs=inputs.get("external", {}),
                noise_inputs=inputs.get("noise", {}),
                override_K=inputs.get("override_K", None),
            )

    # ------------------------------------------------------------------
    # Convenience accessors

    def get_history_series(self, claim_id: str, field: str) -> List[float]:
        return [snap[claim_id][field] for snap in self.history if claim_id in snap]

    def projection_ready_at(self, claim_id: str) -> Optional[int]:
        for t, snap in enumerate(self.history):
            if snap.get(claim_id, {}).get("projection_ready", False):
                return t
        return None

    def status_at(self, claim_id: str, t: int) -> str:
        if t < len(self.history):
            return self.history[t].get(claim_id, {}).get("status", "unknown")
        return "unknown"
