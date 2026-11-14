


from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, order=True)
class Bar:
    """日线 bar。不可变、可按 (symbol, ts) 排序、拒绝 high < low 的脏数据"""
    symbol: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0

    def __post_init__(self):
        if self.high < self.low:
            raise ValueError(f"high < low: {self.high} < {self.low}")
