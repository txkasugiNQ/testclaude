# NQ Structure Levels – Phase 1: Code-Analyse, Lookahead-Prüfung und Level-Reaktionen

**Umfang dieser Phase** (wie gewünscht): vollständige Analyse des Pine-Indikators, Prüfung auf Lookahead/Repainting, Level-Typen, Feature-Katalog, dann Chart- und Statistik-Untersuchung der Level-Reaktionen.
**Noch keine Strategie.** Alle Statistiken stammen ausschließlich aus dem Trainingszeitraum. VAL und OOS sind unberührt.

Analysierter Code: `pine/NQ_Structure_Levels_original.pine`. Das ist die Datei `ScriptTest` aus dem Branch `claude/vibrant-noether-186jok`, unverändert übernommen.
Forschungscode: `levels_research/`. Ergebnistabellen: `levels_research/results/`. Charts: `levels_research/charts_*`.

---

## 0. Kurzfazit

1. **Die Level-Logik verwendet keine Zukunftsdaten.** Alle Level, Events und Marker entstehen auf geschlossenen Bars. HTF-Daten kommen sauber über `[1]` + `lookahead_on`. Bestätigt ist das mit einem harten Test: Die Python-Replik erzeugt auf abgeschnittenen Daten **bit-identische** Events wie auf der vollen Historie (§6).
   Was sich historisch anders zeigt als in Echtzeit, ist nur die **Zeichnung**. Linien sind auf den Pivot-Zeitpunkt rückdatiert, und es wird nur der aktuelle Level-Bestand gezeichnet (§3).
2. **Strukturproblem des Indikators: Die Level-Datenbank ist gesättigt.** Das Kapazitätslimit von 50 Levels und ein Score, der vor allem Interaktionen zählt (Touches, Rejections, Fakeouts, Retests), wirken zusammen:
   - Auf 1m werden **96,9 % aller neu erzeugten Levels noch im selben Bar wieder gelöscht** (3m: 86,5 %, 5m: 74,2 %).
   - **96,5 % aller Touches** treffen Levels mit Rang „HC“ (3m 92,5 %, 5m 89,9 %).
   - 82 % dieser Touches treffen Levels, die schon ≥10-mal berührt wurden.
   - „High Confluence“ heißt in der Praxis also meist: Hier ist der Preis schon oft hin und her gelaufen. In Trends zeigt der Indikator auf 1m/3m praktisch **keine aktuellen** Levels.
3. **Gegen eine Placebo-Kontrolle haben die Indikator-Levels keinen handelbaren Edge.** Die Kontrolle sind identische Pseudo-Levels ±1 ATR neben jedem echten Level, mit identischer Event-Logik.
   - Touch, Rejection, Sweep, Break, False Break und Retest liefern an echten Levels dieselben Ergebnisse wie an Placebo-Preisen, auf 1m, 3m und 5m.
   - Das gilt auch für die Untergruppen: Indikator-Stärke, Level-Typ, HTF-Herkunft, Anzahl Tests, Alter, Clustering, Key-Level-Nähe und Session.
   - Messbar ist nur ein winziger Reaktionsvorteil von **+2,8 Prozentpunkten** (95 %-KI 1,7–3,9) auf der 2-ATR-Skala (≈ 8 Punkte). Er reicht nicht, um einen Trade profitabel zu machen.
4. **Der einzige robuste, nicht-zufällige Effekt betrifft den ersten Test signifikanter Levels.** Signifikant heißt hier: Session-Key-Levels (ONH/ONL, LDNH/LDNL, pRTH H/L, ORH/ORL), PDH/PDL/PWH/PWL und 1H/4H/D-Pivots. Die eigenen 1m-Swing- und Major-Levels zeigen diesen Effekt nicht.
   - An diesen Levels sagt die Schlussposition der Touch-Kerze die Folgerichtung **stärker voraus** als an Zufallspreisen.
   - Durchbrüche laufen häufiger weiter („Break & Go“ 36–40 % vs. 31 % Placebo). Saubere Rejections sind dort sogar seltener.
   - Als Trade (Train, konservative Ausführung) bringt die Fortsetzung nach einem Erst-Test, der jenseits des Levels schließt, etwa **+0,07 bis +0,12R**. In H1-2024 ist es schwächer als 2023. Das liegt **weit unter dem Ziel von +0,35R**.
5. **Vorläufiges Urteil:** Als Standalone-Signal sind die Levels des Indikators wertlos. Als Kontext gibt es genau einen schwachen, plausiblen Effekt (Erst-Test signifikanter Levels). Ob daraus eine Strategie mit ≥ +0,35R werden kann, ist nach diesen Daten **unwahrscheinlich**. Vorschlag für Phase 2 mit Abbruchkriterium: §9.

---

## 1. Daten und Methodik

| Punkt | Befund |
|---|---|
| Datei | `Dataset_NQ_1min_2022_2025 (1).csv`, unverändert. 1.048.575 1m-Bars, 2022-12-26 18:01 bis 2025-12-11 20:52, 767 Sessions. |
| Zeitstempel | **Bar-Schlusszeit, New York (mit DST).** Für die TradingView-Konvention (Bar-Öffnungszeit) werden intern 1 Minute abgezogen. Das Original wird nicht verändert. |
| Qualität | Keine OHLC-Inkonsistenzen, alles auf dem 0,25-Raster. Einzelne fehlende Minuten in dünnen Nachtstunden (kein Trade). Feiertags-Halbtage. Eine Lücke am 2023-04-05. |
| Kontrakt | Back-adjusted Continuous (vgl. frühere Analyse). Wichtig für TradingView, siehe §10. |
| Trading Day | CME-Session ab 18:00 ET. Dasselbe wie `timeframe.change("D")` in Pine. |
| Splits (fixiert **vor** jeder Level-Statistik, `levels_research/SPLITS.json`) | **TRAIN** 2023-01 → 2024-06 · **VAL** 2024-07 → 2024-12 · **OOS** 2025-01 → 2025-12 |

**Offenlegung:** Außerhalb von TRAIN habe ich nur zwei Dinge gesehen: Event-*Anzahlen* (Log der Engine) und den Median-ATR je Jahr (2025: 6,5 Punkte auf 1m). Ergebnis-, Rendite- oder Trefferquoten-Zahlen für VAL/OOS gibt es keine.
Frühere Sessions in diesem Repo haben 2025 bereits als Holdout für **andere** Hypothesen benutzt (NY-PM-Breakout, London). Für Level-Hypothesen ist 2025 ungesehen, für das Forschungsprogramm insgesamt aber nicht jungfräulich. Siehe §10.

**Arbeitsweise:** Chart → Beobachtung → Hypothese. Regel, Backtest und Validierung folgen erst in Phase 2.

Statistik wird immer **gegen ein Placebo** gerechnet. Ein Ergebnis, das an Zufallspreisen genauso auftritt, ist keine Level-Eigenschaft.

---

## 2. Analyse des Pine-Codes – Antworten auf Fragen 1–10

### 2.1 Wie werden die Levels erzeugt? (Frage 1)

Der Indikator hält eine Datenbank (`array<Level>`) mit maximal 50 Levels. Alle Zeilenangaben beziehen sich auf `pine/NQ_Structure_Levels_original.pine`.

| Quelle (`kind`) | Erzeugung | Bestätigung / frühester Zeitpunkt | Filter |
|---|---|---|---|
| **1 – Minor Swing** | `ta.pivothigh/low(high/low, 5, 5)` (Zeilen 307–308, 720–741) | **5 Bars nach dem Pivot** | Prominenz ≥ 1,0·ATR(21) im 11-Bar-Fenster. Abstand zum letzten gegenläufigen akzeptierten Swing ≥ 1,5·ATR. ≥ 5 Bars zum letzten gleichseitigen Pivot. Volumen optional (aus). |
| **2 – Major Swing** | `ta.pivothigh/low(…, 15, 15)` (Zeilen 743–750) | **15 Bars nach dem Pivot** | Prominenz ≥ 3,0·ATR im 31-Bar-Fenster |
| **3 – Range-Grenze** | Range erkannt, wenn High−Low der letzten 30 Bars ≤ 3·ATR (Zeilen 760–824). Die Range wächst mit jedem neuen Hoch/Tief. | **Erst wenn die Range endet:** Close-Ausbruch ± Puffer oder > 4,5·ATR breit | Dauer ≥ 40 Bars, ≥ 2 Tests je Grenze |
| **4 – HTF-Pivot** | `pivothigh/low(3,3)` auf 5m/15m/(30m)/1H/4H/D via `request.security(…[1], lookahead_on)` (Zeilen 327–357, 753–758) | Auf dem ersten Chart-Bar nach Schluss des HTF-Bars, der den Pivot bestätigt (3 HTF-Bars nach dem Pivot) | keine (jeder HTF-Pivot) |
| **Key-Levels** (PDH/PDL/PDC, PWH/PWL, ONH/ONL, LDNH/LDNL, pRTH H/L, ORH/ORL; PMH/PML optional aus) | Session-Tracker `f_sess` (Zeilen 223–251) | Erst **nach Ende** der jeweiligen Session/Tag/Woche | – |

**Wichtig:** Key-Levels sind **keine** Objekte der Level-Datenbank. Sie werden nur gezeichnet und als Confluence-Zähler (`refCount`) für strukturelle Levels in ihrer Nähe verwendet. Touch/Break/Retest an PDH usw. verfolgt der Indikator nicht.
Für die Forschung habe ich sie deshalb als eigenen Pool mit identischer Event-Logik ergänzt. Das ist klar als Erweiterung gekennzeichnet.

**Merging** (`f_addLevel`, Zeilen 410–449): Ein neuer Preis wird dem **nächstgelegenen** bestehenden Level zugeschlagen, wenn er höchstens `mergeTol` = 0,25·ATR(21) entfernt ist. Auf 1m sind das im Median **1,26 Punkte**.
- Der Level-Preis bleibt dabei der ursprüngliche. Nur die Zone (`top`/`bot`) wächst.
- Treffen Hoch und Tief zusammen, wird das Level zum „FLIP“ (`dir = 0`).
- Ein zweiter Swing in derselben Richtung innerhalb `eqTol` (0,5·mergeTol), mindestens 5 Bars später und mit intaktem Level zählt als **Equal High/Low** (`eqHits`).

### 2.2 Welche Daten werden verwendet? (Frage 2)

- OHLC und Volumen des Chart-Timeframes.
- ATR(21), eine Wilder-RMA auf dem **Chart-TF**.
- Session-VWAP (`ta.vwap(hlc3)`, Reset um 18:00).
- Volumen-SMA(20) für das „volHit“-Flag.
- Zeit/Sessions in America/New_York.
- HTF-OHLC über `request.security`.

**Alle Toleranzen und Längen hängen am Chart-TF** (Bars und ATR des Charts). Derselbe Indikator liefert deshalb auf 1m, 3m und 5m unterschiedliche Level-Sets (§6).

### 2.3 Wann entsteht ein neues Level? (Frage 3)

Ausschließlich auf einem **geschlossenen** Bar (`ready = barstate.isconfirmed`), und zwar zu den Bestätigungszeitpunkten aus 2.1.

Die Reihenfolge pro Bar ist:
1. Interaktionen mit bestehenden Levels.
2. Neue Levels.
3. Scoring und Löschen.

Ein neues Level wird deshalb frühestens auf dem **nächsten** Bar auf Touch/Break geprüft.

### 2.4 Wann wird ein Level verändert oder entfernt? (Frage 4)

**Verändert:**
- Beim Merging: Zone, `dir`, Quellenzähler.
- Bei jeder Interaktion: `touches`, `rejections`, `breakouts`, `fakeouts`, `retests`, `side` (S/R-Flip nach Close-Break).
- Bei jedem Bar: `nearVwap`, `refCount`, wenn sich Key-Levels ändern, und Score/Rang.

**Entfernt** (Zeilen 839–853):
- (a) Mehr als 5 Handelstage ohne Reaktion, oder älter als 10 Handelstage.
- (b) **Kapazität:** Bei mehr als 50 Levels wird das schwächste gelöscht.

Regel (b) dominiert in der Praxis (siehe §4.3).

**Interaktions-Definitionen** (Zeilen 583–714, alle auf Bar-Close):

| Event | Definition im Code |
|---|---|
| Touch | Bar-Range überlappt Zone ± touchTol (≈ 0,63 Punkte auf 1m). Flankengetriggert, Cooldown 3 Bars. |
| Rejection | Bar berührt das intakte Level und **schließt** ≥ 0,3·ATR auf der Anlaufseite (einmal pro Touch) |
| Sweep („liquidity sweep“) | Bar sticht ≥ breakBuf (0,15·ATR) über die Zone und schließt wieder auf der Anlaufseite des Level-Preises |
| Break | **Close** jenseits der Zone + breakBuf. `side` flippt. |
| False Break | Innerhalb von 6 Bars nach dem Break schließt ein Bar wieder auf der alten Seite |
| Retest | Nach dem Break erst ≥ 0,75·ATR weggelaufen, dann zurück an die Zone und Close auf der neuen Seite (≤ 60 Bars) |

### 2.5 Gibt es unterschiedliche Level-Typen? (Frage 5)

Ja, und zwar zwei Dimensionen:
- **Herkunft:** Swing, Major, Range, HTF mit TF-Maske 5m/15m/30m/1H/4H/D, Key-Levels.
- **Charakter:** HIGH, LOW, FLIP, EQH/EQL.

Die Label-Funktion `f_typeName` priorisiert so: MAJOR > RANGE > EQ > SWING > HTF.

### 2.6 Gibt es eine Hierarchie bzw. Stärke? (Fragen 6 und 7)

Ja. Der Score `conf` (Zeilen 471–492) setzt sich so zusammen:

| Komponente | Gewicht × Deckel |
|---|---|
| Swing | 1,0 × min(swingHits, 2) |
| Major | 1,5 |
| Range | 1,5 × min(rangeHits, 2) |
| Equal H/L | 1,5 × min(eqHits, 2) |
| MTF | 1,0 × min(Σ TF-Gewichte, 4). TF-Gewichte: 5m 0,5 · 15m 0,75 · 1H 1,25 · 4H 1,5 · D 2,0 |
| Key-Level in Zone | 1,5 × min(refCount, 3) |
| VWAP in der Nähe | 0,5 |
| Touches | 0,5 × min(touches, 6) |
| Rejections | 0,75 × min(rejections, 4) |
| Retests | 1,0 × min(retests, 3) |
| Fakeouts/Sweeps | 1,25 × min(fakeouts, 3) |
| Volumen-Spike | 0,5 |
| Displacement | 1,0 |
| Chop-Strafe | −0,5 × min(max(breakouts − retests − fakeouts − 1, 0), 4) |

Daraus wird `strength = conf × 0,85^(Handelstage seit letzter Reaktion)`. Ränge: Weak < 3 ≤ Moderate < 5 ≤ Strong < 7 ≤ HC.

**Als Feature verwertbar** (im Event-Log der Replik enthalten, jeweils als Zustand **vor** dem Event):
- `strength`, `conf`, `rank`
- alle Einzelkomponenten
- Alter in Bars/Tagen
- „Quiet Days“
- Zonenbreite
- Herkunftsmaske und HTF-Maske
- Zahl anderer Levels und Key-Levels im Umkreis von 0,5/1/2 ATR, Abstand zum nächsten Level

**Problem:** Bis zu 12,75 Punkte des Scores stammen aus **Interaktionen** (Touches, Rejections, Retests, Fakeouts). Der Score ist damit zirkulär: Ein Level, um das der Preis viel herumpendelt, wird „stark“. Das zeigt sich empirisch in §4.3.

### 2.7 Zukunftsdaten, Pivot-Bestätigung, Repainting? (Frage 8)

Siehe §3. Kurz:
- Die Pivots sind **korrekt verzögert**. Das Level wird erst zum Bestätigungszeitpunkt in die Datenbank aufgenommen.
- HTF ist sauber.
- Es gibt kein Repainting der Logik.

### 2.8 Kann ein Level historisch anders aussehen als in Echtzeit? (Frage 9)

**Logisch nein** (Abschneide-Test, §6). **Visuell ja**, und das ist für die Chart-Beurteilung wichtig:
1. **Rückdatierte Linien.** `line.new(lv.bornTime, …)` zeichnet ab der Pivot-Zeit, bei Ranges ab dem Range-Start. In Echtzeit existierte das Level aber erst 5, 15 oder ≥ 40 Bars später. Im Chart sieht es so aus, als hätte der Preis an einer Linie reagiert, die zu diesem Zeitpunkt noch gar nicht bekannt war. Das ist der klassische visuelle Lookahead-Effekt.
2. **Nur der aktuelle Bestand wird gezeichnet.** Gezeichnet wird ausschließlich auf `barstate.islast`. Beim Zurückscrollen sieht man die *heutigen* Levels, nicht die damals existierenden. Gelöschte Levels sind unsichtbar.
3. Zone, Farbe (Res/Sup relativ zum **aktuellen** Close), Label, Stärke und Tabelle zeigen immer den aktuellen Zustand.
4. „dev“-Elemente (laufende Session-H/L, laufende Range) ändern sich in Echtzeit, so gewollt.
5. **Abhängigkeit vom Historienstart.** Der Zustand (lastSHp/lastSLp, Range, Kapazitäts-Pruning) hängt kurz vom ersten geladenen Bar ab. Durch die 10-Tage-Regel konvergiert er. Auf einem 1m-Chart mit wenigen Wochen Historie können aber die ersten Tage abweichen.

Die **Marker** (`plotshape`) und Alerts (`freq_once_per_bar_close`) erscheinen auf dem Bestätigungsbar und sind nicht rückdatiert.

### 2.9 Was kann 1:1 in Backtest- und Bot-Logik übernommen werden? (Frage 10)

Die Abschnitte 1–3 des Codes übernehme ich vollständig: Interaktionen, Level-Erkennung, Scoring und Pruning. Sie sind in `levels_research/engine.py` repliziert (numba, ≈ 2,5 min für 3 Jahre 1m).

Diese Details sind **gegen TradingView zu verifizieren**, bevor ein Bot sich exakt darauf verlässt:
- **Gleichstand-Regel von `ta.pivothigh/low`:** Ich nehme konservativ an, dass bei gleichen Extremen der rechte Bar der Pivot ist. Das ergibt die spätere Bestätigung.
- **Ausrichtung der 4H-Bars:** angenommen ist Session-verankert ab 18:00 ET.
- **ATR-Seed:** SMA der ersten 21 TR.
- **VWAP-Anker:** Session.
- **Session-Grenzen bei Datenlücken.**

Empfehlung: Ein kurzer Paritätstest. Dafür im Pine `plot(levels.size())` und z. B. die Touch-Zähler ausgeben und mit der Replik an denselben Tagen vergleichen.

---

## 3. Lookahead und Repainting – Detailprüfung

| Stelle | Bewertung |
|---|---|
| `ta.pivothigh/low(·, L, L)` | Liefert den Wert erst L Bars nach dem Pivot. Das Level wird auch erst dann angelegt. Prominenz-, Displacement- und Volumenfenster enden am aktuellen Bar. ✅ |
| `request.security(tf, f_htfPiv()[1], lookahead_on)` + `timeframe.change(tf)` | Standard-Idiom ohne Repainting: Es wird nur der Wert des zuletzt **geschlossenen** HTF-Bars verwendet. ✅ |
| PDH/PDL/PDC/PWH/PWL | Werden beim ersten Bar des neuen Tages bzw. der neuen Woche aus dem abgeschlossenen Zeitraum gesetzt. ✅ |
| ON/London/RTH/OR H/L | `last*` erst nach Session-Ende, `orToday` korrekt. ✅ |
| Range-Levels | Erst beim Range-Ende in der Datenbank, mit Preis = max/min der Range. ✅ (Zeichnung aber ab Range-Start, siehe 2.8) |
| VWAP-Nähe | Aktueller, geschlossener Bar. Schwankt mit dem VWAP. Kein Repaint. ✅ |
| `refCount` | Wird nur bei Änderung der Key-Levels neu berechnet und nutzt dann die damalige mergeTol. Leicht „stale“, aber deterministisch. ✅ |
| Datenbank-Updates | Nur bei `barstate.isconfirmed`. Echtzeit und Historie verhalten sich deshalb gleich. ✅ |
| Zeichnung | Rückdatiert, nur aktueller Bestand, siehe 2.8. ⚠️ nur visuell |

**Es musste für die Forschung nichts korrigiert werden.** Ich verwende ausschließlich den Event-Zeitpunkt, also den Bar, an dem das Level in die Datenbank kommt. Die rückdatierte Linie verwende ich nie. Ein Level ist im Backtest ab dem Bar **nach** seiner Aufnahme nutzbar.

---

## 4. Level-Typen in der Praxis (TRAIN, 1m, Indikator unverändert)

### 4.1 Wie viele Levels entstehen pro Tag?

| Quelle | neu/Tag | zusätzlich gemerged/Tag |
|---|---|---|
| Minor Swing (1m) | 130,6 | 29,9 |
| HTF-Pivot | 58,0 (5m 39,9 · 15m 13,4 · 1H 3,5 · 4H 1,0 · D 0,2) | 17,4 |
| Major Swing (1m) | 45,0 | 12,9 |
| Range | 1,2 | 0,4 |

### 4.2 Toleranzen auf 1m

ATR(21) liegt im Median bei 3,8 (2023) und 4,9 (2024) Punkten. Daraus folgen:
- mergeTol ≈ 1,26 Punkte
- touchTol ≈ 0,63 Punkte
- Break-Puffer ≈ 0,6–0,7 Punkte

Das sind sehr enge Zonen.

### 4.3 Sättigung der Datenbank – das zentrale Strukturproblem

| | 1m | 3m | 5m |
|---|---|---|---|
| neu erzeugte Levels, die **im selben Bar** wieder gelöscht werden | **96,9 %** | 86,5 % | 74,2 % |
| Anteil aller Touches an Levels mit Rang HC | **96,5 %** | 92,5 % | 89,9 % |
| Anteil aller Touches an Levels mit ≥ 10 Vor-Touches | 82 % | 68 % | 59 % |
| Median-Stärke beim Touch (HC-Schwelle 7) | 19,3 | – | – |

Der Mechanismus: Die Datenbank ist fast immer voll (Median 50/50). Neue Levels starten mit einem Score von etwa 1–3. Bestehende Levels haben durch Interaktionen 15–25. Deshalb wird praktisch jedes neue Level sofort als schwächstes gelöscht.

Auf 1m überleben nur etwa **7 neue Levels pro Tag**. Diese bleiben dann im Median **7 Handelstage** stehen, bis die Altersregel greift.

**Folgen:**
- Was der Indikator als „HC“ zeigt, sind überwiegend alte **Chop-Zonen**.
- Die Klassen Weak/Moderate/Strong/HC unterscheiden praktisch nichts.
- Im Trend erscheinen keine aktuellen Levels.

Die Charts zeigen genau das (§7).

---

## 5. Feature-Katalog

Diese Features lassen sich ohne Lookahead aus dem Indikator gewinnen. Alle sind in `engine.py` als Zustand vor dem Event geloggt.

| Gruppe | Features |
|---|---|
| Herkunft | swing / major / range / HTF; HTF-TF-Maske (5m…D); dir (High/Low/Flip); Equal H/L (`eqHits`) |
| Stärke | `conf`, `strength`, `rank`, Einzelkomponenten, `volHit`, `dispHit`, `nearVwap`, `refCount` (Key-Level in der Zone) |
| Historie | Alter (Bars, Tage), Tage seit letzter Reaktion, `touches`/`rejections`/`breakouts`/`retests`/`fakeouts` bis zum Event (= n-ter Test), `side` |
| Kontext | Zahl anderer struktureller Levels und Key-Levels innerhalb 0,5/1/2 ATR (Clustering); Abstand zum nächsten Level und Key-Level; Level innerhalb oder außerhalb der bisherigen Tagesrange; Key-Level-Art; Uhrzeit/Session; ATR |
| Event | Touch, Rejection, Sweep, Break, False Break, Retest (Definitionen 2.4); Schlussposition der Event-Kerze relativ zum Level |

---

## 6. Python-Replik und Tests

- `engine.py` bildet Abschnitte 1–3 des Pine-Codes Bar für Bar in derselben Reihenfolge nach. Zusätzlich gibt es zwei Forschungspools:
  - **Key-Levels als eigene Objekte** mit derselben Event-Logik.
  - **Placebo-Levels:** zwei Pseudo-Levels ±1·ATR neben jedem neu erzeugten Level, mit identischer Event-Logik.
- **Lookahead-Test (`06_lookahead_test.py`):** Die Engine läuft auf Daten, die bei Bar 150.000 bzw. 333.333 abgeschnitten sind. Alle 416.910 bzw. 902.878 Events vor dem Schnitt sind mit dem Vollhistorie-Lauf **identisch**. Damit ist bewiesen, dass keine Zukunftsinformation einfließt (inklusive HTF und Sessions).
- **Variante „v2“ (nur Forschung):** gleiche Generatoren und Events, aber:
  - kein 50er-Kapazitätslimit;
  - ein gebrochenes Level wird nur noch für das False-Break/Retest-Fenster verfolgt und dann entfernt;
  - Merging nur in intakte Levels.

  Damit gibt es „n-ter Test eines intakten Levels“ und frische Levels überhaupt erst. Der v2-Pool hat im Mittel 54 aktive Levels, und es gibt etwa 240 Touches pro Tag.
- **In dieser Phase gefundene und behobene Fehler:**
  1. Die 3m/5m-Aggregation hatte die Zeitstempel falsch rekonstruiert (µs/ns). Betroffen waren Sessions und HTF auf 3m/5m. Der Fehler ist behoben, alle 3m/5m-Ergebnisse sind neu gerechnet.
  2. Die Regel „flat 15:55“ hat auch Trades zwischen 18:00 und 24:00 sofort geschlossen. Jetzt wird session-relativ gerechnet, alle Event-Studien sind neu gerechnet. Beide Fehler betrafen echte und Placebo-Levels gleich, die Schlussfolgerungen haben sich nicht geändert.

---

## 7. Chart-Untersuchung (CHART → OBSERVATION)

`05_charts.py` erzeugt **60 zufällige 1m-Fenster** (3 h) und **40 zufällige 3m-Fenster** (8 h), alle aus TRAIN, 03:00–16:00 ET. Die Startzeitpunkte sind zufällig, nichts ist ausgewählt.

Jedes Level wird **erst ab dem Bar nach seiner Aufnahme** gezeichnet und endet bei der Löschung. Das ist eine echte Point-in-Time-Darstellung, anders als im Indikator selbst. Dazu kommen Key-Levels (gestrichelt) und alle Events. Dateien: `levels_research/charts_1m/`, `levels_research/charts_3m/`.

Zusätzlich gibt es je **16 zufällige Erst-Tests** von Key-Levels, 1H/4H/D-Pivots und Placebo-Levels mit Verhaltens-Klassifikation: `levels_research/examples_firsttouch_*.png`.

**Wiederkehrende Beobachtungen:**
1. **In Trendphasen zeigt der Indikator keine strukturellen Levels im Preisbereich.** Beispiele: 1m #9 (2023-03-31), #0 (2023-01-25). Neue Levels erscheinen nur als winzige Striche, weil sie sofort gelöscht werden.
2. **Sichtbare Levels bilden dichte „Level-Felder“** alter Major-Pivots in früheren Konsolidierungen, mit 10–30 Linien auf 30–60 Punkten. Beispiele: 3m #27 (2024-02-06), #35 (2024-04-15), #5 (2023-03-13), 1m #31. Dort feuert fast **jede** Kerze ein Touch/Reject/Sweep/Retest-Event. Die Events sind dort bedeutungslos.
3. **Rückkehr in ein altes Level-Feld führt eher zu Stocken und Chop als zu einer sauberen Umkehr.** Beispiele: 3m #19, #27.
4. **Key-Levels** (ONH/ONL, LDNH/LDNL, PDH/PDL, ORH/ORL) werden häufig **ohne Zögern durchlaufen**, wenn der Preis mit Momentum ankommt (z. B. 3m #11, 09:36, ONL/PDL). Wenn die Touch-Kerze dagegen deutlich auf der Anlaufseite schließt, folgt oft eine kräftigere Gegenbewegung als an beliebigen Preisen (Grid-Beispiele).
5. **PDC wird oft direkt zur Session-Eröffnung um 18:00 „berührt“.** Das ist trivial, weil der Settlement-Preis ≈ Eröffnungspreis ist. Für Phase 2 ausschließen.

Aus diesen Beobachtungen ergaben sich die Hypothesen, die in §8 statistisch geprüft wurden.

---

## 8. Statistische Untersuchung (nur TRAIN)

### 8.1 Placebo-Design

Zu jedem neu erzeugten Level werden zwei Pseudo-Levels im Abstand ±1·ATR angelegt. Sie haben dieselbe Event-Logik und dieselbe Lebensdauerregel. Gleiche Zeit, gleicher Markt, gleiche Volatilität, nur **kein** strukturell begründeter Preis.

Wenn echte Levels nicht besser sind als Placebo, ist der Effekt keine Level-Eigenschaft.

### 8.2 Reaktion am Level (Barrier-Race, Indikator unverändert, 1m)

Gemessen wird, ob der Preis vom Level aus **zuerst** ±X in Reaktionsrichtung oder ±X durch das Level läuft. Basis sind Touches, deren Kerze auf der Anlaufseite schließt.

| | X = 1 ATR | 2 ATR | 4 ATR |
|---|---|---|---|
| Indikator-Level, isoliert | 0,767 | 0,649 | 0,578 |
| Placebo, isoliert | 0,714 | 0,621 | 0,570 |
| Key-Level, isoliert | 0,703 | 0,609 | 0,559 |

Differenz Indikator − Placebo bei 2 ATR: **+2,8 pp** (Day-Block-Bootstrap, 95 %-KI 1,7–3,9).
Der Effekt ist real, aber klein, und er verschwindet mit der Skala. Bei 4 ATR (≈ 16 Punkte) ist er praktisch weg. Auf 3m und 5m ergibt sich dasselbe Bild.

### 8.3 Event-Studie: jedes Indikator-Event als „natürlicher“ Trade (v2)

**Aufbau:**
- **Entry:** Open des nächsten Bars.
- **Stop:** strukturelle Invalidierung (jenseits Kerzen-Extrem bzw. Level) + Puffer 0,15·ATR + 1 Tick.
- **Ziele:** fixe Ziele 0,25–2R.
- **Ausführung:** konservativ. SL und TP im selben Bar zählt als Verlust. Ein Stop-Touch im Entry-Bar zählt als Verlust.
- **Exit:** flat 15:55 oder nach 240 Minuten.
- **Filter:** nur Trades mit Risiko ≥ 4 Punkte, wo vermerkt.

**1m, Erwartungswert in R (TRAIN):**

| Event | Gruppe | n | Risiko (Pkt) | E@0,25R | E@0,5R | E@1R | E@2R |
|---|---|---|---|---|---|---|---|
| Rejection | Indikator | 58.260 | 4,2 | −0,090 | −0,048 | −0,014 | −0,003 |
| | Placebo | 115.143 | 4,1 | −0,090 | −0,047 | −0,010 | +0,009 |
| Sweep | Indikator | 33.580 | 4,3 | −0,110 | −0,061 | −0,020 | −0,006 |
| | Placebo | 70.008 | 4,3 | −0,113 | −0,062 | −0,019 | +0,006 |
| Break | Indikator | 68.404 | 3,4 | −0,195 | −0,130 | −0,062 | −0,018 |
| | Placebo | 138.750 | 3,2 | −0,211 | −0,143 | −0,068 | −0,016 |
| False Break | Indikator | 25.613 | 5,3 | −0,046 | −0,020 | +0,001 | +0,014 |
| | Placebo | 52.970 | 5,1 | −0,048 | −0,024 | −0,004 | +0,011 |
| Retest | Indikator | 34.375 | 3,6 | −0,158 | −0,101 | −0,047 | −0,013 |
| | Placebo | 68.332 | 3,5 | −0,167 | −0,109 | −0,044 | −0,014 |

Die 3m- und 5m-Tabellen (`results/es_3m_v2.txt`, `results/es_5m_v2.txt`) sind qualitativ identisch.

Die Werte nahe 0 bzw. negativ bei kleinen Zielen sind der Preis der konservativen Ausführung. Bei einem Zufallsentry wäre das Ergebnis genauso. **Echte Levels unterscheiden sich nirgends nennenswert vom Placebo.**
Hohe Trefferquoten (≈ 75 % bei +0,25R) entstehen an jedem beliebigen Preis und bedeuten hier keinen Edge.

### 8.4 Untergruppen A–H (Rejection, Sweep, False Break, Break; Risiko ≥ 4 Punkte; E@1R, getrennt nach 2023 und H1-2024)

Volle Tabellen: `results/subsets_1m_v2.txt`.

| Frage | Ergebnis |
|---|---|
| **A Touch** | Negativ wie Placebo (konservative Kosten). Kein Level-Effekt. |
| **B Rejection** | Indikator −0,014R vs. Placebo −0,010R. Kein Unterschied. |
| **C Sweep/Reclaim** | Indikator −0,020R vs. Placebo −0,019R. Kein Unterschied. Auch mehrere Bars (False Break) ≈ 0. |
| **D Break** | −0,062R vs. −0,068R. Kein Unterschied. Alte Levels (> 24 h) +0,02R, nicht signifikant. |
| **E Break + Retest** | −0,047R vs. −0,044R. Kein Unterschied. |
| **F Mehrfachtests** | 1., 2., 3.+ Test ohne konsistentes Muster. Unterschiede ±0,03R, Vorzeichen wechseln zwischen den Hälften. |
| **G Stärke** | Weak/Mod/Strong/HC liefern dasselbe Ergebnis (z. B. Rejection: −0,011 / −0,022 / +0,001 / −0,008R). **Der Indikator-Score trennt nichts.** Alter > 24 h ist für Reaktions-Trades konsistent *schlechter* (−0,05 bis −0,09R). |
| **H Clustering** | Mehr Levels innerhalb 0,5 ATR macht Touches **schlechter**, bei echten *und* Placebo-Levels gleichermaßen. Dichte Zonen werden eher durchlaufen bzw. chopped. Confluence-Zonen bringen **keinen** Vorteil. Key-Level in der Nähe: neutral. |
| Level-Typ | Swing, Major, HTF-Maske ≈ Placebo. „HTF-only“ und Range haben zu kleine Stichproben (n ≈ 300). |
| Equal Highs/Lows | Kein Unterschied (Verhaltens-Klassen ±1 pp). |
| Session | Unterschiede gibt es nur zwischen Sessions, nicht zwischen echt und Placebo. NY-Eröffnung und Premarket sind für Reaktionen am schlechtesten, Asien/London am ruhigsten. |

### 8.5 Was passiert typischerweise nach einem Level-Kontakt? (15 Bars, 1m)

| Gruppe | Break&Go | Chop | saubere Rejection | Sweep+Reclaim | n |
|---|---|---|---|---|---|
| Placebo, 1. Test | 0,313 | 0,237 | 0,104 | 0,345 | 79.513 |
| Swing (1m), 1. Test | 0,313 | 0,248 | 0,100 | 0,339 | 25.941 |
| Major (1m), 1. Test | 0,327 | 0,228 | 0,098 | 0,347 | 14.009 |
| **HTF ≥ 1H, 1. Test** | **0,373** | 0,221 | **0,067** | 0,339 | 1.166 |
| **Key-Level, 1. Test** | **0,362** | 0,232 | **0,069** | 0,338 | 2.773 |
| Key-Level, außerhalb der Tagesrange | **0,395** | 0,224 | 0,053 | 0,328 | 1.085 |

Die Verhaltensverteilung an den 1m-Swing- und Major-Levels des Indikators ist **identisch** mit Placebo.
Nur **signifikante** Levels (Key, HTF ≥ 1H) weichen ab, und zwar in Richtung **Durchbruch/Fortsetzung**. Besonders deutlich ist das, wenn das Level zugleich ein neues Tageshoch oder -tief bedeutet.

### 8.6 Erst-Test signifikanter Levels: Die Schlussposition der Touch-Kerze entscheidet

P(10 Punkte in Reaktionsrichtung vor 10 Punkten in Gegenrichtung), aufgeschlüsselt nach Schlussposition der Touch-Kerze in ATR (+ = Anlaufseite, − = jenseits des Levels):

| Close-Position | Session-Key | HTF ≥ 1H | PD/PW | Placebo | Swing/Major |
|---|---|---|---|---|---|
| ≤ −1 | 0,054 | 0,120 | 0,107 | 0,171 | 0,182 |
| −1 … −0,25 | **0,208** | 0,282 | 0,264 | 0,365 | 0,370 |
| −0,25 … 0 | 0,419 | 0,411 | 0,350 | 0,479 | 0,479 |
| 0 … 0,5 | 0,607 | 0,562 | 0,556 | 0,575 | 0,565 |
| 0,5 … 1 | **0,827** | 0,718 | 0,596 | 0,672 | 0,661 |
| 1 … 2 | 0,900 | 0,779 | 0,732 | 0,780 | 0,761 |

Bei gleicher Schlussposition ist die Folgebewegung an Session-Key-Levels deutlich **entschiedener** als an Zufallspreisen. Das gilt in beide Richtungen. Stabilität (gehalten, P10): 2023 0,741, H1-2024 0,676, Placebo jeweils 0,63. Der Effekt ist in beiden Hälften positiv, in 2024 kleiner.

**Als Trade** (Entry nächstes Open, Stop jenseits des Extrems der Touch-Kerze, konservativ, TRAIN):

| Setup | Gruppe | n | Risiko (Pkt) | E@0,5R | E@0,75R | E@1R | E@2R |
|---|---|---|---|---|---|---|---|
| **ACC**: Erst-Test schließt ≥ 0,25 ATR jenseits → Fortsetzung | Session-Key | 595 | 18,6 | +0,089 | +0,111 | +0,091 | +0,075 |
| | PD/PW | 281 | 10,6 | +0,068 | +0,109 | +0,123 | +0,124 |
| | HTF ≥ 1H | 377 | 14,4 | +0,034 | +0,071 | +0,072 | +0,080 |
| | Placebo | 16.369 | 8,3 | −0,012 | −0,008 | −0,012 | −0,016 |
| **REJ**: Erst-Test schließt ≥ 0,5 ATR auf Anlaufseite → Fade | Session-Key | 440 | 11,4 | +0,007 | −0,001 | −0,007 | −0,045 |
| | HTF ≥ 1H | 281 | 8,1 | −0,027 | +0,028 | +0,058 | −0,048 |
| | Placebo | 18.700 | 4,5 | −0,040 | −0,024 | −0,013 | +0,004 |

ACC an Session-Key-Levels nach Hälften (E@1R): 2023 +0,142, H1-2024 −0,015.

**Interpretation:** Der einzige Level-Effekt, der sich vom Placebo abhebt, ist ein **Akzeptanz/Fortsetzungs-Effekt** beim ersten Test signifikanter Referenz-Levels. Er tritt etwa 1–3-mal pro Tag auf, liefert in-sample nur +0,07 bis +0,12R und schwächt sich 2024 ab.
Die Fade-Seite (Rejection) ist trotz besserem Barrier-Race als Trade nicht profitabel. Der Grund: Der Stop jenseits des Kerzen-Extrems ist im Verhältnis zur Reaktion zu groß.

---

## 9. Was folgt daraus? – Hypothesen für Phase 2

**Verworfen** (in TRAIN kein Unterschied zum Placebo, nicht weiter verfolgen):
- Touch, Rejection, Sweep, Break, False Break und Retest an den **1m-Swing/Major/Range-Levels** des Indikators.
- Der Indikator-Score und seine Klassen.
- Mehrfachtests.
- Confluence-Cluster aus Indikator-Levels.
- Equal Highs/Lows.

**Einzige Kandidaten-Familie** (aus TRAIN abgeleitet, VAL/OOS unberührt): **H-ACC – Akzeptanz beim ersten Test signifikanter Referenz-Levels.**
Levels: ONH/ONL, LDNH/LDNL, pRTH H/L, ORH/ORL, PDH/PDL, PWH/PWL, 1H/4H/D-Pivots. PDC ist ausgeschlossen.
Zu prüfende Varianten. Jede ist einfach, jede wird zuerst auf TRAIN entwickelt und dann **einmal** auf VAL geprüft:
1. **Direkt-Entry** nach Close jenseits des Levels (wie oben), aber mit einem Stop an echter Invalidierung (Level-Rückeroberung) statt am Kerzen-Extrem. Die heutigen R sind wegen Stops von 15–19 Punkten unnötig groß.
2. **Erster Pullback/Retest** an das gerade akzeptierte Level (Limit am Level, Stop jenseits). Das ergibt kleineres R, eine höhere Trefferquote ist möglich.
3. **Exits per MAE/MFE-Analyse:** Fixed vs. BE/Trailing vs. Teil-TP.
4. **Kontext-Features, eines nach dem anderen**, jeweils nur bei messbarem Mehrwert: Level außerhalb der Tagesrange, Session (London/NY), kurzfristige Vola.

**Abbruchkriterium**, vorab festgelegt: Wenn keine Variante auf TRAIN **und** VAL jeweils ≥ +0,25R bei ≥ 150 Trades erreicht, bauen wir keine Strategie. Dann ist das Ergebnis „Die Levels haben keinen ausreichenden Edge“, und das sage ich auch so.
Das Ziel von +0,35R vor Kosten ist nach den Daten dieser Phase **nicht wahrscheinlich**. Der Effekt ist etwa 3–4-mal zu klein.

---

## 10. Offene Punkte und Risiken

- **TradingView-Parität:** Pivot-Gleichstände, 4H-Ausrichtung und Historienstart (siehe 2.9). Vor jeder Pine-Strategie ist ein Paritätstest nötig.
- **Back-adjusted Daten:** Die CSV ist rückadjustiert. Auf TradingView mit `NQ1!` **ohne** „Back-adjust“ springen Preise am Rollover. Levels, die über den Rollover hinweg leben (bis zu 10 Tage), lägen dort verschoben. Für einen Bot muss die Level-Historie am Roll zurückgesetzt oder adjustiert werden.
- **„Frisches“ OOS:** 2025 ist für Level-Hypothesen ungesehen, wurde in diesem Repo aber schon für andere Strategien als Holdout verwendet. Für einen wirklich unabhängigen Test empfehle ich zusätzliche NQ-1m-Daten aus der Zeit vor 2023 (z. B. 2019–2022).
- **Volatilitäts-Regime:** Der 1m-ATR stieg von 3,8 (2023) über 4,9 (2024) auf 6,5 (2025) Punkte. Alle Regeln müssen ATR-skaliert sein.

---

## 11. Dateien

| Datei | Inhalt |
|---|---|
| `pine/NQ_Structure_Levels_original.pine` | Original-Indikator (unverändert) |
| `levels_research/engine.py` | Bar-genaue Replik + Forschungspools (Key, Placebo) + v2-Modus |
| `levels_research/outcomes.py` | Barrier-Race, MFE/MAE, konservative Fixed-R-Simulation |
| `01_load.py` … `12_example_grid.py` | Laden/Integrität, Engine-Lauf, Population, Placebo-Race, Charts, Lookahead-Test, Event-Studie, Untergruppen, Erst-Test-Analyse, Verhaltensklassen, Beispiel-Grids |
| `levels_research/results/*.txt` | alle Ergebnistabellen dieser Phase (nur TRAIN) |
| `levels_research/charts_1m/`, `charts_3m/` | 60 + 40 zufällige Point-in-Time-Charts (TRAIN) |
| `levels_research/examples_firsttouch_*.png` | je 16 zufällige Erst-Tests: Key, HTF ≥ 1H, Placebo |
| `levels_research/SPLITS.json` | fixierte Splits + Offenlegung |

Reproduktion: `cd levels_research && python3 01_load.py && python3 02_run.py 1 && python3 02_run.py 1 v2 && …`. Benötigt pandas, numpy, numba und matplotlib.
