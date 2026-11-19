from datetime import datetime

import pytest

from quant_lab.bar import Bar
from quant_lab.handler import DataHandler


def make(sym, day, px=10.0):
    return Bar(sym, datetime(2026, 11, day), px, px, px, px)

def test_data_handler_1():
    bars = {"A":[make("A", 17), make("A", 18)]}
    data_handler = DataHandler(bars)
    events = data_handler.update()
    assert events[0].ts == datetime(2026, 11, 17) and len(events) == 1
    events = data_handler.update()
    assert events[0].ts == datetime(2026, 11, 18)


def test_data_handler_2():
    bars = {"HK":[make("HK", 17), make("HK", 19)],
            "BTC":[make("BTC", 17), make("BTC", 18)]}
    data_handler = DataHandler(bars)
    events = []
    while cur_events := data_handler.update():
        events += cur_events
    assert [event.ts.day for event in events] == [17, 17, 18, 19]

    assert data_handler.update() is None


def test_data_handler_3():
    bars = {"HK":[make("HK", 20), make("HK", 19)]}
    with pytest.raises(ValueError):
        DataHandler(bars)


