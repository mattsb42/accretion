"""Internal Accretion exceptions."""


class AccretionError(Exception):
    """Parent Accretion exception."""


class ZipBuilderError(AccretionError):
    """Raised when an error is encountered building a zip file."""


class ExecutionError(AccretionError):
    """Raised when a command fails to execute."""
