"""Filter CloudWatch Events for layer creation workflow."""
from accretion_workers._util import ARTIFACT_MANIFESTS_PREFIX


def lambda_handler(event, context):
    """We only want to process events for artifact manifests.

    :param event: CloudWatch Event record for S3:PutObject event
    :param context:
    :return:
    """
    s3_key = event["detail"]["requestParameters"]["key"]
    return {"ProcessEvent": s3_key.startswith(ARTIFACT_MANIFESTS_PREFIX)}
