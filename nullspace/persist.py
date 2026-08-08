"""File-backed ghost store so the board process and demo CLI share state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from nullspace.ghosts import Ghost, MemoryGhostStore, ResolutionEvent

DEFAULT_PATH = Path(
    os.getenv("NULLSPACE_STORE", Path(tempfile.gettempdir()) / "nullspace-ghosts.json")
)


class FileGhostStore(MemoryGhostStore):
    def __init__(self, path: Path | None = None) -> None:
        super().__init__()
        self.path = path or DEFAULT_PATH
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for item in raw.get("ghosts", []):
            g = Ghost(
                want=item["want"],
                urn=item["urn"],
                dataset_name=item["dataset_name"],
                demand=item.get("demand", 0),
                state=item.get("state", "ghost"),
                requesters=list(item.get("requesters") or []),
                pr_url=item.get("pr_url"),
                claimed_by=item.get("claimed_by"),
                resolution=[
                    ResolutionEvent(**e) for e in (item.get("resolution") or [])
                ],
            )
            self._by_want[g.want.strip().lower()] = g

    def save(self, ghost: Ghost) -> None:
        super().save(ghost)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"ghosts": [g.to_public() for g in self.list_ghosts()]}
        # to_public flattens resolution; re-dump full
        payload = {
            "ghosts": [
                {
                    **g.to_public(),
                    "resolution": [
                        {
                            "agent_id": e.agent_id,
                            "at_ms": e.at_ms,
                            "event": e.event,
                            "detail": e.detail,
                        }
                        for e in g.resolution
                    ],
                }
                for g in self.list_ghosts()
            ]
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
