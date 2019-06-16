"""Unit tests for ``accretion_common.util``."""
import pytest

from accretion_common.util import PackageDetails

pytestmark = [pytest.mark.local, pytest.mark.functional]


# Test vectors from PEP508 https://www.python.org/dev/peps/pep-0508/#complete-grammar
@pytest.mark.parametrize(
    "entry, name, details",
    (
        ("A", "A", ""),
        ("A.B-C_D", "A.B-C-D", ""),
        ("aa", "aa", ""),
        ("name", "name", ""),
        ("name<=1", "name", "<=1"),
        ("name>=3", "name", ">=3"),
        ("name>=3,<2", "name", ">=3,<2"),
        ("name@http://foo.com", "name", "@http://foo.com"),
        (
            "name [fred,bar] @ http://foo.com ; python_version=='2.7'",
            "name",
            " [fred,bar] @ http://foo.com ; python_version=='2.7'",
        ),
        (
            "name[quux, strange];python_version<'2.7' and platform_version=='2'",
            "name",
            "[quux, strange];python_version<'2.7' and platform_version=='2'",
        ),
        ("name; os_name=='a' or os_name=='b'", "name", "; os_name=='a' or os_name=='b'"),
        # Should parse as (a and b) or c
        (
            "name; os_name=='a' and os_name=='b' or os_name=='c'",
            "name",
            "; os_name=='a' and os_name=='b' or os_name=='c'",
        ),
        # Overriding precedence -> a and (b or c)
        (
            "name; os_name=='a' and (os_name=='b' or os_name=='c')",
            "name",
            "; os_name=='a' and (os_name=='b' or os_name=='c')",
        ),
        # should parse as a or (b and c)
        (
            "name; os_name=='a' or os_name=='b' and os_name=='c'",
            "name",
            "; os_name=='a' or os_name=='b' and os_name=='c'",
        ),
        # Overriding precedence -> (a or b) and c
        (
            "name; (os_name=='a' or os_name=='b') and os_name=='c'",
            "name",
            "; (os_name=='a' or os_name=='b') and os_name=='c'",
        ),
    ),
)
def test_packageversion_from_requirements_entry(entry: str, name: str, details: str):
    test = PackageDetails.from_requirements_entry(entry)

    assert test.Name == name
    assert test.Details == details
