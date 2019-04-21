""""""
from typing import Callable, Dict, Iterable

from troposphere import awslambda, Template, Parameter, iam, Tags
from awacs import aws as AWS

from ._iam import lambda_role
from . import DEFAULT_TAGS


def _lambda_environment(bucket_name: Parameter) -> awslambda.Environment:
    return awslambda.Environment(Variables=dict(S3_BUCKET=bucket_name.ref()))


def lambda_function(
    *,
    bucket_name: Parameter,
    workers_key: Parameter,
    boto3_layer: Parameter,
    name: str,
    role: iam.Role,
    runtime: str,
    module: str,
    memory_size: int,
    timeout: int,
) -> awslambda.Function:
    return awslambda.Function(
        name,
        Role=role.get_att("Arn"),
        Code=awslambda.Code(S3Bucket=bucket_name.ref(), S3Key=workers_key.ref()),
        Handler=f"accretion_workers.layer_builder.{module}.lambda_handler",
        Environment=_lambda_environment(bucket_name),
        Runtime=runtime,
        Layers=[boto3_layer.ref()],
        MemorySize=memory_size,
        Timeout=timeout,
        Tags=DEFAULT_TAGS,
    )


def add_lambda_core(
    *,
    builder: Template,
    lambda_builder: Callable,
    base_name: str,
    statements: Iterable[AWS.Statement],
    lambda_args: Dict,
) -> awslambda.Function:
    role = lambda_role(f"{base_name}Role", *statements)

    function = lambda_builder(name=f"{base_name}Function", role=role, **lambda_args)

    builder.add_resource(role)
    builder.add_resource(function)

    return function
