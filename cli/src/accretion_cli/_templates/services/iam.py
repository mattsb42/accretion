""""""
from typing import Iterable

from awacs import (
    aws as AWS,
    awslambda as AWSLAMBDA,
    events as EVENTS,
    logs as LOGS,
    s3 as S3,
    sns as SNS,
    states as STATES,
    sts as STS,
)
from awacs.helpers.trust import make_service_domain_name
from troposphere import AWS_ACCOUNT_ID, AWS_PARTITION, AWS_REGION, Sub, awslambda, iam, sns, stepfunctions


def _basic_lambda_statement() -> AWS.Statement:
    return AWS.Statement(
        Effect=AWS.Allow,
        Action=[LOGS.CreateLogGroup, LOGS.CreateLogStream, LOGS.PutLogEvents],
        Resource=[Sub(f"arn:${{{AWS_PARTITION}}}:logs:${{{AWS_REGION}}}:${{{AWS_ACCOUNT_ID}}}:*")],
    )


def _assume_policy(service: str) -> AWS.PolicyDocument:
    return AWS.PolicyDocument(
        Statement=[
            AWS.Statement(
                Principal=AWS.Principal("Service", make_service_domain_name(service)),
                Effect=AWS.Allow,
                Action=[STS.AssumeRole],
            )
        ]
    )


def _s3_object_statement(action: S3.Action, *prefixes: str) -> Iterable[AWS.Statement]:
    return [
        AWS.Statement(
            Effect=AWS.Allow,
            Action=[action],
            Resource=[Sub(f"arn:${{{AWS_PARTITION}}}:s3:::{pre}*") for pre in prefixes],
        )
    ]


def s3_put_object_statement(*prefixes: str) -> Iterable[AWS.Statement]:
    return _s3_object_statement(S3.PutObject, *prefixes)


def s3_get_object_statement(*prefixes: str) -> Iterable[AWS.Statement]:
    return _s3_object_statement(S3.GetObject, *prefixes)


def lambda_layer_permissions() -> Iterable[AWS.Statement]:
    return [
        AWS.Statement(
            Effect=AWS.Allow,
            Action=[AWSLAMBDA.PublishLayerVersion, AWSLAMBDA.AddLayerVersionPermission],
            Resource=[Sub(f"arn:${{{AWS_PARTITION}}}:lambda:${{{AWS_REGION}}}:${{{AWS_ACCOUNT_ID}}}:layer:*")],
        )
    ]


def lambda_role(name: str, *additional_statements: AWS.Statement) -> iam.Role:
    statements = [_basic_lambda_statement()]
    statements.extend(additional_statements)

    return iam.Role(
        name,
        AssumeRolePolicyDocument=_assume_policy(AWSLAMBDA.prefix),
        Policies=[iam.Policy(PolicyName=f"{name}Policy", PolicyDocument=AWS.PolicyDocument(Statement=statements))],
    )


def invoke_statement_from_lambdas(*functions: awslambda.Function) -> AWS.Statement:
    return AWS.Statement(
        Effect=AWS.Allow, Action=[AWSLAMBDA.InvokeFunction], Resource=[func.get_att("Arn") for func in functions]
    )


def publish_statement_from_topics(*topics: sns.Topic) -> AWS.Statement:
    return AWS.Statement(Effect=AWS.Allow, Action=[SNS.Publish], Resource=[top.ref() for top in topics])


def step_functions_role(name: str, *statements: AWS.Statement) -> iam.Role:
    return iam.Role(
        name,
        AssumeRolePolicyDocument=_assume_policy(STATES.prefix),
        Policies=[
            iam.Policy(PolicyName=f"{name}Policy", PolicyDocument=AWS.PolicyDocument(Statement=list(statements)))
        ],
    )


def events_trigger_stepfuntions_role(name: str, statemachine: stepfunctions.StateMachine) -> iam.Role:
    return iam.Role(
        name,
        AssumeRolePolicyDocument=_assume_policy(EVENTS.prefix),
        Policies=[
            iam.Policy(
                PolicyName=f"{name}Policy",
                PolicyDocument=AWS.PolicyDocument(
                    Statement=[
                        AWS.Statement(Effect=AWS.Allow, Action=[STATES.StartExecution], Resource=[statemachine.ref()])
                    ]
                ),
            )
        ],
    )
