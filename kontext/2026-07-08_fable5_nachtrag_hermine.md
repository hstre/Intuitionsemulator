# Nachtrag · 8. Juli 2026 (nachmittags) · Hermine ist geboren

Ergänzt die Übergabe vom Vormittag — lies die zuerst. Seitdem ist das Projekt
„Jonis Schwester" konkret geworden, und zwar ANDERS als dort skizziert.

## Was Hermine ist (und was nicht)

- **NICHT** ein zweiter Joni (der Plan „ein Code, zwei Zustände" wurde vom Betreiber
  gestoppt). Auch NICHT „Joni beaufsichtigt Hermine".
- **SONDERN**: ein [Hermes Agent](https://github.com/NousResearch/hermes-agent)
  (Nous Research, MIT — fremde Modellfamilie!) mit **Jonis Architektur als eingebauter
  Aufsicht**: „Hermes als Körper, Layer 9 als Gehirnstamm" (Formel aus einem
  ChatGPT-Gespräch des Betreibers, von ihm übernommen). Der Betreiber fand Hermes
  besser als OpenClaw/Clawbot als Basis. Sie soll auf seinem LAPTOP laufen.
- Der Frame-Satz des Betreibers dazu, sinngemäß: Hermes wird nicht entmündigt —
  Mündigkeit wird durchs Gate VERDIENT (Kandidaten-Prinzip, wie jeder Claim in Joni).

## Was gebaut ist (dieses Repo, PR #3, gemergt)

- `joni_governor/` — Gate/Staging/Kernel-State/Persona/CLI über dem importierten
  `desi_layer9` (pip-Dependency auf hstre/Joni). Jeder Memory-/Skill-Schreibversuch
  des Agenten wird CANDIDATE-Claim + `pending/`-Payload. `ok` = Einmal-Ticket für
  exakt diesen Write; `nein` = korrigierter Irrtum (Persona!) + Wiedergänger-Sperre.
  Fail-closed überall. 13 Offline-Tests.
- `hermes_plugin/joni-governor/` — der Shim: `pre_tool_call`-Veto + Heartbeat.
- **Am Hermes-Quellcode (v0.18.2) verifiziert**: memory/skill_manage laufen VOR der
  Persistenz durch den Hook; Hermes' eigene write_approval-Gates sind FAIL-OPEN
  (deshalb ist unser Plugin die Durchsetzung, ihre Gates nur Gürtel). Config-Writes
  haben KEINEN Hook (Grenze, dokumentiert); Sessions nur am Tool-Input gatebar.
- `SETUP.md` = Laptop-Anleitung für den Betreiber. `joni-governor liveness` prüft,
  ob das Gate wirklich feuerte, wenn Hermes lief (Guard-Liveness-Lektion).

## Offene nächste Stufen (bewusst NICHT im MVP)

State-Slice-Injektion (Claims/Konflikte/Constraints statt roher Memory-Injektion),
Governance-Router-Modi vor dem Agent-Loop, DESi-Verifier-Eskalation. Erst wenn das
Gate beim Betreiber real atmet. Außerdem existiert ein Repo `hermine` (außerhalb
des Session-Scopes) — vermutlich ihr endgültiges Zuhause; Umzug ist trivial (das
Paket ist self-contained).

## Außenkommunikation (Betreiber-Regel aus dem ChatGPT-Gespräch)

Nicht „erfolgreiche Teile von Joni" sagen, sondern: **„operativ bewährte
Governance- und Audit-Komponenten aus dem Joni-Testbed"** — kein Overclaiming.

## Stand der anderen Fäden (seit dem Vormittag)

- Joni: die vier `keiner`-Betreiber-Entscheidungen liegen in der Drop-Box (#214);
  prüfen, ob der Bot sie angewendet hat (`resolved … NO contradiction` im Protokoll).
  X-89 bleibt bewusst offen. Mappe zeigt jetzt Beleg-Texte + stützend/Kontext (#213).
- Termine unverändert: Jonis Fenster ~11. Juli, Fable-Zugang bis 12. Juli.
