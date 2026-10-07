"""
JEditor 的核心服務層
JEditor's core service layer.

工作區、文件、診斷、語言服務、除錯、工作執行、遠端與 AI 供應者的介面與資料物件。
這一層不匯入 Qt，也不匯入 ``je_editor.pyside_ui``，所以可以在沒有視窗的地方使用；
``test/test_core_architecture.py`` 守著這條界線。
The interfaces and data objects for the workspace, documents, diagnostics,
language services, debugging, task execution, remote sessions and AI providers.
Nothing here imports Qt or ``je_editor.pyside_ui``, so it works where there is
no window; ``test/test_core_architecture.py`` holds that line.
"""
from je_editor.core.ai.ai_provider import (
    AIProvider, CancelToken, ChatMessage, ChatRequest, ChatResponse, ChatRole, ModelInfo
)
from je_editor.core.ai.ai_settings import AISettings, ProviderSettings
from je_editor.core.ai.chat_session import ChatSession
from je_editor.core.debug.debug_session import (
    Breakpoint, DebugLaunchRequest, DebugSession, DebugSessionFactory, DebugState,
    StackFrame, StepKind, Variable
)
from je_editor.core.diagnostics.diagnostic_model import (
    Diagnostic, DiagnosticStore, Position, QuickFix, RelatedInformation, Severity,
    TextEdit, TextRange, filter_diagnostics
)
from je_editor.core.document.document_model import Document, DocumentStore, TextDocument
from je_editor.core.events.event_hook import EventHook
from je_editor.core.language.language_request import (
    CancelRequest, LanguageReply, LanguageRequest, ReplyHandler
)
from je_editor.core.language.language_service import (
    LanguageCapability, LanguageService, LanguageServiceRegistry
)
from je_editor.core.process.task_service import (
    OutputStream, TaskHandle, TaskRunner, TaskSpec, TaskState
)
from je_editor.core.registry.named_registry import NamedRegistry
from je_editor.core.remote.remote_session import RemoteSession, RemoteState, RemoteTransport
from je_editor.core.services.editor_services import EditorServices
from je_editor.core.syntax.syntax_model import (
    LineSpan, NoSyntaxEngine, RegionKind, StructuralRegion, SyntaxCategory, SyntaxEngine,
    SyntaxSession, SyntaxSpan
)
from je_editor.core.uri.resource_uri import is_local_uri, to_path, to_uri, uri_key, uri_scheme
from je_editor.core.workspace.workspace_model import ProjectRoot, Workspace
from je_editor.utils.exception.exceptions import JEditorServiceException

__all__ = [
    # Services
    "EditorServices", "EventHook", "NamedRegistry", "JEditorServiceException",
    # Workspace
    "Workspace", "ProjectRoot",
    # Resource URIs
    "to_uri", "to_path", "is_local_uri", "uri_key", "uri_scheme",
    # Documents
    "Document", "TextDocument", "DocumentStore",
    # Diagnostics
    "Diagnostic", "DiagnosticStore", "Severity", "Position", "TextRange",
    "RelatedInformation", "TextEdit", "QuickFix", "filter_diagnostics",
    # Language services
    "LanguageService", "LanguageServiceRegistry", "LanguageCapability",
    "LanguageRequest", "LanguageReply", "ReplyHandler", "CancelRequest",
    # Syntax analysis
    "SyntaxEngine", "SyntaxSession", "SyntaxSpan", "SyntaxCategory", "LineSpan",
    "StructuralRegion", "RegionKind", "NoSyntaxEngine",
    # Debugging
    "DebugSession", "DebugSessionFactory", "DebugState", "DebugLaunchRequest",
    "Breakpoint", "StackFrame", "Variable", "StepKind",
    # Task execution
    "TaskRunner", "TaskHandle", "TaskSpec", "TaskState", "OutputStream",
    # Remote sessions
    "RemoteSession", "RemoteState", "RemoteTransport",
    # AI providers
    "AIProvider", "ChatRequest", "ChatResponse", "ChatMessage", "ChatRole",
    "ModelInfo", "CancelToken", "ChatSession", "AISettings", "ProviderSettings",
]
