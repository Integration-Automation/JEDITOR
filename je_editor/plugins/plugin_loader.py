"""
外部插件載入器 / External Plugin Loader

從專案根目錄下的 jeditor_plugins/ 目錄自動載入插件。
Auto-discover and load plugins from jeditor_plugins/ under the project root.

插件目錄結構 / Plugin directory structure:
    jeditor_plugins/
        my_language.py          # 單檔插件 / Single-file plugin
        my_package/             # 套件插件 / Package plugin
            __init__.py

每個插件必須提供一個 register() 函式。
Each plugin must provide a register() function.
"""
import importlib.util
import sys
import traceback
from pathlib import Path

from je_editor.utils.logging.loggin_instance import jeditor_logger

# 插件目錄搜尋順序 / Plugin directory search order:
# 1. 使用者的工作目錄 / User's current working directory
# 2. je_editor 套件的上層目錄（開發模式）/ Parent of je_editor package (development mode)
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
_PLUGIN_DIR_NAME = "jeditor_plugins"


def _find_plugins_dir() -> Path:
    """
    尋找 jeditor_plugins/ 目錄。
    Find the jeditor_plugins/ directory.
    優先使用工作目錄，其次使用套件目錄。
    Prefer current working directory, then fall back to package directory.
    """
    cwd_plugins = Path.cwd() / _PLUGIN_DIR_NAME
    if cwd_plugins.exists():
        return cwd_plugins
    return _PACKAGE_ROOT / _PLUGIN_DIR_NAME


_plugins_loaded = False


def load_external_plugins(plugins_dir: Path | str | None = None) -> list[str]:
    """
    從 jeditor_plugins/ 目錄載入所有外部插件。
    Load all external plugins from jeditor_plugins/ directory.

    每個插件（.py 檔案或含 __init__.py 的資料夾）都需提供 register() 函式。
    Each plugin (.py file or folder with __init__.py) must provide a register() function.

    :param plugins_dir: 插件目錄路徑（預設為專案根目錄下的 jeditor_plugins/）
                        Plugin directory path (defaults to jeditor_plugins/ under project root)
    :return: 成功載入的插件名稱列表 / List of successfully loaded plugin names
    """
    global _plugins_loaded
    if _plugins_loaded and plugins_dir is None:
        return []

    if plugins_dir is not None:
        plugins_dir = Path(plugins_dir)
    else:
        plugins_dir = _find_plugins_dir()

    loaded = []

    if not plugins_dir.exists():
        _plugins_loaded = True
        jeditor_logger.info(f"Plugin directory not found: {plugins_dir}, skipping external plugins")
        return loaded

    jeditor_logger.info(f"Loading external plugins from: {plugins_dir}")

    # 收集所有插件入口 / Collect all plugin entries
    plugin_entries = []

    for item in sorted(plugins_dir.iterdir()):
        if item.name.startswith("_") or item.name.startswith("."):
            continue

        if item.is_file() and item.suffix == ".py":
            # 單檔插件 / Single-file plugin
            plugin_entries.append((item.stem, item))
        elif item.is_dir() and (item / "__init__.py").exists():
            # 套件插件 / Package plugin
            plugin_entries.append((item.name, item / "__init__.py"))

    # 載入並註冊 / Load and register
    for plugin_name, plugin_path in plugin_entries:
        try:
            jeditor_logger.info(f"Loading plugin: {plugin_name} from {plugin_path}")

            spec = importlib.util.spec_from_file_location(
                f"jeditor_plugin_{plugin_name}", str(plugin_path)
            )
            if spec is None or spec.loader is None:
                jeditor_logger.warning(
                    f"Plugin '{plugin_name}' cannot be loaded from {plugin_path}, skipped"
                )
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # 呼叫 register() 函式 / Call register() function
            if hasattr(module, "register"):
                module.register()
                loaded.append(plugin_name)
                jeditor_logger.info(f"Plugin loaded successfully: {plugin_name}")
            else:
                jeditor_logger.warning(
                    f"Plugin '{plugin_name}' has no register() function, skipped"
                )

        except Exception as e:
            jeditor_logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            jeditor_logger.error(traceback.format_exc())

    _plugins_loaded = True
    jeditor_logger.info(f"External plugins loaded: {loaded}")
    return loaded
