"""Experiment C – Selective Reactivation via History.

Design rationale
----------------
Identical to Exp B's recovery logic but tests SPECIFICITY across three alternatives:

  alt1  max_R=0.80 (pre-set: strong prior history)
  alt2  max_R=0.15 (default: no relevant prior)
  alt3  max_R=0.15

Phase 1 (steps 0-19): weak drain → all three decay.
  Baseline A/C (H=8): A falls below theta_dead → verworfen before step 20.
  Main/B   (H≈10):   A ≈ 0.10 at step 20 (latent but alive).

Phase 2 (steps 20+):
  alt1 gets K=0.22, E=0.03, N=0.12:
    • WITHOUT F: A_fixed ≈ 0.26 (latent) → no activation for baseline B.
    • WITH    F: score = r1*0.80+… > theta_reactivate → F fires → alt1 activates.
  alt2/alt3 get K=0.0, E=0.03, N=0.12:
    score = r1*0.15+… never reaches theta_reactivate even with F.

Expected:
  main:       alt1 reactivated; alt2/alt3 not → precision = 1.0
  baseline_a: all verworfen before step 20 → nothing reactivates → precision = 0
  baseline_b: alt1 stays latent (F=0 insufficient) → precision = 0
  baseline_c: same as main (has F) → precision = 1.0, slightly slower proj_speed
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

PHASE2_START = 20


def _build_claims():
    return [
        ClaimState("alt1", tags=["B_correct", "kontextuell"],
                   R=0.15, P=0.38, A=0.40, max_R=0.80),
        ClaimState("alt2", tags=["gruen"],
                   R=0.15, P=0.38, A=0.40),
        ClaimState("alt3", tags=["niedrig"],
                   R=0.15, P=0.38, A=0.40),
    ]


def _input_fn(t: int, claims):
    if t < PHASE2_START:
        return {
            "external": {"alt1": 0.08, "alt2": 0.08, "alt3": 0.08},
            "noise":    {"alt1": 0.12, "alt2": 0.12, "alt3": 0.12},
        }
    else:
        return {
            "external": {"alt1": 0.04, "alt2": 0.04, "alt3": 0.04},
            "noise":    {"alt1": 0.12, "alt2": 0.12, "alt3": 0.12},
            "override_K": {"alt1": 0.22, "alt2": 0.0, "alt3": 0.0},
        }


def run_experiment_c(params: dict, out_dir: Path = OUTPUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = RuleVerifier()

    modes = ["main", "baseline_a", "baseline_b", "baseline_c",
             "baseline_a_prime", "baseline_c_prime",
             "persistence_only", "feedback_only_h8", "feedback_only_h12"]
    results = {}

    fig, axes = plt.subplots(3, 3, figsize=(14, 10))
    fig.suptitle("Experiment C – Selective Reactivation", fontsize=12)

    for mode in modes:
        claims = _build_claims()
        sys = IntuitionSystem(claims, params, mode=mode, verifier=verifier)
        sys.run(90, _input_fn)

        reactivated_correct = 0
        unnecessary = 0
        for cid in ["alt1", "alt2", "alt3"]:
            ever_active = any(
                sys.history[t][cid]["status"] == "aktiv"
                for t in range(PHASE2_START, len(sys.history))
            )
            if ever_active:
                if cid == "alt1":
                    reactivated_correct += 1
                else:
                    unnecessary += 1

        total = reactivated_correct + unnecessary
        precision = reactivated_correct / total if total > 0 else 0.0

        proj_step_alt1 = sys.projection_ready_at("alt1")
        proj_speed = (proj_step_alt1 - PHASE2_START) if proj_step_alt1 is not None else None

        results[mode] = {
            "reactivated_correct":       reactivated_correct,
            "unnecessary_reactivations": unnecessary,
            "precision":                 precision,
            "proj_step_alt1":            proj_step_alt1,
            "proj_speed":                proj_speed,
        }

        for row, cid in enumerate(["alt1", "alt2", "alt3"]):
            for col, (field, label) in enumerate([("R", "R"), ("P", "P"), ("A", "A")]):
                ser = sys.get_history_series(cid, field)
                axes[row][col].plot(ser, label=mode)
                axes[row][col].set_title(f"{cid} – {label}")
                axes[row][col].set_xlabel("Step")
                axes[row][col].set_ylim(-0.05, 1.05)
                axes[row][col].axvline(PHASE2_START, color="orange",
                                       linestyle="--", linewidth=0.8)

    axes[0][0].legend(fontsize=7)
    plt.tight_layout()
    plot_path = out_dir / "experiment_c.png"
    plt.savefig(plot_path, dpi=120)
    plt.close()

    return {"results": results, "plot": str(plot_path)}


if __name__ == "__main__":
    params = load_params()
    r = run_experiment_c(params)
    for mode, res in r["results"].items():
        print(f"{mode}: {res}")
