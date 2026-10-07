核心服務
========

``je_editor.core`` 放的是編輯器裡不屬於元件的部分：工作區、開著的文件、診斷、語法分析，以及
語言服務、除錯、工作執行、遠端工作階段與 AI 供應者的介面。這一層完全不匯入 Qt，所以測試、命令列工具，
或從不建立 JEditor 視窗的宿主程式都可以使用。

.. note::

   這一層是下一代編輯器藍圖的基礎。編輯器視窗一次改接一個部分：目前診斷、AI 對話面板、工作區
   與語法高亮已經在用它，除錯、工作執行與遠端工作階段還只有介面。

快速範例
--------

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

每一個 ``EditorServices`` 都是獨立的。這裡沒有模組層級的實例，所以同一個應用程式嵌入兩個編輯器時，
它們不會共用工作區或診斷。擁有者關閉時要呼叫 ``shutdown()``：語言服務與工作執行器可能持有程序與
執行緒。

EditorServices
---------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 屬性
     - 內容
   * - ``workspace``
     - ``Workspace``：零到多個專案根目錄
   * - ``documents``
     - ``DocumentStore``：所有開著的文件，以 URI 為鍵
   * - ``diagnostics``
     - ``DiagnosticStore``：每個來源回報的診斷
   * - ``languages``
     - ``LanguageServiceRegistry``，文件事件來自 ``documents``
   * - ``syntax``
     - ``SyntaxEngine``。接上解析器之前它什麼語言都不會； ``build_default_services()`` 會接上
       Tree-sitter
   * - ``debug_adapters``
     - 除錯工作階段的建立函式，以轉接器種類登記
   * - ``task_runners``
     - 工作執行器，以執行的地方登記
   * - ``remote_transports``
     - 遠端工作階段的建立函式，以 URI 的 scheme 登記
   * - ``ai_providers``
     - AI 供應者，以名稱登記

後面四個是 ``NamedRegistry``：``register(name, item)``、``get(name)``、``require(name)``
（找不到時丟出 ``JEditorServiceException`` 並列出已登記的名稱）、``unregister(name)`` 與
``names()``。

工作區
------

工作區是一串 ``ProjectRoot``。只有一個根目錄的工作區完全合法，也就是原本的「專案目錄」。

.. code-block:: python

   from je_editor.core import Workspace

   workspace = Workspace.single_root("frontend")
   workspace.add_root("backend")

   owner = workspace.root_for("backend/src/main.py")        # "backend" 這個根目錄
   root, relative = workspace.relative_path("backend/src/main.py")
   print(root.name, relative)                               # backend src/main.py

- 根目錄以 URI 指認。本機目錄是 ``file://`` URI；``ProjectRoot.is_local`` 與 ``ProjectRoot.path``
  可以分辨兩種情況。
- 根目錄互相包含時，``root_for`` 回傳最深的那一個。``root_for_uri`` 以 URI 回答同一個問題，文件與診斷
  就是靠它找到自己的根目錄。
- ``ProjectRoot.resolve(relative_path)`` 把路徑接到根目錄上；結果會跑到根目錄外面時（例如
  ``..``）丟出 ``JEditorServiceException``。
- 根目錄增減之後會發出 ``workspace.changed``。

文件
----

``Document`` 是一個協定（protocol）：只要有 ``uri``、``language_id``、``version`` 與 ``text()``
就是文件。``TextDocument`` 是內容放在記憶體裡的實作。

.. code-block:: python

   from je_editor.core import DocumentStore, TextDocument, to_uri

   documents = DocumentStore()
   uri = to_uri("notes.py")
   documents.open(TextDocument(uri, "x = 1\n", "python"))
   documents.replace_text(uri, "x = 2\n")      # 版本加一，並發出 ``changed``
   documents.close(uri)

內容放在別處的文件（例如編輯器元件）用同樣的方式開啟，每次內容改變後由擁有者呼叫
``documents.notify_changed(uri)``。``opened``、``changed`` 與 ``closed`` 三個事件都會帶著那份文件。

診斷
----

所有來源都回報成同一種模型：

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 欄位
     - 意義
   * - ``message``
     - 給人看的說明文字
   * - ``range``
     - 由兩個 ``Position`` 組成的 ``TextRange``；行與欄都從一起算
   * - ``severity``
     - ``Severity.ERROR``、``WARNING``、``INFORMATION`` 或 ``HINT``，數值與 LSP 相同
   * - ``source``
     - 誰報的，例如 ``ruff`` 或語言伺服器的名稱
   * - ``code``
     - 規則代碼
   * - ``uri``
     - 所在的資源
   * - ``related``
     - ``RelatedInformation``：跟這筆診斷有關的其他位置
   * - ``fixes``
     - ``QuickFix``：每一筆有名稱，以及套用時要做的 ``TextEdit`` 清單

``DiagnosticStore.publish(source, uri, diagnostics)`` 會把該來源對該資源的診斷整組換掉，這是 LSP
``publishDiagnostics`` 的語意；給空清單就是清掉。``select(severities=None, sources=None, uri=None)``
負責篩選，而且同樣的內容一定回傳同樣的順序：先依資源，再依位置，再依嚴重度。``counts()`` 回傳各
嚴重度的數量，``sources()`` 回傳目前有回報診斷的來源。

語言服務
--------

語言服務會在它處理的文件開啟、變更或關閉時收到通知，並透過 ``LanguageCapability`` 說明自己提供
哪些功能。

.. code-block:: python

   from je_editor.core import (
       Diagnostic, EditorServices, LanguageCapability, LanguageReply, Severity, TextDocument,
       TextRange, to_uri
   )


   class TodoFinder:
       """回報每一行含有 TODO 的程式碼。"""

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

在文件已經開著之後才登記的服務，會收到它處理的每一份文件的「開啟」通知，所以晚啟動的伺服器仍然
知道有哪些文件開著。``services_for(document, capability)`` 用來找出處理某份文件的服務。

向語言服務發問
~~~~~~~~~~~~~~

補全、懸停說明、符號，以及其他任何問題都走同一個呼叫：給一個收回覆的函式，拿回一個取消的函式。
``services.languages.request()`` 會把問題交給登記順序裡第一個處理那份文件、又提供那個功能的服務。

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

不論服務是當場回答還是過一陣子才回答，呼叫的方式都一樣：

- 手上就有答案的服務（例如語法服務）會在 ``request()`` 回傳之前呼叫那個函式。
- 要等的服務（例如語言伺服器）之後才呼叫，而且可能從自己的執行緒呼叫。要更新畫面的呼叫端得
  自己把回覆轉回畫面執行緒。
- 回覆最多只會送達一次，呼叫取消函式之後不會再送達。這兩點由登記表保證，服務不必自己處理。
- 沒有人能回答時，回覆會帶著 ``error`` ，而且 ``reply.ok`` 是 ``False`` 。不會丟出例外。

``reply.value`` 的內容依功能而定：

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 功能
     - ``reply.value``
   * - ``SYNTAX_TREE``
     - 那份文件的 ``SyntaxSession`` （見下一節）
   * - ``DOCUMENT_SYMBOLS``
     - 有名稱的 ``StructuralRegion`` 組成的 tuple：類別、函式與方法
   * - 其他
     - 等第一個提供它的服務出現時決定

語法分析
--------

``SyntaxEngine`` 把文字變成編輯器需要解析器提供的兩樣東西：一行裡哪幾段是關鍵字、字串或函式
名稱，以及一份文件有哪些類別、函式與區塊。語法樹本身不會離開引擎，所以畫面層不依賴解析器。

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

- ``open_session(language_id)`` 為一份文件開一個自己的 ``SyntaxSession`` ；引擎不能分析那個語言
  時回傳 ``None`` 。
- ``update(text)`` 接收整份文字，回傳分類可能變了的 ``LineSpan`` ；文字沒變時回傳 ``None`` 。
  只有編輯影響到的部分會重新解析，而回傳的範圍可以超出被編輯的那一行：打開一個字串會改變它
  之後的每一行。
- ``spans(line)`` 回傳一行的 ``SyntaxSpan`` ，外層的在前、內層的在後，所以照順序套用時，插值會
  蓋過包住它的字串。
- ``regions()`` 回傳 ``StructuralRegion`` ，外層的在前。 ``kind`` 是 ``RegionKind.CLASS`` 、
  ``FUNCTION`` 、 ``BLOCK`` 與 ``COLLECTION`` 其中之一。
- 行號與欄號跟診斷一樣從 1 起算。欄號以 UTF-16 的單位計，也就是 Qt 與語言伺服器協定用的單位。

``je_editor.adapters.syntax`` 以 Tree-sitter 實作這個引擎，支援 Python、JavaScript 與 JSON。
一種語言就是 ``grammar_table.py`` 裡的一列 ``GrammarSpec`` ，加上 ``queries/<語言>/`` 底下的查詢檔：
``highlights.scm`` 會接在文法自帶的高亮查詢之後， ``regions.scm`` 則指出結構區塊。文法沒有安裝、
或查詢檔編譯不過時，那個語言只是變成不支援，不會丟出例外，編輯器會退回以樣式比對的高亮器。

除錯、工作執行、遠端工作階段與 AI 供應者
----------------------------------------

這四項是介面加上各自的資料物件。實作放在這一層之外的 ``je_editor.adapters`` ，目前有兩個 AI 供應者
（ ``openai`` 與 ``anthropic`` ，見 :doc:`ai_assistant` ）；其餘的由宿主程式或外掛自行登記。

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - 領域
     - 介面
     - 資料物件
   * - 除錯
     - ``DebugSession``
     - ``DebugLaunchRequest``、``Breakpoint``、``StackFrame``、``Variable``、``DebugState``、
       ``StepKind``
   * - 工作執行
     - ``TaskRunner``、``TaskHandle``
     - ``TaskSpec``、``TaskState``、``OutputStream``
   * - 遠端工作階段
     - ``RemoteSession``
     - ``RemoteState``
   * - AI 供應者
     - ``AIProvider``
     - ``ChatRequest``、``ChatMessage``、``ChatRole``、``ChatResponse``、``ModelInfo``、
       ``CancelToken``

- ``TaskSpec`` 的指令一律是引數清單。沒有「把一整行交給 shell」的形式，給字串會被拒絕。
- ``TaskRunner.create(spec)`` 回傳一個尚未啟動的把手。先訂閱它的 ``output`` 與 ``finished`` 事件，
  再呼叫 ``start()``，才不會漏掉一開始的輸出。
- ``RemoteSession.task_runner()`` 回傳的是同一個 ``TaskRunner`` 介面，所以呼叫端不必分辨程序在哪裡
  執行。
- ``AIProvider.complete(request, on_text, cancel)`` 會等到回覆完成才返回，請在背景執行緒呼叫。
  ``on_text`` 會一段一段收到回覆，``CancelToken`` 可以中途取消。

.. code-block:: python

   from je_editor.core import (
       ChatMessage, ChatRequest, ChatResponse, ChatRole, EditorServices, ModelInfo
   )


   class UpperCaseProvider:
       """把問題轉成大寫當作回答。"""

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

事件與執行緒
------------

這些服務用 ``EventHook`` 而不是 Qt 訊號來通知變更。``hook.subscribe(listener)`` 會回傳一個用來
取消這次訂閱的函式。

訂閱者在引發事件的那個執行緒上被呼叫。要更新元件的訂閱者得自己轉回 UI 執行緒，例如發出自己的 Qt
訊號。一個訂閱者丟出例外不會擋住其他訂閱者，錯誤會寫進 JEditor 的日誌。

維持不依賴 Qt
-------------

``test/test_core_architecture.py`` 用三種方式守住這條界線：走訪 ``je_editor.core`` 的匯入關係，
底下只要出現 Qt 或 ``je_editor.pyside_ui`` 的匯入就失敗；列出 UI 層以下唯一允許向上匯入的模組；
並在一個擋掉 Qt 匯入的行程裡實際建立這些服務。

匯入任何子套件都會先執行 ``je_editor/__init__.py``，``import je_editor.core`` 也不例外，而那個檔案會
匯入整個 Qt 應用程式。這些服務本身不需要 Qt，也不需要 ``QApplication``。
