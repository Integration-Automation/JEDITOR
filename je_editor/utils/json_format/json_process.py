import json.decoder
import sys
from json import dumps
from json import loads

from je_editor.utils.exception.exception_tags import je_editor_cant_reformat_json_error
from je_editor.utils.exception.exception_tags import je_editor_wrong_json_data_error
from je_editor.utils.exception.exceptions import JEditorJsonException


def __process_json(json_string: str, **kwargs):
    try:
        return dumps(loads(json_string), indent=4, sort_keys=True, **kwargs)
    except json.JSONDecodeError as error:
        print(je_editor_wrong_json_data_error, file=sys.stderr)
        raise error
    except TypeError:
        try:
            return dumps(json_string, indent=4, sort_keys=True, **kwargs)
        except TypeError:
            raise JEditorJsonException(je_editor_wrong_json_data_error)


def reformat_json(json_string: str, **kwargs):
    try:
        return __process_json(json_string, **kwargs)
    except JEditorJsonException:
        raise JEditorJsonException(je_editor_cant_reformat_json_error)
