==================
je_editor Tag Keyword Doc
==================

.. code-block:: python

    class HighlightText(object):

        def __init__(self, tkinter_text, start_position="1.0", end_position="end"):
            """
            :param tkinter_text: want to set highlight's tkinter text
            :param start_position: search start position
            :param end_position: search end position
            """

        def search(self, event=None):
            """
            :param event: tkinter event
            create temp var tag
            remove tag
            search all word in keyword_list and tag
            """