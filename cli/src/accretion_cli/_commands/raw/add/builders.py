"""Command for ``accretion raw add builders``."""
import click

from ...._util.parameters import try_to_load_deployment_file, try_to_write_deployment_file
from ...._util.workers_zip import build_worker_bytes
from . import artifact_builder, layer_builder

__all__ = ("add_all_builders",)


@click.command("builders")
@click.argument("deployment_file", required=True, type=click.STRING)
def add_all_builders(deployment_file: str):
    """Add all builders to an existing deployment described in DEPLOYMENT_FILE."""
    record = try_to_load_deployment_file(deployment_file_name=deployment_file)

    workers_zip_data = build_worker_bytes()

    artifact_builder.deploy_all_regions(record=record, workers_zip_data=workers_zip_data)
    layer_builder.deploy_all_regions(record=record, workers_zip_data=workers_zip_data)

    try_to_write_deployment_file(deployment_filename=deployment_file, record=record)
