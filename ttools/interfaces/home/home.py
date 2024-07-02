from __future__ import annotations
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Header, ListView, ListItem, Static
from textual.message import Message

from helperfunctions import get_logger
from textual import on
from helperfunctions import TestMessage
from ..canvas import Canvas

logger = get_logger(__name__)


# FIXME: Cleanup needed
class Item(ListItem):
    def __init__(self, label: str, item: object) -> None:
        super().__init__()
        self.label = label
        self.item = item

    def compose(self) -> ComposeResult:
        yield Static(self.label)


class Home(Screen):
    """
    Starting point for TUI, dashboard/main menu
    """

    # FIXME: Cleanup needed
    class Interface(ListItem):
        def __init__(self, label: str) -> None:
            super().__init__()
            self.label = label

        def compose(self) -> ComposeResult:
            yield Static(self.label)

    # FIXME: Cleanup needed
    class InterfaceMessage(Message):
        def __init__(self, module: str):
            super().__init__()
            self.module = module

    CSS_PATH = "css/home.tcss"
    TITLE = "T-tools"
    SUB_TITLE = "Canvas GUI No More"
    BINDINGS = [
        ("ctrl+z", "suspend_process", "suspend"),
        ("q", "quit", "quit"),
    ]

    def __init__(self):
        super().__init__()

        self.modules = ["Canvas"]

    def compose(self) -> ComposeResult:
        with Container(id="app-grid"):
            yield Header(show_clock=True)
            yield Static(self.__class__.__qualname__, id="sidebar")
            yield ListView(
                *[self.Interface(name) for name in self.modules],
                id="interface-list",
            )

    def on_canvas_course(self, event: Canvas.Course) -> None:
        logger.debug(f"Canvas selected: {event.course}")
        self.push_screen(event.course)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, Home.Interface):
            logger.debug(f"Interface selected: {event.item}")
            self.post_message(self.InterfaceMessage(event.item.label))
        else:
            logger.exception(ValueError(f"Unknown item type:{type(event.item)}"))

    @on(TestMessage)
    def my_test(self, event):
        logger.debug("home recv test message")
