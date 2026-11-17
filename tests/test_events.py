from datetime import datetime

from quant_lab.events import Event, EventQueue, EventType


def test_event_queue_sequence():
    # 同一 ts 两个事件，入队 A→B，出队也是 A→B；构造两次队列各跑一遍，结果一致
    event_queue = EventQueue()
    event1 = Event(datetime(2023, 1, 3), EventType.MARKET, {"symbol": "0700_HK", "bar": None, 'no':1})
    event_queue.put(event1)
    event2 = Event(datetime(2023, 1, 3), EventType.MARKET, {"symbol": "0700_HK", "bar": None, 'no':2})
    event_queue.put(event2)
    assert (len(event_queue) == 0) == event_queue.empty(), "队列长度和空状态不一致"

    pop1 = event_queue.get()
    pop2 = event_queue.get()
    assert pop1.payload['no'] == 1 and pop2.payload['no'] == 2, f"出队顺序错误: {pop1.payload['no']} -> {pop2.payload['no']}"
    assert (len(event_queue) == 0) == event_queue.empty(), "队列长度和空状态不一致"

    # 先 put 11-18 再 put 11-17，出队第一个是 11-17
    event_queue = EventQueue()
    event3 = Event(datetime(2023, 1, 18), EventType.MARKET, {"symbol": "0700_HK", "bar": None})
    event4 = Event(datetime(2023, 1, 17), EventType.MARKET, {"symbol": "0700_HK", "bar": None})
    event_queue.put(event3)
    event_queue.put(event4)
    pop3 = event_queue.get()
    assert pop3.ts == datetime(2023, 1, 17), f"出队顺序错误: {pop3.ts}，应为 2023-01-17"


def test_event_queue_empty():
    # 空队列 get() → None
    event_queue = EventQueue()
    assert event_queue.get() is None, "空队列 get() 应返回 None"


def test_event_queue_push_same_event_twice():
    event_queue = EventQueue()
    event = Event(datetime(2023, 1, 18), EventType.MARKET, {"symbol": "0700_HK", "bar": None})
    event_queue.put(event)
    event_queue.put(event)
    assert len(event_queue) == 2


def test_event_queue_iter():
    event_queue = EventQueue()
    event1 = Event(datetime(2023, 1, 3), EventType.MARKET, {"symbol": "0700_HK", "bar": None, 'no':1})
    event2 = Event(datetime(2023, 1, 3), EventType.MARKET, {"symbol": "0700_HK", "bar": None, 'no':2})
    event_queue.put(event1)
    event_queue.put(event2)

    cur_iter = iter(event_queue)
    for event in cur_iter:
        assert event_queue.get() == event

    cur_iter = iter(event_queue)
    event_queue.put(event2)
    assert len(list(cur_iter)) == 0


