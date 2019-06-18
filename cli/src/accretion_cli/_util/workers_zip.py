""""""
import io
from tempfile import TemporaryDirectory
from typing import IO

import click
from accretion_common.util import PackageDetails
from accretion_common.venv_magic.builder import build_requirements
from accretion_common.venv_magic.zipper import build_zip

__all__ = ("build_and_write_workers", "build_worker_bytes")
WORKERS_PACKAGE = PackageDetails(Name="accretion_workers", Details="==0.1.0")


def build_and_write_workers(*, outfile: IO):
    """"""
    with TemporaryDirectory() as venv_dir, TemporaryDirectory() as build_dir:
        installed_requirements = build_requirements(
            build_dir=build_dir, venv_dir=venv_dir, requirements=[WORKERS_PACKAGE]
        )
        click.echo(f"Installed requirements: {installed_requirements}")
        zip_buffer = build_zip(build_dir=build_dir, layer=False)
        for line in zip_buffer:
            outfile.write(line)


def build_worker_bytes() -> bytes:
    """"""
    # Build workers zip.
    workers_zip = io.BytesIO()
    build_and_write_workers(outfile=workers_zip)
    # Copy into bytes that we can farm out to multiple threads.
    workers_zip_data = workers_zip.getvalue()
    # Then discard the original.
    workers_zip.truncate(0)

    return workers_zip_data
