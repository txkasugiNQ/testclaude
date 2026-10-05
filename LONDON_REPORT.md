# NQ London Session — Simple Price‑Behavior Research

**Outcome: B.** The tested London behaviors do **not** provide a robust edge of ≥ +0.35R/trade.

Simple London price action does contain two real, coherent behaviors:
- **momentum in the first ~16 minutes after 08:00**, then
- **reversion of the early move back toward the 08:00 open**.

On 2023–2024 each is worth about +0.15–0.30R. Both were pre‑registered and evaluated once on the untouched 2025 holdout, and **both fell to about 0R** there. Walk‑forward agrees.

No Pine Script was produced, because the condition "if you find something promising" was not met. Files are listed in §8.

---

## 1. Session definition and timezone handling

- **Timestamps.** Dataset stamps are bar‑close times in America/New_York. Every bar was converted to **Europe/London** with full DST handling (`research/ldn_prep.py`).
- **London 08:00 in ET.** It is 03:00 ET on most days, but **04:00 ET on 54 trading days** in the US/UK DST‑mismatch weeks (about 3 weeks in March and 1 week around late October). All of these were detected and handled.
- **Choosing the session from the data** (median 1m volume/range by London time, discovery period only):

  | London time | What happens |
  |---|---|
  | 07:00 | Frankfurt/Eurex open; volume ×2 |
  | **08:00** | **London open; biggest jump** (median 1m range 3 → 5 pts) |
  | 08:30–11:30 | Activity decays |
  | 12:00–13:30 | US pre‑market rise |
  | 13:30 / 14:30 | US data / NY open |

- **Study session: 08:00–12:00 London.** Entries 08:00–11:56, flat at 12:00. This always ends before US data (12:30 London in mismatch weeks, 13:30 otherwise), so the session is purely London‑driven.
- **Pre‑session context** (objectively known before 08:00): the Asia range (00:00–07:00 London), the Frankfurt hour (07:00–08:00), the overnight range, prior‑day RTH high/low/close, and the Globex open.
- **Splits, fixed before testing:** IS 2023‑01→2024‑06, VAL 2024‑07→12, **holdout 2025, never evaluated until the single pre‑registered run.**

## 2. Look → observe

I inspected 20 random London sessions (2m, London time) with all levels drawn (`research/ldn_chart.py`; examples in `results/london_charts/`).

**The striking visual pattern was the "first push fails":**
- In most sessions, the move in the first 5–60 minutes, often a sweep of the Asia or Frankfurt high/low, made one extreme of the London session and was then reversed. Examples: 2023‑02‑10, 2023‑04‑03, 2024‑01‑23.
- Some days showed the opposite: the open impulse consolidated and continued (2023‑08‑21).
- Some stayed inside the opening range all session.

## 3. Hypothesize → test the simple statistics first

**Is "the early extreme" real?** Raw counts look supportive: the London high is set in the first 60 minutes 41–44% of the time, against 33% for a uniform random walk.

But volatility is front‑loaded. A **volatility‑preserving null** shuffles each day's 1m bars within their own 30‑minute bucket (`research/ldn_null.py`, 200 shuffles). Against it, the real frequencies sit **inside the null's 95% band**:

| Statistic | Real | Null mean | Null 95% band |
|---|---|---|---|
| High in first 30 min | 28.8% | 27.8% | 25.8–30.2% |
| High in first 60 min | 41.9% | 40.3% | 37.9–42.3% |
| Low in first 60 min | 43.3% | 43.6% | 41.5–45.6% |

**The "Judas swing" look is mostly an illusion created by high early volatility.** The genuine signal is mild: the first‑30‑minute move is negatively correlated with the rest of the session (r ≈ −0.11, about 2.5 standard errors from zero).

## 4. Simple rule tests (both sides: high‑RR and high‑win‑rate)

All tests use the conservative 1m engine (worst‑case intrabar rules) with signals on 1m, 2m or 3m bars. They were run on IS/VAL only, with targets 0.33R–3R plus hold to 12:00. A random‑entry calibration reproduces the random‑walk win rates with about 0R expectancy. There were 679 cells in the first battery (`research/ldn_simple.py`) and about 300 more in follow‑ups (`ldn_round2.py`, `ldn_fade.py`, `ldn_mr.py`, `ldn_open.py`).

| Behavior (simple rules) | Best worst‑period expectancy | Finding |
|---|---|---|
| **Break of Asia / Frankfurt / prior‑day / overnight high‑low → continuation** | −0.19 to −0.26R (stop orders); ≈0 to −0.30R with close confirmation | **London breakouts of pre‑session levels fail** |
| Opening‑range (15/30/60 min) breakout | ≤ +0.08R | No edge |
| Opening‑range failure fade | ≤ +0.04R | No edge |
| Sweep‑and‑reclaim fade of Asia / overnight / prior‑day levels | +0.14 to +0.24R (hold, 1m, ~5–8 pt stops, 15–25% win rate) | Tail‑driven, tiny stops, IS‑heavy |
| "Return to the range" after a sweep (target = Asia mid / far side) | IS +0.05 to +0.17R, VAL ≈ 0 to +0.10R | Weak |
| Fade / follow the Frankfurt‑hour move at 08:00 | ≈ 0R | No edge |
| **Follow the London opening impulse (decided 08:10–08:16)** | IS +0.13 to +0.22R, VAL +0.11 to +0.45R | **Consistent but small; gone by 08:20** |
| Fade the first 6–16 minutes' impulse | mostly −0.1 to −0.4R | The mirror of the above |
| **Fade the early move back toward the 08:00 open (09:00–09:30, ≥ 2–4 ATR)** | IS +0.04 to +0.31R, VAL +0.2 to +0.95R | **Real but unstable by quarter (−0.46 to +1.06R)** |
| Simple mean reversion: k ATR from the London open | ≤ +0.22R | Same family as above |
| Magnets (Globex open, prior close), target = touch | ≈ 0R (edge ±2 pts over random) | No edge |
| Compression‑box breakout | ≤ +0.07R | No edge |
| **High‑win‑rate cells (≥ 65% wins in both IS and VAL)** | best +0.085R | Win rates are the random‑walk baseline plus a few points |

**What was learned:** London on NQ is mean‑reverting at the hour scale. Breakouts of pre‑London levels lose, and the early move tends to give back. Only the **very first 10–16 minutes after 08:00** show momentum. A high win rate is obtainable (75% with a 0.5R target following the opening impulse, which is +8 pts over random), but it is worth only about +0.1R. The user's "small but very repeatable move" exists, but it is too small.

## 5. Pre‑registered candidates (`research/PREREG_LDN.json`), 2025 evaluated once

**Rules.** Both use 2m signal bars and 1m execution, with market entry on the next 1m bar and max 1 trade/day.
- **LOM, London Open Momentum.** At the 2m bar closing 08:16 London, if |close − 08:00 open| ≥ 2 × ATR14(2m), go with the move. Stop 1.5 × ATR (avg 9.4 pts in IS, 16.7 in 2025). Targets 0.5R / 1R / 1.5R.
- **LER, London Early‑move Reversion.** At the 2m bar closing 09:30 London, if |close − 08:00 open| ≥ 3 × ATR, fade the move. Stop beyond the running London extreme + 1 tick (avg 12.2 pts IS, 18.8 in 2025). Target = the 08:00 open. Flat at 12:00.

| Strategy | IS | VAL | **2025 holdout** | Win rate IS / VAL / 2025 | 2025 max DD | 2025 max losing streak |
|---|---|---|---|---|---|---|
| LOM, 0.5R target | +0.13R | +0.11R | **−0.04R** | 76% / 74% / 65% | 5.3R | 5 |
| LOM, 1R target | +0.17R | +0.28R | **−0.03R** | 59% / 64% / 49% | 11.0R | 7 |
| LOM, 1.5R target | +0.22R | +0.45R | **−0.20R** | 49% / 58% / 32% | 19.9R | 9 |
| LER, target = 08:00 open | +0.31R | +0.55R | **+0.00R** | 30% / 39% / 28% | 22.4R | 9 |

**Walk‑forward** (quarterly, re‑optimised on all prior data):

| Family | Grid | 2023 Q4 | 2024 | 2025 | All periods |
|---|---|---|---|---|---|
| LOM | decision 08:10/08:16 × threshold 1–3 ATR × stop 1–1.5 ATR × target 0.5–1.5R | +0.02R | +0.25R | **−0.15R** | +0.06R |
| LER | decision 09:00/09:30/10:00 × threshold 2–4 ATR | +0.95R | +0.42R | **+0.12R** | +0.34R, 32% win rate |

LER's all‑period +0.34R comes mostly from two outlier quarters (Q4 2023 +0.95R, Q3 2024 +1.16R). It is the strongest London result, but it is not ≥ +0.35R, its 2025 value is only +0.12R, and it is a low‑win‑rate strategy.

**Tail risk.** As in the NY work, every loss is exactly −1R; this 1m data shows no gaps through stops. The 2025 risk is clustering: LOM‑0.5R spent 73 of 96 trades underwater. Removing the 5 best LER trades in 2025 turns it from +0.00R to −0.30R, so whatever profit remains depends on a few trades.

## 6. Answer

**Outcome B.** Simple London price behavior on NQ does **not** produce a surprisingly strong edge:
- The visually obvious "first push fails / Judas swing" pattern is largely what a random walk with front‑loaded volatility looks like.
- The two real effects found are a brief opening momentum (~16 min) and a reversion of the early move toward the 08:00 open. Each is worth about +0.15–0.30R in 2023–24, and both vanished in 2025.
- On the high‑win‑rate side, 74–76% win rates are achievable with small targets, but the edge over random is only a few points, about +0.1R.
- **No London setup reached ≥ +0.35R in both IS and VAL, and none survived the 2025 holdout.**

## 7. Pine Script

None was produced: no candidate met the "promising" bar. If you want to forward‑test LOM or LER on live 2026 data, the only clean out‑of‑sample left, both are simple enough that a Pine version would take about 60 lines. It would use the same London‑time conversion as the research: `hour(time, "Europe/London")`.

## 8. Files

| Path | Content |
|---|---|
| `research/ldn_prep.py` | DST‑correct London‑time columns for all bar files (`lbars{1,2,3}.pkl`). |
| `research/ldn_lab.py` | London lab: day filter, pre‑session levels, runner on the conservative 1m engine. |
| `research/ldn_chart.py`, `results/london_charts/` | Chart generator and example sessions. |
| `research/ldn_stats1.py`, `research/ldn_null.py` | Extreme‑timing statistics and the volatility‑preserving permutation null. |
| `research/ldn_calib.py`, `ldn_simple.py`, `ldn_round2.py`, `ldn_fade.py`, `ldn_mr.py`, `ldn_open.py` | Calibration and all simple‑rule tests. |
| `research/PREREG_LDN.json`, `ldn_validate.py`, `ldn_wf.py` | Frozen candidates, single 2025 evaluation, walk‑forward. |
| `results/ldn_prereg_results.csv`, `results/ldn_trades_*.csv` | Candidate metrics and trade lists. |
