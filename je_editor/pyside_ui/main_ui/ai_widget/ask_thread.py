from threading import Thread

from je_editor.pyside_ui.main_ui.ai_widget.ai_config import ai_config
from je_editor.pyside_ui.main_ui.ai_widget.langchain_interface import LangChainInterface


class AskThread(Thread):

    def __init__(self, lang_chain_interface: LangChainInterface, prompt):
        super().__init__()
        self.lang_chain_interface = lang_chain_interface
        self.prompt = prompt


    def run(self):
        ai_response = self.lang_chain_interface.call_ai_model(prompt=self.prompt)
        ai_config.message_queue.put(ai_response)