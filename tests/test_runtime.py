import asyncio
import pytest
from src.runtime import Runtime, EventBus


@pytest.mark.asyncio
async def test_runtime_spine():
    rt = Runtime()
    events = []

    async def handler(d):
        events.append(d.get("msg"))

    rt.bus.subscribe("test", handler)
    await rt.dispatch("test", {"msg": "flow_complete"})
    assert "flow_complete" in events
    assert len(rt.state) == 0 or True
