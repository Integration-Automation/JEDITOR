from __future__ import annotations

import os
import re
from typing import Union, TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

class LangChainInterface(object):

    def __init__(self, main_window: EditorMain, prompt_template: str, base_url: str, api_key: Union[SecretStr, str],
                 chat_model: str):
        self.system_message_prompt = SystemMessagePromptTemplate.from_template(prompt_template)
        self.base_url = base_url
        self.api_key = api_key
        self.chat_model = chat_model
        self.main_window = main_window
        os.environ["OPENAI_BASE_URL"] = self.base_url
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["CHAT_MODEL"] = self.chat_model
        self.chat_ai = ChatOpenAI(base_url=self.base_url, api_key=self.api_key, model=self.chat_model)

    def call_ai_model(self, prompt: str) -> str | None:
        message = None
        try:
            message = self.chat_ai.invoke(prompt).text()
            match = re.search(r"</think>\s*(.*)", message, re.DOTALL)
            if match:
                message = match.group(1).strip()
            else:
                message = message

        except Exception as error:
            QMessageBox.warning(self.main_window,
                                language_wrapper.language_word_dict.get("call_ai_model_error_title"),
                                language_wrapper.language_word_dict.get(repr(error)))
        return message
