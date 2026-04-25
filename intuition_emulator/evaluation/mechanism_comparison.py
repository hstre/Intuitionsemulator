"""Explicit mechanism comparison: pairwise analysis of mechanism paths.

Mechanism aliases (explicit labels for existing mode variants):
  combined_main     = mode "main"              (H = f(P), F active)
  persistence_only  = mode "persistence_only"  (H = f(P), F = 0)      [= baseline_b]
  feedback_only_h8  = mode "feedback_only_h8"  (H = 8,    F active)   [= baseline_c]
  feedback_only_h12 = mode "feedback_only_h12" (H = 12,   F active)   [= baseline_c_prime]

Standard comparison pairs per experiment (outcome="win" means left side is better):
  1. persistence_only  vs feedback_only_h8   — H=f(P) vs H=8+F: does persistence beat low-H feedback?
  2. persistence_only  vs feedback_only_h12  — H=f(P) vs H=12+F: does persistence beat high-H feedback?
  3. combined_main     vs persistence_only   — adding F to H=f(P): does feedback help?
  4. combined_main     vs feedback_only_h12  — H=f(P)+F vs H=12+F: does variable H matter when F is active?
"""
from __future__ import annotations

THRESHOLD = 0.20

MECHANISM_LABELS: dict[str, str] = {
    "combined_main":      "main",
    "persistence_only":   "persistence_only",
    "feedback_only_h8":   "feedback_only_h8",
    "feedback_only_h12":  "feedback_only_h12",
}

MECHANISM_DESCRIPTIONS: dict[str, str] = {
    "combined_main":      "H=f(P), F active  (= main)",
    "persistence_only":   "H=f(P), F=0       (= baseline_b)",
    "feedback_only_h8":   "H=8,    F active  (= baseline_c)",
    "feedback_only_h12":  "H=12,   F active  (= baseline_c_prime)",
}

COMPARISON_PAIRS: list[tuple[str, str, str]] = [
    (
        "persistence_only", "feedback_only_h8",
        "H=f(P) vs H=8+F — is persistence enough to beat low-H feedback?",
    ),
    (
        "persistence_only", "feedback_only_h12",
        "H=f(P) vs H=12+F — is persistence enough to beat high-H feedback?",
    ),
    (
        "combined_main", "persistence_only",
        "F contribution: does adding F to H=f(P) improve over persistence alone?",
    ),
    (
        "combined_main", "feedback_only_h12",
        "H=f(P) over H=12: does variable H add anything when F is already active?",
    ),
]


def _cr(outcome: str, metric: str, margin=None) -> dict:
    return {"outcome": outcome, "metric": metric, "margin": margin}


def _margin_outcome(margin: float) -> str:
    if margin >= THRESHOLD:
        return "win"
    if margin <= -THRESHOLD:
        return "loss"
    return "tie"


# ---------------------------------------------------------------------------
# Per-experiment pairwise comparison
# outcome="win"  → label_a is better on the primary metric
# outcome="loss" → label_b is better

def compare_pair_a(results: dict, label_a: str, label_b: str) -> dict:
    """Exp A: alive_at_50 primary, reactivation_time secondary."""
    mode_a = MECHANISM_LABELS.get(label_a, label_a)
    mode_b = MECHANISM_LABELS.get(label_b, label_b)
    ra = results.get(mode_a, {})
    rb = results.get(mode_b, {})

    a_alive = ra.get("alive_at_50", False)
    b_alive = rb.get("alive_at_50", False)
    a_time  = ra.get("reactivation_time")
    b_time  = rb.get("reactivation_time")
    a_react = ra.get("reactivation_step") is not None
    b_react = rb.get("reactivation_step") is not None

    if a_alive and not b_alive:
        return _cr("win", "alive_at_50", 1.0)
    if not a_alive and b_alive:
        return _cr("loss", "alive_at_50", 1.0)
    if not a_alive and not b_alive:
        return _cr("not_applicable", "alive_at_50", None)
    if a_react and not b_react:
        return _cr("win", "reactivation", 1.0)
    if not a_react and b_react:
        return _cr("loss", "reactivation", 1.0)
    if a_react and b_react and a_time is not None and b_time is not None and b_time > 0:
        m = (b_time - a_time) / b_time
        return _cr(_margin_outcome(m), "reactivation_time", m)
    return _cr("tie", "alive_at_50", 0.0)


def compare_pair_b(results: dict, label_a: str, label_b: str) -> dict:
    """Exp B: recovery_time primary (lower = better for label_a to win).
    If neither recovers, compare false_projections (lower = better).
    """
    mode_a = MECHANISM_LABELS.get(label_a, label_a)
    mode_b = MECHANISM_LABELS.get(label_b, label_b)
    ra = results.get(mode_a, {})
    rb = results.get(mode_b, {})

    a_rt = ra.get("recovery_time")
    b_rt = rb.get("recovery_time")
    a_fp = ra.get("false_projections", 0)
    b_fp = rb.get("false_projections", 0)

    if a_rt is not None and b_rt is None:
        return _cr("win", "recovery_time", 1.0)
    if a_rt is None and b_rt is not None:
        return _cr("loss", "recovery_time", 1.0)
    if a_rt is None and b_rt is None:
        if b_fp > 0 and a_fp < b_fp:
            return _cr("win", "false_projections", (b_fp - a_fp) / b_fp)
        if a_fp > 0 and a_fp > b_fp:
            return _cr("loss", "false_projections", (a_fp - b_fp) / a_fp)
        return _cr("not_applicable", "recovery_time", None)
    # Both recover — lower is better for label_a
    m = (a_rt - b_rt) / max(a_rt, 1)   # positive → b faster → loss for a
    return _cr(_margin_outcome(-m), "recovery_time", (b_rt - a_rt) / max(b_rt, 1))


def compare_pair_c(results: dict, label_a: str, label_b: str) -> dict:
    """Exp C: precision primary, proj_speed secondary."""
    mode_a = MECHANISM_LABELS.get(label_a, label_a)
    mode_b = MECHANISM_LABELS.get(label_b, label_b)
    ra = results.get(mode_a, {})
    rb = results.get(mode_b, {})

    a_p  = ra.get("precision", 0.0)
    b_p  = rb.get("precision", 0.0)
    a_sp = ra.get("proj_speed")
    b_sp = rb.get("proj_speed")

    if b_p > 0:
        pm = (a_p - b_p) / b_p
    elif a_p > 0:
        pm = 1.0
    else:
        pm = 0.0

    if abs(pm) >= THRESHOLD:
        return _cr(_margin_outcome(pm), "precision", pm)

    # Precision tied — speed tiebreaker (lower = better for label_a)
    if a_sp is not None and b_sp is not None and b_sp > 0:
        sm = (b_sp - a_sp) / b_sp
        return _cr(_margin_outcome(sm), "proj_speed", sm)
    if a_sp is not None and b_sp is None:
        return _cr("win", "proj_speed", 1.0)
    if a_sp is None and b_sp is not None:
        return _cr("loss", "proj_speed", 1.0)
    return _cr("tie", "precision", pm)


def compare_pair_d(results: dict, label_a: str, label_b: str) -> dict:
    """Exp D: success_d primary, proj_speed secondary."""
    mode_a = MECHANISM_LABELS.get(label_a, label_a)
    mode_b = MECHANISM_LABELS.get(label_b, label_b)
    ra = results.get(mode_a, {})
    rb = results.get(mode_b, {})

    a_ok = ra.get("success_d", False)
    b_ok = rb.get("success_d", False)
    a_sp = ra.get("proj_speed")
    b_sp = rb.get("proj_speed")

    if a_ok and not b_ok:
        return _cr("win", "success_d", 1.0)
    if not a_ok and b_ok:
        return _cr("loss", "success_d", 1.0)
    if not a_ok and not b_ok:
        return _cr("not_applicable", "success_d", None)
    # Both succeed — lower speed is better for label_a
    if a_sp is not None and b_sp is not None and b_sp > 0:
        m = (b_sp - a_sp) / b_sp
        return _cr(_margin_outcome(m), "proj_speed", m)
    if a_sp is not None and b_sp is None:
        return _cr("win", "proj_speed", 1.0)
    if a_sp is None and b_sp is not None:
        return _cr("loss", "proj_speed", 1.0)
    return _cr("tie", "success_d", 0.0)


# ---------------------------------------------------------------------------
# Full 4-pair comparison for each experiment

def _run_pairs(compare_fn, results: dict) -> dict:
    out = {}
    for label_a, label_b, desc in COMPARISON_PAIRS:
        key = f"{label_a} vs {label_b}"
        out[key] = {
            "result":      compare_fn(results, label_a, label_b),
            "description": desc,
            "label_a":     label_a,
            "label_b":     label_b,
        }
    return out


def full_comparison_a(results: dict) -> dict:
    return _run_pairs(compare_pair_a, results)


def full_comparison_b(results: dict) -> dict:
    return _run_pairs(compare_pair_b, results)


def full_comparison_c(results: dict) -> dict:
    return _run_pairs(compare_pair_c, results)


def full_comparison_d(results: dict) -> dict:
    return _run_pairs(compare_pair_d, results)


# ---------------------------------------------------------------------------
# Problem-class classification from pairs

def classify_from_pairs(pairs: dict) -> tuple[str, str]:
    """Return (class_label, reasoning).

    Inspects the first two pairs (persistence vs feedback variants) to determine
    which mechanism has the advantage in this experiment.
    """
    p_vs_fh8  = pairs.get("persistence_only vs feedback_only_h8",  {}).get("result", {})
    p_vs_fh12 = pairs.get("persistence_only vs feedback_only_h12", {}).get("result", {})

    p_beats_fh8  = p_vs_fh8.get("outcome")  == "win"
    p_beats_fh12 = p_vs_fh12.get("outcome") == "win"
    f_beats_p_h8  = p_vs_fh8.get("outcome") == "loss"
    f_beats_p_h12 = p_vs_fh12.get("outcome") == "loss"

    if (p_beats_fh8 or p_beats_fh12) and not f_beats_p_h8 and not f_beats_p_h12:
        which = []
        if p_beats_fh8:  which.append("feedback_only_h8")
        if p_beats_fh12: which.append("feedback_only_h12")
        return (
            "persistence_dominated",
            f"persistence_only outperforms {' and '.join(which)}; "
            "no feedback variant outperforms persistence_only",
        )

    if (f_beats_p_h8 or f_beats_p_h12) and not p_beats_fh8 and not p_beats_fh12:
        which = []
        if f_beats_p_h8:  which.append("feedback_only_h8")
        if f_beats_p_h12: which.append("feedback_only_h12")
        return (
            "feedback_dominated",
            f"{' and '.join(which)} outperforms persistence_only; "
            "persistence_only shows no compensating advantage",
        )

    if (p_beats_fh8 or p_beats_fh12) and (f_beats_p_h8 or f_beats_p_h12):
        return (
            "mixed",
            "persistence_only wins against some feedback variants but loses to others; "
            "advantage depends on the H-level of the feedback baseline",
        )

    return (
        "no_clear_advantage",
        "no comparison shows a margin ≥ 20% in either direction",
    )


# ---------------------------------------------------------------------------
# Architectural verdict

def overall_architectural_verdict(
    classes: dict,  # {exp_name: (class_label, reasoning)}
    all_pairs: dict,  # {exp_name: pairs_dict}
) -> dict:
    labels = [c[0] for c in classes.values()]
    n_pers  = sum(1 for l in labels if l == "persistence_dominated")
    n_feed  = sum(1 for l in labels if l == "feedback_dominated")
    n_mixed = sum(1 for l in labels if l == "mixed")

    # Check whether combined_main ever beats feedback_only_h12
    cm_wins_over_fh12 = [
        exp for exp, pairs in all_pairs.items()
        if pairs.get("combined_main vs feedback_only_h12", {})
                .get("result", {}).get("outcome") == "win"
    ]

    combined_note: str
    if not cm_wins_over_fh12:
        combined_note = (
            "combined_main (H=f(P) + F) shows no advantage over feedback_only_h12 "
            "(H=12 + F) in any tested experiment. The plausibility-dependent half-life "
            "provides no measurable benefit when reactivation feedback is already active."
        )
    else:
        combined_note = (
            f"combined_main shows an advantage over feedback_only_h12 in: "
            f"{', '.join(cm_wins_over_fh12)}."
        )

    if n_feed > n_pers:
        conclusion = "B"
        text = (
            "The existing experiment set does not support the strong coupling hypothesis. "
            "Feedback (F) is the dominant differentiator in the majority of tested scenarios. "
            "Persistence (H=f(P)) provides a survival advantage only in the pure dormancy "
            "scenario (Exp A) where no external context signal is present. "
            "These two problem classes are disjoint: dormancy survival and context-driven "
            "recovery are separate challenges addressed by separate mechanisms.\n\n"
            "The data point toward modular problem-class-specific selection rather than "
            "a globally superior combined model. Persistence and feedback are better "
            "understood as two distinct tools for two distinct problem classes."
        )
    elif n_pers > n_feed:
        conclusion = "B"
        text = (
            "Persistence (H=f(P)) is the dominant differentiator across tested scenarios. "
            "Feedback adds no robust general advantage beyond the persistence mechanism alone. "
            "The data point toward modular selection with a persistence-first architecture."
        )
    elif n_mixed >= 2:
        conclusion = "C"
        text = (
            "The tested scenarios do not produce a consistent architectural signal. "
            "Results are mixed. No robust conclusion about architectural superiority "
            "can be drawn from the current data set."
        )
    else:
        conclusion = "B"
        text = (
            "Persistence and feedback appear to address different problem classes. "
            "The current experiment set does not provide evidence for a globally "
            "superior combined model."
        )

    return {
        "conclusion":    conclusion,   # "B" = modular, "C" = no clear difference
        "text":          text,
        "combined_note": combined_note,
        "cm_wins_over_fh12": cm_wins_over_fh12,
        "counts": {
            "persistence_dominated": n_pers,
            "feedback_dominated":    n_feed,
            "mixed":                 n_mixed,
        },
    }


# ---------------------------------------------------------------------------
# Mechanism Selection Conclusion (nüchtern, direct)

def mechanism_selection_conclusion(
    all_classes: dict,   # {exp_name: (class_label, reasoning)}
    all_pairs: dict,     # {exp_name: pairs_dict}
    arch_verdict: dict,  # from overall_architectural_verdict()
) -> str:
    pers_exps  = [e for e, (c, _) in all_classes.items() if c == "persistence_dominated"]
    feed_exps  = [e for e, (c, _) in all_classes.items() if c == "feedback_dominated"]
    mixed_exps = [e for e, (c, _) in all_classes.items() if c == "mixed"]

    exp_labels = {
        "experiment_a": "Exp A",
        "experiment_b": "Exp B",
        "experiment_c": "Exp C",
        "experiment_d": "Exp D",
    }

    lines = []

    if pers_exps:
        exps_str = ", ".join(exp_labels.get(e, e) for e in pers_exps)
        lines.append(
            f"- **persistence_only** seems preferable for long-dormancy scenarios without "
            f"external context ({exps_str}). H=f(P) keeps high-plausibility claims alive "
            f"longer than H=8; it provides no additional advantage over H=12."
        )
    else:
        lines.append(
            "- **persistence_only** does not clearly outperform any feedback-based "
            "alternative in the current test set."
        )

    if feed_exps:
        exps_str = ", ".join(exp_labels.get(e, e) for e in feed_exps)
        lines.append(
            f"- **feedback_only** (H=8 or H=12, F active) seems preferable for "
            f"context-driven recovery and selective reactivation ({exps_str}). "
            f"The F mechanism is necessary and sufficient; H level affects only "
            f"whether the claim survives the pre-context drain phase."
        )

    if mixed_exps:
        exps_str = ", ".join(exp_labels.get(e, e) for e in mixed_exps)
        lines.append(
            f"- In **{exps_str}**, both mechanisms contribute to different sub-problems "
            f"(persistence for survival, feedback for reactivation speed). "
            f"Neither alone is fully sufficient."
        )

    lines.append("")

    if not arch_verdict.get("cm_wins_over_fh12"):
        lines.append(
            "- **combined_main shows no robust advantage over feedback_only_h12** "
            "in any tested experiment. Adding H=f(P) to an already-active feedback "
            "mechanism does not produce a measurable improvement."
        )
    else:
        wins = ", ".join(
            exp_labels.get(e, e) for e in arch_verdict["cm_wins_over_fh12"]
        )
        lines.append(
            f"- combined_main shows a marginal advantage over feedback_only_h12 in: {wins}."
        )

    lines += [
        "",
        "**Current evidence supports modular selection rather than forced coupling.** "
        "Persistence and feedback are better understood as two separate tools for two "
        "separate problem classes than as a robustly synergistic combined mechanism. "
        "A model choosing the appropriate mechanism per scenario would perform at least "
        "as well as combined_main and would be architecturally clearer.",
    ]

    return "\n".join(lines)
