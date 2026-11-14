from datetime import datetime
from pathlib import Path

import pytest

from quant_lab.data import align, load_frame, to_bars

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
pytestmark = pytest.mark.skipif(
    not DATA_DIR.is_dir(), reason="run scripts/fetch_sample.py first"
)

def test_load_frame_reads_hk_daily_bars():
    df = load_frame(DATA_DIR / "0700_HK.parquet")
    assert len(df) == 939
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert df.index.is_monotonic_increasing


def test_to_bars_maps_row_to_bar():
    df = load_frame(DATA_DIR / "0700_HK.parquet")
    bar = next(to_bars(df, symbol="0700_HK"))
    assert isinstance(bar.volume, int)
    assert isinstance(bar.ts, datetime)
    assert bar.ts == df.index[0]


def test_align():
    df1 = load_frame(DATA_DIR / "0700_HK.parquet")
    df2 = load_frame(DATA_DIR / "BTC-USD.parquet")
    aligned = align({"0700_HK": df1, "BTC-USD": df2}, how="inner")
    assert len(aligned) == 938
    assert aligned.loc['2023-01-03', ('BTC-USD', 'Volume')]  == 13903079207
    aligned = align({"0700_HK": df1, "BTC-USD": df2}, how="outer")
    assert len(aligned) == 1399
    assert aligned.loc['2023-01-03', ('BTC-USD', 'Volume')]  == 13903079207
