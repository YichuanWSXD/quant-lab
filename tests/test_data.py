from pathlib import Path

import pandas as pd
import pytest

from quant_lab.data import load_frame

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def test_load_frame_reads_hk_daily_bars():
    frame = load_frame(DATA_DIR / "0700_HK.parquet")
    assert len(frame) == 939
