"""Command for ``accretion raw add regions``."""
from typing import Iterable

import click

from ...._commands.update.all import update_all_regions
from ...._util import Deployment
from ...._util.parameters import try_to_load_deployment_file, try_to_write_deployment_file

__all__ = ("add_more_regions",)


@click.command("regions")
@click.argument("deployment_file", required=True, type=click.STRING)
@click.argument("regions", required=True, type=click.STRING, nargs=-1)
def add_more_regions(deployment_file: str, regions: Iterable[str]):
    """Add more regions to an existing deployment described in DEPLOYMENT_FILE."""
    record = try_to_load_deployment_file(deployment_file_name=deployment_file)

    for region in regions:
        if region not in record.Deployments:
            record.Deployments[region] = Deployment()

    update_all_regions(record=record)

    try_to_write_deployment_file(deployment_filename=deployment_file, record=record)
