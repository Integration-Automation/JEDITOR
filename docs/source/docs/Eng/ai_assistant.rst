AI Assistant
=============

JEditor integrates an AI-powered chat assistant using `LangChain <https://www.langchain.com/>`_
and OpenAI-compatible APIs. The AI panel allows you to have conversations with a large language
model directly within the editor.

Setup
------

Before using the AI assistant, you need to configure it:

1. Open the AI configuration dialog from the menu
2. Set the following parameters:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Setting
     - Description
   * - **API Base URL**
     - The API endpoint (e.g., ``https://api.openai.com/v1``)
   * - **API Key**
     - Your OpenAI API key
   * - **Model**
     - The model to use (e.g., ``gpt-3.5-turbo``, ``gpt-4``, or any custom model)
   * - **System Prompt**
     - A template that sets the AI's behavior and context

What you enter in the dialog applies to the current session. To have the settings loaded
on every launch, write them to ``.jeditor/ai_config.json`` yourself — the editor reads
that file at startup but never writes it, so your key is only ever stored where you put
it:

.. code-block:: json

   {
     "AI_model": {
       "ai_base_url": "https://api.openai.com/v1",
       "ai_api_key": "...",
       "chat_model": "gpt-4",
       "prompt_template": ""
     }
   }

``.jeditor/`` is worth adding to ``.gitignore`` so the key is never committed. Once a
model is configured, the editor exports ``OPENAI_BASE_URL``, ``OPENAI_API_KEY`` and
``CHAT_MODEL`` into the environment for the LangChain packages to pick up.

Chat Interface
---------------

The AI chat panel provides:

- **Message history** — Scrollable chat history with all previous messages
- **Input field** — Type your prompt at the bottom of the panel
- **Font size adjustment** — Customize the chat panel's font size
- **Read-only message area** — Chat history is displayed in a read-only area

Async Communication
--------------------

AI requests are handled asynchronously to keep the editor responsive:

- Messages are sent to the AI in a background thread
- Responses are pulled back using a configurable timer interval
- A message queue ensures orderly communication
- The UI remains fully interactive while waiting for responses

Error Handling
---------------

If the AI request fails (e.g., network error, invalid API key), JEditor shows a clear error
dialog describing the problem. The chat session continues to work after resolving the issue.
