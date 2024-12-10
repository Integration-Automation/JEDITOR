import logging
from logging.handlers import RotatingFileHandler

logging.root.setLevel(logging.DEBUG)
jeditor_logger = logging.getLogger("JEditor")
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

# Rotating File Handler
rotating_file_handler = RotatingFileHandler(filename="JEditor.log", mode="w",maxBytes=1073741824)
rotating_file_handler.setFormatter(formatter)
jeditor_logger.addHandler(rotating_file_handler)


