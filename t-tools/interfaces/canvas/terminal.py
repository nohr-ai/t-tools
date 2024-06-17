from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Placeholder
from helperfunctions import get_shell, get_logger

from _terminal import Terminal

logger = get_logger(__name__)


class TerminalView(Screen):
    def compose(self) -> ComposeResult:
        yield Placeholder("Terminal", id="terminal")

    def detach_terminal(self) -> None:
        try:
            t = self.query_one("#terminal")
            t.stop()
            t.remove()
            self.query_one("#terminal").mount(Placeholder("Terminal", id="terminal"))
        except Exception as e:
            logger.exception(e)
            logger.debug("no matches:", "#terminal")
            return

    def start_terminal(self) -> None:
        try:
            self.query_one("#terminal").remove()
            self.app.mount(Terminal(command=f"{get_shell()}", id="terminal"))
            terminal: Terminal = self.app.query_one("#terminal")
            terminal.start()
        except Exception as e:
            logger.exception(e)
            return

    def on_mount(self) -> None:
        self.start_terminal()

    def on_terminal_started(self, event: Terminal.Started) -> None:
        logger.debug("terminal started:", event)

    def on_terminal_stopped(self, event: Terminal.Stopped) -> None:
        logger.debug("terminal stopped:", event)
        self.detach_terminal()
        self.app.pop_screen()
