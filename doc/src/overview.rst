********
Overview
********

Concept
=======

The idea of Accretion is to make building and consuming dependencies in AWS Lambda simple.

Historically, in order to consume dependencies in Lambda,
you had to build your dependencies locally,
hoping that everything was compatible with the Lambda runtime,
zip everything up,
upload it to S3,
and finally update your Lambda definition.

When Lambda launched Lambda Layers, this changed.
Now, you can separate the contents of your eventual Lambda deployable into two categories:

#. Things that you depend on.
#. Things that you author.

When you build your Lambda,
rather than needing to include everything in one zip,
you can define dependencies on one or more Layers.
This means that you can control and iterate on your dependencies and your code independently.

However, you still need to build those dependencies and create those Layers.
This is where Accretion comes in.

Problem
=======

There are a few fundamental problems that people encounter when building dependencies:

#. Dependencies need to be built in as close as possible to the Lambda runtime.
   This can be difficult to programmatically ensure.
#. Building dependencies is likely to take longer than building your code.
#. Dependencies are unlikely to change as frequently as your code, especially during development.
   This together with #2 means that your builds probably take a lot longer than they could and repeat a lot of work.
#. In the AWS parlance, this is "undifferentiated heavy lifting".
   You probably don't care how it happens, you just want to have your dependencies there when you need them.

Goals
=====

* It should be very simple to define what dependencies should be built.
* Dependencies should be defined as broadly or as rigidly as the native tools allow.
* The user should not need to do anything more than provide a listing that native tools will understand and resolve.
* Users should be able to determine what is actually installed in a Layer version that they are consuming.
* Notifications should be available to tell a consumer that there is a new Layer version available.
* For the end user, building their Lambda deployment artifact should be as simple as possible.
  For Python, this should ideally simply mean uploading the project wheel file as the Lambda zip.

Assumptions
-----------

These are initial assumptions for simplicity.
As Accretion evolves, these should be revisited and addressed.

#. Only the primary public artifact repositories will be considered as dependency sources.
#. All artifacts and Layers will be publicly consumable.
#. The license info for the Layer cannot be determined.
#. Project names must not exceed 70 characters.
   This is to save space to add runtime information to the Layer name.
   Initially, we use the language specified at the start to build a separate artifact for every runtime.
   A better approach might be to require specified runtimes from the start,
   but this will have its own issues because the artifacts for one language version
   might not always be compatible with the artifacts for other language versions.
#. Given the above, we are not caring about SSE anywhere.
   Once support for private resources is added, SSE support should also be added everywhere.


Solution
========

There are several components needed to solve this:

#. **Artifact Builder.**
   Given a dependency definition, build a dependency artifact.
#. **Layer Creator.**
   Given a dependency artifact and details, determine whether it differs from the previous Layer version.
   If it does, publish a new Layer version.
#. **Simple CLI.**
   In addition to the lower-level resources that will build and orchestrate all of the above,
   a simple CLI should be defined that provides access to important information about all managed resources
   as well as the ability to create new resources.

Moving Forward
==============

Moving forward, some additional features that should be considered:

* Support for additional languages.
  The system architecture is designed to support arbitrary languages,
  but initially only Python builders are defined.
* Support for private artifacts and Layers.
  This will require some way to define the permissions for a Layer.
* Support for private artifact repositories.
* Support for custom builders.
  This could cover both additional languages and non-standard artifact repositories.
* Scheduled re-creation of Layers.
* Event source for updates to public package repositories.
* Global artifact replication.
  The original plan was to have a single artifact builder
  with an artifact replication layer that would send those artifacts to all target regions.
  This plan was abandoned because the full regional isolation is both
  much simpler to manage and probably a better idea for isolation anyway.
  However, the artifact and layer builders are decoupled in such a way
  that a replication layer could still be added between them.
  Depending on demand, we can reconsider this.
* An API that provides all of the capabilities of the CLI.
