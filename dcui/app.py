#!/usr/bin/env python
import argparse
import json
import os
import sys

from . import DCUIApp

basedir = os.path.dirname(os.path.realpath(__file__))


def pre_startup():
    print("I'm prerunnin")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--docker-compose", "-d", action="append", type=str)
    parser.add_argument("--conf", "-c", help="Path to config file")
    parser.add_argument("--hook-file", help="Path to hook file")

    subparsers = parser.add_subparsers(dest="subparser")
    sp = {}
    for cmd in []:
        sp[cmd] = subparsers.add_parser(cmd)

    args = parser.parse_args()
    print(args)

    if args.conf is not None:
        for conf_fname in args.conf:
            with open(conf_fname, "r") as f:
                parser.set_defaults(**json.load(f))

        # Reload arguments to override config file values with command line values
        args = parser.parse_args()

    print(args.docker_compose)
    if not args.docker_compose:
        parser.print_help()
        sys.exit(1)

    d = DCUIApp(
        docker_compose_files=[os.path.expanduser(f) for f in args.docker_compose],
        # hook_file=os.path.expanduser(args.hook_file),
    )
    return d
    # d.run()


if __name__ == "__main__":
    main().run()
elif __name__ == "dcui.app":
    # This nonsense is so I can run in with textual run --dev "dcui.app:test_app"
    # sys.argv = sys.argv[-1].split(" ")
    print(sys.argv)
    # test_app = main()
    main().run()
