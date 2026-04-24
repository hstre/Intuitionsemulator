"""Stability check: 2-3 claims, fixed constant inputs, 200 steps.
Verifies the system converges without oscillation or divergence.
Also runs a parameter sweep over alpha x eta.
"""
from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from itertools import product

from ..core.claim import ClaimState
from ..core.system import IntuitionSystem, load_params


OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


def run_stability_check(params: dict, out_dir: Path = OUTPUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    claims = [
        ClaimState("c1", tags=["rot"], R=0.6, P=0.5, A=0.6),
        ClaimState("c2", tags=["positiv"], R=0.3, P=0.4, A=0.4),
        ClaimState("c3", tags=["hoch"], R=0.8, P=0.7, A=0.7),
    ]

    # Fixed constant inputs
    E_fixed = {"c1": 0.4, "c2": 0.2, "c3": 0.6}
    N_fixed = {"c1": 0.1, "c2": 0.1, "c3": 0.1}

    sys = IntuitionSystem(claims, params, mode="main")
    sys.run(200, lambda t, _: {"external": E_fixed, "noise": N_fixed})

    fig, axes = plt.subplots(3, 3, figsize=(14, 10))
    fig.suptitle("Stability Check – Fixed Inputs, 200 Steps", fontsize=13)

    results = {}
    for col, claim in enumerate(claims):
        cid = claim.claim_id
        R_ser = sys.get_history_series(cid, "R")
        P_ser = sys.get_history_series(cid, "P")
        A_ser = sys.get_history_series(cid, "A")

        # Convergence: last-20 std < 0.05
        converged = (
            np.std(R_ser[-20:]) < 0.05
            and np.std(P_ser[-20:]) < 0.05
            and np.std(A_ser[-20:]) < 0.05
        )
        results[cid] = {"converged": converged}

        for row, (ser, label) in enumerate([(R_ser, "R"), (P_ser, "P"), (A_ser, "A")]):
            axes[row][col].plot(ser)
            axes[row][col].set_ylim(-0.05, 1.05)
            axes[row][col].set_title(f"{cid} – {label}")
            axes[row][col].set_xlabel("Step")
            axes[row][col].set_ylabel(label)
            status_tag = "✓ converged" if converged else "✗ diverged"
            if row == 0:
                axes[row][col].set_title(f"{cid} ({status_tag}) – {label}")

    plt.tight_layout()
    plot_path = out_dir / "stability_check.png"
    plt.savefig(plot_path, dpi=120)
    plt.close()

    return {"claim_results": results, "plot": str(plot_path)}


def run_parameter_sweep(params_base: dict, out_dir: Path = OUTPUT_DIR) -> dict:
    """Sweep alpha in {0.4,0.5,0.6,0.7,0.8} x eta in {0.3,0.5,0.7}."""
    out_dir.mkdir(parents=True, exist_ok=True)

    alphas = [0.4, 0.5, 0.6, 0.7, 0.8]
    etas = [0.3, 0.5, 0.7]

    sweep_results = {}
    fig, axes = plt.subplots(len(etas), len(alphas), figsize=(18, 10))
    fig.suptitle("Parameter Sweep – alpha × eta (Claim c1 Activation)", fontsize=12)

    E_fixed = {"c1": 0.4, "c2": 0.2, "c3": 0.6}
    N_fixed = {"c1": 0.1, "c2": 0.1, "c3": 0.1}

    for ei, eta in enumerate(etas):
        for ai, alpha in enumerate(alphas):
            p = dict(params_base)
            p["alpha"] = alpha
            p["eta"] = eta

            claims = [
                ClaimState("c1", tags=["rot"], R=0.6, P=0.5, A=0.6),
                ClaimState("c2", tags=["positiv"], R=0.3, P=0.4, A=0.4),
                ClaimState("c3", tags=["hoch"], R=0.8, P=0.7, A=0.7),
            ]
            sys = IntuitionSystem(claims, p, mode="main")
            sys.run(200, lambda t, _: {"external": E_fixed, "noise": N_fixed})

            A_ser = sys.get_history_series("c1", "A")
            converged = np.std(A_ser[-20:]) < 0.05
            sweep_results[(alpha, eta)] = converged

            ax = axes[ei][ai]
            ax.plot(A_ser)
            ax.set_ylim(-0.05, 1.05)
            ax.set_title(f"α={alpha} η={eta}\n{'✓' if converged else '✗'}", fontsize=8)
            ax.set_xlabel("Step", fontsize=7)

    plt.tight_layout()
    sweep_path = out_dir / "stability_sweep.png"
    plt.savefig(sweep_path, dpi=120)
    plt.close()

    all_stable = all(sweep_results.values())
    return {
        "sweep_results": {str(k): v for k, v in sweep_results.items()},
        "all_stable": all_stable,
        "plot": str(sweep_path),
    }


if __name__ == "__main__":
    params = load_params()
    r1 = run_stability_check(params)
    r2 = run_parameter_sweep(params)
    print("Stability check:", r1["claim_results"])
    print("All sweep stable:", r2["all_stable"])
