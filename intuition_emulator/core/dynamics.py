from __future__ import annotations
import numpy as np
from .claim import ClaimState


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def compute_stability(P_history: list, window: int) -> float:
    """stability = 1 - normalized_variance(P_history over window).
    Max variance for P in [0,1] is 0.25 (Bernoulli), used for normalization.
    """
    recent = P_history[-window:] if len(P_history) >= window else P_history
    if len(recent) < 2:
        return 1.0
    var = float(np.var(recent))
    normalized = min(1.0, var / 0.25)
    return 1.0 - normalized


def compute_half_life(P: float, params: dict, mode: str) -> float:
    """H = H_min + (H_max - H_min) * P  (main model and baseline B).
    Baselines A/C use H_const = (H_min+H_max)/2 = 8.0.
    Baselines A'/C' use H_const_prime = 12.0 (robustness test).
    """
    if mode in ("baseline_a", "baseline_c"):
        return (params["h_min"] + params["h_max"]) / 2.0
    if mode in ("baseline_a_prime", "baseline_c_prime"):
        return 12.0
    return params["h_min"] + (params["h_max"] - params["h_min"]) * P


def compute_feedback(claim: ClaimState, context_signal: float, params: dict, mode: str) -> float:
    """Reactivation feedback F.  Zero for baselines A, A' and B."""
    if mode in ("baseline_a", "baseline_b", "baseline_a_prime"):
        return 0.0
    if claim.status == "verworfen":
        return 0.0
    if claim.verifier_exempt:  # reference/background claims don't receive reactivation feedback
        return 0.0

    verifier_penalty = max(0.0, -claim.last_n_verifier_sum(3))
    score = (
        params["r1"] * claim.max_R
        + params["r2"] * claim.A
        + params["r3"] * claim.P
        + params["r4"] * context_signal
        - params["r5"] * verifier_penalty
    )
    if score >= params["theta_reactivate"]:
        return params["mu"] * score
    return 0.0


def update_claim(
    claim: ClaimState,
    E: float,
    K: float,
    N: float,
    V: int,
    hard_reject: bool,
    context_signal: float,
    params: dict,
    mode: str = "main",
) -> ClaimState:
    """Apply one time-step update to a claim in-place and return it."""

    if claim.status == "verworfen":
        claim.age += 1
        return claim

    # Feedback signal
    F = compute_feedback(claim, context_signal, params, mode)

    # Resonance update
    R_new = clamp(
        params["alpha"] * claim.R
        + params["beta"] * E
        + params["gamma"] * K
        + params["delta"] * F
        - params["eta"] * N
    )

    # Plausibility update (uses V as float: +1, 0, -1)
    P_new = sigmoid(
        params["w1"] * claim.P
        + params["w2"] * R_new
        + params["w3"] * float(V)
        + params["w4"] * K
        - params["w5"] * N
    )

    # Half-life
    H_new = compute_half_life(P_new, params, mode)

    # Activation decay + resonance injection
    dt = params["dt"]
    A_new = clamp(claim.A * (2.0 ** (-dt / H_new)) + params["lambda_"] * R_new)

    # Update P_history and stability
    claim.P_history.append(P_new)
    stability_new = compute_stability(claim.P_history, params["stability_window"])

    # Apply updates
    claim.R = R_new
    claim.P = P_new
    claim.H = H_new
    claim.A = A_new
    claim.stability = stability_new
    claim.age += 1

    if R_new > claim.max_R:
        claim.max_R = R_new

    # Record verifier signal
    claim.record_verifier(V)

    # Status logic — hard reject requires 3 consecutive V=-1 in history, or A<0.3
    effective_hard = False
    if hard_reject:
        recent_3 = claim.verifier_history[-3:]
        effective_hard = (
            len(recent_3) >= 3 and all(v == -1 for v in recent_3)
        ) or (claim.A < 0.3)

    if effective_hard or claim.A <= params["theta_dead"]:
        claim.status = "verworfen"
    elif claim.A >= params["theta_active"]:
        claim.status = "aktiv"
    else:
        claim.status = "latent"

    return claim
