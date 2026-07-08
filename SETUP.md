# Hermine auf dem Laptop — Setup

## 1. Hermes Agent installieren

Nach der offiziellen Anleitung: https://github.com/NousResearch/hermes-agent
(macOS/Windows/Linux; Python ≥3.11 <3.14). Modelle wahlweise über Nous Portal
(Free-Tier) oder **OpenRouter** (`model.provider: "openrouter"` in
`~/.hermes/config.yaml` — dort laufen auch die Hermes-4-Modelle).

## 2. Governor installieren

```bash
pip install "joni-governor @ git+https://github.com/hstre/Intuitionsemulator.git"
joni-governor status     # legt ~/.joni-governor an (Kernel, pending/, heartbeat)
```

## 3. Plugin einhängen

```bash
mkdir -p ~/.hermes/plugins
cp -r <dieses-repo>/hermes_plugin/joni-governor ~/.hermes/plugins/
```

In `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - joni-governor      # Allow-List: das Gate MUSS hier stehen, sonst lädt es nicht

# Gürtel + Hosenträger: Hermes' eigene Staging-Gates zusätzlich einschalten.
# ACHTUNG: beide sind fail-open - sie ersetzen das Plugin nicht, sie ergänzen es.
memory:
  write_approval: true
skills:
  write_approval: true
```

## 4. Täglicher Umgang (die Mappe)

```bash
joni-governor status                 # offene Vorschläge + Liveness auf einen Blick
joni-governor sheet                  # die Vorschlags-Mappe (Inhalt, nicht nur Zahl)
joni-governor decide P-3 ok  weil sinnvoll und harmlos
joni-governor decide P-4 nein zu breit, kein klarer Nutzen
```

- **ok** = einmaliges Ticket: Hermine darf *genau diesen* Schreibvorgang einmal
  wiederholen (sag ihr im Chat: „P-3 ist freigegeben, führe es erneut aus").
- **nein** = korrigierter Irrtum: fließt in ihre Persona; Wiedergänger desselben
  Vorschlags werden künftig automatisch abgewiesen.

## 5. Der wichtigste Handgriff

```bash
joni-governor liveness
```

Beide eingebauten Hermes-Gates sind **fail-open**. Wenn Hermes lief, ohne dass das
Plugin feuerte (Plugin nicht in `plugins.enabled`, Importfehler, …), sagt dir dieser
Befehl das laut — ein Wächter, der still nicht läuft, ist schlimmer als keiner.

## Policy lockern (optional, explizit)

`~/.joni-governor/policy.yaml`:

```yaml
memory:
  auto_allow_actions: add      # z. B. schlichte Notizen ungefragt erlauben
# skills bleiben immer entscheidungspflichtig, bis du es hier ausdrücklich lockerst
```
