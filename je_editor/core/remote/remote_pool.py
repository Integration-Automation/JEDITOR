"""
目前開著的遠端工作階段
The remote sessions that are open.

同一台機器只該有一條連線：兩個根目錄在同一台機器上時共用一個工作階段，關閉服務時
也才有一個地方可以把它們全部中斷。傳輸方式依 URI 的 scheme 從登記表裡找。
One machine should have one connection: two roots on the same machine share a
session, and there is one place to disconnect them all from when the services
shut down. The transport is looked up in the registry by the URI's scheme.
"""
from __future__ import annotations

import threading
from urllib.parse import urlsplit

from je_editor.core.registry.named_registry import NamedRegistry
from je_editor.core.remote.remote_session import RemoteSession, RemoteTransport
from je_editor.utils.exception.exceptions import JEditorServiceException


def split_remote_uri(uri: str) -> tuple[str, str, str]:
    """
    把遠端資源的 URI 拆成 scheme、authority 與路徑
    Split the URI of a remote resource into its scheme, authority and path.

    :param uri: 例如 ``ssh://me@build-box:2222/home/me/project/main.py``
        such as ``ssh://me@build-box:2222/home/me/project/main.py``
    :return: ``(scheme, authority, 路徑)``；路徑一律以 ``/`` 開頭
        ``(scheme, authority, path)``, the path always starting with ``/``
    :raises JEditorServiceException: 沒有 scheme 或沒有 authority
        when it has no scheme or no authority
    """
    parts = urlsplit(uri)
    if not parts.scheme or not parts.netloc:
        raise JEditorServiceException(f"Not a remote URI (scheme://authority/path expected): {uri}")
    return parts.scheme.lower(), parts.netloc, parts.path or "/"


class RemoteSessionPool:
    """
    依 scheme 與 authority 保管遠端工作階段
    Keeps remote sessions by scheme and authority.
    """

    def __init__(self, transports: NamedRegistry[RemoteTransport]) -> None:
        """
        :param transports: 以 URI 的 scheme 登記的傳輸方式 / the transports, registered by URI scheme
        """
        self._transports = transports
        self._sessions: dict[tuple[str, str], RemoteSession] = {}
        self._lock = threading.Lock()

    def session_for(self, uri: str) -> RemoteSession:
        """
        取得某個遠端資源所在機器的工作階段，還沒有的話就建立（但不連線）
        The session of the machine a remote resource is on, built when there is none yet, without connecting.

        :param uri: 遠端資源的 URI / the remote resource's URI
        :return: 那台機器的工作階段 / the session of that machine
        :raises JEditorServiceException: URI 不是遠端的，或沒有登記那個 scheme 的傳輸方式
            when the URI is not remote, or no transport is registered for its scheme
        """
        scheme, authority, _path = split_remote_uri(uri)
        with self._lock:
            session = self._sessions.get((scheme, authority))
            if session is None:
                session = self._transports.require(scheme)(authority)
                self._sessions[(scheme, authority)] = session
            return session

    def sessions(self) -> list[RemoteSession]:
        """
        目前保管的工作階段
        The sessions that are kept.

        :return: 工作階段，依建立順序 / the sessions, in the order they were built
        """
        with self._lock:
            return list(self._sessions.values())

    def shutdown(self) -> None:
        """
        中斷每一條連線
        Disconnect every session.
        """
        with self._lock:
            sessions, self._sessions = list(self._sessions.values()), {}
        for session in sessions:
            session.disconnect()
