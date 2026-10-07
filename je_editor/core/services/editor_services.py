"""
把核心服務組在一起
The core services, put together.

每個視窗或每個嵌入的編輯器各有一組自己的服務，由建立它的人持有。這裡刻意沒有
模組層級的單例：宿主程式嵌入兩個編輯器時，它們不該共用工作區與診斷。
Each window, or each embedded editor, has a set of services of its own, held by
whoever built it. There is deliberately no module-level singleton here: a host
that embeds two editors must not find them sharing a workspace and diagnostics.

建立這組服務不需要 ``QApplication``，也不會啟動任何程序或執行緒。
Building this needs no ``QApplication`` and starts no process or thread.
"""
from __future__ import annotations

from je_editor.core.ai.ai_provider import AIProvider
from je_editor.core.debug.debug_session import DebugSessionFactory
from je_editor.core.diagnostics.diagnostic_model import DiagnosticStore
from je_editor.core.document.document_model import DocumentStore
from je_editor.core.language.language_service import LanguageServiceRegistry
from je_editor.core.process.task_service import TaskRunner
from je_editor.core.registry.named_registry import NamedRegistry
from je_editor.core.remote.remote_session import RemoteTransport
from je_editor.core.workspace.workspace_model import Workspace


class EditorServices:
    """
    一個編輯器用到的所有核心服務
    Every core service one editor uses.
    """

    def __init__(self, workspace: Workspace | None = None) -> None:
        """
        :param workspace: 要處理的工作區，沒給時從空的工作區開始
            the workspace to work on, an empty one when omitted
        """
        self.workspace: Workspace = workspace if workspace is not None else Workspace()
        self.documents = DocumentStore()
        self.diagnostics = DiagnosticStore()
        self.languages = LanguageServiceRegistry(self.documents)
        # 以轉接器的種類登記，例如 ``pdb`` / Registered by adapter type, such as ``pdb``
        self.debug_adapters: NamedRegistry[DebugSessionFactory] = NamedRegistry("debug adapter")
        # 以執行的地方登記，例如 ``local`` / Registered by where they run, such as ``local``
        self.task_runners: NamedRegistry[TaskRunner] = NamedRegistry("task runner")
        # 以 URI 的 scheme 登記，例如 ``ssh`` / Registered by URI scheme, such as ``ssh``
        self.remote_transports: NamedRegistry[RemoteTransport] = NamedRegistry("remote transport")
        # 以供應者名稱登記 / Registered by provider name
        self.ai_providers: NamedRegistry[AIProvider] = NamedRegistry("AI provider")
        self._shut_down = False

    @property
    def is_shut_down(self) -> bool:
        """是否已經關閉 / Whether this has been shut down."""
        return self._shut_down

    def shutdown(self) -> None:
        """
        放掉這組服務持有的所有資源
        Release everything these services hold.

        語言服務與工作執行器可能持有程序與執行緒，所以擁有者關閉時一定要呼叫這個。
        重複呼叫沒有作用。
        Language services and task runners may hold processes and threads, so
        the owner has to call this when it closes. Calling it again does nothing.
        """
        if self._shut_down:
            return
        self._shut_down = True
        self.languages.shutdown()
        for name in self.task_runners.names():
            runner = self.task_runners.unregister(name)
            if runner is not None:
                runner.shutdown()
        self.diagnostics.clear()
        for document in self.documents.documents():
            self.documents.close(document.uri)
