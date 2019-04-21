""""""
from typing import Iterable

from troposphere import AWS_ACCOUNT_ID, AWS_PARTITION, AWS_REGION, Sub, iam, awslambda, sns
from awacs import aws as AWS, logs as LOGS, sts as STS, awslambda as AWSLAMBDA, s3 as S3, states as STATES, sns as SNS
from awacs.helpers.trust import make_service_domain_name


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


def s3_put_object_statement(*prefixes: str) -> Iterable[AWS.Statement]:
    return [
        AWS.Statement(
            Effect=AWS.Allow,
            Action=[S3.PutObject],
            Resource=[Sub(f"arn:${{{AWS_PARTITION}}}:s3:::{pre}*") for pre in prefixes],
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
