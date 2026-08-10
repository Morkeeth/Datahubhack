"""claim_and_build reports the ghost's real state, never a constant.

On 2026-08-10 the MCP tool set ``status = "solidified"`` unconditionally after
``build_and_solidify`` returned. A build that opened a pull request and correctly
left the ghost ``claimed`` still answered "solidified", so the watcher printed
``solid · <pr>`` while a fresh hydrate from DataHub said ``claimed``,
``schema_fields`` was empty and no table existed in the warehouse. The catalog was
right and the tool was lying, which is the one failure this project exists to
refuse. Status has to be read off the ghost.
"""

import nullspace.mcp_server as mcp_server


class _FakeGhost:
    def __init__(self, state: str) -> None:
        self.state = state
        self.want = "monthly recurring revenue by segment"
        self.demand = 3
        self.requesters = ["a", "b", "c"]
        self.urn = "urn:li:dataset:(urn:li:dataPlatform:nullspace,ghost_mrr,PROD)"

    def to_public(self) -> dict:
        return {"want": self.want, "state": self.state, "urn": self.urn}


class _FakeStore(dict):
    pass


class _FakeNs:
    demand_threshold = 3
    dh = None

    def __init__(self, ghost: _FakeGhost) -> None:
        self.store = _FakeStore({ghost.want: ghost})


def _call(monkeypatch, state_after_build: str) -> dict:
    """Open ghost goes in; ``state_after_build`` is what the builder leaves behind."""
    before = _FakeGhost("ghost")
    after = _FakeGhost(state_after_build)
    ns = _FakeNs(before)
    monkeypatch.setattr(mcp_server, "public_mode", lambda: False)
    monkeypatch.setattr(mcp_server, "_identify", lambda ctx: ("test-builder", "test"))
    monkeypatch.setattr(mcp_server, "_ns", lambda: ns)
    monkeypatch.setattr(mcp_server, "build_and_solidify", lambda *a, **k: after)
    fn = getattr(mcp_server.claim_and_build, "fn", mcp_server.claim_and_build)
    return fn(want=before.want, ctx=None)


def test_claimed_ghost_is_not_reported_as_solidified(monkeypatch):
    out = _call(monkeypatch, "claimed")
    assert out["status"] == "claimed"
    assert out["status"] != "solidified"
    assert "awaiting" in out, "a claimed build must say what is still owed"


def test_solid_ghost_is_reported_as_solidified(monkeypatch):
    out = _call(monkeypatch, "solid")
    assert out["status"] == "solidified"
    assert "awaiting" not in out
