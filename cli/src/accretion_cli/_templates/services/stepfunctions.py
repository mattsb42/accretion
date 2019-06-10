"""AWS Step Functions state machines."""
import json
from typing import Dict

from troposphere import AWSObject, Sub, Tags, Template, awslambda, sns, stepfunctions

from .iam import invoke_statement_from_lambdas, publish_statement_from_topics, step_functions_role


def _resource_to_sub_reference(resource: AWSObject) -> str:
    return f"${{{resource.title}}}"


def _resource_to_sub_arn(resource: AWSObject) -> str:
    return f"${{{resource.title}.Arn}}"


def _artifact_builder_workflow(parse_requirements_arn: str, build_python_36_arn: str, build_python_37_arn: str) -> Dict:
    sm = dict(Comment="Artifact Builder", StartAt="ParseRequirements")
    sm["States"] = states = dict()

    states["ParseRequirements"] = dict(Type="Task", Resource=parse_requirements_arn, Next="SelectLanguage")

    states["SelectLanguage"] = dict(
        Type="Choice",
        Choices=[dict(Variable="$.Language", StringEquals="python", Next="BuildPython")],
        Default="UnknownLanguage",
    )

    states["UnknownLanguage"] = dict(Type="Fail", Cause="Invalid language")

    states["BuildPython"] = dict(
        Type="Parallel",
        Branches=[
            dict(
                StartAt="BuildPython36",
                States=dict(BuildPython36=dict(Type="Task", Resource=build_python_36_arn, End=True)),
            ),
            dict(
                StartAt="BuildPython37",
                States=dict(BuildPython37=dict(Type="Task", Resource=build_python_37_arn, End=True)),
            ),
        ],
        ResultPath="$.BuildResults",
        End=True,
    )

    return sm


def add_artifact_builder(
    builder: Template,
    parse_requirements: awslambda.Function,
    python36_builder: awslambda.Function,
    python37_builder: awslambda.Function,
    tags: Tags,
) -> stepfunctions.StateMachine:
    name = "ArtifactBuilderStateMachine"

    statement = invoke_statement_from_lambdas(parse_requirements, python36_builder, python37_builder)
    role = step_functions_role(f"{name}Role", statement)

    workflow = _artifact_builder_workflow(
        parse_requirements_arn=_resource_to_sub_arn(parse_requirements),
        build_python_36_arn=_resource_to_sub_arn(python36_builder),
        build_python_37_arn=_resource_to_sub_arn(python37_builder),
    )
    sm = stepfunctions.StateMachine(
        name, DefinitionString=Sub(json.dumps(workflow)), RoleArn=role.get_att("Arn"), Tags=tags
    )

    builder.add_resource(role)
    return builder.add_resource(sm)


def _replication_listener_workflow(
    filter_arn: str, locate_artifact_arn: str, publish_layer_arn: str, sns_topic_arn: str
) -> Dict:
    sm = dict(Comment="Replication Listener", StartAt="Filter")
    sm["States"] = states = dict()

    states["Filter"] = dict(Type="Task", Resource=filter_arn, ResultPath="$", Next="ShouldProcess")

    states["ShouldProcess"] = dict(
        Type="Choice",
        Choices=[dict(Variable="$.ProcessEvent", BooleanEquals=True, Next="LocateArtifact")],
        Default="IgnoreEvent",
    )

    states["IgnoreEvent"] = dict(Type="Succeed", Comment="Ignore this event")

    states["LocateArtifact"] = dict(
        Type="Task", Resource=locate_artifact_arn, ResultPath="$.Artifact", Next="ArtifactCheck"
    )

    states["ArtifactCheck"] = dict(
        Type="Choice",
        Choices=[
            dict(Variable="$.Artifact.Found", BooleanEquals=True, Next="PublishNewVersion"),
            dict(
                And=[
                    dict(Variable="$.Artifact.Found", BooleanEquals=False),
                    dict(Variable="$.Artifact.ReadAttempts", NumericGreaterThan=15),
                ],
                Next="ReplicationTimeout",
            ),
        ],
        Default="WaitForReplication",
    )

    states["ReplicationTimeout"] = dict(Type="Fail", Error="Timed out waiting for artifact to replicate")

    states["WaitForReplication"] = dict(Type="Wait", Seconds=60, Next="LocateArtifact")

    states["PublishNewVersion"] = dict(Type="Task", Resource=publish_layer_arn, ResultPath="$.Layer", Next="Notify")

    states["Notify"] = dict(
        Type="Task",
        Resource="arn:aws:states:::sns:publish",
        Parameters={"TopicArn": sns_topic_arn, "Message.$": "$.Layer"},
        End=True,
    )

    return sm


def add_replication_listener(
    builder: Template,
    filter_func: awslambda.Function,
    locate_artifact_func: awslambda.Function,
    publish_layer_func: awslambda.Function,
    notify_topic: sns.Topic,
    tags: Tags,
) -> stepfunctions.StateMachine:
    name = "ReplicationListener"

    lambda_statement = invoke_statement_from_lambdas(filter_func, locate_artifact_func, publish_layer_func)
    sns_statement = publish_statement_from_topics(notify_topic)
    role = step_functions_role(f"{name}Role", lambda_statement, sns_statement)

    workflow = _replication_listener_workflow(
        filter_arn=_resource_to_sub_arn(filter_func),
        locate_artifact_arn=_resource_to_sub_arn(locate_artifact_func),
        publish_layer_arn=_resource_to_sub_arn(publish_layer_func),
        sns_topic_arn=_resource_to_sub_reference(notify_topic),
    )
    sm = stepfunctions.StateMachine(
        name, DefinitionString=Sub(json.dumps(workflow)), RoleArn=role.get_att("Arn"), Tags=tags
    )

    builder.add_resource(role)
    return builder.add_resource(sm)
