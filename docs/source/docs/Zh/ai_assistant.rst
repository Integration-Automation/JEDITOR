AI 助理
=======

JEditor 有一個對話面板，不必離開編輯器就能與大型語言模型對話。面板不綁定任何一家供應者：
它把對話送給目前選用的供應者並顯示回覆，裡面沒有任何一家專屬的程式碼。

編輯器內建兩個供應者：

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - 供應者
     - 連到哪裡
   * - ``openai``
     - 任何 OpenAI 相容的端點，透過 `LangChain <https://www.langchain.com/>`_ 呼叫。
       位址、金鑰與模型都由您填寫。
   * - ``anthropic``
     - Anthropic 的 Messages API，透過官方的 ``anthropic`` SDK 呼叫。回覆以串流方式取得，
       所以會邊產生邊顯示。

從 **Tab → ChatUI** 或 **Dock → AI** 開啟面板。

設定
----

按面板上的 **設定 AI 設定**，填入要使用的供應者。每個欄位都可以留空。

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - 設定
     - 說明
   * - **供應者**
     - 這組設定屬於哪個供應者。每個供應者各自保管金鑰、位址、模型與提示詞，來回切換不會
       互相蓋掉。
   * - **AI 伺服器 URL**
     - 服務的位址。 ``openai`` 必填（例如 ``https://api.openai.com/v1`` ）。 ``anthropic``
       除非經過代理，否則留空。
   * - **AI 伺服器 API Key**
     - 金鑰，輸入時顯示為圓點。 ``anthropic`` 留空時會使用環境變數 ``ANTHROPIC_API_KEY``
       或已登入的設定檔。
   * - **AI Model**
     - 要使用的模型。 ``anthropic`` 提供 ``claude-opus-5-5`` （預設）、
       ``claude-sonnet-5-5`` 、 ``claude-haiku-4-5`` 與 ``claude-fable-5-1`` ，也可以自行
       輸入其他模型代號。 ``openai`` 沒有固定清單。
   * - **系統提示詞**
     - 每次請求都會一併送出的指示。

**套用** 只把設定用在這次執行，不寫入磁碟，所以金鑰只會存在您自己放的地方。勾選
**同時存到 .jeditor/ai_config.json** 才會保留到下次啟動。這個檔案以明文儲存金鑰；請把
``.jeditor/`` 加進 ``.gitignore`` ，避免金鑰被提交。

設定檔以供應者分組：

.. code-block:: json

   {
     "active_provider": "anthropic",
     "providers": {
       "anthropic": {
         "api_key": "",
         "base_url": "",
         "model": "claude-opus-5-5",
         "system_prompt": "Answer briefly."
       },
       "openai": {
         "api_key": "...",
         "base_url": "https://api.openai.com/v1",
         "model": "gpt-4o-mini",
         "system_prompt": ""
       }
     }
   }

舊格式的檔案（只有一組 ``AI_model`` ）仍然讀得進來：那一組會成為 ``openai`` 供應者的設定。
**載入 AI 設定** 會重新讀取這個檔案。

.. note::

   先前的版本會把 ``OPENAI_BASE_URL`` 、 ``OPENAI_API_KEY`` 與 ``CHAT_MODEL`` 匯出到編輯器的
   環境變數，這也等於把金鑰交給編輯器啟動的每一個程式。現在不再這麼做。如果您執行的程式
   依賴這些變數，請自行設定。

對話介面
--------

- **供應者** 與 **模型** — 選擇由誰回答。模型清單來自供應者，也可以輸入清單以外的模型代號。
- **傳送 prompt** — 送出輸入框的內容（按 ``Enter`` 也可以）。到目前為止的整段對話會一併
  送出，所以追問時模型知道前後文。
- **停止** — 取消進行中的請求。串流的回覆會在下一段文字到達時停下；已經收到的部分留在畫面上，
  但不算進對話。
- **新對話** — 忘掉目前的對話並清空面板。
- **狀態** — 顯示是否正在等待回覆；完成後，若供應者有回報，會顯示請求與回覆各用了多少 token。
- **字型大小** — 調整面板文字的大小。

請求在背景執行緒進行，等待回覆時編輯器仍然可以操作。

Anthropic 的細節
----------------

- 回覆以串流取得，輸出上限設得夠大，長的回答不會被截斷。
- 使用 ``claude-opus-5-5`` 、 ``claude-opus-5`` 、 ``claude-sonnet-5-5`` 與
  ``claude-fable-5-1`` 時，請求會啟用伺服器端的拒絕後備機制：模型的安全分類器拒絕請求時，
  服務會改用另一個模型重跑，而不是把拒絕傳回來。設定了自訂的 **AI 伺服器 URL** 時不會啟用，
  因為這個功能只存在於 Anthropic 自己的 API。
- 如果模型仍然拒絕，面板會把它當成失敗的請求回報，已收到的片段不會被當成答案。

錯誤處理
--------

請求失敗時會跳出對話框說明原因：金鑰被拒、模型不存在、被限流、網路失敗或找不到認證，各有自己的
訊息。失敗的那一句會從對話中移除，所以下一次請求不會帶著一句沒人回答過的話。

新增供應者
----------

供應者是任何具有 ``name`` 、 ``models()`` 方法與 ``complete()`` 方法的物件，介面請見
:doc:`core_services` 的 ``AIProvider`` 。把它登記到視窗的服務上，面板的供應者清單就會出現它：

.. code-block:: python

   from je_editor.core import ChatResponse, ModelInfo


   class ShoutingProvider:
       """把問題轉成大寫當作回答。"""

       name = "shouting"

       def models(self):
           return [ModelInfo("shout-1", "Shout")]

       def complete(self, request, on_text=None, cancel=None):
           text = request.messages[-1].content.upper()
           if on_text is not None:
               on_text(text)
           return ChatResponse(text, "shout-1")


   def add_to(window):
       """以編輯器視窗呼叫，例如在外掛的 ``register()`` 裡。"""
       window.services.ai_providers.register(ShoutingProvider.name, ShoutingProvider())

``complete()`` 會在背景執行緒被呼叫，可以等待。請求失敗時請丟出 ``JEditorServiceException`` ，
訊息會顯示給使用者。
