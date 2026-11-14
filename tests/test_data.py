from datetime import datetime
from pathlib import Path

from quant_lab.data import load_frame, to_bars

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def test_load_frame_reads_hk_daily_bars():
    df = load_frame(DATA_DIR / "0700_HK.parquet")
    assert len(df) == 939
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert df.index.is_monotonic_increasing

    bar = next(to_bars(df, symbol="0700_HK"))
    assert isinstance(bar.volume, int)
    assert isinstance(bar.ts, datetime)
    assert bar.ts == df.index[0]
