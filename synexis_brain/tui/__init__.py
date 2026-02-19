"""TUI package."""

__all__ = ["run_tui"]


def run_tui(db_path: str = "data/meta.db", config_path: str = "config.yaml") -> None:
    try:
        from synexis_brain.tui.app import run_tui as _run_tui
    except ModuleNotFoundError as exc:
        if exc.name == "textual":
            raise RuntimeError(
                "Missing dependency 'textual'. Install project dependencies with: pip install -e ."
            ) from exc
        raise

    _run_tui(db_path=db_path, config_path=config_path)
