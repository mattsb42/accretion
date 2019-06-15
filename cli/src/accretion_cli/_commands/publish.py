"""Command for ``accretion publish``."""
import json
import sys
from typing import IO

import click

from .._util import Deployment, DeploymentFile
from .._util.cloudformation import artifact_builder_state_machine
from .._util.step_functions import start_execution


def _publish_in_single_region(*, region: str, regional_record: Deployment, request: str):
    """"""
    # find the ArtifactBuilderStateMachine physical name
    state_machine_arn = artifact_builder_state_machine(region=region, regional_record=regional_record)
    # trigger SFn state machine
    click.echo(f"Requesting layer build in {region} from {state_machine_arn}")
    start_execution(region=region, state_machine=state_machine_arn, event_input=request)


def _publish_to_all_regions(*, record: DeploymentFile, request: str):
    """"""
    for region, regional_record in record.Deployments.items():
        if regional_record.ArtifactBuilder is None:
            click.echo(f"Artifact builder is not deployed in {region}. Skipping.", file=sys.stdout)

        _publish_in_single_region(region=region, regional_record=regional_record, request=request)


@click.command("publish")
@click.argument("deployment_file", required=True, type=click.File("r", encoding="utf-8"))
@click.argument("request_file", required=True, type=click.File("r", encoding="utf-8"))
def publish_new_layer(deployment_file: IO, request_file: IO):
    """Request a new layer based on a request config.

    .. code:: json

        {
            "Name": "layer name",
            "Language": "Language to target",
            "Requirements": {
                "Type": "ready",
                "Requirements": [
                    {
                        "Name": "Requirement Name",
                        "Version": "Requirement Version"
                    }
                ]
            },
            "Requirements": {
                "Type": "requirements.txt",
                "Requirements": "Raw contents of requirements.txt file format"
            }
        }

    .. note::

        Language must be a valid
        `runtime prefix <https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html>`_
        (ex: "python", "java", etc).

    """
    record = DeploymentFile.from_dict(json.load(deployment_file))

    request = request_file.read()
    # TODO: Validate the request

    _publish_to_all_regions(record=record, request=request)
