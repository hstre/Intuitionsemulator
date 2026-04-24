# Intuitionsemulator – Forschungsprototyp Bericht

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

## 1. Stabilitätsprüfung

### 1.1 Konvergenztests (200 Schritte, feste Inputs)

| Claim | Konvergiert? |
|-------|-------------|
| c1 | True |
| c2 | True |
| c3 | True |

![Stabilitätsprüfung](/home/user/Intuitionsemulator/output/stability_check.png)

### 1.2 Parameter-Sweep (α × η)

Alle Kombinationen stabil: **✓**

![Parameter-Sweep](/home/user/Intuitionsemulator/output/stability_sweep.png)

---

## 2. Experiment A – H=f(P)-Diskriminierung (25-Schritt-Totzeit)

Baselines A/C: H=const=8.0 · Baselines A'/C': H=const=12.0 (Robustheitstest)

| Modus | Lebt bei t=25 | A bei t=25 | Reaktivierung Schritt | Projektion Schritt | Projektion bis t=45 |
|-------|:------------:|:---------:|:--------------------:|:-----------------:|:-------------------:|
| main | ✓ | 0.129 | 26 | 26 | ✓ |
| baseline_a | ✗ | 0.075 | — | — | ✗ |
| baseline_b | ✓ | 0.129 | 26 | 26 | ✓ |
| baseline_c | ✗ | 0.075 | — | — | ✗ |
| baseline_a_prime | ✓ | 0.151 | 26 | 26 | ✓ |
| baseline_c_prime | ✓ | 0.151 | 26 | 26 | ✓ |

![Experiment A](/home/user/Intuitionsemulator/output/experiment_a.png)

**Schlüsselmetriken:**
- Korrekte Reaktivierung (Hauptmodell): 1
- Zeit bis Reaktivierung: 1 Schritte
- A-Werte bei Schritt 25 (Diskriminierung): main: 0.1287 | baseline_a: 0.0747 | baseline_b: 0.1287 | baseline_c: 0.0747 | baseline_a_prime: 0.1509 | baseline_c_prime: 0.1509

---

## 3. Experiment B – Falscher Dominator + History-basierte Erholung

| Modus | Dominator verworfen Schritt | Falsche Projektionen | Erholungszeit |
|-------|:-------------------------:|:-------------------:|:------------:|
| main | 1 | 1 | 24 |
| baseline_a | 1 | 1 | — |
| baseline_b | 1 | 1 | — |
| baseline_c | 1 | 1 | 24 |
| baseline_a_prime | 1 | 1 | — |
| baseline_c_prime | 1 | 1 | 24 |

![Experiment B](/home/user/Intuitionsemulator/output/experiment_b.png)

---

## 4. Experiment C – Selektive Reaktivierung

| Modus | Korrekte Reaktivierungen | Unnötige | Präzision | Proj.-Geschwindigkeit |
|-------|:-----------------------:|:-------:|:--------:|:--------------------:|
| main | 1 | 0 | 1.000 | 3 |
| baseline_a | 0 | 0 | 0.000 | — |
| baseline_b | 0 | 0 | 0.000 | — |
| baseline_c | 1 | 0 | 1.000 | 3 |
| baseline_a_prime | 1 | 0 | 1.000 | — |
| baseline_c_prime | 1 | 0 | 1.000 | 3 |

![Experiment C](/home/user/Intuitionsemulator/output/experiment_c.png)

---

## 5. Negativszenario – Reines Rauschen

| Metrik | Wert | OK? |
|--------|------|-----|
| Reaktivierungsrate | 0.0% | ✓ |
| Projektionsrate | 0.0% | ✓ |

![Negativszenario](/home/user/Intuitionsemulator/output/negative_scenario.png)

---

## 6. Go/No-Go Entscheidung

## Go/No-Go Verdict: **NO_GO**
Criteria passed: 2/3

### Criterion 1 – ✗ FAIL
  - experiments_beaten: 0
  - exp_a_beats_all_baselines: False
  - exp_b_beats_all_baselines: False
  - exp_c_beats_all_baselines: False
  - comparisons_a: {'baseline_a': 1.0, 'baseline_b': 0.0, 'baseline_c': 1.0, 'baseline_a_prime': 0.0, 'baseline_c_prime': 0.0}
  - comparisons_b: {'baseline_a': 1.0, 'baseline_b': 1.0, 'baseline_c': 0.0, 'baseline_a_prime': 1.0, 'baseline_c_prime': 0.0}
  - comparisons_c: {'baseline_a': 1.0, 'baseline_b': 1.0, 'baseline_c': 0.0, 'baseline_a_prime': 1.0, 'baseline_c_prime': 0.0}

### Criterion 2 – ✓ PASS
  - reactivation_rate: 0.0
  - projection_rate: 0.0
  - reactivation_ok: True
  - projection_ok: True

### Criterion 3 – ✓ PASS
  - all_sweep_stable: True

### Failed Criteria Details
- Criterion 1: Main model beats all baselines in only 0/3 experiments (need ≥2, each with ≥20% margin against every baseline)

---

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
