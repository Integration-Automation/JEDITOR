from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.english import english_word_dict
from je_editor.utils.multi_language.japanese import japanese_word_dict
from je_editor.utils.multi_language.locale_match import (
    language_for_locale, system_locale_name
)
from je_editor.utils.multi_language.simplified_chinese import simplified_chinese_word_dict
from je_editor.utils.multi_language.traditional_chinese import traditional_chinese_word_dict


class LanguageWrapper(object):
    """
    功能說明 (Function Description):
    - 提供一個語言包裝器，用來管理目前使用的語言與對應的字典。
    - A language wrapper to manage the current language and its corresponding dictionary.

    找不到某個鍵時會退回英文，因此翻譯還沒補齊的語言只會有幾個字是英文，而不是整
    片空白——這也讓「先加語言、再慢慢補字」變得可行。
    A key that is missing falls back to English, so a language whose translation
    is not finished shows a few English words rather than blanks, which is what
    makes it possible to add a language first and fill it in over time.
    """

    def __init__(self) -> None:
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
            "Traditional_Chinese": traditional_chinese_word_dict,
            "Simplified_Chinese": simplified_chinese_word_dict,
            "Japanese": japanese_word_dict,
        }

        # 每個語言的顯示名稱，以該語言自己的寫法呈現
        # Each language's name, written the way that language writes it
        self.display_names = {
            "English": "English",
            "Traditional_Chinese": "繁體中文",
            "Simplified_Chinese": "简体中文",
            "Japanese": "日本語",
        }

        # 根據目前語言選擇對應字典
        # Select the dictionary based on current language
        self.language_word_dict: dict = self._dictionary_for(self.language)

    def _dictionary_for(self, language: str) -> dict:
        """
        取得某個語言的字典，缺的鍵由英文補上
        The dictionary for a language, with anything missing filled in from English.

        :param language: 語言名稱 / the language's name
        :return: 可直接使用的字典 / a dictionary ready to use
        """
        chosen = self.choose_language_dict.get(language)
        if chosen is None or chosen is english_word_dict:
            return english_word_dict
        return {**english_word_dict, **chosen}

    def available_languages(self) -> list:
        """
        取得目前可用的語言
        The languages currently available.

        :return: 語言名稱，英文排在最前面 / their names, with English first
        """
        names = sorted(self.choose_language_dict)
        names.remove("English")
        return ["English", *names]

    def display_name(self, language: str) -> str:
        """
        取得語言的顯示名稱
        The name a language is shown under.

        用該語言自己的寫法，這樣看不懂目前介面語言的人也找得到自己的。
        Written the way that language writes it, so someone who cannot read the
        interface's current language can still find their own.

        :param language: 語言名稱 / the language's name
        :return: 顯示名稱 / the name to show
        """
        return self.display_names.get(language, language.replace("_", " "))

    def register_language(self, language: str, word_dict: dict,
                          display_name: str = "") -> None:
        """
        註冊一個語言（供插件使用）
        Register a language, for a plugin to add one.

        :param language: 語言名稱 / the language's name
        :param word_dict: 該語言的字典 / its dictionary
        :param display_name: 顯示名稱 / the name to show it under
        """
        self.choose_language_dict[language] = word_dict
        if display_name:
            self.display_names[language] = display_name

    def reset_language(self, language: str) -> None:
        """
        重設語言 (Reset the language)
        :param language: 任何已註冊的語言鍵 / Any registered language key
        """
        jeditor_logger.info(f"LanguageWrapper reset_language language: {language}")

        # 檢查輸入是否為支援的語言（包含插件註冊的語言）
        # Check if the input language is supported (including plugin-registered languages)
        if language in self.choose_language_dict:
            # 更新語言與對應字典
            # Update language and corresponding dictionary
            self.language = language
            self.language_word_dict = self._dictionary_for(language)


# 建立一個全域的 LanguageWrapper 實例
# Create a global instance of LanguageWrapper
language_wrapper = LanguageWrapper()


def resolve_startup_language(settings: dict) -> str:
    """
    決定啟動時要用哪個語言
    Work out which language to start in.

    使用者選過就照他選的。沒有的話照系統語系挑一個：系統已經說明了他讀哪種語言，
    一律給英文只是把這個資訊丟掉。挑到的語言會記進設定，之後就以那個為準。
    A language the user chose is used as chosen. Otherwise the system's locale
    decides: it already says which language the user reads, and defaulting to
    English throws that away. What gets picked is recorded, so from then on it is
    simply the chosen one.

    :param settings: 使用者設定 / the user settings
    :return: 語言名稱 / the language's name
    """
    chosen = settings.get("language")
    if chosen in language_wrapper.choose_language_dict:
        return chosen
    detected = language_for_locale(
        system_locale_name(), set(language_wrapper.choose_language_dict))
    settings["language"] = detected
    jeditor_logger.info(f"multi_language_wrapper picked {detected} from the system locale")
    return detected
