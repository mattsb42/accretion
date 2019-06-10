"""Build the CloudFormation template for the Accretion core resource in the source region."""
from troposphere import Template, s3


def _source_bucket() -> s3.Bucket:
    return s3.Bucket(
        "SourceBucket",
        BucketEncryption=s3.BucketEncryption(
            ServerSideEncryptionConfiguration=[
                s3.ServerSideEncryptionRule(
                    ServerSideEncryptionByDefault=s3.ServerSideEncryptionByDefault(SSEAlgorithm="AES256")
                )
            ]
        ),
    )


def build():
    core = Template(Description="Core Accretion resources for source region")

    core.add_resource(_source_bucket())

    return core
