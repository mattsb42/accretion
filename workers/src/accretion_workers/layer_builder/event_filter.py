"""Filter CloudWatch Events for layer creation workflow."""

try:
    from accretion_workers._util import ARTIFACTS_PREFIX, ARTIFACT_MANIFESTS_PREFIX
except ImportError:
    ARTIFACTS_PREFIX = "accretion/artifacts/"
    ARTIFACT_MANIFESTS_PREFIX = "accretion/manifests/"


def lambda_handler(event, context):
    """We only want to process events for artifact manifests.

    Event shape:

    ..note::

        CloudWatch Event record for S3:PutObject event.

    Return shape:

    ..code:: json

        {
            "ResourceKey": "S3 key containing object that triggered event",
            "ProcessEvent": boolean decision stating whether to continue processing event
        }

    Required permissions:

    * None

    :param event: CloudWatch Event record for S3:PutObject event
    :param context:
    :return:
    """
    try:
        s3_key = event["detail"]["requestParameters"]["key"]
        return {"ProcessEvent": s3_key.startswith(ARTIFACT_MANIFESTS_PREFIX), "ResourceKey": s3_key}
    except Exception:
        # TODO: Turn these into known-cause state machine failures.
        raise
