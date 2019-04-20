"""Accretion requirements parser."""
import logging
from typing import Iterator, Union

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def _requirements_txt_to_ready(requirements_txt: str) -> Iterator[str]:
    return requirements_txt.strip().split()


def _validate_ready_requirements(requirements: Iterator[str]):
    for req in requirements:
        if not req:
            raise Exception(f"Invalid requirements: {req!r}")


def _validate_languge(language: str) -> str:
    language = language.lower()
    if language != "python":
        raise Exception(f"Unsupported language: {language!r}")

    return language


def _normalize_requirements(requirements_type: str, requirements: Union[str, Iterator[str]]) -> Iterator[str]:
    requirements_parsers = {
        "ready": lambda x: x,
        "requirements.txt": _requirements_txt_to_ready
    }

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

    ..code:: json

        {
            "Name": "layer name",
            "Language": "Language to target",
            "Requirements": {
                "Type": "ready",
                "Requirements": ["List of requirements"]
            },
            "Requirements": {
                "Type": "requirements.txt",
                "Requirements": "Raw contents of requirements.txt file format"
            }
        }

    ..note::

        Language must be a valid
        `runtime prefix <https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html>`_
        (ex: "python", "java", etc).

    Return shape:

    ..code:: json

        {
            "Name": "layer name",
            "Language": "Language to target",
            "Requirements": ["List of requirements"]
        }

    :param event:
    :param context:
    :return:
    """
    valid_language = _validate_languge(event["Language"])
    valid_requirements = _normalize_requirements(
        requirements_type=event["Requirements"]["Type"],
        requirements=event["Requirements"]["Requirements"],
    )

    return {
        "Name": event["Name"],
        "Language": valid_language,
        "Requirements": valid_requirements,
    }
