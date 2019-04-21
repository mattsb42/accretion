"""Lambda Layer zip artifact_builder for Python dependencies."""
import io
import json
import logging
import os
import shutil
import subprocess
import sys
import uuid
import venv
from zipfile import ZipFile
from typing import Dict, Iterable

import boto3

try:
    from accretion_workers._util import ARTIFACTS_PREFIX, ARTIFACT_MANIFESTS_PREFIX
except ImportError:
    ARTIFACTS_PREFIX = "accretion/artifacts/"
    ARTIFACT_MANIFESTS_PREFIX = "accretion/manifests/"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

WORKING_DIR = "/tmp/accretion"
VENV_DIR = f"{WORKING_DIR}/venv"
BUILD_DIR = f"{WORKING_DIR}/build"
BUILD_INPUT = f"{WORKING_DIR}/build-input"
BUILD_REQUIREMENTS = f"{WORKING_DIR}/build-requirements"
BUILD_LOG = f"{WORKING_DIR}/build-log"
S3_BUCKET = "S3_BUCKET"
_is_setup = False


class ZipBuilderError(Exception):
    """Raised when any known error happens."""


class ExecutionError(Exception):
    """Raised when a command fails to execute."""


def _setup():
    global _bucket_name
    _bucket_name = os.environ[S3_BUCKET]

    global _s3
    _s3 = boto3.client("s3")

    global _is_setup
    _is_setup = True


class PackageVersion:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    @classmethod
    def from_pip_log(cls, log_value: str) -> "PackageVersion":
        name, version = log_value.rsplit("-", 1)
        return PackageVersion(name, version)

    def to_dict(self) -> Dict[str, str]:
        return dict(Name=self.name, Version=self.version)


def _execute_command(command: str) -> (str, str):
    logger.debug(f"Executing command: {command}")
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", shell=True)
    logger.debug("============STDOUT============")
    logger.debug(proc.stdout)
    logger.debug("============STDERR============")
    logger.debug(proc.stderr)
    if proc.stderr:
        raise ExecutionError("Failed to execute command")
    return proc.stdout, proc.stderr


def _execute_in_venv(command: str) -> (str, str):
    return _execute_command(f"source {VENV_DIR}/bin/activate; {command}; deactivate")


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


def _parse_install_log() -> Iterable[Dict[str, str]]:
    trigger = "Successfully installed"
    installed = []
    with open(BUILD_LOG, "r") as f:
        for line in f:
            line = line.split(" ", 1)[-1].strip()
            if line.startswith(trigger):
                line = line[len(trigger) :].strip()
                installed = line.split()
                break
    logger.debug(f"Installed to layer artifact: {installed}")
    return [PackageVersion.from_pip_log(log_entry).to_dict() for log_entry in installed]


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
                zipper.write(filename=filepath, arcname=f"python/{filepath[len(BUILD_DIR) + 1:]}")

    logger.debug(f"Zip file size: {buffer.tell()} bytes")
    buffer.seek(0)
    return buffer


def _build_and_upload_zip(project_name: str) -> str:
    key = f"{ARTIFACTS_PREFIX}{project_name}/{uuid.uuid4()}.zip"
    zip_buffer = _build_zip()

    _s3.put_object(Bucket=_bucket_name, Key=key, Body=zip_buffer)
    return key


def _write_manifest(
    project_name: str, artifact_key: str, requirements=Iterable[str], installed=Iterable[str], runtimes=Iterable[str]
) -> str:
    artifact_id = artifact_key[artifact_key.rindex("/") + 1 : artifact_key.rindex(".")]
    key = f"{ARTIFACT_MANIFESTS_PREFIX}{project_name}/{artifact_id}.manifest"
    body = json.dumps(
        dict(
            ProjectName=project_name,
            ArtifactS3Key=artifact_key,
            Requirements=requirements,
            Installed=installed,
            Runtimes=runtimes,
        ),
        indent=4,
    )

    _s3.put_object(Bucket=_bucket_name, Key=key, Body=body)
    return key


def _runtime_name():
    try:
        return {3: {6: "python3.6", 7: "python3.7"}}[sys.version_info.major][sys.version_info.minor]
    except KeyError:
        raise Exception(f"Unexpected runtime: {sys.version_info}")


def lambda_handler(event, context):
    """
    Event shape:

    ..code:: json

        {
            "Name": "layer name",
            "Requirements": ["List of requirements"]
        }

    Return shape:

    ..code:: json

        {
            "Installed": ["Actual versions of all installed requirements"],
            "Runtimes": ["Lambda runtime name"],
            "ArtifactKey": "S3 key containing built zip",
            "ManifestKey": "S3 key containing job manifest"
        }

    Required permissions:

    * s3:PutObject for S3_BUCKET/accretion/artifacts/*
    * s3:PutObject for S3_BUCKET/accretion/manifests/*

    :param event:
    :param context:
    :return:
    """
    try:
        if not _is_setup:
            _setup()

        _build_venv()
        _build_requirements(*event["Requirements"])
        _install_requirements_to_build()
        installed = _parse_install_log()
        artifact_key = _build_and_upload_zip(event["Name"])
        manifest_key = _write_manifest(
            project_name=event["Name"],
            artifact_key=artifact_key,
            requirements=event["Requirements"],
            installed=installed,
            runtimes=[_runtime_name()],
        )
        return {
            "Installed": installed,
            "Runtimes": [_runtime_name()],
            "ArtifactKey": artifact_key,
            "ManifestKey": manifest_key,
        }
    except ZipBuilderError as error:
        raise
    except Exception:
        raise
