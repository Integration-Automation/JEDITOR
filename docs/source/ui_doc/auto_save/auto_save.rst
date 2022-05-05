==================
je_editor Auto Save Doc
==================

.. code-block:: python

    def start_auto_save(auto_save_thread_object, current_file, code_editor):
        """
        :param auto_save_thread_object: auto save thread object
        :param current_file: current edit file
        :param code_editor: code editor we load text to save
        :return: new auto save thread object
        """