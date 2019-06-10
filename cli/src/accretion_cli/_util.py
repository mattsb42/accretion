""""""
import uuid
from collections import defaultdict
from functools import partial

import attr
import boto3
import botocore.session
from attr.validators import deep_mapping, instance_of, optional


@attr.s
class Deployment:
    Core = attr.ib(default=None, validator=optional(instance_of(str)))
    ArtifactBuilder = attr.ib(default=None, validator=optional(instance_of(str)))
    LayerBuilder = attr.ib(default=None, validator=optional(instance_of(str)))


@attr.s
class DeploymentFile:
    Deployments = attr.ib(
        default=attr.Factory(partial(defaultdict, Deployment)),
        validator=deep_mapping(key_validator=instance_of(str), value_validator=instance_of(Deployment)),
    )

    @classmethod
    def from_dict(cls, kwargs):
        return cls(
            Deployments={region: Deployment(**sub_args) for region, sub_args in kwargs.get("Deployments", {}).items()}
        )


def _boto3_session(*, region: str) -> boto3.session.Session:
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
