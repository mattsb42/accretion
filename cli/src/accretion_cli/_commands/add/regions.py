"""Command for ``accretion add regions``."""
from typing import Iterable

import click

from ..._util import Deployment
from ..._util.parameters import try_to_load_deployment_file, try_to_write_deployment_file
from ..._util.workers_zip import build_worker_bytes
from .. import init
from . import artifact_builder, layer_builder

__all__ = ("add_more_regions",)


@click.command("regions")
@click.argument("deployment_file", required=True, type=click.STRING)
@click.argument("regions", required=True, type=click.STRING, nargs=-1)
def add_more_regions(deployment_file: str, regions: Iterable[str]):
    """Add more regions to an existing deployment."""
    record = try_to_load_deployment_file(deployment_file_name=deployment_file)

    for region in regions:
        if region not in record.Deployments:
            record.Deployments[region] = Deployment()

    init.init_all_regions(regions=regions, record=record)

    workers_zip_data = build_worker_bytes()

    artifact_builder.deploy_all_regions(record=record, workers_zip_data=workers_zip_data)
    layer_builder.deploy_all_regions(record=record, workers_zip_data=workers_zip_data)

    try_to_write_deployment_file(deployment_filename=deployment_file, record=record)
