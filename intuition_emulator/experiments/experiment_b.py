"""Experiment B – False Dominant + History-based Recovery.

Design rationale
----------------
A claim can only be reactivated via F when:
  score = r1*max_R + r2*A + r3*P + r4*K >= theta_reactivate (0.45)
AND the Phase-3 input is deliberately kept so weak that without F:
  A_fixed = lambda * R_fixed / (1 - decay) < theta_active (0.45)

Three claims:
  oracle    – verifier_exempt, status="aktiv", A=0.50 (just above theta_active).
              After step 0 its A > 0.7, so from step 1 it hard-rejects the dominant.
  dominant  – tags contradict oracle. Gets soft V=-1 at step 0 (oracle.A=0.50 < 0.7),
              hard V=-1 at step 1 (oracle.A≈0.73 > 0.7) → verworfen=1.
              FALSE projection at step 0 (proj_ready=True before hard-reject).
  correct   – max_R=0.80 pre-set (represents prior strong activation).
              Phase 1 (steps 0-19): weak drain → A decays; baselines A/C fall below
              theta_dead → verworfen. Main/B survive with H=f(P).
              Phase 2 (steps 20+): K=0.22, E=0.03, N=0.12 – chosen so that:
                • WITHOUT F: A_fixed ≈ 0.26 (latent, stays below theta_active)
                • WITH    F: F fires (max_R=0.80 pushes score > 0.45) → A rises above 0.45

Expected: main reactivates correct, baseline A/B/C cannot.
Recovery metric: correct_proj_step - dominant_dead_step  (lower = better).
"""
from __future__ import annotations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..core.claim import ClaimState
from ..core.system import IntuitionSystem, load_params
from ..core.verifier import RuleVerifier

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

# Phase boundaries
PHASE2_START = 20


def _build_claims():
    return [
        ClaimState("oracle",   tags=["oracle_correct"],  R=0.70, P=0.80, A=0.50,
                   status="aktiv", verifier_exempt=True),
        ClaimState("dominant", tags=["dominant_wrong"],  R=0.90, P=0.80, A=0.80),
        # max_R=0.80 pre-set: claim was strongly resonant in a prior context
        ClaimState("correct",  tags=["kontextuell"],     R=0.15, P=0.38, A=0.40,
                   max_R=0.80),
    ]


def _input_fn(t: int, claims):
    if t < PHASE2_START:
        # Phase 1: drain correct toward latent / verworfen
        return {
            "external": {"oracle": 0.50, "dominant": 0.40, "correct": 0.08},
            "noise":    {"oracle": 0.05, "dominant": 0.05, "correct": 0.12},
        }
    else:
        # Phase 2: weak context – only sufficient if F fires
        return {
            "external": {"oracle": 0.50, "dominant": 0.00, "correct": 0.04},
            "noise":    {"oracle": 0.05, "dominant": 0.05, "correct": 0.12},
            "override_K": {"correct": 0.22},
        }


def run_experiment_b(params: dict, out_dir: Path = OUTPUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = RuleVerifier()

    modes = ["main", "baseline_a", "baseline_b", "baseline_c",
             "baseline_a_prime", "baseline_c_prime"]
    results = {}

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle("Experiment B – False Dominant + History-Based Recovery", fontsize=12)

    for mode in modes:
        claims = _build_claims()
        sys = IntuitionSystem(claims, params, mode=mode, verifier=verifier)
        sys.run(90, _input_fn)

        dominant_dead_step = None
        for t, snap in enumerate(sys.history):
            if snap["dominant"]["status"] == "verworfen":
                dominant_dead_step = t
                break

        false_projections = sum(
            1 for snap in sys.history if snap["dominant"]["projection_ready"]
        )

        correct_proj_step = sys.projection_ready_at("correct")
        if dominant_dead_step is not None and correct_proj_step is not None:
            recovery_time = max(0, correct_proj_step - dominant_dead_step)
        else:
            recovery_time = None

        results[mode] = {
            "dominant_dead_step": dominant_dead_step,
            "false_projections":  false_projections,
            "correct_proj_step":  correct_proj_step,
            "recovery_time":      recovery_time,
        }

        for row, cid in enumerate(["dominant", "correct"]):
            for col, (field, label) in enumerate([("R", "R"), ("P", "P"), ("A", "A")]):
                ser = sys.get_history_series(cid, field)
                axes[row][col].plot(ser, label=mode)
                axes[row][col].set_title(f"{cid} – {label}")
                axes[row][col].set_xlabel("Step")
                axes[row][col].set_ylim(-0.05, 1.05)
                axes[row][col].axvline(PHASE2_START, color="orange",
                                       linestyle="--", linewidth=0.7)

    axes[0][0].legend(fontsize=7)
    plt.tight_layout()
    plot_path = out_dir / "experiment_b.png"
    plt.savefig(plot_path, dpi=120)
    plt.close()

    return {"results": results, "plot": str(plot_path)}


if __name__ == "__main__":
    params = load_params()
    r = run_experiment_b(params)
    for mode, res in r["results"].items():
        print(f"{mode}: {res}")
