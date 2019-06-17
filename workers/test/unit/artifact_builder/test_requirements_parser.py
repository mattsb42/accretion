"""Unit tests for ``accretion_workers.artifact_builder.requirements_parser``."""
import json

import pytest

from accretion_workers.artifact_builder import requirements_parser

pytestmark = [pytest.mark.local, pytest.mark.functional]

LAYER_NAME = "test-layer-name"
PYTHON = "python"
READY = "ready"
REQUIREMENTS = "requirements.txt"


@pytest.mark.parametrize(
    "request_body, expected_response",
    (
        (
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=dict(
                    Type=READY,
                    Requirements=[
                        dict(Name="attrs", Details="==19.1.0"),
                        dict(Name="awacs", Details="==0.9.2"),
                        dict(Name="Click", Details="==7.0"),
                        dict(Name="boto3", Details="==1.9.169"),
                        dict(Name="botocore", Details="==1.12.169"),
                    ],
                ),
            ),
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=[
                    dict(Name="attrs", Details="==19.1.0"),
                    dict(Name="awacs", Details="==0.9.2"),
                    dict(Name="Click", Details="==7.0"),
                    dict(Name="boto3", Details="==1.9.169"),
                    dict(Name="botocore", Details="==1.12.169"),
                ],
            ),
        ),
        (
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=dict(
                    Type=READY,
                    Requirements=[
                        dict(Name="attrs", Details=""),
                        dict(Name="troposphere", Details="[policy]"),
                        dict(Name="awacs", Details=">=0.9.2"),
                        dict(Name="Click", Details=">=7.0"),
                        dict(Name="boto3", Details=""),
                        dict(Name="botocore", Details=""),
                    ],
                ),
            ),
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=[
                    dict(Name="attrs", Details=""),
                    dict(Name="troposphere", Details="[policy]"),
                    dict(Name="awacs", Details=">=0.9.2"),
                    dict(Name="Click", Details=">=7.0"),
                    dict(Name="boto3", Details=""),
                    dict(Name="botocore", Details=""),
                ],
            ),
        ),
        (
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=dict(
                    Type=REQUIREMENTS,
                    Requirements="\n".join(
                        ["attrs==19.1.0", "awacs==0.9.2", "Click==7.0", "boto3==1.9.169", "botocore==1.12.169"]
                    ),
                ),
            ),
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=[
                    dict(Name="attrs", Details="==19.1.0"),
                    dict(Name="awacs", Details="==0.9.2"),
                    dict(Name="Click", Details="==7.0"),
                    dict(Name="boto3", Details="==1.9.169"),
                    dict(Name="botocore", Details="==1.12.169"),
                ],
            ),
        ),
        (
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=dict(
                    Type=REQUIREMENTS,
                    Requirements="\n".join(
                        ["attrs", "troposphere[policy]", "awacs>=0.9.2", "Click>=7.0", "boto3", "botocore"]
                    ),
                ),
            ),
            dict(
                Name=LAYER_NAME,
                Language=PYTHON,
                Requirements=[
                    dict(Name="attrs", Details=""),
                    dict(Name="troposphere", Details="[policy]"),
                    dict(Name="awacs", Details=">=0.9.2"),
                    dict(Name="Click", Details=">=7.0"),
                    dict(Name="boto3", Details=""),
                    dict(Name="botocore", Details=""),
                ],
            ),
        ),
    ),
)
def test_parse_requirements(request_body, expected_response):
    test = requirements_parser.lambda_handler(request_body, None)

    assert json.dumps(test, sort_keys=True) == json.dumps(expected_response, sort_keys=True)
