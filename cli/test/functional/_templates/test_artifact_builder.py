"""Functional tests for ``accretion_cli._templates.artifact_builder``."""
import pytest

from accretion_cli._templates import artifact_builder

from ..functional_test_utils import load_vector_as_template

pytestmark = [pytest.mark.local, pytest.mark.functional]


def test_build():
    expected = load_vector_as_template("artifact_builder_template")

    test = artifact_builder.build()

    assert test.to_json() == expected.to_json()
