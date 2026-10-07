Core Services
==============

``je_editor.core`` holds the parts of the editor that are not widgets: the workspace, the open
documents, the diagnostics, and the interfaces for language services, debugging, task execution,
remote sessions and AI providers. Nothing in it imports Qt, so it can be used from a test, a
command-line tool or a host application that never builds the JEditor window.

.. note::

   This layer is the foundation of the next-generation editor roadmap. The data models work
   today. The editor window does not consume them yet: its panels still talk to their own
   back ends, and they move onto these services one milestone at a time.

Quick Example
--------------

.. code-block:: python

   from je_editor.core import (
       Diagnostic, EditorServices, Severity, TextDocument, TextRange, Workspace, to_uri
   )

   services = EditorServices(Workspace.single_root("my_project"))

   uri = to_uri("my_project/main.py")
   services.documents.open(TextDocument(uri, "import os\n", "python"))

   services.diagnostics.changed.subscribe(lambda changed_uri: print("changed:", changed_uri))
   services.diagnostics.publish("ruff", uri, [
       Diagnostic("`os` imported but unused", TextRange.from_lines(1, 8, 1, 10),
                  Severity.WARNING, code="F401"),
   ])

   for diagnostic in services.diagnostics.select([Severity.WARNING]):
       print(diagnostic.source, diagnostic.label)

   services.shutdown()

Each ``EditorServices`` is independent. There is no module-level instance, so two editors
embedded in one application never share a workspace or diagnostics. Call ``shutdown()`` when
the owner closes: language services and task runners may hold processes and threads.

EditorServices
---------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Attribute
     - What it holds
   * - ``workspace``
     - The ``Workspace``: zero or more project roots
   * - ``documents``
     - The ``DocumentStore``: every open document, keyed by URI
   * - ``diagnostics``
     - The ``DiagnosticStore``: what every source reported
   * - ``languages``
     - The ``LanguageServiceRegistry``, fed by ``documents``
   * - ``debug_adapters``
     - Debug session factories, registered by adapter type
   * - ``task_runners``
     - Task runners, registered by where they run
   * - ``remote_transports``
     - Remote session factories, registered by URI scheme
   * - ``ai_providers``
     - AI providers, registered by name

The last four are ``NamedRegistry`` objects: ``register(name, item)``, ``get(name)``,
``require(name)`` (raises ``JEditorServiceException`` and lists what is registered),
``unregister(name)`` and ``names()``.

Workspace
----------

A workspace is a list of ``ProjectRoot`` objects. One root is a perfectly valid workspace and
is what a project directory has always been.

.. code-block:: python

   from je_editor.core import Workspace

   workspace = Workspace.single_root("frontend")
   workspace.add_root("backend")

   owner = workspace.root_for("backend/src/main.py")        # the "backend" root
   root, relative = workspace.relative_path("backend/src/main.py")
   print(root.name, relative)                               # backend src/main.py

- Roots are named by URI. A local directory is a ``file://`` URI; ``ProjectRoot.is_local`` and
  ``ProjectRoot.path`` tell the two cases apart.
- When roots nest, ``root_for`` returns the deepest one. ``root_for_uri`` answers the same
  question for a URI, which is how a document or a diagnostic finds its root.
- ``ProjectRoot.resolve(relative_path)`` joins a path onto the root and raises
  ``JEditorServiceException`` when the result would leave it, as ``..`` can.
- ``workspace.changed`` fires after a root is added or removed.

Documents
----------

``Document`` is a protocol: anything with ``uri``, ``language_id``, ``version`` and ``text()``
is a document. ``TextDocument`` is the in-memory implementation.

.. code-block:: python

   from je_editor.core import DocumentStore, TextDocument, to_uri

   documents = DocumentStore()
   uri = to_uri("notes.py")
   documents.open(TextDocument(uri, "x = 1\n", "python"))
   documents.replace_text(uri, "x = 2\n")      # raises the version and fires ``changed``
   documents.close(uri)

A document whose text lives elsewhere (an editor widget, for example) is opened the same way,
and its owner calls ``documents.notify_changed(uri)`` after each change. ``opened``, ``changed``
and ``closed`` each pass the document concerned.

Diagnostics
------------

Every source reports into one model:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Meaning
   * - ``message``
     - The human-readable text
   * - ``range``
     - A ``TextRange`` of two ``Position`` objects; lines and columns count from one
   * - ``severity``
     - ``Severity.ERROR``, ``WARNING``, ``INFORMATION`` or ``HINT`` (LSP's numbers)
   * - ``source``
     - Who reported it, such as ``ruff`` or a language server's name
   * - ``code``
     - The rule code
   * - ``uri``
     - The resource it is in
   * - ``related``
     - ``RelatedInformation`` entries: other locations that relate to it
   * - ``fixes``
     - ``QuickFix`` entries, each a title and the ``TextEdit`` list that applies it

``DiagnosticStore.publish(source, uri, diagnostics)`` replaces everything that source said
about that resource, which is what LSP's ``publishDiagnostics`` means; an empty list clears
it. ``select(severities=None, sources=None, uri=None)`` filters, and always returns the same
order for the same content: by resource, then position, then severity. ``counts()`` gives the
total per severity and ``sources()`` the sources that have findings.

Language Services
------------------

A language service is told when a document it handles opens, changes or closes, and says what
it offers through ``LanguageCapability``.

.. code-block:: python

   from je_editor.core import (
       Diagnostic, EditorServices, LanguageCapability, Severity, TextDocument, TextRange, to_uri
   )


   class TodoFinder:
       """Reports every line that contains TODO."""

       name = "todo-finder"

       def __init__(self, services):
           self._services = services

       def capabilities(self):
           return frozenset({LanguageCapability.DIAGNOSTICS})

       def handles(self, document):
           return document.language_id == "python"

       def document_opened(self, document):
           self._check(document)

       def document_changed(self, document):
           self._check(document)

       def document_closed(self, document):
           self._services.diagnostics.publish(self.name, document.uri, [])

       def shutdown(self):
           self._services.diagnostics.clear(source=self.name)

       def _check(self, document):
           found = [
               Diagnostic("TODO left in the code", TextRange.from_lines(number), Severity.HINT)
               for number, line in enumerate(document.text().splitlines(), start=1)
               if "TODO" in line
           ]
           self._services.diagnostics.publish(self.name, document.uri, found)


   services = EditorServices()
   services.languages.register(TodoFinder(services))
   services.documents.open(TextDocument(to_uri("a.py"), "x = 1  # TODO rename\n", "python"))
   print(len(services.diagnostics))    # 1

A service registered after documents are open is told about each one it handles, so a server
that starts late still learns what is open. ``services_for(document, capability)`` finds the
services for a document.

Debugging, Tasks, Remote Sessions and AI Providers
---------------------------------------------------

These four are interfaces with their data objects. JEditor ships no implementation of them in
this layer yet; a host or a plugin registers its own.

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - Area
     - Interface
     - Data objects
   * - Debugging
     - ``DebugSession``
     - ``DebugLaunchRequest``, ``Breakpoint``, ``StackFrame``, ``Variable``, ``DebugState``,
       ``StepKind``
   * - Task execution
     - ``TaskRunner``, ``TaskHandle``
     - ``TaskSpec``, ``TaskState``, ``OutputStream``
   * - Remote sessions
     - ``RemoteSession``
     - ``RemoteState``
   * - AI providers
     - ``AIProvider``
     - ``ChatRequest``, ``ChatMessage``, ``ChatRole``, ``ChatResponse``, ``ModelInfo``,
       ``CancelToken``

- A ``TaskSpec`` command is always a list of arguments. There is no form that hands a line to
  a shell, and a string is refused.
- ``TaskRunner.create(spec)`` returns a handle that has not started. Subscribe to its
  ``output`` and ``finished`` events, then call ``start()``, so no early output is missed.
- ``RemoteSession.task_runner()`` returns the same ``TaskRunner`` interface, so a caller never
  has to tell where a process runs.
- ``AIProvider.complete(request, on_text, cancel)`` blocks until the reply is complete. Call it
  from a worker thread. ``on_text`` receives the reply piece by piece and a ``CancelToken``
  stops it part-way.

.. code-block:: python

   from je_editor.core import (
       ChatMessage, ChatRequest, ChatResponse, ChatRole, EditorServices, ModelInfo
   )


   class UpperCaseProvider:
       """Answers by shouting the question back."""

       name = "upper"

       def models(self):
           return [ModelInfo("upper-1", "Upper Case")]

       def complete(self, request, on_text=None, cancel=None):
           text = request.messages[-1].content.upper()
           if on_text is not None:
               on_text(text)
           return ChatResponse(text, "upper-1")


   services = EditorServices()
   services.ai_providers.register(UpperCaseProvider.name, UpperCaseProvider())
   provider = services.ai_providers.require("upper")
   reply = provider.complete(ChatRequest((ChatMessage(ChatRole.USER, "hello"),)))
   print(reply.text)    # HELLO

Events and Threads
-------------------

The services announce changes through ``EventHook`` objects rather than Qt signals.
``hook.subscribe(listener)`` returns a function that undoes the subscription.

A listener runs on whichever thread caused the event. A listener that updates widgets has to
hand over to the UI thread itself, for example by emitting a Qt signal of its own. One
listener raising does not stop the others; the failure is written to the JEditor log.

Staying Qt-Free
----------------

``test/test_core_architecture.py`` holds this boundary in three ways: it walks the import
graph of ``je_editor.core`` and fails on any Qt or ``je_editor.pyside_ui`` import beneath it,
it lists the only modules below the UI that may reach upwards, and it builds the services in
a process where importing Qt is blocked.

``import je_editor.core`` still runs ``je_editor/__init__.py`` first, as importing any
sub-package does, and that file imports the Qt application. The services themselves need
neither Qt nor a ``QApplication``.
