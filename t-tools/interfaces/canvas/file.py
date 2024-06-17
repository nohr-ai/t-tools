from __future__ import annotations
import os
import logging
import canvasapi
from logging.handlers import RotatingFileHandler
import inspect

from helperfunctions import AdaptiveInput, MethodItem, get_logger, get_methods, hide

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, ListView, ListItem, Label, Select, Input, Footer
from pypdf import PdfReader
import io


logger = get_logger(__name__)


class File(Screen):
    BINDINGS = [
        ("escape", "go_back", "Go back to last screen"),
        ("h", "toggle_helptext", "Toggle help text"),
    ]
    CSS_PATH = "css/file.tcss"

    class Item(ListItem):
        def __init__(self, file: File) -> None:
            super().__init__()
            self.file = file

        def compose(self) -> ComposeResult:
            yield Static(f"{self.file}")

        def as_file(self) -> File:
            return self.file

    def __init__(self, file: canvasapi.file.File) -> None:
        super().__init__()
        self.file = file
        self.output = ""

    def __str__(self) -> str:
        return f"{self.file.display_name} ({self.file.id})"

    @hide
    def as_item(self) -> Item:
        return self.Item(self)

    def action_go_back(self) -> None:
        self.dismiss(True)

    def compose(self) -> ComposeResult:
        with Container(id="app-grid"):
            yield Static(self.file.display_name, id="sidebar")
            yield AdaptiveInput(get_methods(self), id="method-list")
            yield AdaptiveInput("file", id="list-view")
            with VerticalScroll(id="config"):
                yield Input(placeholder="Download folder", id="download-location")
                yield Input(placeholder="File name", id="file-name")
            yield Footer()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, MethodItem):
            logger.debug(f"Highlighted method view: {event.item}")
            self.query_one("#list-view").update(event.item.method(self))

    def download(self, location: str = None) -> None:
        """
        Download the file to the specified location, defaults to 'downloads/<file-name>'
        """
        # TODO: Move this to startup
        os.makedirs("downloads", exist_ok=True)
        if location is None:
            location = f"downloads/{self.file.display_name}"
        logger.debug(f"Downloading to: {location}")
        self.file.download(location)

        return f"Downloaded to: {location}"

    @hide
    def read(self, file, binary: bool) -> str:
        match file.mime_class:
            case "pdf":
                pdf = PdfReader(io.BytesIO(file.get_contents(binary=True)))
                num_pages = pdf.get_num_pages()
                return "".join(
                    [pdf.get_page(i).extract_text() for i in range(num_pages)]
                )
            case _:
                return file.get_contents(binary=False)

    def content(self, binary=False) -> str | bytes:
        return self.read(self.file, binary=binary)
