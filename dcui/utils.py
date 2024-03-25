import asyncio
import ctypes
import os
import signal
import socket
import subprocess
import threading
from contextlib import closing
from typing import Dict, List, Optional

from dotenv import dotenv_values

# import docker_compose

scriptdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.abspath(os.path.join(scriptdir, ".."))
peerdir = os.path.abspath(os.path.join(basedir, "..", ".."))
dirs = {
    k: os.path.abspath(v)
    for k, v in {
        "script": scriptdir,
        "base": basedir,
        "data": os.path.join(basedir, "data"),
        "eis": os.path.join(peerdir, "eis"),
        "dgraphsync": os.path.join(peerdir, "dgraphessync"),
        "nodeserver": os.path.join(peerdir, "NodeServer"),
        "datamodel": os.path.join(peerdir, "datamodel"),
        "startup_scripts_dir": os.path.join(basedir, "..", "automation", "scripts"),
    }.items()
}

"""
setup_rulesengine_db() {
  echo "Setting rules engine db"
  docker run --rm --net=host --name re_db_migration ${RULES_ENGINE_IMAGE} /app/dbmigration -dsn="mysql://${RULES_ENGINE_DB_DSN}" \
                  -source="file:///app/conf/schema_migrations"
}
"""


def get_github_password():
    cachefile = "/tmp/pw"
    if not os.path.exists(cachefile):
        # This assumes osx, how do we do it on linux?
        pw = (
            subprocess.check_output(["security", "find-internet-password", "-s", "github.com", "-w"])
            .decode("utf-8")
            .strip()
        )
        with open(cachefile, "w") as f:
            f.write(pw)

    with open(cachefile) as f:
        return f.read().strip()


def gen_env():
    env = dotenv_values(dotenv_path=os.path.join(basedir, "..", "docker_env", "dev.env"))

    env.update(
        {
            "DOCKER_STACK_NAME": "local-hib",
            "DATAMODEL_DIR": dirs["datamodel"],
            "EIS_DIR": dirs["eis"],
            "DGRAPHSYNC_DIR": dirs["dgraphsync"],
            "NODESERVER_DIR": dirs["nodeserver"],
            "DATA_DIR": dirs["data"],
            "STARTUP_SCRIPTS_DIR": dirs["startup_scripts_dir"],
            "SCRIPT_DIR": basedir,
            "ELASTIC_INDEX_MAPPINGS_DIR": os.path.join(dirs["datamodel"], "schema", "elasticsearch"),
            # Nodeserver
            "NODESERVER_DB_DB": "hubble",
            "NODESERVER_DB_USER": "hubble",
            "HUBBLE_MYSQL_HUBBLE_PASSWORD": "hubble_test",
            # Rules engine
            "RULES_ENGINE_DB_NAME": "rules",
            "RULES_ENGINE_DB_USER": "rules",
            "RULES_ENGINE_DB_PSWD": "rules",
            # HAS
            "HUBBLE_APP_SERVER_DB_NAME": "hubble_app_server",
            "HUBBLE_APP_SERVER_DB_USER": "hubble_app_server_user",
            "HUBBLE_APP_SERVER_DB_PASSWORD": "hubble_app_server_pass",
            "HUBBLE_MYSQL_ROOT_PASSWORD": "mysql_root",
            "EIS_MEM_LIMIT": "2G",
            "DGRAPHESSYNC_MEM_LIMIT": "2G",
            "AWS_REGION": "us-east-1",
            "S3_BUCKET": "",
            # images
            # "DGRAPHESSYNC_IMAGE": "899138803732.dkr.ecr.us-east-1.amazonaws.com/dgraphessync:2022.01.21_4d42f88",
            # "EIS_IMAGE": "899138803732.dkr.ecr.us-east-1.amazonaws.com/eis:feat_debug_raw_data_latest",
            "DGRAPHESSYNC_IMAGE": "dgraphessync:latest",
            "EIS_IMAGE": "eis:latest",
            "NGINX_IMAGE": "nginx:1.19.3",
            "NODESERVER_IMAGE": "busybox",
            "HUBBLE_APP_SERVER_IMAGE": "busybox",
            "NORMALIZATION_CLIENT_IMAGE": "busybox",
            "CVE_SYNC_IMAGE": "busybox",
            "AUTHSERVER_IMAGE": "busybox",
            "AHS_IMAGE": "busybox",
            "CUSTOMER_ID": "n/a",
            "AHS_IPV4_ASSIGNMENTS_TABLE": "n/a",
            "AHS_ASSET_HISTORY_TABLE": "n/a",
        }
    )

    with open(os.path.join(basedir, ".env"), "w") as f:
        for k, v in env.items():
            f.write(f'{k}="{v}"\n')


def setup_kafka():
    wait_for_port(9092)

    # channels = docker_compose.exec(
    #     "kafka",
    #     ["bash", "-c" '"kafka-topics.sh --bootstrap-server localhost:9092 --list"'],
    #     return_command=False,
    # )
    # print(channels)
    """

    echo "Getting list of kafka topics"
    for i in $(seq 3); do
      kafka_list=$(docker compose -f "${DOCKER_COMPOSE}" -p ${DOCKER_STACK_NAME} exec kafka bash -c "kafka-topics.sh --bootstrap-server localhost:9092 --list")
      echo "... attempt ${i} topics=${kafka_list}"
      ret=$?
      if [ $ret -eq 0 ]; then
        if [ -n "$kafka_list" ]; then
          break
        fi
      fi
      sleep 2
    done

    echo "Setting up kafka topics"
    kafka_topics="events normalizedEvents policyDecisions assetChangeEvents connector_raw_data_events"
    for topic in $kafka_topics; do
      if echo "$kafka_list" | grep -e "\b$topic\b" &>/dev/null; then
        echo "Already have kafka topic: $topic"
      else
        echo "Setting up kafka topic: $topic"
        docker compose -f "${DOCKER_COMPOSE}" -p ${DOCKER_STACK_NAME} exec kafka bash -c "kafka-topics.sh --bootstrap-server localhost:9092 --create --topic $topic"
      fi
    done
    echo "Done setting up kafka topics"
    """
    pass


def setup_dgraph():
    """
    function setup_dgraph {
      echo "Setting up dgraph"
      while true; do
        curl_out=$(curl -s -X POST localhost:8080/alter --data-binary @"$DATAMODEL_DIR/schema/dgraph/datamodel.dql")
        if [ $? -eq 0 ]; then
          if ! echo "$curl_out" | grep error; then
            break
          fi
        fi
        sleep 2
      done
      echo "dgraph setup complete"
    }"""
    pass


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
            f"The docker command executed was `{command_launched_str}`.\n" f"It returned with code {return_code}\n"
        )
        if stdout is not None:
            error_msg += f"The content of stdout is '{self.stdout}'\n"
        else:
            error_msg += "The content of stdout can be found above the " "stacktrace (it wasn't captured).\n"
        if stderr is not None:
            error_msg += f"The content of stderr is '{self.stderr}'\n"
        else:
            error_msg += "The content of stderr can be found above the " "stacktrace (it wasn't captured)."
        super().__init__(error_msg)


def stream_stdout_and_stderr(full_cmd: list, env: Dict[str, str] = None, callback=None) -> subprocess.Popen[bytes]:
    if env is None:
        subprocess_env = None
    else:
        subprocess_env = dict(os.environ)
        subprocess_env.update(env)

    full_cmd = list(map(str, full_cmd))
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
