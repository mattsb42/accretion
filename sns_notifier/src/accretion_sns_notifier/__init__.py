"""Accretion SNS notifier."""
import json
import os

import boto3

SNS_TOPIC = "SNS_TOPIC"
VERSION = 1
is_setup = False


def _setup():
    global sns
    sns = boto3.client("aws")
    global topic
    topic = os.environ[SNS_TOPIC]
    global is_setup
    is_setup = True


def _send_message(**kwargs):
    kwargs["version"] = VERSION
    body = json.dumps(kwargs)
    sns.publish(
        TopicArn=topic,
        Message=body,
    )


def lambda_handler(event, context):
    """

    Event shape:

    ..code: json

        {
            "name": "layer name",
            "requirements": ["List of requirements"],
            "build_results": [
                {
                    "installed": ["Actual versions of all installed requirements"],
                    "runtimes": ["Lambda runtime name"],
                    "s3_key": "S3 key containing built zip"
                }
            ]
        }

    :param event:
    :param context:
    :return:
    """
    if not is_setup:
        _setup()
    for results in event["build_results"]:
        _send_message(
            name=event["name"],
            requirements=event["requirements"],
            **results
        )
