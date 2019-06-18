#########
Accretion
#########

.. image:: https://img.shields.io/badge/code_style-black-000000.svg
   :target: https://github.com/ambv/black
   :alt: Code style: black

.. image:: https://readthedocs.org/projects/accretion/badge/
   :target: https://accretion.readthedocs.io/en/stable/
   :alt: Documentation Status

.. image:: https://travis-ci.org/mattsb42/accretion.svg?branch=master
   :target: https://travis-ci.org/mattsb42/accretion
   :alt: Travis CI Test Status

.. important::

    Accretion is not yet stable. Use with care.

.. important::

    Accretion relies on AWS Lambda and AWS Step Functions,
    and so will NOT work in the Osaka-Local (ap-northeast-3) region.

Tooling for building AWS Lambda Layers containing desired dependencies.

Find `our source code on GitHub`_.

.. toctree::
   :maxdepth: 2
   :caption: Accretion

   src/overview
   src/manifests
   src/cli

.. _our source code on GitHub: https://github.com/mattsb42/accretion
