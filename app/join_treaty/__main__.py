"""Join Treaty command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .apply import treaty_exists
from .datahub import DataHubClient
from .pipeline import apply_candidate, audit
from .seed import build_seed_queries, seed

app = typer.Typer(add_completion=False, help="Mine repeated joins into native DataHub ER relationships.")
console = Console()

DEFAULT_RECEIPT = "examples/join-treaty-receipt.json"


def _client() -> DataHubClient:
    return DataHubClient()


@app.command("seed")
def cmd_seed() -> None:
    """Emit real DataHub Query entities for the warehouse joins."""
    client = _client()
    console.print(f"[bold]Seeding {len(build_seed_queries())} Query entities...[/bold]")
    urns = seed(client)
    for u in urns:
        console.print(f"  [green]+[/green] {u}")
    console.print(f"[bold green]Seeded {len(urns)} queries into DataHub.[/bold green]")


@app.command("audit")
def cmd_audit(json_out: Optional[str] = typer.Option(None, "--json", help="Write the audit report to this path.")) -> None:
    """Discover + validate join candidates (deterministic, read-only)."""
    client = _client()
    result = audit(client)

    table = Table(title=f"Join Treaty audit ({result.run_id})", show_lines=False)
    table.add_column("candidate id", style="cyan", no_wrap=True)
    table.add_column("join")
    table.add_column("queries", justify="right")
    table.add_column("verdict")
    table.add_column("cardinality")
    table.add_column("reason")

    for item in result.items:
        c, v = item.candidate, item.verdict
        pred = c.predicate
        join = f"{_short(pred.left.dataset_urn)}.{pred.left.field} = {_short(pred.right.dataset_urn)}.{pred.right.field}"
        verdict = "[green]ACCEPT[/green]" if v.accepted else "[red]REJECT[/red]"
        applied = " [dim](applied)[/dim]" if v.accepted and treaty_exists(client, c.id) else ""
        table.add_row(
            c.id, join, str(c.occurrences), verdict + applied, v.cardinality or "-", v.reason
        )
    console.print(table)
    console.print(
        f"[bold]{len(result.accepted())} accepted, {len(result.rejected())} rejected.[/bold]"
    )

    if json_out:
        payload = {
            "run_id": result.run_id,
            "items": [
                {
                    "candidate_id": i.candidate.id,
                    "join": i.candidate.predicate.key(),
                    "occurrences": i.candidate.occurrences,
                    "accepted": i.verdict.accepted,
                    "cardinality": i.verdict.cardinality,
                    "reason": i.verdict.reason,
                    "gates": [
                        {"name": g.name, "passed": g.passed, "detail": g.detail}
                        for g in i.verdict.gates
                    ],
                    "evidence_query_urns": sorted({e.query_urn for e in i.candidate.evidence}),
                }
                for i in result.items
            ],
        }
        Path(json_out).write_text(json.dumps(payload, indent=2))
        console.print(f"[dim]Wrote audit report to {json_out}[/dim]")


@app.command("apply")
def cmd_apply(
    candidate: Optional[str] = typer.Option(None, "--candidate", help="Candidate id to apply."),
    all_accepted: bool = typer.Option(False, "--all-accepted", help="Apply every accepted candidate."),
    yes: bool = typer.Option(False, "--yes", help="Skip the interactive approval prompt."),
    out: str = typer.Option(DEFAULT_RECEIPT, "--out", help="Where to write the treaty receipt(s)."),
) -> None:
    """Human-approved write of the native ER relationship + dataset receipts."""
    client = _client()
    result = audit(client)

    if all_accepted:
        targets = [i.candidate.id for i in result.accepted()]
    elif candidate:
        targets = [candidate]
    else:
        console.print("[red]Provide --candidate <id> or --all-accepted.[/red]")
        raise typer.Exit(2)

    if not targets:
        console.print("[yellow]No accepted candidates to apply.[/yellow]")
        raise typer.Exit(0)

    if not yes:
        console.print(f"About to write treaties: {', '.join(targets)}")
        typer.confirm("Approve native DataHub writes?", abort=True)

    receipts = []
    new_count = 0
    for cid in targets:
        receipt, was_new = apply_candidate(client, result, cid)
        new_count += 1 if was_new else 0
        state = "new" if was_new else "idempotent (already present)"
        raw = receipt.read_after_write
        console.print(
            f"[green]OK[/green] {cid} -> {receipt.er_relationship_urn} "
            f"[{receipt.cardinality}] ({state}); "
            f"read-after-write: ER={raw['er_relationship_present']} "
            f"src_receipt={raw['source_receipt_present']} "
            f"dst_receipt={raw['destination_receipt_present']}"
        )
        receipts.append(receipt.to_dict())

    payload = receipts[0] if len(receipts) == 1 else {"run_id": result.run_id, "treaties": receipts}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(payload, indent=2))
    console.print(f"[bold]Wrote receipt to {out}. New this run: {new_count}.[/bold]")


@app.command("serve")
def cmd_serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(3000, "--port"),
) -> None:
    """Serve the minimal Join Treaty web view."""
    import uvicorn

    from .web import create_app

    uvicorn.run(create_app(), host=host, port=port, log_level="info")


@app.command("demo")
def cmd_demo(yes: bool = typer.Option(True, "--yes/--no-yes", help="Auto-approve writes.")) -> None:
    """Seed, audit, then apply every accepted candidate (end-to-end)."""
    client = _client()
    console.print("[bold]1) Seeding queries...[/bold]")
    seed(client)
    console.print("[bold]2) Auditing...[/bold]")
    result = audit(client)
    console.print(
        f"   {len(result.accepted())} accepted, {len(result.rejected())} rejected."
    )
    console.print("[bold]3) Applying accepted treaties...[/bold]")
    for item in result.accepted():
        if not yes:
            typer.confirm(f"Apply {item.candidate.id}?", abort=True)
        receipt, was_new = apply_candidate(client, result, item.candidate.id)
        console.print(
            f"   [green]{item.candidate.id}[/green] -> {receipt.er_relationship_urn} "
            f"({'new' if was_new else 'idempotent'})"
        )
    console.print("[bold green]Demo complete. Run `join-treaty serve` for the view.[/bold green]")


def _short(urn: str) -> str:
    try:
        return urn.split(",")[1].split(".")[-1]
    except Exception:
        return urn


if __name__ == "__main__":
    app()
