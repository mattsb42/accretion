""""""
from collections import defaultdict
from functools import partial

import attr
import boto3
import botocore.session
from attr.validators import deep_mapping, instance_of, optional

__all__ = ("Deployment", "DeploymentFile", "boto3_session")


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


def boto3_session(*, region: str) -> boto3.session.Session:
    """Generate a threading-friendly boto3 session for ``region``.

    :param str region: Region to target
    :return: independent boto3 session for ``region``
    :rtype: boto3.session.Session
    """
    botocore_session = botocore.session.Session()
    return boto3.session.Session(botocore_session=botocore_session, region_name=region)
