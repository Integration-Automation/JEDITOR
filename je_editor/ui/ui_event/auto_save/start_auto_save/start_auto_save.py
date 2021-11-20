from je_editor.utils.file.save.save_file import SaveThread


def start_auto_save(auto_save_thread_object, current_file, code_editor):
    if auto_save_thread_object is not None:
        auto_save_thread_object.file = current_file
        return auto_save_thread_object
    elif current_file is not None and auto_save_thread_object is None:
        auto_save = SaveThread(current_file, code_editor)
        auto_save.start()
        return auto_save
