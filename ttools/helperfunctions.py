from __future__ import annotations
import logging.handlers
import os
import sys
import psutil
import logging
from logging.handlers import RotatingFileHandler
import textual
from textual.widgets import Static, ListView, ListItem
from textual.app import ComposeResult
from textual.widget import Widget
from textual.containers import VerticalScroll
import builtins
import inspect

import textual.widgets
from textual.message import Message

logger = logging.getLogger(__name__)


def hide(func) -> builtins.function:
    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    inner.hidden = True
    return inner


def is_hidden(func) -> bool:
    return getattr(func, "hidden", False)


def get_shell() -> str:
    return psutil.Process(os.getpid()).parent().name()


def get_logger(
    name: str,
    log_level: int = logging.DEBUG,
    formatter=logging.Formatter | None,
) -> logging.Logger:
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    )
    logger = logging.getLogger(name)
    handler = RotatingFileHandler(
        "logs/" + os.getenv("LOG_FILE"), maxBytes=100000, backupCount=1
    )
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    logger.addHandler(handler)
    handler = RotatingFileHandler(
        "logs/" + os.getenv("LOG_DEBUG_FILE"), maxBytes=100000, backupCount=5
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.setLevel(log_level)
    logger.propagate = False
    return logger


class MethodItem(ListItem):
    def __init__(self, label: str, method: builtins.classmethod) -> None:
        super().__init__()
        self.label = label
        self.method = method

    def compose(self) -> ComposeResult:
        yield Static(self.label)

    def as_item(self) -> MethodItem:
        return self


class MethodView(ListView):
    def __init__(self, *items: MethodItem) -> None:
        super().__init__(*items)


class AdaptiveInput(Widget, can_focus=True):
    def __init__(
        self,
        arg: any,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.arg = arg

    class DictItem(ListItem):
        def __init__(self, key: str, value: any) -> None:
            super().__init__()
            self.key = key
            self.value = value

        def compose(self) -> ComposeResult:
            yield Static(f"{self.key}")

    def compose(self) -> ComposeResult:
        match type(self.arg):
            case builtins.list:
                yield self.list_to_listview(self.arg)
            case builtins.dict:
                yield self.dict_to_listview(self.arg)
            case _:
                yield VerticalScroll(Static(str(self.arg)))

    def update(self, arg):
        self.arg = arg
        self.query().remove()
        new = next(self.compose())
        await_new = self.mount(new)
        return await_new

    def dict_to_listview(self, arg: dict) -> ListView:
        return ListView(*[self.DictItem(k, v) for k, v in arg.items()])

    def list_to_listview(self, values: list) -> ListView:
        if not values:
            return ListView()
        return ListView(*[value.as_item() for value in values])


def get_methods(
    obj: object, exclude_list: list[str] = []
) -> list[builtins.classmethod]:
    """
    probably a cleaner way to do this _        _
                                        \_(ツ)_/
    """
    to_exclude = [
        name
        for name, _ in inspect.getmembers(
            obj.__class__.__base__, predicate=inspect.isfunction
        )
    ] + exclude_list
    logger.debug(f"Excluding {to_exclude}")
    attributes = dir(obj)
    methods = []
    for attr in attributes:
        if (
            attr not in to_exclude
            and not attr.startswith("_")
            and not attr.startswith("action_")
            and not attr.startswith("on_")
        ):
            try:
                attr_val = inspect.getattr_static(obj, attr)
                if (
                    not inspect.isclass(attr_val)
                    and not is_hidden(attr_val)
                    and callable(attr_val)
                ):
                    methods.append(MethodItem(attr, attr_val))
            except Exception:
                continue
    return methods


class TestMessage(Message):
    def __init__(self, message: str):
        super().__init__()
        self.message = message
