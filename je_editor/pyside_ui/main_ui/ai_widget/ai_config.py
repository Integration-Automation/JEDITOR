from pathlib import Path

from je_editor.utils.json.json_file import read_json


class AIConfig(object):

    def __init__(self):
        self.current_ai_model_system_prompt: str = ""
        self.choosable_ai: dict[str, dict[str, str]] = {
            "AI_model": {"ai_base_url": "", "ai_api_key": "", "chat_model": ""}
        }


if __name__ == "__main__":
    ai_config = AIConfig()
    ai_config_file = Path(str(Path.cwd()) + "/" + ".jeditor/ai_config.json")
    if ai_config_file.exists():
        with open(ai_config_file, "r", encoding="utf-8") as file:
            json_data: dict = read_json(str(ai_config_file))
        if json_data:
            if json_data.get("AI_model") and len(json_data.get("AI_model")) == 3:
                ai_info: dict = json_data.get("AI_model")
                if ai_info.get("ai_base_url") and ai_info.get("chat_model"):
                    ai_config.choosable_ai.update(json_data)
                    print(ai_config.choosable_ai)
                else:
                    print("OOO")
