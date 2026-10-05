# NQ-Research Runde 4: vom Chart ausgehend

**Vorgehen:** Ich habe echte Kerzencharts aus der CSV gerendert und selbst angesehen:
- 20 zufällig gezogene Handelstage aus 2023 im 5-Minuten-Chart, 08:00–16:00, mit Vortages-Hoch/-Tief, Overnight-Hoch/-Tief, RTH-Open und VWAP
- 8 Eröffnungsphasen im 1-Minuten-Chart, 09:15–11:30

Was mir wiederholt auffiel, habe ich zuerst **beschreibend** quantifiziert. Danach habe ich es objektiv definiert, als Trade mit realistischen Fills getestet und unverändert auf 2024 und 2025 geprüft. Zusätzlich hat ein **Formen-Clustering** (2-Stunden-Kursverläufe im 5-Minuten-Chart, ohne Indikatoren) wiederkehrende Chartformen automatisch gesucht.

Charts: `research/charts/` · Skripte: `chartscan.py`, `s_openrev.py`, `s_openrev_check.py`, `openrev.py`, `s_struct.py`, `s_flag_why.py`, `flag_wf.py`, `motifs.py`, `motif_plot.py`, `s_trendcont.py`, `s_pmrev.py`, `cards4.py`.

**Ergebnis vorweg:** Keine der Chart-Strukturen hält über alle drei Jahre robust. Die stärkste ist die **Flagge (Impuls → enge Konsolidierung → Ausbruch)**:
- Sie hat genau das gewünschte Profil (WR 56–60 %, max. Verlustserie 4–7, Stop ~30 Pkt), **aber nur 2023 und 2024**.
- 2025 kippt sie ins Minus. Im Walk-Forward liegt sie bei PF ≈ 1,0.

---

## Was ich im Chart gesehen habe (vor jeder Messung)

| Nr. | Bild | Beispiele (2023) |
|---|---|---|
| B1 | Eröffnungs-Umkehr: starker erster Move nach 09:30, dann Rückkehr durchs RTH-Open, Trend in Gegenrichtung | 12.01., 13.02., 06.04., 17.04., 10.08., 03.10., 22.11. |
| B2 | Treppe: Impuls → enge Flagge am Impuls-Ende (kein Rücklauf zum VWAP) → nächster Impuls | 13.01., 01.06., 02.08., 08.08., 29.08., 10.11. |
| B3 | Erster VWAP-Test nach Eröffnungs-Drive prallt ab | 17.02., 20.04., 10.11. |
| B4 | Nachmittags-Rückkehr zum VWAP nach starkem Vormittag | 17.04., 20.04., 09.08. |
| M | Formen-Clustering: „sauberer 2-h-Trend, schließt am Extrem“ und „Bein → Rücksetzer → Rückkehr zum Hoch“, fast nur 11:30–16:00 | automatisch gefunden |

---

## Struktur-Steckbriefe

### S1 · FLAGGE / TREPPE (B2)

**Was sehe ich?** Ein kräftiger Impuls, danach seitwärts eine enge Kerzenbox nahe dem Impuls-Hoch ohne tiefen Rücksetzer, dann der Ausbruch in Impulsrichtung.

**Warum könnte das funktionieren?** Die Konsolidierung am Impuls-Ende zeigt, dass die Gegenseite den Preis nicht zurückdrücken kann (Absorption). Der Ausbruch löst Anschlusskäufe aus.

**Objektive Definition (1-min-Bars):**
- Pole: 20 Bars mit einer Range ≥ 0,20 × Tages-ATR, Close am Pole-Ende im oberen 30 %
- Flagge: die folgenden 15 Bars mit einer Range ≤ 40 % der Pole, Flaggen-Tief ≥ Pole-Hoch − 50 % Pole
- Trigger: Close über dem Flaggen-Hoch, 09:35–15:30. Short spiegelbildlich.

**Entry, SL, TP:**
- Entry: Market zur nächsten Open (+1 Tick)
- SL: unter dem Flaggen-Tief − 1 Tick. Das ist die logische Invalidierung: Bricht die Flagge nach unten, ist die Idee tot.
- TP: 1R, alternativ 2R

**Stop-Größe:** Median 27–48 Pkt = 0,12 ATR (struktureller Stop, nicht künstlich groß). Die Gewinner laufen bis P75 0,55–0,74× des Stops gegen die Position.

**Beschreibende Prüfung, P(+1R vor −1R), Random Walk = 50 %:**

| Jahr | P(+1R vor −1R) | Abweichung |
|---|---|---|
| 2023 | 63,0 % | +13 Pp |
| 2024 | 53,6 % | +4 Pp |
| 2025 | 40,8 % | −9 Pp |

**Trade-Backtest (Ziel 1R):**

| Jahr | Trades | Trades/aktiver Tag | WR | Ø Win / Ø Loss | PF | Exp | max. Verlustserie | Ø Verlustserie | MaxDD |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 142 | 1,3 | 59,9 % | 0,96 / −0,99 | **1,45** | +0,18R | 4 | 1,7 | 7,3R |
| 2024 | 136 | 1,3 | 55,9 % | 0,97 / −1,01 | **1,21** | +0,10R | 7 | 1,8 | 8,7R |
| 2025 | 113 | 1,3 | 44,2 % | 0,99 / −1,00 | **0,78** | −0,12R | 5 | 2,0 | 13,2R |

Ziel 2R: PF 1,39 / 1,27 / 0,80.

**Walk-Forward** (Familie mit 162 Varianten: Pole/Flagge, Ziel, Trendfilter, Zeitfenster):

| Mindest-Trades/Tag | PF | Exp | max. Verlustserie |
|---|---|---|---|
| 0,25 | 1,08 | +0,04R | 11 |
| 0,5 | 0,96 | −0,02R | 11 |
| 1,0 | 1,02 | +0,01R | 9 |

**Warum es manchmal nicht funktioniert:**
- Die Flagge folgt dem übergeordneten Marktzustand.
  - 2023 (ruhiger Aufwärtsmarkt): Long-Flaggen 70 %
  - 2025 (Abverkäufe, hohe Volatilität): Long-Flaggen 38 %
- In ruhiger Intraday-Volatilität (atr60 < atr390) hielt die Flagge in allen Jahren (72 / 58 / 57 %). Das sind aber nur ~25–30 Trades pro Jahr. Der Effekt wurde **nach** Blick auf 2024/25 gefunden und gilt daher nur als Spur, nicht als Ergebnis.
- Ein Trendfilter (Daily-SMA20) verbesserte 2023 nur minimal und wurde vom Walk-Forward nie gewählt.

**Status:** IDEA TO REWORK. Das beste Profil aller Runden, aber regimeabhängig. Ohne längere Historie mit mehreren Regimen ist nicht entscheidbar, ob die Regime-Abhängigkeit vorab erkennbar ist.

### S2 · ERÖFFNUNGS-UMKEHR DURCH DAS RTH-OPEN (B1)

**Was sehe ich?** Ein starker erster Move bildet das frühe Extrem. Der Preis fällt zurück durchs Open, der Tag trendet in Gegenrichtung.

**Warum könnte das funktionieren?** Die frühe Bewegung ist Auktions-Imbalance, nach dem Re-Cross sind die frühen Käufer gefangen.

**Definition:**
- Frühe Bewegung ≥ 0,15 ATR weg vom Open bis 10:30/11:00, danach Re-Cross des Opens
- Entry-Level: Sell-Stop am Open − 1 Tick (oder Close-Bestätigung)
- SL am frühen Extrem (logische Invalidierung) bzw. 0,5–0,75× der Spanne
- TP 0,5–1× der Spanne jenseits des Opens

**Beschreibende Studie:** Zunächst 73–81 % vs. 66,7 % Random Walk in allen Jahren. Sah robust aus.

**Fehler gefunden:** Gemessen wurde ab dem Open, obwohl das Ereignis erst durch einen Close jenseits des Opens ausgelöst wird. Ab dem echten Entscheidungspreis:

| Jahr | Trefferquote | Random Walk |
|---|---|---|
| 2023 | 74,6 % | 74,1 % |
| 2024 | 79,2 % | 75,4 % |
| 2025 | 73,6 % | 76,4 % |

**Kein Vorteil.**

**Trade-Backtest (72 Varianten × 3 Jahre):**
- Beste Variante: Stop-Entry, Stop am Extrem, TP 0,5×: WR 61–67 %, max. Verlustserie 4, aber **PF 0,99 / 0,77 / 1,03**
- Keine Variante ist in allen Jahren positiv

**Warum der Eindruck täuschte:** Umkehr-Trend-Tage sind einprägsam. Tatsächlich wird das frühe Extrem in 56–76 % der Fälle am selben Tag doch wieder erreicht.

**Status:** FAILED.

### S3 · ERSTER VWAP-TEST NACH ERÖFFNUNGS-DRIVE (B3)

**Definition:**
- Seit 09:30 mindestens N Minuten keine VWAP-Berührung und maximaler Abstand ≥ X ATR
- Danach der erste Touch, Entry als Limit am VWAP
- Ziel: das Drive-Extrem; Stop jenseits des VWAP

**Ergebnis:** Nur 5–16 Fälle in 2023, weil der VWAP zur Eröffnung am Preis startet. Bei 16 Fällen war die Trefferquote mit engem Stop sogar schlechter als Zufall.

**Status:** FAILED / zu selten in dieser Definition.

### S4 · NACHMITTAGS-RÜCKKEHR ZUM VWAP (B4)

**Definition:**
- Um 12:00/13:00/14:00: Bewegung ab RTH-Open ≥ 0,3/0,5 ATR, Preis im äußeren 25 % der Tagesrange → Fade
- Ziel = VWAP (natürliches Ziel), Stop = jenseits des Tages-Extrems (Invalidierung: neues Extrem)

**Ergebnis:**
- Abweichung zum Random Walk 2023 −5 bis +9 Pp, 2024 −6 bis +3 Pp, 2025 −14 bis 0 Pp
- **Starke Vormittags-Trends laufen eher weiter, als zum VWAP zurückzukehren.**

**Status:** FAILED. Der visuelle Eindruck war Auffälligkeits-Verzerrung.

### S5 · SAUBERER 2-H-TREND AM EXTREM (Formen-Clustering)

**Was sehe ich?** In den Cluster-Mittelwerten: ein gleichmäßiger Trend über 2 h, der am Extrem schließt, läuft 30 min weiter. 3 von 3 auffälligen Clustern behielten ihr Vorzeichen.

**Definition:**
- 11:30–15:00 zur 5-min-Close: Effizienz (Netto-Bewegung / 2-h-Range) ≥ 0,7, Range ≥ 0,25 ATR, Close im äußeren 15 %
- Erstes Ereignis pro Tag und Seite
- Stop jenseits des 30-min-Swings (Median 44–63 Pkt), Ziel 1R

**Trade-Backtest:**

| Jahr | WR | PF | max. Verlustserie |
|---|---|---|---|
| 2023 | 48,3 % | 0,85 | 7 |
| 2024 | 54,5 % | 1,18 | 6 |
| 2025 | 51,3 % | 1,00 | 6 |

**Status:** FAILED. Der Cluster-Mittelwert (+1–2 % ATR in 30 min) trägt keinen Trade mit logischem Stop.

---

## Was diese Runde methodisch gezeigt hat

1. **Visuelle Muster täuschen systematisch.** Bei allen vier Chart-Bildern war die Häufigkeit des „schönen“ Ausgangs viel geringer, als es beim Anschauen wirkte. Die Charts bleiben als Ideenquelle wertvoll, die Messung muss aber entscheiden.
2. **Referenzpunkt-Fehler sind leicht gemacht.** Die Eröffnungs-Umkehr sah über alle Jahre robust aus. Erst die Messung ab dem echten Entscheidungspreis zeigte: kein Vorteil.
3. **Echte Muster sind regimeabhängig.** Die Flagge war 2023 deutlich (+13 Pp), 2025 umgekehrt (−9 Pp). Drei Jahre reichen nicht, um zu klären, ob sich das Regime vorab erkennen lässt.

## Vergleich mit den Benchmarks der früheren Runden

| Kandidat | WR | PF (je Jahr bzw. WF) | max. Verlustserie | Stop | Trades/aktiver Tag | robust? |
|---|---|---|---|---|---|---|
| MBL (Runde 2) | 30–34 % | 1,10 / 1,29 / 1,09; WF 1,13–1,18 | 14–20 | ~52 Pkt | ~1,9 | ja, klein |
| Portfolio MBL+OBR (Runde 2) | 29–34 % | WF 1,29 | 13–18 | 25–52 Pkt | ~2,5 | eingeschränkt (OBR fragil) |
| **Flagge (Runde 4)** | **44–60 %** | **1,45 / 1,21 / 0,78; WF 0,96–1,08** | **4–7** | **~30 Pkt** | 1,3 | **nein (Regime)** |
| Eröffnungs-Umkehr (Runde 4) | 47–67 % | 0,77–1,06 | 4–7 | 32–90 Pkt | 1,0 | nein |

## Empfehlung

- Die Flagge kommt deinem Zielprofil am nächsten.
- Ob ihr Regime-Problem lösbar ist, lässt sich mit 3 Jahren Daten, die jetzt alle „gesehen“ sind, **nicht ehrlich klären**.
- Der nächste sinnvolle Schritt sind **mehr historische NQ-1-min-Daten, idealerweise 2010–2022** (inkl. 2018, 2020, 2022). Daran ließen sich unberührt prüfen:
  - die Flagge in vielen Marktphasen
  - der Hinweis „ruhige Volatilität“
  - ein vorab erkennbarer Regime-Filter
- Ohne neue Daten würde jede weitere Verfeinerung auf 2023–2025 zwangsläufig auf bereits gesehene Daten optimieren.
