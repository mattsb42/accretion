"""Unit tests for ``accretion_cli._util.parameters``."""
from typing import Optional

import click
import pytest

from accretion_cli._util.parameters import try_to_load_deployment_file

pytestmark = [pytest.mark.local, pytest.mark.functional]


@pytest.mark.parametrize(
    "file_contents, error_message", ((None, "Deployment file does not exist!"), ("", "Invalid deployment file!"))
)
def test_try_to_load_deployment_file_fail(tmpdir, file_contents: Optional[str], error_message: str):
    tmpfile = tmpdir.join("deployment_file")

    if file_contents is not None:
        tmpfile.write(file_contents)

    with pytest.raises(click.BadParameter) as excinfo:
        try_to_load_deployment_file(deployment_file_name=str(tmpfile))

    excinfo.match(error_message)
