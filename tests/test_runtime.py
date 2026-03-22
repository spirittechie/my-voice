import asyncio
import pytest
from src.runtime.runtime import Runtime
from src.runtime.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_runtime_init():
    rt = Runtime()
    await rt.init()
    assert rt.state is not None


@pytest.mark.asyncio
async def test_event_dispatch():
    rt = Runtime()
    received = []

    async def h(d):
        received.append(d)

    rt.events.subscribe("test", h)
    await rt.events.emit("test", {"ok": True})
    assert len(received) > 0


@pytest.mark.asyncio
async def test_state_transitions():
    o = Orchestrator()
    res = await o.run()
    assert res == "stub transcription"
