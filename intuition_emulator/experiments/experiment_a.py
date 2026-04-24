"""Experiment A: Weak signal → late strong signal.
Phase 1 (steps 0-20): near-zero input + inhibition  → baselines A/C (H=const=8) let A decay
                       below theta_dead; main/B (H=f(P)≈10.4) keep the claim alive.
Phase 2 (steps 20-30): gentle ramp-up
Phase 3 (steps 30+):   strong context K=0.85 → reactivation, projection-ready by step 50.
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

# Initial state: A=0.42 is just below theta_active=0.45.
# With H≈10.4 (main) the claim survives 20 steps of decay;
# with H=8 (baseline A/C) it falls below theta_dead=0.08.
def _build_claims():
    return [ClaimState("target", tags=["kontextuell"], R=0.2, P=0.4, A=0.42)]


def _input_fn(t: int, claims):
    if t < 20:
        # Barely any input, slight inhibition – drives R toward 0
        return {"external": {"target": 0.03}, "noise": {"target": 0.15}}
    elif t < 30:
        # Transition: moderate input
        return {"external": {"target": 0.15}, "noise": {"target": 0.08}}
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

    modes = ["main", "baseline_a", "baseline_b", "baseline_c"]
    results = {}

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle("Experiment A – Weak Signal, Late Context", fontsize=12)

    for mode in modes:
        claims = _build_claims()
        sys = IntuitionSystem(claims, params, mode=mode, verifier=verifier)
        sys.run(70, _input_fn)

        cid = "target"
        alive_at_20 = sys.status_at(cid, 19) != "verworfen"

        reactivation_step = None
        for t in range(30, len(sys.history)):
            if sys.history[t][cid]["status"] == "aktiv":
                reactivation_step = t
                break

        proj_step = sys.projection_ready_at(cid)
        proj_by_50 = proj_step is not None and proj_step <= 50

        results[mode] = {
            "alive_at_20": alive_at_20,
            "reactivation_step": reactivation_step,
            "projection_step": proj_step,
            "projection_by_50": proj_by_50,
            "reactivation_time": (reactivation_step - 30) if reactivation_step else None,
        }

        for ax_i, (field, label) in enumerate([("R", "Resonance R"), ("P", "Plausibility P"), ("A", "Activation A")]):
            ser = sys.get_history_series(cid, field)
            axes[ax_i].plot(ser, label=mode)
            axes[ax_i].set_title(label)
            axes[ax_i].set_xlabel("Step")
            axes[ax_i].axvline(20, color="gray", linestyle=":", linewidth=0.8)
            axes[ax_i].axvline(30, color="orange", linestyle="--", linewidth=0.8)
            axes[ax_i].axvline(50, color="green", linestyle="--", linewidth=0.8)
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
