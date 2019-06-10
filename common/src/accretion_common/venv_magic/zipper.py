"""Create a venv, build requirements into it, and package that into a zip."""
import io
import logging
import os
from zipfile import ZipFile

__all__ = ("build_zip",)
_LOGGER = logging.getLogger(__name__)


def _file_filter(filename: str) -> bool:  # pylint: disable=unused-argument
    """Determine whether this file should be included in the zip file.

    :param str filename: Filename
    :rtype: bool
    """
    # For now, leave everything in.
    return True


#    Leaving this here as an example of what this function might do later.
#    if filename.endswith(".pyc"):
#        return False

#    if f"{os.path.sep}__pycache__{os.path.sep}" in filename:
#        return False

#    return True


def build_zip(build_dir: str) -> io.BytesIO:
    """Build a Lambda Layer zip from a given directory.

    :param str build_dir: Directory to pack into Layer zip
    :returns: Binary file-like of zip
    :rtype: io.BytesIO
    """
    buffer = io.BytesIO()
    with ZipFile(buffer, mode="w") as zipper:
        for root, _dirs, files in os.walk(build_dir):
            for filename in files:
                if not _file_filter(filename):
                    continue

                filepath = os.path.join(root, filename)
                zipper.write(filename=filepath, arcname=f"python/{filepath[len(build_dir) + 1:]}")

    _LOGGER.debug("Zip file size: %s bytes", buffer.tell())
    buffer.seek(0)
    return buffer
