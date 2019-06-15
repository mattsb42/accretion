"""Utilities for working with S3."""
import uuid

import botocore.client
import click

from . import boto3_session

__all__ = ("empty_bucket", "upload_artifact")


def _artifact_key(*, prefix: str) -> str:
    """"""
    return f"{prefix}{uuid.uuid4()}.zip"


def upload_artifact(*, region: str, bucket: str, prefix: str, artifact_data: bytes):
    """"""
    key = _artifact_key(prefix=prefix)

    session = boto3_session(region=region)
    s3_client = session.client("s3")

    s3_client.put_object(Bucket=bucket, Key=key, Body=artifact_data)

    return key


def _find_and_delete_versions(*, client: botocore.client.BaseClient, bucket: str):
    """"""
    response = client.list_object_versions(Bucket=bucket, MaxKeys=1000)

    more_to_process = response["IsTruncated"]

    objects = []
    for version in response.get("Versions", []):
        description = dict(Key=version["Key"], VersionId=version["VersionId"])
        if description["VersionId"] == "null":
            del description["VersionId"]
        objects.append(description)

    for marker in response.get("DeleteMarkers", []):
        objects.append(dict(Key=marker["Key"], VersionId=marker["VersionId"]))

    if objects:
        click.echo(f"Deleting {len(objects)} objects from bucket {bucket}")
        client.delete_objects(Bucket=bucket, Delete=dict(Objects=objects))

    return more_to_process


def empty_bucket(*, region: str, bucket: str):
    """"""
    session = boto3_session(region=region)
    s3_client = session.client("s3")

    confidence = 0

    click.echo(f"Emptying bucket {bucket}")
    while confidence < 2:
        more_to_process = _find_and_delete_versions(client=s3_client, bucket=bucket)

        if not more_to_process:
            confidence += 1
