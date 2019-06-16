"""Unit tests for ``accretion_common.venv_magic.builder``."""
from typing import Iterable

import pytest

from accretion_common.util import PackageDetails
from accretion_common.venv_magic import builder

pytestmark = [pytest.mark.local, pytest.mark.functional]


@pytest.mark.parametrize(
    "requirements, expected_file_contents",
    (
        (
            (
                PackageDetails(Name="attrs", Details="==19.1.0"),
                PackageDetails(Name="awacs", Details="==0.9.2"),
                PackageDetails(Name="Click", Details="==7.0"),
                PackageDetails(Name="boto3", Details="==1.9.169"),
                PackageDetails(Name="botocore", Details="==1.12.169"),
            ),
            "attrs==19.1.0\nawacs==0.9.2\nClick==7.0\nboto3==1.9.169\nbotocore==1.12.169\n",
        ),
        (
            (
                PackageDetails(Name="attrs"),
                PackageDetails(Name="awacs"),
                PackageDetails(Name="Click"),
                PackageDetails(Name="boto3"),
                PackageDetails(Name="botocore"),
            ),
            "attrs\nawacs\nClick\nboto3\nbotocore\n",
        ),
    ),
)
def test_build_requirements_file(tmpdir, requirements: Iterable[PackageDetails], expected_file_contents: str):
    requirements_file = tmpdir.join("requirements.txt")

    builder._build_requirements_file(str(requirements_file), *requirements)

    assert requirements_file.read() == expected_file_contents
