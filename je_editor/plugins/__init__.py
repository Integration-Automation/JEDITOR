from je_editor.utils.logging.loggin_instance import jeditor_logger


# -----------------------------
# Programming Language Plugin Registry
# 程式語言插件註冊表
# -----------------------------
# Maps file suffix (e.g. ".cpp") to syntax config dict
# 將副檔名（如 ".cpp"）映射到語法設定字典
_programming_language_plugins: dict = {}


def register_programming_language(
    suffix: str,
    syntax_words: dict,
    syntax_rules: dict | None = None,
) -> None:
    """
    註冊一個程式語言插件，用於語法高亮。
    Register a programming language plugin for syntax highlighting.

    :param suffix: 副檔名，例如 ".cpp" / File suffix, e.g. ".cpp"
    :param syntax_words: 關鍵字設定字典 / Keyword settings dict
        格式 / Format: {"group_name": {"words": (...), "color": QColor(...)}}
    :param syntax_rules: 額外語法規則字典（可選）/ Extra syntax rules dict (optional)
        格式 / Format: {"rule_name": {"rules": (...), "color": QColor(...)}}
    """
    jeditor_logger.info(f"register_programming_language suffix: {suffix}")
    _programming_language_plugins[suffix] = {
        "syntax_words": syntax_words,
        "syntax_rules": syntax_rules or {},
    }
    # 同步到 syntax_extend_setting_dict，讓 PythonHighlighter 也能使用
    # Sync to syntax_extend_setting_dict so PythonHighlighter can use it
    from je_editor.pyside_ui.code.syntax.syntax_setting import syntax_extend_setting_dict
    syntax_extend_setting_dict[suffix] = syntax_words


def get_programming_language_plugin(suffix: str) -> dict | None:
    """
    取得指定副檔名的程式語言插件。
    Get programming language plugin by file suffix.
    """
    return _programming_language_plugins.get(suffix)


def get_all_programming_language_suffixes() -> list[str]:
    """
    取得所有已註冊的程式語言副檔名列表。
    Get all registered programming language suffixes.
    """
    return list(_programming_language_plugins.keys())


# -----------------------------
# Natural Language Plugin Registry
# 自然語言插件註冊表
# -----------------------------
# Maps language key (e.g. "French") to translation dict
# 將語言鍵（如 "French"）映射到翻譯字典
_natural_language_plugins: dict = {}


def register_natural_language(
    language_key: str,
    display_name: str,
    word_dict: dict,
) -> None:
    """
    註冊一個自然語言插件，用於 UI 翻譯。
    Register a natural language plugin for UI translation.

    :param language_key: 語言鍵，例如 "French" / Language key, e.g. "French"
    :param display_name: 顯示名稱，例如 "Francais" / Display name, e.g. "Francais"
    :param word_dict: 翻譯字典 / Translation dictionary (same keys as english_word_dict)
    """
    jeditor_logger.info(f"register_natural_language language_key: {language_key}")
    _natural_language_plugins[language_key] = {
        "display_name": display_name,
        "word_dict": word_dict,
    }
    # 同步到 LanguageWrapper，讓語言切換生效
    # Sync to LanguageWrapper so language switching works
    from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
    language_wrapper.choose_language_dict[language_key] = word_dict


def get_natural_language_plugin(language_key: str) -> dict | None:
    """
    取得指定語言鍵的自然語言插件。
    Get natural language plugin by language key.
    """
    return _natural_language_plugins.get(language_key)


def get_all_natural_languages() -> dict:
    """
    取得所有已註冊的自然語言插件。
    Get all registered natural language plugins.
    Returns: {"French": {"display_name": "Francais", "word_dict": {...}}, ...}
    """
    return _natural_language_plugins.copy()


# -----------------------------
# Plugin Run Config Registry
# 插件執行設定註冊表
# -----------------------------
# Maps plugin name to run config dict
# 將插件名稱映射到執行設定字典
_plugin_run_configs: list[dict] = []


def register_plugin_run_config(run_config: dict) -> None:
    """
    註冊一個插件的執行設定。
    Register a plugin's run configuration.

    :param run_config: 執行設定字典 / Run configuration dict
        格式 / Format: {"name": "C++ (G++)", "suffixes": (".cpp",), "compiler": "g++", ...}
    """
    jeditor_logger.info(f"register_plugin_run_config: {run_config.get('name')}")
    _plugin_run_configs.append(run_config)


def get_all_plugin_run_configs() -> list[dict]:
    """
    取得所有已註冊的插件執行設定。
    Get all registered plugin run configurations.
    """
    return _plugin_run_configs.copy()


def get_plugin_run_config_by_suffix(suffix: str) -> dict | None:
    """
    依副檔名取得對應的插件執行設定。
    Get plugin run configuration by file suffix.
    """
    for config in _plugin_run_configs:
        if suffix in config.get("suffixes", ()):
            return config
    return None


# -----------------------------
# Plugin Metadata Registry
# 插件元資料註冊表
# -----------------------------
# Stores plugin metadata (name, author, version, etc.)
# 儲存插件元資料（名稱、作者、版本等）
_plugin_metadata_list: list[dict] = []


def register_plugin_metadata(metadata: dict) -> None:
    """
    註冊一個插件的元資料。
    Register a plugin's metadata.

    :param metadata: 元資料字典 / Metadata dict
        格式 / Format: {"name": "...", "author": "...", "version": "...", "run_config": {...} or None}
    """
    jeditor_logger.info(f"register_plugin_metadata: {metadata.get('name')}")
    _plugin_metadata_list.append(metadata)


def get_all_plugin_metadata() -> list[dict]:
    """
    取得所有已註冊的插件元資料。
    Get all registered plugin metadata.
    """
    return _plugin_metadata_list.copy()
