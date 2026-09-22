# JEditor / PyBreeze Plugin Guide / 插件開發指南

JEditor (`je_editor`) supports external plugins for adding **syntax highlighting**, **UI translations**
and **run configurations**. PyBreeze is built on JEditor and loads the same plugins, so this file is the
single guide for both; PyBreeze's `PLUGIN_GUIDE.md` only points here.
Ready-made plugins live in the [IDE_Plugins](https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins) repository.

JEditor（`je_editor`）支援外部插件，可用於新增**語法高亮**、**UI 翻譯**與**執行設定**。
PyBreeze 建立在 JEditor 之上、載入同一套插件，所以兩者共用這份指南；PyBreeze 的 `PLUGIN_GUIDE.md` 只是指向這裡。
現成的插件放在 [IDE_Plugins](https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins) repo。

---

## Installing Plugins / 安裝插件

- **Plugin Browser**: *Plugins → Plugin Browser* lists every `.py` file of a GitHub repository
  (default `https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins`, any public repository URL can be typed in), shows its metadata and source,
  and **Download & Install** saves the file into `jeditor_plugins/` under the current working
  directory. Restart the editor to load it.
- **By hand**: copy a plugin file (or a package directory) into `jeditor_plugins/`.

<!-- -->

- **插件瀏覽器**：*插件 → Plugin Browser* 會列出 GitHub repo 裡的每個 `.py` 檔（預設為 `https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins`，
  也可以輸入其他公開 repo 的網址），可以看 metadata 與原始碼；按 **Download & Install** 會把檔案存到
  目前工作目錄下的 `jeditor_plugins/`。重新啟動編輯器後生效。
- **手動**：把插件檔（或套件目錄）複製到 `jeditor_plugins/`。

---

## Quick Start / 快速開始

1. Create a `.py` file in the `jeditor_plugins/` directory (under your working directory).
2. Define a `register()` function.
3. Optionally define `PLUGIN_NAME`, `PLUGIN_AUTHOR`, `PLUGIN_VERSION` for the Plugins menu.

<!-- -->

1. 在工作目錄下的 `jeditor_plugins/` 建立一個 `.py` 檔案。
2. 定義一個 `register()` 函式。
3. 可選：定義 `PLUGIN_NAME`、`PLUGIN_AUTHOR`、`PLUGIN_VERSION`，會顯示在插件選單中。

---

## Plugin Metadata / 插件元資料

```python
PLUGIN_NAME = "My Plugin"       # Display name in the Plugins menu / 插件選單顯示名稱
PLUGIN_AUTHOR = "Your Name"     # Author / 作者
PLUGIN_VERSION = "1.0.0"        # Version / 版本號
```

All three are optional. If omitted, the filename is used as the plugin name.

三者皆為可選。若未定義，則以檔名作為插件名稱。

---

## Syntax Highlighting Plugin / 語法高亮插件

Use `register_programming_language()` to add syntax highlighting for file types.

使用 `register_programming_language()` 為檔案類型新增語法高亮。

### API

```python
from je_editor.plugins import register_programming_language

register_programming_language(
    suffix=".ext",              # File extension / 副檔名
    syntax_words={...},         # Keyword groups / 關鍵字群組
    syntax_rules={...},         # Regex rules (optional) / 正則規則（可選）
)
```

### syntax_words format / syntax_words 格式

```python
from PySide6.QtGui import QColor

syntax_words = {
    "group_name": {
        "words": ("keyword1", "keyword2", ...),   # Tuple or set of keywords / 關鍵字元組或集合
        "color": QColor(r, g, b),                  # Highlight color / 高亮顏色
    },
    # More groups...
}
```

### syntax_rules format / syntax_rules 格式

```python
syntax_rules = {
    "rule_name": {
        "rules": (r"regex_pattern", ...),   # Tuple of regex patterns / 正則表達式元組
        "color": QColor(r, g, b),           # Highlight color / 高亮顏色
    },
}
```

### Full Example / 完整範例

```python
"""Go syntax highlighting plugin."""
from PySide6.QtGui import QColor
from je_editor.plugins import register_programming_language

PLUGIN_NAME = "Go Syntax Highlighting"
PLUGIN_AUTHOR = "Your Name"
PLUGIN_VERSION = "1.0.0"

go_syntax_words = {
    "keywords": {
        "words": (
            "break", "case", "chan", "const", "continue",
            "default", "defer", "else", "fallthrough", "for",
            "func", "go", "goto", "if", "import",
            "interface", "map", "package", "range", "return",
            "select", "struct", "switch", "type", "var",
        ),
        "color": QColor(86, 156, 214),
    },
    "types": {
        "words": (
            "bool", "byte", "complex64", "complex128",
            "float32", "float64", "int", "int8", "int16",
            "int32", "int64", "rune", "string", "uint",
            "uint8", "uint16", "uint32", "uint64", "uintptr",
            "error", "nil", "true", "false", "iota",
        ),
        "color": QColor(78, 201, 176),
    },
}

go_syntax_rules = {
    "single_line_comment": {
        "rules": (r"//[^\n]*",),
        "color": QColor(106, 153, 85),
    },
}


def register() -> None:
    register_programming_language(
        suffix=".go",
        syntax_words=go_syntax_words,
        syntax_rules=go_syntax_rules,
    )
```

### Multiple Suffixes / 多個副檔名

If a language uses multiple file extensions, register each suffix with the same `syntax_words`:

若一個語言使用多個副檔名，用相同的 `syntax_words` 分別註冊每個副檔名：

```python
def register() -> None:
    for suffix in (".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx"):
        register_programming_language(
            suffix=suffix,
            syntax_words=cpp_syntax_words,
            syntax_rules=cpp_syntax_rules,
        )
```

They will be grouped under one submenu in the Plugins menu.

它們會在插件選單中合併顯示在同一個子選單下。

---

## Translation Plugin / 翻譯插件

Use `register_natural_language()` to add a new UI language.

使用 `register_natural_language()` 新增 UI 語言。

### API

```python
from je_editor.plugins import register_natural_language

register_natural_language(
    language_key="French",          # Internal key / 內部鍵值
    display_name="Francais",        # Shown in Language menu / 語言選單顯示名稱
    word_dict={...},                # Translation dictionary / 翻譯字典
)
```

### word_dict keys / word_dict 鍵值

The `word_dict` should contain the same keys as jeditor's built-in `english_word_dict`.
Common keys include:

`word_dict` 應包含與 jeditor 內建 `english_word_dict` 相同的鍵值。
常用鍵值包括：

| Key | Description / 說明 |
|---|---|
| `application_name` | Window title / 視窗標題 |
| `file_menu_label` | File menu / 檔案選單 |
| `run_menu_label` | Run menu / 執行選單 |
| `tab_name_editor` | Editor tab / 編輯器分頁 |
| `language_menu_label` | Language menu / 語言選單 |
| `help_menu_label` | Help menu / 幫助選單 |

For a complete list, refer to `je_editor.utils.multi_language.english.english_word_dict`
or see the example plugin [`languages/french.py`](https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins/blob/main/languages/french.py) in IDE_Plugins.

完整鍵值列表請參考 `je_editor.utils.multi_language.english.english_word_dict`，
或參考 IDE_Plugins 的範例插件 [`languages/french.py`](https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins/blob/main/languages/french.py)。

### Full Example / 完整範例

```python
"""Japanese translation plugin."""
from je_editor.plugins import register_natural_language

PLUGIN_NAME = "Japanese Translation"
PLUGIN_AUTHOR = "Your Name"
PLUGIN_VERSION = "1.0.0"

japanese_word_dict = {
    "application_name": "JEditor",
    "file_menu_label": "ファイル",
    "run_menu_label": "実行",
    "tab_name_editor": "エディタ",
    "language_menu_label": "言語",
    "language_menu_bar_english": "英語",
    "language_menu_bar_traditional_chinese": "繁体字中国語",
    "language_menu_bar_please_restart_messagebox": "アプリケーションを再起動してください",
    # ... more keys
}


def register() -> None:
    register_natural_language(
        language_key="Japanese",
        display_name="日本語",
        word_dict=japanese_word_dict,
    )
```

---

## Run Config (Execute Files) / 執行設定

Plugins can register a `PLUGIN_RUN_CONFIG` to enable running files from the **Run with...** menu.

插件可定義 `PLUGIN_RUN_CONFIG`，讓使用者可以從 **以...執行** 選單執行檔案。

### Interpreted Languages / 直譯式語言

For languages that run directly (Go, Java 11+, Python):

直接執行的語言（Go、Java 11+、Python）：

```python
PLUGIN_RUN_CONFIG = {
    "name": "Go",                   # Display name in menu / 選單顯示名稱
    "suffixes": (".go",),           # Supported file types / 支援的副檔名
    "compiler": "go",               # Executable / 執行檔
    "args": ("run",),               # Args before file path / 檔案路徑前的參數
}
# Runs: go run file.go
```

### Compiled Languages / 編譯式語言

For languages that need compile-then-run (C, C++, Rust):

需要先編譯再執行的語言（C、C++、Rust）：

```python
PLUGIN_RUN_CONFIG = {
    "name": "C (GCC)",
    "suffixes": (".c",),
    "compiler": "gcc",
    "args": (),
    "compile_then_run": True,       # Compile first, then run output / 先編譯再執行
    "output_flag": "-o",            # Flag for output binary / 輸出檔案的旗標
}
# Compiles: gcc file.c -o file
# Then runs: ./file (Linux/Mac) or file.exe (Windows)
```

### Config Keys / 設定鍵值

| Key | Required | Description |
|---|---|---|
| `name` | Yes | Display name / 顯示名稱 |
| `suffixes` | Yes | Tuple of file extensions / 副檔名元組 |
| `compiler` | Yes | Compiler/interpreter executable / 編譯器或直譯器 |
| `args` | No | Extra args before file path / 檔案路徑前的額外參數 |
| `compile_then_run` | No | If `True`, compile first / 若為 `True` 則先編譯 |
| `output_flag` | No | Output file flag (default `"-o"`) / 輸出旗標 |

---

## Directory Structure / 目錄結構

```
working_directory/
  jeditor_plugins/
    my_syntax.py            # Single-file plugin / 單檔插件
    my_language.py
    my_package/             # Package plugin / 套件插件
      __init__.py
    program_languages/      # Category directory (no __init__.py) / 分類目錄（沒有 __init__.py）
      go_syntax.py
```

- Two `jeditor_plugins/` directories are scanned: the one under the current working directory, then
  the one next to the installed `je_editor` package (development checkouts). If two plugins share a
  name, the first one found wins.
- A subdirectory with `__init__.py` is one package plugin; a subdirectory without it is a category and
  is scanned recursively.
- Files and directories starting with `_` or `.` are ignored.
- Each plugin must have a `register()` function; a module without one is skipped with a warning.

<!-- -->

- 會掃描兩個 `jeditor_plugins/`：先是目前工作目錄底下的，再來是已安裝的 `je_editor` 套件旁邊的（開發用的
  原始碼目錄）。兩個插件同名時，先找到的那個生效。
- 有 `__init__.py` 的子目錄算一個套件插件；沒有的算分類目錄，會遞迴往下找。
- 以 `_` 或 `.` 開頭的檔案與目錄會被忽略。
- 每個插件必須有 `register()` 函式；沒有的模組會被略過並記一筆警告。

---

## Existing Plugins / 現有插件

These live in the [IDE_Plugins](https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins) repository (install them with the Plugin Browser).

這些插件放在 [IDE_Plugins](https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins) repo（用插件瀏覽器安裝）。

| Plugin | File | Type | Run Support |
|---|---|---|---|
| C Syntax Highlighting | `program_languages/c_syntax.py` | Syntax (`.c`, `.i`) | GCC compile & run |
| C++ Syntax Highlighting | `program_languages/cpp_syntax.py` | Syntax (`.cpp`, `.cxx`, `.cc`, `.h`, `.hpp`, `.hxx`) | G++ compile & run |
| Go Syntax Highlighting | `program_languages/go_syntax.py` | Syntax (`.go`) | `go run` |
| Java Syntax Highlighting | `program_languages/java_syntax.py` | Syntax (`.java`, `.jav`) | `java` |
| Rust Syntax Highlighting | `program_languages/rust_syntax.py` | Syntax (`.rs`) | rustc compile & run |
| French Translation | `languages/french.py` | Language | - |
