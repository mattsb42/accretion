"""Command for ``accretion add artifact-builder``."""
import click


@click.command("artifact-builder")
@click.argument("deployment_file", required=True, type=click.STRING)
def add_artifact_builder(deployment_file: str):
    """Add the artifact builder to an existing deployment."""
