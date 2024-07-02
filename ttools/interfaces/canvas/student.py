from __future__ import annotations
import os
import logging
import canvasapi
from logging.handlers import RotatingFileHandler
import inspect

from helperfunctions import AdaptiveInput, MethodItem, get_logger, get_methods, hide
from .assignment import Assignment
from .file import File


from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, ListView, ListItem, Label, Select, Input, Footer
from textual.message import Message

import builtins

logger = get_logger(__name__)


class Student(Screen):
    BINDINGS = [
        ("escape", "go_back", "Go back to course"),
        ("h", "toggle_helptext", "Toggle help text"),
    ]
    CSS_PATH = "css/student.tcss"

    class Item(ListItem):
        def __init__(self, student: Student) -> None:
            super().__init__()
            self.student = student

        def compose(self) -> ComposeResult:
            yield Static(f"{self.student}")

        def as_student(self) -> Student:
            return self.student

    class File(Message):
        def __init__(self, file: File, callback: builtins.classmethod) -> None:
            super().__init__()
            self.file = file
            self.callback = callback

    class Assignment(Message):
        def __init__(
            self, assignment: Assignment, callback: builtins.classmethod
        ) -> None:
            super().__init__()
            self.assignment = assignment
            self.callback = callback

    def __init__(self, student: canvasapi.user.User, course_id: int) -> None:
        super().__init__()
        self.student = student
        self.course_id = course_id
        self.profile = None
        self.output = ""
        self.highlighted_method = None

    def __str__(self) -> str:
        if self.profile:
            return f"{self.profile['name']}\n{self.profile['id']}\n{self.profile['login_id']}"
        return f"{self.student}"

    @hide
    def get_profile(self) -> dict | None:
        if not self.profile:
            try:
                return self.student.get_profile()
            except canvasapi.exceptions.Forbidden as cf:
                logger.exception(cf)
                return None

    @hide
    def as_item(self) -> ListItem:
        return self.Item(self)

    @hide
    def compose(self) -> ComposeResult:
        if not self.profile:
            self.get_profile()
        with Container(id="app-grid"):
            yield Static(str(self), id="sidebar")
            yield AdaptiveInput(get_methods(self), id="method-list")
            yield AdaptiveInput("", id="list-view")
            yield Footer()

    def action_go_back(self) -> None:
        logger.debug(f"Going back from {self.__class__.__qualname__}")
        self.dismiss(True)

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
        logger.debug(f"Selected: {type(event.item)}")
        if isinstance(event.item, File.Item):
            self.post_message(self.File(event.item.as_file(), self.update))
            event.stop()
        elif isinstance(event.item, Assignment.Item):
            self.post_message(self.Assignment(event.item.as_assignment(), self.update))
            event.stop()

    def assignments(self) -> list[Assignment]:
        return [
            Assignment(assignment, self.student.id)
            for assignment in self.student.get_assignments(self.course_id)
        ]

    def files(self) -> list[File]:
        try:
            return [File(file) for file in self.student.get_files()]
        except canvasapi.exceptions.Forbidden as cf:
            logger.exception(cf)
            return "Unauthorized"
