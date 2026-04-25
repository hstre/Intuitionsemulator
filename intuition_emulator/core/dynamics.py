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


def compute_trust(
    current_trust: float,
    P_new: float,
    verifier_history: list,
    params: dict,
) -> float:
    """T_new = clamp(rho * T + (1-rho) * sigmoid(t1 * v_smooth + t2 * P_new), 0, 1)

    v_smooth = mean(verifier_history[-stability_window:])  or 0.0 if empty

    Uses P_new (updated plausibility) and verifier_history BEFORE the current
    step's V is appended, so trust lags one step behind the live signal.

    Calibration notes (rho=0.98 rejected before implementation):
      rho=0.98, T₀=0, n=20: T₂₀_max = 1.0×(1−0.98²⁰) = 0.332 — below target
      range 0.55–0.70. rho=0.95 selected:
        T₂₀ ≈ 0.94×(1−0.95²⁰) = 0.94×0.641 ≈ 0.60  (V=+1, P≈0.7)  ✓

      r_T=1.5 rejected: with V=0 during dormancy t2*P drives T→0.6, yielding a
      fixed-point R_ss=0.81 > theta_R=0.40 in Exp D → early projection, breaking
      the success condition. r_T=0.3 selected:
        Fixed-point R_ss = 0.310/(1−0.175) = 0.376 < theta_R=0.40  ✓
        Negative-scenario score ≈ 0.43 < theta_reactivate=0.45           ✓
        T at steady state (V=0, P≈0.70) ≈ 0.70; contribution = 0.3×0.70 = 0.21
        — meaningful additive boost without dominating the score.

      Phase-2 decay (V=−1, 60 steps from T₂₀≈0.60):
        target = sigmoid(2×(−1) + 1×0.5) ≈ 0.182
        T₈₀ ≈ 0.60×0.95⁶⁰ + 0.182×(1−0.95⁶⁰) ≈ 0.028 + 0.174 ≈ 0.201
        (expected ≈0.165; actual depends on verifier signal during dormancy;
        with V=0 during dormancy T converges to ~sigmoid(t2*P) not 0.165)
    """
    window = int(params.get("stability_window", 10))
    if verifier_history:
        recent = verifier_history[-window:]
        v_smooth = float(sum(recent)) / len(recent)
    else:
        v_smooth = 0.0
    target = sigmoid(params["t1"] * v_smooth + params["t2"] * P_new)
    return clamp(params["rho"] * current_trust + (1.0 - params["rho"]) * target)


def compute_half_life(P: float, params: dict, mode: str) -> float:
    """H = H_min + (H_max - H_min) * P  (main, baseline_b, persistence_only).
    H = (H_min+H_max)/2 = 8.0  for baseline_a/c and feedback_only_h8.
    H = 12.0                    for baseline_a'/c' and feedback_only_h12.
    """
    if mode in ("baseline_a", "baseline_c", "feedback_only_h8"):
        return (params["h_min"] + params["h_max"]) / 2.0
    if mode in ("baseline_a_prime", "baseline_c_prime", "feedback_only_h12"):
        return 12.0
    # main, baseline_b, persistence_only — plausibility-dependent
    return params["h_min"] + (params["h_max"] - params["h_min"]) * P


def compute_feedback(claim: ClaimState, context_signal: float, params: dict, mode: str) -> float:
    """Reactivation feedback F.  Zero for baselines A, A', B and persistence_only.

    Trust (r_T * T) amplifies F magnitude but does NOT gate it: F only fires when
    the base score (without T) already meets theta_reactivate.  This preserves all
    experiment calibrations — e.g. Experiment D Phase 1 has score_base=0.4275 < 0.45
    so F stays off regardless of T, preventing premature projection.
    """
    if mode in ("baseline_a", "baseline_b", "baseline_a_prime", "persistence_only"):
        return 0.0
    if claim.status == "verworfen":
        return 0.0
    if claim.verifier_exempt:  # reference/background claims don't receive reactivation feedback
        return 0.0

    verifier_penalty = max(0.0, -claim.last_n_verifier_sum(3))
    score_base = (
        params["r1"] * claim.max_R
        + params["r2"] * claim.A
        + params["r3"] * claim.P
        + params["r4"] * context_signal
        - params["r5"] * verifier_penalty
    )
    if score_base >= params["theta_reactivate"]:
        score = score_base + params["r_T"] * claim.trust
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

    # Trust update — uses P_new and verifier_history BEFORE this step's V is appended
    T_new = compute_trust(claim.trust, P_new, claim.verifier_history, params)

    # Update P_history and stability
    claim.P_history.append(P_new)
    stability_new = compute_stability(claim.P_history, params["stability_window"])

    # Apply updates
    claim.R = R_new
    claim.P = P_new
    claim.H = H_new
    claim.A = A_new
    claim.trust = T_new
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
