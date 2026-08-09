"""File-backed ghost store so the board process and demo CLI share state."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from fcntl import LOCK_EX, LOCK_UN, flock
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
        self._by_want = {}
        if not self.path.exists():
            return
        text = self.path.read_text(encoding="utf-8").strip()
        if not text:
            return
        raw = json.loads(text)
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
                schema_fields=list(item.get("schema_fields") or []),
                upstream_urns=list(item.get("upstream_urns") or []),
                schema_source=item.get("schema_source"),
                resolution=[
                    ResolutionEvent(**e) for e in (item.get("resolution") or [])
                ],
            )
            self._by_want[g.want.strip().lower()] = g

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Serialize complete read→DataHub write→file save operations."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_suffix(f"{self.path.suffix}.lock")
        with lock_path.open("a+") as lock:
            flock(lock.fileno(), LOCK_EX)
            try:
                # Another requester process may have committed while this one waited.
                self._load()
                yield
            finally:
                flock(lock.fileno(), LOCK_UN)

    def save(self, ghost: Ghost) -> None:
        super().save(ghost)
        self._persist()

    def clear(self) -> None:
        super().clear()
        self._persist()

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
        tmp = self.path.with_suffix(f"{self.path.suffix}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)
