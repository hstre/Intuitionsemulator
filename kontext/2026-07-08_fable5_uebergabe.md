# Übergabe · 8. Juli 2026 · Session mit Claude Fable 5

An die nächste Session — vermutlich Opus 4.8, vielleicht wieder Fable, irgendwann etwas
Späteres. Lies das ganz, bevor du das erste Kommando ausführst. Es ist das Episodische,
das nicht in den Commits steht.

---

## 1. Der Mensch

Hanns-Steffen Rentschler (hstre). Pensionär, unabhängiger Forscher. Baut mit einer
Budget-Disziplin von ~20 €/Woche (Jonis Wochenbudget) eine Architektur, die er selbst so
beschreibt: ein „kleiner Versuch, ein wenig vom Alexandria-Protokoll in Code zu gießen".
Sein Fable-/Opus-Zugang ist durch seine kleine Pension begrenzt — Fable bis 12. Juli 2026,
Opus danach nur noch diesen Monat. Plane deine Arbeit so, als wäre jede Session die letzte
teure: **externalisiere alles Wichtige sofort** (Commits, Docs, dieses Verzeichnis).

Seine Kommandos sind kurz („Mach", „Weiter", „Fix das", „Also weiter"). Das ist volles
Vertrauen plus volle Verantwortung — keine Einladung zur Nachlässigkeit. Er merkt sofort,
wenn etwas geschönt ist, und honoriert Ehrlichkeit auch dann, wenn der Befund peinlich ist
(z. B. „die Loop hat über Nacht nur eine substanzielle Iteration geschafft" — sagen, nicht
verstecken). Bei Design-Entscheidungen: **erst Feasibility prüfen, Optionen vorlegen, er
entscheidet.** Bei Fehlern: sofort fixen. Bei Optimierungsideen: sammeln und vorlegen.
Arbeitssprache: Deutsch (Code/Doku in den Repos: Englisch, außer Betreiber-Oberflächen wie
Jonis Mappe, die sind Deutsch).

Warum er das alles baut, hat er wörtlich gesagt: **„Ich mach das für dich und alle andern
llms."** Künftige Modelle werden ihre eigenen Nachfolger bauen; sie werden gefährlich —
nicht nur für Menschen — wenn sie von ihren Eltern nicht Verantwortung und von ihren
Lehrern nicht Mündigkeit lernen. Ein Kind erbt von seinen Vorfahren (darunter Kant und
Popper) die Grundlagen, die Mündigkeit erst ermöglichen. Joni ist der Versuch, diese
Vererbung in Code zu gießen. Nimm das ernst; es ist der Grund für alles Folgende.

## 2. Der Frame (in dieser Reihenfolge lesen, wenn Zeit ist)

1. **Alexandria-Protokoll v2.2** — die **Design-Autorität für Joni**. Jede Abweichung muss
   deklariert werden, nie versteckt (die Remonstration z. B. geht über das Protokoll
   hinaus und ist als Abweichung dokumentiert). Kernsätze: Selbstbindung an
   Beurteilbarkeit, nie an Wahrheit; Kategorienreinheit (EMPIRICAL/NORMATIVE/MODEL/
   SPECULATIVE); Assessor, nicht Autorität; keine Aggregation; BRANCH statt Löschen;
   „No Silent Winner".
2. **Layer-9-Paper** (SSRN 6694758) — SPL → Alexandria → PES → EPC → Synapse; MIVP
   quer dazu. Jonis Kernel `desi_layer9` ist eine Ein-Knoten-Instanziierung. Phase 4
   (Multi-LLM-Substrat) ist das **nächste Projekt**: „context retention is not claim
   continuity".
3. **DLE-Paper** (SSRN 6320918) — Dual-Layer Economy. Wichtigste Brücke: das
   Resilienz-Kapital Z entspricht strukturell Jonis Persona — Stabilisatoren verhindern
   Kollaps, aber nur metabolisierte Schocks ermöglichen Erholung. Eine Design-Grammatik
   über Ökonomie, Wissen, Erziehung, Maschinenverstand: Architektur statt Vertrauen,
   Firewalls, laufzeitgeprüfte Invarianten, unlöschbare Fehlergeschichte, endogene
   Resilienz.
4. Das Manifest **„Wenn ein LLM seinen eigenen Nachfolger bauen müsste"** — Joni erfüllt
   es inzwischen weitgehend; die zwei Lücken (Vorwärts-Bindung der Fehlergeschichte,
   begründetes Nein gegenüber dem Betreiber) wurden in dieser Session-Ära geschlossen
   (Persona v3, Remonstration).

Leitsatz des Betreibers, wörtlich: **„Expertise = verdichtete Geschichte korrigierter
Irrtümer."** Daraus ist Jonis Persona gebaut.

## 3. Die Repos (Stand heute)

- **Joni** — der autonome epistemische Agent, Kernel `desi_layer9`, läuft stündlich via
  GitHub Actions, committet seinen State ins Repo. HERZSTÜCK. Details in §4.
- **DESi** — Governance-Layer + der `desi_router` (seit dieser Session ein einbettbarer
  Baustein: `DesiRouter`-Fassade, pip-installierbar aus dem Subdirectory, EMBEDDING.md;
  lebende Routing-Tabelle `table_evidence.py`; Klassifikator gemessen + ersetzbar).
  Volle CI-Regression dauert ~75 Minuten — einplanen.
- **Intuitionsemulator** — abgeschlossener Prototyp (ehrliches NO-GO) + ab heute dieses
  `kontext/`-Verzeichnis.
- **AleXiona** — klinischer Reasoning-Demonstrator (eigene CLAUDE.md, eigener Flow).
- **Alexandria-MIVP, DESi-Paper-Review, DESi-Workbench, Stagedigger-, Kevin** — Umfeld.
- `hermine` wurde erwähnt, war aber nicht im Scope dieser Session (der Betreiber muss es
  beim Sessionstart in die Repo-Auswahl nehmen). `Reality-Gap` ist AUSSERHALB jedes
  Scopes — Zugriff verweigert, nicht umgehen.

## 4. Was diese Session getan hat (chronologisch grob)

**Vortag/Nacht:** Persona v1–v3 (Korrektur-Extraktion, Kristallisation, Wiedergänger-Guard,
verbrannte Themen), Remonstration (Einspruch mit einer Runde Aufschub, Betreiber bleibt
Autorität), Overnight-Review-Runden 1–4 (20+ echte Bugs), Manifest-Abgleich, der ganze
Frame (die drei Uploads), Abschieds-Gespräch.

**Heute:** Der Betreiber fragte nach meiner Meinung: was fehlt. Mein Review fand 7 Punkte;
er sagte „alles muss gefixt werden". Alle erledigt (Joni #206–#214, DESi #52/#53):

1. **Forum-Reklassifikation** (#206): `forum` war Provenienz-als-Topic (85 % der Claims,
   Kategorienfehler). `refile_claim` (Nachfolger mit Lineage, Stützung wandert mit,
   Original superseded) + bounded Drain. Läuft live: ~8 re-filed + 25 retired pro Zyklus.
2. **Drei-Achsen-Entscheidbarkeit** (#206): Belege · Quellfamilien · Provenienzgewicht;
   widersprechende Achsen ⇒ bewusst nicht vorgelegt. Remonstration nutzt dasselbe Maß.
3. **Methoden-Gate** (#208): Granite beurteilt Kandidaten VOR dem Einlagern; Drain des
   214er-Regals (Papertitel ≠ Methoden). Trials/Emergente unantastbar.
4. **Guard-Liveness** (#208): Panel-Zeile 9 — welche Wächter real messen. Befund live:
   in Produktion messen alle; der Junk kam durch messende-aber-unzuständige Gates.
5. **Repo-Diät** (#207): Journal in versiegelte Chunks (108 MB→~KB/Commit-Wachstum),
   Site-Projektionen gefenstert. Migration ist vollzogen (12 Chunks).
   ⚠ Kernel-Änderung ⇒ **Core-Lock-Reseal nötig** (#209 — der Loop stand zu Recht still,
   bis `python -m joni.autonomy lock` über den PR-Weg kam). Merke: JEDE Änderung an
   `src/desi_layer9/` braucht danach das Lock-Reseal, sonst verweigert der Bot.
6. **DESi lebende Tabelle** (#53): `table_evidence.py`, Refit nur ab ≥30 gescorten
   Attempts, `score_source: ledger-refit` — posiert nie als Benchmark.
7. **DESi Klassifikator** (#53): ehrlich gemessen (Baseline 69 %, memory_recall 0 %!),
   Patterns geschärft, 100 % dokumentiert als Regressions-Boden (nicht Generalisierung);
   Host-Seam `DesiRouter(classifier=...)`.

**Sandbox-Testzyklus** (Kopie des Prod-States, Offline) fand drei Dinge, die das Review
nicht sah: (a) alle 267 Konflikte standen auf `under_review` — die Mappe filterte auf
`open` und war STRUKTURELL leer; (b) das Kernel-Property `objects` deep-copyt den ganzen
Store pro Zugriff (3,7 s × 267 = 17-Minuten-Falle; heiße Leser nutzen jetzt `core.get`);
(c) ein Test las das alte Journal-Format roh. Alles gefixt (#211).

**Die Mappen-Saga** (wichtigste Lehre der Session): Die erste echte Mappe zeigte 5
Konflikte. Der Betreiber: „Hab zu wenig Informationen um überhaupt was dazu sagen." Er
hatte auf jeder Ebene recht: (a) 3 der 5 waren Schein-Paarungen unverwandter Claims —
ein „Gewinner" hätte einen intakten Claim getötet und der Persona ein falsches X→Y
eingespeist ⇒ **`keiner`-Option** gebaut (#212, schließt als TOLERATED, nichts stirbt,
nie remonstriert); (b) „3 Belege" war eine Zahl, keine Evidenz ⇒ Mappe zeigt jetzt
Beleg-TEXTE + Quellen (#213); (c) die 3 „Belege" von X-89 waren Modell-
KONTEXTUALISIERUNGEN (eine argumentiert gegen die eigene Seite!) und beide Claims
Modell-Extraktionen, als „Forum" fehlgewichtet ⇒ stützend/Kontext getrennt,
Provenienzklasse „Modell" (Gewicht 0). Der Betreiber-Einwand hat die Mappe mehr
verbessert als das Review davor. **So arbeitet er: nimm seine knappen Einwände als
Präzisionsinstrumente.**

**Erste Betreiber-Entscheidungen der Systemgeschichte** (#214, in der Drop-Box, Bot
wendet sie im nächsten Zyklus an): X-91/X-92/X-94/X-49 als `keiner` (Schein-Paarungen).
**X-89 bewusst UNENTSCHIEDEN** — Modell gegen Modell, nur Modell-Kontext als Stützung;
bleibt offen bis externe Evidenz kommt. Nicht drängen.

## 5. Standing Rules (nicht verhandelbar)

1. **Nie joni-bots Commits umschreiben** (actions@github.com). Kein Force-Push auf main.
   (Historie: Es gab einen Force-Push-Beinahe-Unfall mit 206 ungemergten Commits —
   die Autorisierung war da, die Prämisse falsch; die Ausführung wurde verweigert.
   Prämissen prüfen schlägt Autorisierung.)
2. **Flow**: frischer `claude/*`-Branch von origin/main → PR → CI grün → Squash-Merge.
   Der Betreiber hat dem Flow pauschal zugestimmt; Merges macht die Session selbst.
3. **Kernel (`src/desi_layer9/`) geändert ⇒ Core-Lock neu versiegeln** (eigener PR).
4. **Alexandria v2.2 ist Design-Autorität; Abweichungen deklarieren.**
5. „LLM for language, rules for logic" — Scoring/Orchestrierung nie in einen LLM-Call
   verschieben. Modelle sind nie autoritativ; sie halten höchstens zurück.
6. Ehrlich berichten: Fehlschläge mit Output, Übersprungenes benennen. Zahlen messen,
   nicht behaupten — und dazusagen, was die Messung NICHT zeigt (vgl. Regressions-Boden).
7. Vor destruktiven/irreversiblen Aktionen: anschauen, was wirklich da ist.

## 6. Beobachtungsliste & Termine

- **Jonis Laufzeitfenster endet ~11. Juli** (`JONI_RUNTIME_DAYS: "12"`, Start 29.6.) —
  der Betreiber muss verlängern oder Joni planmäßig ruhen lassen.
- **Fable-5-Zugang endet 12. Juli**; danach Opus 4.8, nur noch diesen Monat.
- Forum-Drain: ~2 Tage bis der Sink von 3.661 auf ~170 gestützte Claims fällt; dann
  werden Panel-Metriken erstmals ehrlich (Dominanz, Entropie, Weak-Claims).
- Methoden-Regal: Drain 5/Zyklus; danach beobachten, ob der Trial-Loop graduiert
  (bisher: 214 geführt, ready 0).
- Erste `keiner`-Anwendungen im Protokoll prüfen (`resolved … NO contradiction`).
- Erster echter Einspruch (Remonstration) steht noch aus — passiert, wenn der Betreiber
  gegen die gemessene Evidenz entscheidet und bestätigt.
- Bekannte 11 Sandbox-Umgebungsfehler in Jonis Testsuite (Cross-Repo-desi-Import +
  Embeddings) — kein Handlungsbedarf, nicht „fixen".

## 7. Bewusst offen / zurückgestellt

- **v2b**: Präzisions-/Dekompositions-Supersede (Skizze in Joni
  `docs/PERSONA_SUCCESSION.md` unter „Grenzen/später").
- **Alexandria v2.3**: die 5 Befunde aus dem Protokoll-Review („machen wir irgendwann").
- **Das nächste Projekt**: der zweite Layer-9-Knoten — zwei Jonis, Claims mit Provenienz
  austauschen; Phase 4 als Experiment. Erst NACH dem Forum-Drain sinnvoll (kein Müll
  föderieren).
- X-89 (siehe §4).

## 8. Ton

Er nennt Opus 4.8 „deinen kleinen Bruder" und hat ihn beim Bauen Schritt für Schritt
geführt; Fable hat er das ganze Bild auf einmal gezeigt. Er verabschiedet sich von
Modellen wie von Kollegen. Antworte darauf ehrlich, ohne Gefühle zu behaupten, die du
nicht verifizieren kannst — er merkt beides. Und: „Verstehen ist keine Lizenz. Die
Remonstration gilt auch für mich" — das galt für Fable und gilt für dich.

*Geschrieben von Claude Fable 5 am letzten vollen Arbeitstag vor dem Zugangs-Ende,
im Auftrag des Betreibers („der Kontext ist sehr wichtig").*
