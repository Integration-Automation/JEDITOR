"""
組出要送給 pdb 的指令
Build the commands to send to pdb.

編輯器的除錯器就是 ``python -m pdb``，它從標準輸入讀指令。中斷點與逐步執行因此
只是「送出正確的指令字串」，這裡負責組字串，實際傳送交給既有的除錯輸入。
The editor's debugger is ``python -m pdb``, which reads commands from standard
input. Breakpoints and stepping are therefore a matter of sending the right
command, and this module builds those strings; sending them is the existing
debugger input's job.

純邏輯：不啟動任何程序。
Pure logic: it starts no process.
"""
from __future__ import annotations

from pathlib import Path

# pdb 的逐步執行指令 / pdb's stepping commands
STEP_INTO = "step"
STEP_OVER = "next"
STEP_OUT = "return"
CONTINUE = "continue"
QUIT = "quit"

# 逐步動作對應的指令 / The command for each stepping action
STEP_COMMANDS = {
    "into": STEP_INTO,
    "over": STEP_OVER,
    "out": STEP_OUT,
    "continue": CONTINUE,
    "quit": QUIT,
}


def breakpoint_command(file_path: str | Path, line: int) -> str:
    """
    組出設定一個中斷點的指令
    Build the command that sets one breakpoint.

    pdb 的行號從 1 起算，與編輯器顯示的一致。
    pdb counts lines from one, the same as the editor shows.

    :param file_path: 檔案路徑 / the file to break in
    :param line: 1 起算的行號 / the 1-based line number
    :return: pdb 指令 / the pdb command
    """
    return f"break {_location(file_path, line)}"


def clear_command(file_path: str | Path, line: int) -> str:
    """
    組出清除一個中斷點的指令
    Build the command that clears one breakpoint.

    :param file_path: 檔案路徑 / the file the breakpoint is in
    :param line: 1 起算的行號 / the 1-based line number
    :return: pdb 指令 / the pdb command
    """
    return f"clear {_location(file_path, line)}"


def toggle_command(file_path: str | Path, line: int, is_set: bool) -> str:
    """
    組出切換一個中斷點的指令
    Build the command for toggling one breakpoint.

    :param file_path: 檔案路徑 / the file the breakpoint is in
    :param line: 1 起算的行號 / the 1-based line number
    :param is_set: 切換後該行是否有中斷點 / whether the line now has one
    :return: pdb 指令 / the pdb command
    """
    return breakpoint_command(file_path, line) if is_set else clear_command(file_path, line)


def _location(file_path: str | Path, line: int) -> str:
    """組出 pdb 認得的「檔案:行號」/ The ``file:line`` pdb understands."""
    return f"{Path(file_path).as_posix()}:{max(1, line)}"


def breakpoint_commands(file_path: str | Path, lines: list[int]) -> list[str]:
    """
    組出設定多個中斷點的指令
    Build the commands that set several breakpoints.

    行號排序且去重，因此送出的指令與畫面上的標記一一對應。
    The lines are sorted and de-duplicated, so the commands match the markers on
    screen one for one.

    :param file_path: 檔案路徑 / the file to break in
    :param lines: 1 起算的行號 / the 1-based line numbers
    :return: pdb 指令 / the pdb commands
    """
    return [breakpoint_command(file_path, line) for line in sorted(set(lines)) if line >= 1]


def step_command(action: str) -> str | None:
    """
    取得某個逐步動作的指令
    The command for a stepping action.

    :param action: 動作名稱 / the action's name
    :return: pdb 指令，動作未知時為 ``None`` / the command, or ``None``
    """
    return STEP_COMMANDS.get(action)
