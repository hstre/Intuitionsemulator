#!/usr/bin/env python3
"""
run_all.py – Orchestrates all experiments and generates report.md.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from intuition_emulator.core.system import load_params
from intuition_emulator.experiments.stability_check import run_stability_check, run_parameter_sweep
from intuition_emulator.experiments.experiment_a import run_experiment_a
from intuition_emulator.experiments.experiment_b import run_experiment_b
from intuition_emulator.experiments.experiment_c import run_experiment_c
from intuition_emulator.experiments.experiment_d import run_experiment_d
from intuition_emulator.experiments.negative_scenario import run_negative_scenario
from intuition_emulator.evaluation.metrics import (
    extract_metrics_a, extract_metrics_b, extract_metrics_c,
    extract_metrics_d, extract_metrics_negative,
)
from intuition_emulator.evaluation.go_no_go import evaluate, format_verdict
from intuition_emulator.evaluation.mechanism_comparison import (
    full_comparison_a, full_comparison_b, full_comparison_c, full_comparison_d,
    classify_from_pairs, overall_architectural_verdict,
    mechanism_selection_conclusion as make_mech_selection_text,
    MECHANISM_DESCRIPTIONS,
)

OUTPUT_DIR = Path(__file__).parent / "output"

_SECTION_0 = """\
## 0. Zusammenfassung der Iterationen

Dieser Prototyp wurde in vier Durchläufen entwickelt:

**Durchlauf 1:** Erster Aufbau mit 25 Schritten Totzeit in Experiment A
(später als zu kurz erkannt). Go/No-Go-Logik nutzte `any()` statt `all()`.

**Durchlauf 2:** Bewertungslogik verschärft (success_a binär, Experiment B
lexikographisch). Experiment A auf echte 25-Schritt-Totzeit umgebaut.

**Durchlauf 3:** Go/No-Go-Logik korrekt mit `all()`. Baselines A' und C' mit
H=12 als Robustheitstest. Diagnostischer Befund zur disjunkten Wirkung der
beiden Modellkomponenten hinzugefügt. Ehrliches NO-GO-Verdikt.

**Durchlauf 4:** Experiment A auf 50-Schritt-Totzeit mit E=0.01
(physikalisch korrekte Diskriminierung). ComparisonResult-Schema eingeführt
(outcome/metric/margin statt roher Floats). Verifier-Logik graduiert (Hard
Reject erst nach 3 konsekutiven V=-1 oder A<0.3). Experiment D als
Kombinationseffekt-Test neu hinzugefügt. Verdikt bleibt NO-GO.

**Durchlauf 5:** Persistenz- und Feedback-Mechanismus als separate
Vergleichsmodi (`persistence_only`, `feedback_only_h8`, `feedback_only_h12`)
parallel zu allen Experimenten ausgeführt.

**Durchlauf 6 (dieser):** Mechanismenvergleich sauber explizit gemacht.
Aliase dokumentiert (combined_main/persistence_only/feedback_only_h*/…).
Neues Modul `mechanism_comparison.py` mit vollständiger 4-Paar-Analyse pro
Experiment. Abschnitte 8–11 ersetzen die alten Sections durch explizite
Mechanismus-Sektionen mit architektonischer Gesamtinterpretation und
nüchterner Mechanism-Selection-Conclusion. Keine neuen Experimente.

---
"""

_SECTION_7 = """\
## 7. Diagnostischer Befund

### 7.1 Halbwertszeit wirkt in Experiment A

In Experiment A (50 Schritte Totzeit, E=0.01) überleben Hauptmodell und
Baseline B (H=f(P)≈10.8, kein Feedback), während Baselines A und C (H=8)
bei Schritt ~36 verworfen werden. A*-Gleichgewicht: H=8→0.060, H=10.8→0.081,
H=12→0.089. Der Effekt ist real aber nicht einzigartig: H=12 (A'/C') erzielt
denselben Outcome.

### 7.2 Feedback wirkt in Experimenten B und C

In Experiment B (falscher Dominator) und Experiment C (selektive Reaktivierung)
sind Hauptmodell, Baseline C (H=8, F) und Baseline C' (H=12, F) äquivalent.
Baselines A, B, A' (kein Feedback) schlagen fehl.

### 7.3 Kein nachweisbarer Kombinationseffekt in Experimenten A–C

In keinem der drei Kernexperimente schlägt das Hauptmodell gleichzeitig
Baseline B und Baseline C. Die Mechanismen wirken in disjunkten Szenarien.

### 7.4 Experiment D: Kombinationseffekt-Test (Langzeit-Kette)

Experiment D testet, ob der Kombinationseffekt auf längeren Zeitskalen (120
Schritte, späte Kontextaktivierung ab Schritt 80) erscheint. Ein Claim muss
sowohl 40 Schritte Totzeit überleben (H-Test) als auch reaktiviert werden (F-Test).

Ergebnis (proj_speed = Schritte bis Projektion nach Kontextstart):
- Hauptmodell: proj_speed=1 (F liefert sofortige Reaktivierung)
- Baseline B (H=f(P), kein F): proj_speed=2 — überlebt Totzeit, reaktiviert sich
  langsamer via K+E. F gibt dem Hauptmodell einen Geschwindigkeitsvorteil (50%).
- Baseline A' (H=12, kein F): proj_speed=2 — identisch zu Baseline B.
- Baseline C' (H=12, mit F): proj_speed=1 — gleich schnell wie Hauptmodell.

Befund: F liefert gegenüber Baselines ohne F einen messbaren Geschwindigkeits-
vorteil (1 Schritt = 50% margin > 20%-Schwelle). Aber Baseline C' (H=12+F)
erzielt denselben Outcome wie das Hauptmodell. Die plausibilitätsabhängige
Halbwertszeit leistet keinen zusätzlichen Beitrag über H=12+F hinaus. Das
Hauptmodell schlägt Baselines A, B, C, A' — aber nicht C' — in Experiment D.
Da _beats_all_baselines_ alle gewinnen muss, wird kein Kombinationseffekt
registriert. Ergebnis bleibt NO-GO.

**Konsequenz:** Die ursprüngliche Hypothese — dass die Kombination aus
plausibilitätsabhängiger Halbwertszeit und selektiver Reaktivierung mehr
leistet als die Einzelkomponenten — wird durch alle vier Experimente nicht
gestützt. Die Mechanismen sind orthogonal für verschiedene Aufgabenklassen.

### 7.5 Mögliche Ursachen

1. Die Kombinationswirkung existiert, wird aber von den gewählten Experimenten
   nicht getestet. Ein Experiment mit höherem Rauschen, stärkerem Verifier-
   Druck oder mehreren konkurrierenden Kontext-Claims fehlt im Testaufbau.

2. Die Kombinationswirkung existiert nicht. H und F sind orthogonale Mechanismen
   und sollten im Zielmodell modular getrennt werden.

3. Die Parameterwahl maskiert den synergistischen Effekt. Mit anderen w1-w5,
   r1-r5 oder theta_reactivate-Werten könnte der Effekt messbar sein.

Welche der drei Interpretationen zutrifft, kann dieser Prototyp nicht
entscheiden.
"""


def _fmt(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:.3f}"
    if isinstance(val, bool):
        return "✓" if val else "✗"
    return str(val)


def _fmt_cr(comp: dict) -> str:
    if not isinstance(comp, dict):
        return str(comp)
    outcome = comp.get("outcome", "?")
    metric  = comp.get("metric", "?")
    margin  = comp.get("margin")
    m_str   = f"{margin:.2f}" if isinstance(margin, float) else "—"
    symbol  = {"win": "✓", "loss": "✗", "tie": "~", "not_applicable": "n/a"}.get(outcome, "?")
    return f"{symbol} {outcome} ({metric}, Δ={m_str})"


def build_report(
    stability_result: dict,
    sweep_result: dict,
    exp_a: dict,
    exp_b: dict,
    exp_c: dict,
    exp_d: dict,
    neg: dict,
    metrics_a: dict,
    metrics_b: dict,
    metrics_c: dict,
    metrics_d: dict,
    metrics_neg: dict,
    verdict_result: dict,
    mech_pairs: dict | None = None,      # {exp_name: full_comparison_X result}
    mech_classes: dict | None = None,    # {exp_name: (class_label, reasoning)}
    arch_verdict: dict | None = None,    # overall_architectural_verdict result
    mech_selection_text: str | None = None,
) -> str:
    from intuition_emulator.evaluation.metrics import (
        compare_main_vs_baselines_a,
        compare_main_vs_baselines_b,
        compare_main_vs_baselines_c,
        compare_main_vs_baselines_d,
    )

    lines = [
        "# Intuitionsemulator – Forschungsprototyp Bericht",
        "",
        _SECTION_0,
        "## 1. Stabilitätsprüfung",
        "",
        "### 1.1 Konvergenztests (200 Schritte, feste Inputs)",
        "",
        "| Claim | Konvergiert? |",
        "|-------|-------------|",
    ]
    for cid, res in stability_result["claim_results"].items():
        lines.append(f"| {cid} | {_fmt(res['converged'])} |")

    lines += [
        "",
        f"![Stabilitätsprüfung]({stability_result['plot']})",
        "",
        "### 1.2 Parameter-Sweep (α × η)",
        "",
        f"Alle Kombinationen stabil: **{_fmt(sweep_result['all_stable'])}**",
        "",
        f"![Parameter-Sweep]({sweep_result['plot']})",
        "",
        "---",
        "",
        "## 2. Experiment A – H=f(P)-Diskriminierung (50-Schritt-Totzeit, E=0.01)",
        "",
        "**Erfolgsdefinition:** Hauptmodell überlebt Totzeit (alive_at_50) UND",
        "reaktiviert sich im Fenster 50-70 UND projiziert bis Schritt 80.",
        "Baselines A/C: H=const=8.0 · Baselines A'/C': H=const=12.0 (Robustheitstest)",
        "",
        "| Modus | Lebt bei t=50 | A bei t=50 | Reaktivierung Schritt | Projektion Schritt | Projektion bis t=80 |",
        "|-------|:------------:|:---------:|:--------------------:|:-----------------:|:-------------------:|",
    ]
    for mode, res in exp_a["results"].items():
        lines.append(
            f"| {mode} | {_fmt(res.get('alive_at_50'))} | "
            f"{_fmt(res.get('a_at_50'))} | "
            f"{_fmt(res.get('reactivation_step'))} | "
            f"{_fmt(res.get('projection_step'))} | "
            f"{_fmt(res.get('projection_by_80'))} |"
        )

    comp_a = compare_main_vs_baselines_a(metrics_a)
    a50_rows = metrics_a.get("a_at_50_all", {})
    a50_table = " | ".join(
        f"{m}: {v:.4f}" if v is not None else f"{m}: —"
        for m, v in a50_rows.items()
    )
    lines += [
        "",
        f"![Experiment A]({exp_a['plot']})",
        "",
        "**Schlüsselmetriken:**",
        f"- Korrekte Reaktivierung (Hauptmodell): {_fmt(metrics_a['correct_late_reactivation'])}",
        f"- Zeit bis Reaktivierung: {_fmt(metrics_a['avg_time_to_reactivation'])} Schritte",
        f"- A-Werte bei Schritt 50 (Diskriminierung): {a50_table}",
        "",
        "**Vergleich Hauptmodell vs. Baselines:**",
        "",
        "| Baseline | Ergebnis |",
        "|----------|---------|",
    ]
    for bname, comp in comp_a.items():
        lines.append(f"| {bname} | {_fmt_cr(comp)} |")

    lines += [
        "",
        "---",
        "",
        "## 3. Experiment B – Falscher Dominator + History-basierte Erholung",
        "",
        "**Erfolgsdefinition:** Hauptmodell gewinnt gegen alle Baselines in",
        "mindestens einer der drei Metriken (dominant_dead, false_proj, recovery_time)",
        "um ≥20%, ohne in einer anderen Metrik >20% schlechter zu sein.",
        "",
        "| Modus | Dominator verworfen Schritt | Falsche Projektionen | Erholungszeit |",
        "|-------|:-------------------------:|:-------------------:|:------------:|",
    ]
    for mode, res in exp_b["results"].items():
        lines.append(
            f"| {mode} | {_fmt(res.get('dominant_dead_step'))} | "
            f"{_fmt(res.get('false_projections'))} | "
            f"{_fmt(res.get('recovery_time'))} |"
        )

    comp_b = compare_main_vs_baselines_b(metrics_b)
    lines += [
        "",
        f"![Experiment B]({exp_b['plot']})",
        "",
        "**Vergleich Hauptmodell vs. Baselines:**",
        "",
        "| Baseline | Ergebnis |",
        "|----------|---------|",
    ]
    for bname, comp in comp_b.items():
        lines.append(f"| {bname} | {_fmt_cr(comp)} |")

    lines += [
        "",
        "---",
        "",
        "## 4. Experiment C – Selektive Reaktivierung",
        "",
        "**Erfolgsdefinition:** Hauptmodell gewinnt primär durch höhere Präzision (≥20%",
        "besser). Geschwindigkeit nur als Tiebreaker, wenn Präzision gebunden (±20%).",
        "",
        "| Modus | Korrekte Reaktivierungen | Unnötige | Präzision | Proj.-Geschwindigkeit |",
        "|-------|:-----------------------:|:-------:|:--------:|:--------------------:|",
    ]
    for mode, res in exp_c["results"].items():
        lines.append(
            f"| {mode} | {_fmt(res.get('reactivated_correct'))} | "
            f"{_fmt(res.get('unnecessary_reactivations'))} | "
            f"{_fmt(res.get('precision'))} | "
            f"{_fmt(res.get('proj_speed'))} |"
        )

    comp_c = compare_main_vs_baselines_c(metrics_c)
    lines += [
        "",
        f"![Experiment C]({exp_c['plot']})",
        "",
        "**Vergleich Hauptmodell vs. Baselines:**",
        "",
        "| Baseline | Ergebnis |",
        "|----------|---------|",
    ]
    for bname, comp in comp_c.items():
        lines.append(f"| {bname} | {_fmt_cr(comp)} |")

    lines += [
        "",
        "---",
        "",
        "## 5. Negativszenario – Reines Rauschen",
        "",
        "| Metrik | Wert | OK? |",
        "|--------|------|-----|",
        f"| Reaktivierungsrate | {metrics_neg['reactivation_rate']:.1%} | {_fmt(metrics_neg['reactivation_rate'] < 0.05)} |",
        f"| Projektionsrate | {metrics_neg['projection_rate']:.1%} | {_fmt(metrics_neg['projection_rate'] < 0.05)} |",
        "",
        f"![Negativszenario]({neg['plot']})",
        "",
        "---",
        "",
        "## 6. Go/No-Go Entscheidung",
        "",
        format_verdict(verdict_result),
        "",
        "---",
        "",
        "## 7. Experiment D – Kombinationseffekt-Test (Langzeit-Kette)",
        "",
        "**Design:** 4 Claims (target, dominant, distractor, support), 120 Schritte,",
        "späte Kontextaktivierung ab Schritt 80. Target muss 40 Schritte Totzeit",
        "überleben (H-Test) UND dann durch Feedback reaktiviert werden (F-Test).",
        "",
        "**Erfolgsbedingungen (success_d):** alle 5 müssen erfüllt sein:",
        "1. target nicht verworfen bei t=79",
        "2. target kein Frühprojekt vor t=80",
        "3. dominant.A < theta_active bei t=79",
        "4. target reaktiviert sich ab Schritt 80",
        "5. target projiziert bis Schritt 110",
        "",
        "| Modus | success_d | A target@79 | A dominant@79 | Reaktiv. Schritt | Proj. Schritt |",
        "|-------|:---------:|:-----------:|:-------------:|:----------------:|:------------:|",
    ]
    for mode, res in exp_d["results"].items():
        lines.append(
            f"| {mode} | {_fmt(res.get('success_d'))} | "
            f"{_fmt(res.get('a_target_at_dormancy'))} | "
            f"{_fmt(res.get('a_dominant_at_dormancy'))} | "
            f"{_fmt(res.get('reactivation_step'))} | "
            f"{_fmt(res.get('proj_step'))} |"
        )

    comp_d = compare_main_vs_baselines_d(metrics_d)
    lines += [
        "",
        f"![Experiment D]({exp_d['plot']})",
        "",
        "**Vergleich Hauptmodell vs. Baselines:**",
        "",
        "| Baseline | Ergebnis |",
        "|----------|---------|",
    ]
    for bname, comp in comp_d.items():
        lines.append(f"| {bname} | {_fmt_cr(comp)} |")

    lines += [
        "",
        "---",
        "",
        _SECTION_7,
    ]

    # --- Sections 8–11: Explicit mechanism comparison ---
    if mech_pairs is not None and mech_classes is not None and arch_verdict is not None:
        _exp_meta = {
            "experiment_a": ("Experiment A – Long Dormancy (Persistence Test)",
                             "Primary metric: alive_at_50 (survival after 50 steps at E=0.01). "
                             "Secondary: reactivation speed after context arrives."),
            "experiment_b": ("Experiment B – False Dominant Recovery (Feedback Test)",
                             "Primary metric: recovery_time (steps from dominant death to correct "
                             "projection). Tests whether F enables history-based reactivation."),
            "experiment_c": ("Experiment C – Selective Reactivation (Selectivity Test)",
                             "Primary metric: precision (correct / total reactivations). "
                             "Tests whether F selectively reactivates only the high-history claim."),
            "experiment_d": ("Experiment D – Long-Chain Reactivation (Combined Scenario)",
                             "Primary metric: success_d (5 conditions). "
                             "Secondary: proj_speed. Tests combined dormancy + context reactivation."),
        }
        _sym = {"win": "✓", "loss": "✗", "tie": "~", "not_applicable": "n/a"}

        lines += [
            "",
            "---",
            "",
            "## Mechanism Comparison: Persistence vs Feedback",
            "",
            "This section compares mechanism paths directly using existing experiment data.",
            "No new experiments. Mode aliases:",
            "",
            "| Label | H | F | Equivalent baseline |",
            "|-------|---|---|---------------------|",
        ]
        for label, desc in MECHANISM_DESCRIPTIONS.items():
            # desc format: "H=f(P), F active  (= main)" — split at first comma and last paren
            parts = desc.split(",", 1)
            h_part = parts[0].strip()
            rest   = parts[1].strip() if len(parts) > 1 else ""
            f_part = rest.split("(")[0].strip()
            eq_part = ("(" + rest.split("(", 1)[1]) if "(" in rest else ""
            lines.append(f"| `{label}` | {h_part} | {f_part} | {eq_part} |")

        lines += [
            "",
            "Standard comparison pairs (outcome=win means left side is better):",
            "",
        ]
        for la, lb, desc in [
            ("persistence_only", "feedback_only_h8",
             "H=f(P) vs H=8+F — does persistence beat low-H feedback?"),
            ("persistence_only", "feedback_only_h12",
             "H=f(P) vs H=12+F — does persistence beat high-H feedback?"),
            ("combined_main",    "persistence_only",
             "F contribution: does adding F to H=f(P) improve over persistence alone?"),
            ("combined_main",    "feedback_only_h12",
             "H=f(P) over H=12: does variable H add anything when F is already active?"),
        ]:
            lines.append(f"- **{la} vs {lb}**: {desc}")
        lines.append("")

        for exp_key, pairs in mech_pairs.items():
            title, context = _exp_meta.get(exp_key, (exp_key, ""))
            cls_label, cls_reason = mech_classes.get(exp_key, ("?", ""))
            lines += [
                f"### {title}",
                "",
                context,
                "",
                "| Comparison | Outcome | Metric | Δ |",
                "|---|---|---|---|",
            ]
            for pair_key, pair_info in pairs.items():
                cr      = pair_info["result"]
                outcome = cr.get("outcome", "?")
                metric  = cr.get("metric", "?")
                margin  = cr.get("margin")
                m_str   = f"{margin:.2f}" if isinstance(margin, float) else "—"
                sym     = _sym.get(outcome, "?")
                lines.append(
                    f"| {pair_key} | {sym} `{outcome}` | {metric} | {m_str} |"
                )
            lines += [
                "",
                f"**Class: `{cls_label}`** — {cls_reason}",
                "",
            ]

        lines += [
            "---",
            "",
            "## Problem-Class Interpretation",
            "",
            "| Experiment | Class | Basis |",
            "|---|---|---|",
        ]
        for exp_key, (cls_label, cls_reason) in mech_classes.items():
            exp_short = _exp_meta.get(exp_key, (exp_key,))[0].split("–")[0].strip()
            lines.append(f"| {exp_short} | `{cls_label}` | {cls_reason} |")

        lines += [
            "",
            "Distribution: "
            + ", ".join(
                f"{k}: {v}"
                for k, v in arch_verdict["counts"].items()
                if v > 0
            ),
            "",
            "---",
            "",
            "## Overall Architectural Interpretation",
            "",
            arch_verdict["text"],
            "",
            arch_verdict["combined_note"],
            "",
            "---",
            "",
            "## Mechanism Selection Conclusion",
            "",
            mech_selection_text or "",
        ]

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Intuitionsemulator – Vollständiger Durchlauf (Durchlauf 6)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    params = load_params()

    print("\n[1/8] Stabilitätsprüfung...")
    stability_result = run_stability_check(params, OUTPUT_DIR)
    print(f"      Konvergenz: {stability_result['claim_results']}")

    print("[2/8] Parameter-Sweep...")
    sweep_result = run_parameter_sweep(params, OUTPUT_DIR)
    print(f"      Alle stabil: {sweep_result['all_stable']}")

    print("[3/8] Experiment A (50-Schritt-Totzeit, E=0.01)...")
    exp_a = run_experiment_a(params, OUTPUT_DIR)
    for mode, res in exp_a["results"].items():
        print(f"      {mode}: alive@50={res['alive_at_50']} A@50={res['a_at_50']:.4f} "
              f"reakt={res['reactivation_step']} proj={res['projection_step']}")

    print("[4/8] Experiment B...")
    exp_b = run_experiment_b(params, OUTPUT_DIR)
    for mode, res in exp_b["results"].items():
        print(f"      {mode}: dom_dead={res['dominant_dead_step']} "
              f"false_proj={res['false_projections']} recovery={res['recovery_time']}")

    print("[5/8] Experiment C...")
    exp_c = run_experiment_c(params, OUTPUT_DIR)
    for mode, res in exp_c["results"].items():
        print(f"      {mode}: correct={res['reactivated_correct']} "
              f"unnecessary={res['unnecessary_reactivations']} "
              f"prec={res['precision']:.2f} proj_speed={res['proj_speed']}")

    print("[6/8] Experiment D (Kombinationseffekt-Test)...")
    exp_d = run_experiment_d(params, OUTPUT_DIR)
    for mode, res in exp_d["results"].items():
        print(f"      {mode}: success={res['success_d']} "
              f"A_target@79={res['a_target_at_dormancy']} "
              f"proj_speed={res['proj_speed']}")

    print("[7/8] Negativszenario...")
    neg = run_negative_scenario(params, OUTPUT_DIR)
    print(f"      Reaktivierung: {neg['reactivation_rate']:.1%}, "
          f"Projektion: {neg['projection_rate']:.1%}, Bestanden: {neg['passes']}")

    # Extract metrics
    metrics_a   = extract_metrics_a(exp_a["results"])
    metrics_b   = extract_metrics_b(exp_b["results"])
    metrics_c   = extract_metrics_c(exp_c["results"])
    metrics_d   = extract_metrics_d(exp_d["results"])
    metrics_neg = extract_metrics_negative(neg)

    # Go/No-Go
    verdict_result = evaluate(
        metrics_a, metrics_b, metrics_c, metrics_neg,
        sweep_result["all_stable"],
        metrics_d=metrics_d,
    )

    print("[8/8] Mechanismus-Vergleich (explizite Paarvergleiche)...")
    mech_pairs = {
        "experiment_a": full_comparison_a(exp_a["results"]),
        "experiment_b": full_comparison_b(exp_b["results"]),
        "experiment_c": full_comparison_c(exp_c["results"]),
        "experiment_d": full_comparison_d(exp_d["results"]),
    }
    mech_classes = {
        exp: classify_from_pairs(pairs)
        for exp, pairs in mech_pairs.items()
    }
    arch_verdict = overall_architectural_verdict(mech_classes, mech_pairs)
    mech_sel_text = make_mech_selection_text(mech_classes, mech_pairs, arch_verdict)

    for exp, (cls, _) in mech_classes.items():
        print(f"      {exp}: {cls}")
    print(f"      combined_main beats feedback_only_h12 in: "
          f"{arch_verdict['cm_wins_over_fh12'] or 'none'}")

    print("\n" + "=" * 60)
    print(f"VERDIKT: {verdict_result['verdict']}")
    print(f"Kriterien bestanden: {verdict_result['criteria_passed']}/3")
    for msg in verdict_result.get("failed_criteria", []):
        print(f"  FEHLER: {msg}")
    exp_d_diag = verdict_result["diagnostics"].get("exp_d_diagnostic", {})
    if exp_d_diag:
        effect = "GEFUNDEN" if exp_d_diag.get("combination_effect_found") else "NICHT GEFUNDEN"
        print(f"  Exp D Kombinationseffekt: {effect}")
    print(f"  Architektur-Fazit: {arch_verdict['conclusion']} "
          f"(pers={arch_verdict['counts']['persistence_dominated']} "
          f"feed={arch_verdict['counts']['feedback_dominated']} "
          f"mixed={arch_verdict['counts']['mixed']})")
    print("=" * 60)

    # Build and save report
    report = build_report(
        stability_result, sweep_result,
        exp_a, exp_b, exp_c, exp_d, neg,
        metrics_a, metrics_b, metrics_c, metrics_d, metrics_neg,
        verdict_result,
        mech_pairs=mech_pairs,
        mech_classes=mech_classes,
        arch_verdict=arch_verdict,
        mech_selection_text=mech_sel_text,
    )
    report_path = Path(__file__).parent / "report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nBericht gespeichert: {report_path}")

    return 0 if verdict_result["verdict"] == "GO" else 1


if __name__ == "__main__":
    sys.exit(main())
