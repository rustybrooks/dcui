# hooks I need
# pre-run (generate env)
# before starting container(s)?
import importlib
import os.path
import sys


class Hooks:
    _hook_types = ["pre_startup", "pre_up", "post_up"]

    def __init__(self, hook_file):
        print("Hooks init", hook_file)
        self.hooks = {}
        if not hook_file:
            return

        ext = os.path.splitext(hook_file)[-1].lower()
        if ext == ".py":
            # with open(hook_file) as f:
            #    code = exec(f.read())
            dirname, filename = os.path.split(hook_file)
            sys.path.append(dirname)
            code = importlib.import_module(os.path.splitext(filename)[0])
            print(code)
        elif ext == ".json":
            pass
        else:
            code = importlib.import_module(hook_file)

        for h in self._hook_types:
            if hasattr(code, h):
                self.add_hook(h, getattr(code, h))

    def execute(self, hook_name):
        if hook_name not in self.hooks:
            print("no hook for", hook_name)
            return

        print("executin", hook_name, self.hooks[hook_name]())

    def add_hook(self, hook_name, fn):
        print("add hook", hook_name)
        self.hooks[hook_name] = fn
