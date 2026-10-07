Core Services
==============

``je_editor.core`` holds the parts of the editor that are not widgets: the workspace, the open
documents, the diagnostics, syntax analysis, and the interfaces for language services, debugging,
task execution, remote sessions and AI providers. Nothing in it imports Qt, so it can be used from a test, a
command-line tool or a host application that never builds the JEditor window.

.. note::

   This layer is the foundation of the next-generation editor roadmap. The editor window moves
   onto it one area at a time: diagnostics, the AI chat panel, the workspace and syntax
   highlighting use it so far, while debugging, task execution and remote sessions are
   interfaces only.

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
   * - ``syntax``
     - The ``SyntaxEngine``. It knows no language until a parser is plugged in;
       ``build_default_services()`` plugs in Tree-sitter
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
       Diagnostic, EditorServices, LanguageCapability, LanguageReply, Severity, TextDocument,
       TextRange, to_uri
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

       def request(self, request, on_reply):
           on_reply(LanguageReply(request, self.name, error="todo-finder answers no questions"))
           return lambda: None

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

Asking a Language Service
~~~~~~~~~~~~~~~~~~~~~~~~~~

Completion, hover, symbols and every other question go through one call: hand over a function
for the reply and get back a function to cancel with. ``services.languages.request()`` puts the
question to the first registered service that handles the document and offers the capability.

.. code-block:: python

   from je_editor.adapters.default_services import build_default_services
   from je_editor.core import LanguageCapability, LanguageRequest, TextDocument, to_uri

   services = build_default_services()
   document = TextDocument(to_uri("greeter.py"),
                           "class Greeter:\n    def greet(self):\n        return 'hi'\n")
   services.documents.open(document)


   def show(reply):
       if reply.ok:
           print(reply.service, [(region.kind.value, region.name) for region in reply.value])
       else:
           print(reply.error)


   cancel = services.languages.request(
       LanguageRequest(LanguageCapability.DOCUMENT_SYMBOLS, document), show)
   # syntax [('class', 'Greeter'), ('function', 'greet')]
   services.languages.request(LanguageRequest(LanguageCapability.HOVER, document), show)
   # no language service offers hover for file:///.../greeter.py
   services.shutdown()

The same call works whether the service answers at once or after a while:

- A service that has the answer at hand, as the syntax service does, calls the function before
  ``request()`` returns.
- A service that has to wait, as a language server does, calls it later and may do so from a
  thread of its own. A caller that updates widgets moves the reply to the widget thread itself.
- The reply arrives at most once, and never after the cancel function was called. The registry
  enforces both, so a service does not have to.
- When nobody can answer, the reply carries an ``error`` and ``reply.ok`` is ``False``. Nothing
  is raised.

What ``reply.value`` holds depends on the capability:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Capability
     - ``reply.value``
   * - ``SYNTAX_TREE``
     - The document's ``SyntaxSession`` (see below)
   * - ``DOCUMENT_SYMBOLS``
     - A tuple of the named ``StructuralRegion`` objects: classes, functions and methods
   * - The others
     - Decided when the first service offers them

Syntax Analysis
----------------

A ``SyntaxEngine`` turns text into the two things an editor needs from a parser: which stretches
of a line are a keyword, a string or a function name, and which classes, functions and blocks a
document has. The parse tree itself never leaves the engine, so the widgets do not depend on the
parser.

.. code-block:: python

   from je_editor.adapters.syntax.tree_sitter_engine import TreeSitterEngine

   engine = TreeSitterEngine()
   print(engine.language_ids())                 # ('python', 'javascript', 'json')
   session = engine.open_session(engine.language_for("main.py"))

   print(session.update("def greet(name):\n    return name\n"))
   # LineSpan(first=1, last=3)
   print([(span.column, span.length, span.category.value) for span in session.spans(1)])
   # [(1, 3, 'keyword'), (5, 5, 'function'), (11, 4, 'variable')]

   print(session.update("def greet(name):\n    return name.upper()\n"))
   # LineSpan(first=2, last=2)
   print([(region.kind.value, region.name, region.is_multiline) for region in session.regions()])
   # [('function', 'greet', True)]

- ``open_session(language_id)`` gives one document its own ``SyntaxSession``; it returns
  ``None`` for a language the engine cannot analyse.
- ``update(text)`` takes the whole text and returns the ``LineSpan`` whose categories may have
  changed, or ``None`` when the text is the same. Only the part an edit touched is parsed
  again, and the span can reach beyond the edited line: opening a string changes every line
  after it.
- ``spans(line)`` gives the ``SyntaxSpan`` objects of a line, outer ones before the ones inside
  them, so applying them in order lets an interpolation override the string around it.
- ``regions()`` gives the ``StructuralRegion`` objects, outer ones first. ``kind`` is one of
  ``RegionKind.CLASS``, ``FUNCTION``, ``BLOCK`` and ``COLLECTION``.
- Lines and columns are 1-based, as in diagnostics. A column counts UTF-16 units, which is what
  Qt and the language server protocol count.

``je_editor.adapters.syntax`` implements the engine with Tree-sitter for Python, JavaScript and
JSON. A language is one ``GrammarSpec`` row in ``grammar_table.py`` plus query files under
``queries/<language>/``: ``highlights.scm`` is appended to the highlight query the grammar ships,
and ``regions.scm`` names the structural regions. A grammar that is not installed, or a query
that does not compile, makes that language unsupported rather than raising, and the editor
falls back to its pattern-based highlighter.

Debugging, Tasks, Remote Sessions and AI Providers
---------------------------------------------------

These four are interfaces with their data objects. The implementations live in
``je_editor.adapters``, outside this layer. So far that is the two AI providers (``openai`` and
``anthropic``, see :doc:`ai_assistant`); a host or a plugin registers its own for the rest.

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
