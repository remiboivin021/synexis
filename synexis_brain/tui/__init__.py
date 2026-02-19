"""TUI package."""

__all__ = ["run_tui"]


def run_tui(db_path: str = "data/meta.db", config_path: str = "config.yaml") -> None:
    from synexis_brain.tui.app import run_tui as _run_tui

    _run_tui(db_path=db_path, config_path=config_path)
