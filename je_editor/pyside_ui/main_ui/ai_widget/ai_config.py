from pathlib import Path

from je_editor.utils.json.json_file import read_json


class AIConfig(object):

    def __init__(self):
        self.current_ai_model_system_prompt: str = ""
        self.choosable_ai: dict[str, dict[str, str]] = {
            "AI_model": {"ai_base_url": "", "ai_api_key": "", "chat_model": ""}
        }

