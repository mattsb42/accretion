"""Utilities for working with parameters."""
import json
import sys

import attr
import click

from . import DeploymentFile

__all__ = ("try_to_load_deployment_file", "try_to_write_deployment_file")


def try_to_load_deployment_file(*, deployment_file_name: str) -> DeploymentFile:
    """Try to load a deployment file, raising the appropriate error if it cannot be opened."""
    try:
        with open(deployment_file_name, "r") as deployment_file:
            return DeploymentFile.from_dict(json.load(deployment_file))
    except FileNotFoundError:
        raise click.BadParameter(message="Deployment file does not exist!")
    # TODO: Add handling for permissions error
    # TODO: Make this more specific?
    # except json.JSONDecodeError:
    except Exception:
        raise click.BadParameter(message="Invalid deployment file!")


def try_to_write_deployment_file(*, deployment_filename: str, record: DeploymentFile):
    """"""
    deployment_dict = attr.asdict(record, filter=lambda _attr, value: value is not None)
    try:
        with open(deployment_filename, "w") as deployment_file:
            json.dump(deployment_dict, deployment_file, indent=4)
    # TODO: Make this more specific?
    except Exception:
        click.echo("Unable to write deployment record!", file=sys.stderr)
        click.echo(f"{deployment_dict}", file=sys.stderr)
