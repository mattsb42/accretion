"""Functional tests for ``accretion_cli._stepfunctions``."""
import json

import pytest

from accretion_cli._stepfunctions import _artifact_builder_workflow

from .functional_test_utils import load_vector

pytestmark = [pytest.mark.local, pytest.mark.functional]


def test_artifact_builder_workflow():
    expected = load_vector("artifact_builder_workflow")

    test = _artifact_builder_workflow(
        parse_requirements_arn="${ParseRequirementsFunction.Arn}",
        build_python_36_arn="${PythonBuilder36Function.Arn}",
        build_python_37_arn="${PythonBuilder37Function.Arn}"
    )

    assert test == expected

    test_json = json.dumps(test, indent=4)
    expected_json = json.dumps(expected, indent=4)

    assert test_json == expected_json
