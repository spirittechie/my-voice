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

    async def h(d):
        received.append(d.get("text"))

    rt.events.subscribe("transcription_result", h)
    await rt.events.emit("transcription_result", {"text": "test"})
    assert "test" in received


@pytest.mark.asyncio
async def test_full_flow():
    o = Orchestrator()
    result = await o.execute_flow()
    assert result["final_state"] == "idle"
    assert result["clipboard"] == "deterministic test voice input"
    assert any("transcribing" in str(h) for h in result["history"])
    assert any("clipboard-writing" in str(h) for h in result["history"])
    assert any("success" in str(h) for h in result["history"])
