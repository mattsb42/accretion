"""Accretion workers."""
import os
import re

from setuptools import find_packages, setup

VERSION_RE = re.compile(r"""__version__ = ['"]([0-9.]+)['"]""")
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*args):
    """Reads complete file contents."""
    return open(os.path.join(HERE, *args)).read()


def get_version():
    """Reads the version from this module."""
    init = read("src", "aws_encryption_sdk", "identifiers.py")
    return VERSION_RE.search(init).group(1)


def get_requirements():
    """Reads the requirements file."""
    requirements = read("requirements.txt")
    return [r for r in requirements.strip().splitlines()]


setup(
    name="accretion_workers",
    packages=find_packages("src"),
    package_dir={"": "src"},
    version=get_version(),
    author="mattsb42",
    maintainer="mattsb42",
    author_email="m@ttsb42.com",
    url="https://github.com/mattsb42/accretion",
    description="Accretion workers.",
    long_description=read("README.rst"),
    keywords="aws lambda accretion",
    license="Apache License 2.0",
    install_requires=get_requirements(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: System :: Archiving :: Packaging",
    ],
)
