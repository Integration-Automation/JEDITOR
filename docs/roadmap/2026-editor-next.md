# JEditor Next-Generation Editor Roadmap

> Status: planning / draft
> Target base: `dev`
> Scope: the next architectural generation of JEditor, covering the 11 capabilities below.
>
> This document is deliberately a roadmap, not an implementation PR. Each milestone should land as a
> separate, reviewable PR with tests and documentation. The order below is dependency-driven.

## Implementation status

| Milestone | Status | Record |
| --- | --- | --- |
| M0 — Foundation and compatibility boundary | Implemented: `je_editor/core/` | `docs/updates/2026-10.md`, U-20261008-01 |
| M2 — diagnostics half | Implemented: one diagnostic model, severity and source filters | U-20261008-04 |
| M2 — Tree-sitter half | Implemented: `je_editor/adapters/syntax/` colours Python, JavaScript and JSON; folding, outline and selection still use their own analysers | U-20261008-08, `PROGRESS.md` |
| M3 — Workspace + multi-root | Implemented; per-root environments and Git are left over | U-20261008-07, `PROGRESS.md` |
| M5 — AI provider abstraction + Anthropic | Implemented: `je_editor/adapters/ai/` | U-20261008-05 |
| M4 — Debugger migration to DAP | Service implemented and tested against debugpy: `je_editor/adapters/debug/`; the debugger UI still drives pdb | U-20261008-11, `PROGRESS.md` |
| M1, M6, M7, M8 | Not started | `PROGRESS.md` |

M0 defines the service layer and proves it runs without Qt. What it left to later milestones:

- the editor window consumes the services one area at a time: diagnostics, the AI chat panel,
  the workspace and syntax highlighting do so far;
- debugging, task execution and remote sessions are interfaces with no implementation yet (M4
  and M6 supply them), and the request-and-reply calls of a language service (completion, hover
  and the rest) take their shape with Tree-sitter in M2;
- `import je_editor.core` still runs `je_editor/__init__.py`, which imports Qt (M7).

## Goals

Turn JEditor from a feature-rich desktop editor into a reusable editor platform:

1. keep the current PySide6 desktop application working while the internals are migrated;
2. make workspace, document, diagnostics, debug, terminal and remote execution services independent of
   the main window;
3. make the editor embeddable as a normal Qt component without requiring the full IDE shell;
4. make syntax parsing, language-server diagnostics and debugging first-class services;
5. keep provider-specific integrations (LLMs, remote transports, language servers) behind small
   interfaces.

## Current state

JEditor already provides several foundations:

- PySide6 desktop UI and an `EditorMain(extend=True)` embedding mode;
- a public `EditorWidget` / `FullEditorWidget` API and `EDITOR_EXTEND_TAB`;
- configurable shortcut registry with conflict detection;
- English / Traditional Chinese / Simplified Chinese / Japanese dictionaries and plugin language
  registration;
- LSP sessions and diagnostics, including a Problems panel;
- a basic debugger based on pdb/process control;
- LangChain + OpenAI AI chat;
- project file indexing and a single project-root-oriented editor workflow;
- pluggable syntax highlighting;
- Sphinx documentation and API documentation.

The roadmap therefore focuses on **consolidation and architectural boundaries**, not replacing working
features merely for the sake of replacement.

## Architecture direction

The target dependency direction is:

```
Qt Application / IDE Shell
        |
        +-- Workspace UI
        +-- Editor UI
        +-- Problems / Debug / Terminal UI
        +-- AI UI
        |
        v
JEditor Core Services
        |
        +-- Workspace / Project Model
        +-- Document Model
        +-- Language Service (Tree-sitter + LSP)
        +-- Diagnostics Model
        +-- Debug Adapter Protocol
        +-- Task / Process Service
        +-- Remote Session Service
        +-- AI Provider Interface
        |
        v
Adapters / Providers
        |
        +-- local filesystem / process
        +-- SSH / remote transport
        +-- LSP servers
        +-- DAP servers
        +-- OpenAI / Anthropic / future providers
```

The Qt widgets should consume these services instead of owning their protocols and process lifetime.
Existing APIs remain compatibility shims during migration.

---

## Milestone plan

### M0 — Foundation and compatibility boundary

**Purpose:** create the seams required by the rest of the roadmap without changing the visible product.

- Define stable interfaces for:
  - workspace and project roots;
  - documents / buffers;
  - diagnostics;
  - language services;
  - debug sessions;
  - process / task execution;
  - remote sessions;
  - AI providers.
- Move protocol/data objects into pure-Python modules where possible.
- Keep the current `EditorMain` and `EditorWidget` as compatibility facades.
- Add architecture tests that prevent core services from importing Qt widgets.
- Preserve current public exports and `extend=True` behavior.

**Exit criteria:** the new service layer can be instantiated in a non-GUI test and the existing editor
still starts unchanged.

---

### M1 — UI redesign + shortcut system + i18n completion

**Scope**

1. UI 重新設計
2. 可以自訂快捷鍵
3. 補齊其他語系 dict

**UI direction**

- Introduce a consistent shell layout: activity/navigation area, editor area, secondary panel and
  bottom panel.
- Separate layout state from feature state so panels can be rearranged without reconstructing the
  editor.
- Use semantic commands rather than widget-specific actions as the UI contract.
- Keep the current qt-material theming compatible during the transition.

**Shortcuts**

- Make every user-facing command register through the command/shortcut registry.
- Support multi-stroke sequences where Qt permits them.
- Detect conflicts before applying settings.
- Persist only overrides from defaults.
- Expose a command identifier independent from translated labels.

**i18n**

- Keep English as the canonical key set.
- Add a parity checker that verifies every dictionary has the same keys and placeholders.
- Prefer English fallback for incomplete translations.
- Make locale loading data-driven rather than hard-coded.
- Do not translate language names or other identifiers that must remain recognizable.

**Exit criteria:** changing language or shortcuts does not rebuild/destroy host-owned widgets; every
registered command has a stable ID; dictionary parity is CI-enforced.

---

### M2 — Tree-sitter syntax engine + LSP diagnostics model

**Scope**

4. 語法高亮改用 Tree-sitter
5. Problem 面板整合語言伺服器診斷的嚴重度過濾

**Tree-sitter**

- Introduce a parser service independent from Qt.
- Parse incrementally from the document buffer.
- Use Tree-sitter queries for syntax categories and structural regions.
- Keep the existing highlighter behind an adapter during migration.
- Reuse the parse tree later for folding, symbols, selection expansion and structural navigation.

**Diagnostics**

Normalize diagnostics from ruff and LSP into one model:

- source;
- severity: Error / Warning / Information / Hint;
- code;
- message;
- URI/path;
- range;
- related information;
- optional quick-fix/edit metadata.

Problems panel filters should support:

- All;
- Errors;
- Warnings;
- Information;
- Hints;
- source/provider.

**Exit criteria:** LSP and ruff findings render through the same diagnostic model; severity filters
are deterministic; Tree-sitter can parse supported languages without the widget layer knowing parser
details.

---

### M3 — Workspace + multi-root projects

**Scope**

6. 工作區與多根專案

Introduce a first-class `Workspace` model:

- one workspace can contain zero or more project roots;
- each root has its own URI/path, language/tool configuration and environment;
- documents resolve against the owning root;
- LSP sessions are keyed by server + root/workspace context;
- search, indexing, TODO scanning, Git and diagnostics become workspace-aware;
- session restore stores workspace identity and open documents.

**Important design rule:** a single-root project remains a valid workspace and should behave almost
exactly as it does today.

**Exit criteria:** opening two unrelated roots in one window works; language servers receive the
correct root; project-wide search and Problems aggregate both roots without path collisions.

---

### M4 — Debugger migration to DAP

**Scope**

7. 除錯器補齊到 DAP

Replace the current debugger-specific control path with a DAP client/service.

Required baseline:

- initialize / launch / attach;
- breakpoints and conditional breakpoints;
- stack frames;
- scopes / variables;
- continue / pause / terminate;
- step over / into / out;
- exception information;
- source locations;
- evaluate expression;
- threads.

The existing pdb workflow should become a DAP adapter where practical rather than a second debugger
architecture.

**Exit criteria:** the debugger UI depends on the DAP service, not on pdb implementation details; at
least one local adapter is covered by integration tests; the public debug API can later host remote
adapters.

---

### M5 — AI provider abstraction + Anthropic backend

**Scope**

8. AI 助理加 Anthropic 後端

Refactor the existing LangChain/OpenAI implementation into a provider-neutral interface.

Suggested abstraction:

- model metadata;
- streaming response;
- cancellation;
- system prompt;
- conversation history;
- tool/context attachments;
- token/error reporting.

Providers:

- OpenAI — existing behavior preserved;
- Anthropic — first new backend;
- future providers should not require changes to the chat widget.

Configuration should be provider-scoped rather than OpenAI-specific.

**Exit criteria:** the same chat UI can switch between OpenAI and Anthropic without provider-specific
branches in the UI.

---

### M6 — Remote development, moved down into JEditor

**Scope**

9. 遠端開發 (下沉到 JEditor)

Remote development should be a **core service**, not a feature owned by the desktop shell.

Introduce:

- remote session lifecycle;
- filesystem abstraction;
- process/task execution;
- port forwarding abstraction;
- environment/interpreter discovery;
- remote LSP process launch;
- remote DAP process launch;
- reconnect/disconnect state.

Initial transport can be SSH, but the service API must not expose SSH-specific concepts.

The workspace model from M3 becomes the integration point: a root may be local or remote.

**Exit criteria:** an editor document can be opened from a remote workspace and the same LSP/debug/task
APIs work without the UI knowing whether the process is local or remote.

---

### M7 — Embeddable editor component

**Scope**

10. 發展成可嵌入的編輯器元件

Split the product into two explicit layers:

**JEditor Core**

- document/buffer;
- commands;
- workspace;
- language services;
- diagnostics;
- debug;
- task/process;
- remote;
- AI provider interfaces.

**JEditor Widgets**

- editor view;
- tabs;
- minimap;
- gutter;
- diagnostics presentation;
- completion UI;
- navigation UI.

**JEditor IDE**

- menus;
- toolbar;
- terminal;
- Git;
- browser;
- project explorer;
- settings;
- system tray.

Target usage:

```python
from je_editor.widgets import JEditor

editor = JEditor(parent)
editor.open_workspace(...)
```

The exact API can be finalized during implementation, but the goal is a small constructor surface and
no implicit application-wide side effects.

Embedding requirements:

- no forced `QApplication`;
- no root logger reconfiguration;
- no automatic browser/tray/system integration;
- configurable persistence location;
- explicit lifecycle / shutdown;
- host-controlled theme and translation hooks.

**Exit criteria:** a small third-party PySide6 application can embed the editor widget without
creating the JEditor IDE shell.

---

### M8 — Tutorial and architecture documentation

**Scope**

11. 教學文件：怎麼用 Qt 跟這專案寫一個編輯器

Create a tutorial series rather than one large page:

1. JEditor architecture in 10 minutes;
2. create a minimal PySide6 window;
3. embed the JEditor component;
4. open files and manage documents;
5. add commands and shortcuts;
6. add a language server;
7. consume diagnostics;
8. add a DAP debugger;
9. create a workspace / multi-root project;
10. add a remote transport;
11. add an AI provider;
12. package a custom editor application.

Every tutorial should be executable from a clean environment and use public APIs only.

---

## Dependency graph

```
M0 Foundation
 ├── M1 UI / Commands / i18n
 │    └── M7 Embeddable component
 ├── M2 Tree-sitter / Diagnostics
 │    ├── M3 Workspace / Multi-root
 │    │    ├── M4 DAP
 │    │    └── M6 Remote development
 │    └── M7 Embeddable component
 └── M5 AI providers

M3 Workspace
 ├── M4 DAP
 └── M6 Remote development

M7 Embeddable component
 └── M8 Tutorials
```

Recommended implementation order:

**M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8**

M5 can run in parallel after M0 because it has little dependency on workspace or parser work.

## Cross-cutting requirements

Every implementation PR should include:

- unit tests for pure service logic;
- Qt tests for widget behavior;
- at least one regression test for the old API path when migrating an existing feature;
- documentation updates for public APIs;
- no UI-thread blocking for filesystem, Git, LSP, DAP, AI or remote I/O;
- explicit lifecycle tests for threads, processes and remote sessions;
- compatibility notes when public APIs change.

For structural changes, update `architecture.md` and `architecture_explore.md` in the same PR.

## Non-goals

This roadmap does **not** mean:

- rewriting the whole editor in another toolkit;
- replacing PySide6;
- removing the plugin system;
- forcing every feature into the core package;
- requiring every language to ship a Tree-sitter grammar;
- requiring every AI provider to use LangChain internally;
- making the standalone IDE and embeddable component share the same UI shell.

The key objective is to make the existing feature set composable, testable and reusable while keeping
JEditor usable as a desktop application throughout the migration.

## Definition of done for the roadmap

The roadmap is complete when:

- JEditor can be used as a standalone IDE and as an embedded Qt component;
- a workspace can contain multiple local or remote roots;
- Tree-sitter provides the structural syntax layer;
- LSP diagnostics share one severity-aware Problems model;
- debugging is exposed through DAP;
- AI providers include OpenAI and Anthropic behind one interface;
- shortcuts, translations and commands are data-driven and testable;
- remote development uses the same workspace/language/debug/task abstractions as local development;
- the public APIs are documented with runnable Qt examples.
