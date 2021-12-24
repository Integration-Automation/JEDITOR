def execute_code(run_result, current_file, save_function, exec_manager):
    """
    :param exec_manager:
    :param run_result tkinter textarea to show result
    :param current_file will execute file
    :param save_function if current_file is None or "" save and run
    """
    run_result.delete("1.0", "end-1c")
    if current_file is not None and current_file != "":
        exec_manager.exec_code(current_file)
    else:
        save_function()
        if current_file is not None and current_file != "":
            exec_manager.exec_code(current_file)
