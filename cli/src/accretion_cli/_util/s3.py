"""Utilities for working with S3."""
import uuid

from . import boto3_session

__all__ = ("upload_artifact",)


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
