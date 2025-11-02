from __future__ import annotations

import os
import re
from typing import Union, TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox
from langchain_core.prompts.chat import SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.ai_widget.chat_ui import ChatUI


class LangChainInterface(object):
    """
    LangChainInterface 負責與 LangChain + OpenAI 模型互動
    LangChainInterface is responsible for interacting with LangChain + OpenAI model
    """

    def __init__(self, main_window: ChatUI, prompt_template: str, base_url: str,
                 api_key: Union[SecretStr, str], chat_model: str):
        """
        初始化 LangChainInterface
        Initialize LangChainInterface

        :param main_window: 主視窗，用於顯示錯誤訊息 / Main window, used for showing error messages
        :param prompt_template: 系統提示詞模板 / System prompt template
        :param base_url: OpenAI API 的基礎 URL / Base URL for OpenAI API
        :param api_key: OpenAI API 金鑰 / OpenAI API key
        :param chat_model: 使用的聊天模型名稱 / Chat model name
        """
        # 建立系統提示詞模板 / Create system message prompt template
        self.system_message_prompt = SystemMessagePromptTemplate.from_template(prompt_template)

        # 儲存基本設定 / Store basic settings
        self.base_url = base_url
        self.api_key = api_key
        self.chat_model = chat_model
        self.main_window = main_window

        # 將設定寫入環境變數，方便其他套件讀取
        # Save settings into environment variables for other packages to read
        os.environ["OPENAI_BASE_URL"] = self.base_url
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["CHAT_MODEL"] = self.chat_model

        # 初始化 ChatOpenAI 物件，用於呼叫模型
        # Initialize ChatOpenAI object for model invocation
        self.chat_ai = ChatOpenAI(base_url=self.base_url, api_key=self.api_key, model=self.chat_model)

    def call_ai_model(self, prompt: str) -> str | None:
        """
        呼叫 AI 模型並回傳結果
        Call AI model and return response

        :param prompt: 使用者輸入的提示詞 / User input prompt
        :return: AI 回覆文字或 None / AI response text or None
        """
        message = None
        try:
            # 呼叫 AI 並取得回覆 / Invoke AI and get response
            message = self.chat_ai.invoke(prompt).text()

            # 嘗試過濾掉 <think> 標籤前的內容，只保留主要回覆
            # Try to filter out content before </think>, keep only main response
            match = re.search(r"</think>\s*(.*)", message, re.DOTALL)
            if match:
                message = match.group(1).strip()
            else:
                message = message

        except Exception as error:
            # 發生錯誤時，彈出警告視窗顯示錯誤訊息
            # Show error message in a warning dialog if exception occurs
            QMessageBox.warning(
                self.main_window,
                language_wrapper.language_word_dict.get("call_ai_model_error_title"),
                str(error)
            )
        return message
