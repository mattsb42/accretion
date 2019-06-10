""""""
import json
import os
from pathlib import Path
from typing import Dict

from troposphere.template_generator import TemplateGenerator

_TEST_VECTORS_DIR = Path(os.path.abspath(os.path.dirname(__file__))) / ".." / "vectors"


def check_vector_exists(name: str):
    vector_filename = (_TEST_VECTORS_DIR / name).with_suffix(".json")

    if not os.path.isfile(vector_filename):
        raise ValueError(f"Vector name {name!r} does not exist.")

    return vector_filename


def load_vector(vector_name: str) -> Dict:
    vector_filename = check_vector_exists(vector_name)

    with open(vector_filename) as vector:
        return json.load(vector)


def load_vector_as_template(vector_name: str) -> TemplateGenerator:
    vector_dict = load_vector(vector_name)
    return TemplateGenerator(vector_dict)
