"""Functional tests for ``accretion_cli._templates.source_region_core``."""
import pytest

from accretion_cli._templates import source_region_core

from ..functional_test_utils import load_vector_as_template

pytestmark = [pytest.mark.local, pytest.mark.functional]


def test_build():
    expected = load_vector_as_template("source_region_core_template")

    test = source_region_core.build()

    assert test.to_json() == expected.to_json()
