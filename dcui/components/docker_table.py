from __future__ import annotations

from textual.reactive import Reactive
from textual.widgets import DataTable

from .logs import Logs
from ..docker_compose import DockerCompose


# CursorType = Literal["cell", "row", "column"]
# CELL: CursorType = "cell"
# CellType = TypeVar("CellType")


def format_port(port):
    if port["PublishedPort"]:
        source = f"{port['URL']}:{port['PublishedPort']}->"
    else:
        source = ""
    return f"{source}{port['TargetPort']}/{port['Protocol']}"


# def default_cell_formatter(obj: object) -> RenderableType | None:
#     """Format a cell in to a renderable.
#
#     Args:
#         obj (object): Data for a cell.
#
#     Returns:
#         RenderableType | None: A renderable or None if the object could not be rendered.
#     """
#     if isinstance(obj, str):
#         return Text.from_markup(obj)
#     if not is_renderable(obj):
#         return None
#     return cast(RenderableType, obj)


# @dataclass
# class Column:
#     """Table column."""
#
#     label: Text
#     width: int = 0
#     visible: bool = False
#     index: int = 0
#
#     content_width: int = 0
#     auto_width: bool = False
#
#     @property
#     def render_width(self) -> int:
#         """Width in cells, required to render a column."""
#         # +2 is to account for space padding either side of the cell
#         if self.auto_width:
#             return self.content_width + 2
#         else:
#             return self.width + 2
#
#
# @dataclass
# class Row:
#     """Table row."""
#
#     index: int
#     height: int
#     y: int
#     cell_renderables: list[RenderableType] = field(default_factory=list)


# class DockerTable(ScrollView, Generic[CellType], can_focus=True):
#     DEFAULT_CSS = """
#     App.-dark DockerTable {
#         background:;
#     }
#     DockerTable {
#         background: $surface ;
#         color: $text;
#         width: 100%;
#     }
#     DockerTable > .DockerTable--header {
#         text-style: bold;
#         background: $primary;
#         color: $text;
#     }
#     DockerTable > .DockerTable--fixed {
#         text-style: bold;
#         background: $primary;
#         color: $text;
#     }
#
#     DockerTable >  .DockerTable--cursor {
#         background: $secondary;
#         color: $text;
#     }
#
#     DockerTable > .DockerTable--highlight {
#         background: $secondary 20%;
#     }
#     """
#
#     COMPONENT_CLASSES: ClassVar[set[str]] = {
#         "DockerTable--header",
#         "DockerTable--fixed",
#         "DockerTable--highlight",
#         "DockerTable--cursor",
#         "DockerTable--cursor-selected",
#     }
#
#     def __init__(
#         self,
#         *,
#         name: str | None = None,
#         id: str | None = None,
#         classes: str | None = None,
#     ) -> None:
#         super().__init__(name=name, id=id, classes=classes)
#         self.columns: dict[str, Column] = {}
#         self.display_columns: list[str] = []
#         self.rows: dict[int, Row] = {}
#         self.data: dict[int, list[CellType]] = {}
#         self.row_count = 0
#         self._y_offsets: list[tuple[int, int]] = []
#         self._row_render_cache: LRUCache[tuple[int, int, Style, int, int], tuple[Lines, Lines]]
#         self._row_render_cache = LRUCache(1000)
#         self._cell_render_cache: LRUCache[tuple[int, int, Style, bool, bool], Lines]
#         self._cell_render_cache = LRUCache(10000)
#         self._line_cache: LRUCache[tuple[int, int, int, int, int, int, Style], list[Segment]]
#         self._line_cache = LRUCache(1000)
#
#         self._line_no = 0
#         self._require_update_dimensions: bool = False
#         self._new_rows: set[int] = set()
#
#     show_header = Reactive(True)
#     fixed_rows = Reactive(0)
#     fixed_columns = Reactive(0)
#     header_height = Reactive(1)
#     show_cursor = Reactive(True)
#
#     cursor_row: Reactive[int] = Reactive(0, repaint=True)
#     hover_row: Reactive[int] = Reactive(0, repaint=True)
#
#     def is_scrollable(self) -> bool:
#         return False
#
#     @property
#     def selected_row(self):
#         return self.data[self.cursor_row]
#
#     def _clear_caches(self) -> None:
#         self._row_render_cache.clear()
#         self._cell_render_cache.clear()
#         self._line_cache.clear()
#         self._styles_cache.clear()
#
#     def get_row_height(self, row_index: int) -> int:
#         if row_index == -1:
#             return self.header_height
#         return self.rows[row_index].height
#
#     async def on_styles_updated(self, message: messages.StylesUpdated) -> None:
#         self._clear_caches()
#         self.refresh()
#
#     def watch_show_header(self, show_header: bool) -> None:
#         self._clear_caches()
#
#     def watch_fixed_rows(self, fixed_rows: int) -> None:
#         self._clear_caches()
#
#     def watch_hover_row(self, old: int, value: int) -> None:
#         self.refresh_row(old)
#         self.refresh_row(value)
#
#     def watch_cursor_row(self, old: int, value: int) -> None:
#         self.refresh_row(old)
#         self.refresh_row(value)
#
#     def _update_dimensions(self, new_rows: Iterable[int]) -> None:
#         """Called to recalculate the virtual (scrollable) size."""
#         for row_index in self.rows:
#             for column_name, renderable in zip(
#                 self.display_columns, self._get_row_renderables(row_index)
#             ):
#                 column = self.columns[column_name]
#                 content_width = measure(self.app.console, renderable, 1)
#                 column.content_width = max(column.content_width, content_width)
#
#         total_width = sum(self.columns[column].render_width for column in self.display_columns)
#
#         header_height = self.header_height if self.show_header else 0
#         self.virtual_size = Size(
#             total_width,
#             len(self._y_offsets) + header_height,
#         )
#
#     def _get_row_region(self, row_index) -> Region:
#         if row_index not in self.rows:
#             return Region(0, 0, 0, 0)
#         row = self.rows[row_index]
#         x = 0
#         width = sum(self.columns[column].render_width for column in self.display_columns)
#         height = row.height
#         y = row.y
#         if self.show_header:
#             y += self.header_height
#         cell_region = Region(x, y, width, height)
#         return cell_region
#
#     def add_columns(self, *labels: TextType) -> None:
#         """Add a number of columns.
#
#         Args:
#             *labels: Column headers.
#
#         """
#         for label in labels:
#             self.add_column(label, width=None)
#
#     def add_column(self, label: str, *, width: int | None = None) -> None:
#         """Add a column to the table.
#
#         Args:
#             label (TextType): A str or Text object containing the label (shown top of column).
#             width (int, optional): Width of the column in cells or None to fit content. Defaults to None.
#         """
#         text_label = Text.from_markup(label) if isinstance(label, str) else label
#
#         content_width = measure(self.app.console, text_label, 1)
#         if width is None:
#             column = Column(
#                 text_label,
#                 content_width,
#                 index=len(self.display_columns),
#                 content_width=content_width,
#                 auto_width=True,
#             )
#         else:
#             column = Column(
#                 text_label, width, content_width=content_width, index=len(self.display_columns)
#             )
#
#         self.columns[label] = column
#         self.display_columns.append(label)
#         self._require_update_dimensions = True
#         self.check_idle()
#
#     def add_row(self, *cells: CellType, height: int = 1) -> None:
#         """Add a row.
#
#         Args:
#             *cells: Positional arguments should contain cell data.
#             height (int, optional): The height of a row (in lines). Defaults to 1.
#         """
#         row_index = self.row_count
#
#         self.data[row_index] = list(cells)
#         self.rows[row_index] = Row(row_index, height, self._line_no)
#
#         for line_no in range(height):
#             self._y_offsets.append((row_index, line_no))
#
#         self.row_count += 1
#         self._line_no += height
#
#         self._new_rows.add(row_index)
#         self._require_update_dimensions = True
#         self.check_idle()
#
#     def add_rows(self, rows: Iterable[Iterable[CellType]]) -> None:
#         """Add a number of rows.
#
#         Args:
#             rows (Iterable[Iterable[CellType]]): Iterable of rows. A row is an iterable of cells.
#         """
#         for row in rows:
#             self.add_row(*row)
#
#     def on_idle(self) -> None:
#         if self._require_update_dimensions:
#             self._require_update_dimensions = False
#             new_rows = self._new_rows.copy()
#             self._new_rows.clear()
#             self._update_dimensions(new_rows)
#
#     def refresh_row(self, row_index: int) -> None:
#         if row_index < 0:
#             return
#         region = self._get_row_region(row_index)
#         if not self.window_region.overlaps(region):
#             return
#         region = region.translate(-self.scroll_offset)
#         self.refresh(region)
#
#     def _get_row_renderables(self, row_index: int) -> list[RenderableType]:
#         """Get renderables for the given row.
#
#         Args:
#             row_index (int): Index of the row.
#
#         Returns:
#             list[RenderableType]: List of renderables
#         """
#
#         if row_index == -1:
#             row = [column for column in self.display_columns]
#             return row
#
#         data = self.data.get(row_index)
#         empty = Text()
#         if data is None:
#             return [empty for _ in self.display_columns]
#         else:
#             return [
#                 default_cell_formatter(data[self.columns[d].index]) for d in self.display_columns
#             ]
#             # return [
#             #     Text() if datum is None else default_cell_formatter(datum) or empty
#             #     for datum, _ in zip_longest(data, range(len(self.display_columns)))
#             # ]
#
#     def _render_cell(
#         self,
#         row_index: int,
#         column_index: int,
#         style: Style,
#         width: int,
#         cursor: bool = False,
#         hover: bool = False,
#     ) -> Lines:
#         """Render the given cell.
#
#         Args:
#             row_index (int): Index of the row.
#             column_index (int): Index of the column.
#             style (Style): Style to apply.
#             width (int): Width of the cell.
#
#         Returns:
#             Lines: A list of segments per line.
#         """
#         if hover:
#             style += self.get_component_styles("DockerTable--highlight").rich_style
#         if cursor:
#             style += self.get_component_styles("DockerTable--cursor").rich_style
#         cell_key = (row_index, column_index, style, cursor, hover)
#         if cell_key not in self._cell_render_cache:
#             style += Style.from_meta({"row": row_index, "column": column_index})
#             height = self.header_height if row_index == -1 else self.rows[row_index].height
#             cell = self._get_row_renderables(row_index)[column_index]
#             lines = self.app.console.render_lines(
#                 Padding(cell, (0, 1)),
#                 self.app.console.options.update_dimensions(width, height),
#                 style=style,
#             )
#             self._cell_render_cache[cell_key] = lines
#         return self._cell_render_cache[cell_key]
#
#     def _render_row(
#         self,
#         row_index: int,
#         line_no: int,
#         base_style: Style,
#         # cursor_column: int = -1,
#         # hover_column: int = -1,
#         cursor_row: int = -1,
#         hover_row: int = -1,
#     ) -> tuple[Lines, Lines]:
#         """Render a row in to lines for each cell.
#
#         Args:
#             row_index (int): Index of the row.
#             line_no (int): Line number (on screen, 0 is top)
#             base_style (Style): Base style of row.
#
#         Returns:
#             tuple[Lines, Lines]: Lines for fixed cells, and Lines for scrollable cells.
#         """
#
#         cache_key = (row_index, line_no, base_style, cursor_row, hover_row)
#
#         if cache_key in self._row_render_cache:
#             return self._row_render_cache[cache_key]
#
#         render_cell = self._render_cell
#
#         if self.fixed_columns:
#             fixed_style = self.get_component_styles("DockerTable--fixed").rich_style
#             fixed_style += Style.from_meta({"fixed": True})
#             fixed_row = [
#                 render_cell(
#                     row_index,
#                     self.columns[column].index,
#                     fixed_style,
#                     self.columns[column].render_width,
#                 )[line_no]
#                 for column in self.display_columns[: self.fixed_columns]
#             ]
#         else:
#             fixed_row = []
#
#         if row_index == -1:
#             row_style = self.get_component_styles("DockerTable--header").rich_style
#         else:
#             row_style = base_style
#
#         scrollable_row = [
#             render_cell(
#                 row_index,
#                 self.columns[column].index,
#                 row_style,
#                 self.columns[column].render_width,
#                 cursor=cursor_row == row_index,
#                 hover=hover_row == row_index,
#             )[line_no]
#             for column in self.display_columns
#         ]
#
#         row_pair = (fixed_row, scrollable_row)
#         self._row_render_cache[cache_key] = row_pair
#         return row_pair
#
#     def _get_offsets(self, y: int) -> tuple[int, int]:
#         """Get row number and line offset for a given line.
#
#         Args:
#             y (int): Y coordinate relative to screen top.
#
#         Returns:
#             tuple[int, int]: Line number and line offset within cell.
#         """
#         if self.show_header:
#             if y < self.header_height:
#                 return (-1, y)
#             y -= self.header_height
#         if y > len(self._y_offsets):
#             raise LookupError("Y coord {y!r} is greater than total height")
#         return self._y_offsets[y]
#
#     def _render_line(self, y: int, x1: int, x2: int, base_style: Style) -> list[Segment]:
#         """Render a line in to a list of segments.
#
#         Args:
#             y (int): Y coordinate of line
#             x1 (int): X start crop.
#             x2 (int): X end crop (exclusive).
#             base_style (Style): Style to apply to line.
#
#         Returns:
#             list[Segment]: List of segments for rendering.
#         """
#
#         width = self.size.width
#
#         try:
#             row_index, line_no = self._get_offsets(y)
#         except LookupError:
#             return [Segment(" " * width, base_style)]
#         # cursor_column = (
#         #     self.cursor_column
#         #     if (self.show_cursor and self.cursor_row == row_index)
#         #     else -1
#         # )
#         # hover_column = self.hover_column if (self.hover_row == row_index) else -1
#         cursor_row = self.cursor_row if self.show_cursor else -1
#         hover_row = self.hover_row
#
#         cache_key = (y, x1, x2, width, cursor_row, hover_row, base_style)
#         if cache_key in self._line_cache:
#             return self._line_cache[cache_key]
#
#         fixed, scrollable = self._render_row(
#             row_index,
#             line_no,
#             base_style,
#             # cursor_column=cursor_column,
#             # hover_column=hover_column,
#             cursor_row=cursor_row,
#             hover_row=hover_row,
#         )
#         fixed_width = sum(
#             self.columns[column].render_width
#             for column in self.display_columns[: self.fixed_columns]
#         )
#
#         fixed_line: list[Segment] = list(chain.from_iterable(fixed)) if fixed else []
#         scrollable_line: list[Segment] = list(chain.from_iterable(scrollable))
#
#         segments = fixed_line + line_crop(scrollable_line, x1 + fixed_width, x2, width)
#         segments = Segment.adjust_line_length(segments, width, style=base_style)
#         simplified_segments = list(Segment.simplify(segments))
#
#         self._line_cache[cache_key] = simplified_segments
#         return segments
#
#     def render_line(self, y: int) -> list[Segment]:
#         width, height = self.size
#         scroll_x, scroll_y = self.scroll_offset
#         fixed_top_row_count = sum(
#             self.get_row_height(row_index) for row_index in range(self.fixed_rows)
#         )
#         if self.show_header:
#             fixed_top_row_count += self.get_row_height(-1)
#
#         style = self.rich_style
#
#         if y >= fixed_top_row_count:
#             y += scroll_y
#
#         return self._render_line(y, scroll_x, scroll_x + width, style)
#
#     def on_mouse_move(self, event: events.MouseMove):
#         meta = event.style.meta
#         if meta:
#             try:
#                 self.hover_row = meta["row"]
#             except KeyError:
#                 pass
#
#     def _get_cell_border(self) -> Spacing:
#         top = self.header_height if self.show_header else 0
#         top += sum(
#             self.rows[row_index].height
#             for row_index in range(self.fixed_rows)
#             if row_index in self.rows
#         )
#         left = sum(
#             self.columns[column].render_width
#             for column in self.display_columns[: self.fixed_columns]
#         )
#         return Spacing(top, 0, 0, left)
#
#     def _scroll_cursor_in_to_view(self, animate: bool = False) -> None:
#         region = self._get_row_region(self.cursor_row)
#         spacing = self._get_cell_border() + self.scrollbar_gutter
#         self.scroll_to_region(region, animate=animate, spacing=spacing)
#
#     def on_click(self, event: events.Click) -> None:
#         meta = self.get_style_at(event.x, event.y).meta
#         if meta:
#             self.cursor_row = meta["row"]
#             self._scroll_cursor_in_to_view()
#             # event.stop()
#
#     def key_down(self, event: events.Key):
#         self.cursor_row += 1
#         event.stop()
#         event.prevent_default()
#         self._scroll_cursor_in_to_view()
#
#     def key_up(self, event: events.Key):
#         self.cursor_row -= 1
#         event.stop()
#         event.prevent_default()
#         self._scroll_cursor_in_to_view()


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
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            cursor_type="row",
            zebra_stripes=True,
            cursor_foreground_priority="renderable",
        )
        self.logger = logger
        self.docker_file = docker_file
        self.docker_compose_parsed = {}
        self.docker_compose = DockerCompose(docker_file)
        self.selected_service = None

        self.column_sets = [
            ["service", "status"],
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
        rows = [[x, ""] for x in self.docker_compose_parsed["services"]]
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
            service = "-".join(service.split("-")[1:-1])

            if service in row_map:
                self.update_cell(row_map[service], "status", el["State"])
                # self.update_cell(row_map[service], "name", el["Name"])
                # self.update_cell(row_map[service], "command",el["Command"][:20])
                # self.update_cell(row_map[service], "port", " ".join([format_port(p) for p in el["Publishers"] or []]))

        self._require_update_dimensions = True
        self.refresh()
        self._clear_caches()

    def on_data_table_row_highlighted(self, message: DataTable.RowHighlighted) -> None:
        self.selected_service = self.get_cell(message.row_key, "service")
