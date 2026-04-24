"""Metric extraction and main-vs-baseline comparison helpers."""
from __future__ import annotations


def extract_metrics_a(results: dict) -> dict:
    main = results.get("main", {})
    baselines = {k: v for k, v in results.items() if k != "main"}

    correct_reactivation = (
        main.get("alive_at_25", False)
        and main.get("reactivation_step") is not None
        and main.get("projection_by_45", False)
    )
    all_modes = {"main": main, **baselines}
    return {
        "correct_late_reactivation": 1 if correct_reactivation else 0,
        "avg_time_to_reactivation": main.get("reactivation_time"),
        "baseline_reactivation_times": {k: v.get("reactivation_time") for k, v in baselines.items()},
        "main_reactivated":  main.get("reactivation_step") is not None,
        "baseline_reactivated": {k: v.get("reactivation_step") is not None for k, v in baselines.items()},
        "alive_at_25":      main.get("alive_at_25", False),
        "projection_by_45": main.get("projection_by_45", False),
        "a_at_25_all":      {k: v.get("a_at_25") for k, v in all_modes.items()},
    }


def extract_metrics_b(results: dict) -> dict:
    main = results.get("main", {})
    baselines = {k: v for k, v in results.items() if k != "main"}
    return {
        "dominant_dead_step":      main.get("dominant_dead_step"),
        "false_projections_main":  main.get("false_projections", 0),
        "recovery_time_main":      main.get("recovery_time"),
        "main_recovered":          main.get("recovery_time") is not None,
        "baseline_recovery_times": {k: v.get("recovery_time") for k, v in baselines.items()},
        "baseline_recovered":      {k: v.get("recovery_time") is not None for k, v in baselines.items()},
        "baseline_false_projections": {k: v.get("false_projections", 0) for k, v in baselines.items()},
        "baseline_dominant_dead":  {k: v.get("dominant_dead_step") for k, v in baselines.items()},
    }


def extract_metrics_c(results: dict) -> dict:
    main = results.get("main", {})
    baselines = {k: v for k, v in results.items() if k != "main"}
    return {
        "reactivated_correct_main": main.get("reactivated_correct", 0),
        "unnecessary_main":         main.get("unnecessary_reactivations", 0),
        "precision_main":           main.get("precision", 0.0),
        "proj_speed_main":          main.get("proj_speed"),       # steps after step 20
        "baseline_precision":   {k: v.get("precision", 0.0) for k, v in baselines.items()},
        "baseline_proj_speed":  {k: v.get("proj_speed") for k, v in baselines.items()},
    }


def extract_metrics_negative(result: dict) -> dict:
    return {
        "reactivation_rate": result.get("reactivation_rate", 1.0),
        "projection_rate":   result.get("projection_rate", 1.0),
        "passes":            result.get("passes", False),
    }


# ---------------------------------------------------------------------------
# Comparison helpers: positive value means main is better

def compare_main_vs_baselines_a(metrics: dict) -> dict:
    """Main wins if it reactivates when baseline doesn't, or reactivates faster."""
    main_time        = metrics.get("avg_time_to_reactivation")
    main_reactivated = metrics.get("main_reactivated", False)
    comparisons = {}
    for bname, btime in metrics.get("baseline_reactivation_times", {}).items():
        b_reactivated = metrics.get("baseline_reactivated", {}).get(bname, False)
        if main_reactivated and not b_reactivated:
            comparisons[bname] = 1.0
        elif main_reactivated and b_reactivated and btime is not None and btime > 0 and main_time is not None:
            comparisons[bname] = (btime - main_time) / btime
        elif not main_reactivated and not b_reactivated:
            comparisons[bname] = 0.0
        else:
            comparisons[bname] = None
    return comparisons


def compare_main_vs_baselines_b(metrics: dict) -> dict:
    """Main wins with shorter recovery_time (lower is better)."""
    main_rt       = metrics.get("recovery_time_main")
    main_recovered = metrics.get("main_recovered", False)
    comparisons = {}
    for bname in metrics.get("baseline_recovery_times", {}):
        brt       = metrics["baseline_recovery_times"][bname]
        b_recovered = metrics.get("baseline_recovered", {}).get(bname, False)
        if main_recovered and not b_recovered:
            comparisons[bname] = 1.0
        elif main_recovered and b_recovered and main_rt is not None and brt is not None and brt > 0:
            comparisons[bname] = (brt - main_rt) / brt
        elif not main_recovered and not b_recovered:
            # Fallback: compare false_projections (fewer = better for main)
            main_fp = metrics.get("false_projections_main", 0)
            b_fp    = metrics.get("baseline_false_projections", {}).get(bname, 0)
            comparisons[bname] = (b_fp - main_fp) / b_fp if b_fp > 0 else 0.0
        else:
            comparisons[bname] = None
    return comparisons


def compare_main_vs_baselines_c(metrics: dict) -> dict:
    """Two sub-metrics: precision (higher=better) and proj_speed (lower=better)."""
    main_p     = metrics.get("precision_main", 0.0)
    main_speed = metrics.get("proj_speed_main")
    comparisons = {}

    for bname in metrics.get("baseline_precision", {}):
        bp     = metrics["baseline_precision"].get(bname, 0.0)
        bspeed = metrics.get("baseline_proj_speed", {}).get(bname)

        # Speed comparison (lower is better for main): improvement = (b-main)/b
        if main_speed is not None and bspeed is not None and bspeed > 0:
            speed_imp = (bspeed - main_speed) / bspeed
        elif main_speed is not None and bspeed is None:
            speed_imp = 1.0
        else:
            speed_imp = None

        # Precision comparison (higher=better)
        if bp is not None and bp > 0:
            prec_imp = (main_p - bp) / bp
        elif main_p > 0 and (bp is None or bp == 0):
            prec_imp = 1.0
        else:
            prec_imp = 0.0

        # Take the best of the two sub-metrics
        candidates = [v for v in [speed_imp, prec_imp] if v is not None]
        comparisons[bname] = max(candidates) if candidates else None

    return comparisons
