import asyncio
from collections import defaultdict
import uuid


class EventSystem:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event, handler, prio=0):
        self.subscribers[event].append((prio, handler))

    def emit(self, event, data=None):
        if data is None:
            data = {}
        data["trace"] = str(uuid.uuid4())[:6]
        for _, h in sorted(self.subscribers.get(event, []), key=lambda x: -x[0]):
            h(data)


class StateModel:
    def __init__(self):
        self.data = {"current": "idle"}
        self.history = []

    def transition(self, to):
        self.history.append((self.data["current"], to))
        self.data["current"] = to

    def get(self, k="current"):
        return self.data.get(k)

    def set(self, k, v):
        self.data[k] = v


class Runtime:
    def __init__(self):
        self.events = EventSystem()
        self.state = StateModel()

    async def init(self):
        self.state.transition("idle")

    async def trigger(self, event, data=None):
        await self.events.emit(event, data)
        if event == "input_trigger":
            self.state.transition("listening")
        elif event == "transcription_result":
            self.state.transition("success")
        elif event == "error":
            self.state.transition("error")
