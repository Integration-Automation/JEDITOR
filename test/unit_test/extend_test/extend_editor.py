from je_editor import EditorMain


class TestEditor(EditorMain):

    def __init__(self):
        super().__init__()


TestEditor().start_editor()
