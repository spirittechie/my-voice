import asyncio
import pytest
from src.runtime.runtime import Runtime
from src.runtime.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_runtime_init():
    rt = Runtime()
    await rt.init()
    assert rt.state.get() == "idle"


@pytest.mark.asyncio
async def test_event_dispatch():
    rt = Runtime()
    received = []

    def h(d):
        received.append(d.get("text"))

    rt.events.subscribe("transcription_result", h)
    rt.events.emit("transcription_result", {"text": "test"})
    assert "test" in received


@pytest.mark.asyncio
async def test_full_flow():
    o = Orchestrator()
    result = await o.run_flow()
    assert "clipboard" in str(o.runtime.state.data)
