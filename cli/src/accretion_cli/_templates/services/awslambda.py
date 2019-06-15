""""""
from typing import Callable, Dict, Iterable, Optional

from awacs import aws as AWS
from troposphere import Parameter, Tags, Template, awslambda, iam

from .iam import lambda_role


def _lambda_environment(bucket_name: Parameter) -> awslambda.Environment:
    return awslambda.Environment(Variables=dict(S3_BUCKET=bucket_name.ref()))


def lambda_function(
    *,
    bucket_name: Parameter,
    workers_key: Parameter,
    name: str,
    role: iam.Role,
    runtime: str,
    namespace: str,
    module: str,
    memory_size: int,
    timeout: int,
    tags: Tags,
    source_bucket: Optional[Parameter] = None,
) -> awslambda.Function:
    if source_bucket is None:
        source_bucket = bucket_name

    return awslambda.Function(
        name,
        Role=role.get_att("Arn"),
        Code=awslambda.Code(S3Bucket=source_bucket.ref(), S3Key=workers_key.ref()),
        Handler=f"accretion_workers.{namespace}.{module}.lambda_handler",
        Environment=_lambda_environment(bucket_name),
        Runtime=runtime,
        MemorySize=memory_size,
        Timeout=timeout,
        Tags=tags,
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
