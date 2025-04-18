import os
from typing import Iterable

from rich.segment import Segment
from textual import events
from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip

from ..utils import stream_stdout_and_stderr
import signal


class Logs(ScrollView):
    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
        )
        print(f"new logs name={name}")
        self.data = []
        self._require_update_dimensions: bool = False
        self._new_rows: set[int] = set()
        self._content_width = 0
        self._scroll_target = None

    def add_log(self, line, source=None):
        row_index = len(self.data)

        self.data.append(line)
        self._new_rows.add(row_index)
        self._require_update_dimensions = True
        self.check_idle()
        # self.update("\n".join(self.data))

    def on_idle(self) -> None:
        if self._require_update_dimensions:
            self._require_update_dimensions = False
            new_rows = self._new_rows.copy()
            self._new_rows.clear()
            self._update_dimensions(new_rows)
            if self._scroll_target is None:
                self.scroll_to(y=len(self.data) - 1, animate=False)
                self._refresh_scrollbars()

    def _update_dimensions(self, new_rows: Iterable[int]) -> None:
        """Called to recalculate the virtual (scrollable) size."""

        new_content_width = max([len(self.data[l]) for l in new_rows])
        self._content_width = max(new_content_width, self._content_width)
        self.virtual_size = Size(self._content_width, len(self.data))

    def render_line(self, y: int) -> Strip:
        width, height = self.size
        scroll_x, scroll_y = self.scroll_offset
        try:
            line = self.data[scroll_y + y]
        except IndexError:
            line = ""

        text = line[scroll_x: scroll_x + width]
        missing_len = max(0, width - len(text))

        return Strip([Segment(text + " " * missing_len, self.rich_style)])


class CommandLogger(Logs):
    def __init__(
        self,
        command,
        exit_message=True,
        exit_command=None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
        )
        self.command = command
        self.process = None
        self.data = []
        self._require_update_dimensions: bool = False
        self._new_rows: set[int] = set()
        self._content_width = 0
        self._scroll_target = None
        self._callback_timer = None
        self.exit_command = exit_command
        self.exit_message = exit_message
        self.can_focus = True

    async def on_mount(self) -> None:
        print("running self.command", self.command)
        self.add_log(f"running {self.command}")
        self.process = stream_stdout_and_stderr(self.command, callback=lambda a, b: self.add_log(b.strip(), source=a))
        self._callback_timer = self.set_interval(1, self.check_process, name="check_process")
        self.focus()

    def on_key(self, event: events.Key) -> None:
        # suppress any keys the parent uses - fix this to be dynamic
        if event.key not in ["x", "q", "t", "m", "l", "s", "r", "u", "d", "b", "ctrl+l", "ctrl+d", "ctrl+u", "ctrl+b"]:
            return

        event.stop()

    def on_unmount(self):
        if self.process:
            print("terminate", self.process.pid, self.process)
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception as e:
                print("Failed to kill", self.process, e)

    async def check_process(self):
        if not self.process:
            return

        return_code = self.process.poll()
        if return_code is not None:
            if self.exit_command:
                self.exit_command()

            self.add_log(f"process ended return_code={return_code}")
            if self.exit_message:
                self.add_log("Press escape to close")
            # self.process = None
            self._callback_timer.stop()
