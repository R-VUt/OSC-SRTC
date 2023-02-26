import threading
import time
import tkinter.ttk as ttk
from tkinter import *
from pythonosc import udp_client, osc_server, dispatcher
from pykakasi import kakasi

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

TK: Tk = None
Button_Start: Button = None
Device_Selection: ttk.Combobox = None
Recognizer_Selection: ttk.Combobox = None
Translator_Selection: ttk.Combobox = None
Source_Selection: ttk.Combobox = None
Target_Selection: ttk.Combobox = None
Target2_Selection: ttk.Combobox = None

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
    if Target_Selection.current() != int(lang_id):
        Target_Selection.current(int(lang_id))
        option_changed()


def OSC_SetSource(*data):
    (link, lang_id) = data

    global Source_Selection
    if Source_Selection.current() != int(lang_id):
        Source_Selection.current(int(lang_id))
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
  OSC_Client.send_message("/avatar/parameters/SRTC/SLang", Source_Selection.current())
  OSC_Client.send_message("/avatar/parameters/SRTC/TLang", Target_Selection.current())
  
  source_lang = Supported_Languages[Source_Selection.current()]
  target_lang = Supported_Languages[Target_Selection.current()]
  target2_lang = Supported_Languages[Target2_Selection.current()-1] if Target2_Selection.current() != 0 else "None"

  if not Recognizer.isLanguageSupported(Recognizer_Selection.current(), source_lang):
    print("[Error] This recognizer does not support " + source_lang + " language.")
    Recognizer_Selection.current(0)

  if not Translator.isLanguageSupported(Translator_Selection.current(), source_lang):
    print("[Error] This translator does not support " + source_lang + " language.")
    Translator_Selection.current(0)
  
  if not Translator.isLanguageSupported(Translator_Selection.current(), target_lang):
    print("[Error] This translator does not support " + target_lang + " language.")
    Translator_Selection.current(0)

  if target2_lang != "None" and not Translator.isLanguageSupported(Translator_Selection.current(), target2_lang):
    print("[Error] This translator does not support " + target2_lang + " language.")
    Translator_Selection.current(0)
  
  if is_running:
    stop_main_thread()
    time.sleep(0.2)
    start_main_thread()

  
def main_thread():
  clear_screen()
  print("[Info] Main thread started.")

  while not Stop_Event.is_set():
    try:
      recognized = Recognizer.ListenAndRecognize(Recognizer_Selection.current(), Supported_Languages[Source_Selection.current()],
                                                Stop_Event, Device_Selection.current(), is_ptt, PTT_End)
      to_send_message = ""

      if recognized != "":
        print("[Info] Recognized: " + recognized)
        
        if Source_Selection.current() != Target_Selection.current():
          print("[Info] Translating to Target 1...")
          translated = Translator.Translate(Translator_Selection.current(), recognized, Supported_Languages[Source_Selection.current()],
                                            Supported_Languages[Target_Selection.current()])
        else:
          translated = recognized

        if Supported_Languages[Target_Selection.current()] == "Japanese" and Romaji_Mode.get() == 1:
          translated = Translator.RomajiConvert(translated)
        print("[Info] Translated to Target 1: " + translated)
        to_send_message += translated

        if Target2_Selection.current() != 0:
          if Source_Selection.current() != Target2_Selection.current()-1:

            print("[Info] Translating to Target 2...")
            translated = Translator.Translate(Translator_Selection.current(), recognized, Supported_Languages[Source_Selection.current()],
                                              Supported_Languages[Target2_Selection.current()-1])  
          else:
            translated = recognized

          if Supported_Languages[Target2_Selection.current()-1] == "Japanese" and Romaji_Mode.get() == 1:
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
  Button_Start.config(text="Stop", command=lambda: stop_main_thread())
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
  Button_Start.config(text="Start", command=lambda: start_main_thread())

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

  TK = Tk()
  TK.iconbitmap(resource_path("resources/logo.ico"))
  TK.title("OSC-SRTC")
  TK.geometry("220x300")
  # tk.resizable(0, 0)

  mic_label = Label(TK, text="Microphone")
  Device_Selection = ttk.Combobox(TK, height=5, width=210, values=Recognizer.getDevices(), state="readonly")

  speech_label = Label(TK, text="Speech Recognition")
  Recognizer_Selection = ttk.Combobox(TK, height=5, width=210, values=Recognizer.getRegisteredRecognizers(), state="readonly")

  source_label = Label(TK, text="Source")
  Source_Selection = ttk.Combobox(TK, height=5, values=Supported_Languages, state="readonly")

  target_label = Label(TK, text="Target")
  Target_Selection = ttk.Combobox(TK, height=5, values=Supported_Languages, state="readonly")

  target2_label = Label(TK, text="Target2 -> ()")
  Target2_Selection = ttk.Combobox(TK, height=5, values=["none"]+Supported_Languages, state="readonly")

  translator_label = Label(TK, text="Translator")
  Translator_Selection = ttk.Combobox(TK, height=5, width=210, values=Translator.getRegisteredTranslators(), state="readonly")
  
  Romaji_Mode = IntVar()
  romajiModeCheck = Checkbutton(TK, text="Romaji Mode (Ja)", variable=Romaji_Mode)

  Button_Start = Button(TK, text="Start", command=lambda: start_main_thread())

  Recognizer_Selection.bind("<<ComboboxSelected>>", option_changed)
  Source_Selection.bind("<<ComboboxSelected>>", option_changed)
  Target_Selection.bind("<<ComboboxSelected>>", option_changed)
  Target2_Selection.bind("<<ComboboxSelected>>", option_changed)
  Translator_Selection.bind("<<ComboboxSelected>>", option_changed)

  Device_Selection.current(0)
  Recognizer_Selection.current(0)
  Source_Selection.current(0)
  Target_Selection.current(0)
  Target2_Selection.current(0)
  Translator_Selection.current(0)


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