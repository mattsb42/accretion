"""Functional tests for ``accretion_cli._templates.artifact_builder``."""
import pytest

from accretion_cli._templates import replication_listener

from ..functional_test_utils import load_vector_as_template

pytestmark = [pytest.mark.local, pytest.mark.functional]


def test_build():
    expected = load_vector_as_template("replication_listener_template")

    test = replication_listener.build()

    assert test.to_json() == expected.to_json()
