Git Integration
================

JEditor includes a full-featured Git client with a graphical interface, powered by
`GitPython <https://gitpython.readthedocs.io/>`_. All Git operations are performed
directly within the editor — no external tools required.

Opening a Repository
---------------------

Open a Git repository from the Git panel. JEditor will:

- Detect the repository root automatically
- Display the current branch in the toolbar
- Load the commit history
- Restore the last opened repository on next launch

Branch Management
------------------

Manage branches directly from the editor:

- **List all branches** — View local and remote branches in the branch tree
- **Switch branches** — Checkout any branch from the dropdown in the toolbar
- **Branch selector** — Quick branch switching via the toolbar dropdown

Commit History
---------------

View the full commit history in a sortable table:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Description
   * - SHA
     - The commit hash (abbreviated)
   * - Author
     - The commit author
   * - Date
     - The commit date and time
   * - Message
     - The commit message

**Commit Graph:**

JEditor can display a visual commit graph showing branch relationships and merge history,
helping you understand the project's development timeline.

Diff Viewer
------------

JEditor provides a powerful side-by-side diff viewer:

- **Color-highlighted changes** — Added, removed, and modified lines are color-coded
- **Line numbers** — Both old and new versions show line numbers
- **Multi-file diff** — View changes across multiple files in a single session
- **Read-only display** — Diff view is read-only to prevent accidental edits

Change Markers in the Editor
----------------------------

The editor's gutter shows how the open file differs from its last commit:

- A **green** bar for added lines
- An **orange** bar for modified lines
- A thin **red** line where lines were deleted

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``F7`` / ``Shift+F7``
     - Jump to the next / previous change
   * - ``Ctrl+Alt+Z``
     - Revert the change under the caret back to its committed form, as one undo step
   * - ``Ctrl+Alt+B``
     - Toggle inline blame — the commit, author and summary that last touched each line

The right-click menu stages just the change under the caret, unstages the whole file, or
commits what is currently staged. The Git menu opens a side-by-side diff of the file
against ``HEAD``, or against what is staged — after staging change by change, that second
one shows which parts actually went into the index.

The committed version is read on a background thread when the file opens, and the
comparison itself is a pure in-memory diff recomputed only after typing pauses, so
editing never waits on Git. Files outside a repository, or not yet committed, simply show
no markers.

Staging & Committing
---------------------

Perform full Git workflows within the editor:

1. **Stage changes** — Select individual files to stage, or stage a single change from
   the editor's gutter
2. **Unstage changes** — Remove files from the staging area
3. **Write commit message** — Enter a descriptive commit message
4. **Commit** — Create a new commit with the staged changes

Stash
------

Set the current changes aside without committing them:

- **Stash** — Save the working tree's changes, optionally with a message
- **List** — See what is currently stashed
- **Pop** — Take a stash back and remove it from the list

Conflict Resolution
--------------------

After a merge leaves files in conflict, JEditor lists them and settles one by keeping
either side — **ours** or **theirs**. The chosen content is written to the file and
staged, which clears the conflict. A file that is not actually in conflict is refused
rather than silently staged.

Remote Operations
------------------

Interact with remote repositories:

- **Push** — Push local commits to the remote repository
- **Pull** — Pull the latest changes from the remote
- **Remote management** — Configure remote repository URLs
- **Tracking branch detection** — Automatically detects upstream branches

Audit Logging
--------------

All Git operations are logged to ``audit.log`` for traceability:

- **Timestamp** — When the operation occurred
- **Action** — What Git command was executed
- **Status** — Success or failure
- **Error details** — If the operation failed, the error message is logged

The audit log is non-intrusive and never interrupts the UI, even if logging fails.
