"""Command for ``accretion add artifact-builder``."""
import io
import sys
import threading

import click

from accretion_common.constants import SOURCE_PREFIX
from ..._templates import artifact_builder as template_builder
from ..._util import Deployment, DeploymentFile
from ..._util.parameters import try_to_load_deployment_file, try_to_write_deployment_file
from ..._util.workers_zip import build_and_write_workers
from ..._util.cloudformation import artifacts_bucket, deploy_stack
from ..._util.s3 import upload_artifact

__all__ = ("add_artifact_builder",)


def _deploy_in_region(*, region: str, deployment: Deployment, workers_zip_data: bytes):
    """Upload the workers data into a region and deploy the artifact builder stack."""
    # Upload workers zip to core stack bucket
    bucket = artifacts_bucket(region=region, regional_record=deployment)
    key = upload_artifact(
        region=region,
        bucket=bucket,
        prefix=SOURCE_PREFIX,
        artifact_data=workers_zip_data
    )
    # Deploy artifact builder in region
    template = template_builder.build()
    deploy_stack(region=region, template=template.to_json(), ArtifactBucketName=bucket, WorkersS3Key=key)


def _deploy_all_regions(*, record: DeploymentFile, workers_zip_data: bytes):
    """Deploy artifact builder in all regions."""

    calls = []

    for region, regional_record in record.Deployments.items():
        if regional_record.Core is None:
            click.echo(f'Region "{region}" in deployment file is not initialized. Skipping.', file=sys.stderr)
            continue

        if regional_record.ArtifactBuilder is not None:
            click.echo(f'Artifact builder is already deployed in "{region}". Skipping.', file=sys.stdout)
            continue

        call = threading.Thread(
            target=_deploy_in_region,
            kwargs=dict(region=region, deployment=regional_record, workers_zip_data=workers_zip_data),
        )
        calls.append(call)
        call.start()

    for call in calls:
        call.join()


@click.command("artifact-builder")
@click.argument("deployment_file", required=True, type=click.STRING)
def add_artifact_builder(deployment_file: str):
    """Add the artifact builder to an existing deployment."""
    record = try_to_load_deployment_file(deployment_file_name=deployment_file)

    # Build workers zip.
    workers_zip = io.BytesIO()
    build_and_write_workers(outfile=workers_zip)
    # Copy into bytes that we can farm out to multiple threads.
    workers_zip_data = workers_zip.getvalue()
    # Then discard the original.
    workers_zip.truncate(0)

    _deploy_all_regions(record=record, workers_zip_data=workers_zip_data)

    try_to_write_deployment_file(deployment_filename=deployment_file, record=record)
