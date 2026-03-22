import asyncio
from collections import defaultdict
import uuid


class EventSystem:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event, handler, prio=0):
        self.subscribers[event].append((prio, handler))

    async def emit(self, event, data=None):
        if data is None:
            data = {}
        data["trace"] = str(uuid.uuid4())[:6]
        for _, h in sorted(self.subscribers[event], key=lambda x: -x[0]):
            await h(data)


class StateModel:
    def __init__(self):
        self.data = {}

    def set(self, k, v):
        self.data[k] = v

    def get(self, k):
        return self.data.get(k)


class Runtime:
    def __init__(self):
        self.events = EventSystem()
        self.state = StateModel()

    async def init(self):
        pass
