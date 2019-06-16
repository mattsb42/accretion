"""Common internal Accretion utilities."""
from typing import Dict

import attr
from pkg_resources import Requirement

__all__ = ("PackageDetails",)


@attr.s(auto_attribs=True)
class PackageDetails:
    """Container for information identifying a package.

    :param str name: Package name
    :param str details: Package version or other identifying details
    """

    Name: str
    Details: str = attr.Factory(str)

    @classmethod
    def from_pip_log(cls, log_value: str) -> "PackageDetails":
        """Read package name and version from a ``pip install`` log."""
        name, version = log_value.rsplit("-", 1)
        return PackageDetails(name, version)

    def to_dict(self) -> Dict[str, str]:
        """Pack information into a dictionary."""
        return dict(Name=self.Name, Details=self.Details)

    @classmethod
    def from_requirements_entry(cls, requirement_line: str) -> "PackageDetails":
        """Read package name and version from a ``requirements.txt`` file entry."""
        entry = Requirement.parse(requirement_line)
        name = entry.project_name

        details = requirement_line[len(name) :]
        return PackageDetails(Name=name, Details=details)
