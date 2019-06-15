"""Build the CloudFormation template for the Accretion replication listener."""
import itertools
from functools import partial
from typing import Callable

from accretion_common.constants import ARTIFACT_MANIFESTS_PREFIX, ARTIFACTS_PREFIX, LAYER_MANIFESTS_PREFIX
from awacs import s3 as S3
from troposphere import (
    AWS_PARTITION,
    Parameter,
    Sub,
    Tags,
    Template,
    awslambda,
    cloudtrail,
    events,
    s3,
    sns,
    stepfunctions,
)

from accretion_cli._templates.services.awslambda import add_lambda_core, lambda_function
from accretion_cli._templates.services.iam import (
    events_trigger_stepfuntions_role,
    lambda_layer_permissions,
    s3_get_object_statement,
    s3_put_object_statement,
)
from accretion_cli._templates.services.sns import public_topic
from accretion_cli._templates.services.stepfunctions import add_replication_listener

DEFAULT_TAGS = Tags(Accretion="ReplicationListener")


def _add_regional_bucket(builder: Template) -> (s3.Bucket, s3.BucketPolicy):
    name = "RegionalBucket"
    bucket = builder.add_resource(s3.Bucket(name, Tags=DEFAULT_TAGS))

    policy = s3.BucketPolicy(
        f"{name}Policy",
        Bucket=bucket.ref(),
        PolicyDocument=dict(
            Version="2012-10-17",
            Statement=[
                dict(
                    Sid="CloudTrailAclCheck",
                    Effect="Allow",
                    Principal=dict(Service="cloudtrail.amazonaws.com"),
                    Action=S3.GetBucketAcl,
                    Resource=Sub(f"arn:${{{AWS_PARTITION}}}:s3:::${{{bucket.title}}}"),
                ),
                dict(
                    Sid="CloudTrailWrite",
                    Effect="Allow",
                    Principal=dict(Service="cloudtrail.amazonaws.com"),
                    Action=S3.PutObject,
                    Resource=Sub(f"arn:${{{AWS_PARTITION}}}:s3:::${{{bucket.title}}}/accretion/cloudtrail/*"),
                    Condition=dict(StringEquals={"s3:x-amz-acl": "bucket-owner-full-control"}),
                ),
            ],
        ),
    )
    builder.add_resource(policy)

    return bucket, policy


def _add_cloudtrail_listener(
    builder: Template, replication_bucket: Parameter, log_bucket: s3.Bucket, log_bucket_policy: s3.BucketPolicy
) -> cloudtrail.Trail:
    trail = cloudtrail.Trail(
        "ReplicationListenerTrail",
        DependsOn=[log_bucket_policy.title],
        EnableLogFileValidation=True,
        EventSelectors=[
            cloudtrail.EventSelector(
                IncludeManagementEvents=False,
                DataResources=[
                    cloudtrail.DataResource(
                        Type="AWS::S3::Object",
                        Values=[
                            Sub(
                                f"arn:${{{AWS_PARTITION}}}:s3:::${{{replication_bucket.title}}}/{ARTIFACT_MANIFESTS_PREFIX}"
                            )
                        ],
                    )
                ],
            )
        ],
        IncludeGlobalServiceEvents=False,
        IsLogging=True,
        IsMultiRegionTrail=False,
        S3BucketName=log_bucket.ref(),
        S3KeyPrefix="accretion/cloudtrail/",
        Tags=DEFAULT_TAGS,
    )
    return builder.add_resource(trail)


def _add_cloudwatch_event_rule(
    builder: Template, replication_bucket: Parameter, listener_workflow: stepfunctions.StateMachine
) -> events.Rule:
    base_name = "ReplicationListenerEvent"
    trigger_role = events_trigger_stepfuntions_role(f"{base_name}Role", statemachine=listener_workflow)
    builder.add_resource(trigger_role)

    rule = events.Rule(
        f"{base_name}Rule",
        State="ENABLED",
        EventPattern={
            "source": ["aws.s3"],
            "detail-type": ["AWS API Call via CloudTrail"],
            "detail": {
                "eventSource": ["s3.amazonaws.com"],
                "eventName": ["PutObject"],
                "requestParameters": {"bucketName": [replication_bucket.ref()]},
            },
        },
        Targets=[
            events.Target(
                Arn=listener_workflow.ref(), Id=f"{base_name}TriggerWorkflow", RoleArn=trigger_role.get_att("Arn")
            )
        ],
    )
    return builder.add_resource(rule)


def _add_event_filter(lambda_adder: Callable) -> awslambda.Function:
    return lambda_adder(
        base_name="EventFilter", statements=[], lambda_args=dict(module="event_filter", memory_size=128, timeout=5)
    )


def _add_artifact_locator(lambda_adder: Callable, replication_bucket: Parameter) -> awslambda.Function:
    statements = s3_get_object_statement(
        *[f"${{{replication_bucket.title}}}/accretion/{group}/" for group in ("artifacts", "manifests")]
    )

    return lambda_adder(
        base_name="ArtifactLocator",
        statements=statements,
        lambda_args=dict(module="artifact_checker", memory_size=512, timeout=30),
    )


def _add_layer_version_publisher(
    lambda_adder: Callable, regional_bucket: s3.Bucket, replication_bucket: Parameter
) -> awslambda.Function:
    statements = itertools.chain(
        s3_put_object_statement(f"${{{regional_bucket.title}}}/{LAYER_MANIFESTS_PREFIX}"),
        s3_get_object_statement(f"${{{replication_bucket.title}}}/{ARTIFACTS_PREFIX}"),
        lambda_layer_permissions(),
    )

    return lambda_adder(
        base_name="LayerVersionPublisher",
        statements=statements,
        lambda_args=dict(module="version_publisher", memory_size=1024, timeout=60),
    )


def _add_notify_topic(builder: Template) -> sns.Topic:
    topic, policy = public_topic("Notify")
    builder.add_resource(policy)
    return builder.add_resource(topic)


def build() -> Template:
    builder = Template(Description="Accretion replication listener resources")

    replication_bucket = builder.add_parameter(
        Parameter(
            "ReplicationBucket", Type="String", Description="Bucket to watch for new Accretion artifacts and manifests"
        )
    )
    workers_key = builder.add_parameter(
        Parameter("WorkersS3Key", Type="String", Description="S3 key in artifacts bucket containing workers zip")
    )

    # regional bucket
    regional_bucket, regional_bucket_policy = _add_regional_bucket(builder)

    # CloudTrail replication event trail
    _add_cloudtrail_listener(
        builder=builder,
        replication_bucket=replication_bucket,
        log_bucket=regional_bucket,
        log_bucket_policy=regional_bucket_policy,
    )

    common_lambda_args = dict(
        source_bucket=replication_bucket,
        workers_key=workers_key,
        runtime="python3.7",
        namespace="layer_builder",
        tags=DEFAULT_TAGS,
    )

    pre_layer_lambda_adder = partial(
        add_lambda_core,
        builder=builder,
        lambda_builder=partial(lambda_function, bucket_name=replication_bucket, **common_lambda_args),
    )
    layer_builder_lambda_adder = partial(
        add_lambda_core,
        builder=builder,
        lambda_builder=partial(lambda_function, bucket_name=regional_bucket, **common_lambda_args),
    )
    # Role and Function for each of:
    #  event filter
    event_filter = _add_event_filter(pre_layer_lambda_adder)
    #  artifact locator
    artifact_locator = _add_artifact_locator(lambda_adder=pre_layer_lambda_adder, replication_bucket=replication_bucket)
    #  layer version publisher
    layer_version_publisher = _add_layer_version_publisher(
        lambda_adder=layer_builder_lambda_adder, regional_bucket=regional_bucket, replication_bucket=replication_bucket
    )

    # Notify Topic and Policy
    notify_topic = _add_notify_topic(builder)

    # Layer Builder workflow and Role
    listener_workflow = add_replication_listener(
        builder=builder,
        filter_func=event_filter,
        locate_artifact_func=artifact_locator,
        publish_layer_func=layer_version_publisher,
        notify_topic=notify_topic,
        tags=DEFAULT_TAGS,
    )

    # CloudWatch Event replication event
    _add_cloudwatch_event_rule(
        builder=builder, replication_bucket=replication_bucket, listener_workflow=listener_workflow
    )

    return builder
