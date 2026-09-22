"""
JEditor 的 logger 與它寫入的日誌檔。
The ``JEditor`` logger and the file it writes to.

日誌檔預設在 ``~/.je_editor/logs/JEditor.log``；環境變數 ``JE_EDITOR_LOG_FILE`` 可以指定別的
路徑（相對路徑以 import 當下的工作目錄為準，設成 ``os.devnull`` 就不寫檔）。以前是相對路徑
``JEditor.log``、import 時就以覆寫模式開檔，所以任何 import 它的程式（PyBreeze、測試）都會在
當下的工作目錄留下一份日誌，還會蓋掉前一個行程寫的內容。
The log file is ``~/.je_editor/logs/JEditor.log`` unless ``JE_EDITOR_LOG_FILE`` names another
path (a relative one resolves against the cwd at import time; ``os.devnull`` turns the file off).
It used to be the relative path ``JEditor.log``, opened for overwrite at import, so every process
that imported the package -- PyBreeze, test runs -- left a log in whatever directory it started
in and wiped the previous process's log.

套件自己的 handler 在第一筆紀錄才開檔，import 不寫任何檔案。同一個帳號的所有行程共用這個檔，
所以用附加模式、每行帶行程編號，而且只在開檔時輪替：Windows 上別的行程開著的檔案改不了名，
在 ``emit()`` 裡輪替會讓之後的每一筆都失敗。
The package's handler opens the file on the first record, so importing writes nothing. Every
process on the account shares the file, so it is opened for append, each line carries the
process id, and it is rotated only when a process opens it: Windows refuses to rename a file
another process holds open, and a rotation attempted inside ``emit()`` would then fail on every
later record.
"""
import logging
import os
import warnings
from logging.handlers import RotatingFileHandler
from pathlib import Path

# root logger 不動。JEditor 會被別的程式嵌進去用，把 root 調成 DEBUG 等於替整個宿主
# 程序決定了日誌層級；而這對自己也沒有用——下面的 logger 有自己的層級，記錄往上傳
# 時只看各個 handler 的層級，不看 root 的。
# The root logger is left alone. JEditor is embedded in other applications, so
# putting root at DEBUG would decide the log level for the whole host process --
# and it gains nothing here anyway: the logger below sets its own level, and
# records travelling up are filtered by each handler's level, never by root's.

# 建立一個名為 "JEditor" 的 logger
# Create a logger named "JEditor"
jeditor_logger = logging.getLogger("JEditor")

# 設定 JEditor logger 的層級為 WARNING (只會輸出 WARNING 以上的訊息)
# Set the JEditor logger level to WARNING (only WARNING and above will be logged)
jeditor_logger.setLevel(logging.WARNING)

# 日誌格式：時間 | 行程編號 | logger 名稱 | 等級 | 訊息
# Log format: time | process id | logger name | level | message
formatter = logging.Formatter('%(asctime)s | %(process)d | %(name)s | %(levelname)s | %(message)s')

#: 指定日誌檔位置的環境變數 / Environment variable that overrides where the log file is written.
LOG_FILE_ENV = "JE_EDITOR_LOG_FILE"

#: 開檔時超過這個大小就先改名成 ``<name>.1`` / A file past this size is moved to ``<name>.1`` on open.
ROTATE_AT_BYTES = 10 * 1024 * 1024


def default_log_file() -> Path:
    """
    回傳日誌檔路徑：``$JE_EDITOR_LOG_FILE``，沒有設就用家目錄下的預設位置。
    Return the log file path: ``$JE_EDITOR_LOG_FILE``, else the home-directory default.
    """
    configured = os.environ.get(LOG_FILE_ENV, "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".je_editor" / "logs" / "JEditor.log"


def _rotate_if_large(path: Path, limit: int) -> None:
    """
    檔案超過 ``limit`` 位元組就改名成 ``<path>.1``；別的行程開著時 Windows 會拒絕，就照舊附加。
    Move ``path`` to ``<path>.1`` when it is larger than ``limit`` bytes. Best effort: while
    another process holds the file Windows refuses the rename, and the file keeps growing.
    """
    try:
        if limit <= 0 or not path.is_file() or path.stat().st_size <= limit:
            return
        os.replace(path, path.with_name(path.name + ".1"))
    except OSError:
        return


class JEditorLoggingHandler(RotatingFileHandler):
    """
    JEditor 的檔案 handler：預設寫到 ``default_log_file()``，附加模式，UTF-8。
    JEditor's file handler: writes to ``default_log_file()``, appends, UTF-8.

    ``delay=True`` 讓開檔（連同建立目錄）延到第一筆紀錄；套件自己的 handler 就是這樣建的。
    開不了檔時改寫到 ``os.devnull`` 並發出一次 ``RuntimeWarning``，不讓 import 失敗。
    ``delay=True`` defers opening (and creating the directory) to the first record, which is how
    the package's own handler is built. A file that cannot be opened is swapped for
    ``os.devnull`` with one ``RuntimeWarning`` instead of failing the import.
    """

    def __init__(self, filename: str | None = None, mode: str = "a",
                 max_bytes: int = 0, backup_count: int = 0,
                 encoding: str = "utf-8", errors: str = "backslashreplace",
                 delay: bool = False) -> None:
        """
        :param filename: 日誌檔路徑，預設 ``default_log_file()`` / log file path, default ``default_log_file()``
        :param mode: 開檔模式（預設附加）/ file open mode (append by default)
        :param max_bytes: ``emit()`` 內輪替的門檻，0 表示只在開檔時輪替 / in-``emit()`` rotation size, 0 = only on open
        :param backup_count: 保留的備份數 / number of backups to keep
        :param encoding: 檔案編碼，預設 UTF-8 / file encoding, UTF-8 by default
        :param errors: 編碼錯誤的處理方式 / how encoding errors are handled
        :param delay: 延到第一筆紀錄才開檔 / open the file on the first record
        """
        # encoding 必須明寫：用系統預設（繁中 Windows 是 cp950）時，翻譯字串或路徑裡只要有
        # cp950 以外的字元，那一筆就會在 emit() 裡丟 UnicodeEncodeError，被 logging 吞掉而消失。
        # errors 用 backslashreplace（logging.basicConfig 的預設）：落單的 surrogate 在 strict
        # 下仍會丟錯，換成跳脫字元總比整筆消失好。
        # encoding must be explicit: on the locale codec (cp950 on zh-TW Windows) any character
        # outside it -- translated strings, file paths -- raises inside emit(), which logging
        # swallows, so the record vanishes. errors is backslashreplace, logging.basicConfig's own
        # default: a lone surrogate still raises under strict, and an escaped record beats a lost one.
        path = filename if filename is not None else str(default_log_file())
        super().__init__(filename=path, mode=mode, maxBytes=max_bytes, backupCount=backup_count,
                         encoding=encoding, delay=delay, errors=errors)
        self.setFormatter(formatter)  # 設定日誌格式 / set log formatter
        self.setLevel(logging.DEBUG)  # 設定 handler 層級為 DEBUG / set handler level to DEBUG

    def _open(self):
        """
        開檔前先建立目錄並輪替；開不了就改寫到 ``os.devnull``，只警告一次。
        Create the directory and rotate before opening; fall back to ``os.devnull``, warning once.
        """
        path = Path(self.baseFilename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _rotate_if_large(path, ROTATE_AT_BYTES)
            return super()._open()
        except OSError as error:
            warnings.warn(f"JEditor log file {path} unavailable, file logging off: {error!r}",
                          RuntimeWarning, stacklevel=2)
            # handler 自己持有並關閉這個串流 / the handler owns and closes this stream
            return open(os.devnull, self.mode, encoding=self.encoding, errors=self.errors)  # noqa: SIM115

    def emit(self, record: logging.LogRecord) -> None:
        """
        實際輸出日誌的方法，這裡直接呼叫父類別的 emit
        Method to emit log records, here just call parent emit
        """
        super().emit(record)


# 建立檔案處理器（第一筆紀錄才開檔）並加入到 JEditor logger
# Create the file handler (opened on the first record) and add it to the JEditor logger
file_handler = JEditorLoggingHandler(delay=True)
jeditor_logger.addHandler(file_handler)
