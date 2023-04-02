import threading
import time
import speech_recognition as sr
from playsound import playsound

from modules.SRTC_Utils import *

# Recognizer Language Codes
Google_Supported_Languages: dict[str, str] = {"English" : "EN", "Korean" : "ko", "Japanese" : "JA", "Chinese (simplified)" : "zh-CN",
                                              "Chinese (traditional)" : "zh-TW", "French" : "FR", "Spanish" : "ES", "Italian" : "IT",
                                              "Russian" : "RU", "Ukrainian" : "uk", "German" : "DE", "Arabic" : "ar", "Thai" : "th",
                                              "Tagalog" : "tl", "Bahasa Malaysia" : "ms", "Bahasa Indonesia" : "id", "Hindi" : "hi",
                                              "Hebrew" : "he", "Turkish" : "tr", "Portuguese" : "PT", "Croatian" : "hr", "Dutch" : "NL"}
    
Azure_Supported_Languages: dict[str, str]  = {"English" : "en-US", "Korean" : "ko-KR", "Japanese" : "ja-JP", "Chinese (simplified)" : "zh-CN",
                                              "Chinese (traditional)" : "zh-TW", "French" : "fr-FR", "Spanish" : "es-ES", "Italian" : "it-IT",
                                              "Russian" : "ru-RU", "Ukrainian" : "uk-UA", "German" : "de-DE", "Arabic" : "ar-SA", "Thai" : "th-TH",
                                              "Tagalog" : "tl-PH", "Bahasa Malaysia" : "ms-MY", "Bahasa Indonesia" : "id-ID", "Hindi" : "hi-IN",
                                              "Hebrew" : "he-IL", "Turkish" : "tr-TR", "Portuguese" : "pt-PT", "Croatian" : "hr-HR", "Dutch" : "nl-NL"}

ETRI_Supported_Languages: dict[str, str]   = {"English" : "english", "Korean" : "korean", "Japanese" : "japanese", "Chinese (simplified)" : "chinese",
                                              "Chinese (traditional)" : "chinese", "Spanish" : "spanish", "Italian" : "italian", "Russian" : "russian",
                                              "Arabic" : "arabic", "Thai": "thai", "Dutch" : "dutch"}
# ----------------------------------------------

class SRecognizer:
    def __init__(self, settings: dict, log):
        self.__Registered_Recognizers: list[str] = ["Google WebSpeech"] # now supports Google, Azure, ETRI
        self.__print_log = log;
        self.__print_log("[SRecognizer][Info] Initializing Speech Recognition...")

        # Recognizer Key Settings
        if settings.get("azure_key") and settings.get("azure_location"):
            self.__Registered_Recognizers.append("Azure Speech")
            self.__azure_key = settings.get("azure_key")
            self.__azure_location = settings.get("azure_location")
            self.__print_log("[SRecognizer][Info] Azure Speech Cognitive API is enabled.")

        if settings.get("etri_key"):
            self.__Registered_Recognizers.append("ETRI Speech")
            self.__etri_key = settings.get("etri_key")
            self._print_log("[SRecognizer][Info] ETRI API is enabled.")
        # ----------------------------------------------

        self.__speech_recognition = sr.Recognizer()

    def getRegisteredRecognizers(self) -> list[str]:
        """
        Get a list of registered recognizers.
        """
        return self.__Registered_Recognizers
    
    def getDevices(self) -> list[str]:
        """
        Get a list of devices.
        """
        return sr.Microphone.list_microphone_names()
    
    def getUsableDevices(self) -> list[str]:
        """
        Get a list of working devices.
        """
        return sr.Microphone.list_usable_microphones()

    def isLanguageSupported(self, recognizer: str, language: str) -> bool:
        """
        Check if the language is supported by the recognizer.
        """
        if recognizer == "Google WebSpeech":
            return language in Google_Supported_Languages
        elif recognizer == "Azure Speech":
            return language in Azure_Supported_Languages
        elif recognizer == "ETRI Speech":
            return language in ETRI_Supported_Languages
        else:
            return False
        
        
    def Recognize(self, recognizer: str, language: str, audio: sr.AudioData) -> str:
        """
        Recognize the audio data.
        """
        if recognizer == "Google WebSpeech":
            return self.__speech_recognition.recognize_google(audio, language=Google_Supported_Languages[language])
        elif recognizer == "Azure Speech":
            return self.__speech_recognition.recognize_azure(audio, key=self.__azure_key, language=Azure_Supported_Languages[language], region=self.__azure_location)
        elif recognizer == "ETRI Speech":
            return self.__speech_recognition.recognize_etri(audio, self.__etri_key, ETRI_Supported_Languages[language])
        else:
            return ""
    
    def ListenAndRecognize(self, recognizer: str, language: str, stop_event: threading.Event(), selected_device: int = 0, is_ptt: bool = False, ptt_event: threading.Event() = None) -> str:
        """
        Listen and recognize the audio data.

        if error occurs, return empty string. 
        """
        
        r = sr.Recognizer()
        while not stop_event.is_set():
          with sr.Microphone(device_index=selected_device) as source:
              if is_ptt:
                  while ptt_event.is_set():
                      if stop_event.is_set():
                          return ""
                      time.sleep(0.1)

              playsound(resource_path("resources\\1.wav").replace("\\", "/"), block=True)
              self.__print_log("[SRecognizer][Info] Listening...")

              try:
                  if is_ptt:
                      audio = r.listen(source, timeout=20, phrase_time_limit=20, stopper=stop_event, ptt_end=ptt_event)
                  else:
                      audio = r.listen(source, timeout=20, phrase_time_limit=20, stopper=stop_event)
              except sr.WaitTimeoutError:
                  self.__print_log("[SRecognizer][Error] Timeout")
                  continue
              except sr.StopperSet:
                  self.__print_log("[SRecognizer][Info] Successfully stopped listening")
                  return ""
              
              self.__print_log("[SRecognizer][Info] Recognizing...")
              try:
                  return self.Recognize(recognizer, language, audio)
              except sr.UnknownValueError:
                  self.__print_log("[SRecognizer][Error] Unknown Value")
                  return ""
              except sr.RequestError as e:
                  self.__print_log("[SRecognizer][Error] Request Error")
                  return ""
              