"""Accretion CLI commands."""

import click

from .init import init_project
from .destroy import destroy_project
from .raw import raw_cli
from .add import add_to_deployment


@click.group()
def cli():
    """Main entry point."""


cli.add_command(init_project)
cli.add_command(destroy_project)
cli.add_command(add_to_deployment)
cli.add_command(raw_cli)
