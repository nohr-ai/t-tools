from __future__ import annotations
import os
import types
import logging
from logging.handlers import RotatingFileHandler
import canvasapi
import inspect
from .course import Course
from helperfunctions import AdaptiveInput, get_logger
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, ListView, ListItem, Label, Select, Input
from textual.message import Message
import builtins

logger = get_logger(__name__)


class Canvas(Screen):
    """
    Canvas API Wrapper
    Main object for interacting with the Canvas API

    REQUIRES:
    ---------
    CANVAS_URL & CANVAS_TOKEN environment variables
    """

    class Course(Message):
        def __init__(self, course: Course, callback: builtins.classmethod):
            super().__init__()
            self.course = course
            self.callback = callback

    class CourseListItem(ListItem):
        def __init__(self, course: Course) -> None:
            super().__init__()
            self.course_name = course._name
            self.course_id = course._id
            self.course = course

        def compose(self) -> ComposeResult:
            yield Static(f"{self.course}")

    class CourseList(ListView):
        def __init__(self, *items: Canvas.CourseListItem) -> None:
            super().__init__(*items)

    BINDINGS = [
        ("escape", "home", "Go to home screen"),
        ("h", "toggle_helptext", "Toggle help text"),
    ]
    CSS_PATH = "css/canvas.tcss"

    class Home(Message):
        def __init__(self):
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self._handle = canvasapi.Canvas(
            os.getenv("CANVAS_URL"), os.getenv("CANVAS_TOKEN")
        )
        self.courses = self.get_courses()

    def compose(self) -> ComposeResult:
        with Container(id="app-grid"):
            yield Static(f"{self.__class__.__qualname__}", id="sidebar")
            yield AdaptiveInput(list(self.courses.values()), id="list-view")

    def action_home(self) -> None:
        self.post_message(self.Home())

    def update(self, course_id) -> None:
        self.courses[course_id] = Course(self._handle.get_course(course_id))

    def get_courses(self) -> dict[int, Course]:
        """
        Fetch a list of all courses

        Parameters:
        -----------
            None

        Returns:
        --------
            Courses: list[[name:str,id:int]]
                List of courses
        """
        return {course.id: Course(course) for course in self._handle.get_courses()}

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, Canvas.CourseListItem):
            event.stop()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, Course.Item):
            logger.debug(
                f"Selected course of type {Canvas.CourseListItem}: {event.item}"
            )
            self.post_message(
                self.Course(self.courses[event.item.course.id], self.update)
            )
            event.stop()
