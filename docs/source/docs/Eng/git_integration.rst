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

Staging & Committing
---------------------

Perform full Git workflows within the editor:

1. **Stage changes** — Select individual files to stage
2. **Unstage changes** — Remove files from the staging area
3. **Write commit message** — Enter a descriptive commit message
4. **Commit** — Create a new commit with the staged changes

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
