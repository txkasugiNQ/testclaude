# NQ NY‑PM Intraday Strategy Research — Final Report

**Bottom line: no strategy was found that meets the hard requirement of ≥ +0.35R per trade on genuinely unseen data.**
The strongest candidate, **Trend‑Day Breakout (TDB)**, made +0.68R/trade on 2023‑01 → 2024‑12. It was pre‑registered and then tested once on the untouched 2025 holdout, where it made **−0.27R/trade**. The walk‑forward agrees: re‑optimising every quarter still gives −0.16R/trade in 2025. Under your own rule ("IS +0.60R / OOS +0.12R → FAIL"), TDB **fails**, and I'm not presenting it as successful.

**Second study (§9): the high‑win‑rate / low‑RR side was searched separately and deliberately.** The verdict is the same. No setup with a high win rate and small targets reaches +0.35R even in‑sample, and the best pre‑registered high‑win‑rate variant lost money on the 2025 holdout.

The rest of this report documents the full research process. It also gives the complete required metrics for the strongest candidate, its exact rules, the Pine implementation (for visual inspection and forward paper‑testing only), and what would be needed to continue credibly.

---

## 1. Data and integrity checks

| Item | Finding |
|---|---|
| File | `Dataset_NQ_1min_2022_2025 (1).csv`: 1,048,575 one‑minute bars, 2022‑12‑26 18:01 → 2025‑12‑11 20:52 (≈ 750 sessions). |
| Timestamp convention | **Bar CLOSE time, New York time.** RTH VWAP (`Vwap_RTH`) starts at 09:31 on all 764 sessions, including all 6 DST changes, so the stamps are true ET with correct DST handling. |
| Session structure | Globex 18:01 → 17:00, 1,380 bars/day. Holiday half‑days are shorter. One data gap (2023‑04‑05). |
| Prices | Continuous contract, **back‑adjusted** (Dec‑2022 prices ≈ 13,700 vs ~10,900 actual). Fine for intraday point distances; see §8 for the TradingView implication. |
| Days used | 732 sessions with a complete 12:00–16:00 PM. |
| Data split (fixed **before** any testing) | **IS** 2023‑01 → 2024‑06 · **VAL** 2024‑07 → 2024‑12 · **OOS holdout** 2025‑01 → 2025‑12. |

## 2. Research process (chart → observation → hypothesis → rule → backtest → validation)

**Chart study.** I generated and inspected about 30 random IS NY‑PM sessions on 2m, 3m and 1m charts. The charts showed the AM range, overnight high/low, prior day H/L/C, RTH open and VWAP (`research/chart.py`). Recurring observations:
- **Trend days** continue in the PM after a midday pause, and new session extremes keep extending (e.g. 2023‑06‑15, 2024‑03‑19, 2023‑04‑27).
- **Range days** produce repeated failed probes of the AM extremes (2023‑05‑11, 2023‑09‑07).
- **VWAP** acts as a midday pivot, both holding pullbacks and being rejected.
- **Late V‑reversals** after long extensions (2023‑09‑27).

**Engine.** All results come from a conservative simulator:
- Signals use completed bars only.
- Stop entries fill at max(stop, open).
- Limit entries fill only when price **trades through** by a tick, at the limit price.
- In the fill bar, a stop touch counts as a loss, and a target counts only on a close beyond it.
- When SL and TP fall in the same bar, SL wins.
- Stop changes take effect from the next bar.

A random‑entry control returns −0.01…−0.04R, which is the cost of this worst‑case bias, so no phantom edge exists. The **backtest of record** is a bar‑by‑bar state machine (`research/sm2.py`) that builds 1/2/3‑minute signal bars from 1‑minute data and executes on 1‑minute bars. That is exactly the logic of the Pine script.

**Hypotheses tested.** All of these were evaluated on IS/VAL with OOS masked:

| # | Hypothesis | Result | Why rejected |
|---|---|---|---|
| 1 | Break of AM high/low → continuation | ≈0R; tight stops −0.3…−0.5R | Breaks oscillate ±10–15 pts around the level |
| 2 | Fade first PM touch of AM extremes | ≈0R | The same noise kills fades |
| 3 | First VWAP touch after an extended leg | IS −0.1R / VAL +0.2R | Sign flips between periods |
| 4 | Sweep & reclaim of 8 key levels (ON/PD/AM/RTH H/L) | −0.03…−0.12R | No edge on either 2m or 3m |
| 5 | Break → retest of key levels | +0.06…+0.10R (vectorized engine, an upper bound) | Too small; long‑side only |
| 6 | 25 continuous state features (VWAP distance/slope, momentum, compression, range position, volume, round numbers…) | every decile 50% ± 3% | No conditional drift |
| 7 | Gradient‑boosting on all features (upper bound on predictability) | AUC IS 0.73–0.79 → **VAL 0.49–0.51** | Pure overfit; no out‑of‑sample information |
| 8 | Extreme tails (top 0.5–3%) | IS continuation 60–70% → VAL reversal 26–47% | Regime‑dependent sign |
| 9 | Variance ratio / intraday momentum / half‑hour periodicity | VR ≈ 1.0 at 2–15 min; correlations ≈ 0 | Near random walk |
| 10 | Predict trend days from AM structure | correlations ≈ 0 | — |
| 11 | Regime switching (trailing 5–40‑day continuation rate) | corr ≈ 0 with next day | Regime not forecastable |
| 12 | Impulse → flag → breakout | IS +0.25…+0.46R / VAL negative | Regime‑dependent |
| 13 | Trend‑aligned dip buying / rally selling | ≈0R (win rate equals the random‑walk value) | No edge |
| 14 | AM trend → midday retracement → PM resumption | IS ≈0R | Wide structural stops (27–45 pts) |
| 15 | Level age, time stops, last‑hour (15:00–15:45) continuation, ETH VWAP, prior‑week and prior‑PM levels | ≤ +0.1R, inconsistent | — |
| 16 | Battery: 22 levels × 5 events × stops × 6 exits × 4 windows (7,392 configs) | Top cluster = long‑only breakouts | Long breakouts positive, short mirror negative → bull drift, not behaviour |
| 17 | **Trend‑aligned breakout of the session extreme in early PM** (daily trend filter) | +0.22…+0.36R in both IS and VAL | Real but below 0.35R |
| 18 | **(17) + trend‑day filter (price ≥ 0.4·ADR from RTH open)** | IS +0.72R / VAL +0.57R on a broad plateau | → pre‑registered as **TDB v1.0** |

**Bugs found and fixed during the research.** Each one inflated results before it was caught:
- **Marketable‑limit R inflation.** Limit orders filled at a better open while the stop stayed anchored, shrinking R. Fixed: limits fill only at the limit price, and marketable limits are rejected.
- **Overlapping‑order selection bias in the vectorized engine.** A later‑filling deep order could replace an earlier‑filling losing one. This turned +0.21R into +0.58R for the pullback variant. Fixed by making the bar‑by‑bar state machine the only accepted backtest.
- **NaN gap in the 50‑day trend filter** caused by partial sessions. Fixed.

**Discipline notes (full disclosure).**
- An early exploratory helper printed OOS columns alongside IS/VAL for hypotheses 1–3, all of which were rejected on IS/VAL anyway.
- One coarse daily‑correlation table, one MFE/MAE `describe()` for a rejected idea, and a table of daily‑trend labels by quarter also included 2025.
- None of this influenced the selection. OOS was masked from then on until the single pre‑registered evaluation.

## 3. Strongest candidate — exact rules (TDB v1.0, `research/PREREG.json`)

**Concept.** On a *trend day*, the daily trend is up (or down) and by early afternoon NQ is already far from its RTH open in that direction. A new session extreme set in early PM then tends to keep running, as trend‑following and stop flows extend the move. On non‑trend days the same breakouts are range fake‑outs, which is why the filter matters.

| Element | Rule |
|---|---|
| Chart / execution | 1‑minute bars. Signals on **2‑minute** bars aggregated from 1m (buckets aligned to the 18:00 ET Globex open). |
| Session | Setups only on 2m bars **closing 12:00–14:00 ET**. Entries can fill 12:00–14:02 ET. Flat at the **16:00 ET** bar close. No entries outside NY PM. |
| Daily trend | Long only if the prior RTH close (16:00) > SMA50 of RTH closes; short only if below. Prior sessions only. |
| Trend‑day filter | At the signal bar close: (close − RTH open at 09:30) × side ≥ **0.4 × ADR10**. ADR10 is the mean RTH (09:30–16:00) range of the prior 10 full sessions. |
| Entry | At each qualifying 2m close, place a **buy stop 1 tick above the running RTH session high** (sell stop 1 tick below the low), valid for the next 2m bar only and re‑placed every bar. Fill at max(stop, open). |
| Stop loss | Entry‑order price − **1.25 × ATR14(2m)** (Wilder). **Average 15.5 pts** in IS+VAL (median 14.0). 2025 average 25.3 pts (median 19.8). |
| Take profit | **Fixed 4R** from the actual fill price. |
| Other | Max 2 trades per day, one position at a time. |

**Timeframe choice.** On 1m, the natural 1×ATR stop (~8 pts) is too tight and fails. 2m and 3m are equivalent. What matters is a stop of about 14–17 pts: 1.25×ATR on 2m, 1.0×ATR on 3m, or 1.5×ATR on 1m. **Sub‑window:** edge decays monotonically through the afternoon, positive from 12:00–14:00 and negative for 14:00–16:00 entries.

## 4. Strongest candidate — full metrics

Before costs (the +0.35R threshold is measured here):

| Metric | IS 2023‑01→2024‑06 | VAL 2024‑07→12 | **OOS 2025 (holdout)** | IS+VAL |
|---|---|---|---|---|
| Total trades | 115 | 39 | **87** | 154 |
| Trades / day | 0.31 | 0.32 | 0.37 | 0.31 |
| Win rate | 35.7% | 33.3% | **14.9%** | 35.1% |
| Avg winning R | 3.81 | 3.71 | 3.80 | 3.79 |
| Avg losing R | 1.00 | 1.00 | 0.99 | 1.00 |
| **Expectancy (R/trade)** | **+0.715** | **+0.571** | **−0.272** | +0.678 |
| Profit factor | 2.11 | 1.86 | **0.68** | 2.05 |
| Max drawdown (R) | 11.0 | 8.0 | **31.6** | 11.0 |
| Longest losing streak | 11 | 8 | **19** | 11 |
| Average losing streak | 3.1 | 2.4 | 5.7 | 2.9 |
| Avg stop (pts) | 14.0 | 20.0 | 25.3 | 15.5 |
| Avg trade duration | 45 min | 44 min | 42 min | 45 min |
| Avg MFE / MAE (R, until exit) | 1.99 / 0.68 | 1.88 / 0.70 | 1.38 / 0.78 | 1.97 / 0.69 |
| t‑stat of mean R | 3.2 | 1.6 | −1.5 | 3.6 |

Unconstrained path probability P(price reaches +kR before −1R), for the same entries:

| k | 0.5R | 1R | 2R | 3R | 4R |
|---|---|---|---|---|---|
| IS | 0.68 | 0.59 | 0.46 | 0.36 | 0.31 |
| VAL | 0.68 | 0.56 | 0.38 | 0.38 | 0.32 |
| **OOS 2025** | 0.69 | **0.51** | **0.29** | **0.21** | **0.15** |

In 2023–24 the 4R/−1R odds were about 31% against 20% for a random walk, which is genuine momentum. In 2025 they fell to 15%, so **the momentum vanished**.

**After estimated costs.** The model assumes 0.5 pt slippage on the stop entry, 0.5 pt on stop‑loss exits, 0 on limit TPs, 0.25 pt on time exits, and 0.25 pt commission per round trip. That gives about 1.0–1.25 pts per trade.

| Metric | IS | VAL | OOS |
|---|---|---|---|
| Expectancy | +0.632R | +0.510R | −0.335R |
| Profit factor | 1.90 | 1.72 | 0.63 |

**Exit mechanisms compared** (expectancy R/trade; full table in `results/tdb_exit_comparison.csv`):

| Exit | IS | VAL | OOS | Win rate (IS) |
|---|---|---|---|---|
| Fixed TP 2R | +0.36 | +0.33 | −0.15 | 45% |
| Fixed TP 3R | +0.39 | +0.60 | −0.16 | 35% |
| **Fixed TP 4R (selected)** | **+0.72** | **+0.57** | **−0.27** | 36% |
| Trailing: start 2R, trail 1R | +0.39 | +0.49 | −0.18 | 46% |
| Trailing: start 3R, trail 1.5R | +0.74 | +0.53 | −0.28 | 37% |
| Hybrid: 50% at 2R + 50% at 4R | +0.59 | +0.40 | −0.23 | 49% |
| Hybrid: 50% at 1.5R → BE → trail | +0.39 | +0.45 | −0.19 | 47% |
| Hold to 16:00 | +1.01 | +0.42 | −0.40 | 28% |

Every exit fails on 2025, which confirms that the *entry* edge disappeared rather than the exit being mis‑chosen. The fixed 4R target was chosen in advance because it had the smallest IS‑vs‑VAL gap and was ≥0.35R in 100% of neighbouring parameter cells.

**Walk‑forward.** Anchored, re‑optimised each quarter over trend‑day threshold {0.3, 0.4, 0.5} × stop {1.0, 1.25, 1.5} ATR × exit {TP3, TP4, trail 3/1.5}, using only prior data:

| Period | Trades | Expectancy (R/trade) |
|---|---|---|
| 2023 Q4 | 19 | +0.83 |
| 2024 | 69 | +0.73 |
| **2025** | 67 | **−0.16** |
| All test quarters | 155 | +0.36 (carried entirely by 2023–24) |

**Regimes.**
- **By year:** 2023 +0.66R (70 trades), 2024 +0.70R (84), 2025 −0.27R (87).
- **By side:** longs IS +0.85 / VAL +0.71 / OOS −0.46; shorts IS +0.14 / VAL +0.25 / OOS +0.20, with small samples.
- **By volatility** (ADR10 as % of price, terciles fixed on IS): 2025 is negative in **every** tercile (−0.24…−0.40R), so the failure is not a volatility artifact.
- **Shape of the decay:** the rolling 30‑trade expectancy slid from about +0.9R in mid‑2024 to +0.25R by December 2024, then turned negative from May 2025. That is a gradual decay, consistent with a fading or exploited effect.
- Monthly results: `results/tdb_by_month.csv`.

## 5. Why there is no robust ≥ +0.35R strategy in this data

1. **The tape is close to a random walk at the tested scale.** At 1–3 minutes, variance ratios are about 1.0. No single feature moves symmetric first‑passage odds beyond 50% ± 3%. A flexible ML model has no out‑of‑sample skill.
2. **+0.35R needs strong drift.** With a 1:1 payoff it means about 67.5% win rate, or the equivalent at other payoffs. The best robust two‑sided intraday effects measured here are about +0.05 to +0.15R.
3. **The only large effect was regime‑bound.** Trend‑day momentum was strong and consistent in 2023 to mid‑2024 and decayed through 2025.
4. **Multiple‑testing control.** In a final battery requiring ≥0.35R separately in each of 2023, 2024 and 2025, **0 of 5,455 real configs passed**. The randomised‑signal control passed at a comparable rate (and, unfiltered, real and random were identical: 0 configs ≥ +0.15R). Continuing to mine the same three years would eventually produce a chance "winner", which is why I stopped rather than present one.

## 6. What would be needed to continue credibly

- **More history.** NQ 1m data from about 2010–2022 gives multiple bull, bear and chop regimes to test regime‑robustness and a new untouched holdout.
- **Forward testing.** Run the Pine script on 2026 data, which is genuinely unseen. This is the only remaining clean OOS for the TDB family.
- **Information outside NQ price/volume.** Examples are ES/RTY, rates, VIX/VVIX, dealer gamma/0DTE positioning (relevant because PM momentum appears to have been damped in 2025), and order‑book or tick data for precise fills on tight stops.
- **Treat any new candidate the same way.** Pre‑register it, then validate on fresh data or a year‑by‑year standard, not on 2025 again.

## 7. Files

| Path | Content |
|---|---|
| `REPORT.md` | This report. |
| `pine/NQ_PM_TrendDayBreakout.pine` | Pine v6 implementation of TDB (research build, clearly flagged as **failed OOS**). |
| `results/tdb_trades_python_reference.csv` | Every TDB trade from the reference engine: signal/entry/exit times (bar‑close, ET), entry/SL/TP/exit prices, R, MFE/MAE. Use it to verify the Pine script trade by trade. |
| `results/*.csv` | Metrics before and after costs, exit comparison, walk‑forward quarters, by year/month/side/volatility. |
| `results/charts/*.png` | Annotated example trades showing setup context, entry, SL, TP, markers and exit. |
| `research/` | All research code. Run `python3 prepare_data.py` first, then any script from inside `research/`. Library: `core.py` (data/day levels), `bars.py` (session‑aligned 1/2/3m bars), `sm2.py` + `smlab2.py` (**state machine of record**), `validate.py` (metrics/costs), `lab.py` + `engine.py` (vectorized exploration engine; single‑bar orders only, see the overlap note in §2). The hypothesis scripts are listed in §2. `PREREG.json` is the frozen spec evaluated once on 2025. |

## 8. Pine Script notes

- **Run it on a 1‑minute NQ chart.** It builds the 2m signal bars internally and evaluates fills and exits on 1m bars with the same conservative rules as the Python engine. The daily trend and ADR come from RTH‑exact 30‑minute data, using prior sessions only, so they are non‑repainting. There are no pivots or future data.
- **Visuals:**
  - setup/preparation: setup window, RTH open, trend‑day threshold line, the running session high/low used as the trigger, and shading when a setup is armed;
  - orders and trades: the pending entry stop and its stop‑loss, BUY/SELL labels with entry/SL/TP, entry/SL/TP lines, and exit labels with the R result;
  - a statistics table computed with the research rules.
- **TradingView Strategy Tester caveat.** TradingView's broker emulator also receives orders. In rare bars where SL and TP (or the entry and SL) fall inside the same 1‑minute bar, it may resolve the order of events differently from the research's worst‑case assumption. The on‑chart table uses the research rules exactly. Enable *Bar Magnifier* if available.
- **Data differences vs this dataset.** Use NQ1! with back‑adjustment enabled to match the price levels. Roll dates may differ slightly, which can change the 50‑day trend sign around rolls. Half‑day sessions are excluded in the research but not automatically in Pine.
- **Not compiled here.** No TradingView compiler was available in this environment, so the script has not been compiled or run. Verify parity against `results/tdb_trades_python_reference.csv` on a few dates before relying on it.

## 9. Second study — high‑win‑rate / low‑RR search

**Question:** is there a high‑win‑rate, low‑RR (or asymmetric) NQ NY‑PM setup with expectancy ≥ +0.35R/trade that survives OOS/WF?
**Answer: no.** The details follow.

### 9.1 The arithmetic that frames the search
With losses at −1R, the win rate needed for +0.35R, compared with the win rate a pure random walk gives for free:

| Avg win | Win rate needed for +0.35R | Random‑walk win rate (no edge) | Edge needed over random |
|---|---|---|---|
| 0.25R | impossible (max +0.25R) | 80% | — |
| 0.33R | impossible (max +0.33R) | 75% | — |
| 0.50R | 90% | 67% | +23 pts |
| 0.67R | 81% | 60% | +21 pts |
| 0.75R | 77% | 57% | +20 pts |
| 1.00R | 67.5% | 50% | +17.5 pts |

A high win rate with small targets is therefore **automatic and worthless by itself**. What matters is the excess over the random‑walk win rate. The only other route is cutting losers below −1R with time or level exits, so that expectancy rises at a lower win rate. Both routes were tested.

### 9.2 What was tested (discovery on IS, selection on VAL, 2025 masked)
- **Edge surface** (`research/hw_lab.py`, `hw_families.py`). For every event, the 1m path was walked forward for every combination of target {0.25, 0.33, 0.5, 0.67, 0.75, 1.0, 1.5}R × stop {0.75, 1, 1.5, 2} ATR or **structural** (beyond the extreme of the move or rejection bar) × hold {5, 10, 20, 40 min, to 16:00}. This was done on **1m, 2m and 3m** signal bars, about **25,000 cells**. A random‑entry calibration reproduces the random‑walk win rate exactly, with expectancy about 0 to −0.01R.
- **Families:**
  1. **impulse exhaustion fade** (3/5/10‑bar moves of ≥2/3/4 ATR), with and without a reversal‑candle confirmation;
  2. **consecutive‑bar exhaustion** (4–6 bars);
  3. **VWAP σ‑band fades** (2/2.5/3σ, on touch or rejection);
  4. **range‑extension fades** beyond AM/IB/ON/PD highs and lows by 0.5/1/2 ATR;
  5. **failed breakouts** of the session extreme (back inside within 1–3 bars);
  6. **sweep & reclaim** of 8 key levels;
  7. **trend‑day pullbacks** with small targets;
  8. **range‑day new‑extreme fades** and all‑day new‑extreme fades;
  9. **single‑bar spike** fade and follow;
  10. on 1m, the same families as **microstructure** reversion.
- **Level‑target tests** (`hw_magnet.py`):
  - **magnets:** price near an untouched VWAP / PDC / RTH open / 12:00 price / round 100 / AM POC / day mid, traded *toward* it with target = touch;
  - **retests:** price beyond a broken level, traded back to it with target = the level;
  - **VWAP‑band fades** with the target at the 2σ/1.5σ/1σ band or at VWAP itself.
- **Deep‑dive** of the best family (`hw_vwb.py`, `hw_late.py`, `hw_late2.py`): MAE‑based stop sizing, every exit type, band level, time windows.

### 9.3 Results
- **No cell reached +0.25R in both IS and VAL** on any timeframe.
- **Among cells with ≥70% win rate in both periods, the best expectancy was +0.075R** (2m), +0.06R (1m) and +0.03R (3m).
- Magnets: median edge over the random walk −0.1 / −0.8 percentage points (IS/VAL); best +3.5 pts, worth about +0.05R. Retests: median −1.3 / +0.7 pts; best +3 pts.
- **The edge shrinks as the target shrinks.** For the best family (VWAP 2.5σ rejection, structural stop, IS), the excess win rate over random is:

  | Target | Excess over random |
  |---|---|
  | 0.25R | −2.6 pts |
  | 0.5R | +1.8 pts |
  | 1R | +7.9 pts |
  | 1.5R | +4.4 pts |

  Whatever reversion exists is a slow drift that shows only over larger excursions. **No "small, fast, highly repeatable" move exists that small targets could harvest.**
- **MAE / stop sizing.** For VWAP‑band fades, eventual winners have a median adverse excursion of 0.46 ATR before +0.5 ATR, but a p90 of 2.2 ATR and a p95 of 3.9 ATR. There is no sharp invalidation point: tighter ATR stops (0.5–0.75 ATR) cut winners as often as losers, and wider ones (2–3 ATR) dilute R. The structural stop (rejection‑bar extreme ± 1 tick, about 13–17 pts ≈ 1 ATR) was best.
- **Exits for the best family** (structural stop, 12:00–16:00):

  | Exit | IS | VAL | Win rate (IS / VAL) |
  |---|---|---|---|
  | Fixed TP 0.25R | −0.01R | −0.05R | 79% / 76% |
  | Fixed TP 0.5R | +0.07R | +0.11R | 71% / 74% |
  | Fixed TP 1R | +0.16R | +0.37R | 57% / 68% |
  | Partial 50% at 0.5R + breakeven runner | −0.06R | +0.39R | — |
  | Runner to VWAP | +0.01R | +0.45R | — |
  | Trail after +0.5R | +0.08 to +0.10R | — | — |
  | Exit at VWAP / 1σ band | −0.02 to +0.02R | +0.86R | — |
  | Time exits (6–20 min) | ≤ +0.18R | — | — |

- **Late‑session lead.** Entries 14:00–16:00 looked better (1R target: IS +0.24R / VAL +0.46R, 64% win rate), but only at exactly 2.5σ. In IS, 2.45σ gives +0.17R and 2.55σ +0.05R, so that peak is noise; the neighbourhood is about +0.1R.

### 9.4 Pre‑registered high‑win‑rate variants (`research/PREREG_HW.json`), 2025 evaluated once
**VWR: late‑session (14:00–15:56) VWAP 2.5σ rejection fade.** Market entry on the next 1m bar, structural stop (average 16.9 pts), max 3 trades/day. Compared side by side with the high‑RR candidates:

| Strategy | Expectancy 2023 / 2024 / **2025** | Win rate 2023 / 2024 / 2025 | 3‑yr expectancy | 3‑yr PF | Max DD | Max losing streak | Avg stop |
|---|---|---|---|---|---|---|---|
| VWR‑0.5R (high win rate) | +0.08 / +0.14 / **−0.18** | 72% / 76% / 54% | +0.04R | 1.12 | 6.4R | 4 | 16.9 pts |
| VWR‑1R (1:1) | +0.14 / +0.42 / **−0.14** | 56% / 71% / 42% | +0.18R | 1.43 | 7.9R | 7 | 16.9 pts |
| TDB v1.0 (high RR, §3) | +0.66 / +0.70 / **−0.27** | 34% / 36% / 15% | +0.34R | 1.47 | 31.6R | 19 | 19.1 pts |
| TDC* (trend‑day continuation, market entry, 3m, stop 1.5 ATR, trail 2R/1R) | +0.27 / +0.64 / +0.20 | 44% / 48% / 46% | +0.37R | 1.69 | 16.2R | 8 | 31.2 pts |

\*TDC was chosen by looking at all three years (it answers "what is best over 2023–2025 combined"), so its 2025 figure is **in‑sample, not OOS**. It is also positive in every year only with a wide ~31‑pt stop, and 2025 alone is below +0.35R.

- **Walk‑forward for the VWR family** (quarterly re‑optimisation over band 2.4/2.5/2.6σ × start 13:30/14:00/14:30 × target 0.5/0.75/1R): 2023 −0.31R, 2024 +0.25R, 2025 −0.21R; all test quarters **−0.005R**, 51% win rate.
- **Tail risk** (`results/hw_tailrisk_*.csv`). In this 1m data, every loss in every strategy is exactly −1R: the largest loss and the p95/p99 losses all equal 1R, with no gap through a stop. So the low‑RR tail risk here is not single catastrophic losses but **clustering**. For VWR‑0.5R the 2025 equity stayed underwater for the whole year (26 of 26 trades). Over three years, dropping the 5 worst VWR‑0.5R trades lifts expectancy only from +0.04R to +0.09R, and dropping the 5 best turns it to +0.01R. The profitability is neither stable nor large. Real fills on fast news minutes (14:00 FOMC) would add losses beyond −1R that 1m bars cannot show.
- **Data limit.** With stops of 0.5 ATR (about 7 pts) and targets of 0.25–0.33R (2–3 pts), the target and stop often fall in the same 1m bar. The worst‑case rule then costs about 0.1R, so those cells cannot be judged honestly without tick data. Larger, testable versions show no edge.

### 9.5 Conclusion of the second study
Searching both sides of the distribution gives the same answer. On both sides, NQ NY‑PM win rates sit at the random‑walk value plus a few points:
- **High‑win‑rate / low‑RR:** the best robust result is +0.04 to +0.08R at a 70–76% win rate, and it failed in 2025.
- **Low‑win‑rate / high‑RR:** TDB reached +0.66–0.70R in 2023–24, then failed in 2025.

The edge that does exist is a slow, regime‑dependent drift. It needs larger targets to show at all, and it reversed in 2025 for both momentum (breakouts) and reversion (VWAP‑band fades). **No high‑win‑rate setup with ≥ +0.35R expectancy survived OOS/WF, and none reached it even in‑sample.**
