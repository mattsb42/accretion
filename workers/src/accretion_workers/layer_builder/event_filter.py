"""Filter CloudWatch Events for layer creation workflow."""

try:
    from accretion_workers._util import ARTIFACTS_PREFIX, ARTIFACT_MANIFESTS_PREFIX
except ImportError:
    ARTIFACTS_PREFIX = "accretion/artifacts/"
    ARTIFACT_MANIFESTS_PREFIX = "accretion/manifests/"


def lambda_handler(event, context):
    """We only want to process events for artifact manifests.

    :param event: CloudWatch Event record for S3:PutObject event
    :param context:
    :return:
    """
    s3_key = event["detail"]["requestParameters"]["key"]
    return s3_key.startswith(ARTIFACT_MANIFESTS_PREFIX)
