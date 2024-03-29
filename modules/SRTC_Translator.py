import json
from googletrans import Translator
import deepl
import requests
from pykakasi import kakasi

Google_Supported_Languages: dict[str, str] = {
    "English": "EN",
    "Korean": "ko",
    "Japanese": "JA",
    "Chinese (simplified)": "zh-CN",
    "Chinese (traditional)": "zh-TW",
    "French": "FR",
    "Spanish": "ES",
    "Italian": "IT",
    "Russian": "RU",
    "Ukrainian": "uk",
    "German": "DE",
    "Arabic": "ar",
    "Thai": "th",
    "Tagalog": "tl",
    "Bahasa Malaysia": "ms",
    "Bahasa Indonesia": "id",
    "Hindi": "hi",
    "Hebrew": "he",
    "Turkish": "tr",
    "Portuguese": "PT",
    "Croatian": "hr",
    "Dutch": "NL",
}


DeepL_Supported_Languages: dict[str, str] = {
    "English": "EN",
    "Korean": "KO",
    "Japanese": "JA",
    "Chinese (simplified)": "zh-CN",
    "French": "FR",
    "Spanish": "ES",
    "Italian": "IT",
    "Russian": "RU",
    "Ukrainian": "UK",
    "German": "DE",
    "Bahasa Indonesia": "ID",
    "Turkish": "TR",
    "Portuguese": "PT",
    "Dutch": "NL",
}

Papago_Supported_Languages: dict[str, str] = {
    "English": "en",
    "Korean": "ko",
    "Japanese": "ja",
    "Chinese (simplified)": "zh-CN",
    "Chinese (traditional)": "zh-TW",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Russian": "ru",
    "German": "de",
}


class SRTC_Translator:
    def __init__(self, settings: dict, log):
        self.__Registered_Translators: list[str] = [
            "Google Translate",
            "DeepL",
        ]  # now supports Google, DeepL, Papago
        self.__print_log = log
        self.__print_log("INFO:T", "translator_init")

        # Translator Key Settings
        if settings.get("papago_id") and settings.get("papago_secret"):
            self.__Registered_Translators.append("Papago")
            self.__papago_id = settings.get("papago_id")
            self.__papago_secret = settings.get("papago_secret")
            self.__print_log("INFO:T", "translator_init_api", api="papago")
        # ----------------------------------------------

    def __papago_translate(self, source, target, text):
        papago_url: str = "https://openapi.naver.com/v1/papago/n2mt"

        headers = {
            "X-Naver-Client-Id": self.__papago_id,
            "X-Naver-Client-Secret": self.__papago_secret,
        }
        data = {"source": source, "target": target, "text": text}
        response = requests.post(papago_url, headers=headers, data=data)
        res_code = response.status_code

        if res_code == 200:
            translated = json.loads(response.text)
            return translated["message"]["result"]["translatedText"]
        return -1

    def getRegisteredTranslators(self) -> list[str]:
        """Get a list of registered translators."""
        return self.__Registered_Translators

    @staticmethod
    def isLanguageSupported(translator: str, language: str) -> bool:
        """Check if the language is supported by the translator."""
        if translator == "Google Translate":
            return language in Google_Supported_Languages
        if translator == "DeepL":
            return language in DeepL_Supported_Languages
        if translator == "Papago":
            return language in Papago_Supported_Languages
        return False

    @staticmethod
    def RomajiConvert(text: str) -> str:
        """Convert the Japanese text to romaji."""
        converter = kakasi()

        tmp = ""
        for i in converter.convert(text):
            tmp += i["hepburn"] + " "
        return tmp

    def Translate(
        self, translator: str, text: str, source_language: str, target_language: str
    ) -> str | int:
        """Translate the text using the translator."""
        if translator == "Google Translate":
            tr = Translator()
            return tr.translate(
                text,
                src=Google_Supported_Languages[source_language],
                dest=Google_Supported_Languages[target_language],
            ).text

        if translator == "DeepL":
            return deepl.translate(
                target_language=DeepL_Supported_Languages[target_language],
                source_language=DeepL_Supported_Languages[source_language],
                text=text,
            )

        if translator == "Papago":
            return self.__papago_translate(
                Papago_Supported_Languages[source_language],
                Papago_Supported_Languages[target_language],
                text,
            )
        return -1
