"""Utilities for working with parameters."""
import json

import click

from . import DeploymentFile

__all__ = ("try_to_load_deployment_file",)


def try_to_load_deployment_file(*, deployment_file_name: str) -> DeploymentFile:
    """Try to load a deployment file, raising the appropriate error if it cannot be opened."""
    try:
        with open(deployment_file_name, "r") as deployment_file:
            return DeploymentFile.from_dict(json.load(deployment_file))
    except FileNotFoundError:
        raise click.BadParameter(message="Deployment file does not exist!")
    # TODO: Make this more specific?
    # except json.JSONDecodeError:
    except Exception:
        raise click.BadParameter(message="Invalid deployment file!")
