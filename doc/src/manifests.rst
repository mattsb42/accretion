*********
Manifests
*********

All manifests are JSON.


Artifact Manifest
=================

When a Layer artifact is created,
the artifact builder also creates a manifest file that describes what that artifact contains.

* **ProjectName** : Name of the project.
* **ArtifactS3Key** : S3 key in the regional artifacts bucket that contains the artifact.
* **Runtimes** : List of Lambda runtimes that are compatible with this artifact.
* **Requirements** : List of requirements strings as they were requested.
* **Installed** : List of package version structures for each package that was actually installed.

  * **Name** : Name of package.
  * **Version** : Version of package.


.. code:: json

    {
        "ProjectName": "example layer",
        "ArtifactS3Key": "accretion/artifacts/exampleLayer/4b14d8bf-61ff-4514-9f9a-ebb59dba08fe.zip",
        "Requirements": [
            "cryptography",
            "requests"
        ],
        "Installed": [
            {
                "Name": "asn1crypto",
                "Version": "0.24.0"
            },
            {
                "Name": "certifi",
                "Version": "2019.3.9"
            },
            {
                "Name": "cffi",
                "Version": "1.12.3"
            },
            {
                "Name": "chardet",
                "Version": "3.0.4"
            },
            {
                "Name": "cryptography",
                "Version": "2.6.1"
            },
            {
                "Name": "idna",
                "Version": "2.8"
            },
            {
                "Name": "pycparser",
                "Version": "2.19"
            },
            {
                "Name": "requests",
                "Version": "2.21.0"
            },
            {
                "Name": "six",
                "Version": "1.12.0"
            },
            {
                "Name": "urllib3",
                "Version": "1.24.2"
            }
        ],
        "Runtimes": [
            "python3.6"
        ]
    }


Layer Manifest
==============

When a Layer version is created,
the layer builder creates a manifest file that describes that Layer.

* **LayerArn** : Layer Amazon Resource Name (Arn).
* **LayerVersion** : Layer version that was created.
* **ArtifactManifest** : Structure identifying location of artifact manifest.

  * **S3Bucket** : S3 regional artifacts bucket name.
  * **S3Key** : S3 key in the regional artifacts bucket that contains the artifact manifest.


.. code:: json

    {
        "Layer": {
            "Arn": "arn:aws:states:region:account-id:stateMachine:stateMachineName",
            "Version": 3
        },
        "ArtifactManifest": {
            "S3Bucket": "accretion-regional-bucket",
            "S3Key": "accretion/manifests/exampleLayer/4b14d8bf-61ff-4514-9f9a-ebb59dba08fe.manifest"
        }
    }
