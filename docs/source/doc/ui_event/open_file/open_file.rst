==================
je_editor Open File Doc
==================

.. code-block:: python

    def open_file_to_read(code_editor):
        """
        :param code_editor the editor to insert file content
        :return readied file
        show open file dialog
        if choose some file
            open and read it insert content to tkinter code_editor
            change current file
            start auto save
        """

    def open_last_edit_file(last_file_name, code_editor):
        """
        :param last_file_name: readied file from output content
        :param code_editor the editor to insert file content
        :return readied file
        open last edit file
        if success open file
        insert file content to code_editor
        """