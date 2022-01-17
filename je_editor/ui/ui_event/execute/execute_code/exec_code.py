def execute_code(current_file, save_function, exec_manager):
    """
    :param exec_manager:
    :param current_file will execute file
    :param save_function if current_file is None or "" save and run
    """
    if current_file is not None and current_file != "":
        exec_manager.exec_code(current_file)
    else:
        save_function()
        if current_file is not None and current_file != "":
            exec_manager.exec_code(current_file)


def stop_program(exec_manager):
    """
    :param exec_manager: call exec manager stop program method to stop
    """
    exec_manager.exit_program()
