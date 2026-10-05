# NQ-Research Runde 3: Beobachtung zuerst (Chart → Phänomen → Hypothese → Test)

**Ergebnis vorweg:** Ich habe in dieser Runde **keine Strategie gefunden, die dein Zielprofil erfüllt**: hohe Winrate, hohe Expectancy, kurze Verlustserien, ≥ 2 Trades pro Tag, stabil OOS. Ich erkläre deshalb keine Strategie zur „finalen“ und baue keinen neuen Indikator.

Stattdessen beschreibt dieser Bericht, **was der NQ in diesen Daten tatsächlich tut**, warum das Zielprofil mit OHLCV-Daten allein nicht erreichbar ist, und was sich ändern müsste.

Alle Zahlen stammen aus Python auf der CSV (12/2022–12/2025) mit Kosten von 1 Tick Slippage und 0,25 Pkt Kommission. Discovery lief auf 2023, die Prüfung auf 2024 und 2025.

Skripte: `research/audit3.py`, `obs_lab.py`, `obs_tod.py`, `obs_new.py`, `rule80.py`, `pocket_search.py`, `mgmt3.py`, `mbl_time.py`.

---

## 1. Ideen-Status (alle drei Runden)

### FAILED IDEAS (OOS ≤ Zufall, verworfen)

**Mean Reversion:**
- VWAP-Re-Entry, VWAP-Band-Limits, RSI-Extreme, Z-Score, Kapitulationskerze
- Fade an ruhigen Tagen, Fade bei 5 gleichgerichteten Closes

**Levels als Reaktionspunkte:**
- PDH/PDL, Overnight/Asia/London, IB/OR, Pivots, POC/VAH/VAL, Monats- und Daily-Pivots
- Confluence mehrerer Levels

**Liquidity und Struktur:**
- Sweep & Reclaim (alle Level-Typen), Wick-Rejection an Extremen
- Equal Highs/Lows-Break, Break & Retest (Limit)
- Impuls-Retracement-Limit (nur scheinbar gut vor dem Lookahead-Fix)

**ICT/SMC:**
- Fair Value Gaps (1 und 5 min)
- Order-Block-ähnliche Displacement-Entries

**Breakouts:**
- Opening Range 15/30/60
- Pre-Market-Range, Inside-Bar 1/5 min
- Kompressions-Box (2023 t = 3,8, OOS PF 0,88)
- Level-Breakouts (PDH, ON, IB, PW, London)

**Zeit und Kalender:**
- Tageszeit-Drift, Halbstunden-Saisonalität (HKS), Intraday-Momentum (Gao)
- Turn-of-Month, Gap-Fill, Extremtag-Reversal

**Market Profile:**
- 80-%-Regel: Target-Hit nur 34–47 %; PF 1,79 in 2023, aber 0,85 in 2024 und 0,57 in 2025

**Volumen:**
- Absorption, Klimax-Bars, Relativvolumen-Filter

**Overnight-Inventory-Korrektur:** Vorzeichen wechselt jährlich.

**Kontextfilter auf Momentum:** Trendseite, Tageszeit, Range-Platz. In-Sample PF 1,3–1,4, OOS verschwunden.

**ML:**
- Klassifikation auf feste TP/SL-Barrieren
- Regression auf 60-min-Rendite (PF ~1,2, aber 3 von 8 Quartalen negativ)

### PROMISING (positiv, aber schwach oder fragil)
- **OBR (Opening Bar Range):** WF-OOS PF 1,76, aber getragen von ~10 Trend-Tagen. Im Permutationstest nur 78./93. Perzentil.
- **Overnight-Drift long:** positiv in allen Jahren, aber Bullenmarkt-abhängig und 1 Trade pro Tag.
- **„Break → kleiner Rücksetzer → Fortsetzung“:** skalenabhängiges Muster (siehe 3.1), Effekt nur 1–3 Prozentpunkte.

### ROBUST (klein, aber in jedem Jahr positiv)
- **Momentum mit Fat Tails (MBL):** Stop-Entry über dem 5-Bar-Hoch nach einem Impuls ≥ 0,12 ATR, Halten bis Session-Ende.
  - PF 1,10 / 1,29 / 1,09 je Jahr, WF-OOS 1,13–1,18
  - Am stabilsten im Vormittagsfenster (09:35–11:30: PF 1,14 / 1,17 / 1,15)
  - **Profil:** Winrate 30–34 %, max. Verlustserie 14–20

### IDEAS TO REWORK (in dieser Runde bearbeitet)
- MBL-Management (Teilgewinne, Breakeven, engere Stops) → Abschnitt 4
- Zeitfenster und Chop-Ausschluss → Abschnitt 5

### UNTESTED (mit diesen Daten nicht testbar)
- Echtes Orderflow-Delta, Bid/Ask, Level 2 / DOM, Footprint
- Tick-Daten, Queue-Position
- Wirtschaftskalender (exakte Event-Zeiten), Options-Flow / Gamma-Exposure
- Cross-Asset (ES, VIX, Renditen, Dollar)
- Lange Historie mit Bärenmärkten (2008, 2022)

---

## 2. Audit: Sind die Stops zu groß?

| Kandidat | SL Median | SL / Tages-ATR | SL / 1-min-Range | MAE der Gewinner P90 | MFE der Verlierer Median / P75 |
|---|---|---|---|---|---|
| MBC (RR 0,6) | 57,5 Pkt | 0,21 | 3,2× | 0,77R | 0,23R / 0,40R |
| MBL | 52,0 Pkt | 0,18 | 3,3× | 0,86R | 0,54R / 1,16R |
| OBR | 24,8 Pkt | 0,09 | 2,9× | 0,86R | 0,64R / 1,66R |

- Relativ zur Tages-ATR sind die Stops moderat. Im Punkten wachsen sie mit der Volatilität (2023 → 2025: +60 %).
- Bei MBC war der Stop 1,67-mal so groß wie das Target. Das ist die „künstliche Winrate“, die du vermutet hast.
- **Engere Stops funktionieren nicht:** Die Gewinner brauchen bis ~0,86R Platz. Ein halbierter Stop dreht MBL OOS ins Minus (Abschnitt 4).
- **Verluste clustern nicht innerhalb eines Tages:** P(Win nach Verlust am selben Tag) = 0,34, P(Win als erster Trade) = 0,32. Eine Regel wie „nach 2 Verlusten aufhören“ würde nichts bringen.

## 3. Beobachtungsatlas: Was der NQ tatsächlich tut

### 3.1 Symmetrische Barrieren nach 22 Ereignistypen (2023)

**Methode:** Nach dem Ereignis wird gemessen, ob der Preis zuerst ±s in Fortsetzungsrichtung oder dagegen erreicht. Im Random Walk ist das exakt 50 %.

| Ereignis | s = 0,03 ATR | s = 0,06 ATR | s = 0,12 ATR |
|---|---|---|---|
| Close bricht 15-Bar-Extrem | **48,9 % (z −2,4)** | 50,4 % | **51,4 % (z +2,9)** |
| Close bricht 60-Bar-Extrem | **48,2 % (z −2,7)** | 49,6 % | **51,4 % (z +2,1)** |
| Neues RTH-Extrem | 48,0 % (z −2,4) | 50,4 % | 51,2 % |
| Wick-Sweep, Close zurück (Fade) | 50,2 % | 50,9 % | 51,1 % |
| PDH/PDL-, ON-, IB-Breaks | 49–51 % | 49–51 % | 46–53 % (n. s.) |
| Rejection-Wick, Engulfing, Inside-Bar | 49–50 % | 49–50 % | 49–50 % |
| VWAP-Cross (Follow) | 51,6 % | **52,1 % (z +2,5)** | 49,9 % |
| ≥ 2σ vom VWAP zurück (Fade) | 49,8 % | 49,2 % | 47,4 % |
| RTH-Open-Recross (Follow) | 50,5 % | **52,6 % (z +2,2)** | 50,7 % |
| Momentum-Burst 0,12 ATR | 52,3 % | 51,2 % | 51,9 % |

**Befund:** Fast alles liegt bei 48–53 %.

Ein **skalenabhängiges Muster** wiederholt sich: Nach einem Bruch kommt **kurzfristig eher ein kleiner Rücksetzer** und **auf größerer Skala eher die Fortsetzung**. Das ist die einzige strukturelle Regelmäßigkeit, aber mit ±1,5 Prozentpunkten nach Kosten praktisch nicht verwertbar.

### 3.2 Tageszeit-Karte (Autokorrelation 5- und 15-min-Renditen, je Jahr)
- Fast alle Halbstunden liegen bei ±0,05 und **wechseln das Vorzeichen von Jahr zu Jahr**.
- In allen Jahren gleichgerichtet sind nur:
  - spätes Asien 22:30–24:00 (Mean Reversion −0,09)
  - 08:00 und 10:30–12:00 (leicht negativ, Chop)
  - 13:30 und 15:00 im 15-min-Raster (leicht positiv)
- Die Nacht-Mean-Reversion entspricht < 1 Pkt erwarteter Bewegung, nach Kosten nicht handelbar.

### 3.3 Volumen als Orderflow-Ersatz
- Breakouts mit **hohem** Relativvolumen (1,5–3×) setzen sofort zurück (46,8 % bei 0,03 ATR, z −3,2). Das bestätigt das Rücksetzer-Muster.
- Niedriges Volumen: 54,7 % bei 0,06 ATR (z 1,8, kleines N).
- Absorption und Klimax-Bars: kein Effekt.

### 3.4 Overnight-Inventory, Market Profile
- Overnight-Korrektur in der ersten RTH-Stunde: Korrelation −0,07 / −0,01 / −0,11 (30 min). Fade-Hit 50–55 %, 2024 gegenläufig.
- **80-%-Regel:** Target nur in 34–47 % der Fälle erreicht. 2023 profitabel, 2024 und 2025 klar negativ.

### 3.5 Stabilitätssuche: Gibt es irgendwelche stabilen Taschen?
- 1 008 Kombinationen aus Ereignis × Kontext (Tageszeit, Volatilität, VWAP-Seite, Range-Verbrauch, Daily-Regime) × Skala × Richtung.
- **18** waren in **beiden Hälften von 2023** jeweils > 53 %.
- Davon blieben nur **28 % in 2024 und 2025 beide über 50 %**. Reiner Zufall erwartet ~25 %.
- Mittleres p 2025: **0,463**.
- Besonders die „ruhige Volatilität“-Taschen kippten im volatilen 2025 (p 0,36–0,41).

**Bedingte Muster tragen nicht über Marktphasen.**

## 4. Die Profil-Grenze: Management auf der robusten Edge (MBL)

| Management | WR 2023 / OOS | Ø / max. Verlustserie OOS | Exp R 2023 / OOS | PF OOS |
|---|---|---|---|---|
| Strukturstop, bis Tagesende | 30,5 / 34,2 % | 2,9 / 14 | +0,07 / +0,12 | 1,19 |
| 0,75 × Strukturstop, bis Tagesende | 27,4 / 26,4 % | 3,8 / 21 | **+0,17 / +0,12** | 1,16 |
| 0,5 × Strukturstop, bis Tagesende | 18,5 / 16,1 % | 6,2 / 26 | +0,12 / **−0,02** | 0,98 |
| Teilgewinn 50 % bei 1R + Breakeven | 50,1 / 52,9 % | 2,0 / 8 | +0,02 / +0,07 | 1,14 |
| Teilgewinn 50 % bei 0,5R + Breakeven | **63,9 / 67,8 %** | **1,4 / 6** | −0,00 / +0,02 | 1,05 |
| Fixes Target 1R | 48,9 / 52,3 % | 1,9 / 10 | −0,02 / +0,03 | 1,07 |

**Kernergebnis:** Höhere Winrate und kürzere Verlustserien sind möglich, aber nur, indem man die seltenen großen Gewinner abschneidet. Genau die tragen die Edge. Die Expectancy fällt dann Richtung null.

Auf diesen Daten gibt es **keinen** Punkt, an dem Winrate ≥ 60 %, Verlustserie ≤ 6 und Expectancy deutlich > 0 gleichzeitig erreichbar sind.

## 5. Zeitfenster und Ursachen der Verlustserien (MBL)

| Fenster | PF 2023 | PF 2024 | PF 2025 | max. Verlustserie |
|---|---|---|---|---|
| 09:35–10:30 | 1,22 | 1,17 | 1,01 | 11 |
| **09:35–11:30** | **1,14** | **1,17** | **1,15** | 17 |
| 09:35–13:00 | 1,12 | 1,23 | 1,12 | 16 |
| 09:35–15:30 | 1,10 | 1,29 | 1,09 | 20 |
| 10:30–15:30 | 0,92 | 1,19 | 0,94 | 17 |
| ohne 11:30–13:30 | 1,11 | 1,16 | 1,08 | 18 |

- **Die Edge sitzt am Vormittag**, der Nachmittag allein ist ≈ Zufall.
- Der Walk-Forward mit dem Zeitfenster als Parameter liefert PF 1,16–1,18, max. Verlustserie 15–17. Er wählt meist das volle Fenster.
- Lange Verlustserien (≥ 6) clustern in **bestimmten Monaten** (Juli 2025: 69 % der Trades, Feb./März 2023, Sept. 2025) und häufiger bei niedriger Volatilität (28 % vs. 21 %).
- Diese Monate lassen sich vorab nicht erkennen: Der Volatilitätsfilter, der 2023 half, kippte 2025.

## 6. Schlussfolgerung

1. **Intraday-NQ ist in OHLCV-Daten nahezu ein effizienter Random Walk.** Über 60 Ereignistypen, 1 000 bedingte Kombinationen, ML-Modelle und Literatur-Effekte zeigen OOS höchstens 1–3 Prozentpunkte Abweichung vom Münzwurf.
2. **Die einzige persistente Struktur ist Momentum mit seltenen großen Fortsetzungen.** Sie lässt sich nur mit niedriger Winrate und langen Verlustserien ernten.
3. **Dein Zielprofil** (hohe Winrate + hohe Expectancy + kurze Serien + 2–5 Trades/Tag) braucht eine Vorhersagekraft, die diese Daten nachweislich nicht enthalten. Jede Version, die so aussah, ist OOS zerfallen.
4. Was die Lage realistisch ändern könnte, sind **andere Daten** (Abschnitt 1, UNTESTED). An erster Stelle: Orderflow/Delta/Footprint, ein Wirtschaftskalender mit exakten News-Zeiten und eine längere Historie mit Bärenmärkten.
