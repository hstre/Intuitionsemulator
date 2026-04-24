# Intuitionsemulator – Forschungsprototyp Bericht

## 0. Zusammenfassung der Iterationen

Dieser Prototyp wurde in vier Durchläufen entwickelt:

**Durchlauf 1:** Erster Aufbau mit 25 Schritten Totzeit in Experiment A
(später als zu kurz erkannt). Go/No-Go-Logik nutzte `any()` statt `all()`.

**Durchlauf 2:** Bewertungslogik verschärft (success_a binär, Experiment B
lexikographisch). Experiment A auf echte 25-Schritt-Totzeit umgebaut.

**Durchlauf 3:** Go/No-Go-Logik korrekt mit `all()`. Baselines A' und C' mit
H=12 als Robustheitstest. Diagnostischer Befund zur disjunkten Wirkung der
beiden Modellkomponenten hinzugefügt. Ehrliches NO-GO-Verdikt.

**Durchlauf 4 (dieser):** Experiment A auf 50-Schritt-Totzeit mit E=0.01
(physikalisch korrekte Diskriminierung). ComparisonResult-Schema eingeführt
(outcome/metric/margin statt roher Floats). Verifier-Logik graduiert (Hard
Reject erst nach 3 konsekutiven V=-1 oder A<0.3). Experiment D als
Kombinationseffekt-Test neu hinzugefügt. Verdikt bleibt NO-GO.

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

## 2. Experiment A – H=f(P)-Diskriminierung (50-Schritt-Totzeit, E=0.01)

**Erfolgsdefinition:** Hauptmodell überlebt Totzeit (alive_at_50) UND
reaktiviert sich im Fenster 50-70 UND projiziert bis Schritt 80.
Baselines A/C: H=const=8.0 · Baselines A'/C': H=const=12.0 (Robustheitstest)

| Modus | Lebt bei t=50 | A bei t=50 | Reaktivierung Schritt | Projektion Schritt | Projektion bis t=80 |
|-------|:------------:|:---------:|:--------------------:|:-----------------:|:-------------------:|
| main | ✓ | 0.103 | 51 | 51 | ✓ |
| baseline_a | ✗ | 0.078 | — | — | ✗ |
| baseline_b | ✓ | 0.103 | 51 | 51 | ✓ |
| baseline_c | ✗ | 0.078 | — | — | ✗ |
| baseline_a_prime | ✓ | 0.119 | 51 | 51 | ✓ |
| baseline_c_prime | ✓ | 0.119 | 51 | 51 | ✓ |

![Experiment A](/home/user/Intuitionsemulator/output/experiment_a.png)

**Schlüsselmetriken:**
- Korrekte Reaktivierung (Hauptmodell): 1
- Zeit bis Reaktivierung: 1 Schritte
- A-Werte bei Schritt 50 (Diskriminierung): main: 0.1031 | baseline_a: 0.0784 | baseline_b: 0.1031 | baseline_c: 0.0784 | baseline_a_prime: 0.1193 | baseline_c_prime: 0.1193

**Vergleich Hauptmodell vs. Baselines:**

| Baseline | Ergebnis |
|----------|---------|
| baseline_a | ✓ win (alive_at_50, Δ=1.00) |
| baseline_b | ~ tie (reactivation_time, Δ=0.00) |
| baseline_c | ✓ win (alive_at_50, Δ=1.00) |
| baseline_a_prime | ~ tie (reactivation_time, Δ=0.00) |
| baseline_c_prime | ~ tie (reactivation_time, Δ=0.00) |

---

## 3. Experiment B – Falscher Dominator + History-basierte Erholung

**Erfolgsdefinition:** Hauptmodell gewinnt gegen alle Baselines in
mindestens einer der drei Metriken (dominant_dead, false_proj, recovery_time)
um ≥20%, ohne in einer anderen Metrik >20% schlechter zu sein.

| Modus | Dominator verworfen Schritt | Falsche Projektionen | Erholungszeit |
|-------|:-------------------------:|:-------------------:|:------------:|
| main | 2 | 2 | 23 |
| baseline_a | 2 | 1 | — |
| baseline_b | 2 | 1 | — |
| baseline_c | 2 | 2 | 23 |
| baseline_a_prime | 2 | 1 | — |
| baseline_c_prime | 2 | 2 | 23 |

![Experiment B](/home/user/Intuitionsemulator/output/experiment_b.png)

**Vergleich Hauptmodell vs. Baselines:**

| Baseline | Ergebnis |
|----------|---------|
| baseline_a | ~ tie (false_proj, Δ=1.00) |
| baseline_b | ~ tie (false_proj, Δ=1.00) |
| baseline_c | ~ tie (dominant_dead, Δ=0.00) |
| baseline_a_prime | ~ tie (false_proj, Δ=1.00) |
| baseline_c_prime | ~ tie (dominant_dead, Δ=0.00) |

---

## 4. Experiment C – Selektive Reaktivierung

**Erfolgsdefinition:** Hauptmodell gewinnt primär durch höhere Präzision (≥20%
besser). Geschwindigkeit nur als Tiebreaker, wenn Präzision gebunden (±20%).

| Modus | Korrekte Reaktivierungen | Unnötige | Präzision | Proj.-Geschwindigkeit |
|-------|:-----------------------:|:-------:|:--------:|:--------------------:|
| main | 1 | 0 | 1.000 | 3 |
| baseline_a | 0 | 0 | 0.000 | — |
| baseline_b | 0 | 0 | 0.000 | — |
| baseline_c | 1 | 0 | 1.000 | 3 |
| baseline_a_prime | 1 | 0 | 1.000 | — |
| baseline_c_prime | 1 | 0 | 1.000 | 3 |

![Experiment C](/home/user/Intuitionsemulator/output/experiment_c.png)

**Vergleich Hauptmodell vs. Baselines:**

| Baseline | Ergebnis |
|----------|---------|
| baseline_a | ✓ win (precision, Δ=1.00) |
| baseline_b | ✓ win (precision, Δ=1.00) |
| baseline_c | ~ tie (precision+speed, Δ=0.00) |
| baseline_a_prime | ✓ win (proj_speed, Δ=1.00) |
| baseline_c_prime | ~ tie (precision+speed, Δ=0.00) |

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
  - comparisons_a:
    - baseline_a: outcome=win metric=alive_at_50 margin=1.0
    - baseline_b: outcome=tie metric=reactivation_time margin=0.0
    - baseline_c: outcome=win metric=alive_at_50 margin=1.0
    - baseline_a_prime: outcome=tie metric=reactivation_time margin=0.0
    - baseline_c_prime: outcome=tie metric=reactivation_time margin=0.0
  - comparisons_b:
    - baseline_a: outcome=tie metric=false_proj margin=1.0
    - baseline_b: outcome=tie metric=false_proj margin=1.0
    - baseline_c: outcome=tie metric=dominant_dead margin=0.0
    - baseline_a_prime: outcome=tie metric=false_proj margin=1.0
    - baseline_c_prime: outcome=tie metric=dominant_dead margin=0.0
  - comparisons_c:
    - baseline_a: outcome=win metric=precision margin=1.0
    - baseline_b: outcome=win metric=precision margin=1.0
    - baseline_c: outcome=tie metric=precision+speed margin=0.0
    - baseline_a_prime: outcome=win metric=proj_speed margin=1.0
    - baseline_c_prime: outcome=tie metric=precision+speed margin=0.0

### Criterion 2 – ✓ PASS
  - reactivation_rate: 0.0
  - projection_rate: 0.0
  - reactivation_ok: True
  - projection_ok: True

### Criterion 3 – ✓ PASS
  - all_sweep_stable: True

### Experiment D Diagnostic – Combination Effect: **NOT FOUND**
  - main success_d: True
  - baseline_a: success=False outcome=win metric=success_d margin=1.0
  - baseline_b: success=True outcome=win metric=proj_speed margin=0.5
  - baseline_c: success=False outcome=win metric=success_d margin=1.0
  - baseline_a_prime: success=True outcome=win metric=proj_speed margin=0.5
  - baseline_c_prime: success=True outcome=tie metric=proj_speed margin=0.0

### Failed Criteria Details
- Criterion 1: Main model beats all baselines in only 0/3 experiments (need >=2, each with outcome='win' against every baseline)

---

## 7. Experiment D – Kombinationseffekt-Test (Langzeit-Kette)

**Design:** 4 Claims (target, dominant, distractor, support), 120 Schritte,
späte Kontextaktivierung ab Schritt 80. Target muss 40 Schritte Totzeit
überleben (H-Test) UND dann durch Feedback reaktiviert werden (F-Test).

**Erfolgsbedingungen (success_d):** alle 5 müssen erfüllt sein:
1. target nicht verworfen bei t=79
2. target kein Frühprojekt vor t=80
3. dominant.A < theta_active bei t=79
4. target reaktiviert sich ab Schritt 80
5. target projiziert bis Schritt 110

| Modus | success_d | A target@79 | A dominant@79 | Reaktiv. Schritt | Proj. Schritt |
|-------|:---------:|:-----------:|:-------------:|:----------------:|:------------:|
| main | ✓ | 0.130 | 0.174 | 81 | 81 |
| baseline_a | ✗ | 0.079 | 0.101 | — | — |
| baseline_b | ✓ | 0.109 | 0.174 | 82 | 82 |
| baseline_c | ✗ | 0.079 | 0.101 | — | — |
| baseline_a_prime | ✓ | 0.114 | 0.206 | 82 | 82 |
| baseline_c_prime | ✓ | 0.114 | 0.206 | 81 | 81 |

![Experiment D](/home/user/Intuitionsemulator/output/experiment_d.png)

**Vergleich Hauptmodell vs. Baselines:**

| Baseline | Ergebnis |
|----------|---------|
| baseline_a | ✓ win (success_d, Δ=1.00) |
| baseline_b | ✓ win (proj_speed, Δ=0.50) |
| baseline_c | ✓ win (success_d, Δ=1.00) |
| baseline_a_prime | ✓ win (proj_speed, Δ=0.50) |
| baseline_c_prime | ~ tie (proj_speed, Δ=0.00) |

---

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
