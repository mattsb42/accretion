"""
Lambda Layer zip builder for Python dependencies.
"""
import io
import logging
import os
import shutil
import subprocess
import sys
import uuid
import venv
from zipfile import ZipFile
from typing import Iterable

import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

WORKING_DIR = "/tmp/accretion"
PIP_CACHE = f"{WORKING_DIR}/pipcache"
VENV_DIR = f"{WORKING_DIR}/venv"
BUILD_DIR = f"{WORKING_DIR}/build"
BUILD_INPUT = f"{WORKING_DIR}/build-input"
BUILD_REQUIREMENTS = f"{WORKING_DIR}/build-requirements"
BUILD_LOG = f"{WORKING_DIR}/build-log"
S3_BUCKET = "S3_BUCKET"


class ExecutionError(Exception):
    """Raised when a command fails to execute."""


def _execute_command(command: str) -> (str, str):
    logger.debug(f"Executing command: {command}")
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        shell=True,
    )
    logger.debug("============STDOUT============")
    logger.debug(proc.stdout)
    logger.debug("============STDERR============")
    logger.debug(proc.stderr)
    if proc.stderr:
        raise ExecutionError("Failed to execute command")
    return proc.stdout, proc.stderr


def _execute_in_venv(command: str) -> (str, str):
    return _execute_command(
        f"source {VENV_DIR}/bin/activate; {command}; deactivate"
    )


def _clean_env():
    shutil.rmtree(WORKING_DIR, ignore_errors=True)


def _build_venv():
    _clean_env()
    venv.create(VENV_DIR, clear=True, with_pip=True)
    _execute_in_venv("pip install --no-cache-dir --upgrade pip")


def _install_requirements_to_build() -> (str, str):
    return _execute_in_venv(
        "pip install --no-cache-dir --upgrade --ignore-installed --no-compile "
        f"--log {BUILD_LOG} "
        f"-r {BUILD_REQUIREMENTS} --target {BUILD_DIR}"
    )


def _build_requirements(*libraries: str):
    with open(BUILD_REQUIREMENTS, "w") as f:
        for library in libraries:
            f.write(f"{library}\n")


def _parse_install_log() -> Iterable[str]:
    trigger = "Successfully installed"
    installed = []
    with open(BUILD_LOG, "r") as f:
        for line in f:
            line = line.split(" ", 1)[-1].strip()
            if line.startswith(trigger):
                line = line[len(trigger):].strip()
                installed = line.split()
                break
    logger.debug(f"Installed to layer artifact: {installed}")
    return installed


def _file_filter(filename: str) -> bool:
    """Determine whether this file should be included in the zip file.

    :param str filename: Filename
    :rtype: bool
    """
    # For now, leave everything in.
    return True

    if filename.endswith(".pyc"):
        return False

    if f"{os.path.sep}__pycache__{os.path.sep}" in filename:
        return False

    return True


def _build_zip() -> io.BytesIO:
    buffer = io.BytesIO()
    with ZipFile(buffer, mode="w") as zipper:
        for root, dirs, files in os.walk(BUILD_DIR):
            for filename in files:
                if not _file_filter(filename):
                    continue

                filepath = os.path.join(root, filename)
                zipper.write(
                    filename=filepath,
                    arcname=f"python/{filepath[len(BUILD_DIR) + 1:]}"
                )

    logger.debug(f"Zip file size: {buffer.tell()} bytes")
    buffer.seek(0)
    return buffer


def _build_and_upload_zip(project_name: str) -> str:
    key = f"{project_name}/{uuid.uuid4()}"
    bucket_name = os.environ[S3_BUCKET]
    zip_buffer = _build_zip()
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=zip_buffer,
    )
    return key


def _runtime_name():
    try:
        return {3: {
            6: "python3.6",
            7: "python3.7"
        }}[sys.version_info.major][sys.version_info.minor]
    except KeyError:
        raise Exception(f"Unexpected runtime: {sys.version_info}")


def lambda_handler(event, context):
    """
    Event shape:

    ..code:: json

        {
            "name": "layer name",
            "requirements": ["Dependency requirements"],
        }

    Return shape:

    ..code:: json

        {
            "name": "layer name",
            "requirements": ["Dependency requirements"],
            "installed": ["Actual versions of all installed requirements"],
            "runtimes": ["Lambda runtime name"],
            "s3_key": "S3 key containing built zip"
        }

    :param event:
    :param context:
    :return:
    """
    _build_venv()
    _build_requirements(*event["requirements"])
    _install_requirements_to_build()
    installed = _parse_install_log()
    s3_key = _build_and_upload_zip(event["name"])
    return {
        "name": event["name"],
        "requirements": event["requirements"],
        "installed": installed,
        "runtimes": [_runtime_name()],
        "s3_key": s3_key,
    }
