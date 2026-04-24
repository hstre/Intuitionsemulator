"""Go/No-Go evaluation: checks all three criteria and emits a verdict."""
from __future__ import annotations
from .metrics import (
    compare_main_vs_baselines_a,
    compare_main_vs_baselines_b,
    compare_main_vs_baselines_c,
)

IMPROVEMENT_THRESHOLD = 0.20  # 20%


def _beats_all_baselines(comparisons: dict, threshold: float = IMPROVEMENT_THRESHOLD) -> bool:
    """True only if main beats EVERY baseline by >= threshold.
    None (incomparable) and 0.0 (tie) both count as failure.
    """
    return all(
        isinstance(v, float) and v >= threshold
        for v in comparisons.values()
    )


def evaluate(
    metrics_a: dict,
    metrics_b: dict,
    metrics_c: dict,
    metrics_neg: dict,
    sweep_stable: bool,
) -> dict:
    """
    Criterion 1: Main beats ALL baselines in ≥2/3 experiments by ≥20%.
    Criterion 2: Negative scenario reactivation <5% AND projection <5%.
    Criterion 3: Sweep stability (qualitative behavior stable at ±20% alpha/eta).
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
    projection_ok = metrics_neg.get("projection_rate", 1.0) < 0.05
    criterion_2 = reactivation_ok and projection_ok

    diagnostics["criterion_2"] = {
        "passed": criterion_2,
        "reactivation_rate": metrics_neg.get("reactivation_rate"),
        "projection_rate": metrics_neg.get("projection_rate"),
        "reactivation_ok": reactivation_ok,
        "projection_ok": projection_ok,
    }

    # --- Criterion 3 ---
    criterion_3 = sweep_stable
    diagnostics["criterion_3"] = {
        "passed": criterion_3,
        "all_sweep_stable": sweep_stable,
    }

    # --- Verdict: only GO requires all 3 criteria ---
    criteria_passed = sum([criterion_1, criterion_2, criterion_3])
    verdict = "GO" if criteria_passed == 3 else "NO_GO"

    failed = []
    if not criterion_1:
        failed.append(
            f"Criterion 1: Main model beats all baselines in only {beaten_count}/3 experiments "
            f"(need ≥2, each with ≥{IMPROVEMENT_THRESHOLD:.0%} margin against every baseline)"
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
            if k != "passed":
                lines.append(f"  - {k}: {v}")
        lines.append("")

    if result["failed_criteria"]:
        lines.append("### Failed Criteria Details")
        for msg in result["failed_criteria"]:
            lines.append(f"- {msg}")

    return "\n".join(lines)
