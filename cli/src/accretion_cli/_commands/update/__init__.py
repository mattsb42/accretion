"""Commands for ``accretion update``."""
import click

from .all import update_all_deployments

__all__ = ("update_deployment",)


@click.group("update")
def update_deployment():
    """Update an existing deployment."""


update_deployment.add_command(update_all_deployments)
