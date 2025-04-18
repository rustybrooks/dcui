import json
import subprocess

from yaml import load

from .utils import stream_stdout_and_stderr, get_github_password, run_async

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class DockerCompose:
    def __init__(self, docker_file):
        self.docker_file = docker_file
        self.prefix = ["docker", "compose", "-f", self.docker_file]

    def load_docker_compose(self, filename):
        with open(filename) as f:
            data = load(f.read(), Loader=Loader)
        return data

    def handle_command(self, command, return_command=True, callback=False):
        if return_command:
            return command
        else:
            if callback:
                return stream_stdout_and_stderr(command, callback=callback)
            else:
                return subprocess.check_call(command)

    def up(self, services=None, detach=False, callback=None, return_command=True):
        command = self.prefix + ["up"]
        if detach:
            command.append("-d")
        if services:
            command.extend(services)

        return command if return_command else stream_stdout_and_stderr(command, callback=callback)

    def down(self, services=None, callback=None, return_command=True):
        command = self.prefix + ["down"]
        if services:
            command.extend(services)

        return command if return_command else stream_stdout_and_stderr(command, callback=callback)

    def stop(self, services, callback=None, return_command=True):
        command = self.prefix + ["stop"]
        if services:
            command.extend(services)

        return command if return_command else stream_stdout_and_stderr(command, callback=callback)

    def build(self, services=None, with_password=False, callback=None, return_command=True):
        command = self.prefix + ["build", "--progress=plain"]

        if services:
            command.extend(services)

        if with_password:
            command += ["--build-arg", f"GITHUB_PASSWORD={get_github_password()}"]

        return command if return_command else stream_stdout_and_stderr(command, callback=callback)

    async def ps(self):
        command = self.prefix + ["ps", "--format=json"]
        lines = await run_async(command)
        data = []
        for line in lines.splitlines():
            line_data = json.loads(line)
            data.append(line_data)

        return data

    def logs(self, services=None, tail=True, callback=None, return_command=True):
        command = self.prefix + ["logs"]
        if tail:
            command.append("-f")
        if services:
            command.extend(services)

        return command if return_command else stream_stdout_and_stderr(command, callback=callback)

    def shell(self, service, callback=None, return_command=True):
        command = self.prefix + ["exec", service, "sh"]
        return command if return_command else stream_stdout_and_stderr(command, callback=callback)

    def run(self, service, callback=None, return_command=True):
        command = self.prefix + ["run", "--entrypoint=sh", service]
        return command if return_command else stream_stdout_and_stderr(command, callback=callback)

    def exec(self, service, command, callback=None, return_command=True):
        docker_command = self.prefix + ["exec", service]
        command.extend(command)
        return self.handle_command(docker_command, callback=callback, return_command=return_command)
