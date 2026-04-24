"""Go/No-Go evaluation: checks all criteria and emits a verdict."""
from __future__ import annotations
from .metrics import (
    compare_main_vs_baselines_a,
    compare_main_vs_baselines_b,
    compare_main_vs_baselines_c,
    compare_main_vs_baselines_d,
)

IMPROVEMENT_THRESHOLD = 0.20  # 20%


def _beats_all_baselines(comparisons: dict) -> bool:
    """True only if main wins against EVERY baseline. Tie or not_applicable = failure."""
    return all(
        isinstance(comp, dict) and comp.get("outcome") == "win"
        for comp in comparisons.values()
    )


def evaluate(
    metrics_a: dict,
    metrics_b: dict,
    metrics_c: dict,
    metrics_neg: dict,
    sweep_stable: bool,
    metrics_d: dict | None = None,
) -> dict:
    """
    Criterion 1: Main beats ALL baselines in >=2/3 core experiments (A, B, C) by outcome='win'.
    Criterion 2: Negative scenario reactivation <5% AND projection <5%.
    Criterion 3: Sweep stability (qualitative behavior stable at ±20% alpha/eta).
    Experiment D is diagnostic only — not part of the core GO/NO-GO criteria.
    """
    diagnostics = {}

    # --- Criterion 1 ---
    comp_a = compare_main_vs_baselines_a(metrics_a)
    comp_b = compare_main_vs_baselines_b(metrics_b)
    comp_c = compare_main_vs_baselines_c(metrics_c)

    exp_a_beats = _beats_all_baselines(comp_a)
    exp_b_beats = _beats_all_baselines(comp_b)
    exp_c_beats = _beats_all_baselines(comp_c)

    beaten_count = sum([exp_a_beats, exp_b_beats, exp_c_beats])
    criterion_1 = beaten_count >= 2

    diagnostics["criterion_1"] = {
        "passed": criterion_1,
        "experiments_beaten": beaten_count,
        "exp_a_beats_all_baselines": exp_a_beats,
        "exp_b_beats_all_baselines": exp_b_beats,
        "exp_c_beats_all_baselines": exp_c_beats,
        "comparisons_a": comp_a,
        "comparisons_b": comp_b,
        "comparisons_c": comp_c,
    }

    # --- Criterion 2 ---
    reactivation_ok = metrics_neg.get("reactivation_rate", 1.0) < 0.05
    projection_ok   = metrics_neg.get("projection_rate", 1.0) < 0.05
    criterion_2     = reactivation_ok and projection_ok

    diagnostics["criterion_2"] = {
        "passed": criterion_2,
        "reactivation_rate": metrics_neg.get("reactivation_rate"),
        "projection_rate":   metrics_neg.get("projection_rate"),
        "reactivation_ok":   reactivation_ok,
        "projection_ok":     projection_ok,
    }

    # --- Criterion 3 ---
    criterion_3 = sweep_stable
    diagnostics["criterion_3"] = {
        "passed": criterion_3,
        "all_sweep_stable": sweep_stable,
    }

    # --- Experiment D diagnostic (not a criterion) ---
    if metrics_d is not None:
        comp_d = compare_main_vs_baselines_d(metrics_d)
        d_beats = _beats_all_baselines(comp_d)
        diagnostics["exp_d_diagnostic"] = {
            "combination_effect_found": d_beats,
            "comparisons_d": comp_d,
            "main_success_d": metrics_d.get("success_d_main", False),
            "baseline_success_d": metrics_d.get("baseline_success_d", {}),
        }

    # --- Verdict: GO only if all 3 criteria pass ---
    criteria_passed = sum([criterion_1, criterion_2, criterion_3])
    verdict = "GO" if criteria_passed == 3 else "NO_GO"

    failed = []
    if not criterion_1:
        failed.append(
            f"Criterion 1: Main model beats all baselines in only {beaten_count}/3 experiments "
            f"(need >=2, each with outcome='win' against every baseline)"
        )
    if not criterion_2:
        failed.append(
            f"Criterion 2: Negative scenario rates too high "
            f"(reactivation={metrics_neg.get('reactivation_rate', '?'):.1%}, "
            f"projection={metrics_neg.get('projection_rate', '?'):.1%})"
        )
    if not criterion_3:
        failed.append("Criterion 3: Parameter sweep unstable (qualitative behavior changes)")

    return {
        "verdict": verdict,
        "criteria_passed": criteria_passed,
        "failed_criteria": failed,
        "diagnostics": diagnostics,
    }


def format_verdict(result: dict) -> str:
    lines = [
        f"## Go/No-Go Verdict: **{result['verdict']}**",
        f"Criteria passed: {result['criteria_passed']}/3",
        "",
    ]
    diag = result["diagnostics"]

    for key in ["criterion_1", "criterion_2", "criterion_3"]:
        d = diag[key]
        status = "✓ PASS" if d["passed"] else "✗ FAIL"
        lines.append(f"### {key.replace('_', ' ').title()} – {status}")
        for k, v in d.items():
            if k == "passed":
                continue
            if isinstance(v, dict):
                lines.append(f"  - {k}:")
                for bname, comp in v.items():
                    if isinstance(comp, dict):
                        lines.append(
                            f"    - {bname}: outcome={comp.get('outcome')} "
                            f"metric={comp.get('metric')} margin={comp.get('margin')}"
                        )
                    else:
                        lines.append(f"    - {bname}: {comp}")
            else:
                lines.append(f"  - {k}: {v}")
        lines.append("")

    # Experiment D diagnostic
    if "exp_d_diagnostic" in diag:
        d = diag["exp_d_diagnostic"]
        effect = "FOUND" if d.get("combination_effect_found") else "NOT FOUND"
        lines.append(f"### Experiment D Diagnostic – Combination Effect: **{effect}**")
        lines.append(f"  - main success_d: {d.get('main_success_d')}")
        for bname, ok in d.get("baseline_success_d", {}).items():
            comp = d.get("comparisons_d", {}).get(bname, {})
            lines.append(
                f"  - {bname}: success={ok} outcome={comp.get('outcome')} "
                f"metric={comp.get('metric')} margin={comp.get('margin')}"
            )
        lines.append("")

    if result["failed_criteria"]:
        lines.append("### Failed Criteria Details")
        for msg in result["failed_criteria"]:
            lines.append(f"- {msg}")

    return "\n".join(lines)
