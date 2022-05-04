from je_editor import EditorMain


class TestEditor(EditorMain):

    def __init__(self):
        super().__init__()
        self.menu.add_command(label="test")


TestEditor().start_editor()
