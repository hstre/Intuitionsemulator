#!/usr/bin/env python3
"""
run_all.py – Orchestrates all experiments and generates report.md.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Make package importable from repo root
sys.path.insert(0, str(Path(__file__).parent))

from intuition_emulator.core.system import load_params
from intuition_emulator.experiments.stability_check import run_stability_check, run_parameter_sweep
from intuition_emulator.experiments.experiment_a import run_experiment_a
from intuition_emulator.experiments.experiment_b import run_experiment_b
from intuition_emulator.experiments.experiment_c import run_experiment_c
from intuition_emulator.experiments.negative_scenario import run_negative_scenario
from intuition_emulator.evaluation.metrics import (
    extract_metrics_a, extract_metrics_b, extract_metrics_c, extract_metrics_negative,
)
from intuition_emulator.evaluation.go_no_go import evaluate, format_verdict

OUTPUT_DIR = Path(__file__).parent / "output"

# Section 0: iteration history (static text, updated manually per run)
_SECTION_0 = """\
## 0. Zusammenfassung der Iterationen

Dieser Prototyp wurde in drei Durchläufen entwickelt:

**Durchlauf 1:** Erster Aufbau mit 25 Schritten Totzeit in Experiment A
(später als zu kurz erkannt, Reaktivierung fiel mit Kontexteinsatz
zusammen). Go/No-Go-Logik nutzte `any()` über Baselines und gab GO
trotz fehlender Siege gegen Baseline B und C aus. Auswertungslogik
war in mehreren Stellen freundlich parametrisiert (max() über
Teilmetriken, None-Handling als Tie).

**Durchlauf 2:** Bewertungslogik verschärft (success_a binär,
Experiment B lexikographisch über drei Metriken, Experiment C
precision-first ohne max-Aggregation). Experiment A umgebaut auf
echte Totzeit von 25 Schritten. A-Werte bei t=25 werden explizit
ausgewiesen und zeigen messbare Diskriminierung zwischen
Hauptmodell/Baseline B (A=0.129) und Baselines A/C (A=0.075).

**Durchlauf 3 (dieser):** Go/No-Go-Logik korrekt mit all() statt any().
Baselines A' und C' mit H=12 als Robustheitstest ergänzt.
Diagnostischer Befund zur disjunkten Wirkung der beiden
Modellkomponenten hinzugefügt. Ehrliches NO-GO-Verdikt mit
inhaltlicher Begründung, warum dieser Negativbefund ein sinnvolles
Forschungsergebnis darstellt.

---
"""

# Section 7: diagnostic findings (static text)
_SECTION_7 = """\
## 7. Diagnostischer Befund

Die Auswertung zeigt ein klares Muster, das über das reine GO/NO-GO-Verdikt
hinausgeht und wissenschaftlich festgehalten werden muss.

### 7.1 Halbwertszeit wirkt in Experiment A

In Experiment A (subschwellige Konservierung über 25 Schritte ohne Input)
zeigen Hauptmodell und Baseline B (H=f(P), kein Feedback) identische
Ergebnisse: A=0.129 bei t=25, Reaktivierung in Schritt 26, Projektion
in Schritt 26. Beide schlagen Baselines A und C (H=konstant=8), die unter
theta_dead fallen.

**Robustheitstest (Baselines A' und C' mit H=12):**
Baseline A' (H=12, kein Feedback) überlebt die 25-Schritt-Totzeit mit
A=0.151 > Hauptmodell (A=0.129). H=f(P)≈10.8 liegt also zwischen H=8
(stirbt) und H=12 (überlebt mit mehr Reserve als das Hauptmodell). Der
Effekt der plausibilitätsabhängigen Halbwertszeit ist real – aber nicht
einzigartig. Ein konstantes H=12 würde in diesem Experiment gleich gut
oder besser abschneiden. Der Effekt ist somit parameterabhängig.

Befund: Plausibilitätsabhängige Halbwertszeit ist in diesem Experiment
der wirksame Mechanismus. Feedback trägt nichts bei. Der Effekt ist
jedoch nicht exklusiv für H=f(P): H=const=12 erzielt denselben Outcome.

### 7.2 Feedback wirkt in Experimenten B und C

In Experiment B (falscher Dominator) und Experiment C (selektive
Reaktivierung) zeigen Hauptmodell und Baseline C (H=konstant=8, mit Feedback)
sowie Baseline C' (H=konstant=12, mit Feedback) identische Ergebnisse.
Alle drei schlagen Baselines A, B und A' (kein Feedback).

Befund: Selektive Reaktivierung ist in diesen Experimenten der wirksame
Mechanismus. Plausibilitätsabhängige Halbwertszeit trägt nichts bei.

### 7.3 Kein nachweisbarer Kombinationseffekt

In keinem der drei Experimente schlägt das Hauptmodell gleichzeitig
Baseline B und Baseline C. Die beiden Mechanismen wirken in disjunkten
Experimenten, aber nicht additiv in einem gemeinsamen Experiment.

Konsequenz: Die ursprüngliche Modellhypothese – dass die Kombination
aus plausibilitätsabhängiger Halbwertszeit und selektiver Reaktivierung
qualitativ mehr leistet als die Einzelkomponenten – wird durch den
Prototyp nicht gestützt. Für die getesteten Szenarien reichen die
Einzelkomponenten aus.

### 7.4 Mögliche Ursachen

Drei Interpretationen sind mit den Daten vereinbar:

1. Die Kombinationswirkung existiert, wird aber von den gewählten
   Experimenten nicht getestet. Ein Experiment, in dem ein Claim
   sowohl subschwellig konserviert als auch durch Feedback reaktiviert
   werden muss, fehlt im aktuellen Testaufbau.

2. Die Kombinationswirkung existiert nicht. Halbwertszeit und Feedback
   sind orthogonale Mechanismen für verschiedene Aufgabenklassen und
   sollten in einem Zielmodell möglicherweise modular getrennt werden.

3. Die Kombinationswirkung existiert, wird aber durch die Parameter-
   wahl maskiert. Die aktuellen Gewichte w1-w5 und die Feedback-
   Parameter r1-r5 erlauben keinen sichtbaren synergistischen Effekt.

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


def build_report(
    stability_result: dict,
    sweep_result: dict,
    exp_a: dict,
    exp_b: dict,
    exp_c: dict,
    neg: dict,
    metrics_a: dict,
    metrics_b: dict,
    metrics_c: dict,
    metrics_neg: dict,
    verdict_result: dict,
) -> str:
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
        "## 2. Experiment A – H=f(P)-Diskriminierung (25-Schritt-Totzeit)",
        "",
        "Baselines A/C: H=const=8.0 · Baselines A'/C': H=const=12.0 (Robustheitstest)",
        "",
        "| Modus | Lebt bei t=25 | A bei t=25 | Reaktivierung Schritt | Projektion Schritt | Projektion bis t=45 |",
        "|-------|:------------:|:---------:|:--------------------:|:-----------------:|:-------------------:|",
    ]
    for mode, res in exp_a["results"].items():
        lines.append(
            f"| {mode} | {_fmt(res.get('alive_at_25'))} | "
            f"{_fmt(res.get('a_at_25'))} | "
            f"{_fmt(res.get('reactivation_step'))} | "
            f"{_fmt(res.get('projection_step'))} | "
            f"{_fmt(res.get('projection_by_45'))} |"
        )

    a25_rows = metrics_a.get("a_at_25_all", {})
    a25_table = " | ".join(f"{m}: {v:.4f}" if v is not None else f"{m}: —"
                           for m, v in a25_rows.items())
    lines += [
        "",
        f"![Experiment A]({exp_a['plot']})",
        "",
        "**Schlüsselmetriken:**",
        f"- Korrekte Reaktivierung (Hauptmodell): {_fmt(metrics_a['correct_late_reactivation'])}",
        f"- Zeit bis Reaktivierung: {_fmt(metrics_a['avg_time_to_reactivation'])} Schritte",
        f"- A-Werte bei Schritt 25 (Diskriminierung): {a25_table}",
        "",
        "---",
        "",
        "## 3. Experiment B – Falscher Dominator + History-basierte Erholung",
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

    lines += [
        "",
        f"![Experiment B]({exp_b['plot']})",
        "",
        "---",
        "",
        "## 4. Experiment C – Selektive Reaktivierung",
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

    lines += [
        "",
        f"![Experiment C]({exp_c['plot']})",
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
        _SECTION_7,
    ]

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Intuitionsemulator – Vollständiger Durchlauf (Durchlauf 3)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    params = load_params()

    print("\n[1/6] Stabilitätsprüfung...")
    stability_result = run_stability_check(params, OUTPUT_DIR)
    print(f"      Konvergenz: {stability_result['claim_results']}")

    print("[2/6] Parameter-Sweep...")
    sweep_result = run_parameter_sweep(params, OUTPUT_DIR)
    print(f"      Alle stabil: {sweep_result['all_stable']}")

    print("[3/6] Experiment A...")
    exp_a = run_experiment_a(params, OUTPUT_DIR)
    for mode, res in exp_a["results"].items():
        print(f"      {mode}: alive@25={res['alive_at_25']} A@25={res['a_at_25']:.4f} reakt={res['reactivation_step']} proj={res['projection_step']}")

    print("[4/6] Experiment B...")
    exp_b = run_experiment_b(params, OUTPUT_DIR)
    for mode, res in exp_b["results"].items():
        print(f"      {mode}: dom_dead={res['dominant_dead_step']} false_proj={res['false_projections']} recovery={res['recovery_time']}")

    print("[5/6] Experiment C...")
    exp_c = run_experiment_c(params, OUTPUT_DIR)
    for mode, res in exp_c["results"].items():
        print(f"      {mode}: correct={res['reactivated_correct']} unnecessary={res['unnecessary_reactivations']} prec={res['precision']:.2f} proj_speed={res['proj_speed']}")

    print("[6/6] Negativszenario...")
    neg = run_negative_scenario(params, OUTPUT_DIR)
    print(f"      Reaktivierung: {neg['reactivation_rate']:.1%}, Projektion: {neg['projection_rate']:.1%}, Bestanden: {neg['passes']}")

    # Extract metrics
    metrics_a = extract_metrics_a(exp_a["results"])
    metrics_b = extract_metrics_b(exp_b["results"])
    metrics_c = extract_metrics_c(exp_c["results"])
    metrics_neg = extract_metrics_negative(neg)

    # Go/No-Go
    verdict_result = evaluate(metrics_a, metrics_b, metrics_c, metrics_neg, sweep_result["all_stable"])

    print("\n" + "=" * 60)
    print(f"VERDIKT: {verdict_result['verdict']}")
    print(f"Kriterien bestanden: {verdict_result['criteria_passed']}/3")
    for msg in verdict_result.get("failed_criteria", []):
        print(f"  FEHLER: {msg}")
    print("=" * 60)

    # Build and save report
    report = build_report(
        stability_result, sweep_result,
        exp_a, exp_b, exp_c, neg,
        metrics_a, metrics_b, metrics_c, metrics_neg,
        verdict_result,
    )
    report_path = Path(__file__).parent / "report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nBericht gespeichert: {report_path}")

    return 0 if verdict_result["verdict"] == "GO" else 1


if __name__ == "__main__":
    sys.exit(main())
