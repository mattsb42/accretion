"""Upload a built artifact to S3."""
import hashlib
import os
from typing import Dict, Iterable, Optional

from botocore.client import BaseClient
from botocore.exceptions import ClientError

from accretion_common.constants import ARTIFACTS_PREFIX

from .zipper import build_zip

__all__ = ("artifact_exists", "efficient_build_and_upload_zip")


def _key_hash(installed: Iterable[Dict[str, str]], runtime_name: str, force_new: bool) -> str:
    """Construct a deterministic ID based on the installed requirements and the runtime.

    :param list installed: List of installed package names and versions.
    :param str runtime_name: Lambda runtimes that this artifact supports.
    :param bool force_new: Should we force a new S3 object creation?
    :return: Hash ID.
    :rtype: str
    """
    hasher = hashlib.sha256()

    hasher.update(b"===INSTALLED===")
    for statement in sorted([package["Name"] + "-" + package["Version"] for package in installed]):
        hasher.update(statement.encode("utf-8"))

    hasher.update(b"===RUNTIMES===")
    hasher.update(runtime_name.encode("utf-8"))

    if force_new:
        hasher.update(os.urandom(32))

    return hasher.hexdigest()


def artifact_exists(s3_client: BaseClient, bucket_name: str, artifact_key: str) -> bool:
    """Determine if the specified S3 object exists.

    :param s3_client: Boto3 client to use for S3 interaction.
    :param bucket_name: S3 bucket name.
    :param artifact_key: S3 object key.
    :return: Statement of whether or not object exists.
    :rtype: bool
    """
    try:
        s3_client.head_object(Bucket=bucket_name, Key=artifact_key)
    except ClientError:
        return False
    else:
        return True


def efficient_build_and_upload_zip(
    s3_client: BaseClient,
    project_name: str,
    installed: Iterable[Dict[str, str]],
    bucket_name: str,
    build_dir: str,
    runtime_name: str,
    force_new: Optional[bool] = False,
) -> str:
    """Construct zip file from built artifacts and upload it to S3.

    .. note::

        By default, the S3 key is based on a deterministic hash of the installed requirements.
        This lets us only upload a new object if it is actually new.
        If you want to override this and create a new object anyway, set ``force_new=True``.

    :param s3_client: Boto3 client to use for S3 interaction.
    :param str project_name: Project name to use in S3 key.
    :param installed: List of all installed packages and versions. Used to calculate the S3 key.
    :param str build_dir: Directory from which to collect built resources.
    :param str bucket_name: S3 bucket to use.
    :param str runtime_name: Lambda runtime that this artifact supports. Used to calculate the S3 key.
    :param bool force_new: Should we force a new S3 object creation? Used to calculate the S3 key.
    :return: S3 key containing zip file.
    :rtype: str
    """
    artifact_id = _key_hash(installed=installed, runtime_name=runtime_name, force_new=force_new)
    key = f"{ARTIFACTS_PREFIX}{project_name}/{artifact_id}.zip"

    if artifact_exists(s3_client, bucket_name, key):
        return key

    zip_buffer = build_zip(build_dir)

    s3_client.put_object(Bucket=bucket_name, Key=key, Body=zip_buffer)
    return key
