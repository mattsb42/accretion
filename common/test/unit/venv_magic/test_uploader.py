"""Unit tests for ``accretion_common.venv_magic.uploader``."""
from typing import Dict, Iterable

import pytest

from accretion_common.venv_magic import uploader

pytestmark = [pytest.mark.local, pytest.mark.functional]


@pytest.mark.parametrize(
    "installed, runtime_name, expected_hash",
    (
            (
                    (
                        dict(Name="asdf", Details="123"),
                        dict(Name="zz", Details="333"),
                        dict(Name="ff", Details="[3214];wutwut")
                    ),
                    "python",
                    "2babf317cda24b98133b8937ca952e64154f3c00a14bb83b7c20a2e2b13a0237",
            ),
    )
)
def test_key_hash(installed: Iterable[Dict[str, str]], runtime_name: str, expected_hash: str):
    test = uploader._key_hash(installed=installed, runtime_name=runtime_name, force_new=False)
    test_unique = uploader._key_hash(installed=installed, runtime_name=runtime_name, force_new=True)

    assert test == expected_hash
    assert test_unique != expected_hash
