import threading
import time
from customtkinter import *
from pythonosc import udp_client, osc_server

from modules.SRTC_Utils import *
from modules.SRTC_Recognizer import SRecognizer
from modules.SRTC_Translator import STranslator


Supported_Languages: list[str] = ["English", "Korean", "Japanese", "Chinese (simplified)", "Chinese (traditional)",
                       "French", "Spanish", "Italian", "Russian", "Ukrainian", "German", "Arabic", "Thai",
                       "Tagalog", "Bahasa Malaysia", "Bahasa Indonesia", "Hindi", "Hebrew", "Turkish",
                       "Portuguese", "Croatian", "Dutch"]

OSC_Send_IP = "127.0.0.1"
OSC_Send_Port = 9000
OSC_Recv_IP = "127.0.0.1"
OSC_Recv_Port = 9001

TK: CTk = None
Button_Start: CTkButton = None
Device_Selection: CTkOptionMenu = None
Recognizer_Selection: CTkOptionMenu = None
Translator_Selection: CTkOptionMenu = None
Source_Selection: CTkOptionMenu = None
Target_Selection: CTkOptionMenu = None
Target2_Selection: CTkOptionMenu = None

Romaji_Mode: IntVar = None

Recognizer: SRecognizer = None
Translator: STranslator = None

OSC_Client: udp_client.SimpleUDPClient = None
OSC_Server: osc_server.ThreadingOSCUDPServer = None

is_running: bool = False
is_ptt: bool = False

Stop_Event: threading.Event = threading.Event()
PTT_End = threading.Event()
PTT_End.set()

# OSC Server Functions
def OSC_SetTarget(*data):
    (link, lang_id) = data

    global Target_Selection
    if Target_Selection.get() != Supported_Languages[lang_id]:
        Target_Selection.set(Supported_Languages[lang_id])
        option_changed()


def OSC_SetSource(*data):
    (link, lang_id) = data

    global Source_Selection
    if Source_Selection.get() != Supported_Languages[lang_id]:
        Source_Selection.set(Supported_Languages[lang_id])
        option_changed()


def OSC_SetOnOff(*data):
    (link, on_off) = data

    global is_running
    if on_off:
        if not is_running:
            start_main_thread()
    else:
        if is_running:
            stop_main_thread()


def OSC_SetPTT(*data):
    (link, mode) = data

    global is_ptt
    is_ptt = mode
    option_changed()



def OSC_PTTButton(*data):
    (link, ptt) = data

    global PTT_End
    if ptt:
        print("[INFO] PTT Start")
        PTT_End.clear()
    else:
        print("[INFO] PTT End")
        PTT_End.set()
# End of OSC Server Functions

def initialize():
  global Recognizer
  global Translator

  global OSC_Client
  global OSC_Server

  global OSC_Send_IP
  global OSC_Send_Port
  global OSC_Recv_IP
  global OSC_Recv_Port

  print("OSC-SRTC v4")
  print("Initializing...")

  settings = load_settings()

  if settings.get("osc_ip"):
    OSC_Send_IP = settings.get("osc_ip")
  if settings.get("osc_port"):
    OSC_Send_Port = settings.get("osc_port")
  if settings.get("osc_serv_ip"):
    OSC_Recv_IP = settings.get("osc_serv_ip")
  if settings.get("osc_serv_port"):
    OSC_Recv_Port = settings.get("osc_serv_port")

  Recognizer = SRecognizer(settings)
  Translator = STranslator(settings)

  OSC_Client = udp_client.SimpleUDPClient(OSC_Send_IP, OSC_Send_Port)

def option_changed(*args):
  OSC_Client.send_message("/avatar/parameters/SRTC/SLang", Supported_Languages.index(Source_Selection.get()))
  OSC_Client.send_message("/avatar/parameters/SRTC/TLang", Supported_Languages.index(Target_Selection.get()))
  
  source_lang = Source_Selection.get()
  target_lang = Target_Selection.get()
  target2_lang = Target2_Selection.get()

  if not Recognizer.isLanguageSupported(Recognizer_Selection.get(), source_lang):
    print("[Error] This recognizer does not support " + source_lang + " language.")
    Recognizer_Selection.set(Recognizer.getRegisteredRecognizers()[0])

  if not Translator.isLanguageSupported(Translator_Selection.get(), source_lang):
    print("[Error] This translator does not support " + source_lang + " language.")
    Translator_Selection.set(Translator.getRegisteredTranslators()[0])
  
  if not Translator.isLanguageSupported(Translator_Selection.get(), target_lang):
    print("[Error] This translator does not support " + target_lang + " language.")
    Translator_Selection.set(Translator.getRegisteredTranslators()[0])

  if target2_lang != "None" and not Translator.isLanguageSupported(Translator_Selection.get(), target2_lang):
    print("[Error] This translator does not support " + target2_lang + " language.")
    Translator_Selection.set(Translator.getRegisteredTranslators()[0])
  
  if is_running:
    stop_main_thread()
    time.sleep(0.2)
    start_main_thread()

  
def main_thread():
  clear_screen()
  print("[Info] Main thread started.")

  while not Stop_Event.is_set():
    try:
      recognized = Recognizer.ListenAndRecognize(Recognizer_Selection.get(), Source_Selection.get(),
                                                Stop_Event, Recognizer.getDevices().index(Device_Selection.get()), is_ptt, PTT_End)
      to_send_message = ""

      if recognized != "":
        print("[Info] Recognized: " + recognized)
        
        if Source_Selection.get() != Target_Selection.get():
          print("[Info] Translating to Target 1...")
          translated = Translator.Translate(Translator_Selection.get(), recognized, Source_Selection.get(),
                                            Target_Selection.get())
        else:
          translated = recognized

        if Target_Selection.get() == "Japanese" and Romaji_Mode.get() == 1:
          translated = Translator.RomajiConvert(translated)
        print("[Info] Translated to Target 1: " + translated)
        to_send_message += translated

        if Target2_Selection.get() != "None":
          if Source_Selection.get() != Target2_Selection.get():

            print("[Info] Translating to Target 2...")
            translated = Translator.Translate(Translator_Selection.get(), recognized, Source_Selection.get(),
                                              Target2_Selection.get())  
          else:
            translated = recognized

          if Target2_Selection.get() == "Japanese" and Romaji_Mode.get() == 1:
            translated = Translator.RomajiConvert(translated)
          print("[Info] Translated to Target 2: " + translated)
          to_send_message += " (" + translated + ")"
          

        if to_send_message != "":
          print("[Info] Sending message: " + to_send_message)
          print(" ")
          OSC_Client.send_message("/chatbox/input", [to_send_message, True])
    except:
      print("[Error] Could not recognize or translate.")

          
def start_main_thread():
  global is_running

  is_running = True
  Button_Start.configure(text="Stop", command=lambda: stop_main_thread())
  Stop_Event.clear()
  OSC_Client.send_message("/avatar/parameters/SRTC/OnOff", True)

  is_alive = False

  for thread in threading.enumerate():
    if thread is not threading.current_thread() and thread.name == "OSC-SRTC":
      is_alive = thread.is_alive()

  if not is_alive:
    t = threading.Thread(target=main_thread, name="OSC-SRTC") #todo
    t.daemon = True
    t.start()

def stop_main_thread():
  global is_running

  is_running = False
  Button_Start.configure(text="Start", command=lambda: start_main_thread())

  Stop_Event.set()
  OSC_Client.send_message("/avatar/parameters/SRTC/OnOff", False)
  print('[Info] Stopppping...')


def on_closing():
  Stop_Event.set()
  TK.destroy()
  os.kill(os.getpid(), 9)

def main_window():
  global TK
  global Button_Start
  global Device_Selection
  global Recognizer_Selection
  global Translator_Selection
  global Source_Selection
  global Target_Selection
  global Target2_Selection

  global Romaji_Mode

  TK = CTk()
  TK.iconbitmap(resource_path("resources/logo.ico"))
  TK.title("OSC-SRTC")
  TK.geometry("220x400")
  # tk.resizable(0, 0)

  mic_label = CTkLabel(TK, text="Microphone")
  Device_Selection = CTkOptionMenu(TK, values=Recognizer.getUsableDevices(), command=option_changed)

  speech_label = CTkLabel(TK, text="Speech Recognition")
  Recognizer_Selection = CTkOptionMenu(TK, width=200, values=Recognizer.getRegisteredRecognizers(), command=option_changed)

  source_label = CTkLabel(TK, text="Source")
  Source_Selection = CTkOptionMenu(TK, width=100, values=Supported_Languages, command=option_changed)

  target_label = CTkLabel(TK, text="Target")
  Target_Selection = CTkOptionMenu(TK, width=100, values=Supported_Languages, command=option_changed)

  target2_label = CTkLabel(TK, text="Target2 -> ()")
  Target2_Selection = CTkOptionMenu(TK, width=100, values=["None"]+Supported_Languages, command=option_changed)

  translator_label = CTkLabel(TK, text="Translator")
  Translator_Selection = CTkOptionMenu(TK, width=200, values=Translator.getRegisteredTranslators(), command=option_changed)
  
  Romaji_Mode = IntVar()
  romajiModeCheck = CTkCheckBox(TK, text="Romaji Mode (Ja)", variable=Romaji_Mode)

  Button_Start = CTkButton(TK, text="Start", command=lambda: start_main_thread())


  Device_Selection.set(Recognizer.getDevices()[0])
  Recognizer_Selection.set(Recognizer.getRegisteredRecognizers()[0])
  Source_Selection.set(Supported_Languages[0])
  Target_Selection.set(Supported_Languages[0])
  Target2_Selection.set("None")
  Translator_Selection.set(Translator.getRegisteredTranslators()[0])


  speech_label.pack()
  Recognizer_Selection.pack()

  translator_label.pack()
  Translator_Selection.pack()

  mic_label.pack()
  Device_Selection.pack()

  source_label.pack()
  Source_Selection.pack()

  target_label.pack()
  Target_Selection.pack()

  target2_label.pack()
  Target2_Selection.pack()


  romajiModeCheck.pack()

  Button_Start.pack()

  TK.protocol("WM_DELETE_WINDOW", on_closing)
  TK.mainloop()


if __name__ == "__main__":
  initialize()
  main_window()