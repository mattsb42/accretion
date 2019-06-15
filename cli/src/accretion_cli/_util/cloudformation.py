"""Utilities for working with CloudFormation stacks."""
import uuid

from . import boto3_session, Deployment

__all__ = ("artifacts_bucket", "deploy_stack", "destroy_stack")


def deploy_stack(*, region: str, template: str, **parameters) -> str:
    """Deploy a new CloudFormation stack in a thread-friendly way.

    :param str region: AWS region to target
    :param str template: Stack template body
    :param parameters: Stack parameters
    :return: Name of deployed stack
    :rtype: str
    """
    stack_name = f"Accretion-{uuid.uuid4()}"
    session = boto3_session(region=region)
    cfn_client = session.client("cloudformation")

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
    session = boto3_session(region=region)
    cfn_client = session.client("cloudformation")

    cfn_client.delete_stack(StackName=stack_name)

    stack_destroyed = cfn_client.get_waiter("stack_delete_complete")
    stack_destroyed.wait(StackName=stack_name, WaiterConfig=dict(MaxAttempts=50))


def artifacts_bucket(*, region: str, regional_record: Deployment) -> str:
    """"""
    session = boto3_session(region=region)
    cfn_client = session.client("cloudformation")

    response = cfn_client.describe_stack_resource(
        StackName=regional_record.Core,
        LogicalResourceId="SourceBucket"
    )

    return response["StackResourceDetail"]["PhysicalResourceId"]
