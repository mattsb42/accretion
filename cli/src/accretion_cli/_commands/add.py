"""Commands for ``accretion add``."""
from typing import Iterable

import click

from .._util import Deployment
from .._util.parameters import try_to_load_deployment_file, try_to_write_deployment_file


@click.group("add")
def add_to_deployment_file():
    """Add resources to a deployment file."""


@add_to_deployment_file.command("regions")
@click.argument("deployment_file", required=True, type=click.STRING)
@click.argument("regions", required=True, type=click.STRING, nargs=-1)
def add_more_regions(deployment_file: str, regions: Iterable[str]):
    """Add more REGIONS to an existing deployment description in DEPLOYMENT_FILE.

    This does NOT deploy to those regions.

    Run "accretion update" to update and fill all regions in a deployment file.
    """
    record = try_to_load_deployment_file(deployment_file_name=deployment_file)

    for region in regions:
        if region not in record.Deployments:
            record.Deployments[region] = Deployment()

    try_to_write_deployment_file(deployment_filename=deployment_file, record=record)
