"""Accretion CloudFormation template artifact_builder."""
import os
import re

from setuptools import find_packages, setup

VERSION_RE = re.compile(r"""__version__ = ['"]([0-9b.]+)['"]""")
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*args):
    """Reads complete file contents."""
    return open(os.path.join(HERE, *args)).read()


def get_version():
    """Reads the version from this module."""
    init = read("src", "accretion_cli", "__init__.py")
    return VERSION_RE.search(init).group(1)


def get_requirements():
    """Reads the requirements file."""
    requirements = read("requirements.txt")
    return [r for r in requirements.strip().splitlines()]


setup(
    name="accretion_cli",
    packages=find_packages("src"),
    package_dir={"": "src"},
    version=get_version(),
    author="mattsb42",
    maintainer="mattsb42",
    author_email="m@ttsb42.com",
    url="https://github.com/mattsb42/accretion",
    description="Accretion CloudFormation template artifact_builder.",
    long_description=read("README.rst"),
    keywords="aws lambda",
    license="Apache License 2.0",
    install_requires=get_requirements(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: System :: Archiving :: Packaging",
    ],
    entry_points=dict(console_scripts=["accretion=accretion_cli._commands:cli"]),
)
