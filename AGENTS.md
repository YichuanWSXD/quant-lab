# AGENTS.md · quant-lab

> Project-level instructions for AI assistants working in this repository.
> Keep this file short. Anything long belongs in `README.md` or a design doc.

## What this repository is

P1 (event-driven backtest engine) and P4 (execution algorithm research) of a personal
quant-development portfolio. Research code, not production. **Nothing here is live-trading
infrastructure and it must never be used to trade real capital.**

Scope and non-goals are in `README.md`. The architecture and per-module contracts are there too —
read it before proposing structural changes.

## Division of labour (non-negotiable)

- **The human writes**: anything that encodes an assumption — `Fill` (fill price, partial fills,
  slippage, fees), `Portfolio` (positions, cash, PnL, look-ahead checks), and any module boundary.
- **The AI may provide**: specs, acceptance criteria, interface signatures, refactors of existing
  code, boilerplate, and review comments. **Not** drop-in implementations of the modules above.
- **Tests**: the human writes them first; the AI points out missing edge cases.
- **Debugging**: the human pastes the error, the AI suggests a direction. Do not edit files to
  "just make it pass".

## Conventions

- Python 3.12, managed by `uv`. Run `uv run pytest` and `uv run ruff check .` before committing.
- Commits: English, imperative, prefixed — `feat:`, `fix:`, `test:`, `docs:`, `chore:`.
- **Never commit data.** `data/` and `*.parquet` are git-ignored; `scripts/` regenerates them.
- Do not add dependencies without asking.

## Honesty rules

- Never tick a box in `README.md` for work that is not done.
- If a result is uncertain, say so; do not fill gaps with plausible-sounding numbers.
- Benchmark numbers in the README must come with the machine and the command used.
