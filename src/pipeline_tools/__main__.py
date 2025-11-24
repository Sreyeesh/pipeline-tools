"""Allow `python -m pipeline_tools` to run the Typer app."""
from pipeline_tools.cli import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
