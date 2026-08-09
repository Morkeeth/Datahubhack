"""Minimal FastAPI view for Join Treaty candidates, evidence, and relationships.

The DataHub OSS V2 UI does not render ERModelRelationship entities yet, so this
view is the relationship/evidence surface. Each accepted, applied treaty also
links to the native dataset Properties receipt in DataHub for UI proof.
"""

from __future__ import annotations

import html
import os
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from .apply import treaty_exists
from .datahub import DataHubClient
from .pipeline import apply_candidate, audit


def _frontend_url() -> str:
    return os.environ.get("DATAHUB_FRONTEND_URL", "http://localhost:9002")


def _short(urn: str) -> str:
    try:
        return urn.split(",")[1].split(".")[-1]
    except Exception:
        return urn


def _dataset_link(urn: str) -> str:
    return f"{_frontend_url()}/dataset/{quote(urn, safe='')}/Properties"


_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  margin: 0; background: #0f1221; color: #e8eaf2; }
header { padding: 28px 40px; background: linear-gradient(120deg,#1b2350,#3a2a6b);
  border-bottom: 1px solid #2a2f55; }
h1 { margin: 0 0 6px; font-size: 26px; }
.sub { color: #aab0d6; font-size: 14px; }
main { padding: 28px 40px; max-width: 1100px; margin: 0 auto; }
.summary { display: flex; gap: 16px; margin-bottom: 22px; }
.pill { padding: 6px 14px; border-radius: 999px; font-size: 13px; font-weight: 600; }
.ok { background: #12351f; color: #6ee7a0; border: 1px solid #1f6b3c; }
.no { background: #3a1620; color: #ff9db0; border: 1px solid #7a2436; }
.card { background: #171a2e; border: 1px solid #2a2f55; border-radius: 14px;
  padding: 20px 22px; margin-bottom: 18px; }
.card.accepted { border-left: 4px solid #3fd07f; }
.card.rejected { border-left: 4px solid #ff6b81; opacity: .92; }
.jointitle { font-size: 18px; font-weight: 700; margin: 0 0 4px; }
.badge { font-size: 12px; padding: 3px 9px; border-radius: 6px; margin-left: 8px; }
.badge.acc { background:#12351f; color:#6ee7a0; }
.badge.rej { background:#3a1620; color:#ff9db0; }
.badge.card { background:#20264d; color:#a9b4f0; }
.gates { margin: 12px 0; padding: 0; list-style: none; }
.gate { display:flex; gap:10px; align-items:center; padding:4px 0; font-size:13px; }
.gicon { width:18px; text-align:center; }
.pass { color:#6ee7a0; } .fail { color:#ff9db0; }
.gdetail { color:#aab0d6; }
.evidence { margin-top:10px; }
.evidence details { background:#10121f; border:1px solid #262b4d; border-radius:8px; padding:8px 12px; }
.evidence code { color:#c7d0ff; font-size:12px; white-space:pre-wrap; }
.links a { color:#8fb4ff; text-decoration:none; margin-right:14px; font-size:13px; }
.apply { margin-top:12px; }
button { background:#3fd07f; color:#05210f; border:none; padding:8px 16px;
  border-radius:8px; font-weight:700; cursor:pointer; }
.applied { color:#6ee7a0; font-weight:700; }
.raw { color:#aab0d6; font-size:12px; margin-top:6px; }
code.urn { color:#c7d0ff; font-size:12px; }
"""


def create_app() -> FastAPI:
    api = FastAPI(title="Join Treaty")
    client = DataHubClient()

    @api.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        result = audit(client)
        cards = []
        for item in result.items:
            c, v = item.candidate, item.verdict
            pred = c.predicate
            cls = "accepted" if v.accepted else "rejected"
            badge = (
                '<span class="badge acc">ACCEPTED</span>'
                if v.accepted
                else '<span class="badge rej">REJECTED</span>'
            )
            card_badge = (
                f'<span class="badge card">{html.escape(v.cardinality)}</span>'
                if v.cardinality
                else ""
            )
            title = (
                f"{_short(pred.left.dataset_urn)}.{pred.left.field} "
                f"= {_short(pred.right.dataset_urn)}.{pred.right.field}"
            )
            gates = "".join(
                f'<li class="gate"><span class="gicon {("pass" if g.passed else "fail")}">'
                f'{("✓" if g.passed else "✕")}</span>'
                f"<span><b>{html.escape(g.name)}</b> "
                f'<span class="gdetail">— {html.escape(g.detail)}</span></span></li>'
                for g in v.gates
            )
            evidence = "".join(
                f"<details><summary>{html.escape(e.query_urn)}</summary>"
                f"<code>{html.escape(e.statement)}</code></details>"
                for e in c.evidence
            )
            action = ""
            if v.accepted:
                if treaty_exists(client, c.id):
                    er = client.er_relationship(c.id)
                    action = (
                        f'<div class="apply"><span class="applied">✓ Applied</span> '
                        f'<code class="urn">urn:li:erModelRelationship:{html.escape(c.id)}</code>'
                        f'<div class="raw">cardinality read-after-write: '
                        f'{html.escape(str(getattr(er, "cardinality", None)))}</div></div>'
                    )
                else:
                    action = (
                        f'<form class="apply" method="post" action="/apply/{quote(c.id)}">'
                        f'<button type="submit">Approve &amp; write native relationship</button></form>'
                    )
                links = (
                    f'<div class="links">'
                    f'<a href="{_dataset_link(pred.left.dataset_urn)}" target="_blank">'
                    f"{_short(pred.left.dataset_urn)} Properties ↗</a>"
                    f'<a href="{_dataset_link(pred.right.dataset_urn)}" target="_blank">'
                    f"{_short(pred.right.dataset_urn)} Properties ↗</a></div>"
                )
            else:
                links = ""
            cards.append(
                f'<div class="card {cls}">'
                f'<div class="jointitle">{html.escape(title)} {badge}{card_badge}</div>'
                f'<div class="gdetail">{html.escape(v.reason)}</div>'
                f'<ul class="gates">{gates}</ul>'
                f'<div class="evidence">{evidence}</div>'
                f"{links}{action}</div>"
            )

        body = (
            f"<header><h1>Join Treaty</h1>"
            f'<div class="sub">Observed join treaties mined from DataHub query history '
            f"· run {html.escape(result.run_id)}</div></header>"
            f"<main>"
            f'<div class="summary">'
            f'<span class="pill ok">{len(result.accepted())} accepted</span>'
            f'<span class="pill no">{len(result.rejected())} rejected</span></div>'
            f"{''.join(cards)}</main>"
        )
        return HTMLResponse(f"<!doctype html><html><head><meta charset='utf-8'>"
                            f"<title>Join Treaty</title><style>{_STYLE}</style></head>"
                            f"<body>{body}</body></html>")

    @api.post("/apply/{candidate_id}")
    def do_apply(candidate_id: str) -> RedirectResponse:
        result = audit(client)
        try:
            apply_candidate(client, result, candidate_id)
        except (KeyError, ValueError):
            pass
        return RedirectResponse(url="/", status_code=303)

    return api
