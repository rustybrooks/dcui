#!/usr/bin/env python
import os
from typing import Type

from textual import events
from textual.app import App, ComposeResult, CSSPathType
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.driver import Driver
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Footer, Header

from .components.docker_table import DockerComposeController
from .components.interactive_shell import InteractiveShell
from .components.logs import Logs, CommandLogger
from .components.panes import Panes
from .hooks import Hooks

global_loggers = []


def global_log(message, source=None):
    print("global log", message, global_loggers)
    for g in global_loggers:
        g.add_log(message, source=source)


class DebugScreen(Screen):
    def compose(self) -> ComposeResult:
        logger = Logs()
        global_loggers.append(logger)
        yield Header()
        yield logger
        yield Footer()


class DockerComposePanel(Vertical):
    # BINDINGS = (
    #     Binding("ctrl+right_square_bracket", "next_pane", "Next Pane", priority=True),
    # )

    docker_compose = None
    docker_composes = None

    def on_mount(self, _: events.Mount) -> None:
        self.docker_composes = [d for d in self.query(DockerComposeController)]

        if self.docker_composes:
            self.change_selected(self.docker_composes[0])
            self.docker_compose.watch_selected(True)

    def change_selected(self, new_selected):
        if self.docker_compose:
            self.docker_compose.selected = False

        self.docker_compose = new_selected
        self.docker_compose.selected = True
        self.docker_compose.focus()

    def action_next_pane(self):
        index = self.docker_composes.index(self.docker_compose)
        next_pane = self.docker_composes[(index + 1) % len(self.docker_composes)]
        self.change_selected(next_pane)

    def on_click(self, event: events.Click):
        clicked = self.screen.get_widget_at(event.screen_x, event.screen_y)[0]
        if isinstance(clicked, DockerComposeController):
            self.change_selected(clicked)
        elif clicked == self:
            self.docker_compose.focus()


class DockerScreen(Screen):
    BINDINGS = [
        # Binding("t", "toggle_panel", "Toggle Pane"),
        Binding("u", "service_up", "Up"),
        Binding("d", "service_down", "Down"),
        Binding("l", "service_logs", "Logs"),
        Binding("b", "service_build", "Build"),
        Binding("s", "service_shell", "Shell"),
        Binding("r", "service_run", "Run"),
        Binding("ctrl+u", "up", "Up all"),
        Binding("ctrl+d", "down", "Down all"),
        Binding("ctrl+l", "logs", "Logs all"),
        Binding("ctrl+b", "build", "Build all"),
        Binding("ctrl+right_square_bracket", "next_pane", "Next Pane"),
        Binding("tab", "next_pane", "Next Pane", show=False),
        Binding(key="escape", action="close_overlay", show=False, description="close overlay"),
        Binding("f2", "split_horizontal", "SplitX", priority=True),
        Binding("f3", "split_vertical", "SplitY", priority=True),
        Binding("ctrl+w", "remove_pane", "Remove", priority=True),
        Binding("ctrl+underscore", "swap_panel", "Swap", priority=True),
    ]
    logger = None
    show_panel = var(True)
    docker_compose_files = []
    docker_composes = []
    docker_compose = None
    container = None
    overlay = None
    action_running = False
    panel = None

    def __init__(self, action_hooks=None, skip_service_regex=None):
        super().__init__()
        self.action_hooks = action_hooks
        self.skip_service_regex = skip_service_regex

    def set_docker_compose_files(self, docker_compose_files):
        self.docker_compose_files = docker_compose_files

    def watch_show_panel(self, show_panel: bool) -> None:
        self.set_class(show_panel, "-show-panel")

    def compose(self) -> ComposeResult:
        self.container = Panes(id="container")
        self.overlay = Container(classes="overlay hide")
        self.panel = DockerComposePanel(
            *[
                DockerComposeController(
                    docker_file=df, logger=self.logger, skip_service_regex=self.skip_service_regex
                )
                for df in self.docker_compose_files
            ],
            id="panel-view",
        )

        yield Header()
        yield Horizontal(
            self.panel,
            self.container,
            self.overlay,
            id="horizontal",
        )

        yield Footer()

    # @classmethod
    # def on_key(cls, event: events.Key) -> None:
    #     print("on key DS", event)

    def action_swap_panel(self):
        if self.focused.__class__ in [DockerComposePanel, DockerComposeController]:
            print("swap to panes")
            self.container.pane_focus()
        else:
            print("swap to docker compose")
            self.panel.docker_compose.focus()

    def action_remove_pane(self):
        self.container.remove_pane()

    def action_split_horizontal(self):
        self.container.last_split = "horizontal"

    def action_split_vertical(self):
        self.container.last_split = "vertical"

    @classmethod
    def logger_callback(cls, source, text):
        global_log(text.strip(), source=source)

    def action_toggle_panel(self) -> None:
        self.show_panel = not self.show_panel

    async def action_service_logs(self) -> None:
        service = self.panel.docker_compose.selected_service
        self.container.add_pane(
            title=f"{service} logs",
            content=CommandLogger(
                self.panel.docker_compose.docker_compose.logs(services=[service]),
                exit_message=False,
            ),
        )
        global_log(f"log_command done {service}")

    async def action_service_shell(self) -> None:
        service = self.panel.docker_compose.selected_service
        self.container.add_pane(
            title=f"{service} shell",
            content=InteractiveShell(
                self.panel.docker_compose.docker_compose.shell(service),
                exit_message=False,
            ),
        )
        # await self.container.mount(InteractiveShell(["bash"]))

    async def action_close_overlay(self):
        await self.single_gated_action_stop()

    async def action_service_run(self) -> None:
        service = self.panel.docker_compose.selected_service
        self.container.add_pane(
            title=f"{service} run",
            content=InteractiveShell(
                self.panel.docker_compose.docker_compose.run(service), exit_message=False
            ),
        )

    def remove_temp_windows(self):
        for w in self.overlay.children:
            global_log(f"remove window {w}")
            w.remove()

    async def single_gated_action(self, content):
        if self.action_running:
            return

        self.overlay.set_class(False, "hide")
        self.action_running = True
        self.remove_temp_windows()
        await self.overlay.mount(content)

    async def single_gated_action_stop(self):
        self.action_running = False
        self.overlay.set_class(True, "hide")
        self.remove_temp_windows()

    def single_gated_service_exit(self):
        self.action_running = False

    async def action_service_up(self) -> None:
        service = self.panel.docker_compose.selected_service
        await self.single_gated_action(
            InteractiveShell(
                self.panel.docker_compose.docker_compose.up(services=[service], detach=True),
                exit_command=self.single_gated_service_exit(),
                focus=False,
                env=os.environ
                | {"PWD": os.path.dirname(self.panel.docker_compose.docker_file) + "/"},
            )
        )

    async def action_service_down(self) -> None:
        service = self.panel.docker_compose.selected_service
        await self.single_gated_action(
            InteractiveShell(
                self.panel.docker_compose.docker_compose.stop(services=[service]),
                exit_command=self.single_gated_service_exit(),
                focus=False,
                env=os.environ
                | {"PWD": os.path.dirname(self.panel.docker_compose.docker_file) + "/"},
            )
        )

    async def action_service_build(self) -> None:
        service = self.panel.docker_compose.selected_service
        await self.single_gated_action(
            CommandLogger(
                self.panel.docker_compose.docker_compose.build(
                    services=[service], with_password=True
                ),
                exit_command=self.single_gated_service_exit(),
            )
        )

    async def action_down(self) -> None:
        self.remove_temp_windows()
        await self.single_gated_action(
            InteractiveShell(
                self.panel.docker_compose.docker_compose.down(),
                exit_command=self.single_gated_service_exit(),
                focus=False,
                env=os.environ
                | {"PWD": os.path.dirname(self.panel.docker_compose.docker_file) + "/"},
            )
        )

    async def action_up(self):
        self.remove_temp_windows()
        self.action_hooks.execute("pre_up")
        await self.single_gated_action(
            InteractiveShell(
                self.panel.docker_compose.docker_compose.up(detach=True),
                exit_command=self.single_gated_service_exit(),
                focus=False,
                env=os.environ
                | {"PWD": os.path.dirname(self.panel.docker_compose.docker_file) + "/"},
            )
        )
        self.action_hooks.execute("post_up")

    async def action_build(self):
        self.remove_temp_windows()
        await self.single_gated_action(
            CommandLogger(
                self.panel.docker_compose.docker_compose.build(with_password=True),
                exit_command=self.single_gated_service_exit(),
            )
        )

    def action_next_pane(self):
        self.panel.action_next_pane()


class DCUIApp(App):
    CSS_PATH = "dcui.css"

    BINDINGS = [
        Binding(
            key="f1",
            action="switch_screen('docker')",
            description="Docker",
            show=False,
            priority=True,
        ),
        Binding(
            key="f12",
            action="switch_screen('debug')",
            description="Debug",
            show=False,
            priority=True,
        ),
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(
        self,
        docker_compose_files=None,
        driver_class: Type[Driver] | None = None,
        css_path: CSSPathType = None,
        watch_css: bool = False,
        hook_file=None,
        skip_service_regex=None,
    ):
        self.hook_file = hook_file
        self.debug_screen = DebugScreen()
        self.docker_screen = DockerScreen(action_hooks=None, skip_service_regex=skip_service_regex)
        self.docker_screen.set_docker_compose_files(docker_compose_files or [])
        self.action_hooks = Hooks(self.hook_file or None)

        self.SCREENS = {
            "debug": self.debug_screen,
            "docker": self.docker_screen,
        }

        super().__init__(driver_class=driver_class, css_path=css_path, watch_css=watch_css)

    def on_mount(self):
        self.docker_screen.action_hooks = self.action_hooks
        self.action_hooks.execute("pre_startup")

        self.push_screen(self.debug_screen)
        self.push_screen(self.docker_screen)

    def action_quit(self):
        global_log("quit")
        self.exit()
