"""Given a new artifact, publish a new Layer."""
import json
import os
from typing import Iterator

import boto3

try:
    from accretion_workers._util import LAYER_MANIFESTS_PREFIX
except ImportError:
    LAYER_MANIFESTS_PREFIX = "accretion/layers/"

S3_BUCKET = "S3_BUCKET"
_is_setup = False


def _setup():
    global _aws_lambda
    _aws_lambda = boto3.client("lambda")

    global _bucket_name
    _bucket_name = os.environ[S3_BUCKET]

    global _s3
    _s3 = boto3.client("s3")

    global _is_setup
    _is_setup = True


_MINIFIED_RUNTIMES = {
    "nodejs": "njs",
    "java": "jav",
    "python": "py",
    "dotnetcore": "dnc",
    "go": "go",
    "ruby": "rby",
    "provided": "pro",
}


def _layer_name(*, project_name: str, runtimes: Iterator[str]):
    squashed_runtimes = "".join(sorted(runtimes)).replace(".", "")
    for runtime, minified in _MINIFIED_RUNTIMES.items():
        squashed_runtimes = squashed_runtimes.replace(runtime, minified)

    layer_name = f"{project_name}-{squashed_runtimes}"
    if len(layer_name) > 140:
        raise Exception(f"Unable to compress project name: {layer_name}")

    return layer_name


def _layer_manifest_s3_prefix(*, layer_name: str) -> str:
    return f"{LAYER_MANIFESTS_PREFIX}{layer_name}/"


def _layer_manifest_s3_key(*, layer_name: str, layer_version: int) -> str:
    return f"{_layer_manifest_s3_prefix(layer_name=layer_name)}{layer_version}.json"


def _publish_layer(
    *, project_name: str, artifact_bucket: str, artifact_key: str, runtimes: Iterator[str]
) -> (str, int):
    layer_name = _layer_name(project_name=project_name, runtimes=runtimes)
    description = f"Accretion manifests: s3://{_bucket_name}/{_layer_manifest_s3_prefix(layer_name=layer_name)}"

    response = _aws_lambda.publish_layer_version(
        LayerName=layer_name,
        Description=description,
        Content=dict(S3Bucket=artifact_bucket, S3Key=artifact_key),
        CompatibleRuntimes=runtimes,
    )
    return response["LayerArn"], response["Version"]


def _set_layer_permissions(*, layer_arn: str, layer_version: str, manifest_key: str):
    artifact_id = manifest_key[manifest_key.rindex("/") + 1 : manifest_key.rindex(".")]
    _aws_lambda.add_layer_version_permission(
        LayerName=layer_arn,
        VersionNumber=layer_version,
        StatementId=artifact_id,
        Principal="*",
        Action="lambda:GetLayerVersion",
    )


def _publish_layer_manifest(
    *, layer_name: str, layer_arn: str, layer_version: int, manifest_bucket: str, manifest_key: str
) -> str:
    s3_key = _layer_manifest_s3_key(layer_name=layer_name, layer_version=layer_version)

    body = json.dumps(
        dict(
            Layer=dict(Arn=layer_arn, Version=layer_version),
            ArtifactManifest=dict(S3Bucket=manifest_bucket, S3Key=manifest_key),
        ),
        indent=4,
    )
    _s3.put_object(Bucket=_bucket_name, Key=s3_key, Body=body)
    return s3_key


def lambda_handler(event, context):
    """

    Event shape:

    ..code:: json

        {
            "ResourceKey": "S3 key containing object that triggered event",
            "ProcessEvent": boolean decision stating whether to continue processing event,
            "Artifact": {
                "Found": boolean statement whether artifact exists yet,
                "ReadAttempts": number of attempts that were made to read artifact,
                "Location": {
                    "S3Bucket": "S3 bucket containing artifact",
                    "S3Key": "S3 key in bucket containing artifact"
                },
                "ProjectName": "project name to be used for Lambda Layer name",
                "Runtimes": List of Lambda runtimes that Layer will support
            }
        }

    Return shape:

    ..code:: json

        {
            "LayerArn": "Arn of published Lambda Layer",
            "LayerVersion": version of published Lambda Layer,
            "ArtifactManifest": {
                "S3Bucket": "S3 bucket containing artifact manifest",
                "S3Key": "S3 key containing artifact manifest"
            }
        }

    Required permissions:

    * lambda:PublishLayerVersion for current account
    * lambda:AddLayerVersionPermission for current account
    * s3:PutObject for S3_BUCKET/accretion/layers/*

    :param event:
    :param context:
    :return:
    """
    try:
        if not _is_setup:
            _setup()

        project_name = event["Artifact"]["ProjectName"]
        manifest_bucket = artifact_bucket = event["Artifact"]["Location"]["S3Bucket"]
        artifact_key = event["Artifact"]["Location"]["S3Key"]
        manifest_key = event["ResourceKey"]
        runtimes = event["Artifact"]["Runtimes"]

        layer_name = _layer_name(project_name=project_name, runtimes=runtimes)
        layer_arn, layer_version = _publish_layer(
            project_name=project_name, artifact_bucket=artifact_bucket, artifact_key=artifact_key, runtimes=runtimes
        )
        _set_layer_permissions(layer_arn=layer_arn, layer_version=layer_version, manifest_key=manifest_key)
        layer_manifest_key = _publish_layer_manifest(
            layer_name=layer_name,
            layer_arn=layer_arn,
            layer_version=layer_version,
            manifest_bucket=manifest_bucket,
            manifest_key=manifest_key,
        )
        return dict(
            ProjectName=project_name,
            Layer=dict(Arn=layer_arn, Version=layer_version),
            Manifest=dict(S3Bucket=_bucket_name, S3Key=layer_manifest_key),
        )
    except Exception:
        # TODO: Turn these into known-cause state machine failures.
        raise
