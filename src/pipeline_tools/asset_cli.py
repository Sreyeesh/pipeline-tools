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
    project_id: int | None = typer.Option(None, "--project-id", "-p", help="Project ID."),
    shot_id: int | None = typer.Option(None, "--shot-id", help="Shot ID."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    asset_id = create_asset(
        db_path,
        name=name,
        asset_type=asset_type,
        status=status,
        project_id=project_id,
        shot_id=shot_id,
    )
    location = ""
    if project_id or shot_id:
        location = f" [project {project_id or '-'}, shot {shot_id or '-'}]"
    typer.echo(f"Added asset #{asset_id}: {name} ({asset_type}, {status}){location}")


@app.command("list")
def cmd_list(
    project_id: int | None = typer.Option(None, "--project-id", "-p", help="Filter by project ID."),
    shot_id: int | None = typer.Option(None, "--shot-id", help="Filter by shot ID."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    assets = list_assets(db_path, project_id=project_id, shot_id=shot_id)
    if not assets:
        typer.echo("No assets yet.")
        raise typer.Exit()
    for asset in assets:
        location = ""
        if asset.get("project_id") or asset.get("shot_id"):
            location = f" [project {asset.get('project_id') or '-'}, shot {asset.get('shot_id') or '-'}]"
        typer.echo(
            f"#{asset['id']} {asset['name']} "
            f"({asset['asset_type']}, {asset['status']}){location}"
        )
