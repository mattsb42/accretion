"""Accretion CloudFormation template artifact_builder."""
from typing import IO

import click

from ._templates import artifact_builder, replication_listener
from ._build_zip import build_and_write_workers

__version__ = "0.0.1b0"
_TEMPLATES = {"builder": artifact_builder, "listener": replication_listener}


@click.group()
def cli():
    """Main entry point."""


@cli.command()
@click.argument("template_type", type=click.Choice(_TEMPLATES.keys()))
@click.argument("output", type=click.File(mode="w", encoding="utf-8"))
def generate(template_type: str, output: IO):
    """Generate a template.

    OUTPUT : Where to write the template?
    \f

    :param str template_type: The type of template to generate.
    :param str output: Where to write the template?
    """
    template = _TEMPLATES[template_type].build()
    output.write(template.to_json(indent=4))


@cli.command()
@click.argument("output", type=click.File(mode="wb"))
def build_workers(output: IO):
    """Build the workers zip file.

    OUTPUT : Where to write the template?
    \f

    :param str output: Where to write the workers zip?
    """
    build_and_write_workers(output)
