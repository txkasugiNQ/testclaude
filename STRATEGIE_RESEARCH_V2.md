# NQ-Research Runde 2: freies RR, Fokus Profit Factor und Robustheit

**Ergebnis vorweg:**

| Rolle | Strategie | WF-OOS PF | Expectancy | Winrate | Trades/aktiver Tag | Einschränkung |
|---|---|---|---|---|---|---|
| **MOST ROBUST** | MBL (Momentum Burst Level) | 1,13 (WF) · fix 1,10 / 1,29 / 1,09 je Jahr | +0,08 bis +0,10 R | 33–36 % | 1,9–2,1 | WF-OOS 2025 nur PF 0,98 |
| **BEST PERFORMER** | OBR (Opening Bar Range) | **1,76** | **+0,59 R** | 24 % | 1,0 | hängt an ~10 Trend-Tagen, Permutationstest nur 78./93. Perzentil |
| **Empfehlung** | **Portfolio MBL + OBR** | **1,29** | **+0,19 R** | 34 % | **2,5** | 6/8 OOS-Quartale positiv, Tages-Sharpe 1,87 |

Alle Zahlen stammen aus Python-Backtests auf der CSV mit realistischen Kosten. **TradingView-Backtests wurden nicht ausgeführt, der Pine-Code wurde nicht kompiliert.** Die Pine-Logik ist bar-für-bar in Python repliziert und erzeugt identische Trades.

---

## 1. Ausgangslage aus Runde 1

**Ausgeschlossen** (WF-OOS ≤ Zufall):
- Mean Reversion (VWAP, RSI, Z-Score)
- Levels als Umkehrpunkte
- Confluence statischer Levels
- Sweep & Reclaim
- Limit-Entries an Levels
- Gap-Fill
- Tageszeit-Drift
- ML auf feste Barrieren

**Interessant:**
- Momentum-Bursts, Breaks von PDH/PDL
- Zeitstruktur der Open
- Volatility Clustering

**Offene Hypothese:** RR 0,6 schneidet die Momentum-Edge ab.

## 2. Methodik Runde 2

**Engine-Erweiterungen:**
- Freies RR, Zeit-Stop, Breakeven, Trailing
- OCO-Stop-Entries
- Level-Invalidierung (Stop vor Entry → Order gestrichen)

**Konservative Ausführung:**

| Situation | Annahme |
|---|---|
| Stop-Entry | Fill zu max(Level, Open) + 1 Tick |
| Stop-Exit | −1 Tick, bei Gap zur Open |
| Fill-Bar | nur der Stop wird geprüft |
| Beide OCO-Seiten in einer Kerze | Seite näher an der Open zählt |
| Kommission | 0,25 Pkt |

**Event-Studies:** signierte Vorwärtsrendite in ATR-Einheiten, Discovery nur auf 2023.

**Walk-Forward v2:**
- 12 Monate Training, 3 Monate Test
- 8 OOS-Quartale (2024–2025)
- Auswahlkriterium: **Expectancy-t-Statistik**, nicht die Winrate

**Permutationstests:** Zufallsrichtung bei identischem Stop und Exit, um Glück auszuschließen.

## 3. Was getestet wurde und was es zeigt

### 3.1 Exit-Struktur: Wo steckt die Edge?
- **Momentum-Burst (Schwelle 0,16):** PF 0,96 bei RR 0,5, 1,17 bei RR 3, 1,24 bei Halten bis Session-Ende (2023).
- **Trailing-Stops und Breakeven verschlechtern** durchgehend (PF 0,79–1,05). Die Edge liegt in wenigen großen Trend-Bewegungen. Wer früh sichert, schneidet sie ab.

### 3.2 Event-Studies (2023, über 40 Ereignisse)
- **Ohne Signal** (|t| < 2):
  - Breaks von Asia-, London-, Overnight- und Opening-Range-Levels
  - ICT-Fair-Value-Gaps (1 und 5 min)
  - VWAP-Touches, Sweeps
  - Vol-Expansion, Gap-Follow
- **Auffällig 2023:** Kompressions-Box-Breakout (t = 3,8) und Equal-Highs-Break (t = 3,7).
- **Im Walk-Forward durchgefallen:** Box PF 0,88–0,90, Equal Highs PF 1,02. Ein Lehrbuchfall von Discovery-Glück.

### 3.3 Literatur-Effekte (alle Jahre einzeln)

| Effekt | Ergebnis |
|---|---|
| Intraday-Momentum (Gao et al.) | t = −1,0 / 0,1 / 0,0, verworfen |
| Halbstunden-Saisonalität (Heston/Korajczyk/Sadka) | Vorzeichen wechselt jährlich, verworfen |
| Turn-of-Month, Extremtag-Reversal | instabil, verworfen |
| Overnight-Drift | positiv in allen Jahren (t 0,9–2,0), aber reine Long-Drift im Bullenmarkt, 1 Trade/Tag, **regimeabhängig** |

### 3.4 ML-Obergrenze (Regression auf 60-min-Vorwärtsrendite, 30 Struktur-Features)
- OOS PF 1,20–1,27 in den Top 5–10 % der Signale
- 3 von 8 Quartalen negativ
- Das Modell nutzt Tagesmerkmale (Gap, ATR, Eröffnungskerze) mit instabilen Mustern
- **Folgerung:** Die Richtungs-Vorhersagbarkeit ist klein und instabil.

### 3.5 Trendhaftigkeit
- Im Permutationstest erzielten 2024–25 sogar **Zufallsrichtungen** mit engem Stop und Halten bis Close einen Median-PF von 1,36, 2023 nur 1,02.
- Die Variance Ratio liegt aber im Mittel bei ≈ 1, ihre Autokorrelation bei 0,02. **Trendhaftigkeit ist nicht vorhersagbar.**
- Der Effekt stammt aus einzelnen Extremtagen (August 2024, April 2025).

### 3.6 Kontext-Zerlegung des Momentum-Bursts
- 2023 sah es nach einer klaren Struktur aus („mit Tagesrichtung, früh, Range-Platz“: PF 1,3–1,4).
- **2024–25 sind diese Unterschiede verschwunden.** Der Basis-Burst blieb positiv, die Filter waren Rauschen.
- G9 im Walk-Forward: PF 1,09, nicht besser als ungefiltert.

### 3.7 Research-Tabelle Runde 2 (Walk-Forward-OOS 2024–2025)

Vollständig mit allen Spalten: `research/research_table2.csv`. Runde 1: `research/research_table.csv`.

| Version | Idee | Entry | Exit | fmin | IS Exp R | **OOS PF** | OOS Exp R | OOS WR | Ø Win / Ø Loss | MaxDD R | Verlust-/Gewinnserie | Sharpe(D) | Trades/aktiver Tag | PF 2024 / 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | Kompressions-Box OCO | Stop an Box-Kante | Box/RR/EOD | 1 | +0,10 | **0,90** | −0,06 | 34 % | 1,73 / −0,97 | 131 | 18 / 9 | −0,99 | 3,0 | 0,92 / 0,86 |
| G2 | Box, Close-Bestätigung | Market | Box/Swing, RR/EOD | 1 | +0,08 | **0,89** | −0,08 | 31 % | 1,94 / −0,99 | 124 | 18 / 6 | −1,10 | 2,6 | 0,89 / 0,89 |
| G3 | Momentum-Burst, freies RR | Market | RR 1–3 / EOD / 120 min | 1 | +0,14 | **1,09** | +0,05 | 43 % | 1,34 / −0,95 | 23 | 8 / 7 | 0,82 | 1,9 | 1,07 / 1,10 |
| G4 | Level-Breakout (PDH, ON, IB, OR, PW, London) | Market | Level/Swing, RR/EOD | 1 | +0,12 | **0,93** | −0,05 | 32 % | 1,85 / −0,95 | 40 | 15 / 7 | −0,48 | 1,2 | 0,89 / 0,98 |
| G5 | Trend-Tag-Regel | Market | ATR-Stop, RR/EOD | 0,25 | +0,32 | **1,12** | +0,07 | 38 % | 1,69 / −0,93 | 9 | 7 / 5 | 0,77 | 1,0 (selten) | 1,10 / 1,15 |
| G6 | Equal Highs/Lows Break | Market | Swing, RR/EOD | 1 | +0,09 | **1,02** | +0,01 | 35 % | 1,83 / −0,95 | 36 | 14 / 6 | 0,25 | 2,6 | 1,04 / 1,01 |
| **G7** | **Opening Bar Range** | **Market 09:31** | **Kerzen-Extrem, EOD** | 0,25 | +0,64 | **1,76** | **+0,59** | 24 % | 5,59 / −1,01 | 18 | 18 / 4 | **2,55** | 1,0 | 1,61 / 2,17 |
| G8 | Burst Asia/London | Market | Swing, RR, Zeit | 1 | +0,08 | **0,99** | −0,01 | 45 % | 1,11 / −0,91 | 60 | 11 / 8 | −0,15 | 2,9 | 1,00 / 0,96 |
| G9 | Burst + Kontextfilter | Market/Stop | Swing, RR/EOD | 1 | +0,19 | **1,08** | +0,05 | 35 % | 1,92 / −0,96 | 25 | 11 / 7 | 0,72 | 1,8 | 1,17 / 0,99 |
| **G10** | **Momentum Burst Level** | **Stop am 5-Bar-Extrem** | **5-Bar-Gegenseite, RR/EOD** | 1 | +0,14 | **1,13** | **+0,08** | 36 % | 1,89 / −0,95 | 38 | 14 / 6 | 1,08 | **2,1** | 1,31 / 0,98 |
| **Portfolio** | **G10 + G7** | | | | | **1,29** | **+0,19** | 34 % | 2,46 / −0,97 | 35 | 13 / 6 | **1,87** | **2,5** | Quartale: −6, +46, +70, +41, +27, +15, −18, +28 R |

## 4. Die finalen Strategien

### 4.1 MBL – Momentum Burst Level (MOST ROBUST)

**Marktlogik:**
- Ein schneller 5-Minuten-Impuls von ≥ 0,12 Tages-ATR zeigt ein Orderfluss-Ungleichgewicht.
- Bricht der Preis danach **über das Hoch dieses Impulses** (Stop-Entry), bestätigt der Markt die Fortsetzung.
- Die meisten Trades verlieren klein (Stop an der anderen Seite der 5-Bar-Range). Wenige Trend-Tage tragen die Gewinne.
- Ex-post-Klassifikation (nur Reporting): Range-Tage −0,67R, Trend-Tage +1,27R im Schnitt.

| Phase | Regel (programmierbar, exakt im Pine-Code) |
|---|---|
| **1 SETUP** | Im Fenster 09:35–15:30 ET erreicht `close − close[5]` ≥ 50 % von 0,12 × Tages-ATR. Ein vorläufiges Level erscheint (dünne Linie am 5-Bar-Hoch + 1 Tick). |
| **2 CONFIRMATION** | Impuls ≥ 75 % der Schwelle, die Linie wird kräftig. Rein visuell, keine Handelsbedingung. |
| **3 ENTRY LEVEL** | Der Impuls **kreuzt am Bar-Schluss** über +0,12 × Tages-ATR (Vorbar noch darunter). **LONG LEVEL = Buy-Stop-Order** bei höchstem Hoch der letzten 5 Bars (inkl. Signal-Bar) + 1 Tick. Short spiegelbildlich (Sell-Stop am 5-Bar-Tief − 1 Tick). |
| Filter | Breite der 5-Bar-Range zwischen 0,02 und 0,60 × Tages-ATR, sonst kein Level |
| **Gültigkeit** | Nur für die **nächsten 5 Bars**, danach **EXPIRED** |
| **Invalidierung** | Wird das Stop-Level gehandelt, **bevor** das Entry getriggert hat (gleiche Kerze zählt als Invalidierung), wird die Order gestrichen (**INVALID**) |
| Entry-Ausführung | Echte Stop-Order: Fill, sobald das Hoch das Level erreicht, zum Level oder zur Open, falls darüber eröffnet wird. Keine Close-Bestätigung, kein Retest nötig. |
| **4 STOP** | Tiefstes Tief der 5 Bars − 1 Tick (Short: höchstes Hoch + 1 Tick). Fix, wird nicht nachgezogen (Trailing hat getestet geschadet). |
| **TARGET** | **Kein festes Target.** Exit zum Close der 15:59-Kerze ET, falls der Stop nicht vorher fällt. Das ist das datenbasierte RR: Ø Gewinn 2,3R, Ø Verlust 0,97R. Feste Targets (RR 2/3) waren in 2025 schlechter. 1R/2R/3R werden nur als Orientierung gezeichnet. |
| Konkurrenz | Maximal **eine** MBL-Order bzw. -Position. Neue Bursts während einer offenen Order oder Position und auf der Bar, auf der die vorige Order bzw. Position endete, werden ignoriert. |
| Target vor Entry? | Entfällt (kein Target). Ein vorab weit gelaufener Preis triggert die Stop-Order zum Open-Preis (Gap-Fill). |

**Statistik (feste Parameter, Python, Kosten inklusive):**

| Zeitraum | Trades | WR | PF | Exp R | Ø Win / Ø Loss | MaxDD | Max. Verlust-/Gewinnserie | Trades/aktiver Tag | Sharpe(D) |
|---|---|---|---|---|---|---|---|---|---|
| 2023–2025 | 1 239 | 32,9 % | 1,16 | +0,102 | 2,29 / −0,97 | 33,9R | 20 / 7 | 1,85 | 1,16 |
| 2023 | 449 | 30,5 % | 1,10 | +0,068 | 2,42 / −0,97 | 33,9R | 20 / 4 | 1,94 | 0,81 |
| 2024 | 424 | 36,1 % | 1,29 | +0,178 | 2,21 / −0,97 | 23,0R | 10 / 7 | 1,79 | 2,00 |
| 2025 | 366 | 32,0 % | 1,09 | +0,057 | 2,25 / −0,97 | 28,6R | 14 / 4 | 1,82 | 0,62 |
| **WF-OOS 2024–25 (Familie, rollierende Wahl)** | 865 | 36,2 % | **1,13** | +0,076 | 1,89 / −0,95 | 37,8R | 14 / 6 | 2,11 | 1,08 |

**Quartale (Exp R):**

| 23Q1 | 23Q2 | 23Q3 | 23Q4 | 24Q1 | 24Q2 | 24Q3 | 24Q4 | 25Q1 | 25Q2 | 25Q3 | 25Q4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| −0,11 | +0,16 | +0,13 | +0,07 | +0,06 | +0,33 | +0,02 | +0,34 | +0,09 | +0,25 | **−0,19** | +0,16 |

**Nach Entry-Zeit (Exp R):**

| 09:30 | 10:00 | 11:00 | 12:00 | 13:00 | 14:00 | 15:00 |
|---|---|---|---|---|---|---|
| +0,08 | +0,13 | +0,11 | +0,22 | +0,31 | +0,04 | **−0,18** |

**Nach Regime (Exp R):**

| Aufteilung | Werte |
|---|---|
| Long / Short | +0,13 / +0,08 |
| Niedrige / mittlere / hohe Volatilität | +0,15 / +0,10 / +0,06 |
| Daily-Bear / -Bull | +0,19 / +0,05 |

Alle Regime sind positiv.

**Auswahl der Parameter:** Schwelle 0,12, Lookback 5, Gültigkeit 5, Exit Session-Ende. Alle 8 Varianten mit Exit zum Session-Ende und Schwelle 0,12/0,16 waren in **jedem** Jahr einzeln profitabel, das Plateau ist also breit. Der WF-Auswahlprozess konvergierte auf Schwelle 0,12 mit Stop-Entry.

### 4.2 OBR – Opening Bar Range (BEST PERFORMER)

**Marktlogik:**
- Die erste RTH-Minute bündelt die Overnight-Order-Imbalance.
- Ein klarer Körper (> 0,03 ATR) zeigt an, wer die Eröffnung gewinnt.
- Der Stop liegt jenseits der Eröffnungskerze und ist daher sehr eng (Median ~25 Pkt). An Trend-Tagen entstehen große R-Vielfache: Ø Gewinn 7,3R.

| Element | Regel |
|---|---|
| Signal | Close der 09:30-Kerze: \|Close − Open\| > 0,03 × Tages-ATR, Richtung = Körperrichtung |
| Filter | Stop-Distanz (Close − Stop) zwischen 0,02 und 0,60 × ATR |
| Entry | **Market zur Open der 09:31-Kerze** (keine Wartezeit, kein Retest) |
| Stop | Tief der 09:30-Kerze − 1 Tick (Short: Hoch + 1 Tick), fix |
| Target | keins, Exit zum 15:59-Close |
| Häufigkeit | max. 1 Trade pro Tag, unabhängig von MBL (eigener Positions-Slot) |

**Statistik (feste Parameter):**

| Zeitraum | Trades | WR | PF | Exp R | MaxDD | Max. Verlustserie |
|---|---|---|---|---|---|---|
| 2023 | 161 | 15,5 % | 1,26 | +0,22 | 27,5R | 19 |
| 2024 | 155 | 17,4 % | 1,75 | +0,63 | 18,5R | 18 |
| 2025 | 150 | 21,3 % | 1,74 | +0,59 | 16,2R | 12 |
| **WF-OOS 2024–25** | 235 | 24,3 % | **1,76** | +0,59 | 18,4R | 18 |

**Warnung:**
- Ohne die 10 besten von 235 OOS-Trades fällt der PF auf 0,99.
- Im Permutationstest liegt die Follow-Richtung nur im 78. (2023) bzw. 93. (2024–25) Perzentil der Zufallsrichtungen.
- Verlustserien von 18–19 Trades sind normal.
- **Hohe Rendite, aber psychologisch und statistisch fragil.**

### 4.3 Portfolio MBL + OBR (Empfehlung)

Die beiden Strategien korrelieren täglich nur mit 0,38.

| | Trades | WR | PF | Exp R | MaxDD | Trades/aktiver Tag | Sharpe(D) |
|---|---|---|---|---|---|---|---|
| Fix 2023 | 610 | 26,6 % | 1,15 | +0,11 | 43,9R | 2,6 | 0,96 |
| Fix 2024 | 579 | 31,1 % | 1,44 | +0,30 | 27,5R | 2,4 | 2,23 |
| Fix 2025 | 516 | 28,9 % | 1,30 | +0,21 | 32,5R | 2,4 | 1,41 |
| **WF-OOS 2024–25** | 1 100 | 33,6 % | **1,29** | **+0,19** | 34,8R | **2,5** | **1,87** |

## 5. Was die Daten über NQ sagen (Marktlogik)

1. **Kurzfristige Richtung ist fast effizient.** Mean Reversion, Level-Reaktionen, Sweeps, FVGs und Kompressions-Breakouts zeigen OOS keine Edge.
2. **Die einzige persistente Struktur ist Momentum mit Fat Tails.** Nach Impulsen und an der Eröffnung setzen sich Bewegungen *manchmal* sehr weit fort. Die Edge liegt im Verhältnis Ø Gewinn zu Ø Verlust, nicht in der Trefferquote.
3. **Deshalb funktionieren nur Exits, die Gewinner laufen lassen.** Feste kleine Targets, Breakeven und Trailing zerstören die Edge.
4. **Winrates von 25–35 % sind hier strukturell richtig**, nicht ein Mangel. Hohe Winrates bei kleinem RR waren in Runde 1 nicht profitabel.
5. Kontext-Filter (Trend, Zeit, Volatilität) wirkten in-sample stark und verschwanden OOS. **Einfache Regeln sind robuster.**

## 6. Pine-Indikator `pine/NQ_Momentum_Levels.pine`

**Darstellung (keine BUY/SELL-Schilder):**

| Element | Bedeutung |
|---|---|
| Dünne Linie | Phase 1, Long- oder Short-Level im Aufbau |
| Kräftige Linie | Phase 2 |
| Farbige Box + Label | „LONG LEVEL · Buy-Stop x · Stop y · R≈z · gültig 5 Bars“, die Box reicht bis zum Ablauf |
| Grau „INVALID“ | Stop wurde vor dem Entry gehandelt |
| Grau „EXPIRED“ | 5 Bars ohne Trigger |
| Aktiver Trade | Entry-Linie, rote Stop-Linie, gepunktete 1R/2R/3R-Referenzen (keine Exits); Label „AKTIV · Exit: Stop oder 15:59 Close“; am Exit Ergebnis-Label in R |
| OBR | Box über der Eröffnungskerze, „OBR LONG · Entry 09:31-Open · Stop x“, dann gestrichelte Entry- und Stop-Linien |

**Weitere Funktionen:**
- Archiv: Zeichnungen älter als N Tage (Default 5) werden gelöscht.
- Statistik-Tabelle: Trades, Winrate, PF gesamt, PF MBL/OBR, Expectancy, MaxDD, Trades pro aktivem Tag.
- Alerts: Confirmation, Level gesetzt, OBR-Signal, Fill, Exit.

**No-Repaint und No-Lookahead:**
- Alle Zustandswechsel nur bei `barstate.isconfirmed`.
- Tages-ATR = `request.security(…, ta.sma(ta.tr(true),14)[1], lookahead_on)`, also nur der Vortageswert.
- Keine Pivots, keine Zukunftsoffsets. Levels werden einmalig fixiert und nie verschoben.

**Parität:** `research/pine_replica2.py` implementiert genau diese Logik bar-für-bar und ist Trade-für-Trade identisch mit der Backtest-Engine (MBL 1 239/1 239, OBR 466/466).

**Einschränkungen:**
- Nicht in TradingView kompiliert. Beim Review habe ich zwei typische Pine-Fehler korrigiert (globale Variablen in Funktionen, lokale Funktionsdeklaration). Es können weitere Kompilierfehler auftreten.
- TradingViews NQ1! ist nicht back-adjusted wie die CSV. Die Tages-ATR an Roll-Tagen kann abweichen.
- Für den NAS100-CFD gilt die Kalibrierung nicht automatisch (anderer Feed, Spread, Tick-Volumen).
- Delta, Orderflow und Bid/Ask sind in den Daten nicht vorhanden und wurden nicht simuliert.

## 7. Ehrliche Bewertung

- Gefunden habe ich **eine robuste, aber kleine Edge (MBL, PF ~1,1–1,3)**, eine **starke, aber fragile Edge (OBR, PF ~1,3–1,8)** und deren Kombination mit WF-OOS PF 1,29.
- Das ist realistisch handelbar, aber kein „heiliger Gral“.
- Lange Verlustserien sind normal: 14–20 bei MBL, 18–19 bei OBR.
- Positionsgröße: fixes Risiko pro Trade (z. B. 0,25–0,5 % des Kontos pro 1R) bzw. MNQ statt NQ.
- Vor Live-Einsatz den Indikator **vorwärts** ab dem 12.12.2025 laufen lassen. Diese Daten liegen außerhalb der CSV und sind echtes Out-of-Sample.
