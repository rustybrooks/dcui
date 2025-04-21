import asyncio
import os
import socket
import subprocess
import threading
from contextlib import closing
from typing import Dict, List, Optional


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) == 0


def wait_for_port(port, host="localhost", interval=2):
    while True:
        if check_socket(host, port):
            break
        asyncio.sleep(interval)


def reader(pipe, pipe_name, callback):
    try:
        with pipe:
            for line in iter(pipe.readline, b""):
                callback(pipe_name, line.decode())
    finally:
        pass


class DockerException(Exception):
    def __init__(
        self,
        command_launched: List[str],
        return_code: int,
        stdout: Optional[bytes] = None,
        stderr: Optional[bytes] = None,
    ):
        self.docker_command: List[str] = command_launched
        self.return_code: int = return_code
        if stdout is None:
            self.stdout: Optional[str] = None
        else:
            self.stdout: Optional[str] = stdout.decode()
        if stderr is None:
            self.stderr: Optional[str] = None
        else:
            self.stderr: Optional[str] = stderr.decode()
        command_launched_str = " ".join(command_launched)
        error_msg = (
            f"The docker command executed was `{command_launched_str}`.\n"
            f"It returned with code {return_code}\n"
        )
        if stdout is not None:
            error_msg += f"The content of stdout is '{self.stdout}'\n"
        else:
            error_msg += (
                "The content of stdout can be found above the stacktrace (it wasn't captured).\n"
            )
        if stderr is not None:
            error_msg += f"The content of stderr is '{self.stderr}'\n"
        else:
            error_msg += (
                "The content of stderr can be found above the stacktrace (it wasn't captured)."
            )
        super().__init__(error_msg)


def stream_stdout_and_stderr(
    full_cmd: list, env: Dict[str, str] = None, callback=None
) -> subprocess.Popen[bytes]:
    if env is None:
        subprocess_env = None
    else:
        subprocess_env = dict(os.environ)
        subprocess_env.update(env)

    full_cmd = list(map(str, full_cmd))
    print("env", env, "spenv", subprocess_env)
    process = subprocess.Popen(
        full_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=subprocess_env,
        start_new_session=True,
        # preexec_fn=set_pdeathsig(signal.SIGTERM),
    )

    # we use daemon threads to avoid hanging if the user uses ctrl+c
    th = threading.Thread(target=reader, args=[process.stdout, "stdout", callback])
    th.daemon = True
    th.start()
    th = threading.Thread(target=reader, args=[process.stderr, "stderr", callback])
    th.daemon = True
    th.start()

    return process


async def run_async(command):
    # print("running", command)
    # Create subprocess
    process = await asyncio.create_subprocess_exec(
        *command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    # Return stdout
    return stdout.decode().strip()
