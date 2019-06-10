*************
Accretion CLI
*************

The Accretion CLI is the primary point for controlling Accretion resources.

The Accretion CLI maintains configuration state in a :ref:`Deployment File`.

.. warning::

    Accretion is under active development and is not yet stable.
    The below reflects the target interface for the Accretion CLI.
    Not all commands will work yet.

Usage
=====

init
----

Create base resources for an Accretion deployment in all specified regions.
The results are stored in ``DEPLOYMENT_FILE``.

.. code:: shell

    accretion init DEPLOYMENT_FILE REGIONS...


destroy
-------

Destroy all resources for an Accretion deployment described in ``DEPLOYMENT_FILE``.

.. important::

    This will destroy ALL resources.
    Be sure that is what you want to do before running this.


.. code:: shell

    accretion destroy DEPLOYMENT_FILE


add
---

region
^^^^^^

Add a region to an Accretion deployment.

.. code:: shell

    accretion add region DEPLOYMENT_FILE

artifact-builder
^^^^^^^^^^^^^^^^

Add an artifact builder stack for the specified Accretion deployment.

.. code:: shell

    accretion add artifact-builder DEPLOYMENT_FILE


layer-builder
^^^^^^^^^^^^^

Add a layer builder stack for the specified Accretion deployment.

.. code:: shell

    accretion add layer-builder DEPLOYMENT_FILE

list
----

layers
^^^^^^

List all Accretion-managed Lambda Layers and their versions in the specified region.

.. code:: shell

    accretion list layers DEPLOYMENT_FILE REGION_NAME

describe
--------

layer-version
^^^^^^^^^^^^^

Describe a Layer version, listing the contents of that Layer.

.. code:: shell

    accretion describe layer-version DEPLOYMENT_FILE REGION_NAME LAYER_NAME LAYER_VERSION

request
-------

Request a new Lambda Layer.
This triggers the Artifact Builder workflow in each region with the specified :ref:`Request File`.

.. code:: shell

    accretion request DEPLOYMENT_FILE REQUEST_FILE

check
-----

Check a :ref:`Request File` for correctness.


.. code:: shell

    accretion check REQUEST_FILE

.. _Deployment File:

Deployment File
===============

An Accretion deployment file describes the stacks associated with a single Accretion deployment.

.. warning::

    Deployment files MUST NOT be modified by anything other than the Accretion CLI.

It is a JSON file with the following structure:

.. code:: json

    {
        "Deployments": {
            "AWS_REGION": {
                "Core": "STACK_NAME",
                "ArtifactBuilder": "STACK_NAME",
                "LayerBuilder": "STACK_NAME"
            }
        }
    }


.. _Request File:

Request File
============

An Accretion require file describes the Layer that is being requested.

It is a JSON file with the following structure:

.. code:: json

    {
        "Name": "layer name",
        "Language": "Language to target",
        "Requirements": {
            "Type": "ready",
            "Requirements": [
                {
                    "Name": "Requirement Name",
                    "Version": "Requirement Version"
                }
            ]
        },
        "Requirements": {
            "Type": "requirements.txt",
            "Requirements": "Raw contents of requirements.txt file format"
        }
    }
