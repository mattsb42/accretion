"""Given a new artifact manifest, determine whether the artifact is present."""
import json
import os
from typing import Dict

import boto3
from botocore.exceptions import ClientError

S3_BUCKET = "S3_BUCKET"
_is_setup = False


def _setup():
    global _bucket_name
    _bucket_name = os.environ[S3_BUCKET]

    global _s3
    _s3 = boto3.client("s3")

    global _is_setup
    _is_setup = True


def _artifact_exists(artifact_key: str) -> bool:
    try:
        _s3.head_object(
            Bucket=_bucket_name,
            Key=artifact_key
        )
    except ClientError:
        return False
    else:
        return True


def _load_manifest(manifest_key: str) -> Dict:
    response = _s3.get_object(
        Bucket=_bucket_name,
        Key=manifest_key,
    )
    return json.loads(response["Body"].read().decode("utf-8"))


def lambda_handler(event, context):
    """
    Since we are depending on S3 Cross-Region Replication to replicate both
    the built artifact and the artifact manifest,
    the manifest might exist in a target region before the artifact.

    Read the manifest to find the artifact and determine if it has replicated yet.

    Event shape:

    ..code:: json

        {
            "ResourceKey": "S3 key containing object that triggered event",
            "ProcessEvent": boolean decision stating whether to continue processing event
        }

    Return shape:

    ..code:: json

        {
            "Found": boolean statement whether artifact exists yet,
            "ArtifactLocation": {
                "S3Bucket": "S3 bucket containing artifact",
                "S3Key": "S3 key in bucket containing artifact"
            }
        }

    :param event:
    :param context:
    :return:
    """
    if not _is_setup:
        _setup()

    manifest = _load_manifest(event["ResourceKey"])
    artifact_location = dict(S3Bucket=_bucket_name, S3Key=manifest["ArtifactS3Key"])
    artifact_exists = _artifact_exists(manifest["ArtifactS3Key"])
    return dict(Found=artifact_exists, ArtifactLocation=artifact_location)
