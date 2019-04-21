"""Build the CloudFormation template for the Accretion artifact builder."""
from functools import partial
from typing import Callable, Dict, Iterable

from troposphere import Template, Tags, Parameter, iam, awslambda
from awacs import aws as AWS

from accretion_cli._iam import lambda_role, s3_put_object_statement
from accretion_cli._stepfunctions import add_artifact_builder


_DEFAULT_TAGS = Tags(Accretion="ArtifactBuilder")


def _lambda_environment(bucket_name: Parameter) -> awslambda.Environment:
    return awslambda.Environment(Variables=dict(S3_BUCKET=bucket_name.ref()))


def _lambda_function(
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
        Tags=_DEFAULT_TAGS,
    )


def _add_lambda_core(
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


def _add_parse_requirements_resources(lambda_adder: Callable) -> awslambda.Function:
    return lambda_adder(
        base_name="ParseRequirements",
        statements=[],
        lambda_args=dict(runtime="python3.7", module="requirements_parser", memory_size=128, timeout=15),
    )


def _add_build_python(lambda_adder: Callable, runtime: str, bucket_name: Parameter) -> awslambda.Function:
    base_name = "PythonBuilder" + runtime.replace(".", "").replace("python", "")
    statements = s3_put_object_statement(
        *[f"${{{bucket_name.title}}}/accretion/{group}/" for group in ("artifacts", "manifests")]
    )

    return lambda_adder(
        base_name=base_name,
        statements=statements,
        lambda_args=dict(runtime=runtime, module="zip_builder", memory_size=2048, timeout=900),
    )


def build() -> Template:
    builder = Template(Description="Accretion artifact builder resources")

    bucket_name = builder.add_parameter(
        Parameter("ArtifactBucketName", Type="String", Description="Name of artifacts bucket")
    )
    workers_key = builder.add_parameter(
        Parameter("WorkersS3Key", Type="String", Description="S3 key in artifacts bucket containing workers zip")
    )
    boto3_layer = builder.add_parameter(
        Parameter(
            "Boto3LambdaLayer", Type="String", Description="Lambda Layer Version Arn containing recent boto3 build"
        )
    )

    _lambda_builder = partial(
        _lambda_function, bucket_name=bucket_name, workers_key=workers_key, boto3_layer=boto3_layer
    )
    lambda_adder = partial(_add_lambda_core, builder=builder, lambda_builder=_lambda_builder)

    parse_requirements = _add_parse_requirements_resources(lambda_adder)

    python36_builder = _add_build_python(lambda_adder, "python3.6", bucket_name)
    python37_builder = _add_build_python(lambda_adder, "python3.7", bucket_name)

    # Step Function state machine
    add_artifact_builder(
        builder=builder,
        parse_requirements=parse_requirements,
        python36_builder=python36_builder,
        python37_builder=python37_builder,
        tags=_DEFAULT_TAGS,
    )

    return builder
