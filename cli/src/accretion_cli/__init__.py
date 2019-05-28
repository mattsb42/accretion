"""Accretion CloudFormation template artifact_builder."""
import click

from ._templates import artifact_builder, replication_listener

__version__ = "0.0.1"
_TEMPLATES = {
    "builder": artifact_builder,
    "listener": replication_listener,
}


@click.group()
def cli():
    """Main entry point."""


@cli.command()
@click.argument("template_type", type=click.Choice(_TEMPLATES.keys()))
@click.argument("output", type=click.File(mode="w", encoding="utf-8"))
def generate(template_type, output):
    """Generate a template.

    OUTPUT : Where to write the template?
    \f

    :param str template_type: The type of template to generate.
    :param str output: Where to write the template?
    """
    template = _TEMPLATES[template_type].build()
    output.write(template.to_json(indent=4))
