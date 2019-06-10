"""Functional tests for ``accretion_cli._stepfunctions``."""
import json

import pytest

from accretion_cli._templates.services.stepfunctions import _artifact_builder_workflow, _replication_listener_workflow

from .functional_test_utils import load_vector

pytestmark = [pytest.mark.local, pytest.mark.functional]


def _assert_equal_workflows(test, expected):
    assert test == expected

    test_json = json.dumps(test, indent=4)
    expected_json = json.dumps(expected, indent=4)

    assert test_json == expected_json


def test_artifact_builder_workflow():
    expected = load_vector("artifact_builder_workflow")

    test = _artifact_builder_workflow(
        parse_requirements_arn="${ParseRequirementsFunction.Arn}",
        build_python_36_arn="${PythonBuilder36Function.Arn}",
        build_python_37_arn="${PythonBuilder37Function.Arn}",
    )

    _assert_equal_workflows(test, expected)


def test_replication_listener_workflow():
    expected = load_vector("replication_listener_workflow")

    test = _replication_listener_workflow(
        filter_arn="${EventFilterFunction.Arn}",
        locate_artifact_arn="${ArtifactLocatorFunction.Arn}",
        publish_layer_arn="${LayerVersionPublisherFunction.Arn}",
        sns_topic_arn="${NotifyTopic}",
    )

    _assert_equal_workflows(test, expected)
