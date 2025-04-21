from __future__ import annotations

import re

from textual.reactive import Reactive
from textual.widgets import DataTable

from .logs import Logs
from ..docker_compose import DockerCompose


def format_port(port):
    if port["PublishedPort"]:
        source = f"{port['URL']}:{port['PublishedPort']}->"
    else:
        source = ""
    return f"{source.replace('0.0.0.0:', '').replace(':::', '')}{port['TargetPort']}"


class DockerComposeController(DataTable):
    DEFAULT_CSS = """
        DockerComposeController {
            border: solid $secondary-darken-3;

            width: 100%;
            height: auto;
        }

        DockerComposeController.selected {
            border: solid $accent;
            background: $accent 30%;
        }
    """

    # BINDINGS = [
    #     ("m", "toggle_columns()", "Toggle"),
    # ]

    selected = Reactive(False)

    def __init__(
        self,
        docker_file: str | None = None,
        logger: Logs | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        skip_service_regex: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            cursor_type="row",
            zebra_stripes=True,
            cursor_foreground_priority="renderable",
        )
        self.skip_service_regex = skip_service_regex
        self.logger = logger
        self.docker_file = docker_file
        self.docker_compose_parsed = {}
        self.docker_compose = DockerCompose(docker_file)
        self.selected_service = None

        self.column_sets = [
            ["service", "status", "ports"],
            ["service", "status", "name", "command", "ports"],
        ]
        self.column_set_index = 0

        for column in self.column_sets[0]:
            self.add_column(column, key=column)

    def __repr__(self):
        return f"DockerComposeController(name={self.name}, file={self.docker_file})"

    def watch_selected(self, selected: bool) -> None:
        print("watch selected", selected)
        self.set_class(selected, "selected")
        self._clear_caches()

    # def action_toggle_columns(self):
    #     self.column_set_index = (self.column_set_index + 1) % len(self.column_sets)
    #     self.display_columns = self.column_sets[self.column_set_index]
    #     self.refresh()
    #     self._clear_caches()

    def on_mount(self) -> None:
        # self.add_columns("service", "status", "name", "command", "ports")
        # self.display_columns = self.column_sets[self.column_set_index]
        self.call_later(self.load_docker)
        self.call_later(self.update_docker_ps)
        self.set_interval(5, self.update_docker_ps)

    def load_docker(self):
        data = self.docker_compose.load_docker_compose(self.docker_file)
        self.docker_compose_parsed = data
        rows = [
            [self.docker_compose_parsed["services"][x].get("container_name", x), "", ""]
            for x in self.docker_compose_parsed["services"]
            if not self.skip_service_regex
            or not re.search(self.skip_service_regex, x, flags=re.IGNORECASE)
        ]
        self.selected_service = rows[0][0]
        self.add_rows(rows)

    async def update_docker_ps(self):
        data = await self.docker_compose.ps()

        row_map = {}
        for k, row in self.rows.items():
            row_map[self.get_cell(k, "service")] = k
            self.update_cell(k, "status", "")

        for el in data:
            service = el["Name"]

            if service in row_map:
                self.update_cell(row_map[service], "status", el["State"])
                self.update_cell(
                    row_map[service],
                    "ports",
                    " ".join(sorted(set([format_port(p) for p in el["Publishers"] or []]))),
                )
                # self.update_cell(row_map[service], "name", el["Name"])
                # self.update_cell(row_map[service], "command",el["Command"][:20])
                # self.update_cell(row_map[service], "port", " ".join([format_port(p) for p in el["Publishers"] or []]))

        self._require_update_dimensions = True
        self.refresh()
        self._clear_caches()

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        self.selected_service = self.get_cell(message.row_key, "service")
