"""Problem class analysis: classifies each experiment by which mechanism dominates.

Classification vocabulary:
  persistence_dominated  – persistence_only wins all comparisons vs feedback_only variants
  feedback_dominated     – feedback_only wins all comparisons vs persistence_only
  mixed                  – split results (persistence wins some, feedback wins others)
  no_clear_advantage     – all comparisons tied or not applicable
"""
from __future__ import annotations


def classify_experiment(p_vs_f_comp: dict) -> str:
    """Return class label for one experiment given its persistence-vs-feedback comparisons."""
    outcomes = [c.get("outcome", "no_advantage") for c in p_vs_f_comp.values()]
    p_wins = sum(1 for o in outcomes if o == "persistence_wins")
    f_wins = sum(1 for o in outcomes if o == "feedback_wins")
    n = len(outcomes)

    if n == 0:
        return "no_clear_advantage"
    if p_wins > 0 and f_wins > 0:
        return "mixed"
    if p_wins > 0:
        return "persistence_dominated"
    if f_wins > 0:
        return "feedback_dominated"
    return "no_clear_advantage"


def analyze_all_experiments(
    p_vs_f_a: dict,
    p_vs_f_b: dict,
    p_vs_f_c: dict,
    p_vs_f_d: dict,
) -> dict:
    """Classify all four experiments and produce a summary."""
    classes = {
        "experiment_a": classify_experiment(p_vs_f_a),
        "experiment_b": classify_experiment(p_vs_f_b),
        "experiment_c": classify_experiment(p_vs_f_c),
        "experiment_d": classify_experiment(p_vs_f_d),
    }

    counts = {
        "persistence_dominated": sum(1 for v in classes.values() if v == "persistence_dominated"),
        "feedback_dominated":    sum(1 for v in classes.values() if v == "feedback_dominated"),
        "mixed":                 sum(1 for v in classes.values() if v == "mixed"),
        "no_clear_advantage":    sum(1 for v in classes.values() if v == "no_clear_advantage"),
    }

    if counts["persistence_dominated"] > counts["feedback_dominated"]:
        overall = "persistence_dominated"
    elif counts["feedback_dominated"] > counts["persistence_dominated"]:
        overall = "feedback_dominated"
    elif counts["mixed"] > 0:
        overall = "mixed"
    else:
        overall = "no_clear_advantage"

    return {
        "classes": classes,
        "counts": counts,
        "overall": overall,
        "comparisons": {
            "experiment_a": p_vs_f_a,
            "experiment_b": p_vs_f_b,
            "experiment_c": p_vs_f_c,
            "experiment_d": p_vs_f_d,
        },
    }
