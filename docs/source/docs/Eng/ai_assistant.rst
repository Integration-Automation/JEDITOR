AI Assistant
=============

JEditor has a chat panel for talking to a large language model without leaving the editor.
The panel is provider-neutral: it sends a conversation to whichever provider is selected and
shows the reply, and it contains no code that belongs to one vendor.

Two providers ship with the editor:

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Provider
     - What it talks to
   * - ``openai``
     - Any OpenAI-compatible endpoint, through `LangChain <https://www.langchain.com/>`_.
       You name the address, the key and the model.
   * - ``anthropic``
     - Anthropic's Messages API, through the official ``anthropic`` SDK. The reply is
       streamed, so it appears as it is generated.

Open the panel from **Tab → ChatUI** or **Dock → AI**.

Setup
------

Press **Set AI setting** in the panel and fill in the provider you want to use. Every field
may be left empty.

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Setting
     - Description
   * - **Provider**
     - Which provider these settings belong to. Each provider keeps its own key, address,
       model and prompt, so switching back and forth loses nothing.
   * - **AI server URL**
     - The service address. Required for ``openai`` (for example
       ``https://api.openai.com/v1``). Leave it empty for ``anthropic`` unless you go
       through a proxy.
   * - **AI server API Key**
     - The key, shown as dots while you type. Leave it empty for ``anthropic`` to use the
       ``ANTHROPIC_API_KEY`` environment variable or a logged-in profile.
   * - **AI Model**
     - The model to use. ``anthropic`` offers ``claude-opus-5-5`` (the default),
       ``claude-sonnet-5-5``, ``claude-haiku-4-5`` and ``claude-fable-5-1``; any other
       model id can be typed in. ``openai`` has no fixed list.
   * - **System prompt**
     - Instructions sent with every request.

**Apply** uses the settings for this session and writes nothing to disk, so a key is only
ever stored where you put it. Tick **Also save to .jeditor/ai_config.json** to keep them for
the next launch. The file stores the key as plain text; add ``.jeditor/`` to ``.gitignore``
so it is never committed.

The settings file is grouped by provider:

.. code-block:: json

   {
     "active_provider": "anthropic",
     "providers": {
       "anthropic": {
         "api_key": "",
         "base_url": "",
         "model": "claude-opus-5-5",
         "system_prompt": "Answer briefly."
       },
       "openai": {
         "api_key": "...",
         "base_url": "https://api.openai.com/v1",
         "model": "gpt-4o-mini",
         "system_prompt": ""
       }
     }
   }

A file in the older format, with a single ``AI_model`` group, still loads: that group
becomes the ``openai`` provider. **Load AI setting** reads the file again.

.. note::

   Earlier versions exported ``OPENAI_BASE_URL``, ``OPENAI_API_KEY`` and ``CHAT_MODEL``
   into the editor's environment, which also handed the key to every program the editor
   started. The editor no longer does this. Set those variables yourself if something you
   run depends on them.

Chat Interface
---------------

- **Provider** and **Model** — Choose who answers. The model list comes from the provider,
  and the box accepts a model id that is not listed.
- **Send prompt** — Sends what is in the input box (``Enter`` does the same). The whole
  conversation so far goes with it, so follow-up questions have their context.
- **Stop** — Cancels the request in flight. A streamed reply stops at the next piece of
  text; what had arrived stays on screen but does not become part of the conversation.
- **New chat** — Forgets the conversation and clears the panel.
- **Status** — Shows whether a reply is awaited, and afterwards how many tokens the request
  and the reply used when the provider reports it.
- **Font size** — Changes the size of the text in the panel.

Requests run on a background thread, so the editor stays usable while a reply is on its way.

Anthropic specifics
--------------------

- Replies are streamed with a generous output limit, so long answers are not cut short.
- For ``claude-opus-5-5``, ``claude-opus-5``, ``claude-sonnet-5-5`` and
  ``claude-fable-5-1`` the request opts into the server-side refusal fallback: if the
  model's safety classifiers decline a request, the service re-runs it on another model
  instead of returning the refusal. This is skipped when a custom **AI server URL** is set,
  because the feature only exists on Anthropic's own API.
- If the model still declines, the panel reports it as a failed request and the partial
  text is not kept as an answer.

Error Handling
---------------

A failed request shows a dialog that says what went wrong: a rejected key, an unknown model,
rate limiting, a network failure or missing credentials each have their own message. The
prompt that failed is dropped from the conversation, so the next request does not carry a
question nobody answered.

Adding a Provider
------------------

A provider is any object with a ``name``, a ``models()`` method and a ``complete()`` method;
see ``AIProvider`` in :doc:`core_services`. Register it on the window's services and it
appears in the panel's provider list:

.. code-block:: python

   from je_editor.core import ChatResponse, ModelInfo


   class ShoutingProvider:
       """Answers by repeating the question in upper case."""

       name = "shouting"

       def models(self):
           return [ModelInfo("shout-1", "Shout")]

       def complete(self, request, on_text=None, cancel=None):
           text = request.messages[-1].content.upper()
           if on_text is not None:
               on_text(text)
           return ChatResponse(text, "shout-1")


   def add_to(window):
       """Call with the editor window, for example from a plugin's ``register()``."""
       window.services.ai_providers.register(ShoutingProvider.name, ShoutingProvider())

``complete()`` is called on a background thread and may block. Raise
``JEditorServiceException`` with a message for the user when the request fails.
