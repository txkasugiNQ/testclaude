# NQ-Strategie-Research: Ziel ≥ 90 % Winrate bei RR 0,6

**Ergebnis vorweg:** Eine Strategie mit ≥ 90 % Walk-Forward-OOS-Winrate bei RR 0,6 habe ich **nicht gefunden**. Dasselbe gilt für jede Abstufung bis 80 %, und auch 70 % sind nicht robust erreichbar.

Die beste robuste Version ist **MBC (Momentum Burst Continuation)**:

| Kennzahl | Wert |
|---|---|
| Walk-Forward-OOS-Winrate (2024–2025, Parameter je Quartal nur aus den Vormonaten gewählt) | **64,7 %** |
| Mit den heute eingefrorenen Parametern, 2023–2025 | 65,1 % |
| Zufalls-Winrate bei RR 0,6 (nach Kosten) | 61–62 % |
| Profit Factor | 1,07–1,10 |
| Trades pro aktivem Tag | 2,26 |

Alle Zahlen stammen aus Python-Backtests auf der CSV. **Ein TradingView-Backtest wurde nicht ausgeführt.** Der Pine-Code konnte hier auch nicht kompiliert werden.

Code: `research/` (Engine, Familien, Walk-Forward, Replik) · Indikator: `pine/MBC_Momentum_Burst_RR06.pine`

---

## 1. Warum 90 % bei RR 0,6 praktisch nicht erreichbar sind

**Optional-Stopping-Theorem:** Ist der Preis kurzfristig ein Martingal (keine vorhersagbare Drift), ist der erwartete Exit-Preis *jeder* Regel gleich dem Entry. Bei TP = 0,6R und SL = 1R folgt daraus:

P(Win) · 0,6 = (1 − P(Win)) · 1 → **P(Win) = 62,5 %**

Das gilt unabhängig von Entry-Regel, Stop-Größe oder Filter. Für 90 % müsste jeder Trade im Mittel **+0,44R** Drift in Trade-Richtung enthalten. Bei mehreren Trades pro Tag wäre das eine der profitabelsten Strategien überhaupt, und so etwas müsste sich in frei verfügbaren OHLCV-Daten verbergen.

Die Daten bestätigen das Theorem:

| Test | Winrate |
|---|---|
| Zufalls-Entries, realistische Kosten | 60–61,6 % |
| Zufalls-Entries, ohne Kosten, TP-Fill schon bei Berührung | 63,2 % |
| Lag-1-Autokorrelation der 1/5/15/30-min-Returns | ≈ 0 |

## 2. Methodik (gegen Selbstbetrug)

**Fills und Kosten:**
- Signal am **Bar-Schluss**, Market-Entry zur **Open der nächsten Bar** plus 1 Tick Slippage
- Limit-Entries nur, wenn der Preis 1 Tick **durch** das Limit handelt
- TP muss 1 Tick durchgehandelt werden
- SL mit 1 Tick Slippage; bei einer Kurslücke über den Stop wird zur Open ausgeführt
- SL und TP in derselben Bar zählen als **Verlust**
- Kommission und Gebühren: 0,25 Punkte Round-Trip
- Win = Netto-PnL > 0
- Zwangs-Exit am Close der 15:59-Bar
- Nur eine Position bzw. offene Order gleichzeitig

**Walk-Forward:**
- 12 Monate Training, 3 Monate Test, rollierend
- 8 OOS-Quartale (Q1/2024–Q4/2025), zusammengeführt
- In jedem Fenster wählt ein **vorher festgelegtes Kriterium** die Parameter aus, nur auf Trainingsdaten: maximale Winrate bei einer Mindest-Trade-Frequenz
- Danach eingefroren und auf das unbekannte Quartal angewendet

**Explorative Suche** (Ideen, Feature-Scans) nur auf 2023.

**Lookahead-Fund während des Research:** Die Engine hat zunächst ungefüllte Limit-Orders nicht als „belegt“ gewertet. Ein späteres Signal durfte dadurch zum Zuge kommen, obwohl man zum Zeitpunkt des zweiten Signals noch nicht wissen konnte, ob die erste Order gefüllt wird. Nach der Korrektur:

| Version | OOS vorher | OOS nachher |
|---|---|---|
| Impuls-Retracement-Limit (F14) | 65,4 % | **60,1 %** |
| dito mit Regimefilter (F14b) | 69,9 % | **64,2 %** |

Alle Zahlen in diesem Bericht sind korrigiert.

## 3. Getestete Hypothesen (Research-Tabelle)

22 Setup-Familien mit insgesamt **2 705 Parameterkombinationen**, dazu zwei ML-Obergrenzen-Tests. „fmin“ = geforderte Mindest-Trades/Tag im Training. Vollständige CSV: `research/research_table.csv`.

| Version | Idee | Kombis | fmin | WR IS (Train) | **WR WF-OOS** | N OOS | PF | Exp R | MaxDD R | Max. Verlustserie | Trades/aktiver Tag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | VWAP-σ-Band Re-Entry | 64 | 0,5 / 2 | 65,6 / 62,4 | **61,6 / 61,8** | 675 / 1417 | 0,95 / 0,94 | −0,02 | 32 / 57 | 6 / 8 | 2,2 / 3,3 |
| F2 | Trend-Pullback EMA/VWAP | 96 | 0,5 / 2 | 65,5 / 64,8 | **60,6 / 61,7** | 827 / 1496 | 0,89 / 0,93 | −0,04 / −0,03 | 54 / 58 | 6 / 8 | 2,8 / 3,2 |
| F3 | Opening-Range-Breakout | 36 | 0,5 | 66,1 | **58,7** | 477 | 0,84 | −0,07 | 40 | 7 | 1,2 |
| F4 | OR-Fake-Out-Fade | 24 | 0,5 | 65,0 | **62,5** | 522 | 0,95 | −0,02 | 31 | 7 | 1,2 |
| F5 | RSI-Extrem + Trendfilter | 112 | 0,5 / 2 | 66,9 / 62,3 | **60,4 / 59,5** | 389 / 1293 | 0,88 / 0,84 | −0,05 / −0,07 | 29 / 97 | 6 / 8 | 1,6 / 2,9 |
| **F6** | **Momentum-Burst-Fortsetzung** | 64 | 0,5 / 2 | 67,1 / 64,9 | **64,9 / 62,6** | 692 / 1952 | **1,08** / 0,98 | **+0,03** / −0,01 | 23 / 52 | 5 / 6 | 2,6 / 4,6 |
| F6b | Momentum + Trend/Volumen/Zeit | 1152 | 0,5 / 2 | 71,2 / 66,8 | **62,5 / 64,8** | 435 / 1422 | 0,98 / 1,07 | −0,01 / +0,03 | 16 / 30 | 5 / 6 | 1,9 / 3,4 |
| F7 | N Gegenbars im Trend | 64 | 0,5 / 2 | 64,6 / 63,8 | **60,8 / 63,4** | 761 / 1206 | 0,90 / 1,00 | −0,04 / 0,00 | 37 / 22 | 8 / 8 | 2,6 / 3,4 |
| F8 | Fade neuer Extreme, ruhige Tage | 48 | 0,5 / 2 | 64,8 / 62,4 | **64,0 / 59,7** | 342 / 1646 | 1,08 / 0,87 | +0,03 / −0,05 | 13 / 99 | 4 / 7 | 1,6 / 3,6 |
| F9 | Gap-Fill | 27 | 0,5 | 62,9 | **59,4** | 288 | 0,87 | −0,05 | 26 | 4 | 1,0 |
| F11 | Z-Score-Reversion, niedrige Vola | 186 | 0,5 / 2 | 66,6 / 63,4 | **61,0 / 59,7** | 726 / 1351 | 0,92 / 0,86 | −0,03 / −0,06 | 34 / 98 | 6 / 11 | 2,3 / 2,9 |
| F12 | Tageszeit-Drift | 72 | 0,5 | 69,5 | **61,7** | 488 | 0,93 | −0,03 | 32 | 7 | 1,0 |
| F13 | Limit an PDH/PDL/OR/VWAP-Bändern | 32 | 0,5 | 64,7 | **60,2** | 304 | 0,90 | −0,04 | 17 | 5 | 1,0 |
| F14 | Impuls → Retracement-Limit | 144 | 0,5 / 2 | 64,6 / 63,2 | **58,2 / 60,1** | 488 / 1354 | 0,81 / 0,88 | −0,08 / −0,05 | 42 / 74 | 6 / 7 | 1,7 / 3,1 |
| F14b | dito + Regimefilter | 288 | 0,5 / 2 | 67,8 / 64,0 | **57,4 / 58,7** | 291 / 1061 | 0,78 / 0,83 | −0,10 / −0,07 | 31 / 85 | 6 / 8 | 1,8 / 3,2 |
| F15 | Break & Retest | 24 | 0,5 | 64,4 | **63,0** | 414 | 1,03 | +0,01 | 10 | 7 | 1,1 |
| F16 | Daily-Regime + VWAP-Dip | 80 | 0,5 / 2 | 66,3 / 63,3 | **56,8 / 59,7** | 465 / 1524 | 0,75 / 0,85 | −0,11 / −0,06 | 53 / 99 | 5 / 12 | 2,2 / 3,4 |
| F17 | Kapitulations-Kerze Fade | 64 | 0,5 / 2 | 64,5 / 59,8 | **61,8 / 57,3** | 455 / 1583 | 0,94 / 0,77 | −0,03 / −0,10 | 27 / 178 | 5 / 6 | 1,8 / 3,5 |
| F18 | VWAP-Band-Limit-Reversion | 48 | 0,5 | 64,3 | **60,1** | 406 | 0,88 | −0,05 | 26 | 8 | 1,7 |
| F19 | Trend-Tag Pullback | 36 | 0,5 / 2 | 67,5 / 63,9 | **64,7 / 62,1** | 374 / 1394 | 1,05 / 0,96 | +0,02 / −0,02 | 11 / 42 | 6 / 6 | 3,9 / 4,6 |
| F20 | 5-min Inside-Bar-Breakout | 32 | 0,5 / 2 | 65,3 / 62,2 | **59,3 / 61,0** | 496 / 1586 | 0,84 / 0,91 | −0,07 / −0,04 | 41 / 68 | 4 / 6 | 1,5 / 3,3 |
| F21 | Pre-Market-Range-Breakout | 12 | 0,5 | 64,1 | **61,3** | 700 | 0,93 | −0,03 | 32 | 9 | 1,4 |
| ML-1 | LightGBM, 47 Features, jede RTH-Minute | – | Top 1–10 % | – | **27–77 %, instabil** (Top 10 %: 59–66 %; Top 1 %: 0,1-ATR-Short 76,6 %, aber 0,2-ATR-Short 26,8 %; stark überlappende Minuten-Labels) | – | – | – | – | – | – |
| ML-2 | LightGBM-Meta-Filter auf F14-Signalen | – | Top 5–50 % | – | **62–64 %** | – | – | – | – | – | – |
| ETH | Alle 24 Stunden, nach Stunde | – | – | 48–65 % | **44–66 %** (unter 52 % nur 16:00–16:30) | – | – | – | – | – | – |
| Swing | Long über Nacht, R = 1 ATR | – | – | 68 % | 69 % | 253 | – | – | – | – | 0,5 |

Die Swing-Zeile ist reine Bullenmarkt-Drift: Short erreicht nur 51–56 %, es kommen nur 0,5 Trades/Tag zustande, und ein Bärenmarkt ist in den Daten nicht enthalten. **Nicht robust.**

### Auswahl über alle Familien zugleich (Winrate vs. Frequenz)

| Mindest-Trades/Tag (Training) | WR In-Sample | **WR WF-OOS** | N | PF | Trades/Tag | WR je OOS-Quartal |
|---|---|---|---|---|---|---|
| 0,1 | 80,5 % | **58,3 %** | 103 | 0,83 | 0,20 | 61 50 25 67 83 64 63 36 |
| 0,2 | 77,6 % | **59,1 %** | 132 | 0,88 | 0,26 | 61 64 0 67 62 46 90 36 |
| 0,5 | 71,8 % | **61,7 %** | 447 | 0,94 | 0,89 | 62 67 60 62 53 65 60 66 |
| 1 | 70,0 % | **63,5 %** | 578 | 1,02 | 1,14 | 58 63 61 61 66 65 64 74 |
| 2 | 66,8 % | **63,1 %** | 1 333 | 1,00 | 2,64 | 52 64 61 58 70 71 59 71 |
| 3 | 66,3 % | **63,2 %** | 1 783 | 1,00 | 3,53 | 66 59 54 65 70 58 63 71 |
| 5 | 65,2 % | **63,2 %** | 2 993 | 1,00 | 5,93 | 57 65 62 64 62 62 64 67 |

**Kernbefund:** Je selektiver gefiltert wird, desto höher die In-Sample-Winrate (bis 80 %) und desto **niedriger** die OOS-Winrate. Hohe In-Sample-Winrates sind hier ausschließlich Selektions-Overfitting.

## 4. Schrittweise Ziel-Reduktion (dokumentiert)

| Ziel | Erreicht? | Begründung |
|---|---|---|
| 90 % | nein | höchste OOS-Winrate einer Familie bei ≥ 2 Trades/Tag: 64,8 % |
| 89 / 88 / 87 % | nein | dito |
| 85 % | nein | selbst die obersten 0,1 % der ML-Wahrscheinlichkeiten sind instabil (N < 70) |
| 80 % | nein | einzelne OOS-Quartale erreichen bei kleinem N 83–90 %, zusammengeführt aber nie > 65 % |
| (70 %) | nein | 69,9 % gab es nur mit dem Lookahead-Fehler und 0,28 Trades/Tag; korrigiert 64,2 % |
| **≈ 65 %** | **ja, robust** | MBC: 64,7 % WF-OOS, alle 12 Quartale zwischen 59 und 74 % |

## 5. Finale Strategie: MBC – Momentum Burst Continuation

| Element | Regel |
|---|---|
| Markt / Chart | NQ1! oder MNQ1!, 1 Minute, volle Globex-Session |
| Tages-ATR | SMA(14) der täglichen True Range, nur abgeschlossene Tage |
| Fenster | Signal-Bar öffnet zwischen 09:35 und 11:30 ET (Option: bis 15:30) |
| Impuls | `close − close[5]` |
| **ENTRY BUY** | Impuls kreuzt am Bar-Schluss über **+0,16 × Tages-ATR** (SELL: unter −0,16 × ATR) |
| Stop | tiefstes Tief der letzten 5 Bars − 1 Tick (Short: höchstes Hoch + 1 Tick) |
| Filter | geschätzte Stop-Distanz zwischen 0,03 und 0,40 × Tages-ATR |
| Entry-Preis | Open der nächsten Bar; **R = Entry − Stop** |
| Take Profit | **Entry + 0,6 × R** (exakt, fix) |
| Exit | SL / TP; beide in einer Bar → SL; spätestens 15:59-Bar |
| Positionen | max. 1; Signale während offenem Trade werden ignoriert |

Die Parameter hat der Walk-Forward im letzten Fenster gewählt (Training Q4/2024–Q3/2025). Sie liegen außerdem auf einem stabilen Plateau: Stärkere Impulse und strukturelle Stops sind in beiden Perioden besser.

### Performance (Python, Kosten wie oben)

| Zeitraum | N | WR | PF | Exp R | Ø Win | Ø Loss | MaxDD | Max. Verlust-/Gewinnserie | Trades/aktiver Tag |
|---|---|---|---|---|---|---|---|---|---|
| **WF-OOS 2024–25 (rollierende Auswahl)** | 797 | **64,7 %** | 1,07 | +0,027 | 0,59R | −1,01R | 22,9R | 5 / 14 | 1,58 je Kalendertag |
| Fix-Parameter 2023 (vor dem Trainingsfenster) | 416 | 65,4 % | 1,11 | +0,039 | 0,60R | −1,01R | 10,5R | 4 / 12 | 2,14 |
| Fix-Parameter 2024 | 414 | 63,3 % | 1,03 | +0,010 | 0,60R | −1,00R | 13,0R | 4 / 13 | 2,29 |
| Fix-Parameter 2025 | 335 | 66,9 % | 1,20 | +0,065 | 0,60R | −1,01R | 13,3R | 4 / 8 | 2,39 |
| Ganzer-Tag-Modus 2023–25 | 1 854 | 63,4 % | 1,04 | +0,014 | 0,59R | −0,99R | 17,1R | 5 / 12 | 3,30 |

**Quartale (Vormittag):**

| 23Q1 | 23Q2 | 23Q3 | 23Q4 | 24Q1 | 24Q2 | 24Q3 | 24Q4 | 25Q1 | 25Q2 | 25Q3 | 25Q4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 59 % | 68 % | 68 % | 65 % | 60 % | 68 % | 61 % | 65 % | 70 % | 74 % | 62 % | 66 % |

**Nach Tageszeit (Vormittag):**

| 09:30–10:00 | 10:00–10:30 | 10:30–11:00 | 11:00–11:30 |
|---|---|---|---|
| 65,9 % | 65,8 % | 67,1 % | 57,8 % |

Im Ganzer-Tag-Modus fallen 14:00–16:00 auf 53–60 % ab. Deshalb ist der Vormittag der Default.

**Nach Regime:**

| Aufteilung | Winrate |
|---|---|
| Long / Short | 66,5 % / 63,9 % |
| Daily-Bull / -Bear (Close vs. SMA20) | 64,9 % / 65,4 % |
| Mit / gegen Daily-Trend | 66,7 % / 63,8 % |
| ATR-Terzile niedrig / mittel / hoch | 65,6 % / 63,0 % / 66,6 % |
| Wochentage | 64–67 % |

Kein Regime bricht ein. Kein Filter verbessert die Werte robust: Trend-, Volumen- und Regimefilter wurden in F6b, F14b und F16 im Walk-Forward getestet und fielen OOS durch.

**Wirtschaftlich:**
- Expectancy ≈ +0,03R pro Trade. Bei einem Median-R von ~58 Punkten sind das etwa +1,5 bis 2 Punkte netto pro NQ-Trade.
- Das ist ein **dünner Vorteil**, statistisch nur knapp vom Zufall (61–62 %) zu unterscheiden.
- Bereits 1 Tick zusätzliche Slippage halbiert ihn.

## 6. Antizipierbarkeit

Gemessen wurde, wie stark der Impuls *vor* dem Signal schon ausgeprägt ist, als Anteil der Schwelle:

| Bars vor dem Signal | 1 | 2 | 3 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|
| Median-Anteil der Schwelle | 0,73 | 0,44 | 0,27 | −0,11 | 0,04 | −0,02 | 0,01 |
| Anteil Signale mit ≥ 50 % | 77 % | 44 % | 29 % | 12 % | 18 % | 15 % | 15 % |

- **Ein Momentum-Burst baut sich in 1–3 Bars auf.** 5 bis 20 Bars vorher gibt es keine verlässliche Vorwarnung.
- Eine Kompressionsphase vor dem Burst ändert die Winrate ebenfalls nicht (62–67 % in allen Terzilen).
- **Phase 1 → Signal:** Erreicht der Impuls 50 % der Schwelle, folgt das volle Signal innerhalb von 10 Bars in 18–29 % der Fälle. Bei 75 % der Schwelle sind es **43–52 %**.
- Wann das Setup sichtbar wurde, hat keinen nennenswerten Einfluss auf die Winrate: 63–70 % je Gruppe.

**Echte Antizipation bietet die Trigger-Linie:** Der exakte Schlusskurs, ab dem die nächste Bar das Signal auslöst, ist *vor* dieser Bar bekannt. Für Long liegt er bei `close[4] + 0,16 × ATR`. Der Indikator zeichnet ihn als Linie. Der Trader sieht also vorab den Preis, der überschritten werden muss.

## 7. Der Indikator (`pine/MBC_Momentum_Burst_RR06.pine`, Pine v6)

| Phase | Darstellung |
|---|---|
| **1 SETUP** | Impuls ≥ 50 % der Schwelle: blasse Trigger-Linie, leichter Hintergrund, Marker „S“ |
| **2 CONFIRMATION** | Impuls ≥ 75 %: kräftige Trigger-Linie, stärkerer Hintergrund, Marker „C“ |
| **3 ENTRY** | BUY/SELL-Label an der Signal-Bar plus Stop-Punkt. Ab der nächsten Bar: Linien für Entry (grau), SL (rot) und TP bei 0,6R (grün) bis zum Exit, dann Markierung TP / SL / T |

**Statistik-Tabelle:**
- Trades, Winrate, Zufallsreferenz, Profit Factor, Expectancy, maximale Verlustserie, Trades pro aktivem Tag
- Gleiches Kostenmodell wie im Research, einstellbar

**Alerts:** für alle drei Phasen.

**No-Repaint-Prüfung (Code-Review):**
- Alle Signale und Zustandsänderungen nur bei `barstate.isconfirmed`
- Tages-ATR per `request.security(..., ta.sma(ta.tr(true),14)[1], lookahead_on)`, liefert nur den Vortageswert
- Keine `ta.pivot*`-Funktionen, keine Zukunftsreferenzen, keine negativen Offsets
- TP und SL werden einmalig beim Fill fixiert

**Parität:** `research/pine_replica.py` implementiert die Pine-Logik bar-für-bar als Zustandsautomat. Die Trades sind **identisch** mit der Research-Engine: 1 165/1 165 (Vormittag) und 1 854/1 854 (ganzer Tag).

**Einschränkungen:**
- Kompiliert und visuell getestet in TradingView habe ich den Code **nicht**, dort ist keine Ausführung möglich.
- TradingViews NQ1! ist nicht wie die CSV back-adjusted. Die True Range an Roll-Tagen kann abweichen.
- Für den NAS100-CFD gilt die Kalibrierung nur eingeschränkt (anderer Preis-Feed, Spread).

## 8. Empfehlung

- Die Strategie ist **ehrlich gemessen**, sauber darstellbar und regelbasiert. Ihr Vorteil gegenüber Zufall ist aber klein: ~65 % gegenüber ~61,5 % bei RR 0,6.
- Wer eine echte 90-%-Winrate sucht, muss das RR deutlich senken. Erst bei RR ≈ 0,11 liegt die Zufalls-Winrate selbst bei 90 %. Mit Kosten und Slippage ist das bei NQ nicht handelbar.
- Indikatoren, die bei RR 0,6 90 % auf historischen Charts zeigen, nutzen fast immer Repainting, Pivot-Lookahead oder Fill-Annahmen, die hier ausgeschlossen wurden.
- Vor Live-Einsatz: den Indikator **vorwärts** ab dem 12.12.2025 beobachten. Die Daten liegen außerhalb der CSV und sind damit echtes Out-of-Sample. Mit kleinem Kontrakt (MNQ) starten.
