AI 助手
========

JEditor 整合了基於 `LangChain <https://www.langchain.com/>`_ 和 OpenAI 相容 API 的
AI 聊天助手。AI 面板讓您可以直接在編輯器內與大型語言模型對話。

設定
-----

使用 AI 助手前，您需要先進行設定：

1. 從選單開啟 AI 設定對話框
2. 設定以下參數：

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 設定項目
     - 說明
   * - **API Base URL**
     - API 端點（例如 ``https://api.openai.com/v1``）
   * - **API Key**
     - 您的 OpenAI API 金鑰
   * - **Model**
     - 使用的模型（例如 ``gpt-3.5-turbo``、``gpt-4`` 或任何自訂模型）
   * - **System Prompt**
     - 設定 AI 行為與上下文的範本

在對話框中輸入的內容只套用於目前這次執行。若希望每次啟動都載入設定，請自行撰寫
``.jeditor/ai_config.json``——編輯器只在啟動時讀取這個檔案，從不寫入它，因此您的金鑰
只會存在您自己放的地方：

.. code-block:: json

   {
     "AI_model": {
       "ai_base_url": "https://api.openai.com/v1",
       "ai_api_key": "...",
       "chat_model": "gpt-4",
       "prompt_template": ""
     }
   }

建議把 ``.jeditor/`` 加進 ``.gitignore``，金鑰才不會被提交。設定好模型之後，編輯器會把
``OPENAI_BASE_URL``、``OPENAI_API_KEY`` 與 ``CHAT_MODEL`` 匯出到環境變數，供 LangChain
套件取用。

聊天介面
---------

AI 聊天面板提供：

- **訊息歷史** — 可捲動的聊天歷史，包含所有先前的訊息
- **輸入欄位** — 在面板底部輸入提示詞
- **字型大小調整** — 自訂聊天面板的字型大小
- **唯讀訊息區域** — 聊天歷史以唯讀方式顯示

非同步通訊
-----------

AI 請求以非同步方式處理，保持編輯器的回應能力：

- 訊息在背景執行緒中傳送給 AI
- 回應透過可設定的計時器間隔拉取回來
- 訊息佇列確保有序通訊
- 等待回應期間 UI 保持完全互動

錯誤處理
---------

如果 AI 請求失敗（例如網路錯誤、無效的 API 金鑰），JEditor 會顯示清楚的錯誤對話框
描述問題。解決問題後，聊天工作階段可繼續正常使用。
