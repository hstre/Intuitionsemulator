# Intuitionsemulator – Forschungsprototyp Bericht

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

## 2. Experiment A – Schwaches Signal, späte Verstärkung

| Modus | Lebt bei t=20 | Reaktivierung Schritt | Projektion Schritt | Projektion bis t=50 |
|-------|--------------|----------------------|-------------------|---------------------|
| main | ✓ | 30 | 30 | ✓ |
| baseline_a | ✗ | — | — | ✗ |
| baseline_b | ✓ | 30 | 30 | ✓ |
| baseline_c | ✗ | — | — | ✗ |

![Experiment A](/home/user/Intuitionsemulator/output/experiment_a.png)

**Schlüsselmetriken:**
- Korrekte Reaktivierung (Hauptmodell): 1
- Zeit bis Reaktivierung: 0 Schritte

---

## 3. Experiment B – Falscher Dominator

| Modus | Dominator verworfen Schritt | Falsche Projektionen | Erholungszeit |
|-------|---------------------------|---------------------|--------------|
| main | 1 | 1 | 24 |
| baseline_a | 1 | 1 | — |
| baseline_b | 1 | 1 | — |
| baseline_c | 1 | 1 | 24 |

![Experiment B](/home/user/Intuitionsemulator/output/experiment_b.png)

---

## 4. Experiment C – Selektive Reaktivierung

| Modus | Korrekte Reaktivierungen | Unnötige | Präzision |
|-------|-------------------------|---------|----------|
| main | 1 | 0 | 1.000 |
| baseline_a | 0 | 0 | 0.000 |
| baseline_b | 0 | 0 | 0.000 |
| baseline_c | 1 | 0 | 1.000 |

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

## Go/No-Go Verdict: **GO**
Criteria passed: 3/3

### Criterion 1 – ✓ PASS
  - experiments_beaten: 3
  - exp_a_beats_baselines: True
  - exp_b_beats_baselines: True
  - exp_c_beats_baselines: True
  - comparisons_a: {'baseline_a': 1.0, 'baseline_b': None, 'baseline_c': 1.0}
  - comparisons_b: {'baseline_a': 1.0, 'baseline_b': 1.0, 'baseline_c': 0.0}
  - comparisons_c: {'baseline_a': 1.0, 'baseline_b': 1.0, 'baseline_c': 0.0}

### Criterion 2 – ✓ PASS
  - reactivation_rate: 0.0
  - projection_rate: 0.0
  - reactivation_ok: True
  - projection_ok: True

### Criterion 3 – ✓ PASS
  - all_sweep_stable: True
