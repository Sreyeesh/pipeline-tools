"""CLI commands for DCC launcher."""

import click
from pathlib import Path
from .launcher import launch_dcc, get_dcc_executable


@click.command("open")
@click.argument("dcc_name", type=str)
@click.option(
    "--file", "-f",
    type=click.Path(exists=True),
    help="File to open in the DCC"
)
@click.option(
    "--project-root", "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Project root directory (defaults to current directory)"
)
@click.option(
    "--background", "-b",
    is_flag=True,
    help="Launch in background and return immediately"
)
@click.option(
    "--list-dccs", "-l",
    is_flag=True,
    help="List supported DCCs"
)
def open_dcc(
    dcc_name: str,
    file: str = None,
    project_root: str = None,
    background: bool = False,
    list_dccs: bool = False
):
    """
    Open a DCC application with optional file and project context.

    Examples:

        # Open Krita
        pipeline-tools open krita

        # Open Blender with a file
        pipeline-tools open blender --file 03_ASSETS/character.blend

        # Open Krita with a file from project root
        pipeline-tools open krita -f 02_PREPRO/designs/characters/design.kra -p /path/to/project

        # Launch in background
        pipeline-tools open krita --background
    """
    from pipeline_tools.tools.dcc_launcher.launcher import DCC_PATHS

    if list_dccs:
        click.echo("Supported DCCs:")
        for dcc in sorted(DCC_PATHS.keys()):
            click.echo(f"  - {dcc}")
        return

    # Default project root to current directory
    if not project_root:
        project_root = str(Path.cwd())

    # Check if DCC exists
    executable = get_dcc_executable(dcc_name)
    if not executable:
        click.echo(f"❌ Could not find {dcc_name}. Is it installed?", err=True)
        click.echo(f"\nSupported DCCs: {', '.join(sorted(DCC_PATHS.keys()))}")
        raise click.Abort()

    # Launch
    try:
        click.echo(f"🚀 Launching {dcc_name}...")
        if file:
            click.echo(f"   File: {file}")
        if project_root:
            click.echo(f"   Project: {project_root}")

        process = launch_dcc(
            dcc_name=dcc_name,
            file_path=file,
            project_root=project_root,
            background=background
        )

        if background:
            click.echo(f"✅ {dcc_name} launched in background (PID: {process.pid})")
        else:
            click.echo(f"✅ {dcc_name} launched. Waiting for exit...")
            process.wait()
            click.echo(f"   {dcc_name} closed.")

    except FileNotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error launching {dcc_name}: {e}", err=True)
        raise click.Abort()
