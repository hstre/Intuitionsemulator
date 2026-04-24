"""Experiment D – Long-Loop Chained Reactivation (Combination Effect Test).

Design rationale
----------------
Tests whether H=f(P) AND selective reactivation (F) together provide a unique
advantage over either mechanism alone. The claim must:
  1. Survive 40 steps of minimal-input dormancy (tests H)
  2. Be selectively reactivated by late context    (tests F — or strong K+E)

Key parameter constraint:
  With current r1-r5 and theta_reactivate=0.45, F fires when:
    score = 0.35*max_R + 0.20*A + 0.20*P + 0.25*K >= 0.45
  F also self-sustains (keeps A=1.0) if max_R is large. Therefore:
    Phase 1 uses E_target=0.20 so max_R grows only to R*=0.25.
    Score_max (dormancy, K=0): 0.35*0.25 + 0.20*1.0 + 0.14 = 0.4275 < 0.45 → F off ✓
    Score (phase 4, K=0.90):   0.35*0.25 + 0.20*0.12 + 0.14 + 0.225 = 0.476 > 0.45 → F on ✓

Claims (no neighbor_ids — K=0 except via override_K in Phase 4):
  target    – tags ["B_correct", "kontextuell"], max_R natural (grows to ~0.25).
  dominant  – tags ["haupt"], verifier_exempt=True — neutral tag; does not
              contradict target via verifier. Decays to latent in dormancy.
  distractor– tags ["gruen"], no verifier interaction with target.
  support   – tags ["kontextuell"], given strong E in Phase 4.

5 Phases (120 steps total):
  Phase 1 (0-19):   E_target=0.20 — target activates (A→1.0), max_R→0.25.
                     R* = 0.25 < theta_R=0.40 → never projection_ready.
  Phase 2 (20-39):  E_target=0.04 — A decays from 1.0 toward 0.508 (still latent
                     within 2 steps of dormancy start). F score stays below 0.45.
  Phase 3 (40-79):  Long dormancy. E=0.01 for all, K=0 for target.
                     F off (score < 0.45) → H=8 → A* ≈ 0.060 → dies ~step 76.
                                           H≈10.8 → A* ≈ 0.081 → survives.
                                           H=12   → A* ≈ 0.089 → survives.
  Phase 4 (80-109): Late context: override_K=0.90 for target, E_target=0.04.
                     Main/c/c' (F on): score=0.476 → F fires → fast reactivation.
                     baseline_b (no F): K+E alone → A* >> theta_active → reactivates.
                     → Mathematical impossibility: baseline_b cannot be kept latent with
                       K large enough to fire F. No binary combination effect exists.
  Phase 5 (110-120): Projection window.

Success conditions (success_d):
  1. target not verworfen at step 79       (tests H — baseline_a/c fail)
  2. target NOT projection_ready in steps 0-79   (tests dormancy quality)
  3. dominant.A < theta_active at step 79  (dominant loses control — all modes)
  4. target becomes aktiv in steps 80-119  (all surviving modes succeed)
  5. target projection_ready by step 110   (all surviving modes succeed)

Expected: baseline_b, baseline_a_prime, baseline_c_prime also satisfy all 5.
No unique combination advantage → NO combination effect. Confirms NO_GO verdict.
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

PHASE2_START   = 20
DORMANCY_START = 40
DORMANCY_END   = 80   # late context begins here
PROJ_DEADLINE  = 110


def _build_claims():
    # max_R is not pre-set — grows naturally during Phase 1 to ~0.25
    # This keeps F score below theta_reactivate during dormancy
    return [
        ClaimState("target",     tags=["B_correct", "kontextuell"],
                   R=0.20, P=0.40, A=0.50),
        ClaimState("dominant",   tags=["haupt"],
                   R=0.55, P=0.60, A=0.65, verifier_exempt=True),
        ClaimState("distractor", tags=["gruen"],
                   R=0.10, P=0.30, A=0.38),
        ClaimState("support",    tags=["kontextuell"],
                   R=0.35, P=0.60, A=0.55),
    ]


def _input_fn(t: int, claims):
    if t < PHASE2_START:
        # Phase 1: E_target=0.20 → max_R grows to 0.25 (below theta_R=0.40)
        return {
            "external": {
                "target": 0.20, "dominant": 0.45,
                "distractor": 0.15, "support": 0.20,
            },
            "noise": {
                "target": 0.05, "dominant": 0.05,
                "distractor": 0.05, "support": 0.05,
            },
        }
    elif t < DORMANCY_START:
        # Phase 2: E_target=0.04 → A decays from 1.0 toward 0.508
        return {
            "external": {
                "target": 0.04, "dominant": 0.50,
                "distractor": 0.10, "support": 0.15,
            },
            "noise": {
                "target": 0.05, "dominant": 0.05,
                "distractor": 0.05, "support": 0.05,
            },
        }
    elif t < DORMANCY_END:
        # Phase 3: long dormancy — E=0.01 for all, no K for target
        return {
            "external": {
                "target": 0.01, "dominant": 0.01,
                "distractor": 0.01, "support": 0.01,
            },
            "noise": {
                "target": 0.0, "dominant": 0.0,
                "distractor": 0.0, "support": 0.0,
            },
        }
    else:
        # Phase 4 & 5: late context — override_K=0.90 fires F for main/c/c'
        return {
            "external": {
                "target": 0.04, "dominant": 0.01,
                "distractor": 0.01, "support": 0.50,
            },
            "noise": {
                "target": 0.0, "dominant": 0.0,
                "distractor": 0.0, "support": 0.0,
            },
            "override_K": {"target": 0.90},
        }


def run_experiment_d(params: dict, out_dir: Path = OUTPUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = RuleVerifier()

    modes = ["main", "baseline_a", "baseline_b", "baseline_c",
             "baseline_a_prime", "baseline_c_prime"]
    results = {}

    fig, axes = plt.subplots(4, 3, figsize=(14, 14))
    fig.suptitle("Experiment D – Long-Loop Chained Reactivation (Combination Effect Test)",
                 fontsize=12)

    for mode in modes:
        claims = _build_claims()
        sys = IntuitionSystem(claims, params, mode=mode, verifier=verifier)
        sys.run(120, _input_fn)

        step_79 = DORMANCY_END - 1

        # Condition 1: target not verworfen at end of dormancy
        target_alive = sys.status_at("target", step_79) != "verworfen"

        # Condition 2: target NOT projection_ready during dormancy (steps 0-79)
        target_not_early = not any(
            sys.history[t]["target"]["projection_ready"]
            for t in range(min(DORMANCY_END, len(sys.history)))
        )

        # Condition 3: dominant.A < theta_active at end of dormancy
        dom_a_79 = sys.history[step_79]["dominant"]["A"] if len(sys.history) > step_79 else 1.0
        dominant_latent = dom_a_79 < params["theta_active"]

        # Condition 4: target becomes aktiv after late context starts
        target_reactivates = any(
            sys.history[t]["target"]["status"] == "aktiv"
            for t in range(DORMANCY_END, len(sys.history))
        )

        # Condition 5: target projection_ready by deadline
        proj_step = sys.projection_ready_at("target")
        proj_by_deadline = proj_step is not None and proj_step <= PROJ_DEADLINE

        proj_speed = (proj_step - DORMANCY_END) if proj_step is not None and proj_step >= DORMANCY_END else None

        reactivation_step = None
        for t in range(DORMANCY_END, len(sys.history)):
            if sys.history[t]["target"]["status"] == "aktiv":
                reactivation_step = t
                break

        success_d = (
            target_alive
            and target_not_early
            and dominant_latent
            and target_reactivates
            and proj_by_deadline
        )

        results[mode] = {
            "success_d":              success_d,
            "proj_speed":             proj_speed,
            "proj_step":              proj_step,
            "reactivation_step":      reactivation_step,
            "a_target_at_dormancy":   round(sys.history[step_79]["target"]["A"], 4),
            "a_dominant_at_dormancy": round(dom_a_79, 4),
            "conditions": {
                "target_alive_before_late_context":  target_alive,
                "target_not_projected_early":        target_not_early,
                "dominant_loses_control":            dominant_latent,
                "target_reactivation_after_context": target_reactivates,
                "target_projection_by_deadline":     proj_by_deadline,
            },
        }

        for row, cid in enumerate(["target", "dominant", "distractor", "support"]):
            for col, (field, label) in enumerate([("R", "R"), ("P", "P"), ("A", "A")]):
                ser = sys.get_history_series(cid, field)
                axes[row][col].plot(ser, label=mode)
                axes[row][col].set_title(f"{cid} – {label}")
                axes[row][col].set_xlabel("Step")
                axes[row][col].set_ylim(-0.05, 1.05)
                axes[row][col].axvline(DORMANCY_START, color="gray",
                                       linestyle=":", linewidth=0.7)
                axes[row][col].axvline(DORMANCY_END, color="orange",
                                       linestyle="--", linewidth=0.8,
                                       label="late context" if (row == 0 and col == 0) else None)
                axes[row][col].axvline(PROJ_DEADLINE, color="green",
                                       linestyle="--", linewidth=0.8,
                                       label="deadline" if (row == 0 and col == 0) else None)
                axes[row][col].axhline(params["theta_dead"], color="red",
                                       linestyle=":", linewidth=0.7)

    axes[0][0].legend(fontsize=7)
    plt.tight_layout()
    plot_path = out_dir / "experiment_d.png"
    plt.savefig(plot_path, dpi=120)
    plt.close()

    return {"results": results, "plot": str(plot_path)}


if __name__ == "__main__":
    params = load_params()
    r = run_experiment_d(params)
    for mode, res in r["results"].items():
        print(f"{mode}: success={res['success_d']} "
              f"A_target@79={res['a_target_at_dormancy']} "
              f"proj_speed={res['proj_speed']}")
        for cname, val in res["conditions"].items():
            print(f"  {cname}: {val}")
