"""Accretion CLI commands."""
import click

from .add import add_to_deployment_file
from .destroy import destroy_project
from .init import init_deployment_file
from .publish import publish_new_layer
from .raw import raw_cli
from .update import update_deployment


@click.group()
def cli():
    """Main entry point."""


cli.add_command(init_deployment_file)
cli.add_command(add_to_deployment_file)
cli.add_command(destroy_project)
cli.add_command(publish_new_layer)
cli.add_command(update_deployment)
cli.add_command(raw_cli)
