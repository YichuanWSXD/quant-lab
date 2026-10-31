# quant-lab

An event-driven backtesting engine and market-data toolkit in which **every assumption is explicit, testable, and printed in the output**.

---

## What it is

Most backtests are a dataframe and a shift. `quant-lab` replaces that with an event loop: data arrives one bar at a time, a strategy sees only what had been published at that timestamp, and every order the engine accepts produces a fill with a recorded price, quantity, slippage and fee.

What a run produces:

- **A fill for every order** — price, size, costs — not a return series with costs subtracted afterwards.
- **Point-in-time data access.** A strategy cannot read a bar that had not been published yet.
- **A per-run report.** Equity curve, drawdown, turnover, hit rate, per-trade and per-symbol attribution.
- **A reproducible run.** Data snapshot + config hash + seed reproduce the same numbers, on any machine.

## Why it exists

The four decisions that most often turn a good-looking backtest into a losing strategy are made *implicitly* by convenient tooling:

| Hidden assumption | What it actually does |
|---|---|
| Fill at the close | A same-bar signal filled at that close is look-ahead, not alpha |
| Every order fills completely | Illiquid names behave like index futures |
| Costs as one flat bps number | A strategy that only survives at zero cost looks profitable |
| One price series, adjusted | Splits and dividends silently rewrite the past |

Production strategies die on these, not on the signal. So the design rule here is the opposite of convenience:

> **Nothing is implicit.** Fill price, fill quantity, the slippage model, the fee schedule and data timing are configuration, and the report states which values produced each number.

That is the whole reason to build this instead of adopting an existing framework: not features, but **auditability**.

## What you can do with it

- **Stress a signal before funding it.** Run the same strategy at 0 / 5 / 10 / 20 bps of slippage and see where the edge dies.
- **Compare execution algorithms.** Market, limit, VWAP, participation — on the same signal, same data, same cost model.
- **Reproduce someone else's result.** The assumptions that produced a number are in the config, so a published Sharpe can be re-run instead of trusted.
- **Attribute PnL.** Separate what came from the signal, from position sizing, and from execution.

## Architecture

![architecture](docs/p1-architecture.png)

Seven components, each with a narrow contract. The `not responsible` column is the load-bearing one: it is what stops modules from growing into each other.

| Component | Responsible for | Explicitly **not** responsible for |
|---|---|---|
| `DataHandler` | Loading, timezone alignment, duplicate/missing-timestamp detection, retry on connection failure | Judging whether a *price* is correct |
| `EventQueue` | Ordering events by timestamp, dispatching to consumers, decoupling consumers from data sources | Data-quality validation, cleaning, gap filling |
| `Strategy` | Turning market events into signals, given its parameters | Position sizing, portfolio state, execution |
| `Portfolio` | Signals + current positions + mark prices → target position → `OrderEvent` | Generating signals, choosing how to execute, computing performance |
| `ExecutionHandler` | Converting orders into actionable executions (live: routing; backtest: handing to the fill simulator) | Making trading decisions |
| `Fill` | **Backtest:** deciding fill price, filled quantity, slippage, fees. **Live:** recording exchange fills | Trading decisions |
| `Performance` | Post-trade reporting: returns, drawdown, turnover, attribution | Producing trades |

### Non-obvious design decisions

1. **`Fill → Portfolio` is a return edge, not a one-way pipe.** Without it positions and cash never update and PnL stays zero. Execution is a loop, not a pipeline.
2. **`Portfolio` emits `OrderEvent` (an order), not `orderBook` (market data).** The book comes from `DataHandler`; the portfolio decides *what it wants*, never *what the market looks like*.
3. **`Fill` is where the price is decided.** In a backtest it *is* the exchange — it owns fill price, quantity, slippage and fees. `Performance` only reads results; it never invents costs.

## Status

Design complete; the engine is under active development and no component is usable yet. The acceptance criteria below are the definition of "done" for the first release.

| Milestone | What | Status |
|---|---|---|
| **P1** | Event-driven backtest engine (this repository) | design ✅ / code ⬜ |
| **P4** | Execution algorithm research — market / limit / VWAP / participation — on top of the P1 engine (this repository) | ⬜ |
| **P2** | L2 order book reconstruction + replay (Binance / OKX depth diff) — separate repository, together with P3 and P5 | ⬜ |
| **P5** | Low-latency components in C++ (ring buffer, matching hot path) — with P2 | ⬜ |

P1 uses **equities** on purpose: suspensions, adjustment factors and market hours force the correctness checks that matter. P2 uses **crypto** because free full-depth, 24/7 data is what makes microstructure work possible.

## Getting started

```bash
uv sync
uv run pytest
```

Python 3.12, managed by [uv](https://docs.astral.sh/uv/).

## Data

Daily OHLCV via `yfinance` (HK equities + HSI), adjusted with `auto_adjust=True`.

Raw data is **not** committed — see `.gitignore`; `scripts/` regenerates it. Nothing in the repository depends on a particular snapshot being present.

## P1 acceptance criteria

- [ ] Same strategy, same data: engine output matches a hand-computed, trade-by-trade result within `1e-6`
- [ ] 100k bars × 10 symbols backtest in under 10 seconds (local machine)
- [ ] Core modules above 70% test coverage
- [ ] A deliberately look-ahead strategy (signal on close, fill on the same close) is **rejected** by the engine's look-ahead check

## Known limitations

- No engine code yet — this README specifies the target, it does not describe a shipped product.
- Daily bars only; intraday and tick granularity arrive with P2.
- Long/short cash equities, single currency; no derivatives, no borrow costs, no financing.
