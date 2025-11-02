from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.english import english_word_dict
from je_editor.utils.multi_language.traditional_chinese import traditional_chinese_word_dict


class LanguageWrapper(object):
    """
    功能說明 (Function Description):
    - 提供一個語言包裝器，用來管理目前使用的語言與對應的字典。
    - A language wrapper to manage the current language and its corresponding dictionary.
    """

    def __init__(self):
        # 初始化時記錄日誌
        # Log initialization
        jeditor_logger.info("Init LanguageWrapper")

        # 預設語言為 English
        # Default language is English
        self.language: str = "English"

        # 可選語言字典對照表
        # Mapping of available languages to their word dictionaries
        self.choose_language_dict = {
            "English": english_word_dict,
            "Traditional_Chinese": traditional_chinese_word_dict
        }

        # 根據目前語言選擇對應字典
        # Select the dictionary based on current language
        self.language_word_dict: dict = self.choose_language_dict.get(self.language)

    def reset_language(self, language) -> None:
        """
        重設語言 (Reset the language)
        :param language: "English" 或 "Traditional_Chinese"
        """
        jeditor_logger.info(f"LanguageWrapper reset_language language: {language}")

        # 檢查輸入是否為支援的語言
        # Check if the input language is supported
        if language in [
            "English",
            "Traditional_Chinese"
        ]:
            # 更新語言與對應字典
            # Update language and corresponding dictionary
            self.language = language
            self.language_word_dict = self.choose_language_dict.get(self.language)


# 建立一個全域的 LanguageWrapper 實例
# Create a global instance of LanguageWrapper
language_wrapper = LanguageWrapper()
