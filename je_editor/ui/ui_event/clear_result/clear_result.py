from tkinter import NORMAL, DISABLED


def clear_result_area(result_area_to_clear=None):
    if result_area_to_clear is not None:
        result_area_to_clear.configure(state=NORMAL)
        result_area_to_clear.delete("1.0", "end-1c")
        result_area_to_clear.configure(state=DISABLED)