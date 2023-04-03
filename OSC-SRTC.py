import threading
import time
from customtkinter import *
from pythonosc import udp_client, osc_server, dispatcher

from modules.SRTC_Utils import *
from modules.SRTC_Recognizer import SRecognizer
from modules.SRTC_Translator import STranslator
from modules.SRTC_Extention import Extention_MainServer
from PIL import Image

sys.stdout = sys.stderr = open(os.devnull, 'w') # noconsole fix

Supported_Languages: list[str] = ["English", "Korean", "Japanese", "Chinese (simplified)", "Chinese (traditional)",
                       "French", "Spanish", "Italian", "Russian", "Ukrainian", "German", "Arabic", "Thai",
                       "Tagalog", "Bahasa Malaysia", "Bahasa Indonesia", "Hindi", "Hebrew", "Turkish",
                       "Portuguese", "Croatian", "Dutch"]

OSC_Send_IP = "127.0.0.1"
OSC_Send_Port = 9000
OSC_Recv_IP = "127.0.0.1"
OSC_Recv_Port = 9001
Extention_Port = 9002

log_temp = ""
log_temp_printed = False

version = "V4E"
version_RCUPD = 13

TK: CTk = None
Button_Start: CTkButton = None
Device_Selection: CTkOptionMenu = None
Recognizer_Selection: CTkOptionMenu = None
Translator_Selection: CTkOptionMenu = None
Source_Selection: CTkOptionMenu = None
Target_Selection: CTkOptionMenu = None
Target2_Selection: CTkOptionMenu = None
log_textbox: CTkTextbox = None

Romaji_Mode: IntVar = None

Recognizer: SRecognizer = None
Translator: STranslator = None

OSC_Client: udp_client.SimpleUDPClient = None
OSC_Server: osc_server.ThreadingOSCUDPServer = None
Extention_System: Extention_MainServer = None

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
        print_log("[INFO] PTT Start")
        PTT_End.clear()
    else:
        print_log("[INFO] PTT End")
        PTT_End.set()
# End of OSC Server Functions

def initialize():
  global Recognizer
  global Translator

  global OSC_Client
  global OSC_Server
  global Extention_System

  global OSC_Send_IP
  global OSC_Send_Port
  global OSC_Recv_IP
  global OSC_Recv_Port
  global Extention_Port

  print_log("Initializing...")

  settings = load_settings()

  if settings.get("osc_ip"):
    OSC_Send_IP = settings.get("osc_ip")
  if settings.get("osc_port"):
    OSC_Send_Port = settings.get("osc_port")
  if settings.get("osc_serv_ip"):
    OSC_Recv_IP = settings.get("osc_serv_ip")
  if settings.get("osc_serv_port"):
    OSC_Recv_Port = settings.get("osc_serv_port")
  
  if settings.get("extention_port"):
    Extention_Port = settings.get("extention_port")

  Recognizer = SRecognizer(settings, print_log)
  Translator = STranslator(settings, print_log)

  disp = dispatcher.Dispatcher()
  disp.map("/avatar/parameters/SRTC/TLang", OSC_SetTarget)
  disp.map("/avatar/parameters/SRTC/SLang", OSC_SetSource)
  disp.map("/avatar/parameters/SRTC/OnOff", OSC_SetOnOff)

  disp.map("/avatar/parameters/SRTC/PTTMode", OSC_SetPTT)
  disp.map("/avatar/parameters/SRTC/PTT", OSC_PTTButton)

  OSC_Server = osc_server.ThreadingOSCUDPServer((OSC_Recv_IP, OSC_Recv_Port), disp)
  threading.Thread(target=OSC_Server.serve_forever).start()

  OSC_Client = udp_client.SimpleUDPClient(OSC_Send_IP, OSC_Send_Port)

  Extention_System = Extention_MainServer(OSC_Recv_IP, Extention_Port, print_log)
  Extention_System.start_server()

def option_changed(*args):
  OSC_Client.send_message("/avatar/parameters/SRTC/SLang", Supported_Languages.index(Source_Selection.get()))
  OSC_Client.send_message("/avatar/parameters/SRTC/TLang", Supported_Languages.index(Target_Selection.get()))
  
  source_lang = Source_Selection.get()
  target_lang = Target_Selection.get()
  target2_lang = Target2_Selection.get()

  if not Recognizer.isLanguageSupported(Recognizer_Selection.get(), source_lang):
    print_log("[Error] This recognizer does not support " + source_lang + " language.")
    Recognizer_Selection.set(Recognizer.getRegisteredRecognizers()[0])

  if not Translator.isLanguageSupported(Translator_Selection.get(), source_lang):
    print_log("[Error] This translator does not support " + source_lang + " language.")
    Translator_Selection.set(Translator.getRegisteredTranslators()[0])
  
  if not Translator.isLanguageSupported(Translator_Selection.get(), target_lang):
    print_log("[Error] This translator does not support " + target_lang + " language.")
    Translator_Selection.set(Translator.getRegisteredTranslators()[0])

  if target2_lang != "None" and not Translator.isLanguageSupported(Translator_Selection.get(), target2_lang):
    print_log("[Error] This translator does not support " + target2_lang + " language.")
    Translator_Selection.set(Translator.getRegisteredTranslators()[0])
  
  if is_running:
    stop_main_thread()
    time.sleep(0.2)
    start_main_thread()

  
def main_thread():
  #clear_screen()
  clear_log()
  print_log("[Info] Main thread started.")

  while not Stop_Event.is_set():
    try:
      recognized = Recognizer.ListenAndRecognize(Recognizer_Selection.get(), Source_Selection.get(),
                                                Stop_Event, Recognizer.getDevices().index(Device_Selection.get()), is_ptt, PTT_End)
      to_send_message = ""

      if recognized != "":
        print_log("[Info] Recognized: " + recognized)
        
        if Source_Selection.get() != Target_Selection.get():
          print_log("[Info] Translating to Target 1...")
          translated = Translator.Translate(Translator_Selection.get(), recognized, Source_Selection.get(),
                                            Target_Selection.get())
        else:
          translated = recognized

        if Target_Selection.get() == "Japanese" and Romaji_Mode.get() == 1:
          translated = Translator.RomajiConvert(translated)
        print_log("[Info] Translated to Target 1: " + translated)
        to_send_message += translated

        if Target2_Selection.get() != "None":
          if Source_Selection.get() != Target2_Selection.get():

            print_log("[Info] Translating to Target 2...")
            translated = Translator.Translate(Translator_Selection.get(), recognized, Source_Selection.get(),
                                              Target2_Selection.get())  
          else:
            translated = recognized

          if Target2_Selection.get() == "Japanese" and Romaji_Mode.get() == 1:
            translated = Translator.RomajiConvert(translated)
          print_log("[Info] Translated to Target 2: " + translated)
          to_send_message += " (" + translated + ")"
          

        if to_send_message != "":
          print_log("[Info] Sending message: " + to_send_message)
          print_log(" ")
          to_send_message = Extention_System.execute_extention(to_send_message)
          if to_send_message != "{Sended-Already}":
            OSC_Client.send_message("/chatbox/input", [to_send_message, True])
    except:
      print_log("[Error] Could not recognize or translate.")

          
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
  print_log('[Info] Stopppping...')


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
  global log_textbox

  global Romaji_Mode

  TK = CTk()
  TK.iconbitmap(resource_path("resources/logo.ico"))
  TK.title("OSC-SRTC")
  TK.geometry("700x480")
  
  TK.grid_rowconfigure(0, weight=1)
  TK.grid_columnconfigure(1, weight=1)
  # tk.resizable(0, 0)

  logo_image = CTkImage(light_image=Image.open(resource_path("resources/logo.jpg")), dark_image=Image.open(resource_path("resources/logo.jpg")), size=(50, 50))

  navigation_frame = CTkFrame(TK, corner_radius=0)
  navigation_frame.grid(row=0, column=0, sticky="nsew")

  navigation_frame_label = CTkLabel(navigation_frame, text="  OSC-SRTC " + version, image=logo_image,
                                                             compound="left", font=CTkFont(size=17, weight="bold"))

  mic_label = CTkLabel(navigation_frame, text="Microphone")
  Device_Selection = CTkOptionMenu(navigation_frame, values=Recognizer.getUsableDevices(), command=option_changed)

  speech_label = CTkLabel(navigation_frame, text="Speech Recognition")
  Recognizer_Selection = CTkOptionMenu(navigation_frame, width=200, values=Recognizer.getRegisteredRecognizers(), command=option_changed)

  source_label = CTkLabel(navigation_frame, text="Source")
  Source_Selection = CTkOptionMenu(navigation_frame, width=100, values=Supported_Languages, command=option_changed)

  target_label = CTkLabel(navigation_frame, text="Target")
  Target_Selection = CTkOptionMenu(navigation_frame, width=100, values=Supported_Languages, command=option_changed)

  target2_label = CTkLabel(navigation_frame, text="Target2 -> ()")
  Target2_Selection = CTkOptionMenu(navigation_frame, width=100, values=["None"]+Supported_Languages, command=option_changed)

  translator_label = CTkLabel(navigation_frame, text="Translator")
  Translator_Selection = CTkOptionMenu(navigation_frame, width=200, values=Translator.getRegisteredTranslators(), command=option_changed)
  
  Romaji_Mode = IntVar()
  romajiModeCheck = CTkCheckBox(navigation_frame, text="Romaji Mode (Ja)", variable=Romaji_Mode)

  Button_Start = CTkButton(navigation_frame, text="Start", command=lambda: start_main_thread())

  home_frame = CTkFrame(TK, corner_radius=0)
  home_frame.grid_columnconfigure(0, weight=1)
  home_frame.grid_rowconfigure(0, weight=1)
  home_frame.grid(row=0, column=1, sticky="nsew")

  log_textbox = CTkTextbox(home_frame, state="disabled", width=400, corner_radius=0)
  log_textbox.grid(row=0, column=0, sticky="nsew")
  
  Device_Selection.set(Recognizer.getDevices()[0])
  Recognizer_Selection.set(Recognizer.getRegisteredRecognizers()[0])
  Source_Selection.set(Supported_Languages[0])
  Target_Selection.set(Supported_Languages[0])
  Target2_Selection.set("None")
  Translator_Selection.set(Translator.getRegisteredTranslators()[0])

  dummy_label = CTkLabel(navigation_frame, text="", height=1)
  dummy_label.pack()
  navigation_frame_label.pack()
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
  print_log("[Info] UI Initialized.")
  
  update_check(version_RCUPD)
  TK.mainloop()

def print_log(text):
  global log_temp
  global log_temp_printed

  if log_textbox is None:
    log_temp += text + "\n"
  else:
    
    log_textbox.configure(state="normal")
    if not log_temp_printed:
      log_textbox.insert("end", log_temp)
      log_temp_printed = True
       
    log_textbox.insert("end", text + "\n")
    log_textbox.see("end")
    log_textbox.configure(state="disabled")
def clear_log():
  log_textbox.configure(state="normal")
  log_textbox.delete("1.0", "end")
  log_textbox.configure(state="disabled")

if __name__ == "__main__":
  initialize()
  main_window()