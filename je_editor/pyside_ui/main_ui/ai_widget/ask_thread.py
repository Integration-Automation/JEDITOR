from threading import Thread

from je_editor.pyside_ui.main_ui.ai_widget.ai_config import ai_config
from je_editor.pyside_ui.main_ui.ai_widget.langchain_interface import LangChainInterface


class AskThread(Thread):
    """
    AskThread 類別：用來在背景執行緒中呼叫 AI 模型，避免阻塞主執行緒
    AskThread class: runs AI model calls in a background thread to avoid blocking the main thread
    """

    def __init__(self, lang_chain_interface: LangChainInterface, prompt):
        """
        初始化 AskThread
        Initialize AskThread
        :param lang_chain_interface: LangChainInterface 實例，用來呼叫 AI 模型
                                     LangChainInterface instance for calling AI model
        :param prompt: 傳給 AI 模型的提示詞
                       Prompt to send to the AI model
        """
        super().__init__()
        self.lang_chain_interface = lang_chain_interface
        self.prompt = prompt

    def run(self):
        """
        執行緒的主要邏輯：
        1. 呼叫 AI 模型並取得回應
        2. 將回應放入 ai_config 的 message_queue 中，供主程式使用
        Thread main logic:
        1. Call AI model and get response
        2. Put response into ai_config.message_queue for main program to consume
        """
        ai_response = self.lang_chain_interface.call_ai_model(prompt=self.prompt)
        ai_config.message_queue.put(ai_response)
