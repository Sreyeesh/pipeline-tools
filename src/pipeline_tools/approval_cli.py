from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import create_approval, init_db, list_approvals, resolve_db_path


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
    for approval in approvals:
        note = f" - {approval['note']}" if approval.get("note") else ""
        typer.echo(
            f"#{approval['id']} asset #{approval['asset_id']} "
            f"{approval['status']}{note}"
        )
