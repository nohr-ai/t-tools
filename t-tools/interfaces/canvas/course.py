from __future__ import annotations
import os
import logging
import canvasapi
from logging.handlers import RotatingFileHandler
import inspect
import builtins
from helperfunctions import (
    AdaptiveInput,
    MethodItem,
    MethodView,
    get_logger,
    get_methods,
    hide,
)
from .student import Student
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, ListView, ListItem, Label, Select, Input, Footer
from textual.message import Message
from textual.widget import Widget
from cachetools import cached, TTLCache

logger = get_logger(__name__)


class Course(Screen):
    BINDINGS = [
        ("escape", "go_back", "Go back"),
        ("h", "toggle_helptext", "Toggle help text"),
    ]
    CSS_PATH = "css/course.tcss"

    class Item(ListItem):
        def __init__(self, course: Course) -> None:
            super().__init__()
            self.course = course

        def compose(self) -> ComposeResult:
            yield Static(f"{self.course}")

        def as_course(self) -> Course:
            return self.course

    class Student(Message):
        def __init__(
            self, student: Student, callback: builtins.classmethod = None
        ) -> None:
            super().__init__()
            self.student = student
            self.callback = callback

    def __init__(self, course: canvasapi.course.Course) -> None:
        super().__init__()
        self._course = course
        self._id = course.id
        self._name = course.name
        self.filter = ["compose"]
        self.output = ""
        self.highlighted_method = None

    def __str__(self) -> str:
        return f"{self._course.name} ({self._course.id})"

    @hide
    def as_item(self) -> ListItem:
        return self.Item(self)

    @hide
    def compose(self) -> ComposeResult:
        logger.debug(f"Composing {self.__class__.__qualname__}")
        with Container(id="app-grid"):
            yield Static(f"{self._course.name}", id="sidebar")
            yield AdaptiveInput(get_methods(self), id="method-list")
            yield AdaptiveInput("", id="list-view")
            yield Footer()

    @hide
    def action_go_back(self) -> None:
        self.dismiss(self._course.id)

    @hide
    def update(self, _) -> None:
        self.query_one("#list-view").update(self.highlighted_method(self))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, MethodItem):
            logger.debug(f"Highlighted: {event.item}")
            self.highlighted_method = event.item.method
            self.query_one("#list-view").update(event.item.method(self))
            event.stop()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, MethodItem):
            logger.debug(f"Selected: {event.item}")
            event.stop()
        elif isinstance(event.item, Student.Item):
            logger.debug(f"Selected student: {event.item}")
            self.post_message(self.Student(event.item.student, self.update))
            event.stop()
        else:
            logger.debug(f"Selected not instance: {event.item}")

    def _get_users(self, enrollment_type: str) -> list[Student]:
        return [
            Student(student, self._course.id)
            for student in self._course.get_users(enrollment_type=enrollment_type)
        ]

    def staff(self) -> list[Student] | str:
        """
        Fetch a list of all staff in a course

        Parameters:
        -----------
            None

        Returns:
        --------
            Staff: list[[name:str,id:int]]
                List of staff
        """
        try:
            return self._get_users("teacher")
        except canvasapi.exceptions.Forbidden as cf:
            logger.exception(cf)
            return "Unauthorized"

    def students(self) -> list[Student]:
        """
        Fetch a list of all students in a course

        Parameters:
        -----------
            None

        Returns:
        --------
            Students: list[[name:str,id:int]]
                List of students
        """
        try:
            return self._get_users("student")
        except canvasapi.exceptions.Forbidden as cf:
            logger.exception(cf)
            return "Unauthorized"
