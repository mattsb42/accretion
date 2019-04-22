""""""
from typing import Dict

from awacs import aws as AWS
from troposphere import AccountId, sns


def _owner_policy(topic: sns.Topic) -> Dict:
    return dict(
        Sid="OwnerPolicy",
        Effect=AWS.Allow,
        Principal=AWS.Principal("*"),
        Action=[
            "SNS:Publish",
            "SNS:RemovePermission",
            "SNS:SetTopicAttributes",
            "SNS:DeleteTopic",
            "SNS:ListSubscriptionsByTopic",
            "SNS:GetTopicAttributes",
            "SNS:Receive",
            "SNS:AddPermission",
            "SNS:Subscribe",
        ],
        Resource=topic.ref(),
        Condition=dict(StringEquals={"AWS:SourceOwner": AccountId}),
    )


def _public_broadcast(topic: sns.Topic) -> Dict:
    return dict(
        Sid="PublicBroadcast",
        Effect=AWS.Allow,
        Principal=AWS.Principal("*"),
        Action=["SNS:Receive", "SNS:Subscribe"],
        Resource=topic.ref(),
        Condition=dict(StringEquals={"SNS:Protocol": ["lambda", "sqs"]}),
    )


def public_topic(base_name: str) -> (sns.Topic, sns.TopicPolicy):
    topic = sns.Topic(f"{base_name}Topic")
    topic_policy = sns.TopicPolicy(
        f"{base_name}TopicPolicy",
        Topics=[topic.ref()],
        PolicyDocument=dict(Version="2008-10-17", Statement=[_owner_policy(topic), _public_broadcast(topic)]),
    )
    return topic, topic_policy
