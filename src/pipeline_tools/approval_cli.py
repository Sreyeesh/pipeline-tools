from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import asset_exists, create_approval, init_db, list_approvals, resolve_db_path
from pipeline_tools.output import render_table


app = typer.Typer(help="Approvals for assets.")


@app.command("set")
def cmd_set(
    asset_id: int = typer.Option(..., "--asset-id", "-a", help="Asset ID."),
    status: str = typer.Option(..., "--status", "-s", help="Approval status (approved/rejected/needs_changes)."),
    note: str | None = typer.Option(None, "--note", "-n", help="Optional note."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    if not asset_exists(db_path, asset_id):
        raise typer.BadParameter(f"Asset ID not found: {asset_id}")
    approval_id = create_approval(db_path, asset_id=asset_id, status=status, note=note)
    typer.echo(f"Recorded approval #{approval_id} for asset #{asset_id} ({status})")


@app.command("list")
def cmd_list(
    asset_id: int | None = typer.Option(None, "--asset-id", "-a", help="Filter by asset ID."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    approvals = list_approvals(db_path, asset_id=asset_id)
    if not approvals:
        typer.echo("No approvals yet.")
        raise typer.Exit()
    rows = [
        [
            str(a["id"]),
            str(a["asset_id"]),
            a["status"],
            a.get("note") or "",
        ]
        for a in approvals
    ]
    for line in render_table(["ID", "ASSET", "STATUS", "NOTE"], rows):
        typer.echo(line)
