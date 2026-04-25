"""Experiment A: H=f(P) vs H=const — pure half-life discrimination.

Phase 1 (steps 0-49): minimal residual input E=0.01 (no true zero — pure zero
  kills all modes within ~36 steps). E=0.01 creates a discriminating equilibrium:
  main/baseline_b  (H≈10.8 from P→0.7):  A* ≈ 0.081 (> theta_dead=0.08) → latent ✓
  baseline_a/c     (H = const = 8.0):     A* ≈ 0.060 (< theta_dead=0.08) → verworfen ~step 36
  baseline_a'/c'   (H = const = 12.0):    A* ≈ 0.089 → latent (robustness test)

Phase 2 (steps 50+): strong context K=0.85, E=0.35
  → alive claims reactivate; projection-ready by deadline t=80.
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

DORMANCY_END  = 50   # first step with full context input
PROJ_DEADLINE = 80   # projection must be ready by this step
WINDOW_START  = 50   # reactivation window start
WINDOW_END    = 70   # reactivation window end


def _build_claims():
    return [ClaimState("target", tags=["kontextuell"], R=0.2, P=0.5, A=0.5)]


def _input_fn(t: int, claims):
    if t < DORMANCY_END:
        # Minimal residual — creates discriminating H equilibrium without pure zero
        return {"external": {"target": 0.01}, "noise": {"target": 0.0}}
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
             "baseline_a_prime", "baseline_c_prime",
             "persistence_only", "feedback_only_h8", "feedback_only_h12"]
    results = {}

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle("Experiment A – H=f(P) Discrimination (50-step dormancy, E=0.01)", fontsize=12)

    for mode in modes:
        claims = _build_claims()
        sys = IntuitionSystem(claims, params, mode=mode, verifier=verifier)
        sys.run(90, _input_fn)

        cid = "target"
        alive_at_50 = sys.status_at(cid, DORMANCY_END - 1) != "verworfen"
        a_at_50 = sys.history[DORMANCY_END - 1][cid]["A"]

        reactivation_step = None
        for t in range(DORMANCY_END, min(WINDOW_END + 1, len(sys.history))):
            if sys.history[t][cid]["status"] == "aktiv":
                reactivation_step = t
                break

        proj_step = sys.projection_ready_at(cid)
        proj_by_80 = proj_step is not None and proj_step <= PROJ_DEADLINE

        results[mode] = {
            "alive_at_50":       alive_at_50,
            "a_at_50":           round(a_at_50, 4),
            "reactivation_step": reactivation_step,
            "projection_step":   proj_step,
            "projection_by_80":  proj_by_80,
            "reactivation_time": (reactivation_step - DORMANCY_END) if reactivation_step else None,
        }

        for ax_i, (field, label) in enumerate([
            ("R", "Resonance R"), ("P", "Plausibility P"), ("A", "Activation A")
        ]):
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
