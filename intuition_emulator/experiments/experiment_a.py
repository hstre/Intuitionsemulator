"""Experiment A: H=f(P) vs H=const — pure half-life discrimination.

Phase 1 (steps 0-24): no external input (E=K=N=0).
  A decays at rate 2^(-1/H_eff) + lambda_*R (R→0 within ~5 steps).
  main/baseline_b  (H≈10.8 from P→0.7):  A_25 ≈ 0.13  (> theta_dead=0.08) → latent ✓
  baseline_a/c     (H = const = 8.0):     A_25 ≈ 0.075 (< theta_dead=0.08) → verworfen ✓

Phase 2 (steps 25+): strong context K=0.85, E=0.35
  → alive claims reactivate within 1-2 steps; projection-ready well before t=45.
  Deadline: projection_by_45.
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

DORMANCY_END = 25   # first step with context input
PROJ_DEADLINE = 45  # projection must be ready by this step


def _build_claims():
    # R=0.2, P=0.5, A=0.5 as specified by user
    return [ClaimState("target", tags=["kontextuell"], R=0.2, P=0.5, A=0.5)]


def _input_fn(t: int, claims):
    if t < DORMANCY_END:
        # Pure decay: no external input, no noise
        return {"external": {"target": 0.0}, "noise": {"target": 0.0}}
    else:
        # Strong context arrives
        return {
            "external": {"target": 0.35},
            "noise": {"target": 0.05},
            "override_K": {"target": 0.85},
        }


def run_experiment_a(params: dict, out_dir: Path = OUTPUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = RuleVerifier()

    modes = ["main", "baseline_a", "baseline_b", "baseline_c",
             "baseline_a_prime", "baseline_c_prime"]
    results = {}

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle("Experiment A – H=f(P) Discrimination (25-step dormancy)", fontsize=12)

    for mode in modes:
        claims = _build_claims()
        sys = IntuitionSystem(claims, params, mode=mode, verifier=verifier)
        sys.run(60, _input_fn)

        cid = "target"
        # alive_at_25: status at step 24 (last step of dormancy)
        alive_at_25 = sys.status_at(cid, DORMANCY_END - 1) != "verworfen"
        a_at_25 = sys.history[DORMANCY_END - 1][cid]["A"]

        reactivation_step = None
        for t in range(DORMANCY_END, len(sys.history)):
            if sys.history[t][cid]["status"] == "aktiv":
                reactivation_step = t
                break

        proj_step = sys.projection_ready_at(cid)
        proj_by_45 = proj_step is not None and proj_step <= PROJ_DEADLINE

        results[mode] = {
            "alive_at_25": alive_at_25,
            "a_at_25": round(a_at_25, 4),
            "reactivation_step": reactivation_step,
            "projection_step": proj_step,
            "projection_by_45": proj_by_45,
            "reactivation_time": (reactivation_step - DORMANCY_END) if reactivation_step else None,
        }

        for ax_i, (field, label) in enumerate([("R", "Resonance R"), ("P", "Plausibility P"), ("A", "Activation A")]):
            ser = sys.get_history_series(cid, field)
            axes[ax_i].plot(ser, label=mode)
            axes[ax_i].set_title(label)
            axes[ax_i].set_xlabel("Step")
            axes[ax_i].axvline(DORMANCY_END, color="orange", linestyle="--", linewidth=0.8,
                               label="context on" if ax_i == 0 else None)
            axes[ax_i].axvline(PROJ_DEADLINE, color="green", linestyle="--", linewidth=0.8,
                               label="deadline" if ax_i == 0 else None)
            axes[ax_i].axhline(params["theta_dead"], color="red", linestyle=":", linewidth=0.7)
            axes[ax_i].set_ylim(-0.05, 1.05)

    axes[0].legend(fontsize=7)
    plt.tight_layout()
    plot_path = out_dir / "experiment_a.png"
    plt.savefig(plot_path, dpi=120)
    plt.close()

    return {"results": results, "plot": str(plot_path)}


if __name__ == "__main__":
    params = load_params()
    r = run_experiment_a(params)
    for mode, res in r["results"].items():
        print(f"{mode}: {res}")
