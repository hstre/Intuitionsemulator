"""Metric extraction and main-vs-baseline comparison helpers.

ComparisonResult schema:
  {"outcome": "win" | "loss" | "tie" | "not_applicable", "metric": str, "margin": float | None}

win  = main is better by >= THRESHOLD (20%)
loss = baseline is better by >= THRESHOLD
tie  = within ±THRESHOLD or both fail identically
not_applicable = comparison cannot be made (both dead, etc.)
"""
from __future__ import annotations

THRESHOLD = 0.20


def _cr(outcome: str, metric: str, margin=None) -> dict:
    return {"outcome": outcome, "metric": metric, "margin": margin}


# ---------------------------------------------------------------------------
# Extraction helpers

def extract_metrics_a(results: dict) -> dict:
    main = results.get("main", {})
    baselines = {k: v for k, v in results.items() if k != "main"}

    correct_reactivation = (
        main.get("alive_at_50", False)
        and main.get("reactivation_step") is not None
        and main.get("projection_by_80", False)
    )
    all_modes = {"main": main, **baselines}
    return {
        "correct_late_reactivation":  1 if correct_reactivation else 0,
        "avg_time_to_reactivation":   main.get("reactivation_time"),
        "baseline_reactivation_times": {k: v.get("reactivation_time") for k, v in baselines.items()},
        "main_reactivated":            main.get("reactivation_step") is not None,
        "baseline_reactivated":        {k: v.get("reactivation_step") is not None for k, v in baselines.items()},
        "alive_at_50":                 main.get("alive_at_50", False),
        "baseline_alive_at_50":        {k: v.get("alive_at_50", False) for k, v in baselines.items()},
        "projection_by_80":            main.get("projection_by_80", False),
        "a_at_50_all":                 {k: v.get("a_at_50") for k, v in all_modes.items()},
    }


def extract_metrics_b(results: dict) -> dict:
    main = results.get("main", {})
    baselines = {k: v for k, v in results.items() if k != "main"}
    return {
        "dominant_dead_step":         main.get("dominant_dead_step"),
        "false_projections_main":     main.get("false_projections", 0),
        "recovery_time_main":         main.get("recovery_time"),
        "main_recovered":             main.get("recovery_time") is not None,
        "baseline_recovery_times":    {k: v.get("recovery_time") for k, v in baselines.items()},
        "baseline_recovered":         {k: v.get("recovery_time") is not None for k, v in baselines.items()},
        "baseline_false_projections": {k: v.get("false_projections", 0) for k, v in baselines.items()},
        "baseline_dominant_dead":     {k: v.get("dominant_dead_step") for k, v in baselines.items()},
    }


def extract_metrics_c(results: dict) -> dict:
    main = results.get("main", {})
    baselines = {k: v for k, v in results.items() if k != "main"}
    return {
        "reactivated_correct_main": main.get("reactivated_correct", 0),
        "unnecessary_main":         main.get("unnecessary_reactivations", 0),
        "precision_main":           main.get("precision", 0.0),
        "proj_speed_main":          main.get("proj_speed"),
        "baseline_precision":       {k: v.get("precision", 0.0) for k, v in baselines.items()},
        "baseline_proj_speed":      {k: v.get("proj_speed") for k, v in baselines.items()},
    }


def extract_metrics_negative(result: dict) -> dict:
    return {
        "reactivation_rate": result.get("reactivation_rate", 1.0),
        "projection_rate":   result.get("projection_rate", 1.0),
        "passes":            result.get("passes", False),
    }


def extract_metrics_d(results: dict) -> dict:
    main = results.get("main", {})
    baselines = {k: v for k, v in results.items() if k != "main"}
    return {
        "success_d_main":         main.get("success_d", False),
        "proj_speed_main":        main.get("proj_speed"),
        "baseline_success_d":     {k: v.get("success_d", False) for k, v in baselines.items()},
        "baseline_proj_speed":    {k: v.get("proj_speed") for k, v in baselines.items()},
        "conditions_main":        main.get("conditions", {}),
        "baseline_conditions":    {k: v.get("conditions", {}) for k, v in baselines.items()},
    }


# ---------------------------------------------------------------------------
# Comparison helpers — all return Dict[baseline_name, ComparisonResult]

def compare_main_vs_baselines_a(metrics: dict) -> dict:
    """Primary: alive_at_50 (binary). Secondary: reactivation speed (lower=better)."""
    main_alive = metrics.get("alive_at_50", False)
    main_time  = metrics.get("avg_time_to_reactivation")
    main_react = metrics.get("main_reactivated", False)
    comparisons = {}

    for bname in metrics.get("baseline_alive_at_50", {}):
        b_alive = metrics["baseline_alive_at_50"][bname]
        b_time  = metrics.get("baseline_reactivation_times", {}).get(bname)
        b_react = metrics.get("baseline_reactivated", {}).get(bname, False)

        if main_alive and not b_alive:
            comparisons[bname] = _cr("win", "alive_at_50", 1.0)
        elif not main_alive and b_alive:
            comparisons[bname] = _cr("loss", "alive_at_50", None)
        elif not main_alive and not b_alive:
            comparisons[bname] = _cr("not_applicable", "alive_at_50", None)
        elif main_react and not b_react:
            comparisons[bname] = _cr("win", "reactivation", 1.0)
        elif not main_react and b_react:
            comparisons[bname] = _cr("loss", "reactivation", None)
        elif main_react and b_react and main_time is not None and b_time is not None and b_time > 0:
            margin = (b_time - main_time) / b_time
            if margin >= THRESHOLD:
                comparisons[bname] = _cr("win", "reactivation_time", margin)
            elif margin <= -THRESHOLD:
                comparisons[bname] = _cr("loss", "reactivation_time", margin)
            else:
                comparisons[bname] = _cr("tie", "reactivation_time", margin)
        else:
            comparisons[bname] = _cr("not_applicable", "reactivation_time", None)

    return comparisons


def compare_main_vs_baselines_b(metrics: dict) -> dict:
    """Three-metric: dominant_dead_step, false_projections, recovery_time.
    win = at least 1 metric >=20% better AND no metric >20% worse.
    """
    main_dead  = metrics.get("dominant_dead_step")
    main_fp    = metrics.get("false_projections_main", 0)
    main_rt    = metrics.get("recovery_time_main")
    comparisons = {}

    for bname in metrics.get("baseline_recovery_times", {}):
        b_dead = metrics.get("baseline_dominant_dead", {}).get(bname)
        b_fp   = metrics.get("baseline_false_projections", {}).get(bname, 0)
        b_rt   = metrics.get("baseline_recovery_times", {}).get(bname)

        margins = {}

        # Metric 1: dominant_dead_step (lower = better for main; sooner death = better)
        if main_dead is not None and b_dead is not None and b_dead > 0:
            margins["dominant_dead"] = (b_dead - main_dead) / b_dead
        elif main_dead is not None and b_dead is None:
            margins["dominant_dead"] = 1.0
        elif main_dead is None and b_dead is not None:
            margins["dominant_dead"] = -1.0

        # Metric 2: false_projections (lower = better for main)
        if b_fp > 0:
            margins["false_proj"] = (b_fp - main_fp) / b_fp
        elif main_fp == 0 and b_fp == 0:
            margins["false_proj"] = 0.0

        # Metric 3: recovery_time (lower = better for main)
        if main_rt is not None and b_rt is not None and b_rt > 0:
            margins["recovery"] = (b_rt - main_rt) / b_rt
        elif main_rt is not None and b_rt is None:
            margins["recovery"] = 1.0
        elif main_rt is None and b_rt is not None:
            margins["recovery"] = -1.0
        elif main_rt is None and b_rt is None:
            pass  # no recovery metric available

        if not margins:
            comparisons[bname] = _cr("not_applicable", "all_metrics", None)
            continue

        any_win   = any(v >= THRESHOLD for v in margins.values())
        any_loss  = any(v <= -THRESHOLD for v in margins.values())
        best_margin = max(margins.values())
        # Determine primary metric for reporting
        primary = max(margins, key=lambda k: abs(margins[k]))

        if any_win and not any_loss:
            comparisons[bname] = _cr("win", primary, best_margin)
        elif any_loss and not any_win:
            comparisons[bname] = _cr("loss", primary, min(margins.values()))
        elif any_win and any_loss:
            # Mixed — classify as tie since no clean advantage
            comparisons[bname] = _cr("tie", primary, best_margin)
        else:
            comparisons[bname] = _cr("tie", primary, best_margin)

    return comparisons


def compare_main_vs_baselines_c(metrics: dict) -> dict:
    """Precision-first. Speed secondary (only if precision tied within ±THRESHOLD)."""
    main_p     = metrics.get("precision_main", 0.0)
    main_speed = metrics.get("proj_speed_main")
    comparisons = {}

    for bname in metrics.get("baseline_precision", {}):
        bp     = metrics["baseline_precision"].get(bname, 0.0)
        bspeed = metrics.get("baseline_proj_speed", {}).get(bname)

        # Precision margin (higher P = better for main)
        if bp is not None and bp > 0:
            prec_margin = (main_p - bp) / bp
        elif main_p > 0 and (bp is None or bp == 0):
            prec_margin = 1.0
        else:
            prec_margin = 0.0

        # Primary decision: precision
        if prec_margin >= THRESHOLD:
            comparisons[bname] = _cr("win", "precision", prec_margin)
        elif prec_margin <= -THRESHOLD:
            comparisons[bname] = _cr("loss", "precision", prec_margin)
        else:
            # Precision tied — use speed as tiebreaker
            if main_speed is not None and bspeed is not None and bspeed > 0:
                speed_margin = (bspeed - main_speed) / bspeed
                if speed_margin >= THRESHOLD:
                    comparisons[bname] = _cr("win", "proj_speed", speed_margin)
                elif speed_margin <= -THRESHOLD:
                    comparisons[bname] = _cr("loss", "proj_speed", speed_margin)
                else:
                    comparisons[bname] = _cr("tie", "precision+speed", prec_margin)
            elif main_speed is not None and bspeed is None:
                comparisons[bname] = _cr("win", "proj_speed", 1.0)
            elif main_speed is None and bspeed is not None:
                comparisons[bname] = _cr("loss", "proj_speed", None)
            else:
                comparisons[bname] = _cr("tie", "precision", prec_margin)

    return comparisons


def compare_main_vs_baselines_d(metrics: dict) -> dict:
    """Exp D: binary success_d first, then projection speed."""
    main_success = metrics.get("success_d_main", False)
    main_speed   = metrics.get("proj_speed_main")
    comparisons  = {}

    for bname in metrics.get("baseline_success_d", {}):
        b_success = metrics["baseline_success_d"][bname]
        b_speed   = metrics.get("baseline_proj_speed", {}).get(bname)

        if main_success and not b_success:
            comparisons[bname] = _cr("win", "success_d", 1.0)
        elif not main_success and b_success:
            comparisons[bname] = _cr("loss", "success_d", None)
        elif not main_success and not b_success:
            comparisons[bname] = _cr("not_applicable", "success_d", None)
        else:
            # Both succeed — compare speed
            if main_speed is not None and b_speed is not None and b_speed > 0:
                margin = (b_speed - main_speed) / b_speed
                if margin >= THRESHOLD:
                    comparisons[bname] = _cr("win", "proj_speed", margin)
                elif margin <= -THRESHOLD:
                    comparisons[bname] = _cr("loss", "proj_speed", margin)
                else:
                    comparisons[bname] = _cr("tie", "proj_speed", margin)
            elif main_speed is not None and b_speed is None:
                comparisons[bname] = _cr("win", "proj_speed", 1.0)
            elif main_speed is None and b_speed is not None:
                comparisons[bname] = _cr("loss", "proj_speed", None)
            else:
                comparisons[bname] = _cr("tie", "success_d", 0.0)

    return comparisons
