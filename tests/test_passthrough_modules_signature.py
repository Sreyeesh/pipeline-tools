import pytest

from pipeline_tools.tools.assets import main as assets_main
from pipeline_tools.tools.character_thumbnails import main as ct_main
from pipeline_tools.tools.shots import main as shots_main
from pipeline_tools.tools.shows import main as shows_main
from pipeline_tools.tools.tasks import main as tasks_main
from pipeline_tools.tools.versions import main as versions_main
from pipeline_tools.tools.workfiles import main as workfiles_main


@pytest.mark.parametrize(
    "module_main",
    [
        shows_main.main,
        shots_main.main,
        assets_main.main,
        tasks_main.main,
        versions_main.main,
        ct_main.main,
        workfiles_main.main,
    ],
)
def test_argparse_modules_accept_argv_and_help(module_main) -> None:
    """
    Guard against TypeError when Typer passthrough forwards argv lists.
    Each module main should accept an argv list and exit cleanly on --help.
    """
    with pytest.raises(SystemExit) as excinfo:
        module_main(["--help"])
    assert excinfo.value.code == 0
