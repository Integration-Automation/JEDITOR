"""
核心服務介面的實作
Implementations of the core service interfaces.

``je_editor.core`` 只定義介面；真正去連某一家服務、啟動某一種程序的程式碼放在這裡。
跟核心層一樣，這裡不匯入 Qt，也不匯入 ``je_editor.pyside_ui``。第三方 SDK 都在用到
的時候才匯入，所以沒用到的供應者不會拖慢啟動。
``je_editor.core`` only defines interfaces. The code that actually talks to one
vendor's service or starts one kind of process lives here. Like the core layer,
nothing here imports Qt or ``je_editor.pyside_ui``. Third-party SDKs are
imported at the point of use, so a provider nobody uses costs nothing at startup.
"""
