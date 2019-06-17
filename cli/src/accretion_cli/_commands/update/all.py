"""Command for ``accretion update all``."""
import json
import threading
from typing import Dict

import attr
import click
from accretion_common.constants import SOURCE_PREFIX

from ..._templates import artifact_builder, replication_listener, source_region_core
from ..._util import Deployment, DeploymentFile
from ..._util.cloudformation import artifacts_bucket, deploy_stack, update_stack
from ..._util.parameters import try_to_load_deployment_file, try_to_write_deployment_file
from ..._util.s3 import upload_artifact
from ..._util.workers_zip import build_worker_bytes

__all__ = ("update_single_region", "update_all_regions", "update_all_deployments")
_TEMPLATE_BUILDERS = dict(ArtifactBuilder=artifact_builder, LayerBuilder=replication_listener, Core=source_region_core)


def _template_kwargs(*, logical_name: str, bucket: str, key: str) -> Dict[str, str]:
    """Generate the template parameter arguments needed for each logical stack type."""
    if logical_name == "ArtifactBuilder":
        return dict(ArtifactBucketName=bucket, WorkersS3Key=key)
    elif logical_name == "LayerBuilder":
        return dict(ReplicationBucket=bucket, WorkersS3Key=key)
    else:
        raise ValueError(f"Unknown logical name: {logical_name}")


def _create_single_stack(
    *, region: str, logical_name: str, regional_record: Deployment, template_kwargs: Dict[str, str]
):
    """Create a single stack in a single region."""
    template = _TEMPLATE_BUILDERS[logical_name].build().to_json()

    click.echo(f"Creating {logical_name} stack in {region}")
    stack_name = deploy_stack(region=region, template=template, allow_iam=True, **template_kwargs)
    setattr(regional_record, logical_name, stack_name)
    click.echo(f"{logical_name} stack in {region} successfully created")


def _update_single_stack(*, region: str, logical_name: str, stack_name: str, template_kwargs: Dict[str, str]):
    """Update a single stack in a single region."""
    template = _TEMPLATE_BUILDERS[logical_name].build().to_json()

    click.echo(f"Updating {logical_name} stack in {region}")
    update_stack(region=region, template=template, allow_iam=True, stack_name=stack_name, **template_kwargs)
    click.echo(f"{logical_name} stack in {region} successfully updated")


def _upsert_single_stack(
    *, region: str, logical_name: str, regional_record: Deployment, template_kwargs: Dict[str, str]
):
    """Update a single stack in a single region."""
    stack_name = getattr(regional_record, logical_name)

    if stack_name is None:
        _create_single_stack(
            region=region, logical_name=logical_name, regional_record=regional_record, template_kwargs=template_kwargs
        )
    else:
        _update_single_stack(
            region=region, logical_name=logical_name, stack_name=stack_name, template_kwargs=template_kwargs
        )


def update_single_region(*, region: str, regional_record: Deployment, workers_zip_data: bytes):
    """Update all stacks in a single region.

    :param str region: Region name
    :param Deployment regional_record: :class:`Deployment` record that describes the deployment in region
    :param bytes workers_zip_data: Zip file for
    :return:
    """
    click.echo("Building zip file for workers")
    _upsert_single_stack(region=region, logical_name="Core", regional_record=regional_record, template_kwargs=dict())

    # Upload workers zip to core stack bucket
    click.echo(f"Locating artifacts bucket in region {region}")
    bucket = artifacts_bucket(region=region, regional_record=regional_record)
    click.echo(f"Uploading workers zip to {bucket} bucket in {region}")
    workers_zip_key = upload_artifact(
        region=region, bucket=bucket, prefix=SOURCE_PREFIX, artifact_data=workers_zip_data
    )
    click.echo(f"Workers zip uploaded in {region}")

    # Update all other stacks
    calls = []
    for field in attr.fields(Deployment):
        if field.name == "Core":
            continue

        template_kwargs = _template_kwargs(logical_name=field.name, bucket=bucket, key=workers_zip_key)

        call = threading.Thread(
            target=_upsert_single_stack,
            kwargs=dict(
                region=region, logical_name=field.name, regional_record=regional_record, template_kwargs=template_kwargs
            ),
        )
        calls.append(call)
        call.start()

    for call in calls:
        call.join()


def update_all_regions(*, record: DeploymentFile):
    """Update all stacks in all regions for a given deployment.

    :param DeploymentFile record: :class:`DeploymentFile` describing deployment
    """
    calls = []

    # Build workers zip
    # Build before touching the Core stack so we can fail fast if requirements are not available.
    # TODO: Print a useful error message on failures.
    workers_zip_data = build_worker_bytes()

    for region, stacks in record.Deployments.items():
        call = threading.Thread(
            target=update_single_region,
            kwargs=dict(region=region, regional_record=stacks, workers_zip_data=workers_zip_data),
        )
        calls.append(call)
        call.start()

    for call in calls:
        call.join()


@click.command("all")
@click.argument("deployment_file", required=True, type=click.STRING)
def update_all_deployments(deployment_file: str):
    """Update deployments in all regions described in DEPLOYMENT_FILE.
    """
    record = try_to_load_deployment_file(deployment_file_name=deployment_file)

    update_all_regions(record=record)

    try_to_write_deployment_file(deployment_filename=deployment_file, record=record)
