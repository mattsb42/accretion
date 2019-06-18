*************
Accretion CLI
*************

The Accretion CLI is the primary point for controlling Accretion resources.

The Accretion CLI maintains configuration state in a "Deployment File".

.. warning::

    Accretion is under active development and is not yet stable.
    The below reflects the target interface for the Accretion CLI.
    Not all commands will work yet.

Usage
=====

init
----

Initialize the ``DEPLOYMENT_FILE`` for deployments to ``REGIONS``.

This does NOT deploy to those regions.

Run ``accretion update`` to update and fill all regions in a deployment file.

.. code:: shell

    accretion init DEPLOYMENT_FILE REGIONS...

update
------

Update deployments in all regions described in ``DEPLOYMENT_FILE``.

This will also
initialize any empty deployment regions
and complete any partial deployments.

.. code:: shell

    accretion update all DEPLOYMENT_FILE


add regions
-----------

Add more ``REGIONS`` to an existing deployment description in ``DEPLOYMENT_FILE``.

This does NOT deploy to those regions.

Run ``accretion update`` to update and fill all regions in a deployment file.


.. code:: shell

    accretion add regions DEPLOYMENT_FILE REGIONS...


destroy
-------

Destroy all resources for an Accretion deployment described in ``DEPLOYMENT_FILE``.

.. warning::

    This will destroy ALL resources in ALL regions.
    Be sure that is what you want to do before running this.

.. code:: shell

    accretion destroy DEPLOYMENT_FILE


request
-------

Request a new layer version build.

.. important::

    These operations are currently completely asynchronous with no way of tracking a layer build through the CLI.
    I plan to add tooling around this later,
    but the exact form it will take is still TBD.
    `mattsb42/accretion#27 <https://github.com/mattsb42/accretion/issues/27>`_

raw
^^^

Request a new layer in every region in ``DEPLOYMENT_FILE``.
The Layer must be described in the Accretion format in ``REQUEST_FILE``.

.. code:: json

    {
        "Name": "layer name",
        "Language": "Language to target",
        "Requirements": {
            "Type": "accretion",
            "Requirements": [
                {
                    "Name": "Requirement Name",
                    "Details": "Requirement version or other identifying details"
                }
            ]
        },
        "Requirements": {
            "Type": "requirements.txt",
            "Requirements": "Raw contents of requirements.txt file format"
        }
    }

.. note::

    The only supported language at this time is ``python``.


.. code:: shell

    accretion request raw DEPLOYMENT_FILE REQUEST_FILE

requirements
^^^^^^^^^^^^

Request a new layer named ``LAYER_NAME`` in every region in ``DEPLOYMENT_FILE``.
The Layer requirements must be defined in the Python requirements.txt format in ``REQUIREMENTS_FILE``.

.. code:: shell

    accretion request DEPLOYMENT_FILE REQUIREMENTS_FILE

list
----

layers
^^^^^^

.. important::

    `This command has not yet been implemented <https://github.com/mattsb42/accretion/issues/4>`_.

List all Accretion-managed Lambda Layers and their versions in the specified region.

.. code:: shell

    accretion list layers DEPLOYMENT_FILE REGION_NAME

describe
--------

layer-version
^^^^^^^^^^^^^

.. important::

    `This command has not yet been implemented <https://github.com/mattsb42/accretion/issues/4>`_.

Describe a Layer version, listing the contents of that Layer.

.. code:: shell

    accretion describe layer-version DEPLOYMENT_FILE REGION_NAME LAYER_NAME LAYER_VERSION

check
-----

.. important::

    `This command has not yet been implemented <https://github.com/mattsb42/accretion/issues/4>`_.

Check a "Request File" for correctness.


.. code:: shell

    accretion check REQUEST_FILE

Deployment File
===============

.. warning::

    Deployment files MUST NOT be modified by anything other than Accretion tooling.

An Accretion deployment file describes the stacks associated with a single Accretion deployment.

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
            "Type": "accretion",
            "Requirements": [
                {
                    "Name": "Requirement Name",
                    "Details": "Requirement version or identifying details"
                }
            ]
        },
        "Requirements": {
            "Type": "requirements.txt",
            "Requirements": "Raw contents of requirements.txt file format"
        }
    }
