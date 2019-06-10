"""Raw CLI commands."""
from typing import IO

import click

from .._build_zip import build_and_write_workers
from .._templates import artifact_builder, replication_listener, source_region_core

_TEMPLATES = {"builder": artifact_builder, "listener": replication_listener, "core-source": source_region_core}


@click.group("raw")
def raw_cli():
    """Raw Accretion commands. Not recommended for direct use."""


@raw_cli.command()
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


@raw_cli.command()
@click.argument("output", type=click.File(mode="wb"))
def build_workers(output: IO):
    """Build the workers zip file.

    OUTPUT : Where to write the template?
    \f

    :param str output: Where to write the workers zip?
    """
    build_and_write_workers(output)
