import json.decoder
import sys
from json import dumps
from json import loads

# 匯入自訂錯誤訊息與例外類別
# Import custom error messages and exception class
from je_editor.utils.exception.exception_tags import cant_reformat_json_error
from je_editor.utils.exception.exception_tags import wrong_json_data_error
from je_editor.utils.exception.exceptions import JEditorJsonException
from je_editor.utils.logging.loggin_instance import jeditor_logger


def __process_json(json_string: str, **kwargs) -> str:
    """
    功能說明 (Function Description):
    嘗試將輸入的 JSON 字串重新格式化 (pretty print)。
    Try to reformat the input JSON string (pretty print).

    :param json_string: JSON 格式字串 / JSON formatted string
    :param kwargs: 額外參數傳給 json.dumps / extra arguments for json.dumps
    :return: 格式化後的 JSON 字串 / formatted JSON string
    """
    try:
        # 嘗試先將字串解析為 JSON，再重新輸出為縮排格式
        # Try to parse string into JSON, then dump with indentation
        return dumps(loads(json_string), indent=4, sort_keys=True, **kwargs)
    except json.JSONDecodeError as error:
        # 如果 JSON 格式錯誤，輸出錯誤訊息到 stderr 並拋出例外
        # If JSON format is invalid, print error to stderr and raise exception
        print(wrong_json_data_error, file=sys.stderr)
        raise error
    except TypeError:
        # 如果輸入不是合法 JSON 字串，嘗試直接將物件轉為 JSON
        # If input is not a valid JSON string, try dumping the object directly
        try:
            return dumps(json_string, indent=4, sort_keys=True, **kwargs)
        except TypeError:
            # 若仍失敗，拋出自訂例外
            # If still fails, raise custom exception
            raise JEditorJsonException(wrong_json_data_error)


def reformat_json(json_string: str, **kwargs) -> str:
    """
    功能說明 (Function Description):
    對外提供的 JSON 格式化函式，會呼叫內部的 __process_json。
    Public function to reformat JSON string, calls __process_json internally.

    :param json_string: JSON 格式字串 / JSON formatted string
    :param kwargs: 額外參數傳給 json.dumps / extra arguments for json.dumps
    :return: 格式化後的 JSON 字串 / formatted JSON string
    """
    # 記錄日誌，方便除錯與追蹤
    # Log the input string and kwargs for debugging and tracking
    jeditor_logger.info(f"json_process.py reformat_json "
                        f"json_string: {json_string} "
                        f"kwargs: {kwargs}")
    try:
        return __process_json(json_string, **kwargs)
    except JEditorJsonException:
        # 捕捉自訂例外並重新拋出
        # Catch custom exception and re-raise
        raise JEditorJsonException(cant_reformat_json_error)