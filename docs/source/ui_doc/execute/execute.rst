==================
je_editor Execute Doc
==================

.. code-block:: python

    def execute_code(current_file, save_function, exec_manager):
        """
        :param exec_manager:
        :param current_file will execute file
        :param save_function if current_file is None or "" save and run
        """


    def stop_program(exec_manager):
        """
        :param exec_manager: call exec manager stop program method to stop
        """

    def execute_shell_command(program_run_result_textarea, code_editor):
    """
    :param program_run_result_textarea tkinter textarea to show result
    :param code_editor get the command to run
    """