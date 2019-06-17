"""Utilities for working with CloudFormation stacks."""
import uuid

import botocore.client
import botocore.exceptions
import click

from . import Deployment, boto3_session
from .s3 import empty_bucket

__all__ = ("artifacts_bucket", "artifact_builder_state_machine", "deploy_stack", "destroy_stack", "update_stack")


def update_stack(*, region: str, stack_name: str, template: str, allow_iam: bool = False, **parameters: str):
    """Update an existing CloudFormation stack in a thread-friendly way.

    :param str region: AWS region to target
    :param str stack_name: Stack name
    :param str template: Stack template body
    :param bool allow_iam: Should this stack be allowed to create IAM resources?
    :param parameters: Stack parameters
    """
    session = boto3_session(region=region)
    cfn_client = session.client("cloudformation")

    kwargs = dict(StackName=stack_name, TemplateBody=template)

    if allow_iam:
        kwargs["Capabilities"] = ["CAPABILITY_IAM"]

    if parameters:
        kwargs["Parameters"] = [dict(ParameterKey=key, ParameterValue=value) for key, value in parameters.items()]

    try:
        cfn_client.update_stack(**kwargs)
    except botocore.exceptions.ClientError as error:
        try:
            message = error.response["Error"]["Message"]
        except KeyError:
            raise error

        if message == "No updates are to be performed.":
            click.echo(f"Stack {stack_name} in {region} is already up to date.")
            return

        raise

    created_waiter = cfn_client.get_waiter("stack_update_complete")
    created_waiter.wait(StackName=stack_name, WaiterConfig=dict(MaxAttempts=50))


def deploy_stack(*, region: str, template: str, allow_iam: bool = False, **parameters: str) -> str:
    """Deploy a new CloudFormation stack in a thread-friendly way.

    :param str region: AWS region to target
    :param str template: Stack template body
    :param bool allow_iam: Should this stack be allowed to create IAM resources?
    :param parameters: Stack parameters
    :return: Name of deployed stack
    :rtype: str
    """
    stack_name = f"Accretion-{uuid.uuid4()}"
    session = boto3_session(region=region)
    cfn_client = session.client("cloudformation")

    kwargs = dict(StackName=stack_name, TemplateBody=template)

    if allow_iam:
        kwargs["Capabilities"] = ["CAPABILITY_IAM"]

    if parameters:
        kwargs["Parameters"] = [dict(ParameterKey=key, ParameterValue=value) for key, value in parameters.items()]

    cfn_client.create_stack(**kwargs)

    created_waiter = cfn_client.get_waiter("stack_create_complete")
    created_waiter.wait(StackName=stack_name, WaiterConfig=dict(MaxAttempts=50))

    return stack_name


def _all_buckets(*, client: botocore.client.BaseClient, stack: str):
    """"""
    complete = False
    next_token = None
    click.echo(f"Looking for buckets in stack {stack}")
    while not complete:
        kwargs = dict(StackName=stack)
        if next_token is not None:
            kwargs["NextToken"] = next_token

        response = client.list_stack_resources(**kwargs)

        try:
            next_token = response["NextToken"]
        except KeyError:
            complete = True

        for resource in response["StackResourceSummaries"]:
            if resource["ResourceType"] == "AWS::S3::Bucket":
                bucket = resource["PhysicalResourceId"]
                click.echo(f"Found bucket {bucket}")
                yield bucket


def destroy_stack(*, region: str, stack_name: str):
    """Destroy the specified stack in the specified region.

    :param str region: AWS region containing stack
    :param str stack_name: Stack name
    """
    session = boto3_session(region=region)
    cfn_client = session.client("cloudformation")

    for bucket in _all_buckets(client=cfn_client, stack=stack_name):
        empty_bucket(region=region, bucket=bucket)

    cfn_client.delete_stack(StackName=stack_name)

    stack_destroyed = cfn_client.get_waiter("stack_delete_complete")
    stack_destroyed.wait(StackName=stack_name, WaiterConfig=dict(MaxAttempts=50))


def _resource_physical_id(*, region: str, stack_name: str, logical_resource_id: str) -> str:
    """"""
    session = boto3_session(region=region)
    cfn_client = session.client("cloudformation")

    response = cfn_client.describe_stack_resource(StackName=stack_name, LogicalResourceId=logical_resource_id)

    return response["StackResourceDetail"]["PhysicalResourceId"]


def artifacts_bucket(*, region: str, regional_record: Deployment) -> str:
    """"""
    return _resource_physical_id(region=region, stack_name=regional_record.Core, logical_resource_id="SourceBucket")


def artifact_builder_state_machine(*, region: str, regional_record: Deployment) -> str:
    """"""
    return _resource_physical_id(
        region=region, stack_name=regional_record.ArtifactBuilder, logical_resource_id="ArtifactBuilderStateMachine"
    )
