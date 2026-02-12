import asyncio
import unittest

from ndefender_antsdr_scan.api.bus import EventBus


class ApiBusTests(unittest.TestCase):
    def test_publish_and_last(self) -> None:
        bus = EventBus(maxlen=2)
        bus.publish({"id": 1})
        bus.publish({"id": 2})
        bus.publish({"id": 3})
        last = bus.last(2)
        self.assertEqual([item["id"] for item in last], [2, 3])

    def test_subscribe_receives(self) -> None:
        bus = EventBus(maxlen=10)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bus.set_loop(loop)
        queue = bus.subscribe(max_queue=1)
        bus.publish({"id": 1})
        item = loop.run_until_complete(queue.get())
        self.assertEqual(item["id"], 1)
        bus.unsubscribe(queue)
        loop.close()


if __name__ == "__main__":
    unittest.main()
