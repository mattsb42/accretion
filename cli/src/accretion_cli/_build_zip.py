""""""
from tempfile import TemporaryDirectory
from typing import IO

import click
from accretion_common.venv_magic.builder import build_requirements
from accretion_common.venv_magic.zipper import build_zip

__all__ = ("build_and_write_workers",)


def build_and_write_workers(outfile: IO):
    """"""
    with TemporaryDirectory() as venv_dir, TemporaryDirectory() as build_dir:
        installed_requirements = build_requirements(
            build_dir=build_dir, venv_dir=venv_dir, requirements=["accretion_workers"]
        )
        click.echo(f"Installed requirements: {installed_requirements}")
        zip_buffer = build_zip(build_dir=build_dir)
        for line in zip_buffer:
            outfile.write(line)
