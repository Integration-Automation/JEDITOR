"""
登記編輯器內建的 AI 供應者
Register the AI providers the editor ships with.

對話面板只跟登記表要供應者，所以新增一家只要在這裡（或外掛裡）多登記一個，面板
不必改。
The chat panel only asks the registry for a provider, so adding a vendor is one
more registration here, or in a plugin, and nothing changes in the panel.
"""
from __future__ import annotations

from collections.abc import Callable

from je_editor.adapters.ai.anthropic_provider import AnthropicProvider
from je_editor.adapters.ai.openai_provider import OpenAIProvider
from je_editor.core.ai.ai_provider import AIProvider
from je_editor.core.ai.ai_settings import AISettings, ProviderSettings
from je_editor.core.registry.named_registry import NamedRegistry

# 內建的供應者，依選單上的順序 / The built-in providers, in the order a menu shows them
BUILTIN_PROVIDER_TYPES = (OpenAIProvider, AnthropicProvider)


def register_builtin_ai_providers(registry: NamedRegistry[AIProvider],
                                  settings: Callable[[], AISettings]) -> None:
    """
    把內建的供應者登記進登記表
    Register the built-in providers.

    每個供應者拿到的是「取得自己那組設定」的函式，而不是設定本身，所以使用者改了
    設定之後，下一次請求就會用新的，不必重新登記。
    Each provider is given a function that returns its own group of settings,
    not the settings themselves, so a change the user makes is used by the next
    request with nothing registered again.

    :param registry: 要登記到哪個登記表 / the registry to register into
    :param settings: 取得目前全部設定的函式 / returns all the settings as they are now
    :raises JEditorServiceException: 已經有同名的供應者 / when a provider of the
        same name is already registered
    """
    for provider_type in BUILTIN_PROVIDER_TYPES:
        registry.register(provider_type.name, provider_type(_settings_of(settings, provider_type.name)))


def _settings_of(settings: Callable[[], AISettings], provider: str) -> Callable[[], ProviderSettings]:
    """取得「某個供應者的設定」的函式 / A function returning one provider's settings."""
    def current() -> ProviderSettings:
        return settings().settings_for(provider)

    return current
