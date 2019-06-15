"""Lambda Layer zip artifact_builder for Python dependencies."""
import json
import logging
import os
import shutil
import sys
from typing import Dict, Iterable

import boto3
from accretion_common.constants import ARTIFACT_MANIFESTS_PREFIX
from accretion_common.venv_magic.builder import build_requirements
from accretion_common.venv_magic.uploader import artifact_exists, efficient_build_and_upload_zip

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

WORKING_DIR = "/tmp/accretion"
VENV_DIR = f"{WORKING_DIR}/venv"
BUILD_DIR = f"{WORKING_DIR}/build"
BUILD_INPUT = f"{WORKING_DIR}/build-input"
BUILD_REQUIREMENTS = f"{WORKING_DIR}/build-requirements"
BUILD_LOG = f"{WORKING_DIR}/build-log"
S3_BUCKET = "S3_BUCKET"
_RUNTIME_NAMES = {3: {6: "python3.6", 7: "python3.7"}}
_is_setup = False


def _setup():
    global _bucket_name
    _bucket_name = os.environ[S3_BUCKET]

    global _s3
    _s3 = boto3.client("s3")

    global _is_setup
    _is_setup = True


def _clean_env():
    shutil.rmtree(WORKING_DIR, ignore_errors=True)


def _write_manifest(
    project_name: str, artifact_key: str, requirements=Iterable[str], installed=Iterable[str], runtimes=Iterable[str]
) -> str:
    artifact_id = artifact_key[artifact_key.rindex("/") + 1 : artifact_key.rindex(".")]
    key = f"{ARTIFACT_MANIFESTS_PREFIX}{project_name}/{artifact_id}.manifest"

    if artifact_exists(_s3, _bucket_name, key):
        return key

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
        return _RUNTIME_NAMES[sys.version_info.major][sys.version_info.minor]
    except KeyError:
        raise Exception(f"Unexpected runtime: {sys.version_info}")


def _upload_artifacts(name: str, requirements: Iterable[str], installed: Iterable[Dict[str, str]]):
    artifact_key = efficient_build_and_upload_zip(
        s3_client=_s3,
        project_name=name,
        installed=installed,
        bucket_name=_bucket_name,
        build_dir=BUILD_DIR,
        runtime_name=_runtime_name(),
    )
    manifest_key = _write_manifest(
        project_name=name,
        artifact_key=artifact_key,
        requirements=requirements,
        installed=installed,
        runtimes=[_runtime_name()],
    )
    return artifact_key, manifest_key


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

        _clean_env()
        installed = build_requirements(build_dir=BUILD_DIR, venv_dir=VENV_DIR, requirements=event["Requirements"])
        artifact_key, manifest_key = _upload_artifacts(event["Name"], event["Requirements"], installed)
        return {
            "Installed": installed,
            "Runtimes": [_runtime_name()],
            "ArtifactKey": artifact_key,
            "ManifestKey": manifest_key,
        }
    except Exception:
        # TODO: Turn these into known-cause state machine failures.
        raise
