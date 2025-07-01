from queue import Queue


class AIConfig(object):

    def __init__(self):
        self.current_ai_model_system_prompt: str = ""
        self.choosable_ai: dict[str, dict[str, str]] = {
            "AI_model": {
                "ai_base_url": "",
                "ai_api_key": "",
                "chat_model": "",
                "prompt_template": "",
            }
        }
        self.message_queue = Queue()


ai_config = AIConfig()
