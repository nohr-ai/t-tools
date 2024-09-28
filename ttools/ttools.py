from __future__ import annotations
import os
import subprocess

# Before loading any user-defined modules, load the .env file
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
from interfaces.canvas.canvas import Canvas
from interfaces.home.home import Home
from interfaces.canvas.student import Student
from interfaces.canvas.assignment import Assignment

from helperfunctions import get_logger
from filesystem import FS
import builtins
from textual.app import App
from textual import on
from textual.message import Message

from helperfunctions import TestMessage

logger = get_logger(__name__)


class TATools(App):
    """
    Starting point for TUI
    """

    BINDINGS = [
        ("ctrl+z", "suspend_process", "suspend"),
        ("q", "quit", "quit"),
    ]
    MODES = {
        "Home": Home,
        "Canvas": Canvas,
    }

    def __init__(self):
        super().__init__()
        self._setup_folders()
        self.fss: dict[str : subprocess.Popen] = {}
        # self.fss: list[str] = []

    def _setup_folders(self):
        """
        God forbid, remove me asap
        """
        os.makedirs("./logs", exist_ok=True)

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

    def on_fs_request(self, event: FS.Request) -> None:
        logger.debug(f"fs req: {event}")

    def on_assignment_fs_request(self, event: Assignment.Test) -> None:
        logger.debug(f"Event: {event}")

    def handle_message(self, message):
        logger.debug(f"Message: {message}")

    def on_assignment_request(self, event: FS.Request) -> None:
        logger.debug(
            f"FS Request: {event.requestor}:{event.id}:{event.mount_point}:{event.root}"
        )
        # if not event.mount_point.startswith("./"):
        #     event.requestor.post_message(
        #         FS.Response(
        #             event.id,
        #             FS.Status(
        #                 event.id, False, ValueError("Mount point must start with ./")
        #             ),
        #         )
        #     )
        #     return
        # logger.debug(f"{list(self.fss.keys())}")
        # for mountpoint in self.fss:
        #     logger.debug(f"{mountpoint}, {event.mount_point}")
        #     if mountpoint.startswith(event.mount_point):
        #         logger.debug(f"Already mounted {mountpoint}")
        #         return

        # self.fss[event.mount_point] =
        # fs = FS(
        #     self,
        #     dash_s_do="whine",
        #     root=event.root,
        #     mountpoint=event.mount_point,
        #     nonempty=True,
        # )
        logger.debug(event.id)
        self.fss[event.mount_point] = subprocess.Popen(
            [
                "python3",
                "filesystem.py",
                "--root",
                f"{event.root}",
                "--mountpoint",
                f"{event.mount_point}",
                "--nonempty",
            ]
        )
        event.requestor.post_message(FS.Response(event.id, FS.Status(event.id, True)))
        logger.debug(f"Request:{event.id} OK")

    def my_shutdown(self):
        logger.debug("My own shutdown")
        cwd = os.getcwd()
        for mount_point in self.fss.keys():
            # for mount_point in self.fss:
            logger.debug(f"umount {mount_point}")
            if mount_point.startswith("/"):
                os.system(f"fusermount -u {mount_point}")
            else:
                logger.debug(f"{cwd}/{mount_point}")
                os.system(f"fusermount -u {cwd}/{mount_point}")

    def my_run(self):
        try:
            self.run()
        finally:
            self.my_shutdown()


if __name__ == "__main__":
    TATools().my_run()
