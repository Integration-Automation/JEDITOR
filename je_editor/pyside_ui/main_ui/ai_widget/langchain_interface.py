import os
from typing import Union

from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


class LangChainInterface(object):

    def __init__(self, prompt_template: str, base_url: str, api_key: Union[SecretStr, str], chat_model: str):
        self.system_message_prompt = SystemMessagePromptTemplate.from_template(prompt_template)
        self.base_url = base_url
        self.api_key = api_key
        self.chat_model = chat_model
        os.environ["OPENAI_BASE_URL"] = self.base_url
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["CHAT_MODEL"] = self.chat_model
        self.chat_ai = ChatOpenAI(base_url=self.base_url, api_key=self.api_key, model=self.chat_model)
        print("Chat output:", self.chat_ai.invoke("你使用甚麼模型").content)
