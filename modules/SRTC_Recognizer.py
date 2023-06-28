import threading
import time
import speech_recognition as sr
import pyaudio
import numpy as np

import simpleaudio as sa

from modules.SRTC_Utils import *

# Recognizer Language Codes
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

Azure_Supported_Languages: dict[str, str] = {
    "English": "en-US",
    "Korean": "ko-KR",
    "Japanese": "ja-JP",
    "Chinese (simplified)": "zh-CN",
    "Chinese (traditional)": "zh-TW",
    "French": "fr-FR",
    "Spanish": "es-ES",
    "Italian": "it-IT",
    "Russian": "ru-RU",
    "Ukrainian": "uk-UA",
    "German": "de-DE",
    "Arabic": "ar-SA",
    "Thai": "th-TH",
    "Tagalog": "tl-PH",
    "Bahasa Malaysia": "ms-MY",
    "Bahasa Indonesia": "id-ID",
    "Hindi": "hi-IN",
    "Hebrew": "he-IL",
    "Turkish": "tr-TR",
    "Portuguese": "pt-PT",
    "Croatian": "hr-HR",
    "Dutch": "nl-NL",
}

ETRI_Supported_Languages: dict[str, str] = {
    "English": "english",
    "Korean": "korean",
    "Japanese": "japanese",
    "Chinese (simplified)": "chinese",
    "Chinese (traditional)": "chinese",
    "Spanish": "spanish",
    "Italian": "italian",
    "Russian": "russian",
    "Arabic": "arabic",
    "Thai": "thai",
    "Dutch": "dutch",
}
# ----------------------------------------------


class SRTC_Recognizer:
    def __init__(self, settings: dict, log):
        self.__Registered_Recognizers: list[str] = [
            "Google WebSpeech"
        ]  # now supports Google, Azure, ETRI
        self.__print_log = log
        self.__print_log("[Recognizer][Info] Initializing Speech Recognition...")
        self.__beep_sound = sa.WaveObject.from_wave_file(
            resource_path("resources\\1.wav").replace("\\", "/")
        )

        # Recognizer Key Settings
        if settings.get("azure_key") and settings.get("azure_location"):
            self.__Registered_Recognizers.append("Azure Speech")
            self.__azure_key = settings.get("azure_key")
            self.__azure_location = settings.get("azure_location")
            self.__print_log(
                "[Recognizer][Info] Azure Speech Cognitive API is enabled."
            )

        if settings.get("etri_key"):
            self.__Registered_Recognizers.append("ETRI Speech")
            self.__etri_key = settings.get("etri_key")
            self._print_log("[Recognizer][Info] ETRI API is enabled.")
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
        if recognizer == "Azure Speech":
            return language in Azure_Supported_Languages
        if recognizer == "ETRI Speech":
            return language in ETRI_Supported_Languages
        return False

    def Recognize(self, recognizer: str, language: str, audio: sr.AudioData) -> str:
        """
        Recognize the audio data.
        """
        if recognizer == "Google WebSpeech":
            return self.__speech_recognition.recognize_google(
                audio, language=Google_Supported_Languages[language]
            )
        if recognizer == "Azure Speech":
            return self.__speech_recognition.recognize_azure(
                audio,
                key=self.__azure_key,
                language=Azure_Supported_Languages[language],
                region=self.__azure_location,
            )
        if recognizer == "ETRI Speech":
            return self.__speech_recognition.recognize_etri(
                audio, self.__etri_key, ETRI_Supported_Languages[language]
            )
        return ""

    def ListenAndRecognize(
        self,
        recognizer: str,
        language: str,
        stop_event: threading.Event(),
        selected_device: int = 0,
        is_ptt: bool = False,
        ptt_event: threading.Event() = None,
        vad_threshold: int = 300,
        min_record_time: float = 1.0,
    ) -> str:
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=selected_device,
            frames_per_buffer=CHUNK,
        )

        min_record_chunks = int(min_record_time * RATE / CHUNK)

        # playsound(resource_path("resources\\1.wav").replace("\\", "/"), block=False)
        self.__beep_sound.play()

        self.__print_log("[Recognizer][Info] Listener is ready.")

        while not stop_event.is_set():
            audio_data = stream.read(CHUNK)
            audio_data_int = np.frombuffer(audio_data, dtype=np.int16)

            if np.abs(audio_data_int).mean() > vad_threshold or (
                is_ptt and not ptt_event.is_set()
            ):
                if is_ptt:
                    while ptt_event.is_set():
                        if stop_event.is_set():
                            print("[Recognizer][Info] Stopped Listening.")
                            return ""
                        time.sleep(0.1)
                self.__print_log("[Recognizer][Info] Listening...")

                audio_buffer = [audio_data]
                vad_below_threshold = 0
                while True:
                    audio_data = stream.read(CHUNK)
                    audio_buffer.append(audio_data)
                    audio_data_int = np.frombuffer(audio_data, dtype=np.int16)

                    if np.abs(audio_data_int).mean() <= vad_threshold:
                        vad_below_threshold += 1
                        if vad_below_threshold > min_record_chunks:
                            break
                    else:
                        vad_below_threshold = 0

                audio_data = b"".join(audio_buffer)
                audio = sr.AudioData(audio_data, RATE, 2)

                self.__print_log("[Recognizer][Info] Recognizing...")
                try:
                    return self.Recognize(recognizer, language, audio)
                except sr.UnknownValueError:
                    self.__print_log(
                        "[Recognizer][Error] Unknown Value, recognizer couldn't understand the audio."
                    )
                except sr.RequestError as e:
                    self.__print_log(
                        "[Recognizer][Error] Request Error : " + e.with_traceback()
                    )

            else:
                continue
        if stop_event.is_set():
            self.__print_log("[Recognizer][Info] Stopped Listening.")

        stream.stop_stream()
        stream.close()
        p.terminate()
        return ""
