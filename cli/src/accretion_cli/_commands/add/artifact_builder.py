"""Command for ``accretion add artifact-builder``."""
import click

from ..._util.parameters import try_to_load_deployment_file


@click.command("artifact-builder")
@click.argument("deployment_file", required=True, type=click.STRING)
def add_artifact_builder(deployment_file: str):
    """Add the artifact builder to an existing deployment."""
    resources = try_to_load_deployment_file(deployment_file_name=deployment_file)
