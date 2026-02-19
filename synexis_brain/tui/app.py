from __future__ import annotations

import asyncio
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from synexis_brain.tui.backend import SearchFilters, SearchService


class ResultItem(ListItem):
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        title = f"{result['path']}#{result.get('heading') or ''}".strip("#")
        super().__init__(Label(title))


class SynexisApp(App):
    CSS = """
    Screen { layout: vertical; }
    #top { height: 3; }
    #filters { height: 3; }
    #body { height: 1fr; }
    #results { width: 45%; border: solid $accent; }
    #preview { width: 55%; border: solid $secondary; padding: 1; }
    """

    BINDINGS = [
        Binding("enter", "open_selected", "Open"),
        Binding("ctrl+r", "reindex", "Reindex"),
        Binding("c", "copy_citation", "Copy citation"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, db_path: str, config_path: str) -> None:
        super().__init__()
        self.service = SearchService(db_path=db_path, config_path=config_path)
        self.filters = SearchFilters()
        self._debounce_task: asyncio.Task[None] | None = None
        self._results: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="top"):
            yield Input(placeholder="Search (BM25)", id="search")
        with Horizontal(id="filters"):
            yield Input(placeholder="vault", id="vault")
            yield Input(placeholder="type", id="type")
            yield Input(placeholder="tag", id="tag")
            yield Input(placeholder="status", id="status")
        with Horizontal(id="body"):
            yield ListView(id="results")
            yield Static("No result", id="preview")
        yield Footer()

    async def on_mount(self) -> None:
        await self.action_reindex()

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "vault":
            self.filters.vault_id = event.value.strip()
        elif event.input.id == "type":
            self.filters.chunk_type = event.value.strip()
        elif event.input.id == "tag":
            self.filters.tag = event.value.strip()
        elif event.input.id == "status":
            self.filters.status = event.value.strip()

        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        self._debounce_task = asyncio.create_task(self._debounced_search())

    async def _debounced_search(self) -> None:
        await asyncio.sleep(0.2)
        query = self.query_one("#search", Input).value
        self._results = self.service.search(query=query, filters=self.filters)
        results = self.query_one("#results", ListView)
        results.clear()
        for result in self._results:
            await results.append(ResultItem(result))
        if self._results:
            self._update_preview(self._results[0])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, ResultItem):
            self._update_preview(item.result)

    def _update_preview(self, result: dict[str, Any]) -> None:
        preview = self.query_one("#preview", Static)
        content = [
            f"path: {result['path']}",
            f"heading: {result.get('heading') or '-'}",
            f"score: {result.get('score')}",
            "",
            result.get("preview") or "",
        ]
        preview.update("\n".join(content))

    async def action_reindex(self) -> None:
        changes = self.service.reindex()
        self.notify(
            f"Indexed new={changes['new']} changed={changes['changed']} deleted={len(changes['deleted'])}",
            title="Synexis",
        )

    async def action_open_selected(self) -> None:
        selected = self._selected_result()
        if not selected:
            return
        target = self.service.open_note_path(selected)
        self._open_external(target)

    async def action_copy_citation(self) -> None:
        selected = self._selected_result()
        if not selected:
            return
        citation = self.service.citation_for(selected)
        self._copy_to_clipboard(citation)
        self.notify(citation, title="Citation")

    def _selected_result(self) -> dict[str, Any] | None:
        results = self.query_one("#results", ListView)
        if results.index is None or results.index >= len(self._results):
            return None
        return self._results[results.index]

    def _copy_to_clipboard(self, text: str) -> None:
        if shutil.which("wl-copy"):
            subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=False)
            return
        if shutil.which("xclip"):
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=False)
            return
        if shutil.which("pbcopy"):
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=False)
            return

    def _open_external(self, path: str) -> None:
        if path.startswith("obsidian://"):
            if shutil.which("xdg-open"):
                subprocess.run(["xdg-open", path], check=False)
            return

        p = Path(path)
        if p.exists() and shutil.which("xdg-open"):
            subprocess.run(["xdg-open", str(p)], check=False)
            return

        uri = os.environ.get("SYNEXIS_OBSIDIAN_URI_PREFIX", "")
        if uri:
            url = f"{uri}{path}"
            if shutil.which("xdg-open"):
                subprocess.run(["xdg-open", url], check=False)


def run_tui(db_path: str = "data/meta.db", config_path: str = "config.yaml") -> None:
    app = SynexisApp(db_path=db_path, config_path=config_path)
    app.run()
