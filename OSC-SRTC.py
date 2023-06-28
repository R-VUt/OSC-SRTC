import threading
import time
import sys

from modules.SRTC_Utils import load_settings, update_check
from modules.SRTC_GUI import SRTC_GUI
from modules.SRTC_Recognizer import SRTC_Recognizer
from modules.SRTC_Translator import SRTC_Translator
from modules.SRTC_Extension import SRTC_Extension
from modules.SRTC_OSC import SRTC_OSC

sys.stdout = sys.stderr = open(os.devnull, "w")  # noconsole fix

Supported_Languages: list[str] = [
    "English",
    "Korean",
    "Japanese",
    "Chinese (simplified)",
    "Chinese (traditional)",
    "French",
    "Spanish",
    "Italian",
    "Russian",
    "Ukrainian",
    "German",
    "Arabic",
    "Thai",
    "Tagalog",
    "Bahasa Malaysia",
    "Bahasa Indonesia",
    "Hindi",
    "Hebrew",
    "Turkish",
    "Portuguese",
    "Croatian",
    "Dutch",
]


mic_vad_thresold = 300
mic_min_record_time = 1.0

version = "V5"
version_RCUPD = 16

GUI: SRTC_GUI = None
Recognizer: SRTC_Recognizer = None
Translator: SRTC_Translator = None
Extension: SRTC_Extension = None
OSC: SRTC_OSC = None

is_running: bool = False
is_ptt: bool = False

Stop_Event: threading.Event = threading.Event()
PTT_End = threading.Event()
PTT_End.set()


def initialize():
    global GUI
    global Recognizer
    global Translator
    global Extension
    global OSC

    global mic_vad_thresold
    global mic_min_record_time

    GUI = SRTC_GUI()
    update_check(version_RCUPD)

    GUI.print_log("Initializing...")

    settings = load_settings()
    if settings.get("mic_vad_thresold"):
        mic_vad_thresold = settings.get("mic_vad_thresold")
    if settings.get("mic_min_record_time"):
        mic_min_record_time = settings.get("mic_min_record_time")

    Recognizer = SRTC_Recognizer(settings, GUI.print_log)
    Translator = SRTC_Translator(settings, GUI.print_log)
    Extension = SRTC_Extension(settings, GUI.print_log)
    OSC = SRTC_OSC(settings, GUI.print_log)

    OSC.recv_callback("/avatar/parameters/SRTC/TLang", OSC_SetTarget)
    OSC.recv_callback("/avatar/parameters/SRTC/SLang", OSC_SetSource)
    OSC.recv_callback("/avatar/parameters/SRTC/OnOff", OSC_SetOnOff)
    OSC.recv_callback("/avatar/parameters/SRTC/PTTMode", OSC_SetPTT)
    OSC.recv_callback("/avatar/parameters/SRTC/PTT", OSC_PTTButton)

    GUI.set_ui_text("version_label", "OSC-SRTC " + version)
    GUI.set_listbox_list("recognizer_option", Recognizer.getRegisteredRecognizers())
    GUI.set_listbox_list("translator_option", Translator.getRegisteredTranslators())
    GUI.set_listbox_list("mic_option", Recognizer.getUsableDevices())
    GUI.set_listbox_list("source_option", Supported_Languages)
    GUI.set_listbox_list("target_option", Supported_Languages)
    GUI.set_listbox_list("target2_option", ["None"] + Supported_Languages)
    GUI.set_callback("exit", on_closing)
    GUI.set_callback("option_changed", option_changed)
    GUI.set_callback("start_button", start_main_thread)

    Extension.start_server()
    OSC.start_server()

    try:
        import pyi_splash

        pyi_splash.close()
    except ImportError:
        pass

    GUI.mainloop()


def main_thread():
    GUI.clear_log()
    GUI.print_log("[Info] Main thread started.")

    tmp = GUI.get_property_value("mic_option")
    GUI.set_listbox_list("mic_option", Recognizer.getUsableDevices())
    GUI.set_property_value("mic_option", tmp)

    while not Stop_Event.is_set():
        try:
            mic = GUI.get_property_value("mic_option")
            recognizer = GUI.get_property_value("recognizer_option")
            translator = GUI.get_property_value("translator_option")
            source_lang = GUI.get_property_value("source_option")
            target_lang = GUI.get_property_value("target_option")
            target2_lang = GUI.get_property_value("target2_option")
            romaji_mode = GUI.get_property_value("romaji_mode")

            recognized = Recognizer.ListenAndRecognize(
                recognizer,
                source_lang,
                Stop_Event,
                Recognizer.getDevices().index(mic),
                is_ptt,
                PTT_End,
                mic_vad_thresold,
                mic_min_record_time,
            )
            to_send_message = ""

            if recognized != "":
                GUI.print_log("[Info] Recognized: " + recognized)

                if source_lang != target_lang:
                    GUI.print_log("[Info] Translating to Target 1...")
                    translated = Translator.Translate(
                        translator, recognized, source_lang, target_lang
                    )
                else:
                    translated = recognized

                if target_lang == "Japanese" and romaji_mode == 1:
                    translated = Translator.RomajiConvert(translated)
                GUI.print_log("[Info] Translated to Target 1: " + translated)
                to_send_message += translated

                if target2_lang != "None":
                    if source_lang != target2_lang:
                        GUI.print_log("[Info] Translating to Target 2...")
                        translated = Translator.Translate(
                            translator, recognized, source_lang, target2_lang
                        )
                    else:
                        translated = recognized

                    if target2_lang == "Japanese" and romaji_mode == 1:
                        translated = Translator.RomajiConvert(translated)
                    GUI.print_log("[Info] Translated to Target 2: " + translated)
                    to_send_message += " (" + translated + ")"

                if to_send_message != "":
                    GUI.print_log("[Info] Executing extension...")
                    to_send_message = Extension.execute_extension(to_send_message)
                    GUI.print_log("[Info] Sending message: " + to_send_message)
                    GUI.print_log(" ")
                    if to_send_message != "{Sended-Already}":
                        OSC.send("/chatbox/input", [to_send_message, True])
        except Exception:
            GUI.print_log("[Error] Could not recognize or translate.")


def start_main_thread():
    global is_running

    is_running = True

    GUI.set_ui_text("start_button", "Stop")
    GUI.set_callback("start_button", stop_main_thread)

    Stop_Event.clear()
    OSC.send("/avatar/parameters/SRTC/OnOff", True)

    is_alive = False
    for thread in threading.enumerate():
        if thread is not threading.current_thread() and thread.name == "OSC-SRTC":
            is_alive = thread.is_alive()

    if not is_alive:
        t = threading.Thread(target=main_thread, name="OSC-SRTC")  # todo
        t.daemon = True
        t.start()


def stop_main_thread():
    global is_running
    is_running = False

    GUI.set_ui_text("start_button", "Start")
    GUI.set_callback("start_button", start_main_thread)

    Stop_Event.set()
    OSC.send("/avatar/parameters/SRTC/OnOff", False)
    GUI.print_log("[Info] Stopppping...")


def on_closing():
    Stop_Event.set()
    GUI.destroy()
    os.kill(os.getpid(), 9)


def option_changed(*args):
    source_lang = GUI.get_property_value("source_option")
    target_lang = GUI.get_property_value("target_option")
    target2_lang = GUI.get_property_value("target2_option")
    selected_recognizer = GUI.get_property_value("recognizer_option")
    selected_translator = GUI.get_property_value("translator_option")

    OSC.send("/avatar/parameters/SRTC/SLang", Supported_Languages.index(source_lang))
    OSC.send("/avatar/parameters/SRTC/TLang", Supported_Languages.index(target_lang))

    if not Recognizer.isLanguageSupported(selected_recognizer, source_lang):
        GUI.print_log(
            "[Error] This recognizer "
            + selected_recognizer
            + " does not support "
            + source_lang
            + " language."
        )
        GUI.set_property_value(
            "recognizer_option", Recognizer.getRegisteredRecognizers()[0]
        )

    if not Translator.isLanguageSupported(selected_translator, source_lang):
        GUI.print_log(
            "[Error] This translator does not support " + source_lang + " language."
        )
        GUI.set_property_value(
            "translator_option", Translator.getRegisteredTranslators()[0]
        )

    if not Translator.isLanguageSupported(selected_translator, target_lang):
        GUI.print_log(
            "[Error] This translator does not support " + target_lang + " language."
        )
        GUI.set_property_value(
            "translator_option", Translator.getRegisteredTranslators()[0]
        )

    if target2_lang != "None" and not Translator.isLanguageSupported(
        selected_translator, target2_lang
    ):
        GUI.print_log(
            "[Error] This translator does not support " + target2_lang + " language."
        )
        GUI.set_property_value(
            "translator_option", Translator.getRegisteredTranslators()[0]
        )

    if is_running:
        stop_main_thread()
        time.sleep(0.2)
        start_main_thread()


# OSC Server Functions
def OSC_SetTarget(*data):
    (_, lang_id) = data

    if GUI.get_property_value("target_option") != Supported_Languages[lang_id]:
        GUI.set_property_value("target_option", Supported_Languages[lang_id])
        option_changed()


def OSC_SetSource(*data):
    (_, lang_id) = data

    if GUI.get_property_value("source_option") != Supported_Languages[lang_id]:
        GUI.set_property_value("target_option", Supported_Languages[lang_id])
        option_changed()


def OSC_SetOnOff(*data):
    (_, on_off) = data
    if on_off:
        if not is_running:
            start_main_thread()
    else:
        if is_running:
            stop_main_thread()


def OSC_SetPTT(*data):
    (_, mode) = data

    global is_ptt
    is_ptt = mode
    option_changed()


def OSC_PTTButton(*data):
    (_, ptt) = data
    if ptt:
        GUI.print_log("[INFO] PTT Start")
        PTT_End.clear()
    else:
        GUI.print_log("[INFO] PTT End")
        PTT_End.set()


# End of OSC Server Functions

if __name__ == "__main__":
    initialize()
