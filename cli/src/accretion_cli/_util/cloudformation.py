"""Utilities for working with CloudFormation stacks."""
import uuid

import boto3
import botocore.session

__all__ = ("deploy_stack", "destroy_stack")


def _boto3_session(*, region: str) -> boto3.session.Session:
    """Generate a threading-friendly boto3 session for ``region``.

    :param str region: Region to target
    :return: independent boto3 session for ``region``
    :rtype: boto3.session.Session
    """
    botocore_session = botocore.session.Session()
    return boto3.session.Session(botocore_session=botocore_session, region_name=region)


def deploy_stack(*, region: str, template: str, **parameters) -> str:
    """Deploy a new CloudFormation stack in a thread-friendly way.

    :param str region: AWS region to target
    :param str template: Stack template body
    :param parameters: Stack parameters
    :return: Name of deployed stack
    :rtype: str
    """
    stack_name = f"Accretion-{uuid.uuid4()}"
    boto3_session = _boto3_session(region=region)
    cfn_client = boto3_session.client("cloudformation")

    kwargs = dict(StackName=stack_name, TemplateBody=template)

    if parameters:
        kwargs["Parameters"] = [dict(ParameterKey=key, ParameterValue=value) for key, value in kwargs.items()]

    cfn_client.create_stack(**kwargs)

    created_waiter = cfn_client.get_waiter("stack_create_complete")
    created_waiter.wait(StackName=stack_name, WaiterConfig=dict(MaxAttempts=50))

    return stack_name


def destroy_stack(*, region: str, stack_name: str):
    """Destroy the specified stack in the specified region.

    :param str region: AWS region containing stack
    :param str stack_name: Stack name
    """
    # TODO: Empty buckets...
    boto3_session = _boto3_session(region=region)
    cfn_client = boto3_session.client("cloudformation")

    cfn_client.delete_stack(StackName=stack_name)

    stack_destroyed = cfn_client.get_waiter("stack_delete_complete")
    stack_destroyed.wait(StackName=stack_name, WaiterConfig=dict(MaxAttempts=50))
