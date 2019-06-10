"""Commands for ``accretion init``."""
import json
import threading
from time import sleep
from typing import IO, Iterable, List

import attr
import click

from .._templates import source_region_core
from .._util import Deployment, DeploymentFile, deploy_stack, destroy_stack


def _not_none_filter(_attr, value):
    return value is not None


def _init_in_region(*, region: str, deployment: Deployment):
    """"""
    click.echo(f"Deploying Core template in {region}")
    stack_name = deploy_stack(region=region, template=source_region_core.build().to_json())
    click.echo(f"Core stack {stack_name} successfully deployed in {region}")
    deployment.Core = stack_name


def _init_all_regions(*, regions: Iterable[str], record: DeploymentFile):
    """"""
    calls = []
    for region in regions:
        call = threading.Thread(
            target=_init_in_region, kwargs=dict(region=region, deployment=record.Deployments[region])
        )
        calls.append(call)
        call.start()

    for call in calls:
        call.join()


def _destroy_stack_in_region(*, region: str, logical_name: str, stack_name: str):
    """"""
    click.echo(f"Destroying {logical_name} stack {stack_name} in {region}")
    destroy_stack(region=region, stack_name=stack_name)
    click.echo(f"{logical_name} stack {stack_name} successfully destroyed in {region}")


def _destroy_in_region(*, region: str, dep: Deployment, calls: List[threading.Thread]):
    """"""
    for field in attr.fields(Deployment):
        logical_name = field.name
        stack_name = getattr(dep, logical_name)

        if stack_name is not None:
            call = threading.Thread(
                target=_destroy_stack_in_region,
                kwargs=dict(region=region, logical_name=logical_name, stack_name=stack_name),
            )
            calls.append(call)
            call.start()


def _destroy_all_regions(*, record: DeploymentFile):
    """"""
    calls = []

    for region, stacks in record.Deployments.items():
        _destroy_in_region(region=region, dep=stacks, calls=calls)

    for call in calls:
        call.join()


@click.command("init")
@click.argument("deployment_file", type=click.File("w", encoding="utf-8"))
@click.argument("regions", type=click.STRING, nargs=-1)
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

    json.dump(attr.asdict(record, filter=_not_none_filter), deployment_file, indent=4)


@click.command("destroy")
@click.argument("deployment_file", type=click.File("r", encoding="utf-8"))
def destroy_project(deployment_file: IO):
    """Destroy an Accretion deployment described in DEPLOYMENT_FILE.
    \f

    :param deployment_file: File containing deployment data
    """
    record = DeploymentFile.from_dict(json.load(deployment_file))

    _destroy_all_regions(record=record)
