"""Read-only Nullspace board — the live URL judges hit."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from nullspace.emit import board_snapshot
from nullspace.persist import FileGhostStore

app = FastAPI(title="Nullspace Board", version="0.1.0")


@app.get("/api/board")
def api_board() -> JSONResponse:
    store = FileGhostStore()  # re-read each request so demo CLI writes are visible
    return JSONResponse(board_snapshot(store.list_ghosts()))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (Path(__file__).parent / "static" / "board.html").read_text(encoding="utf-8")
