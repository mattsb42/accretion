"""Commands for ``accretion add``."""
import click

from .artifact_builder import add_artifact_builder
from .layer_builder import add_layer_builder
from .builders import add_all_builders

__all__ = ("add_to_deployment",)


@click.group("add")
def add_to_deployment():
    """Add things to a deployment."""


add_to_deployment.add_command(add_artifact_builder)
add_to_deployment.add_command(add_layer_builder)
add_to_deployment.add_command(add_all_builders)
