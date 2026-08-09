"""GitHub webhook: MERGED PR on nullspace-dbt → solidify the claimed ghost.

Run locally (Lane A):

    NULLSPACE_WEBHOOK_SECRET=dev \\
      python3 -m nullspace.webhook

Point a GitHub repo webhook (pull_request events) at this server, or POST a
synthetic payload during the demo:

    curl -X POST http://localhost:8790/hooks/github \\
      -H 'Content-Type: application/json' \\
      -H "X-Hub-Signature-256: sha256=$(...)" \\
      -d @payload.json

When ``NULLSPACE_WEBHOOK_SECRET`` is empty, signature checks are skipped (demo only).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from nullspace.builder import solidify_after_merge
from nullspace.client import DataHubClient
from nullspace.config import settings
from nullspace.ghosts import Nullspace
from nullspace.persist import FileGhostStore

app = FastAPI(title="Nullspace finalize webhook", version="1.0.0")


def _ns() -> Nullspace:
    cfg = settings()
    dh = DataHubClient(cfg)
    ns = Nullspace(
        FileGhostStore(),
        demand_threshold=cfg.demand_threshold,
        dh=dh if dh.healthy() else None,
    )
    if ns.dh is not None:
        ns.hydrate(replace=False)
    return ns


def _verify(secret: str, body: bytes, signature: str | None) -> None:
    if not secret:
        return
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=401, detail="missing X-Hub-Signature-256")
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    expected = "sha256=" + digest
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="bad signature")


@app.post("/hooks/github")
async def github_pull_request(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> JSONResponse:
    body = await request.body()
    secret = os.getenv("NULLSPACE_WEBHOOK_SECRET", "")
    _verify(secret, body, x_hub_signature_256)
    if x_github_event and x_github_event not in {"pull_request", "ping"}:
        return JSONResponse({"status": "ignored", "event": x_github_event})
    if x_github_event == "ping":
        return JSONResponse({"status": "pong"})

    payload: dict[str, Any] = json.loads(body.decode("utf-8"))
    action = payload.get("action")
    pr = payload.get("pull_request") or {}
    if action != "closed" or not pr.get("merged"):
        return JSONResponse(
            {"status": "ignored", "action": action, "merged": pr.get("merged")}
        )

    pr_url = pr.get("html_url") or ""
    ns = _ns()
    if ns.dh is None:
        raise HTTPException(status_code=503, detail="DataHub unreachable")

    matched = [
        g
        for g in ns.store.list_ghosts()
        if g.pr_url == pr_url and g.state == "claimed"
    ]
    if not matched:
        # Hydrate again in case search index lagged.
        ns.hydrate(replace=True)
        matched = [
            g
            for g in ns.store.list_ghosts()
            if g.pr_url == pr_url and g.state == "claimed"
        ]
    if not matched:
        return JSONResponse(
            {
                "status": "no_claimed_ghost",
                "pr_url": pr_url,
                "hint": "ghost must be claimed with this pr_url before merge",
            },
            status_code=404,
        )

    results = []
    for ghost in matched:
        solid = solidify_after_merge(
            ns, ghost.want, builder_id="webhook", merge=False
        )
        results.append(
            {
                "want": solid.want,
                "urn": solid.urn,
                "state": solid.state,
                "fields": [f["name"] for f in solid.schema_fields],
            }
        )
    return JSONResponse({"status": "solidified", "ghosts": results, "pr_url": pr_url})


def main() -> None:
    import uvicorn

    host = os.getenv("NULLSPACE_WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("NULLSPACE_WEBHOOK_PORT", "8790"))
    uvicorn.run("nullspace.webhook:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
