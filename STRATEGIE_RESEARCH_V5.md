# NQ-Research Runde 5: Hypothese „Range → Deviation → Entry“

Alle Zahlen stammen aus Python-Backtests auf der CSV (12/2022–12/2025). **Ein TradingView-Backtest wurde nicht ausgeführt.**

**Ausführung (konservativ):**

| Situation | Annahme |
|---|---|
| Market-Entry | nächste Open + 1 Tick |
| Stop-Entry | max(Level, Open) + 1 Tick |
| Limit-Entry | Preis muss 1 Tick durchhandeln |
| Stops | −1 Tick Slippage |
| Kommission | 0,25 Pkt |
| Fill-Kerze | nur der Stop wird geprüft |

Discovery lief auf 2023, die Prüfung auf 2024 und 2025, dazu ein Walk-Forward mit 12 Monaten Training und 3 Monaten Test.

Skripte: `research/rangelib.py`, `rd_map.py`, `rd_placebo.py`, `rd_map2.py`, `rd_charts.py`, `rd_speed.py`, `rd_exits.py`, `rd_mech.py`, `rd_wf.py`, `rd_concept.py`, `rd_econ.py`, `rd_econ15.py`, `rd_wf2.py`, `rd_robust.py`
Charts: `research/charts/rd_*.png`

---

## Kurzantwort

**Ja, rund um Ranges und Deviations gibt es wiederkehrendes Verhalten. Es ist aber klein, und die Wahl der besten Variante ist nicht stabil.**

| Erkenntnis | Stärke | Robust über 2023 / 2024 / 2025? |
|---|---|---|
| **Die bloße Berührung einer Deviation ist ein Fake.** Stop-Entries direkt am Level verlieren (PF 0,78–0,90) | deutlich | ja, in allen Jahren negativ |
| **Erst der Kerzen-Schluss jenseits einer weiten Deviation (≥ 1–1,5× Range) erzeugt Fortsetzung.** Der Effekt steigt monoton mit der Deviation | klein (+3 bis +6 Pp) | ja, solange die Variante fest bleibt |
| Reversion an Deviations (Limit-Fade, Sweep & Reclaim → Gegenrichtung) | negativ | ja, verliert in allen Jahren |
| **Vortages-Hoch/-Tief nicht faden.** Limit-Fade am ersten Kontakt gewinnt nur 28–35 % (0,1 ATR) | sehr deutlich | ja, das ist der stabilste Befund der Runde |
| Walk-Forward über die Wahl von Deviation, Stop und Exit | PF 0,95–0,99 | **nein** |

**Fazit:** Das Konzept *„Akzeptanz jenseits einer weiten Deviation → Fortsetzung“* ist echt, aber es ist dieselbe kleine Momentum-Edge wie in Runde 2 (MBL), nur in Level-Form. Fest gehaltene Varianten sind in jedem Jahr positiv. Die Auswahl der besten Variante per Walk-Forward liefert jedoch ≈ 0. **Als robust handelbar im strengen Sinn kann ich es nicht bezeichnen.**

---

## 1. Getestete Range-Definitionen (11) und Deviations

| Range | Bildung | Gültig für Entries | Mediane Breite (2023) |
|---|---|---|---|
| OR15 / OR30 / IB60 | 09:30–09:45 / 10:00 / 10:30 | bis 15:30 | 62 / 79 / 108 Pkt |
| Pre-Market | 08:00–09:30 | 09:30–15:30 | 57 Pkt |
| Overnight | 18:00–09:30 | 09:30–15:30 | 115 Pkt |
| Asia | 18:00–02:00 | 02:00–15:30 (London + NY) | 56 Pkt |
| London | 02:00–08:30 | 08:30–15:30 | 79 Pkt |
| Vortag RTH | 09:30–16:00 Vortag | 09:35–15:30 | 184 Pkt |
| Stunden-Block | jede volle Stunde 09:30–15:30 | nächste Stunde | 68 Pkt |
| Kompressions-Box 30 Bars < 0,10 ATR | lokale Konsolidierung | nächste 60 Bars | 22 Pkt |
| Kompressions-Box 60 Bars < 0,15 ATR | lokale Konsolidierung | nächste 60 Bars | 33 Pkt |

**Deviations:**
- 0 (Range-Kante), 0,25 / 0,5 / 1,0 / 1,5 / 2,0 × Range-Breite
- Zusätzlich ATR-basierte Ziel- und Stop-Abstände

## 2. Beobachtung: Was passiert am ersten Kontakt? (`rd_map.py`, `rd_placebo.py`)

**Placebo** (zufällige Levels, gleiche Mechanik, ±0,1 ATR): Continuation 0,47–0,50, Reversion 0,48–0,51.

**Muster 2023 über fast alle Range-Typen:**
- **Kleine Deviation (0,25–0,5×):** eher Rücklauf. Beispiele: Pre-Market Continuation 0,38–0,40 / Reversion 0,54; Overnight k = 0,25: 0,42 / 0,58
- **Große Deviation (1–1,5×):** eher Fortsetzung. Beispiele: OR30 k = 1,5: 0,60 / 0,35; IB k = 1: 0,61 / 0,39; Overnight k = 1,5: 0,66 / 0,34

**Prüfung 2024/25:**
- Der Rücklauf bei kleinen Deviations ist **nicht stabil**: 2024 meist verschwunden.
- Konsistent negativ war nur die **Stop-Entry-Fortsetzung bei kleinen Deviations** (Pre-Market, London, Asia: 0,38–0,46).
- Die Gegenposition (Reversion) gewinnt aber nicht entsprechend. Grund: Viele erste Berührungen sind Spikes, die sofort zurückdrehen, und zwar weniger als 0,1 ATR. Sie schaden dem Stop-Entry, ohne dem Limit-Fade zu nützen.
- **Vortages-Range:** Reversion in allen Jahren 0,28–0,35 (k = 0, 0,1 ATR). PDH/PDL zu faden ist systematisch falsch.

## 3. Saubere Messung vom Entscheidungspreis (`rd_map2.py`)

Gemessen ab dem Close der Signal-Kerze (Lehre aus Runde 4). Konsistent über alle drei Jahre war **Mechanismus C (Close jenseits Deviation → Fortsetzung)** bei weiten Deviations:

| Range | k | P(+0,1 ATR vor −0,1 ATR) 2023 / 24 / 25 |
|---|---|---|
| Overnight | 0,5 | 0,558 / 0,603 / 0,531 |
| London | 1,0 | 0,525 / 0,588 / 0,536 |
| OR15 | 1,5 | 0,556 / 0,521 / 0,521 |
| Vortag | 0,25 | 0,545 / 0,536 / 0,528 |
| Box 30 | 1,5 | 0,514 / 0,506 / 0,543 |

Sweep & Reclaim zeigte **keine** konsistente Zelle.

## 4. Visuelle Validierung (`rd_charts.py`)

**Overnight + 0,5×, 2023:** je 8 zufällige Gewinner und Verlierer.
- Eindruck: Gewinner erreichen die Deviation langsam, mit Akzeptanz außerhalb der Range. Verlierer kommen per Spike.
- **Quantifiziert (`rd_speed.py`, 5 Zellen gepoolt): widerlegt.**
  - Schnelle Ankunft: 0,60 / 0,54 / 0,56
  - Langsame Ankunft: 0,54 / 0,60 / 0,48
  - Bars außerhalb der Range und Tageszeit: ebenfalls kein stabiles Muster

**OR15 + 1,5×, Gewinner und Verlierer aus 2024–25:**
- Gewinner sind Trend-Tage.
- Verlierer kommen häufig nach langem Lauf (Einstieg am Ende eines V-Beins) oder mittags/nachmittags.
- Ein visuell klarer, stabiler Trennfaktor ist nicht erkennbar.

## 5. Welcher Mechanismus erzeugt den Edge? (`rd_mech.py`, 5 Zellen, Risiko 0,1 ATR)

| Mechanismus | Ziel 2R: PF 23 / 24 / 25 | bis Session-Ende: PF 23 / 24 / 25 |
|---|---|---|
| A Stop-Entry am Deviation-Level (Touch) | **0,82 / 0,90 / 0,78** | 0,97 / 1,01 / 0,67 |
| **C Close jenseits → Market** | **1,10 / 1,14 / 1,18** | 1,17 / 1,45 / 1,04 |
| D Close, dann Retest-Limit am Level (15 Bars) | 1,06 / 1,01 / 1,06 | **1,25 / 1,40 / 1,12** |
| E/F Sweep & Reclaim → Gegenrichtung | 0,89 / 0,95 / 0,82 | 0,81 / 0,81 / 1,10 |
| B Limit-Reversion am Level | (Karte §2: ≈ Placebo, Vortag deutlich negativ) | — |

**Der Edge entsteht durch Akzeptanz, also einen Kerzen-Schluss jenseits der Deviation, nicht durch die Berührung.**

## 6. Konzepttest ohne Zellen-Auswahl (`rd_concept.py`, alle 11 Range-Typen gepoolt)

| k | Exit | PF 2023 / 2024 / 2025 | Exp R | WR | max. Verlustserie |
|---|---|---|---|---|---|
| 0,5 | 2R | 1,06 / 1,01 / 0,96 | +0,04 / +0,01 / −0,03 | 34–36 % | 12–15 |
| 1,0 | 2R | 1,15 / 1,08 / 1,07 | +0,09 / +0,05 / +0,04 | 36–39 % | 10–11 |
| 1,0 | Session-Ende | 1,23 / 1,24 / 1,07 | +0,18 / +0,19 / +0,05 | 22–26 % | 13–19 |
| 1,5 | Session-Ende | 1,24 / 1,36 / 1,14 | +0,18 / +0,27 / +0,10 | 24–27 % | 11–19 |

**Monoton in k**, positiv in jedem Jahr für k ≥ 1.

## 7. SL/TP-Ökonomie aus MAE/MFE (`rd_econ.py`, `rd_econ15.py`)

**Weg ohne Stop bis Session-Ende** (ab Entry): MFE Median 0,21–0,22 ATR (P75 0,42), MAE Median 0,19–0,20 ATR. Nur 30 % der Ereignisse laufen weniger als 0,1 ATR gegen den Entry.

**Stops:**

| Stop | Ergebnis |
|---|---|
| 0,05 ATR (~15 Pkt) | in guten Jahren hoher PF, 2025 schwach (k 1,0: +0,06 R) bzw. negativ (k 1,5: −0,13 R), Verlustserien 25–37 |
| **0,10–0,15 ATR (27–47 Pkt)** | bestes robustes Verhältnis |
| Deviation-Level − 0,25 Range | 2025 negativ |
| Range-Kante (55–90 Pkt) | zu weit, 2025 negativ |
| Swing 10 Bars | 2025 negativ |

**Targets:**

| Target | Ergebnis |
|---|---|
| Nächste Deviation (+0,5 Range) | hohe WR (55–67 %); bei k 1,0 nur klein positiv (+0,03 bis +0,05 R), bei k 1,5 in 2024/25 negativ |
| 1R | ≈ 0 |
| 2R / 3R | positiv, schwächer als Runner |
| **Runner bis Session-Ende** | höchste Expectancy |
| **Teilgewinn 50 % @1R + Breakeven** | bestes Winrate- und Verlustserien-Profil |

**Die beiden Profile:**

| Variante | WR | Ø Win / Ø Loss | PF | Exp | max. / Ø Verlustserie | MaxDD | Ø DD | Trades/aktiver Tag | SL Ø / Median | MFE / MAE (R) | Haltedauer |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A: k 1,0, Stop 0,15 ATR, 50 % @1R + BE, Runner bis 15:59** | **52,1 %** | 1,02 / −0,98 R | 1,14 | +0,066 R | **6 / 2,0** | 21,5 R | 4,7 R | 2,0 | 47 / 42 Pkt | 1,52 / 0,67 | 112 min |
| **B: k 1,5, Stop 0,10 ATR, Runner bis 15:59** | 25,4 % | 3,68 / −1,00 R | 1,25 | +0,188 R | 19 / 3,7 | 43,8 R | 6,8 R | 1,7 | 31 / 27 Pkt | 2,14 / 0,85 | 101 min |

Variante A je Jahr: PF 1,12 / 1,21 / 1,08, Exp +0,06 / +0,10 / +0,04 R, max. Verlustserie 6 / 6 / 6.
Variante B je Jahr: PF 1,24 / 1,36 / 1,14, Exp +0,18 / +0,27 / +0,10 R.

## 8. Walk-Forward (die entscheidende Prüfung)

| Walk-Forward | PF | Exp | max. Verlustserie | Trades/aktiver Tag |
|---|---|---|---|---|
| Zellen-Portfolio (176 Zellen, je Quartal Top-Zellen aus 12 Monaten) | 0,99–1,04 | −0,01 bis +0,03 R | 16–19 | 2,0–3,5 |
| Konzept (alle Ranges; k / Stop / Exit gewählt) | 0,95–0,99 | −0,03 bis −0,01 R | 13–15 | 2,1 |

**Warum der Walk-Forward scheitert, obwohl feste Varianten jedes Jahr positiv sind:**
- Die beste Variante wechselt von Quartal zu Quartal (2R → Teilgewinn → Runner). Die zuletzt beste Variante liefert im Folgequartal unterdurchschnittlich.
- Mit 2023-Daten allein hätte man k 1,5 mit Stop 0,05 ATR + Runner gewählt (beste Expectancy 2023). Diese Variante verliert 2025 (−0,13 R).
- Der echte Effekt ist klein, die Variantenwahl verrauscht ihn.

## 9. Session, Regime, Tage (`rd_wf2.py`, `rd_robust.py`)

**Expectancy je Session (Variante B):**

| Session | 2023 | 2024 | 2025 |
|---|---|---|---|
| London | −1,02 | +0,59 | +0,13 |
| NY Pre | +0,52 | −0,00 | −0,28 |
| NY Open 09:30–10:00 | +0,40 | +0,64 | −0,22 |
| **NY AM 10:00–11:30** | **+0,20** | **+0,14** | **+0,61** |
| NY Mitte | +0,21 | +0,28 | +0,04 |
| NY PM | +0,25 | +0,14 | −0,28 |

Variante A in NY AM: +0,00 / +0,17 / +0,03.

**Einziges stabil positives Fenster: NY-Vormittag 10:00–11:30.** Gefunden mit Blick auf alle Jahre, also nur ein Hinweis, kein validierter Filter. Ein solcher Filter senkt die Frequenz auf ~0,5 Trades/Tag.

**Volatilität (ATR-Terzile):** niedrig/mittel +0,26 / +0,29 R (B), hoch +0,02 R. **Im Hochvolatilitäts-Regime ist der Edge weg.**

**Monate:** 58 % (B) bzw. 67 % (A) positiv. Schlechtester Monat −19,8 R (B) bzw. −12,7 R (A).

**Tagestyp (ex-post):** Trend-Tage +1,18 R (B), Range-Tage −0,73 R. Das ist klassisches Momentum.

## 10. Varianten, die nicht funktionieren (dokumentiert)

- Stop-Entry bei Berührung der Deviation (alle Range-Typen): verliert, die Berührung ist meist ein Fake
- Limit-Reversion an Deviations: ≈ Placebo; an Vortages-Extremen klar negativ
- Sweep & Reclaim → Gegenrichtung: negativ
- Stunden-Block-Ranges: ≈ 0 bei k ≤ 0,5
- Kleine Deviations (0,25–0,5×) als Reversion-Zone: nur 2023 sichtbar
- Stops an der Range-Kante oder knapp hinter dem Level, Ziele an der nächsten Deviation bei k 1,5: 2024/25 ≈ 0 oder negativ
- Visueller Filter „langsame Ankunft / Akzeptanz“: widerlegt
- Zellen-Auswahl nach Vergangenheit: nicht persistent

## 11. Vergleich mit den Benchmarks

| Kandidat | WR | PF (fest je Jahr) | Walk-Forward PF | max. Verlustserie | Stop | Trades/aktiver Tag |
|---|---|---|---|---|---|---|
| MBL (Runde 2) | 30–34 % | 1,10 / 1,29 / 1,09 | **1,13–1,18** | 14–20 | ~52 Pkt | ~1,9 |
| Flagge (Runde 4) | 44–60 % | 1,45 / 1,21 / 0,78 | 0,96–1,08 | 4–7 | ~30 Pkt | 1,3 |
| **Deviation A (Runde 5)** | **52 %** | 1,12 / 1,21 / 1,08 | 0,95–0,99 (Familie) | **6** | ~42 Pkt | **2,0** |
| **Deviation B (Runde 5)** | 25 % | **1,24 / 1,36 / 1,14** | 0,95–0,99 (Familie) | 19 | ~27 Pkt | 1,7 |

**Einordnung:**
- **Deviation A** hat das beste Gesamtprofil aller fest gehaltenen Varianten im Sinne deines Ziels: rund 50 % WR, max. 6 Verluste in Folge, 2 Trades/Tag, in jedem Jahr positiv. Die Expectancy ist aber dünn (+0,07 R).
- **Deviation B** hat die höchste fest gehaltene Expectancy, aber Momentum-typische lange Verlustserien.
- Robuster im Walk-Forward bleibt MBL.

## 12. Empfehlung

1. Als **Ergebnis** dieser Hypothese halte ich fest:
   - Range-Deviations funktionieren nur als **Akzeptanz-Breakout bei weiter Deviation** (Close jenseits ≥ 1–1,5× Range), nicht als Reversion- oder Touch-Level.
   - Vortages-Extreme nie faden.
2. **Variante A** ist ein sinnvoller Kandidat für einen **Vorwärtstest** ab 12/2025 auf ungesehenen Daten, wenn du das Profil (52 % WR, Serien ≤ 6, kleine Expectancy) akzeptierst. Als Level-Indikator lässt sie sich sehr gut darstellen:
   - Range-Box mit den Deviation-Linien ±1,0×
   - Entry nach Kerzen-Schluss jenseits der Linie
   - SL 0,15 ATR
   - 50 % bei 1R, danach Breakeven, Rest bis 15:59
3. Für einen **echten Robustheitsnachweis** fehlen weiterhin unberührte Daten. Mit NQ-1-min-Daten 2010–2022 ließe sich prüfen:
   - ob der Akzeptanz-Effekt in vielen Regimen trägt
   - ob sich der Hochvolatilitäts-Ausfall vorab filtern lässt
