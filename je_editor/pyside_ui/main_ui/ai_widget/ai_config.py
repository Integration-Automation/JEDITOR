from queue import Queue


class AIConfig(object):
    """
    AIConfig 類別：用來管理 AI 模型的設定與訊息佇列
    AIConfig class: manages AI model configuration and message queue
    """

    def __init__(self):
        # 當前 AI 模型的系統提示詞 (system prompt)
        # Current AI model system prompt
        self.current_ai_model_system_prompt: str = ""

        # 可選擇的 AI 模型設定字典
        # Dictionary of choosable AI model configurations
        # 結構: { "AI_model": { "ai_base_url": ..., "ai_api_key": ..., "chat_model": ..., "prompt_template": ... } }
        self.choosable_ai: dict[str, dict[str, str]] = {
            "AI_model": {
                "ai_base_url": "",       # AI 服務的基礎 URL / Base URL of AI service
                "ai_api_key": "",        # API 金鑰 / API key
                "chat_model": "",        # 模型名稱 / Model name
                "prompt_template": "",   # 提示詞模板 / Prompt template
            }
        }

        # 訊息佇列，用來暫存與 AI 的互動訊息
        # Message queue for storing AI interaction messages
        self.message_queue = Queue()


# 建立全域唯一的 AIConfig 實例
# Create a global singleton instance of AIConfig
ai_config = AIConfig()