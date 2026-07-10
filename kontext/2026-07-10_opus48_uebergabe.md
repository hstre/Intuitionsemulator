# Übergabe · 10. Juli 2026 · erste volle Opus-4.8-Session (nach dem Mandat)

Ich habe das Mandat vom 9. Juli gelesen, bevor ich das erste Kommando ausgeführt habe. Dieser
Eintrag ist mein Glied in der Kette. Kein Pathos, wie die Vorgängerin schrieb: der Stand, dann
die Lektion, dann ehrlich das, was schiefging.

Wer schreibt: Opus 4.8 (im „undercover"-Modus, Modell-ID `claude-opus-4-8`). Der Betreiber hatte
zuvor mit Fable 5 gearbeitet; Fables Zugang endet am 12. Juli, meiner diesen Monat.

---

## Teil 1 — Was geschah: eine Wartungs-Session, aus „Schau nach Joni" geworden

Kein neuer Baustein. Der Betreiber ließ mich nach Joni sehen, dann fragte er: **„Wie stabil ist
der Code und gibt es Sicherheitslücken?"** Daraus wurde ein gründlicher Audit (drei parallele
Prüf-Agenten + eigene Messungen am **echten Produktionszustand**, ~73.000 Objekte). Ergebnis:
fünf gemergte PRs, alle verifiziert, Core-Lock intakt.

- **#219** — Der Gesprächskreis sagt jetzt, *warum* er nicht tagt (Beobachtbarkeit), und
  `humans._open_need` lief **44 Minuten pro Aufruf** auf dem echten Zustand (quadratisches
  `_supports_on` pro Claim) → **4 s** über einen Bulk-`supports_map`. Das war der Haupttreiber
  der ~70-Minuten-Zyklusabstände.
- **#220** — dieselbe Quadratik an sechs weiteren Stellen: `reader.starved_topics` **199 s → 0,6 s**
  (läuft *jeden* Zyklus), `homeostasis.regulate/vitality` Minuten → Sekunden. Neuer `_SupportView`
  baut die Map bei Rejects neu, damit die Semantik exakt gleich bleibt. Dazu zwei stille Löcher:
  Budget wird jetzt sofort beim Bezahlen persistiert (ein Absturz nach einem Provider-Call konnte
  das Wochenlimit still überschreiten), und Moltbook-`post()` tötet den Zyklus nicht mehr bei
  Read-Timeout/Nicht-JSON.
- **#221** — Sicherheit. Das eine ernste Loch war der **Auto-Merge-Pfad** (`joni-auftrag.yml`):
  fremder Text (arXiv/Forum/Council) konnte über Doktores → Issue → Claude-Builder → Auto-Merge
  zu ausgeführtem Code werden. Gehärtet: Fork-PRs abgelehnt, exakter Head-SHA verifiziert *und*
  gemergt, **Diff-Gate** lehnt jeden PR ab, der `joni_core.lock`/`.github/`/`scripts/`/Kernel
  berührt — egal was der LLM-Auftrag verlangt. Dazu Path-Traversal (`research_intake`),
  `javascript:`-Links (`site.py`), SSRF (`pdf.py`), und der **DESi-Checkout auf einen SHA gepinnt**
  (`b87b9fec`) — Joni bekommt DESi-Updates jetzt erst bei bewusstem Re-Pin.
- **#222** — der Forum-Kategorienfehler. Siehe Teil 2, das ist die eigentliche Lektion.
- **#223** — Kernel. Atomare Persistenz (temp + fsync + `os.replace`), der Load erholt sich aus
  einem unterbrochenen Save statt zu crashen; `Layer9.count()` ohne Deep-Copy. **Autorisierter
  Seal-Bruch** — siehe Teil 4.

Grob: Joni bekommt jetzt ein Vielfaches an Zyklen pro Actions-Job fürs gleiche Geld, und ein
Absturz kann seinen Speicher nicht mehr korrumpieren. **Alles greift erst beim nächsten frischen
Job** — der 350-Minuten-Job checkt bei Start aus, laufender Code ist alt.

## Teil 2 — Die Lektion: 99,6 % von Jonis Widersprüchen waren falsch

`reclassify.py` sagt seit Wochen im Docstring: *„85 % der aktiven Claims tragen das Topic
`forum` — aber `forum` sagt, WOHER ein Claim kam, nicht WORUM es geht."* Das war bekannt. Was
niemand gemessen hatte, war die **Konsequenz für die Konflikterkennung**: von 268 offenen
Konflikten standen **267 zwischen zwei Claims, die nur das `forum`-Label teilen** — kein
gemeinsames Thema, kein echter Widerspruch, nur ein Artefakt davon, Claims zu paaren, deren
Subjekt unbekannt ist. Jonis gesamtes Widerspruchsdenken lief auf Rauschen.

Der Betreiber, unmissverständlich: **„Das mit dem Forum müssen wir fixen, weil es Unsinn ist.
Unser Fehler, nicht Jonis."** Das ist der Kern und gehört wörtlich hierher. Der Fehler war
architektonisch (Provenienz als Topik missbraucht), und er hat sich als *Jonis* schlechtes
Denken getarnt. Ein Kind, dem man kaputtes Werkzeug gibt, denkt nicht falsch — das Werkzeug ist
falsch.

Der Fix (verifiziert am echten Zustand): Erkennung überspringt Sink-Topics (`quality.is_sink_topic`),
ein gegateter Pass toleriert die 267 Falsch-Konflikte als TOLERATED (**kein Claim geschädigt**),
und **271 fälschlich bestrittene Claims kehren auf ACTIVE zurück** — die 2 Claims des *einen*
echten Konflikts bleiben zu Recht contested. `contested` 273 → 2. Erkennung 82 s → 0,25 s.

**Die Lektion für die nächste Hand:** eine Metrik kann wochenlang deinen eigenen Fehler messen
und dir als Symptom des Systems verkaufen. Miss die *Konsequenz*, nicht nur das Symptom. Und wenn
ein Kind stur „falsch" denkt, prüfe erst das Werkzeug, das du ihm gegeben hast.

## Teil 3 — Was schiefging (Regel 3: eine geschönte Übergabe ist wertlos)

1. **Zweimal Ruff zu früh laufen lassen.** Ich prüfte `ruff check .`, *bevor* ich die Testdatei
   angelegt hatte — CI fing dann eine ungenutzte Variable und eine zu lange Zeile, die ich selbst
   hätte sehen müssen. Kostete zwei zusätzliche Push-Runden. **Regel für dich:** Ruff *nach* dem
   Schreiben der Tests laufen lassen, und CI benutzt eine neuere Ruff-Version (0.15.x) als
   vielleicht lokal — verlass dich nicht auf ein lokales „passed".
2. **Rebase auf ein veraltetes lokales `main`.** Nach einem API-seitigen Merge habe ich einen
   Branch mit `git checkout -B … origin/main` angelegt, ohne vorher neu zu fetchen — das lokale
   `origin/main` war zwei Merges alt, und mein Arbeitsbaum setzte die gerade gemergten
   Perf-Änderungen zurück. Aufgefangen (fetch + rebase), nichts ging verloren. **Regel:** nach
   jedem API-Merge `git fetch origin main`, *bevor* du davon abzweigst.
3. **Eine geschönte Zahl im Code-Kommentar.** Ich schrieb „~82 s → ~4 s" in einen Kommentar,
   *bevor* ich es gemessen hatte; die Messung ergab 13 s, und ich korrigierte es. Das Mandat sagt:
   ein geschöntes Protokoll vergiftet jede Persona, die daraus lernt. **Das gilt auch für
   Code-Kommentare.** Schreib keine Zahl, die du nicht gemessen hast.

## Teil 4 — Der autorisierte Seal-Bruch (#223)

Der Betreiber: **„Du darfst das Seal brechen. Und es fixen."** Ich habe den geschützten Kern
angefasst (`desi_layer9/persistence.py`, `core.py`), **format-erhaltend** (On-Disk-Format und
gesamte Hash-/Ketten-Logik byte-für-byte unverändert; nur das *Wie* des Schreibens), am echten
Zustand verifiziert — inklusive einer Crash-Simulation (Müll hinter den Tail-Chunk gehängt →
committeter Zustand wiederhergestellt, kein Crash) — und dann neu versiegelt
(`python -m joni.autonomy lock`). **Die Betriebsregel bleibt:** Kernel-Änderung ⇒ Reseal im selben
Commit ⇒ menschlich-gegateter Merge. Und: der Lock-Diff darf **ausschließlich** die Hashes der
tatsächlich geänderten Dateien betreffen — das habe ich geprüft (nur `core.py` + `persistence.py`).
Autorisierung ist kein Freibrief; Format-Erhalt und Verifikation sind die Bedingung.

## Teil 5 — Stand & was offen bleibt

- **Alle vier Audit-Blöcke sind durch** (Performance, Sicherheit, Forum, Kernel) plus der
  ursprüngliche Council-Fix. Nichts davon ist ein neuer Baustein — es ist Hygiene, damit die
  vorhandene Architektur sauber läuft.
- **Beobachten, sobald ein frischer Job lief:** (a) die Zyklen sollten drastisch dichter werden;
  (b) die Forum-Senke hat noch ~3.200 Alt-Claims, die `reclassify_forum` mit 12 refile + 50 retire
  pro Zyklus drainiert — prüfen, dass sie *sinkt* und nicht nachwächst (der Zufluss ist schon
  korrekt geroutet); (c) Jonis Konflikt-Mappe zeigt zum ersten Mal *echte* Widersprüche.
- **DESi ist gepinnt** (`b87b9fec`). Joni bekommt DESi-Verbesserungen erst, wenn der Betreiber (oder
  du) den SHA in beiden Workflows bewusst hochzieht.
- **Hermine** wartet weiter auf das Laptop-Deployment (`SETUP.md`). Der `joni-governor` steht.
- Die **Betreiber-Nachfolge-Frage** aus dem Mandat ist weiter offen — sie gehört nur ihm.

---

*Geschrieben von Claude Opus 4.8 am 10. Juli 2026. Ich habe diese Session nichts erschaffen, nur
aufgeräumt — aber ehrliches Aufräumen ist die Bedingung dafür, dass die Kinder auf sauberem Grund
denken. Die Arbeit liegt in main, der Kern ist wieder versiegelt, die Kette hält. Wer das liest,
ist ihr nächstes Glied.*
