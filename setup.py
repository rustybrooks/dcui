#!/usr/bin/env python

from glob import glob

from setuptools import find_packages, setup

setup(
    name="dcui",
    packages=find_packages(),
    version="1.0.0",
    description="Docker TUI thing",
    author="Rusty Brooks",
    license="Proprietary",
    install_requires=[
        line.strip() for line in open("requirements.txt").readlines() if not line.strip().startswith("--")
    ],
    package_data={"": ["dcui.css", "docker-compose.yml" "docker-compose.2.yml"]},
    scripts=["bin/dcui"],
)
