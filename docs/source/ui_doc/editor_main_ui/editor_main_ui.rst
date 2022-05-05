==================
je_editor Main UI Doc
==================

.. code-block:: python

    "class that can inheritance and edit ui if you want"
    class EditorMain(object):

        """
        ui event
        """

        "start editor and start auto save if auto save not start"
        def start_editor(self):

        "editor close event"
        def close_event(self):

        """
        editor open  file from path
        event: tkinter event
        """
        def ui_open_file_to_read(self, event=None):

        """
        save editor file to choose path
        event: tkinter event
        """
        def ui_save_file_to_open(self, event=None):

        "open last edit file, use edit content last_file value to open"
        def ui_open_last_edit_file(self):

        """
        execute current file
        event: tkinter event
        """
        def ui_execute_program(self, event=None):

        """
        use to show popup menu
        event: tkinter event
        """
        def ui_show_popup_menu(self, event):

        """
        init high light and open and read last edit file then high light
        read content setting and set
        """
        def ui_init(self):

        """
        actually init object
        use_theme: tkinter theme
        main_window: what window will use
        """
        __init__(self, use_theme=None, main_window=Tk()):
            "setting"
            "is on test run"
            self.test_run
            "use to auto save"
            self.auto_save_thread
            "use to high light code editor text"
            self.highlight_text
            "tkinter style"
            self.style
            "top level window"
            self.main_window
            "file"
            "current edit file"
            self.current_file
            "use to read file from content"
            self.file_from_output_content
            "code and result textarea"
            "code editor frame"
            self.code_edit_frame
            "run result frame"
            self.program_run_result_frame
            "code edit textarea"
            self.code_editor_textarea
            "code edit scrollbar"
            self.code_editor_textarea_scrollbar_y
            "run result textarea"
            self.program_run_result_textarea
            "run result scrollbar"
            self.program_run_result_textarea_scrollbar_y
            "MenuBar"
            self.menu
            "file menu"
            self.file_menu
            "text menu"
            self.text_menu
            "use to choose text font"
            self.text_font_sub_menu
            "use to choose text size"
            self.text_size_sub_menu
            "use to get all font on computer"
            self.font_tuple
            "Encoding menu"
            self.encoding_menu
            "Language menu"
            self.language_menu
            "Popup menu"
            self.popup_menu
            "Exec Manager"
            self.exec_manager

