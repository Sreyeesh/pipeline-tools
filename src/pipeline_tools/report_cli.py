from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import init_db, report_summary, resolve_db_path


app = typer.Typer(help="Production reports.")


@app.command("summary")
def cmd_summary(
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    summary = report_summary(db_path)
    counts = summary["counts"]
    typer.echo(
        "Totals: "
        f"{counts['projects']} projects, "
        f"{counts['shots']} shots, "
        f"{counts['assets']} assets, "
        f"{counts['tasks']} tasks, "
        f"{counts['approvals']} approvals, "
        f"{counts['schedules']} schedules"
    )

    asset_status = summary["asset_status"]
    task_status = summary["task_status"]
    if asset_status:
        typer.echo("Assets by status:")
        for status, count in sorted(asset_status.items()):
            typer.echo(f"  {status}: {count}")
    if task_status:
        typer.echo("Tasks by status:")
        for status, count in sorted(task_status.items()):
            typer.echo(f"  {status}: {count}")
