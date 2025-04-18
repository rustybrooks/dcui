import asyncio
import os
import pty
import select
import signal
import subprocess

import pyte
from textual import events
from textual.app import App
from textual.content import Content
from textual.widgets import Static


class InteractiveShell(Static):
    _screen = None
    _stream = None
    _pty = _tty = None

    DEFAULT_CSS = """
    InteractiveShell {
        width: 100%;
        height: 100%;
    }"""

    def __init__(
        self,
        command,
        exit_command=None,
        exit_message=True,
        focus=True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            "",
            name=name,
            id=id,
            classes=classes,
        )
        self.command = command
        self.exit_command = exit_command
        self.exit_message = exit_message
        self._focus = focus
        self.process = None

    async def on_mount(self):
        if self._focus:
            self.focus()
            self.can_focus = True
        self.call_later(self._run)

    def on_key(self, event: events.Key) -> None:
        print("onkey", event.key)
        if event.key in ["ctrl+]", "ctrl+_"]:
            return
        elif event.character:
            os.write(self._pty, event.character.encode("utf-8"))
        elif event.key == "up":
            os.write(self._pty, "".join([chr(0x1B), chr(0x5B), chr(0x41)]).encode("utf-8"))
        elif event.key == "down":
            os.write(self._pty, "".join([chr(0x1B), chr(0x5B), chr(0x42)]).encode("utf-8"))
        elif event.key == "left":
            os.write(self._pty, "".join([chr(0x1B), chr(0x5B), chr(0x44)]).encode("utf-8"))
        elif event.key == "right":
            os.write(self._pty, "".join([chr(0x1B), chr(0x5B), chr(0x43)]).encode("utf-8"))

        event.stop()

    def on_unmount(self):
        print("unmount?")
        if self.process:
            print("terminate", self.process.pid, self.process)
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception as e:
                print("Failed to kill", self.process, e)

    async def _run(self):
        print("run", self.command)
        self._pty, self._tty = pty.openpty()
        self.process = subprocess.Popen(
            self.command,
            stdin=self._tty,
            stdout=self._tty,
            stderr=self._tty,
            start_new_session=True,
        )
        self._screen = pyte.Screen(self.size[1], self.size[0])
        self._stream = pyte.Stream(self._screen)
        print("await run_check")
        await self._run_check()

    async def _run_check(self):
        return_code = self.process.poll()
        if return_code is not None:
            print("process is gone, quitting")
            if self.exit_command:
                self.exit_command()

            exit_message = [
                f"process ended return_code={return_code}",
            ]
            if self.exit_message:
                exit_message += ["Press escape to close"]

            print(exit_message)
            screen = [x for x in self._screen.display if x.strip()] + exit_message
            print(screen)
            self.update(Content("\n".join(screen)))
            self.refresh()
            return

        r, _, _ = select.select([self._pty], [], [], 0)
        if self._pty in r:
            output = os.read(self._pty, 10240)

            w, h = self.size
            if self._screen.columns != w or self._screen.lines != h:
                self._screen.resize(h, w)

            # print(repr(self._screen.buffer))

            self._stream.feed(output.decode())
            self.update(Content("\n".join(self._screen.display)))
            self._screen.dirty.clear()
        else:
            await asyncio.sleep(1 / 100.0)

        self.call_later(self._run_check)


class TestApp(App):
    def compose(self):
        yield InteractiveShell(["vi"], self.exit)


if __name__ == "__main__":
    a = TestApp()
    a.run()
