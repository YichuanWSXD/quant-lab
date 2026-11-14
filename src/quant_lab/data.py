"""P1 数据层 · W02 目标 3（P1-03 / P1-04 / P1-05 / P1-06）

本文件是**骨架**：只有签名、契约、和数据事实。函数体由你写。
判据（`weeks/W02.md` 目标 3）：`quant-lab` 有 commit、3 个单测绿、能加载 2 标的并对齐。

跑（在 C:\\projects\\quant-lab 下）：

    uv run pytest -q
    uv run ruff check .

── 数据事实（2026-11-10 用 `data/raw/` 实测，不是估计）──────────────────
    标的        行数    索引范围                      备注
    0700_HK      939    2023-01-03 → 2026-10-30        港股交易日历
    BTC-USD     1398    2023-01-01 → 2026-10-29        含周末；比 HK 多 460 天

两表共同点：索引名 `Date`、`datetime64[ms]`、tz-naive、升序、无重复索引；
列 = `Open/High/Low/Close/Volume`（大写、float）；`columns.name == "Price"`；
`Close` 无缺失。
对齐（实测）：`inner` → **938** 行（HK 的 2026-10-30 在 BTC 里没有）；`outer` → **1399** 行。

这两个数是单测的锚：如果你算出别的数，先怀疑自己的对齐，再怀疑数据。

── 三个契约（对应 3 个单测）────────────────────────────────────────────
1. `load_frame` 读 parquet → 干净 DataFrame。缺文件抛 `FileNotFoundError`，
   缺列抛 `ValueError`，返回前把索引规整成升序 / tz-naive / 无重复。
2. `to_bars` DataFrame 的一行 → 一个 `Bar`，逐行 yield。
3. `align` 两个标的按时间对齐。**规则你定**：交易日历取谁、缺值怎么处理
   （丢 / 前值填充 / 保留 NaN）。只要单测能把"股票日历 vs 加密日历"的差异
   测出来（938 / 1399 这两个数就是干这个用的），就算过。

── 为什么这里不给实现 ─────────────────────────────────────────────────
仓库 `AGENTS.md`：测试你先写，我只指出缺的边界；模块边界和"哪些假设"归你。
所以下面每个函数只有签名和 docstring，body 是 `raise NotImplementedError`。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Literal

import pandas as pd

from quant_lab.bar import Bar

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


# ── Bar ─────────────────────────────────────────────────────────────────
# 放本文件还是单独 `bar.py`？你定——模块边界也是设计，写一行理由在 commit 里。
# 形状照 `C:\projects\python-drills\ch05_dataclass.py` 的成品搬（周六开工前先把它跑绿）：
#   symbol / ts / open / high / low / close / volume(int, 默认 0)
#   frozen（不可变）+ order（按 symbol, ts 排序）+ __post_init__ 校验 high >= low。
# 搬的时候把断言一起搬走，别只搬字段——那 7 条就是验收。


def load_frame(path: str | Path) -> pd.DataFrame:
    """读一个日线 parquet，返回规范化后的 DataFrame。

    契约：
    - 路径不存在 → `FileNotFoundError`（别吞，别返回空表）
    - 缺列 → `ValueError`，消息里写清缺了哪几列
    - 返回：索引升序、tz-naive、无重复；列只留 `REQUIRED_COLUMNS`
    - 不做清洗（不补前值、不去极值）——那是 `align` 的事

    待你决定、并写进本 docstring：symbol 从哪来？
    （文件名 `0700_HK.parquet` 推 / 当参数传 / 根本不放进 DataFrame）

    我打算用的 API：
    """
    df = pd.read_parquet(path, engine="pyarrow")

    # check index
    if df.index.name != "Date":
        if "Date" not in df.columns:
            raise ValueError("Missing column: Date")
        df = df.set_index("Date")
    df.index = pd.DatetimeIndex(df.index)
    df = df.sort_index()
    df = df.loc[~df.index.duplicated(keep="first")]
    df.index = df.index.tz_localize(None) # type: ignore

    if missing_columns := set(REQUIRED_COLUMNS) - set(df.columns):
        raise ValueError(f"Missing columns: {missing_columns}")

    df = df.loc[:, list(REQUIRED_COLUMNS)]
    return df



def to_bars(frame: pd.DataFrame, symbol: str) -> Iterator[Bar]:
    """逐行 yield `Bar`。`volume` 由 float 转 int；ts 取 index 上的 Timestamp。NaN 的 OHLC 行：跳过。

    契约：
    - 必须是生成器（调用时不把整表遍历一遍）
    - 产出条数 = `len(frame)`，顺序不变

    我打算用的 API：
    """
    for ts, row in frame.iterrows():
        if row[["Open", "High", "Low", "Close", 'Volume']].isna().any():
            continue
        yield Bar(
            symbol=symbol,
            ts=ts, # type: ignore
            open=row["Open"],
            high=row["High"],
            low=row["Low"],
            close=row["Close"],
            volume=int(row["Volume"]),
        )


def align(
    frames: dict[str, pd.DataFrame],
    how: Literal["inner", "outer"] = "inner",
) -> pd.DataFrame:
    """把多个标的按时间对齐成一张表。

    契约：
    - `how="inner"` 对 0700_HK + BTC-USD → **938** 行
    - `how="outer"` → **1399** 行
    - 对齐后任取一行，能同时拿到两个标的的 `Close`
    - 宽表,列 = (symbol, field) 的 MultiIndex
    """
    if how not in {"inner", "outer"}:
        raise ValueError(f"Unsupported alignment mode: {how!r}")

    results = pd.concat(frames, axis=1, join=how, sort=True)
    results.columns.names = ["symbol", "field"]
    return results
