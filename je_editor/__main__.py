if __name__ == "__main__":
    # argparse
    import argparse

    from je_editor.ui.editor_main_ui.tkinter_editor import start_editor

    argparse_event_dict = {
        "start": start_editor,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", action="store_true", help="start editor")
    args = parser.parse_args()
    args = vars(args)
    for key, value in args.items():
        if value is not None and key not in ["start"]:
            argparse_event_dict.get(key)(value)
        else:
            argparse_event_dict.get(key)()

