"""Build the CloudFormation template for the Accretion artifact builder."""
from functools import partial
from typing import Callable, Dict

from troposphere import Template, Tags, Parameter, iam, awslambda
from awacs import aws as AWS, s3 as S3, awslambda as AWSLAMBDA

from accretion_cli._iam import lambda_role, s3_put_object_statement


_DEFAULT_TAGS = (Tags(Accretion="ArtifactBuilder"),)


def _lambda_environment(bucket_name: Parameter) -> awslambda.Environment:
    return awslambda.Environment(Variables=dict(S3_BUCKET=bucket_name.ref()))


def _lambda_function(
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
    builder: Template, lambda_builder: Callable, base_name: str, statement_builder: Callable, lambda_args: Dict
) -> awslambda.Function:
    role = lambda_role(f"{base_name}Role", *statement_builder())

    function = lambda_builder(f"{base_name}Function", role, **lambda_args)

    builder.add_resource(role)
    builder.add_resource(function)

    return function


def _add_parse_requirements_resources(lambda_adder: Callable) -> awslambda.Function:
    return lambda_adder(
        "ParseRequirements", lambda: [], dict(runtime="python3.7", module="event_filter", memory_size=128, timeout=15)
    )


def _add_build_python(lambda_adder: Callable, runtime: str, bucket_name: Parameter) -> awslambda.Function:
    base_name = "PythonBuilder" + runtime.replace(".", "")
    statement_builder = partial(
        s3_put_object_statement,
        *[f"${{{bucket_name.title}}}/accretion/{group}" for group in ("artifacts", "manifests")],
    )

    return lambda_adder(
        base_name, statement_builder, dict(runtime=runtime, module="zip_builder", memory_size=2048, timeout=900)
    )


def build() -> Template:
    builder = Template(Description="Accretion artifact builder resources")

    bucket_name = builder.add_parameter(Parameter("ArtifactBucketName", Type="String"))
    workers_key = builder.add_parameter(Parameter("WorkersS3Key", Type="String"))
    boto3_layer = builder.add_parameter(Parameter("Boto3LambdaLayer", Type="String"))

    _lambda_builder = partial(_lambda_function, bucket_name, workers_key, boto3_layer)
    lambda_adder = partial(_add_lambda_core, builder, _lambda_builder)

    parse_requirements = _add_parse_requirements_resources(lambda_adder)

    python36_builder = _add_build_python(lambda_adder, "python3.6", bucket_name)
    python37_builder = _add_build_python(lambda_adder, "python3.7", bucket_name)

    # Step Function state machine

    return builder
