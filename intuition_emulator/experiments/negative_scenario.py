"""Negative scenario: 20 claims, pure random noise, verifier always 0.

Initial A in [0.10, 0.25] keeps all claims latent (below theta_active=0.45) from
the start.  E and N are both drawn from [0, 0.15] so R's fixed point ≈ 0 – A only
decays.  Expected: <5% of claims ever become active or projection-ready.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..core.claim import ClaimState
from ..core.system import IntuitionSystem, load_params


OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

NUM_CLAIMS = 20
STEPS = 100
RNG_SEED = 42


def _build_claims(rng: np.random.Generator) -> list:
    claims = []
    for i in range(NUM_CLAIMS):
        r0 = float(rng.uniform(0.05, 0.15))
        a0 = float(rng.uniform(0.10, 0.25))
        p0 = float(rng.uniform(0.20, 0.35))
        claims.append(ClaimState(f"noise_{i:02d}", tags=["rauschen"], R=r0, P=p0, A=a0))
    return claims


def _make_input_fn(rng: np.random.Generator, claim_ids: list):
    def _fn(t: int, claims):
        external = {cid: float(rng.uniform(0.0, 0.15)) for cid in claim_ids}
        noise    = {cid: float(rng.uniform(0.0, 0.15)) for cid in claim_ids}
        return {"external": external, "noise": noise}
    return _fn


def run_negative_scenario(params: dict, out_dir: Path = OUTPUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    claims = _build_claims(rng)
    claim_ids = [c.claim_id for c in claims]

    sys = IntuitionSystem(claims, params, mode="main", verifier=None)
    sys.run(STEPS, _make_input_fn(rng, claim_ids))

    reactivated = 0
    projected = 0
    for cid in claim_ids:
        if any(sys.history[t][cid]["status"] == "aktiv"   for t in range(STEPS)):
            reactivated += 1
        if any(sys.history[t][cid]["projection_ready"]    for t in range(STEPS)):
            projected += 1

    reactivation_rate = reactivated / NUM_CLAIMS
    projection_rate   = projected   / NUM_CLAIMS

    fig, ax = plt.subplots(figsize=(12, 5))
    for cid in claim_ids:
        ax.plot(sys.get_history_series(cid, "A"), alpha=0.5, linewidth=0.8)
    ax.axhline(params["theta_active"], color="red", linestyle="--",
               label=f"θ_active={params['theta_active']}")
    ax.set_title("Negative Scenario – 20 Claims, Pure Noise")
    ax.set_xlabel("Step")
    ax.set_ylabel("Activation A")
    ax.legend()
    plot_path = out_dir / "negative_scenario.png"
    plt.tight_layout()
    plt.savefig(plot_path, dpi=120)
    plt.close()

    return {
        "reactivation_rate": reactivation_rate,
        "projection_rate":   projection_rate,
        "reactivated_count": reactivated,
        "projected_count":   projected,
        "passes": reactivation_rate < 0.05 and projection_rate < 0.05,
        "plot": str(plot_path),
    }


if __name__ == "__main__":
    params = load_params()
    r = run_negative_scenario(params)
    print(r)
