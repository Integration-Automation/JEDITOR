# JEDITOR

<p align="center">
  <img src="../docs/source/docs/Eng/image/JEditor.png" alt="JEDITOR Logo" width="200"/>
</p>

<p align="center">
  <strong>一款基于 Python 与 PySide6 打造的现代化、轻量级、可扩展代码编辑器。</strong>
</p>

<p align="center">
  <a href="https://github.com/JE-Chen/je_editor">
    <img src="https://img.shields.io/github/stars/JE-Chen/je_editor?style=social" alt="GitHub Stars"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/v/je_editor" alt="PyPI Version"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/pyversions/je_editor" alt="Python Versions"/>
  </a>
  <a href="https://github.com/JE-Chen/je_editor/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/JE-Chen/je_editor" alt="License"/>
  </a>
  <a href="https://je-editor.readthedocs.io/en/latest/">
    <img src="https://img.shields.io/readthedocs/je-editor" alt="Read the Docs"/>
  </a>
</p>

<p align="center">
  <a href="../README.md">English</a> |
  <a href="README_zh-TW.md">繁體中文</a>
</p>

---

## 目录

- [简介](#简介)
- [主要特性](#主要特性)
- [截图展示](#截图展示)
- [系统要求](#系统要求)
- [安装方式](#安装方式)
- [快速开始](#快速开始)
- [功能详情](#功能详情)
  - [代码编辑](#代码编辑)
  - [导航](#导航)
  - [程序执行与调试](#程序执行与调试)
  - [代码质量与格式化](#代码质量与格式化)
  - [文件操作](#文件操作)
  - [Git 集成](#git-集成)
  - [AI 助手](#ai-助手)
  - [控制台与 REPL](#控制台与-repl)
  - [内置浏览器](#内置浏览器)
  - [插件系统](#插件系统)
  - [主题与自定义](#主题与自定义)
  - [多语言界面](#多语言界面)
- [键盘快捷键](#键盘快捷键)
- [项目架构](#项目架构)
- [插件开发](#插件开发)
- [配置文件](#配置文件)
- [文档](#文档)
- [参与贡献](#参与贡献)
- [许可证](#许可证)

---

## 简介

JEDITOR 是原始 JEditor 项目的完全重写版本，从零开始重新打造，专注于**速度**、**易用性**与**可扩展性**。以 **PySide6**（Qt for Python）为基础，提供现代化的桌面编辑体验，内置语法高亮、自动补全、集成式 Git 客户端、AI 助手、内嵌浏览器、IPython 控制台以及强大的插件系统等丰富功能。

与原始 JEditor 相比，JEDITOR 性能提升高达 **1000%**，同时提供更加丰富的功能集。

---

## 主要特性

| 类别 | 功能 |
|---|---|
| **编辑器** | 多标签页编辑、十二种语言的语法高亮、自动补全（Jedi 与语言服务器）、可选中的多光标、支持联动占位符的代码片段、分屏视图、缩略图、代码折叠（缩进与花括号）、书签、出现处高亮、行操作 |
| **导航** | 命令面板、快速打开（转到文件）、转到符号、文档大纲、导航历史（前进／后退）、TODO/FIXME 任务面板 |
| **执行** | 运行 Python 脚本（F5）、调试模式（F9）、Shell 命令、虚拟环境检测 |
| **代码质量** | YAPF 格式化、保存时格式化、PEP8 检查、Ruff 静态分析与问题面板、语言服务器诊断与快速修复、带 traceback 与覆盖率的 pytest 面板、JSON 重新格式化 |
| **Git** | 分支管理、提交历史、并排差异查看器、行号区变更标记、逐处变更暂存与还原、行内 blame、贮藏（stash）、冲突解决、审计日志 |
| **AI** | 通过 LangChain 集成 OpenAI GPT、交互式聊天面板、可配置模型与提示词 |
| **控制台** | 交互式 Shell、Jupyter/IPython 控制台、命令历史、多 Shell 支持 |
| **浏览器** | 内嵌网页浏览器、URL 导航、页面内搜索 |
| **插件** | 自定义语法高亮、UI 翻译、运行配置、自动发现 |
| **界面** | 深色/浅色主题（Qt Material）与配套的编辑器配色、可配置的键盘快捷键、字体自定义、可停靠面板、系统托盘、工具栏、状态栏 |
| **国际化** | 英文、繁体中文、简体中文、日本語；跟随系统语言、无需重启即可切换、可通过插件扩展 |
| **文件** | 自动保存、多编码支持（UTF-8、GBK、Latin-1 等）、最近打开的文件、多文件会话恢复 |

---

## 截图展示

<p align="center">
  <img src="../docs/source/docs/Zh/image/JEditor.png" alt="JEDITOR 截图"/>
</p>

---

## 系统要求

| 平台 | 版本 |
|---|---|
| **Windows** | Windows 10 / 11 |
| **macOS** | 10.5 ~ 11 Big Sur |
| **Linux** | Ubuntu 20.04+ |
| **Raspberry Pi** | 3B+ |
| **Python** | 3.10+（已测试 3.10、3.11、3.12） |

---

## 安装方式

### 从 PyPI 安装（推荐）

```bash
pip install je_editor
```

### 从源码安装

```bash
git clone https://github.com/JE-Chen/je_editor.git
cd je_editor
pip install .
```

### 依赖包

核心依赖包会自动安装：

| 包名 | 用途 |
|---|---|
| PySide6 | GUI 框架（Qt for Python） |
| qt-material | 深色/浅色 Material 主题 |
| yapf | Python 代码格式化（Google 风格） |
| jedi | Python 自动补全与分析 |
| ruff | 快速 Python 静态分析工具 |
| gitpython | Git 仓库操作 |
| langchain + langchain_openai | AI/LLM 集成 |
| watchdog | 文件系统监控 |
| pycodestyle | PEP8 风格检查 |
| qtconsole | Jupyter/IPython 控制台组件 |

---

## 快速开始

### 启动编辑器

```bash
python -m je_editor
```

### 作为 Python 库使用

```python
from je_editor import start_editor

start_editor()
```

编辑器默认会以最大化窗口与深色琥珀色主题启动。

---

## 功能详情

### 代码编辑

- **多标签页编辑器** -- 同时处理多个文件，支持关闭标签页。
- **语法高亮** -- 内置 Python 语法高亮，可通过插件扩展支持更多语言。
- **自动补全** -- 由 Jedi 驱动的上下文感知代码建议。
- **行号显示** -- 编辑器旁显示行号，并高亮当前行。
- **搜索与替换** -- 支持在当前文件、文件夹或整个项目中搜索，提供正则表达式与区分大小写选项。大型项目使用后台线程处理。
- **代码折叠** -- 从行号区的折叠三角或键盘展开与收起代码块。Python 等以缩进表达层级的文件按缩进折叠；C 系语言（JavaScript、TypeScript、Rust、Go、C/C++、Java、JSON）则按花括号配对折叠，因此单独一行的花括号同样能开启一个区域。位于字符串与注释中的花括号会被跳过——字符串里的一个括号会让后面每一组配对全部错位。折叠只切换行的显示与否，完全不修改文本，因此保存时一定写入完整文件。折叠还能自我修复：标题行已不存在的折叠会直接展开，而不是藏错行。
- **书签** -- 标记行并用键盘在书签之间跳转，也可点击行号区切换。书签锚定在文本上（通过 `QTextCursor`），因此在其上方插入或删除行时会跟着代码移动，而不会跑偏。
- **多光标** -- `Ctrl+Shift+L` 在每个选中行的行尾放一个光标，`Ctrl+Alt+N` 在光标所在词的下一个出现处加一个，`Ctrl+Alt+Shift+Up` / `Down` 在上一行或下一行加一个，`Alt` + 点击则可在任意位置添加或移除。所有光标会随方向键、Home 与 End 一起移动，按住 `Shift` 配合这些键则在每个光标各自扩大选区。输入、Backspace 与 Delete 会在所有光标上生效并算作一次撤销，有选区的位置则以输入内容替换；`Ctrl+Shift+Esc` 或直接点击即可回到单个光标。
- **分屏视图**（`Ctrl+Alt+\`）-- 同一文件的第二个视图，两者共用同一份文档：任一侧的编辑会立刻反映到另一侧，而滚动位置与光标各自独立。
- **缩略图**（`Ctrl+Alt+M`）-- 以长条呈现每一行长度与缩进的整文件概览，并用色带标示当前屏幕上的范围。两侧的标记显示 lint 诊断、git 变更，以及您当前正在查找的内容——搜索框打开时是搜索命中处，否则是光标所在词的其他出现处。点击或拖动即可跳转。大文件采用采样绘制，而非逐行绘制。
- **代码片段** -- 输入触发词后按 Tab 展开，再用 Tab 在占位符之间移动，每个默认值都会自动选中。重复出现的占位符只需输入一次，其余位置会随着输入同步更新。采用常见的 `$1` / `${2:default}` / `$0` 记法，因此已有片段可直接放进 `snippets.json`，并支持各语言专属的片段集。请从 Tab > 编辑代码片段 进行编辑，而不要手动改文件；文件缺失或损坏时会回退到内置的 Python 片段集。
- **测试面板** -- 从停靠面板运行 pytest 并查看结果，失败项排在最前面，摘要作为状态行。选中一条失败会在列表下方的窗格显示其 traceback，覆盖率框则在摘要旁显示总覆盖率（需要被测项目安装 `pytest-cov`）。可运行全部、仅运行选中项，或只重跑上次失败的项；双击一行可在失败的那一行打开该测试。
- **语言服务器支持** -- 非 Python 的文件可通过 stdio 从语言服务器获得补全、hover、转到定义、重命名、格式化、函数签名提示、查找引用、快速修复与文档符号（TypeScript、Rust、Go、C/C++、Lua、JSON 等，可按扩展名配置），Python 则继续使用 jedi。每个需要服务器的标签页共用同一个服务器实例，以「命令 + 项目根目录」为键，而不是每打开一个文件就起一个进程。诊断会与 ruff 的诊断显示在同样的下划线与问题面板中。未安装的服务器只意味着没有补全，不会产生错误。
- **编码与换行符** -- 文件的编码与换行符会在打开时检测、保存时原样写回，因此修改 CRLF 文件的一行不会再重写整个文件。两者都可从 File 菜单更改；更改编码会重新读取未修改的文件，让乱码可以就地修正，且永远不会丢弃未保存的内容。
- **保存时格式化** -- 可选择在保存文件时运行 yapf，并让光标停留在原来的行上。无法解析的代码会原样保留，而不会阻挡保存。
- **缩进参考线与行尾空白** -- 每个缩进层级的竖直参考线，以及行尾多余空白的标示，两者都可从 UI 风格菜单切换。
- **Lint 诊断** -- `ruff` 的检查结果会在编辑器中以下划线标示，并列在问题（Problems）停靠面板中（规则、信息、行号），双击即可跳转。检查的是 **缓冲区** 而非磁盘上的文件，因此未保存的编辑同样会被检查；检查在停止输入后于工作线程执行，被取代的过时结果会被丢弃。若未安装 `ruff` 或运行失败，编辑器只会不显示诊断，而不会报错。
- **Git 变更标记** -- 行号区显示文件与最后一次提交的差异：绿色长条表示新增、橙色表示修改、细红线表示该处有行被删除。用 `F7` / `Shift+F7` 在变更之间跳转，用 `Ctrl+Alt+Z` 将光标所在的变更还原成已提交的内容（一次撤销），也可从右键菜单只暂存那一处变更。`Ctrl+Alt+B` 切换行内 blame，显示最后改动每一行的提交、作者与摘要。Git 菜单可打开整个文件与 `HEAD` 的并排差异，或与暂存区内容的差异——在逐处变更暂存之后，后者正好显示哪些部分真的进了索引。右键菜单同时提供取消整个文件的暂存与提交已暂存的内容。已提交的版本在文件打开时于后台线程读取，比对本身则是纯内存中的 diff，只在停止输入后重新计算，因此编辑永远不必等待 git。不在仓库中或尚未提交的文件就单纯不显示标记。
- **出现处高亮** -- 将光标放在标识符上时，文件中该标识符的其他全词出现处都会被高亮。关键字与单个字符会被忽略，超大文件则跳过扫描，以保持光标移动的即时性。
- **行操作** -- 删除当前行或选中内容（`Ctrl+Shift+D`）、排序选中的行（`Ctrl+Alt+S`）、将选中的行合并成一行（`Ctrl+Shift+J`），以及（在 Text 菜单中）自然排序、删除重复行、删除空行、反转行顺序，或按分隔符（例如 `=`）对齐。每一项都算作一次撤销。
- **复制行**（`Ctrl+D`）-- 有选区时复制选中内容并选中新的副本，没有时则复制整行。
- **大小写转换**（Text 菜单）-- 将选中内容转为大写或小写，并保持选中状态。
- **智能选择** -- 由词 → 行 → 外层缩进块 → 整个文件逐步向外扩大选区（`Ctrl+Alt+Right`），并可逐步收回（`Ctrl+Alt+Left`）。收回只会回溯之前的扩大，手动改变选区则会重置历史。
- **数字加减** -- 将光标处的整数加一或减一（`Ctrl+Alt+Up` / `Ctrl+Alt+Down`），并正确处理负号与位数变化。
- **文件内重命名**（`F2`）-- 将光标所在标识符在整个文件中的每个全词出现处一次改名，算作一次撤销。词边界可保护部分匹配的情况（改 `val` 绝不会动到 `value`）。
- **导航历史** -- 像浏览器一样在光标跳转历史中前进后退（`Alt+Left` / `Alt+Right`）。一次跳转会同时记录来源与目的地，因此「后退」会回到您原本所在的位置。
- **文档大纲** -- 可停靠的树状面板，列出当前文件的类、方法、函数与模块级变量。Python 用 `ast` 解析，不会执行任何代码；其他语言则向其语言服务器询问，因此 TypeScript 或 Rust 文件同样有大纲。双击即可跳到定义。
- **键盘快捷键**（UI 风格 > 键盘快捷键）-- 所有命令的按键集中在一份可编辑的列表中。两个命令不能共用同一组按键，因为发生这种情况时 Qt 两个都不会执行；改动立即生效，而且只有与默认值不同的项会被记录。
- **变量检查器** -- 在程序执行期间检查与调试变量。

### 导航

- **命令面板**（Ctrl+Shift+A）-- 以名称或菜单路径模糊搜索任何菜单命令并直接执行，不必在菜单中翻找。结果按词边界、连续字符与前缀排序，每一行也会显示该命令自己的快捷键。
- **快速打开／转到文件**（Ctrl+P）-- 以文件名 *或* 文件夹路径模糊搜索项目树。索引在后台线程建立，并跳过版本控制、缓存、虚拟环境与构建目录以及二进制文件类型。开头输入 `>` 可将同一个选择器切换成命令模式。
- **转到符号**（Ctrl+Shift+O）-- 跳到当前 Python 文件中的任何类、函数、方法或模块级变量。符号用标准库的 `ast` 模块解析，因此绝不会执行用户代码；无法解析的文件在您输入时只会没有符号，而不会报错。
- **TODO 面板**（Tab > 工具，或作为停靠面板）-- 扫描项目中的 `TODO`、`FIXME`、`HACK`、`XXX`、`BUG`、`NOTE` 与 `OPTIMIZE` 注释，涵盖 Python、C 系、HTML、SQL 等注释风格。可按标签筛选，双击一行即可在该行打开文件。标签只有出现在注释符之后才会被报告，因此普通字符串不会被误判。

### 程序执行与调试

- **运行 Python 脚本**（F5）-- 执行当前文件并实时流式输出。
- **调试模式**（F9）-- 启动 Python 调试器进行逐步调试：`Ctrl+F9` 切换断点、`Ctrl+F5` 继续执行、`F10` / `F11` / `Shift+F11` 分别为单步跳过／进入／跳出。断点锚定在文本上，因此会跟着代码移动。
- **Shell 命令** -- 在编辑器内直接执行任意 Shell/终端命令。
- **虚拟环境检测** -- 自动检测并激活 Python 虚拟环境。
- **进程管理** -- 停止单个或所有运行中的进程。
- **错误高亮** -- 错误信息在输出面板中以红色显示。

### 代码质量与格式化

- **YAPF Python 格式化**（Ctrl+Shift+Y）-- 使用 Google 风格自动格式化 Python 代码。
- **PEP8 检查**（Ctrl+Alt+P）-- 验证代码是否符合 PEP8 风格指南。
- **Ruff 静态分析** -- 在后台线程中执行快速且全面的 Python 静态分析。
- **JSON 重新格式化**（Ctrl+J）-- 美化打印并验证 JSON 内容。
- **删除行尾空白**（Text 菜单）-- 去除每一行结尾的空白，算作一次撤销，并保留光标位置。
- **转换缩进**（Text 菜单）-- 在 Tab 与空格之间转换前导缩进（按您设置的缩进大小）。只处理前导空白，因此字符串内的 Tab 与空格永远不会被改动。
- **可配置的缩进宽度** -- Tab 缩进、取消缩进与 Enter 自动缩进都遵循设置的缩进大小（`Text > Indent Size`），而打开文件时也会从文件本身的内容自动检测缩进宽度。
- **文本转换**（Text 菜单）-- 大小写转换（大写／小写／互换／标题式）、命名风格转换（`snake_case` / `camelCase` / `PascalCase` / `kebab-case`）、进制转换（十六进制／十进制／二进制），以及编码解码工具（Base64、URL、HTML 实体、JSON 字符串转义）。解码失败时原文保持不变。
- **统计**（Text 菜单）-- 整个文档或当前选区的行数、词数与字符数。

### 文件操作

- **创建、打开、保存**文件，使用标准快捷键（Ctrl+N、Ctrl+O、Ctrl+S）。
- **打开文件夹**（Ctrl+K）-- 浏览项目目录结构。
- **自动保存** -- 自动定期保存文件，防止数据丢失。
- **会话恢复** -- 重新打开上次关闭时所有打开的文件，而不只是最后一个。不存在、重复与已打开的文件会被跳过，列表有上限，损坏或手工改过的配置文件也绝不会挡住启动。可在 `.jeditor/user_setting.json` 中将 `restore_session` 设为 `false` 禁用。
- **多编码支持** -- 无缝处理 UTF-8、GBK、Latin-1 及其他编码，具备自动检测功能。
- **最近打开的文件** -- 快速访问之前打开的文件。

### Git 集成

JEDITOR 内置完整的 Git 客户端：

- **分支管理** -- 从工具栏列出、切换与检出分支。
- **提交历史** -- 以表格形式查看提交的元数据（作者、日期、信息）。
- **并排差异查看器** -- 具有行号的彩色高亮代码比较。
- **多文件差异** -- 比较多个文件间的变更。
- **暂存区操作** -- 暂存或取消暂存单个文件的变更，也可从编辑器的行号区逐处变更暂存。
- **贮藏（Stash）** -- 把当前的变更先收起来、列出贮藏的内容，并可取回其中一条。
- **冲突解决** -- 列出合并后仍处于冲突的文件，并可选择保留其中一方来解决。
- **审计日志** -- 记录所有 Git 操作，方便追踪与合规。

### AI 助手

集成 OpenAI 与 LangChain 的 AI 助手：

- **GPT-3.5 / GPT-4 支持** -- 连接 OpenAI 的语言模型。
- **交互式聊天面板** -- 编辑器内的对话式 AI 面板。
- **可配置模型** -- 设置自定义 API 密钥、端点、模型名称与系统提示词。
- **异步消息** -- 使用消息队列实现非阻塞 AI 交互。

### 控制台与 REPL

- **交互式控制台** -- 执行 Shell 命令并支持历史导航（上/下方向键）。
- **Jupyter/IPython 控制台** -- 内置进程 IPython 内核，支持丰富输出。
- **多 Shell 支持** -- 支持 cmd、PowerShell、bash 与 sh。
- **工作目录控制** -- 独立设置执行目录。

### 内置浏览器

- **内嵌网页浏览器** -- 不离开编辑器即可浏览网页。
- **URL 导航** -- 具有集成搜索功能的地址栏。
- **页面内搜索**（Ctrl+F）-- 在网页中搜索文字。
- **标准导航** -- 后退、前进、刷新与停止控制。

### 插件系统

JEDITOR 支持模块化的插件架构，提供四种插件类型：

| 类型 | 用途 |
|---|---|
| 编程语言 | 为新语言添加语法高亮 |
| 自然语言 | 为新语系添加 UI 翻译 |
| 运行配置 | 定义自定义执行环境 |
| 插件元数据 | 提供插件版本与作者信息 |

插件会自动从 `jeditor_plugins/` 目录中发现并加载。详见[插件开发](#插件开发)章节。

### 主题与自定义

- **深色/浅色主题** -- Qt Material 主题，琥珀色配色方案。编辑器本身的颜色会跟随窗口样式，您自己挑过的颜色则不会被覆盖。
- **字体自定义** -- 更改编辑器与 UI 的字体族与大小。
- **可停靠面板** -- 通过停靠/取消停靠面板重新排列 UI 布局。
- **系统托盘** -- 将编辑器最小化至系统托盘。
- **工具栏** -- JetBrains 风格的快速操作按钮。

### 多语言界面

- **英文**、**繁体中文**、**简体中文** 与 **日本語** -- 四种都是完整的。简体中文以中国大陆的用词直接撰写，而非由繁体转换——文件/檔案、文件夹/資料夾、程序/程式 这些词在两地并不相同。
- **首次启动跟随系统** -- 语言取自系统的区域设置，而不是一律默认英文；中文按书写系统判断：`zh-Hant` 以及台湾、香港、澳门地区使用繁体，其余使用简体。检测到的结果会被记录下来，之后就单纯是您所选的语言。
- **无需重启即可切换** -- 选择语言后，菜单、工具栏、面板、标签页与状态栏会立刻换成新语言。标签页上的文件名与分支名保持不变。
- **回退英文** -- 某个语言尚未翻译的字符串会显示英文原文，而不是空白标签，因此一种语言可以在尚未完成时就先加入。
- **可扩展** -- 通过插件系统添加更多语言。韩文、西班牙文、法文、德文、俄文与葡萄牙文的区域判断规则都已就绪，各自只差一份词典。

---

## 键盘快捷键

| 快捷键 | 操作 |
|---|---|
| `Ctrl+N` | 新建文件 |
| `Ctrl+O` | 打开文件 |
| `Ctrl+K` | 打开文件夹 |
| `Ctrl+S` | 保存文件 |
| `Ctrl+Shift+S` | 保存所有已修改的标签页 |
| `Ctrl+Shift+A` | 命令面板 |
| `Ctrl+P` | 快速打开（转到文件） |
| `Ctrl+Shift+O` | 转到符号 |
| `Ctrl+Shift+[` | 切换光标所在的折叠 |
| `Ctrl+Alt+[` | 全部折叠 |
| `Ctrl+Alt+]` | 全部展开 |
| `Ctrl+Alt+K` | 切换书签 |
| `Ctrl+Alt+L` | 下一个书签 |
| `Ctrl+Alt+J` | 上一个书签 |
| `Alt+Left` | 后退 |
| `Alt+Right` | 前进 |
| `Ctrl+Shift+D` | 删除当前行／选中内容 |
| `Ctrl+Alt+S` | 排序选中的行 |
| `Ctrl+Shift+J` | 合并选中的行 |
| `Ctrl+Alt+Right` | 扩大选区 |
| `Ctrl+Alt+Left` | 收回选区 |
| `Ctrl+Alt+Up` | 光标处的数字加一 |
| `Ctrl+Alt+Down` | 光标处的数字减一 |
| `F2` | 文件内重命名所有出现处 |
| `Ctrl+Shift+L` | 在每个选中行的行尾放一个光标 |
| `Ctrl+Alt+N` | 在下一个出现处加一个光标 |
| `Ctrl+Alt+Shift+Up` / `Ctrl+Alt+Shift+Down` | 在上一行／下一行加一个光标 |
| `Ctrl+Shift+Esc` | 回到单个光标 |
| `Ctrl+Shift+R` | 开始／结束录制宏 |
| `Ctrl+Shift+G` | 回放宏 |
| `Ctrl+Alt+E` | 最近位置 |
| `Ctrl+Alt+\` | 切换分屏视图 |
| `Ctrl+Alt+M` | 切换缩略图 |
| `F7` / `Shift+F7` | 下一处／上一处变更 |
| `Ctrl+Alt+Z` | 还原光标所在的变更 |
| `Ctrl+Alt+B` | 切换行内 blame |
| `Ctrl+J` | 重新格式化 JSON |
| `Ctrl+Shift+Y` | YAPF Python 格式化 |
| `Ctrl+Alt+P` | PEP8 格式检查 |
| `Ctrl+F` | 搜索文字（编辑器、浏览器） |
| `Ctrl+Shift+F` | 跨文件搜索 |
| `Alt+W` | 自动换行 |
| `Ctrl+Shift+P` | 用 pip 安装包 |
| `Ctrl+Shift+U` | 升级与安装包 |
| `Ctrl+Shift+V` | 切换 Python 解释器 |
| `Ctrl+H` | 搜索与替换 |
| `Ctrl+G` | 跳到指定行 |
| `F5` | 运行程序 |
| `F9` | 调试 |
| `Shift+F5` | 停止程序 |
| `Ctrl+F9` | 切换断点 |
| `Ctrl+F5` | 调试器：继续执行 |
| `F10` / `F11` / `Shift+F11` | 调试器：单步跳过／进入／跳出 |
| `上/下方向键` | 命令历史（控制台） |

上表所有快捷键都可从 **UI 风格 > 键盘快捷键** 重新指定。以下按键由编辑区本身处理，
因此是固定的：

| 快捷键 | 操作 |
|---|---|
| `Ctrl+D` | 复制行／选中内容 |
| `Ctrl+/` | 切换注释 |
| `Alt+Up` / `Alt+Down` | 将该行上移／下移 |
| `Ctrl+B` | 跳到光标处符号的定义 |
| `Ctrl+Shift+\` | 跳到匹配的括号 |
| `Ctrl++` / `Ctrl+-` | 放大／缩小编辑器字体 |
| `Tab` / `Shift+Tab` | 将该行或选中内容缩进／取消缩进 |

---

## 项目架构

```
je_editor/
├── pyside_ui/                    # GUI 组件（PySide6）
│   ├── browser/                  # 内嵌网页浏览器
│   ├── code/                     # 核心代码编辑
│   │   ├── auto_save/            # 自动保存
│   │   ├── bookmark/             # 书签管理（以 QTextCursor 锚定）
│   │   ├── breakpoint/           # 断点标记
│   │   ├── code_format/          # YAPF 与 PEP8 格式化
│   │   ├── code_process/         # 程序执行（ExecManager）
│   │   ├── folding/              # 代码折叠管理
│   │   ├── git_diff/             # 行号区变更标记与行内 blame
│   │   ├── lint/                 # 单个编辑器的 lint 诊断
│   │   ├── lsp/                  # 语言服务器客户端与共享连接
│   │   ├── minimap/              # 缩略图组件
│   │   ├── multi_cursor/         # 额外光标管理
│   │   ├── snippets/             # 代码片段展开
│   │   ├── shell_process/        # Shell 执行（ShellManager）
│   │   ├── syntax/               # 语法高亮引擎
│   │   ├── plaintext_code_edit/  # 纯文本编辑器组件
│   │   ├── textedit_code_result/ # 输出显示组件
│   │   └── variable_inspector/   # 变量调试
│   ├── dialog/                   # 对话框窗口
│   │   ├── ai_dialog/            # AI 配置对话框
│   │   ├── file_dialog/          # 文件操作对话框
│   │   └── search_ui/            # 搜索与替换对话框
│   ├── git_ui/                   # Git 界面
│   │   ├── code_diff_compare/    # 并排差异查看器
│   │   └── git_client/           # 分支与提交 UI
│   └── main_ui/                  # 主编辑器窗口
│       ├── ai_widget/            # AI 聊天面板
│       ├── command_palette/      # 命令面板、快速打开、转到符号
│       ├── console_widget/       # 交互式控制台
│       ├── dock/                 # 可停靠组件管理
│       ├── editor/               # 标签页式编辑器
│       ├── ipython_widget/       # Jupyter/IPython 控制台
│       ├── menu/                 # 菜单栏系统
│       ├── outline_panel/        # 文档大纲（符号树）
│       ├── plugin_browser/       # 插件管理 UI
│       ├── problems_panel/       # lint 诊断面板
│       ├── retranslate.py        # 语言变更时重新标注整个界面
│       ├── save_settings/        # 设置持久化、快捷键与配色
│       ├── system_tray/          # 系统托盘集成
│       ├── test_panel/           # pytest 结果、traceback 与覆盖率
│       ├── todo_panel/           # TODO/FIXME 任务面板
│       └── toolbar/              # 工具栏操作
├── code_scan/                    # 代码扫描
│   ├── ruff_thread.py            # Ruff 静态分析（多线程）
│   ├── watchdog_implement.py     # 文件系统监控
│   └── watchdog_thread.py        # Watchdog 多线程
├── git_client/                   # Git 后端
│   ├── git_action.py             # Git 操作（含审计日志）
│   ├── git_cli.py                # Git CLI 包装器
│   └── commit_graph.py           # 提交图形可视化
├── plugins/                      # 插件系统
│   └── plugin_loader.py          # 动态插件加载
├── utils/                        # 工具程序
│   ├── align/                    # 按分隔符对齐行（不依赖 Qt）
│   ├── bookmark/                 # 书签导航逻辑（不依赖 Qt）
│   ├── browser/                  # 内嵌 Chromium 标志（不依赖 Qt）
│   ├── case_convert/             # 命名风格转换（不依赖 Qt）
│   ├── code_folding/             # 折叠区域：按缩进与按花括号（不依赖 Qt）
│   ├── command_palette/          # 模糊匹配与排序（不依赖 Qt）
│   ├── debugger/                 # 组装 pdb 命令（不依赖 Qt）
│   ├── encode_decode/            # Base64/URL/HTML/JSON 转换（不依赖 Qt）
│   ├── encodings/                # 编码检测
│   ├── exception/                # 自定义异常
│   ├── file/                     # 文件 I/O（打开/保存）
│   ├── file_diff/                # 行状态、hunk 与 unified diff（不依赖 Qt）
│   ├── file_scan/                # 共享忽略规则、文件索引、TODO 扫描
│   ├── format_code/              # yapf 格式化（不依赖 Qt）
│   ├── indentation/              # Tab/空格转换与缩进检测（不依赖 Qt）
│   ├── json_format/              # JSON 格式化
│   ├── line_ops/                 # 行操作转换（不依赖 Qt）
│   ├── lint/                     # Ruff 诊断解析（不依赖 Qt）
│   ├── logging/                  # 日志设置
│   ├── lsp/                      # LSP 分包、协议与服务器注册表（不依赖 Qt）
│   ├── macro/                    # 按键宏录制（不依赖 Qt）
│   ├── minimap/                  # 缩略图几何与采样（不依赖 Qt）
│   ├── multi_cursor/             # 额外光标位置与编辑位移（不依赖 Qt）
│   ├── multi_language/           # 国际化：英文、繁体与简体中文、日文、
│   │                             #   区域匹配、实时重新标注
│   ├── navigation/               # 光标跳转历史（不依赖 Qt）
│   ├── number_ops/               # 光标处数字加减（不依赖 Qt）
│   ├── occurrence/               # 词出现处查找与全词重命名（不依赖 Qt）
│   ├── redirect_manager/         # 输出流重定向
│   ├── selection/                # 智能选区与包围（不依赖 Qt）
│   ├── session/                  # 多文件会话恢复（不依赖 Qt）
│   ├── shortcuts/                # 键盘快捷键表（不依赖 Qt）
│   ├── snippets/                 # 片段展开与 tab stop（不依赖 Qt）
│   ├── status/                   # 状态栏文本（不依赖 Qt）
│   ├── symbols/                  # 符号提取：Python 用 ast，其余问服务器
│   ├── syntax/                   # 各语言的高亮规则（不依赖 Qt）
│   ├── test_runner/              # pytest 输出解析（不依赖 Qt）
│   ├── text_cleanup/             # 行尾空白／换行清理（不依赖 Qt）
│   ├── text_stats/               # 行／词／字符统计（不依赖 Qt）
│   ├── theme/                    # 深色与浅色的编辑器配色（不依赖 Qt）
│   └── venv_check/               # 虚拟环境检测
├── __init__.py                   # 公共 API
├── __main__.py                   # CLI 入口点
└── start_editor.py               # 应用程序启动器
```

---

## 插件开发

在工作目录中创建 `jeditor_plugins/` 目录来放置插件。JEDITOR 支持三种插件类型：

### 1. 编程语言插件

为新语言添加语法高亮：

```python
from je_editor.plugins import register_programming_language

register_programming_language(
    suffix=".rs",
    syntax_words={"keywords": ["fn", "let", "mut", "struct", "impl", "enum"]},
    syntax_rules={"keyword_color": "#FF6600"}
)
```

### 2. 自然语言插件

添加 UI 翻译：

```python
from je_editor.plugins import register_natural_language

register_natural_language(
    language_key="ja",
    display_name="Japanese",
    word_dict={"file": "ファイル", "edit": "編集", "run": "実行"}
)
```

### 3. 运行配置插件

定义自定义执行环境：

```python
from je_editor.plugins import register_plugin_run_config

register_plugin_run_config(
    name="Node.js",
    run_config={"command": "node", "suffix": ".js"}
)
```

完整指南请参阅 `PLUGIN_GUIDE.md`。

---

## 配置文件

JEDITOR 将用户设置存储在 `.jeditor/` 目录中：

| 文件 | 内容 |
|---|---|
| `user_setting.json` | 通用偏好设置（字体、主题、语言、最近打开的文件、打开的标签页、重新指定过的快捷键） |
| `user_color_setting.json` | 编辑器与输出的配色，含语法高亮 |
| `ai_config.json` | AI 助手设置——启动时读取、从不写入，需自行创建 |

---

## 文档

完整文档请参阅：
**[https://je-editor.readthedocs.io/en/latest/](https://je-editor.readthedocs.io/en/latest/)**

---

## 参与贡献

欢迎贡献！请在 [GitHub](https://github.com/JE-Chen/je_editor) 上提交 Issue 与 Pull Request。

---

## 许可证

本项目采用 **MIT 许可证**。详见 [LICENSE](../LICENSE)。

Copyright (c) 2021 ~ Now JE-Chen
