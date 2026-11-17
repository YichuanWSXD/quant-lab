"""事件与事件队列（P1-08）

契约在下面每个成员的 docstring 里。**实现由本人写；测试本人先写**（`quant-lab/AGENTS.md`）。

本文件只给签名和契约，不含实现——函数体是 `raise NotImplementedError`。

── 为什么先做这个 ────────────────────────────────────────────────
`DataHandler` 产出 `Event`，`EventQueue` 按时间排 `Event`，所以 **Event 的类型定不下来，
后面两块都得返工**。顺序：Event → EventQueue → DataHandler。

── 四个决定 · 答案写在这里（11-16 已讨论完，把结论填进 `答：` 后面）──────
D1 同一 ts 谁先出队：
    答：按照插入顺序出队（先进先出）。EventQueue 内部用一个计数器记录每个事件的插入顺序，出队时先比较 ts，再比较插入顺序。
D2 队列空时 get() 返回什么：
    答：返回None,因为上游的market来决定是否结束,而事件队列空时比较正常的,可以返回None,让上游决定是否继续等待,而不是抛异常。
D3 Event 要不要 frozen：
    答：要。Event 是只读的，这是一个契约。EventQueue 只读 Event，DataHandler 只读 Event，Portfolio 只读 Event，Execution 只读 Event。谁都不该改它。
D4 payload 用什么承载：
    答：用 `dict` 承载。虽然会丢失类型信息，但提供了灵活性。键名靠约定,缺键就抛出异常.

── 原始问题（留作对照，别删）──────────────────────────────────
1. 同一时间戳的两个事件，谁先出队？（插入顺序？还是由你在 Event 上加序号？）
2. 队列空时 `get()` 返回 `None` 还是抛异常？（下游 `while True: e = q.get()` 怎么写）
3. `Event` 要不要 `frozen`？（它会被多个模块读，谁都不该改它）
4. `payload` 用什么承载？（`dict` 灵活但类型全丢；具体字段类型安全但每加一种事件就改类）
"""

from __future__ import annotations

import heapq
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto


class EventType(Enum):
    """事件种类。加新种类时，先想清楚"谁消费它"。"""

    MARKET = auto()   # 行情（来自 DataHandler）
    SIGNAL = auto()   # 策略信号
    ORDER = auto()    # 下单意图（Portfolio 发出）
    FILL = auto()     # 成交回报（Execution 发出）


@dataclass(frozen=True)
class Event:
    """一条事件。

    契约：
    - 不可变（`frozen=True`）；下游只读
    - `ts` 是事件时间，不是处理时间（point-in-time 的基础）
    - 可比较：按 `ts` 排序（同 ts 的先后由 EventQueue 决定，不由 Event 决定）

    边界（4 条）：
    1. `payload` 的键名是约定：MARKET 必有 `symbol`/`bar`；ORDER 必有
       `symbol`/`side`/`qty`/`price`；FILL 必有 `order_id`/`price`/`qty`。
       缺键 = 程序错误，消费端直接抛 `KeyError`，**禁用 `.get()` 兜底**（它会把错误变成 NaN）。
    2. 校验必须在"改状态之前"：缺键/脏 bar 要在 Portfolio 动现金和持仓之前炸掉；
       不许"只终止这一笔"——半改的状态比崩溃更难查。
    3. `ts` 一律 tz-naive（和 `data/raw` 的索引一致）；tz-aware 传进来算调用方错误。
    4. 空 `payload={}` 合法（事件种类决定里面有没有东西），但消费该种类的代码要自己按第 1 条抛。
    """

    ts: datetime
    type: EventType
    payload: dict  # ← D4：dict + 约定键名，键表见上面边界 1




class EventQueue:
    """按时间戳出队的事件队列。

    契约：
    - `put(e)`：入队，O(log n)
    - `get()`：取出**时间戳最早**的事件；同时间戳时按边界 1
    - `__len__`：当前积压条数
    - `empty()`：是否为空
    - D1 / D2 的落点是下面边界 1、2

    边界（4 条）：
    1. 同 `ts` 按 `put` 的先后出队（内部自增序号）；同一个 `Event` 对象 `put` 两次
       算两条，各占一个序号——去重是调用方的事，队列不管。
    2. 队列空时 `get()` 返回 `None`：只表示"此刻没有"，**不表示数据结束**。
    3. `put` 不要求按时间序：先入 11-18 再入 11-17，出队仍是 11-17 先。
    4. `__iter__` 看的是调用那一刻的快照：不消费队列，遍历期间新 `put` 的看不到。
    """

    def __init__(self) -> None:
        self.events: list[tuple[datetime, int, Event]] = []
        self._next_seq = 0

    def put(self, event: Event) -> None:
        heapq.heappush(self.events, (event.ts, self._next_seq, event))
        self._next_seq += 1

    def get(self) -> Event | None:
        if not self.events:
            return None
        return heapq.heappop(self.events)[2]

    def __len__(self) -> int:
        return len(self.events)

    def empty(self) -> bool:
        return len(self.events) == 0

    def __iter__(self) -> Iterator[Event]:
        """按出队顺序遍历（不消费）。

        这段是**普通函数**，不是生成器——函数体里没有 `yield`。

        对比一下之前那版（错的）：
            def __iter__(self):
                copied_events = self.events.copy()
                while copied_events:
                    yield heapq.heappop(copied_events)[2]
        那版的顺序没错，但**整段都被推迟**：函数体里有 `yield`，所以 `iter(q)` 只是
        造了一个生成器对象，`copy()` 要等到第一次 `next()` 才执行。于是
        `it = iter(q); q.put(x)` 之后再遍历，还能看到 `x`——边界 4 的"调用那一刻的快照"
        就不成立了。

        写成普通函数，`iter(q)` 一返回，快照已经拷完，之后 `put` 的看不到。
        """
        snapshot = self.events.copy()
        return (heapq.heappop(snapshot)[2] for _ in range(len(snapshot)))
