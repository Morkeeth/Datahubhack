"""URN helpers for Nullspace ghosts.

Ghosts are real DataHub dataset URNs under platform `nullspace`.
Naming is deterministic so three independent consumers converge on one ghost.
"""

from __future__ import annotations

import hashlib
import re

from nullspace import ENV, PLATFORM


def _slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "unnamed"


def ghost_dataset_name(want: str) -> str:
    """Stable dataset name for a demand phrase."""
    slug = _slug(want)
    # Short digest keeps collisions rare without ugly full hashes in the UI
    digest = hashlib.sha256(slug.encode()).hexdigest()[:8]
    return f"ghost_{slug}_{digest}"


def dataset_urn(dataset_name: str) -> str:
    return f"urn:li:dataset:(urn:li:dataPlatform:{PLATFORM},{dataset_name},{ENV})"


def ghost_urn(want: str) -> str:
    return dataset_urn(ghost_dataset_name(want))


def corpuser_urn(agent_id: str) -> str:
    safe = _slug(agent_id)
    return f"urn:li:corpuser:nullspace_{safe}"
