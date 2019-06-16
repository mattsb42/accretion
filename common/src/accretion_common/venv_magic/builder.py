"""Tools for working with venvs."""
import logging
import os
import shutil
import subprocess  # nosec : bandit B404 is addressed by only executing pre-defined commands
import tempfile
import venv
from typing import Dict, Iterable

from accretion_common.exceptions import ExecutionError
from accretion_common.util import PackageDetails

__all__ = ("build_requirements",)
_LOGGER = logging.getLogger(__name__)


def _execute_command(command: str) -> (str, str):
    _LOGGER.debug("Executing command: %s", command)
    proc = subprocess.run(  # nosec : bandit B602 is addressed by only executing pre-defined commands
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", shell=True
    )
    _LOGGER.debug("============STDOUT============")
    _LOGGER.debug(proc.stdout)
    _LOGGER.debug("============STDERR============")
    _LOGGER.debug(proc.stderr)
    if proc.stderr:
        raise ExecutionError("Failed to execute command")
    return proc.stdout, proc.stderr


def _execute_in_venv(venv_dir: str, command: str) -> (str, str):
    return _execute_command(f"source {venv_dir}/bin/activate; {command}; deactivate")


def _build_venv(venv_dir: str) -> (str, str):
    shutil.rmtree(venv_dir, ignore_errors=True)
    venv.create(venv_dir, clear=True, with_pip=True)
    return _execute_in_venv(venv_dir=venv_dir, command="pip install --no-cache-dir --upgrade pip")


def _build_requirements_file(requirements_file: str, *libraries: PackageDetails):
    with open(requirements_file, "w") as requirements:
        for library in libraries:
            requirements.write(f"{library.Name}{library.Details}\n")


def _install_requirements_to_build(build_dir: str, requirements_file: str, log_file: str, venv_dir: str) -> (str, str):
    return _execute_in_venv(
        venv_dir=venv_dir,
        # Do not cache in order to save what little disk space we have in Lambda.
        command="pip install --no-cache-dir --upgrade --ignore-installed --no-compile "
        f"--log {log_file} "
        f"-r {requirements_file} --target {build_dir}",
    )


def _parse_install_log(log_file: str) -> Iterable[Dict[str, str]]:
    trigger = "Successfully installed"
    installed = []
    with open(log_file, "r") as logs:
        for line in logs:
            line = line.split(" ", 1)[-1].strip()
            if line.startswith(trigger):
                line = line[len(trigger) :].strip()
                installed = line.split()
                break
    _LOGGER.debug("Installed to layer artifact: %s", installed)
    return [PackageDetails.from_pip_log(log_entry).to_dict() for log_entry in installed]


def build_requirements(
    build_dir: str, venv_dir: str, requirements: Iterable[PackageDetails]
) -> Iterable[Dict[str, str]]:
    """Build the requested requirements into the target build directory using a newly created venv.

    :param str build_dir: Path to directory into which to build requirements.
    :param str venv_dir: Path to directory to use for venv.
    :param requirements: List of requirements to install.
    """
    _build_venv(venv_dir)

    _, requirements_file = tempfile.mkstemp()
    _, log_file = tempfile.mkstemp()

    try:
        _build_requirements_file(requirements_file, *requirements)
        _install_requirements_to_build(
            build_dir=build_dir, requirements_file=requirements_file, log_file=log_file, venv_dir=venv_dir
        )
        return _parse_install_log(log_file=log_file)
    finally:
        os.remove(requirements_file)
        os.remove(log_file)
