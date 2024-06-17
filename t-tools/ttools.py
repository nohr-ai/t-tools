from __future__ import annotations

# Before loading any user-defined modules, load the .env file
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
from interfaces.canvas.canvas import Canvas
from interfaces.home.home import Home
from interfaces.canvas.student import Student
from interfaces.canvas.assignment import Assignment

from helperfunctions import get_logger

import builtins
from textual.app import App


logger = get_logger(__name__)


class TATools(App):
    """
    Starting point for TUI
    """

    BINDINGS = [
        ("ctrl+z", "suspend_process", "suspend"),
        ("q", "quit", "quit"),
        ("t", "toggle_dark", "Toggle dark mode"),
    ]
    MODES = {
        "Home": Home,
        "Canvas": Canvas,
    }

    def __init__(self):
        super().__init__()

    def on_mount(self) -> None:
        self.switch_mode("Home")

    def on_canvas_home(self) -> None:
        self.switch_mode("Home")

    def on_canvas_course(
        self, event: list[Canvas.Course, builtins.classmethod]
    ) -> None:
        logger.debug(f"Pushing course: {event.course}")
        self.push_screen(event.course, event.callback)

    def on_course_student(self, event: Canvas.StudentMessage) -> None:
        logger.debug(f"Pushing student: {event.student}")
        self.push_screen(event.student, event.callback)

    def on_student_file(self, event: Student.File):
        logger.debug(f"Pushing file: {event.file}")
        self.push_screen(event.file, event.callback)

    def on_student_assignment(self, event: Student.Assignment):
        logger.debug(f"Pushing assignment: {event.assignment}")
        self.push_screen(event.assignment, event.callback)

    def on_home_interface_message(self, event: Home.InterfaceMessage) -> None:
        logger.debug(f"Pushing interface: {event.module}")
        self.switch_mode(event.module)

    def on_assignment_terminal(self, event: Assignment.Terminal) -> None:
        logger.debug(f"Pushing terminal: {event.terminal}")
        self.push_screen(event.terminal)


if __name__ == "__main__":
    TATools().run()
