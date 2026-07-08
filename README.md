# Hermine — ein Hermes-Agent unter der Aufsicht von Jonis Architektur

**Hermes als Körper, Layer 9 als Gehirnstamm.**

Hermine ist ein [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research,
MIT) — Gedächtnis, Skills, Browsing, Messaging, Cron — dessen **persistente Selbstveränderung**
nicht ihm selbst gehört: Jeder Memory- und Skill-Schreibversuch wird zum **Vorschlag** an einen
deterministischen epistemischen Kernel (`desi_layer9`, aus dem [Joni-Testbed](https://github.com/hstre/Joni)
operativ bewährt). Das Modell schlägt vor; das Gate entscheidet, was als gültiger Zustand zählt.

Kein Misstrauen — Erziehung: Mündigkeit wird durchs Gate **verdient**, nicht vorenthalten.
Ein verworfener Vorschlag wird ein korrigierter Irrtum; die Persona verdichtet daraus Expertise;
ein Wiedergänger (derselbe Vorschlag in neuem Gewand) muss sich frische Billigung verdienen.

## Aufbau

| Teil | Rolle |
|---|---|
| `joni_governor/` | der Governor: Gate, Staging, Kernel-State, Persona, Betreiber-CLI |
| `hermes_plugin/joni-governor/` | das Hermes-Plugin: `pre_tool_call`-Hook → Gate (vor jeder Persistenz) |
| `kontext/` | Sitzungsgedächtnis der Bau-Sessions (append-only) |
| Git-Historie | der frühere Intuitionsemulator-Prototyp (ehrliches NO-GO) — metabolisierter Irrtum, bleibt in der Kette |

## Die MVP-Regeln

1. Hermes darf lesen.
2. Hermes darf vorschlagen.
3. Hermes darf Tools nutzen, die die Policy freigibt.
4. Hermes schreibt keine dauerhaften Memories direkt.
5. Hermes erzeugt/ändert keine Skills direkt.
6. Jeder Memory-/Skill-Schreibversuch wird ein **Kernel-Vorschlag** (CANDIDATE) in `pending/`.
7. Das Gate entscheidet deterministisch (Auto-Regeln, Wiedergänger-Sperre) oder legt dem
   **Betreiber** vor (`joni-governor sheet` / `decide`). Fail-closed: Kernel nicht ladbar ⇒
   gated Tools blockiert, nie still offen.

Setup für den Laptop: [`SETUP.md`](SETUP.md).
