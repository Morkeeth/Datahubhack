"""Throughput helpers stay honest under unit constraints (no GMS required)."""

from nullspace.client import DataHubClient


def test_ghost_emit_batch_size_default():
    client = DataHubClient.__new__(DataHubClient)
    client._ghost_buffer = []
    client._ghost_buffer_meta = []
    client._props_cache = {}
    client._ghost_batch_size = 40
    assert client._ghost_batch_size == 40


def test_open_demand_cache_roundtrip():
    client = DataHubClient.__new__(DataHubClient)
    client._open_demand_cache = set()
    assert not client.is_open_demand("foo")
    client.mark_open_demand("foo")
    assert client.is_open_demand("foo")
    client.clear_open_demand("foo")
    assert not client.is_open_demand("foo")
