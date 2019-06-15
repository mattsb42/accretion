"""Common internal Accretion utilities."""
from typing import Dict

import attr

__all__ = ("PackageVersion",)


@attr.s(auto_attribs=True)
class PackageVersion:
    """Container for information identifying a package.

    :param str name: Package name
    :param str version: Package version
    """

    name: str
    version: str

    @classmethod
    def from_pip_log(cls, log_value: str) -> "PackageVersion":
        """Read package name and version from a ``pip install`` log."""
        name, version = log_value.rsplit("-", 1)
        return PackageVersion(name, version)

    def to_dict(self) -> Dict[str, str]:
        """Pack information into a dictionary."""
        return dict(Name=self.name, Version=self.version)
