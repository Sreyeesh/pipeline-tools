from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import create_asset, init_db, list_assets, resolve_db_path


app = typer.Typer(help="Track assets in the local database.")


@app.command("add")
def cmd_add(
    name: str = typer.Option(..., "--name", "-n", help="Asset name."),
    asset_type: str = typer.Option(..., "--type", "-t", help="Asset type (character/prop/env/etc)."),
    status: str = typer.Option("todo", "--status", "-s", help="Asset status."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    asset_id = create_asset(db_path, name=name, asset_type=asset_type, status=status)
    typer.echo(f"Added asset #{asset_id}: {name} ({asset_type}, {status})")


@app.command("list")
def cmd_list(
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    assets = list_assets(db_path)
    if not assets:
        typer.echo("No assets yet.")
        raise typer.Exit()
    for asset in assets:
        typer.echo(
            f"#{asset['id']} {asset['name']} "
            f"({asset['asset_type']}, {asset['status']})"
        )
