import asyncio
from collections import defaultdict
import uuid


class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event_type, handler, priority=0):
        self.subscribers[event_type].append((priority, handler))

    async def publish(self, event_type, data=None):
        if data is None:
            data = {}
        data["trace_id"] = str(uuid.uuid4())[:8]
        for p, h in sorted(self.subscribers.get(event_type, []), key=lambda x: -x[0]):
            await h(data)


class Runtime:
    def __init__(self):
        self.bus = EventBus()
        self.state = {}

    def update_state(self, k, v):
        self.state[k] = v

    async def dispatch(self, event, data):
        await self.bus.publish(event, data)


class Agent:
    def __init__(self, rt):
        self.runtime = rt

    async def start(self):
        pass

    async def stop(self):
        pass
