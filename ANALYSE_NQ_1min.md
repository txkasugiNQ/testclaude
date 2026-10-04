# NQ 1-Minuten-Daten – Analyse & Konzept für einen TradingView-Indikator

Datei: `Dataset_NQ_1min_2022_2025 (1).csv` · Reproduzierbare Skripte: `analysis/01_load.py` … `13_final.py`
(im Ordner `analysis/` der Reihe nach ausführen; benötigt `pandas`, `numpy`).

---

## 1. Was steckt in der CSV?

| Spalte | Inhalt | Befund |
|---|---|---|
| `timestamp ET` | `MM/DD/YYYY HH:MM`, New-York-Zeit | **Zeitstempel = Schlusszeit der Kerze** (erste RTH-Kerze heißt `09:31`, Session beginnt `18:01`, endet `17:00`) |
| `open, high, low, close` | Preise in Punkten | alle exakt im 0,25-Tick-Raster, OHLC immer konsistent |
| `volume` | Kontrakte pro Minute | kein 0- oder Negativwert, Ø 421, max 18 535 |
| `Vwap_RTH` | Session-VWAP ab 09:30 | `0` außerhalb 09:31–17:00 (68 % der Zeilen). Läuft nach 16:00 bis 17:00 weiter. Nachgerechnet: identisch mit Σ(Typical Price·V)/ΣV, Typical Price = (H+L+C)/3 |
| `Vwap_ETH` | VWAP der Globex-Session | Reset bei 18:01, nie 0 |

- **Zeiteinheit:** 1 Minute, Globex-Handel (ETH) 18:00–17:00 ET, 23 Std/Tag
- **Zeitraum:** 26.12.2022 18:01 bis 11.12.2025 20:52
- **Zeilen:** 1 048 575 Datenzeilen + Header = **1 048 576 = exakt das Excel-Zeilenlimit**
- **Handelstage:** 767 Sessions, davon 729 mit voller RTH (390 Minuten), 33 verkürzte Feiertags-Sessions
- **Marktinformationen:** nur Preis, Volumen und zwei VWAPs. **Keine** Bid/Ask-Daten, kein Delta/Orderflow, kein Open Interest, keine Kontrakt- oder Rollkennung, keine Tick- oder Footprint-Daten.

## 2. Datenqualität: fehlende oder fehlerhafte Daten

Formal ist die Datei sauber: keine NaNs, keine doppelten Zeitstempel, streng aufsteigend sortiert, keine OHLC-Widersprüche. Inhaltlich gibt es vier wichtige Punkte:

1. **Datei ist abgeschnitten.** Sie endet mitten in einer Session (11.12.2025 20:52) bei genau 1 048 576 Zeilen. Fast sicher wurde sie mit Excel gespeichert und dabei gekürzt. Die letzte Session ist unvollständig, alles danach fehlt.
2. **Back-adjusted Continuous Contract (Schluss aus den Preisen).** Der erste Schlusskurs (Ende Dez. 2022) liegt bei ca. 13 680. Der tatsächliche Front-Month-NQ stand damals bei ca. 11 000. Ende 2023 beträgt die Differenz ca. 2 000 Punkte, Ende 2025 ist sie annähernd 0. Die Rollverluste wurden also additiv rückwirkend aufgeschlagen. Die beiden Vergleichskurse stammen aus meinem Marktwissen, nicht aus der CSV. Die Richtung ist eindeutig, die genauen Offsets sind Näherungen. Folgen:
   - **Absolute historische Preise sind keine real gehandelten Levels.** Runde Zahlen (00/50/000) lassen sich mit dieser CSV nicht prüfen. Im Test unten dienen sie deshalb als Placebo.
   - Prozentangaben sind in den Anfangsjahren verzerrt. Ich normiere deshalb alles auf die **ATR in Punkten**.
3. **Echte Lücken:**
   - Feiertage, Early Closes (13:00/13:15) und Wochenenden: normal
   - 05.04.2023, 14:03–20:01: Datenausfall (358 min)
   - 07.04.2023: Karfreitag, Session endet 09:15
   - 09.01.2025: Handelsschluss 09:30 (nationaler Trauertag für Carter)
   - 28.11.2025: Lücke 21:45 → 08:31 (CME-Ausfall)
   - zusätzlich ~140 kleine 2- bis 10-Minuten-Lücken (Minuten ohne Umsatz), vernachlässigbar
4. **Extremwerte sind real, keine Fehler:** Zollschock April 2025 (Tagesrange bis 2 650 Punkte, 1-Minuten-Kerzen > 2 %), Wochenend-Gaps bei Sonntagseröffnung (z. B. 06.04.2025 −780 Punkte).

**Für TradingView heißt das:** Pine Script kann die CSV nicht einlesen. Der Indikator muss alles live aus dem Chart berechnen. Die CSV dient nur zur **Kalibrierung und Validierung** der Logik. Zeitstempel-Konvention: CSV = Schlusszeit, TradingView = Eröffnungszeit. Die CSV-Kerze `09:31` entspricht also der TV-Kerze `09:30`.

## 3. Markt- und Volatilitätsstruktur

**Tagesrange (volle ETH-Session) in Punkten, nur Tage mit voller RTH:**

| Jahr | Median | 10 % | 90 % | Max |
|---|---|---|---|---|
| 2023 | 233 | 147 | 362 | 601 |
| 2024 | 270 | 161 | 508 | 1 077 |
| 2025 | 361 | 192 | 646 | 2 652 |

- Die Volatilität in Punkten hat sich fast verdoppelt. **Feste Punkt-Parameter wären Overfitting.** Normiert auf die ATR(14) des Vortags ist die Verteilung stabil: Median Range/ATR = 0,95, 90 %-Quantil 1,61, 95 %-Quantil 1,87.
- **Volatility Clustering:** Autokorrelation der log. Tagesrange = 0,46 (Lag 1) und bleibt bis Lag 5 bei ~0,4. Die ATR ist daher ein guter Prognosewert für heute.
- RTH deckt im Median 85 % der ETH-Tagesrange ab.
- **Wochentag:** Montag ruhigste Tage (0,85 ATR), Donnerstag die volatilsten (1,06 ATR).
- **NR7 und Inside Days führen hier nicht zu Expansion.** Die Folgetag-Range liegt mit 0,86–0,88 ATR sogar unter dem Schnitt von 0,93. Die gängige Trading-Regel bestätigt sich in diesen Daten nicht.

**Intraday-Volatilitätsprofil** (Ø Minutenrange relativ zum Tagesschnitt):
- 09:30–10:00: 2,9×
- 10:00–10:30: 2,5×
- 10:30–11:00: 2,1×
- 15:30–16:00: 1,8×
- Einzelminuten-Spitzen: 09:30 (4,3×), **08:30 (4,3×, Wirtschaftsdaten)**, **10:00 (4,0×, Daten)**, 15:50 (3,2×, MOC-Imbalances)

## 4. Wann entstehen Tops und Bottoms?

**Zeitpunkt von RTH-Hoch (HOD) und RTH-Tief (LOD), 729 volle RTH-Tage:**

| Fenster | HOD | LOD |
|---|---|---|
| 09:30–09:45 | **21,7 %** | **24,3 %** |
| 09:45–10:00 | 6,7 % | 8,6 % |
| 10:00–10:30 | 8,6 % | 10,3 % |
| 10:30–15:45 | ~48 % | ~47 % |
| 15:45–16:00 | **14,4 %** | 10,4 % |

- Zum Vergleich ein reiner Zufallspfad (Arcsinus-Gesetz): P(Extrem in den ersten 15 min) ≈ 12,6 %. **Die ersten 15 RTH-Minuten bilden fast doppelt so oft das Tageshoch oder -tief wie bei Zufall.** Das ist der stärkste Befund dieser Analyse.
- Das ETH-Tageshoch fällt zu 55 % in die RTH, zu 16 % in Asien und zu 11 % nach London. Beim Tagestief sind es 49 % RTH und 22 % Asien.

**Opening Range (OR) der RTH:**

| OR-Länge | P(OR-High = HOD) | P(OR-Low = LOD) | P(eines davon) | P(beide Seiten gebrochen) | OR-Breite/ATR | Median-Extension (OR-Vielfache) |
|---|---|---|---|---|---|---|
| 5 min | 14 % | 16 % | 30 % | 70 % | 0,17 | 1,8× |
| 15 min | 22 % | 24 % | 46 % | 54 % | 0,25 | 1,1× |
| 30 min | 28 % | 33 % | 61 % | 39 % | 0,32 | 0,8× |
| 60 min (IB) | 37 % | 43 % | **78 %** | 22 % | 0,43 | 0,55× |

## 5. Kerntest: Sind Levels überhaupt Levels?

**Methode (kausal, ohne Lookahead):**
- Jedes Level wird nur aus Daten gebildet, die zum Zeitpunkt der Nutzung bekannt sind.
- Pro RTH-Tag zählt der erste Touch. Die Seite (Widerstand oder Support) richtet sich nach dem RTH-Open.
- Ab dem Touch wird geprüft, ob der Preis zuerst ±R vom Level entfernt zurückläuft („hält“) oder zuerst R über das Level hinausläuft („bricht“). R = 0,1 bzw. 0,2 × ATR.
- Liegen beide Barrieren in derselben Kerze, zählt das konservativ als „bricht“.
- **Kontrolle:** dieselbe Messung am selben Tag an Levels, die um ±0,1/0,2/0,3 ATR verschoben sind. Gemessen wird der Vorsprung (*Edge*) des echten Levels gegenüber dieser Kontrolle.
- Zusätzlich aufgeteilt in In-Sample (2023–24) und Out-of-Sample (2025).

**Ergebnis (R = 0,1 ATR, Auszug):**

| Level | Touch-Rate | N | Halten | Kontrolle | Edge | z | Edge 2025 |
|---|---|---|---|---|---|---|---|
| Vortags-POC (RTH) | 57 % | 402 | 53,0 % | 49,0 % | +4,0 | 1,6 | +10,1 |
| Vortags-VWAP (Settle) | 56 % | 397 | 53,1 % | 50,0 % | +3,1 | 1,3 | +6,8 |
| Overnight High | 66 % | 462 | 50,4 % | 48,9 % | +1,5 | 0,7 | +4,5 |
| Asia H / London H | 66–70 % | ~480 | ~50 % | ~50 % | ±0,7 | ~0 | ~0 |
| 15-min-Swing-Pivots (unberührt) | ~60 % | ~415 | ~48 % | ~50 % | −1 bis −2 | <1 | ~0 |
| Runde 100er (Placebo) | 70 % | ~500 | ~48 % | ~50 % | −0,5 bis −3 | <1,3 | – |
| **PDH** | 48 % | 334 | **45,2 %** | 49,3 % | **−4,1** | −1,5 | −4,3 |
| **PDL** | 38 % | 271 | **45,4 %** | 50,3 % | **−4,9** | −1,6 | +0,7 |
| Vortags-VAH | 58 % | 407 | 45,7 % | 50,9 % | −5,2 | −2,1 | −4,7 |

Bei R = 0,2 ATR: PDH −6,9 (z −2,4), London-Low −7,1 (z −3,1).

**Ehrliche Interpretation:**
- **Kein klassisches Level hält beim Erst-Touch robust besser als ein beliebig verschobenes Level.** Bei ~25 Tests ist ein |z| um 2 durch Zufall zu erwarten.
- **PDH, PDL und London-Low brechen tendenziell eher**, als dass sie halten. Das passt zu Liquiditäts- und Stop-Runs. Diese Levels taugen eher als **Ziel- und Breakout-Referenz** denn als Umkehrzone.
- **Confluence statischer Levels hilft nicht.** Halten nach Zahl weiterer Levels im Umkreis von 0,05 ATR: 0 → 50,0 %, 1 → 48,1 %, 2 → 48,9 %, ≥3 → 48,7 %.
- **Tops und Bottoms bilden sich nicht gehäuft an Levels.** 35,5 % aller RTH-Extreme liegen innerhalb von 0,03 ATR eines Levels, bei verschobenen Level-Sets sind es 32–36 %.
- **Leichter Magnet-Effekt bei Value-Levels.** Vortags-Close, -VWAP und -POC werden 3,5–4,6 Prozentpunkte häufiger erreicht als ein gespiegeltes Level in gleicher Distanz. Vorsicht: Die Aufwärtsdrift 2023–25 überzeichnet das leicht.
- **Höhere Zeitebenen** (unberührte Daily-Swing-Pivots, Vormonats-High/-Low) liefern zu wenige Touches (N = 36–107). Kein signifikanter Effekt.

**Weitere Muster ohne Edge:**
- **Sweep & Reclaim** an allen Levels: 48,7 % Trefferquote bei 1R:1R, Kontrolle 49,1 %.
- **Volumen-Klimax an neuen RTH-Extremen:** Ein neues Hoch oder Tief mit 3- bis 5-fachem Relativvolumen hält zu 6,8 %, mit normalem Volumen zu 3,6–4,2 %. Danach läuft der Preis im Median aber sogar weiter (0,21 statt 0,14 ATR).
- **Kurzfrist-Autokorrelation:** 1/5/15/30-min-Returns haben eine Lag-1-Autokorrelation von nahezu 0. Auf Minutenebene gibt es kein Momentum und keine Mean-Reversion.

## 6. Was tatsächlich Struktur hat

| Befund | Stärke | Stabil über die Jahre? |
|---|---|---|
| Extreme entstehen gehäuft 09:30–09:45 (und HOD 15:45–16:00) | stark (fast 2× Zufall) | ja, plausibler Mechanismus (Eröffnungsauktion) |
| IB (erste Stunde) enthält zu 78 % HOD oder LOD | stark | ja |
| ATR-Normierung: Range/ATR stabil, Volatility Clustering | stark | ja |
| **Extreme RTH-VWAP-Bänder (≥ 2,5 σ) reverten häufiger als Zufall** | moderat | **ja, in allen drei Jahren** |
| Gap-Fill-Wahrscheinlichkeit sinkt monoton mit Gap/ATR | stark, aber v. a. distanzbedingt | ja |
| Leichter Value-Magnet (PDC/VWAP/POC) | schwach | teils |

**VWAP-Bänder im Detail.** Gemessen: erster Touch nach 10:00, dann P(zurück zum VWAP, bevor 1 σ weitere Ausdehnung folgt). Die Zufallserwartung ist 1/(1+b):

| Band | Zufall | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| 1,0 σ | 0,50 | gesamt 0,456 (leichtes Momentum!) | | |
| 2,0 σ | 0,333 | 0,322 | 0,389 | 0,347 |
| 2,5 σ | 0,286 | 0,307 | 0,356 | 0,342 |
| 3,0 σ | 0,250 | 0,289 | 0,330 | 0,329 |

Ein statisches Level innerhalb von 0,1 ATR am 2σ-Band verbessert das kaum: 0,356 gegenüber 0,331.

**Range-Erschöpfung (ETH-Session):**
- P(Range erreicht 0,5 ATR) = 93 %, 1,0 ATR = 46 %, 1,5 ATR = 13 %, 2,0 ATR = 4 %.
- Nachdem 1 ATR erreicht ist, läuft das gerade gesetzte Extrem im Median noch 0,22 ATR weiter. In 54 % der Fälle sind es weniger als 0,25 ATR.
- Die Sättigung ist schwach. Für Wahrscheinlichkeitsbänder taugt das trotzdem, für harte Umkehrsignale nicht.

## 7. Was eignet sich für einen TradingView-Indikator?

**Geeignet** (live berechenbar, ohne Lookahead, robust gemessen):
- Session-Struktur: Asia, London, Overnight, RTH, Opening Range, IB
- Vortags-Referenzen: High, Low, Close, VWAP-Settle, POC, VAH, VAL
- ATR-basierte Range-Projektion
- RTH-VWAP mit σ-Bändern
- Zeitfenster-Gewichtung
- Gap-Statistik

**Nur eingeschränkt geeignet:**
- Volume Profile: in Pine nur approximiert möglich
- Volumen-Features beim **NAS100-CFD**: dort gibt es nur Tick-Volumen des Brokers. Volumenbasierte Module (VWAP, POC) sind dort weniger aussagekräftig. **Empfehlung: auf `NQ1!` oder `MNQ1!` laufen lassen.**

**Ungeeignet:**
- Runde Zahlen kalibrieren (Back-Adjustment)
- Orderflow, Delta (nicht in der CSV)
- Feste Punktwerte
- „Level hält“-Signale ohne Bestätigung, denn das widerlegen die Daten oben

---

## 8. Vorschlag für die Indikator-Logik

**Leitidee:** Nach dieser Analyse wäre ein Indikator unseriös, der bunte Confluence-Linien als „starke Levels“ verkauft. Statische Levels sind hier im Mittel nicht besser als Zufall. Der Indikator sollte stattdessen:
1. **Struktur** sauber darstellen (Sessions, Ranges, Referenzen),
2. **Kontext** quantifizieren (Range verbraucht, Zeitfenster, VWAP-Extension),
3. **Top- und Bottom-Kandidaten** nur aus nachweislich tragenden Faktoren bilden, mit Bestätigung,
4. seine **eigene Trefferquote live und vorwärts** mitzählen, damit der Nutzer ihn auf ungesehenen Daten prüft.

### Modul A – Session- und Range-Struktur (rein deskriptiv)
- Asia (18:00–02:00), London (02:00–08:30), NY-Pre (08:30–09:30): High, Low und Mitte als Boxen bzw. Linien
- Overnight High/Low (18:00–09:30)
- RTH Opening Range (wählbar 5/15/30 min) und IB (60 min) als Boxen
  - Extensions in OR-Vielfachen 0,5/1/1,5/2. Begründung: Median-Extension IB ≈ 0,55×, OR15 ≈ 1,1×
- Die Linien entstehen erst **nach Abschluss** der jeweiligen Session und werden nach rechts verlängert
- Kennzeichnung „getestet“ oder „gebrochen“ ab dem ersten Durchbruch

### Modul B – Referenz-Levels des Vortags und der Vorwoche
- PDH, PDL, PDC, Vortags-VWAP-Settle, Vortags-POC/VAH/VAL, PWH, PWL
- **Labels nach Datenlage:**
  - PDH/PDL/London-Low: „Liquidity / Breakout-Referenz“ (brechen eher)
  - PDC/VWAP/POC: „Value / Magnet“
- Optional Gap-Info am RTH-Open: Gap in ATR und historische Füllrate des Buckets als Hinweistext
  - |Gap| < 0,1 ATR: 92 %
  - 0,1–0,25 ATR: 70 %
  - 0,25–0,5 ATR: 48 %
  - 0,5–1 ATR: 30 %
  - > 1 ATR: 19 %

### Modul C – Dynamischer Kontext
- **RTH-VWAP mit volumengewichteten σ-Bändern** (1/2/2,5/3 σ), Formel identisch zur CSV-Spalte
- **ATR-Range-Projektion:** ATR(14) aus Daily-Daten des Vortags
  - Bänder: Session-Tief + {1,0 / 1,5 / 2,0}·ATR und Session-Hoch − {…}·ATR
  - Anzeige „Range verbraucht: x % ATR“
  - Historische Erreichbarkeit: 1 ATR 46 %, 1,5 ATR 13 %, 2 ATR 4 %
- **Zeitfenster-Hinweis:** Open-Auktion 09:30–09:45, Daten-Minuten 08:30 und 10:00, MOC 15:45–16:00

### Modul D – Top/Bottom-Kandidaten (Score, nur auf bestätigten Bars)

Score-Komponenten (alle zur Bar-Zeit bekannt). Die Gewichte sind bewusst grob und nicht auf die CSV optimiert:

| Faktor | Bedingung | Gewicht |
|---|---|---|
| VWAP-Extension | Preis ≥ 2,5 σ (Top) bzw. ≤ −2,5 σ (Bottom) | 2 (bei ≥ 3 σ: 3) |
| Range verbraucht | Session-Range ≥ 1,0 ATR und Extrem auf der Signalseite | 1 |
| Zeitfenster | Extrem in 09:30–10:00 oder 15:30–16:00 | 1 |
| Value-Confluence | Vortags-VAH/VAL/POC/VWAP innerhalb 0,1 ATR | 0,5 (Datenlage schwach) |
| Bestätigung (Pflicht) | bestätigte Bar schließt zurück innerhalb des 2σ-Bands **oder** Swing-Pivot (N links/rechts) bestätigt | Gate |

- **Signal = Gate erfüllt UND Score ≥ Schwelle** (Default 3). Erst dann erscheint ein Label.
- Das Label wird an der **Bestätigungs-Bar** gesetzt. Optional wird gestrichelt auf die Pivot-Bar zurückgezeigt, klar als „bestätigt N Bars später“ markiert.
- Alarme nur über `alertcondition` bzw. `alert()` mit `barstate.isconfirmed`.

### Modul E – Integrierte Live-Statistik (Anti-Overfitting)
- Jedes Signal wird **vorwärts** ausgewertet: Erreicht der Preis zuerst den VWAP (Ziel) oder 1 σ weiter (Invalidierung)?
- Trefferquote, N und Zufallserwartung 1/(1+b) erscheinen in einer Tabelle.
- So lässt sich der Indikator auf beliebigen Zeiträumen und Märkten (NQ, MNQ, ES) prüfen, statt der CSV zu vertrauen.

### Regeln gegen Lookahead und Repainting (technische Umsetzung)
- Alle Parameter in **ATR- bzw. σ-Einheiten**, keine festen Punkte. Wenige Parameter (≤ ~10), runde Defaults.
- Sessions per `time(timeframe.period, "0930-1600", "America/New_York")` selbst tracken. Intraday-Levels erst nach Session-Ende fixieren.
- Höhere Zeitebenen ausschließlich per `request.security(…, "D", ta.atr(14)[1], lookahead = barmerge.lookahead_on)`. Das ist das offizielle nicht-repaintende Muster: Offset [1] plus lookahead_on liefert nur abgeschlossene Werte.
- Vortags-POC/VAH/VAL: Volumen-Histogramm des laufenden RTH-Tages in einem Array mit Bin-Größe ≈ 0,02 ATR auf dem Chart-Timeframe akkumulieren. Gültig erst nach Session-Ende. Für Genauigkeit Chart ≤ 5 min empfehlen. Optional `request.security_lower_tf` mit 1 min, ebenfalls nur abgeschlossene Daten.
- Swing-Pivots mit `ta.pivothigh/low(N, N)`. Das Signal gilt erst N Bars später und wird auch so dokumentiert.
- Signale, Alarme und Statistik nur bei `barstate.isconfirmed`. Die Darstellung der laufenden Bar (z. B. VWAP) darf sich aktualisieren, Signale nicht.
- Pine-Limits beachten: `max_lines_count`, `max_boxes_count`, `max_labels_count` (je ≤ 500). Alte Objekte per Array-Queue löschen.

### Validierungsplan (vor dem Live-Einsatz)
1. Pine-Logik bar-für-bar gegen ein Python-Replikat auf der CSV prüfen (gleiche Levels und Signale).
2. Gewichte und Schwelle **nur auf 2023–24** festlegen und unverändert auf 2025 bewerten. Danach in TradingView **vorwärts** auf Daten nach dem 11.12.2025 prüfen. Die liegen außerhalb der CSV und sind echtes Out-of-Sample.
3. Gegenprobe auf ES/MES. Eine Logik, die nur auf NQ funktioniert, ist verdächtig.

---

**Fazit in drei Sätzen:**
- Die Daten sind sauber, aber abgeschnitten und back-adjusted. Analysen müssen deshalb in ATR-Einheiten und ohne absolute Preisniveaus laufen.
- Klassische Levels und deren Confluence zeigen beim Erst-Touch keinen robusten Halte-Vorteil. Belastbar sind dagegen Zeitstruktur (Open-Auktion, IB), Volatilitätsnormierung und extreme VWAP-σ-Ausdehnungen.
- Der vorgeschlagene Indikator stellt Struktur und Kontext dar und erzeugt Top/Bottom-Kandidaten nur aus diesen belegten Faktoren mit Bestätigung. Seine eigene Trefferquote prüft er vorwärts mit.
