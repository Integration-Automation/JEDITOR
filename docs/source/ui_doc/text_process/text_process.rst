==================
je_editor ExecManager Doc
==================

.. code-block:: python

    class ExecManager(object):

        def __init__(
                self,
                program_run_result_textarea,
                process_error_function,
                main_window,
                running_menu,
                program_language="python",
                program_encoding="utf-8"
        ):
            """
            :param program_run_result_textarea:  program run result textarea
            :param process_error_function: when process error call this function
            :param main_window: tkinter main window
            :param running_menu: menu when running change state
            :param program_language: which program language
            :param program_encoding: which encoding
            """

        def exec_code(self, exec_file_name):
            """
            :param exec_file_name: string file will open to run
            :return: if error return result and True else return result and False
            """

       "ui update method"
        def edit_tkinter_text(self):

        "exit program change run flag to false and clean read thread and queue and process"
        def exit_program(self):

        def read_program_output_from_process(self):

        def read_program_error_output_from_process(self):