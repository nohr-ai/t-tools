from __future__ import annotations
import canvasapi
from .file import File
from .terminal import TerminalView

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Static, ListView, ListItem, Footer
from textual.message import Message
from helperfunctions import (
    AdaptiveInput,
    MethodItem,
    get_logger,
    get_methods,
    hide,
    get_shell,
)

logger = get_logger(__name__)


class Assignment(Screen):
    BINDINGS = [
        ("escape", "go_back", "Go back to last screen"),
        ("h", "toggle_helptext", "Toggle help text"),
    ]
    CSS_PATH = "css/assignment.tcss"

    class Item(ListItem):
        def __init__(self, assignment: Assignment) -> None:
            super().__init__()
            self.assignment = assignment

        def compose(self) -> ComposeResult:
            yield Static(f"{self.assignment}")

        def as_assignment(self) -> Assignment:
            return self.assignment

    class Terminal(Message):
        def __init__(self, terminal: Screen):
            super().__init__()
            self.terminal = terminal

    def __init__(
        self, assignment: canvasapi.assignment.Assignment, student_id: int
    ) -> None:
        super().__init__()
        self.assignment = assignment
        self.student_id = student_id
        self.output = ""
        self._files = self.submission()

    def __str__(self) -> str:
        return f"{self.assignment.name} ({self.assignment.id})"

    def action_go_back(self) -> None:
        self.dismiss(True)

    @hide
    def as_item(self) -> Item:
        return self.Item(self)

    @hide
    def compose(self) -> ComposeResult:
        with Container(id="app-grid"):
            yield Static(f"{self.assignment}", id="sidebar")
            yield AdaptiveInput(get_methods(self), id="method-list")
            yield AdaptiveInput("", id="list-view")
            yield Footer()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, MethodItem):
            logger.debug(f"Highlighted method view: {event.item}")
            self.query_one("#list-view").update(event.item.method(self))
            logger.debug(f"{event.item.method}")
            event.stop()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, MethodItem):
            logger.debug(f"Selected method view: {event.item}")
            event.item.method(self)
            event.stop()

    @hide
    def submission(self) -> list[File]:
        s = self.assignment.get_submission(self.student_id)
        return [File(a) for a in s.attachments]

    def files(self) -> list[File]:
        return self._files

    def preview(self) -> None:
        self.post_message(Assignment.Terminal(TerminalView()))
