"""Accretion requirements parser."""
import logging
import re
from typing import Dict, Iterator, Union

from accretion_common.util import PackageDetails

MAX_NAME_LENGTH = 70
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def _requirements_txt_to_accretion(requirements_txt: str) -> Iterator[Dict[str, str]]:
    return [PackageDetails.from_requirements_entry(line).to_dict() for line in requirements_txt.strip().splitlines()]


def _validate_name(project_name: str):
    """Project names must be valid Lambda Layer names.
    https://docs.aws.amazon.com/lambda/latest/dg/API_PublishLayerVersion.html#API_PublishLayerVersion_RequestSyntax

    :param project_name:
    :return:
    """
    if not re.fullmatch(r"[a-zA-Z0-9-_]+", project_name):
        raise Exception(f"Project name must be a valid Lambda Layer name: {project_name!r}")

    if len(project_name) > MAX_NAME_LENGTH:
        raise Exception(f"Project name must not be longer than {MAX_NAME_LENGTH} characters")


def _validate_ready_requirements(requirements: Iterator[Dict[str, str]]):
    for req in requirements:
        if not req:
            raise Exception(f"Invalid requirements: {req!r}")


def _validate_languge(language: str) -> str:
    language = language.lower()
    if language != "python":
        raise Exception(f"Unsupported language: {language!r}")

    return language


def _normalize_requirements(
    requirements_type: str, requirements: Union[str, Iterator[str]]
) -> Iterator[Dict[str, str]]:
    requirements_parsers = {"accretion": lambda x: x, "requirements.txt": _requirements_txt_to_accretion}

    try:
        parser = requirements_parsers[requirements_type]
    except KeyError:
        raise Exception(f"Invalid requirements type: {requirements_type}")

    logger.debug(f"Raw requirements: {requirements!r}")
    parsed_requirements = parser(requirements)
    logging.debug(f"Parsed requirements: {parsed_requirements}")
    _validate_ready_requirements(parsed_requirements)
    return parsed_requirements


def lambda_handler(event, context):
    """Lambda entry point.

    Event shape:

    .. code:: json

        {
            "Name": "layer name",
            "Language": "Language to target",
            "Requirements": {
                "Type": "accretion",
                "Requirements": [
                    {
                        "Name": "Requirement Name",
                        "Details": "Requirement version or other identifying details"
                    }
                ]
            },
            "Requirements": {
                "Type": "requirements.txt",
                "Requirements": "Raw contents of requirements.txt file format"
            }
        }

    .. note::

        Language must be a valid
        `runtime prefix <https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html>`_
        (ex: "python", "java", etc).

    Return shape:

    .. code:: json

        {
            "Name": "layer name",
            "Language": "Language to target",
            "Requirements": [
                {
                    "Name": "Requirement Name",
                    "Details": "Requirement version or other identifying details"
                }
            ]
        }

    Required permissions:

    * None

    :param event:
    :param context:
    :return:
    """
    try:
        _validate_name(event["Name"])

        valid_language = _validate_languge(event["Language"])
        valid_requirements = _normalize_requirements(
            requirements_type=event["Requirements"]["Type"], requirements=event["Requirements"]["Requirements"]
        )

        return {"Name": event["Name"], "Language": valid_language, "Requirements": valid_requirements}
    except Exception:
        # TODO: Turn these into known-cause state machine failures.
        raise
