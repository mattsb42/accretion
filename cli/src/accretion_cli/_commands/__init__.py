"""Accretion CLI commands."""

import click

from .init import destroy_project, init_project
from .raw import raw_cli


@click.group()
def cli():
    """Main entry point."""


cli.add_command(init_project)
cli.add_command(destroy_project)
cli.add_command(raw_cli)
