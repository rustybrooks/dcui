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
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--hook-file", help="Path to hook file")
    parser.add_argument(
        "--skip-service-regex",
        "-s",
        default=None,
        required=False,
        help="Regex pattern to skip service names",
    )

    args = parser.parse_args()

    if args.config is not None:
        with open(os.path.expanduser(args.config), "r") as f:
            parser.set_defaults(**json.load(f))

        # Reload arguments to override config file values with command line values
        args = parser.parse_args()

    if not args.docker_compose:
        parser.print_help()
        sys.exit(1)

    d = DCUIApp(
        docker_compose_files=[os.path.expanduser(f) for f in args.docker_compose],
        # hook_file=os.path.expanduser(args.hook_file),
        skip_service_regex=args.skip_service_regex,
    )
    return d
    # d.run()


if __name__ == "__main__":
    main().run()
elif __name__ == "dcui.app":
    print("argv", repr(sys.argv))
    # This nonsense is so I can run in with textual run --dev "dcui.app:test_app"
    # sys.argv = sys.argv[-1].split(" ")
    # sys.argv = sys.argv[1:]
    print("argv after", sys.argv)
    # test_app = main()
    main().run()
