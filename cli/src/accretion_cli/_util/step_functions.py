"""Utilities for working with Step Functions stacks."""
import uuid

from .._util import boto3_session

__all__ = ("start_execution",)


def start_execution(*, region: str, state_machine: str, event_input: str):
    """"""
    session = boto3_session(region=region)
    client = session.client("stepfunctions")

    client.start_execution(stateMachineArn=state_machine, name=f"Accretion_CLI-{uuid.uuid4()}", input=event_input)
