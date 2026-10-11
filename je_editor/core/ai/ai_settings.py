"""
AI 助理的設定：每個供應者各有一組
The AI assistant's settings: one set for each provider.

原本的設定檔只認得一個「AI_model」，欄位名稱也綁著 OpenAI 相容的服務。這裡改成
以供應者名稱分組，換供應者時各自的金鑰與模型不會互相蓋掉；舊格式的檔案仍然讀得
進來，被當成 OpenAI 那一組。
The settings file used to know a single ``AI_model`` whose fields assumed an
OpenAI-compatible service. Settings are now grouped by provider name, so
switching providers never overwrites another's key or model. A file in the older
format still loads, as the OpenAI group.

純邏輯：只在字典與資料物件之間轉換，不讀寫檔案，也不碰 Qt。
Pure logic: it converts between dictionaries and data objects only, reads and
writes no file, and touches no Qt.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace

# 設定檔裡的鍵 / The keys of the settings file
ACTIVE_PROVIDER_KEY = "active_provider"
PROVIDERS_KEY = "providers"
# 舊格式唯一的一組設定，以及它對應的供應者
# The single group the older format had, and the provider it belongs to
LEGACY_GROUP_KEY = "AI_model"
LEGACY_PROVIDER = "openai"
# 舊格式的欄位名稱對應到現在的欄位 / The older field names and what they are now
_LEGACY_FIELDS = {
    "ai_base_url": "base_url",
    "ai_api_key": "api_key",
    "chat_model": "model",
    "prompt_template": "system_prompt",
}
# 遮蔽金鑰時頭尾各保留幾個字元 / How many characters a masked key keeps at each end
_MASK_KEEP = 4


@dataclass(frozen=True)
class ProviderSettings:
    """
    一個供應者的設定
    The settings of one provider.

    :param api_key: API 金鑰；空字串表示交給供應者自己從環境找
        the API key, empty to let the provider find its own in the environment
    :param base_url: 服務的位址；空字串表示供應者的預設 / the service address,
        empty for the provider's default
    :param model: 要使用的模型；空字串表示供應者的預設 / the model to use, empty
        for the provider's default
    :param system_prompt: 系統提示詞 / the system prompt
    """

    api_key: str = ""
    base_url: str = ""
    model: str = ""
    system_prompt: str = ""

    @property
    def masked_api_key(self) -> str:
        """
        可以顯示在畫面或日誌上的金鑰
        The key in a form that may be shown on screen or written to a log.

        只留頭尾各四個字元；太短的金鑰整個遮掉，免得一半以上都露出來。
        Only the first and last four characters are kept. A key too short for
        that is hidden altogether rather than showing most of itself.
        """
        if not self.api_key:
            return ""
        if len(self.api_key) <= _MASK_KEEP * 2:
            return "*" * len(self.api_key)
        return f"{self.api_key[:_MASK_KEEP]}...{self.api_key[-_MASK_KEEP:]}"


@dataclass
class AISettings:
    """
    所有供應者的設定，以及目前選用哪一個
    Every provider's settings, and which provider is in use.

    :param active_provider: 目前選用的供應者名稱；空字串表示還沒選
        the name of the provider in use, empty when none is chosen yet
    :param providers: 供應者名稱對應它的設定 / each provider's settings, by name
    """

    active_provider: str = ""
    providers: dict[str, ProviderSettings] = field(default_factory=dict)

    def settings_for(self, provider: str) -> ProviderSettings:
        """
        取得某個供應者的設定
        The settings of a provider.

        :param provider: 供應者名稱 / the provider's name
        :return: 它的設定；還沒設定過時是一組空的 / its settings, an empty set
            when it has none yet
        """
        return self.providers.get(provider, ProviderSettings())

    def update(self, provider: str, **changes: str) -> ProviderSettings:
        """
        修改某個供應者的設定
        Change the settings of a provider.

        :param provider: 供應者名稱 / the provider's name
        :param changes: 要改的欄位 / the fields to change
        :return: 修改後的設定 / the settings after the change
        """
        updated = replace(self.settings_for(provider), **changes)
        self.providers[provider] = updated
        return updated

    def to_dict(self) -> dict:
        """
        轉成可以寫進設定檔的字典
        The dictionary to write to the settings file.

        :return: 設定的字典形式 / the settings as a dictionary
        """
        return {
            ACTIVE_PROVIDER_KEY: self.active_provider,
            PROVIDERS_KEY: {name: asdict(item) for name, item in self.providers.items()},
        }

    @classmethod
    def from_dict(cls, data: object) -> AISettings:
        """
        由設定檔的內容建立設定
        Build the settings from what the settings file holds.

        設定檔可能被手動編輯，所以型別不對的項目會被略過，而不是讓整份設定失效。
        The file may have been edited by hand, so an entry of the wrong type is
        skipped instead of invalidating everything.

        :param data: 設定檔解析後的內容，任何型別 / the parsed file, of any type
        :return: 設定 / the settings
        """
        settings = cls()
        if not isinstance(data, Mapping):
            return settings
        stored = data.get(PROVIDERS_KEY)
        if isinstance(stored, Mapping):
            for name, raw in stored.items():
                if isinstance(name, str) and name and isinstance(raw, Mapping):
                    settings.providers[name] = _provider_settings(raw)
        legacy = data.get(LEGACY_GROUP_KEY)
        if isinstance(legacy, Mapping) and LEGACY_PROVIDER not in settings.providers:
            migrated = _provider_settings(
                {_LEGACY_FIELDS[key]: value for key, value in legacy.items() if key in _LEGACY_FIELDS})
            if migrated != ProviderSettings():
                settings.providers[LEGACY_PROVIDER] = migrated
        active = data.get(ACTIVE_PROVIDER_KEY)
        if isinstance(active, str) and active:
            settings.active_provider = active
        elif LEGACY_PROVIDER in settings.providers and isinstance(legacy, Mapping):
            settings.active_provider = LEGACY_PROVIDER
        return settings


def _provider_settings(raw: Mapping) -> ProviderSettings:
    """只取認得而且是字串的欄位 / Keep only the fields that are known and are strings."""
    known = ProviderSettings.__dataclass_fields__
    return ProviderSettings(**{
        key: value for key, value in raw.items() if key in known and isinstance(value, str)})
