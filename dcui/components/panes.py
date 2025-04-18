#!/usr/bin/env python
from collections import defaultdict

from textual import events
from textual.app import App
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Header, Footer, Static

GRID_WIDTH = 8
GRID_HEIGHT = 4


class Panel(Widget):
    DEFAULT_CSS = """
        .title {
            content-align: center top;
            background: $primary-background;
        }
    """

    def __init__(
        self,
        title,
        content: Widget = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.title = title
        self.content = content

    def compose(self):
        yield Static("", name=self.title, classes="title")
        yield self.content

    def is_scrollable(self) -> bool:
        return False


class Panes(
    Container,
    can_focus=True,
    can_focus_children=True,
):
    DEFAULT_CSS = f"""
        Panes {{
            layout: grid;
            grid-size: {GRID_WIDTH} {GRID_HEIGHT};
            grid-columns: 1fr 1fr;
        }}    

        .box {{
            height: 100%;
            border: solid $secondary;
            background: $surface;
        }}
        
        .box-selected {{
            height: 100%;
            border: solid $accent;
            background: $accent 30%;
        }}
    """

    BINDINGS = [Binding(key="ctrl+]", action="next_pane()", description="Next pane")]

    selected = reactive((0, 0))

    def __init__(
        self,
        first=None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        # if not first:
        #    first = Panel(title=str(self.selected), content=Static(""))

        self.grid = {}
        self.last_split = "horizontal"
        self.splits = []

    def watch_selected(self, old, new):
        if not self.grid:
            return

        if old:
            self.grid[old]["object"].toggle_class("box", "box-selected")
        self.grid[new]["object"].toggle_class("box", "box-selected")
        if self.grid[new]["object"].can_focus:
            self.grid[new]["object"].focus()

    def add_first(self):
        el = self.grid[self.selected]["object"]
        el.set_class(True, "box-selected")
        el.set_styles(f"column-span: {GRID_WIDTH};")
        el.set_styles(f"row-span: {GRID_HEIGHT};")
        self.splits = [self.selected]
        self.mount(el)

    def find_empty_pane(self):
        pass
        # for k, v in self.grid.items():
        #    if v["object"]

    def find_largest_splittable_pane(self):
        size_map = defaultdict(list)
        for k, v in self.grid.items():
            size = v["width"] * v["height"]

            if v["width"] <= 1 and v["height"] <= 1:
                continue

            size_map[size].append(k)

        sorted_keys = sorted(size_map.keys())
        if sorted_keys:
            return size_map[sorted_keys[-1]][0]

        return None

    def add_pane(self, title, content):
        if not self.grid:
            self.grid = {
                (0, 0): {
                    "object": Panel(title=title, content=content),
                    "width": GRID_WIDTH,
                    "height": GRID_HEIGHT,
                }
            }
            self.add_first()
            return True

        fn = self.action_splitx if self.last_split == "horizontal" else self.action_splity
        print("split", self.last_split, fn)
        did_split = fn(title=title, content=content)

        if not did_split:
            sc = self.find_largest_splittable_pane()
            if not sc:
                return True

            self.selected = sc
            fn = (
                self.action_splitx
                if self.grid[sc]["width"] >= self.grid[sc]["height"]
                else self.action_splity
            )
            return fn(title=title, content=content)

    def recursive_remove(self, remove_index):
        if isinstance(remove_index, tuple):
            remove = self.grid.pop(remove_index)
            remove["object"].remove()
            return [remove]
        else:
            return sum([self.recursive_remove(el) for el in remove_index], [])

    def recursive_flatten(self, remove_index):
        if isinstance(remove_index, tuple):
            return [remove_index]
        else:
            return sum([self.recursive_flatten(el) for el in remove_index], [])

    def remove_pane(self):
        print("remove_pane", len(list(self.grid.keys())))
        if len(list(self.grid.keys())) == 1:
            self.recursive_remove(self.selected)
            return

        split = self.find_split(self.selected, self.splits)
        keepi = next(x for x in split if x == self.selected)
        removei = next(x for x in split if x != self.selected)
        # print(split, self.selected, keepi, removei)
        keep = self.grid[keepi]
        removed = self.recursive_remove(removei)
        recursive_index = self.recursive_flatten(removei)
        # print(removed, keep["width"], keepi[0] == removei[1])
        # print("ri", recursive_index)

        if isinstance(removei, list):
            minrow = min([x[0] for x in recursive_index])
            mincol = min([x[1] for x in recursive_index])
        else:
            minrow = removei[0]
            mincol = removei[1]

        if keepi[0] == minrow:
            # same row, horizontal split
            keep["width"] = keep["width"] + sum([r["width"] for r in removed])
            keep["object"].set_styles(f"column-span: {keep['width']};")
        else:
            # same col, horizontal split
            keep["height"] = keep["height"] + sum([r["height"] for r in removed])
            keep["object"].set_styles(f"row-span: {keep['height']};")

        print("after", keep["width"], keep["height"])
        split2 = self.find_split(split, self.splits)
        i = split2.index(split)
        split2[i] = keepi

    def find_split(self, index, input=None):
        if not input or isinstance(input, tuple):
            return

        if index in input:
            return input

        for el in input:
            val = self.find_split(index, el)
            if val:
                return val

    def new_item(self, new_coord, old_item, title=None, content=None):
        if not content:
            content = Static("foo")

        if not title:
            title = str(new_coord)

        self.handle_split(new_coord)

        new_object = Panel(title=title, content=content, classes="box")
        new_object.set_styles(f"column-span: {old_item['width']};")
        new_object.set_styles(f"row-span: {old_item['height']};")
        self.grid[new_coord] = {
            "object": new_object,
            "width": old_item["width"],
            "height": old_item["height"],
        }

        new_index = sorted(self.grid.keys()).index(new_coord)
        if new_index == 0:
            kwargs = {"before": 0}
        else:
            kwargs = {"after": new_index - 1}

        self.mount(self.grid[new_coord]["object"], **kwargs)

    def handle_split(self, new_coord):
        split = self.find_split(self.selected, self.splits)
        i = split.index(self.selected)
        split[i] = [self.selected, new_coord]

    def action_splitx(self, title=None, content=None):
        self.last_split = "horizontal"
        sel = self.grid.get(self.selected)
        if not sel:
            self.add_pane(title=title, content=content)
            return True

        if sel["width"] <= 1:
            return False

        row, col = self.selected
        sel["width"] = sel["width"] // 2
        sel["object"].set_styles(f"column-span: {sel['width']};")
        new_coord = (row, col + sel["width"])
        self.new_item(new_coord, sel, title, content)

        return True

    def action_splity(self, title=None, content=None):
        self.last_split = "vertical"
        sel = self.grid[self.selected]
        if sel["height"] <= 1:
            return False

        row, col = self.selected
        sel["height"] = sel["height"] // 2
        sel["object"].set_styles(f"row-span: {sel['height']};")
        new_coord = (row + sel["height"], col)
        self.new_item(new_coord, sel, title, content)

        return True

    def on_click(self, event: events.Click):
        clicked = self.screen.get_widget_at(event.screen_x, event.screen_y)[0]

        indices = sorted(self.grid.keys())
        widgets = [self.grid[x]["object"] for x in indices]

        while True:
            if clicked is None:
                return

            try:
                index = widgets.index(clicked)
                break
            except ValueError:
                clicked = clicked.parent

        self.selected = indices[index]

        event.stop()

    def action_next_pane(self):
        keys = list(sorted((self.grid or {}).keys()))
        i = keys.index(self.selected)
        self.selected = keys[(i + 1) % len(keys)]

    def pane_focus(self):
        print(self.grid)
        if not self.grid:
            return

        print(self.selected)
        sel = self.grid[self.selected]["object"]
        if sel.content.can_focus:
            sel.content.focus()
        else:
            self.focus()


class Test(App):
    BINDINGS = [("1", "add()", "Add"), ("x", "remove()", "Remove")]

    def compose(self):
        self.panes = Panes()
        yield Header()
        yield self.panes
        yield Footer()

    def on_mount(self):
        self.query_one(Panes).focus()

    def action_add(self):
        self.panes.add_pane(title="blah", content=Static("add"))

    def action_remove(self):
        self.panes.remove_pane()


if __name__ == "__main__":
    app = Test()
    app.run()
