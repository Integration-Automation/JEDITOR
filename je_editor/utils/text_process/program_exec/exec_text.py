import os.path
import subprocess


def exec_code(exec_file_name):
    """
    :param exec_file_name: string file will open to run
    :return: if error return result and True else return result and False
    """
    exec_file_name = exec_file_name.encode("utf-8").decode("utf-8")
    reformat_os_file_path = os.path.normpath(exec_file_name)
    exec_command = "".join(["python ", '"' + reformat_os_file_path + '"'])
    return_exec_result = ""
    return_error_result = ""
    process = subprocess.Popen(exec_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    print("execute: " + reformat_os_file_path)
    exec_result, error_result = process.communicate()
    reformat_exec_result = str(exec_result, encoding="utf-8")
    reformat_error_result = str(error_result, encoding="utf-8")
    for exec_result_line in reformat_exec_result:
        if not exec_result_line.startswith('#'):
            return_exec_result = "".join([return_exec_result, exec_result_line])
    for error_result_line in reformat_error_result:
        if not error_result_line.startswith('#'):
            return_error_result = "".join([return_error_result, error_result_line])
    if reformat_error_result == "":
        return return_exec_result, return_error_result
    else:
        return return_exec_result, return_error_result


if __name__ == "__main__":
    test_exec_file_name = r'D:\WorkSpaces\Program WorkSpace\Python\Project\je_editor\test\exec\get_exec_test.py'
    print(exec_code(test_exec_file_name))
