"""Command for ``accretion init``."""
import json
import threading
from typing import IO, Iterable

import attr
import click

from .._templates import source_region_core
from .._util import Deployment, DeploymentFile
from .._util.cloudformation import deploy_stack

__all__ = ("init_project",)


def _init_in_region(*, region: str, deployment: Deployment):
    """Deploy a single init stack in a single region.

    :param str region: Region to target
    :param Deployment deployment: :class:`Deployment` describing deployment
    """
    click.echo(f"Deploying Core template in {region}")
    stack_name = deploy_stack(region=region, template=source_region_core.build().to_json())
    click.echo(f"Core stack {stack_name} successfully deployed in {region}")
    deployment.Core = stack_name


def _init_all_regions(*, regions: Iterable[str], record: DeploymentFile):
    """Initialize deployment in all target regions.

    :param regions: Regions to target
    :param record: :class:`DeploymentFile` describing deployment
    """
    calls = []
    for region in regions:
        call = threading.Thread(
            target=_init_in_region, kwargs=dict(region=region, deployment=record.Deployments[region])
        )
        calls.append(call)
        call.start()

    for call in calls:
        call.join()


@click.command("init")
@click.argument("deployment_file", required=True, type=click.File("w", encoding="utf-8"))
@click.argument("regions", required=True, type=click.STRING, nargs=-1)
def init_project(deployment_file: IO, regions: Iterable[str]):
    """Deploy an initial Accretion project.
    Accretion is initialized in REGIONS regions.
    \f

    :param deployment_file: File to which to write deployment data
    :param regions: List of region names
    """
    regions = set(regions)

    record = DeploymentFile()

    _init_all_regions(regions=regions, record=record)

    json.dump(attr.asdict(record, filter=lambda _attr, value: value is not None), deployment_file, indent=4)
