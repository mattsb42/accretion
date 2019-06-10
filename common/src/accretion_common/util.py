"""Common internal Accretion utilities."""
from dataclasses import dataclass
from typing import Dict

__all__ = ("PackageVersion",)


@dataclass
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
