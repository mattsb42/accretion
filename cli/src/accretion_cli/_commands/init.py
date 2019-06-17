"""Command for ``accretion init``."""
import json
from typing import IO, Iterable

import attr
import click

from .._util import Deployment, DeploymentFile


@click.command("init")
@click.argument("deployment_file", required=True, type=click.File("w", encoding="utf-8"))
@click.argument("regions", required=True, type=click.STRING, nargs=-1)
def init_deployment_file(deployment_file: IO, regions: Iterable[str]):
    """Initialize the DEPLOYMENT_FILE for deployments to REGIONS.

    This does NOT deploy to those regions.

    Run "accretion update" to update and fill all regions in a deployment file.
    """
    record = DeploymentFile(Deployments={region: Deployment() for region in regions})

    deployment_dict = attr.asdict(record, filter=lambda _attr, value: value is not None)
    json.dump(deployment_dict, deployment_file, indent=4)
