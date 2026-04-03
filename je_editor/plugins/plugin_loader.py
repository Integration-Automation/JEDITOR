"""
外部插件載入器 / External Plugin Loader

從工作目錄下的 jeditor_plugins/ 目錄自動載入插件。
Auto-discover and load plugins from jeditor_plugins/ under the working directory.

插件目錄結構 / Plugin directory structure:
    jeditor_plugins/
        my_language.py              # 單檔插件 / Single-file plugin
        my_package/                 # 套件插件 / Package plugin
            __init__.py
        program_languages/          # 分類目錄 / Category directory
            cpp_syntax.py
        languages/
            french.py

每個插件必須提供一個 register() 函式。
Each plugin must provide a register() function.
"""
import importlib.util
import sys
import traceback
from pathlib import Path

from je_editor.utils.logging.loggin_instance import jeditor_logger

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
_PLUGIN_DIR_NAME = "jeditor_plugins"


def _find_all_plugins_dirs() -> list[Path]:
    """
    收集所有可能的 jeditor_plugins/ 目錄（去重）。
    Collect all possible jeditor_plugins/ directories (deduplicated).

    搜尋順序 / Search order:
    1. 使用者的工作目錄 / User's current working directory
    2. je_editor 套件的上層目錄（開發模式）/ Parent of je_editor package (development mode)

    兩個位置都會掃描，確保不同位置啟動都能載入插件。
    Both locations are scanned so plugins load regardless of launch location.
    """
    dirs = []
    seen = set()

    for base in (Path.cwd(), _PACKAGE_ROOT):
        candidate = (base / _PLUGIN_DIR_NAME).resolve()
        if candidate not in seen and candidate.exists():
            dirs.append(candidate)
            seen.add(candidate)

    return dirs


_plugins_loaded = False


def _collect_plugin_entries(directory: Path, entries: list[tuple[str, Path]]) -> None:
    """
    遞迴收集插件入口。
    Recursively collect plugin entries from a directory.

    支援三種結構 / Supports three structures:
    1. 單檔插件: xxx.py (含 register()) / Single-file plugin
    2. 套件插件: xxx/__init__.py / Package plugin
    3. 分類目錄: 不含 __init__.py 的子目錄，遞迴進入 / Category directory (no __init__.py), recurse into
    """
    if not directory.exists():
        return

    for item in sorted(directory.iterdir()):
        if item.name.startswith("_") or item.name.startswith("."):
            continue

        if item.is_file() and item.suffix == ".py":
            # 單檔插件 / Single-file plugin
            entries.append((item.stem, item))
        elif item.is_dir():
            if (item / "__init__.py").exists():
                # 套件插件 / Package plugin
                entries.append((item.name, item / "__init__.py"))
            else:
                # 分類目錄，遞迴進入 / Category directory, recurse
                _collect_plugin_entries(item, entries)


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

    loaded = []

    # 決定要掃描的目錄 / Determine directories to scan
    if plugins_dir is not None:
        dirs_to_scan = [Path(plugins_dir)]
    else:
        dirs_to_scan = _find_all_plugins_dirs()

    if not dirs_to_scan:
        _plugins_loaded = True
        jeditor_logger.info("No plugin directories found, skipping external plugins")
        return loaded

    # 從所有目錄收集插件入口（遞迴掃描子目錄）
    # Collect plugin entries from all directories (recursively scan subdirectories)
    plugin_entries = []
    seen_names: set[str] = set()
    for scan_dir in dirs_to_scan:
        jeditor_logger.info(f"Loading external plugins from: {scan_dir}")
        entries: list[tuple[str, Path]] = []
        _collect_plugin_entries(scan_dir, entries)
        for name, path in entries:
            # 同名插件只載入第一個（工作目錄優先）
            # Skip duplicate plugin names (working directory takes priority)
            if name not in seen_names:
                plugin_entries.append((name, path))
                seen_names.add(name)

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

            # 收集插件元資料 / Collect plugin metadata
            from je_editor.plugins import register_plugin_metadata, register_plugin_run_config
            metadata = {
                "name": getattr(module, "PLUGIN_NAME", plugin_name),
                "author": getattr(module, "PLUGIN_AUTHOR", ""),
                "version": getattr(module, "PLUGIN_VERSION", ""),
                "run_config": getattr(module, "PLUGIN_RUN_CONFIG", None),
            }
            register_plugin_metadata(metadata)

            # 註冊執行設定 / Register run config
            if hasattr(module, "PLUGIN_RUN_CONFIG"):
                register_plugin_run_config(module.PLUGIN_RUN_CONFIG)

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
