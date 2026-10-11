"""
在遠端機器上執行的小幫手程式
The small helper program that runs on the remote machine.

遠端的每一件事——讀寫檔案、列目錄、找直譯器、在某個目錄下執行指令——都是請遠端的
Python 執行同一支程式、給它不同的操作名稱。這樣送到遠端的永遠是一個單純的引數清單，
不需要在遠端的 shell 裡組 ``cd ... && ...`` 這種指令，也就沒有 shell 語法注入的餘地；
回來的是 JSON，不必解析 ``ls`` 的輸出。
Everything done on the remote side, reading and writing files, listing
directories, finding interpreters, running a command in some directory, is the
remote Python running one program with a different operation name. What is sent
is therefore always a plain argument list: no ``cd ... && ...`` is ever built in
the remote shell, which leaves no room for shell injection, and what comes back
is JSON rather than the output of ``ls``.

``HELPER_SOURCE`` 是原始碼字串，以 ``python -c`` 交給遠端；它只用標準函式庫，而且要能
在舊一點的 Python 3 上執行，所以裡面不用新語法。
``HELPER_SOURCE`` is source text handed to the remote side with ``python -c``. It
uses the standard library only and has to run on an older Python 3, so it avoids
newer syntax.
"""
from __future__ import annotations

# 幫手程式回報「做不到」時用的結束代碼 / The exit code the helper uses to say it could not do it
HELPER_FAILED = 3
# 遠端要有其中一個 / One of these has to exist on the remote machine
REMOTE_PYTHON_CANDIDATES = ("python3", "python")

OP_PROBE = "probe"
OP_READ = "read"
OP_WRITE = "write"
OP_LIST = "list"
OP_STAT = "stat"
OP_INTERPRETERS = "interpreters"
OP_RUN = "run"

HELPER_SOURCE = r'''
import json, os, sys

def entry(path):
    info = os.stat(path)
    is_dir = os.path.isdir(path)
    return {"name": os.path.basename(path.rstrip("/")) or path, "path": path,
            "is_directory": is_dir, "size": 0 if is_dir else info.st_size, "modified": info.st_mtime}

def interpreters(root):
    import shutil, subprocess
    found, seen = [], set()
    candidates = []
    if root:
        for folder in (".venv", "venv", "env"):
            for name in ("bin/python", "Scripts/python.exe"):
                candidates.append(os.path.join(root, folder, name))
    candidates.append(sys.executable)
    for name in ("python3", "python"):
        located = shutil.which(name)
        if located:
            candidates.append(located)
    for candidate in candidates:
        real = os.path.realpath(candidate)
        if real in seen or not os.path.isfile(candidate):
            continue
        seen.add(real)
        try:
            version = subprocess.check_output(
                [candidate, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
                stderr=subprocess.DEVNULL, timeout=10).decode().strip()
        except Exception:
            continue
        found.append({"path": candidate, "version": version})
    return found

def main(argv):
    op, args = argv[0], argv[1:]
    out = sys.stdout.buffer
    if op == "probe":
        out.write(json.dumps({"python": sys.executable, "home": os.path.expanduser("~")}).encode())
    elif op == "read":
        with open(args[0], "rb") as handle:
            out.write(handle.read())
    elif op == "write":
        data = sys.stdin.buffer.read()
        folder = os.path.dirname(args[0])
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(args[0], "wb") as handle:
            handle.write(data)
    elif op == "list":
        names = sorted(os.listdir(args[0]))
        items = [entry(os.path.join(args[0], name)) for name in names]
        items.sort(key=lambda item: (not item["is_directory"], item["name"].lower()))
        out.write(json.dumps(items).encode())
    elif op == "stat":
        out.write(json.dumps(entry(args[0]) if os.path.exists(args[0]) else None).encode())
    elif op == "interpreters":
        out.write(json.dumps(interpreters(args[0] if args else "")).encode())
    elif op == "run":
        cwd = args[0]
        count = int(args[1])
        for pair in args[2:2 + count]:
            key, _, value = pair.partition("=")
            os.environ[key] = value
        command = args[2 + count:]
        import subprocess
        sys.exit(subprocess.call(command, cwd=cwd or None))
    else:
        raise ValueError("unknown operation: " + op)

try:
    main(sys.argv[1:])
except Exception as error:
    sys.stderr.write(type(error).__name__ + ": " + str(error))
    sys.exit(3)
'''
