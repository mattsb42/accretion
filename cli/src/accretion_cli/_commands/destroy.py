"""Command for ``accretion destroy``."""
import json
import threading
from typing import IO, List

import attr
import click

from .._util import Deployment, DeploymentFile
from .._util.cloudformation import destroy_stack

__all__ = ("destroy_project",)


def _destroy_stack_in_region(*, region: str, logical_name: str, stack_name: str):
    """Destroy a single stack in a single region.

    :param str region: Region to target
    :param str logical_name: Logical name of stack in :class:`Deployment`
    :param str stack_name: Stack name
    """
    click.echo(f"Destroying {logical_name} stack {stack_name} in {region}")
    destroy_stack(region=region, stack_name=stack_name)
    click.echo(f"{logical_name} stack {stack_name} successfully destroyed in {region}")


def _destroy_in_region(*, region: str, dep: Deployment, calls: List[threading.Thread]):
    """Destroy all stacks in a single region.

    :param str region: Region to target
    :param Deployment dep: :class:`Deployment` describing stacks to destroy
    :param calls: List collecting :class:`threading.Thread` references
    """
    for field in attr.fields(Deployment):
        logical_name = field.name
        stack_name = getattr(dep, logical_name)

        if stack_name is not None:
            call = threading.Thread(
                target=_destroy_stack_in_region,
                kwargs=dict(region=region, logical_name=logical_name, stack_name=stack_name),
                name=f"{region}:::{stack_name}",
            )
            calls.append(call)
            call.start()


def _destroy_all_regions(*, record: DeploymentFile):
    """Destroy all stacks in all regions for a given deployment.

    :param DeploymentFile record: :class:`DeploymentFile` describing deployment
    """
    calls = []

    for region, stacks in record.Deployments.items():
        _destroy_in_region(region=region, dep=stacks, calls=calls)

    for call in calls:
        call.join()


@click.command("destroy")
@click.argument("deployment_file", required=True, type=click.File("r", encoding="utf-8"))
def destroy_project(deployment_file: IO):
    """Destroy an Accretion deployment described in DEPLOYMENT_FILE.
    \f

    :param deployment_file: File containing deployment data
    """
    record = DeploymentFile.from_dict(json.load(deployment_file))

    _destroy_all_regions(record=record)
