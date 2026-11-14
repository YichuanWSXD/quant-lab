"""示例测试：只示范形状（imports / 路径 / pytest.raises / parametrize），不测 load_frame。

看完可以删，也可以留着——"data/raw 里的原始文件齐全"本来就是条有用的测试。
"""

from pathlib import Path

import pandas as pd
import pytest

# 从 tests/ 往上走一级就是仓库根目录，不写死盘符
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def test_raw_files_exist():
    """最基础的一条：文件在不在。"""
    assert DATA_DIR.is_dir(), f"数据目录不存在: {DATA_DIR}"
    expected = {"0700_HK", "BTC-USD", "0005_HK", "^HSI"}
    found = {p.stem for p in DATA_DIR.glob("*.parquet")}
    assert expected <= found, f"缺文件: {expected - found}"


@pytest.mark.parametrize("symbol", ["0700_HK", "BTC-USD"])
def test_raw_columns(symbol):
    """parametrize：同一个测试跑两组参数，失败时 pytest 会告诉你是哪一组。"""
    frame = pd.read_parquet(DATA_DIR / f"{symbol}.parquet")
    assert list(frame.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert frame.index.is_monotonic_increasing


def test_missing_file_raises():
    """怎么测"应该抛异常"。"""
    with pytest.raises(FileNotFoundError):
        pd.read_parquet(DATA_DIR / "does_not_exist.parquet")
