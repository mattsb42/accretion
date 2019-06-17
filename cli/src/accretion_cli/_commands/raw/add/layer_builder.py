"""Command for ``accretion raw add layer-builder``."""
import sys
import threading

import click
from accretion_common.constants import SOURCE_PREFIX

from ...._templates import replication_listener as template_builder
from ...._util import Deployment, DeploymentFile
from ...._util.cloudformation import artifacts_bucket, deploy_stack
from ...._util.parameters import try_to_load_deployment_file, try_to_write_deployment_file
from ...._util.s3 import upload_artifact
from ...._util.workers_zip import build_worker_bytes

__all__ = ("add_layer_builder", "deploy_all_regions")


def _deploy_in_region(*, region: str, deployment: Deployment, workers_zip_data: bytes):
    """Upload the workers data into a region and deploy the artifact builder stack."""
    # Upload workers zip to core stack bucket
    click.echo(f"Locating artifacts bucket in region {region}")
    bucket = artifacts_bucket(region=region, regional_record=deployment)
    click.echo(f"Uploading workers zip to {bucket} bucket in {region}")
    key = upload_artifact(region=region, bucket=bucket, prefix=SOURCE_PREFIX, artifact_data=workers_zip_data)
    click.echo(f"Workers zip uploaded in {region}")
    # Deploy artifact builder in region
    template = template_builder.build()
    click.echo(f"Deploying Layer Builder template in {region}")
    stack_name = deploy_stack(
        region=region, template=template.to_json(), allow_iam=True, ReplicationBucket=bucket, WorkersS3Key=key
    )
    deployment.LayerBuilder = stack_name
    click.echo(f"Layer builder stack {stack_name} successfully deployed in {region}")


def deploy_all_regions(*, record: DeploymentFile, workers_zip_data: bytes):
    """Deploy layer builder in all regions."""

    calls = []

    for region, regional_record in record.Deployments.items():
        if regional_record.Core is None:
            click.echo(f"Region {region} in deployment file is not initialized. Skipping.", file=sys.stderr)
            continue

        if regional_record.LayerBuilder is not None:
            click.echo(f"Layer builder is already deployed in {region}. Skipping.", file=sys.stdout)
            continue

        call = threading.Thread(
            target=_deploy_in_region,
            kwargs=dict(region=region, deployment=regional_record, workers_zip_data=workers_zip_data),
            name=region,
        )
        calls.append(call)
        call.start()

    for call in calls:
        call.join()


@click.command("layer-builder")
@click.argument("deployment_file", required=True, type=click.STRING)
def add_layer_builder(deployment_file: str):
    """Add the layer builder to an existing deployment described in DEPLOYMENT_FILE."""
    record = try_to_load_deployment_file(deployment_file_name=deployment_file)

    workers_zip_data = build_worker_bytes()

    # deploy to all regions
    deploy_all_regions(record=record, workers_zip_data=workers_zip_data)

    try_to_write_deployment_file(deployment_filename=deployment_file, record=record)
