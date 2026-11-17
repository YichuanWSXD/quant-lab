"""P1-07 · DataHandler：逐 bar 推送（point-in-time）

契约在下面每个成员的 docstring 里。**实现由本人写；测试本人先写**（`quant-lab/AGENTS.md`）。
本文件只有签名和契约，函数体是 `raise NotImplementedError`。

── 为什么这块最容易出前视偏差 ────────────────────────────────
`DataHandler` 是回测里"时间"的唯一来源。只要它允许策略在 t 时刻看到 t+1 的 bar，
后面所有模块（Strategy / Portfolio / Performance）都会把未来信息算进收益，而且**看不出来**——
回测曲线会很好看，实盘会打脸，而且你找不到是哪一行漏的。
所以判据不是"能跑"，是**两条测试**（`weeks/W03.md` 目标 1）：
  1. t 时刻拿不到 t+1：推进到 ts=t 之后，不可能拿到 ts>t 的任何 bar
  2. 同时间戳顺序稳定：多个标的同时刻，出队顺序可复现（跑两次一样）

── 和 events.py 的分工 ──────────────────────────────────────
`DataHandler` **只产出** `Event`（`type == EventType.MARKET`）；排序、积压、重放是 `EventQueue` 的事。
别把队列逻辑写进 handler——那会让"数据源"和"排序器"耦合，P1-12 执行层就复用不了。

── 需要你决定的三件事（实现前写进 class docstring，一句话一条）────────
1. 同一 ts 有多个标的时（0700_HK 与 BTC-USD 都有 2026-10-29），`update()` 一次返回**一个** Event
   还是**一批**？前者下游简单，后者少一层循环——你怎么选，测试就怎么写。
2. 入参给 `list[Bar]`（可重复读、能 reset、占内存）还是 `Iterator[Bar]`（省内存、只能跑一遍）？
   先问自己：回测要跑多少次？
3. 数据耗尽时 `update()` 返回 `None` 还是抛 `StopIteration`？下游 `while (e := h.update())`
   怎么写最省事，就选哪个。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from quant_lab.bar import Bar
from quant_lab.events import Event


class DataHandler:
    """把多个标的的 bar 流按时间合并，逐条推给回测主循环。

    契约（我写的，你可以加，但别默默改）：
    - `update()` 返回的 Event：`type == EventType.MARKET`，`ts` 是 bar 自己的时间
    - **时间单调**：一旦吐出 ts=T 的 bar，之后任何 bar 的 ts 都 >= T
    - **同 ts 分组**：ts=T 的所有标的都吐完，才允许吐 ts>T 的
    - 不做任何"未来函数"：不能因为手里有后面的数据，就改变已经吐出去的 bar
    - 数据耗尽：按你决定的第 3 条办（None 或 StopIteration），**不要**返回一个假 Event

    边界（你填，3–5 条）：
    1.
    2.
    3.
    """

    def __init__(self, bars: Mapping[str, Iterable[Bar]]) -> None:
        """`bars`：symbol -> 该标的按 ts 升序排列的 bar。

        契约：
        - key 是 symbol，value 的 ts 必须**升序**；不升序时抛 `ValueError`（别偷偷 sort——
          偷偷排序会掩盖数据源的问题，回测里最难查的就是这种"帮你兜底"）
        - 同一个 symbol 的时间戳**不允许重复**（一天一条 bar）
        - 空 dict 合法：`update()` 立刻按耗尽处理
        - 传入后不再修改调用方的容器（拷贝还是惰性消费，你定，写一行理由进 commit）
        """
        raise NotImplementedError

    @property
    def symbols(self) -> tuple[str, ...]:
        """标的列表，顺序固定（= 你决定同 ts 内的出队顺序）。"""
        raise NotImplementedError

    def update(self) -> Event | None:
        """推进一个 bar，返回对应 Event。

        契约：
        - 内部要维护"每个标的的下一条"的指针；不能每次调用都从头扫
        - 返回的 Event.payload 至少能拿到 `Bar`（键名你定，例如 `payload["bar"]`）
        - 重复调用不推进时间：只有在真的吐出新 bar 时才改变内部状态
        - 数据耗尽：见 class docstring
        """
        raise NotImplementedError
