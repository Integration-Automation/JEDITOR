"""
組出一組帶著內建實作的核心服務
Build a set of core services with the built-in implementations registered.

``EditorServices`` 本身是空的：沒有供應者，設定也沒有載入。編輯器視窗（以及嵌入
編輯器的宿主程式）用這裡取得一組可以直接用的服務。
``EditorServices`` on its own is empty: no provider, no settings loaded. The
editor window, and a host that embeds the editor, get a ready-to-use set here.
"""
from __future__ import annotations

from pathlib import Path

from je_editor.adapters.ai.builtin_providers import register_builtin_ai_providers
from je_editor.adapters.ai.settings_file import ai_settings_path, load_ai_settings
from je_editor.core.services.editor_services import EditorServices
from je_editor.core.workspace.workspace_model import Workspace


def build_default_services(workspace: Workspace | None = None,
                           settings_directory: str | Path | None = None) -> EditorServices:
    """
    建立一組服務，載入 AI 設定並登記內建的 AI 供應者
    Build the services, load the AI settings and register the built-in AI providers.

    :param workspace: 要處理的工作區，沒給時從空的工作區開始
        the workspace to work on, an empty one when omitted
    :param settings_directory: 放 ``.jeditor`` 的目錄，沒給時用目前工作目錄
        the directory holding ``.jeditor``, the working directory when omitted
    :return: 可以直接使用的服務；擁有者關閉時要呼叫它的 ``shutdown()``
        services ready for use; the owner calls ``shutdown()`` on them when it closes
    """
    services = EditorServices(workspace)
    reload_ai_settings(services, settings_directory)

    def current_settings():
        return services.ai_settings

    register_builtin_ai_providers(services.ai_providers, current_settings)
    return services


def reload_ai_settings(services: EditorServices, settings_directory: str | Path | None = None) -> None:
    """
    從設定檔重新載入 AI 設定
    Load the AI settings from their file again.

    :param services: 要更新的服務 / the services to update
    :param settings_directory: 放 ``.jeditor`` 的目錄，沒給時用目前工作目錄
        the directory holding ``.jeditor``, the working directory when omitted
    """
    services.ai_settings = load_ai_settings(ai_settings_path(settings_directory))
