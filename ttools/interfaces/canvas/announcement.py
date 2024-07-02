import canvasapi

from textual.screen import Screen


class Assignment(Screen):
    def __init__(self, assignment: canvasapi.assignment.Assignment) -> None:
        super().__init__()
        self._assignment = assignment
        self.helptext = ""
        self.toggle_helptext = True
        self.output = ""
