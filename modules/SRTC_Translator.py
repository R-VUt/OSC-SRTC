from googletrans import Translator
import deepl
import urllib
from pykakasi import kakasi

Google_Supported_Languages: dict[str, str] = {"English" : "EN", "Korean" : "ko", "Japanese" : "JA", "Chinese (simplified)" : "zh-CN",
                                              "Chinese (traditional)" : "zh-TW", "French" : "FR", "Spanish" : "ES", "Italian" : "IT",
                                              "Russian" : "RU", "Ukrainian" : "uk", "German" : "DE", "Arabic" : "ar", "Thai" : "th",
                                              "Tagalog" : "tl", "Bahasa Malaysia" : "ms", "Bahasa Indonesia" : "id", "Hindi" : "hi",
                                              "Hebrew" : "he", "Turkish" : "tr", "Portuguese" : "PT", "Croatian" : "hr", "Dutch" : "NL"}
    

DeepL_Supported_Languages: dict[str, str] = {"English" : "EN", "Korean" : "KO", "Japanese" : "JA", "Chinese (simplified)" : "zh-CN",
                                            "French" : "FR", "Spanish" : "ES", "Italian" : "IT",
                                            "Russian" : "RU", "Ukrainian" : "UK", "German" : "DE",
                                            "Bahasa Indonesia" : "ID", "Turkish" : "TR", "Portuguese" : "PT", "Dutch" : "NL"}

Papago_Supported_Languages: dict[str, str] = {"English" : "en", "Korean" : "ko", "Japanese" : "ja", "Chinese (simplified)" : "zh-CN",
                                            "Chinese (traditional)" : "zh-TW", "French" : "fr", "Spanish" : "es", "Italian" : "it",
                                            "Russian" : "ru", "German" : "de"}

class STranslator:
    def __init__(self, settings: dict, log):
        self.__Registered_Translators: list[str] = ["Google Translate", "DeepL"] # now supports Google, DeepL, Papago
        self.__print_log = log
        self.__print_log("[Translator][Info] Initializing Translator...")

        # Translator Key Settings
        if settings.get("papago_id") and settings.get("papago_secret"):
            self.__Registered_Translators.append("Papago")
            self.__papago_id = settings.get("papago_id")
            self.__papago_secret = settings.get("papago_secret")
            self.__print_log("[Recognizer][Info] Azure Speech Cognitive API is enabled.")
        # ----------------------------------------------

    def __papago_translate(self, source, target, text):
      encText = urllib.parse.quote(text)
      data: str = "source=" + source + "&target=" + target + "&text=" + encText
      papago_url: str = "https://openapi.naver.com/v1/papago/n2mt"
      request = urllib.request.Request(papago_url)
      request.add_header("X-Naver-Client-Id", self.__papago_id)
      request.add_header("X-Naver-Client-Secret", self.__papago_secret)
      response = urllib.request.urlopen(request, data=data.encode("utf-8"))
      res_code = response.getcode()
      if res_code == 200:
          response_body = response.read()
          translated = json.loads(response_body.decode('utf-8'))
          return translated['message']['result']['translatedText']
      else:
          return -1

    def getRegisteredTranslators(self) -> list[str]:
        """
        Get a list of registered translators.
        """
        return self.__Registered_Translators

    def isLanguageSupported(self, translator: str, language: str) -> bool:
        """
        Check if the language is supported by the translator.
        """
        if translator == "Google Translate":
            return language in Google_Supported_Languages
        elif translator == "DeepL":
            return language in DeepL_Supported_Languages
        elif translator == "Papago":
            return language in Papago_Supported_Languages
        else:
            return False
    
    def RomajiConvert(self, text: str) -> str:  
        converter = kakasi()

        tmp = ""
        for i in converter.convert(text):
          tmp += i['hepburn'] + " "
        return tmp

    def Translate(self, translator: str, text: str, source_language: str, target_language: str) -> str | int:
        """
        Translate the text using the translator.
        """
        if translator == "Google Translate":
            tr = Translator()
            return tr.translate(text, src=Google_Supported_Languages[source_language], dest=Google_Supported_Languages[target_language]).text
        
        elif translator == "DeepL":
            return deepl.translate(target_language=DeepL_Supported_Languages[target_language], source_language=DeepL_Supported_Languages[source_language], text=text)
        
        elif translator == "Papago":
            return self.__papago_translate(Papago_Supported_Languages[source_language], Papago_Supported_Languages[target_language], text)
        else:
            return -1