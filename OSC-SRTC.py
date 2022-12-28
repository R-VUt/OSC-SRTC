import json
import time
#import beautifulsoup
import bs4 as bs
import requests
from tkinter import *
import  tkinter.ttk as ttk
import os
import speech_recognition as sr
import threading
from googletrans import Translator
from pythonosc import udp_client, osc_server, dispatcher
import deepl 
import sys
import urllib
from playsound import playsound
from pykakasi import kakasi

nowversion = "10"
url = "https://rera-c.booth.pm/items/4217922"

lang_list = ["English", "Korean", "Japanese", "Chinese (simplified)", "Chinese (traditional)", "French", "Spanish", "Italian", "Russian", "Ukrainian", "German", "Arabic", "Thai", "Tagalog", "Bahasa Malaysia", "Bahasa Indonesia", "Hindi", "Hebrew", "Turkish", "Portuguese", "Croatian", "Dutch"]

lang_code = ["EN", "ko", "JA", "zh-CN","zh-TW", "FR", "ES" , "IT", "RU", "uk", "DE", "ar", "th", "tl", "ms", "id", "hi", "he", "tr", "PT", "hr", "NL"]
azure_code = ["en-US", "ko-KR", "ja-JP", "zh-CN", "zh-TW", "fr-FR", "es-ES", "it-IT", "ru-RU", "uk-UA", "de-DE", "ar-SA", "th-TH", "tl-PH", "ms-MY", "id-ID", "hi-IN", "he-IL", "tr-TR", "pt-PT", "hr-HR", "nl-NL"]
deepl_code = ["EN", "JA", "FR", "DE", "ES", "IT", "NL", "PL", "PT", "RU", "ZH"]
papago_code = ["en", "ko", "ja", "zh-CN", "zh-TW", "fr", "es", "it", "ru", "de"]
whisper_code = ["english", "korean", "japanese", "chinese", "chinese", "french", "spanish", "italian", "russian", "ukrainian", "german", "arabic", "thai", "tagalog", "malay", "indonesian", "hindi", "hebrew", "turkish", "portuguese", "croatian", "dutch"]
etri_code = ["korean", "english", "chinese", "japanese", "dutch", "spanish", "russian", "vietnamese", "arabic", "thai", "italian", "malay"]

speech_recog_list = ["Google WebSpeech"]
translator_list = ["Google Translate", "Deepl"]

azure_key = ""
azure_location = ""
papago_id = ""
papago_secret = ""
etri_key = ""
osc_ip = "127.0.0.1"
osc_port = 9000
osc_serv_ip = "127.0.0.1"
osc_serv_port = 9001

tk = None
button_stat = None
combobox = None
sourceBox = None
targetBox = None
romajiModeCheck = None
speechBox = None
translatorBox = None

romajiMode = None

onoff = False
PTTmode = False
PTT_end = threading.Event()
PTT_end.set()
stop_event = threading.Event()


converter = kakasi()

def check_update():
  try:
    source = requests.get(url).text
    soup = bs.BeautifulSoup(source, 'html.parser')

    modules = soup.find('script', id='json_modules')
    
    data = json.loads(modules.string)
    for section in data['modules']:
      if section['title'] == 'RCUPDCHK':
        print('Checking for updates...')
        print('---------------------------------')
        if section['content'] == nowversion:
            print("You are using the latest version.")
        else:
            print("There is a new version available.")
            print("Go to " + url + " to download the new version.")
        print('---------------------------------')

  except:
    print("couldn't check for updates" )

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def check_api_settings():
    global azure_key
    global azure_location
    global papago_id
    global papago_secret
    global etri_key

    global osc_ip
    global osc_port
    global osc_serv_ip
    global osc_serv_port

    if os.path.isfile("api_settings.json"):
        
        with open("./api_settings.json", "r") as f:
            api_settings = json.load(f)

            if api_settings.get("osc_ip") and api_settings.get("osc_port") and api_settings["osc_ip"] != "" and api_settings["osc_port"] != "":
                osc_ip = api_settings["osc_ip"]
                osc_port = api_settings["osc_port"]
                print('[Info] Found OSC IP and Port in api_settings.json')

            if api_settings.get("osc_serv_ip") and api_settings.get("osc_serv_port") and api_settings["osc_serv_ip"] != "" and api_settings["osc_serv_port"] != "":
                osc_serv_ip = api_settings["osc_serv_ip"]
                osc_serv_port = api_settings["osc_serv_port"]
                print('[Info] Found OSC Server IP and Port in api_settings.json')

            if api_settings.get("azure_key") and api_settings.get("azure_location") and api_settings["azure_key"] != "" and api_settings["azure_location"] != "":
                speech_recog_list.append("Azure Speech Cognitive")
                azure_key = api_settings["azure_key"]
                azure_location = api_settings["azure_location"]
                print("[Info] Found API Key from settings : Azure Speech Cognitive API is enabled")
            
            if api_settings.get("papago_id") and api_settings.get("papago_secret") and api_settings["papago_id"] != "" and api_settings["papago_secret"] != "":
                translator_list.append("Papago")
                papago_id = api_settings["papago_id"]
                papago_secret = api_settings["papago_secret"]
                print("[Info] Found API Key from settings : Papago API is enabled")

            if api_settings.get("etri_key") and api_settings["etri_key"] != "":
                speech_recog_list.append("ETRI")
                etri_key = api_settings["etri_key"]
                print("[Info] Found API Key from settings : ETRI API is enabled")

def papago_translate(source, target, text):
  encText = urllib.parse.quote(text)
  data = "source="+source+"&target="+target+"&text=" + encText
  url = "https://openapi.naver.com/v1/papago/n2mt"
  request = urllib.request.Request(url)
  request.add_header("X-Naver-Client-Id",papago_id)
  request.add_header("X-Naver-Client-Secret",papago_secret)
  response = urllib.request.urlopen(request, data=data.encode("utf-8"))
  rescode = response.getcode()
  if(rescode==200):
      response_body = response.read()
      translated = json.loads(response_body.decode('utf-8'))
      return translated['message']['result']['translatedText']
  else:
      return -1

def checkBoxChanged(*args):
    client.send_message("/avatar/parameters/SRTC/TLang", targetBox.current())
    client.send_message("/avatar/parameters/SRTC/SLang", sourceBox.current())
    
    source_lang = lang_code[sourceBox.current()]
    target_lang = lang_code[targetBox.current()]

    if target_lang.lower() == "ja":
        romajiModeCheck.config(state=NORMAL)

    if translator_list[translatorBox.current()] == "Deepl":
        

        if source_lang == "zh-CN":
            source_lang = "ZH"
        if target_lang == "zh-CN":
            target_lang = "ZH"
        
        if source_lang not in deepl_code or target_lang not in deepl_code:
            print("[Error] Not supported Language in Deepl mode")
            translatorBox.current(0)
    
    elif translator_list[translatorBox.current()] == "Papago":
        source_lang = lang_code[sourceBox.current()]
        target_lang = lang_code[targetBox.current()]

        if source_lang.lower() not in papago_code or target_lang.lower() not in papago_code:
            print("[Error] Not supported Language in Papago mode")
            translatorBox.current(0)
    
    if speech_recog_list[speechBox.current()] == "ETRI":
        if whisper_code[sourceBox.current()] not in etri_code:
            print("[Error] Not supported Language in ETRI mode")
            speechBox.current(0)

def recognize_and_send(r, audio):
    try:
        print("[Info] Recognizing...")
        if speech_recog_list[speechBox.current()] == "Google WebSpeech":
            text = r.recognize_google(audio, language=lang_code[sourceBox.current()])
        elif speech_recog_list[speechBox.current()] == "Azure Speech Cognitive":
            text = r.recognize_azure(audio, key=azure_key, location=azure_location, language=azure_code[sourceBox.current()])[0]
        elif speech_recog_list[speechBox.current()] == "ETRI":
            if whisper_code[sourceBox.current()] in etri_code:
                text = r.recognize_etri(audio, etri_key, whisper_code[sourceBox.current()])
        
        print("[Info] Recognized: " + text)
        
        if sourceBox.current() != targetBox.current():
            if translator_list[translatorBox.current()] == "Deepl":
                source_lang = lang_code[sourceBox.current()]
                target_lang = lang_code[targetBox.current()]

                if target_lang == "zh-CN":
                    target_lang = "ZH"
                if source_lang == "zh-CN":
                    source_lang = "ZH"

                text = deepl.translate(source_language=source_lang, target_language=target_lang, text=text)
            elif translator_list[translatorBox.current()] == "Papago":
                source_lang = lang_code[sourceBox.current()].lower()
                target_lang = lang_code[targetBox.current()].lower()

                text = papago_translate(source=source_lang, target=target_lang, text=text)
            elif translator_list[translatorBox.current()] == "Google Translate":
                translator = Translator()
                translated = translator.translate(text, dest=lang_code[targetBox.current()])
                text = translated.text
        
        if lang_code[targetBox.current()].lower() == "ja" and romajiMode.get() == 1:
            tmp = ""
            for i in converter.convert(text):
                tmp += i['hepburn'] + " "
            text = tmp
            
        print("[Info] Output: " + text)
        print()
        
        client.send_message("/chatbox/input", [text, True])
    except:
        print("[Err] Couldn't recognize")
        print()


def mainfunc():
    os.system("cls")
    print("[Info] OSChat-SRTC Thread started")

    r = sr.Recognizer()
    '''with sr.Microphone(device_index=combobox.current()) as source:
        print("[Info] Calibrating noise...")
        r.adjust_for_ambient_noise(source)
        print("[Info] Done")
        print("")
    '''
    while True:
        with sr.Microphone(device_index=combobox.current()) as source:
            if stop_event.is_set():
                break
            if PTTmode == True:
                while PTT_end.is_set():
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
                if stop_event.is_set():
                    break
            
            
            playsound(resource_path("resources\\1.wav").replace("\\", "/"), block=False)
            print("[Info] Listening...")
            try:
                if PTTmode == False:
                    audio = r.listen(source, timeout=20, phrase_time_limit=20, stopper=stop_event)
                else:
                    audio = r.listen(source, timeout=20, phrase_time_limit=20, stopper=stop_event, ptt_end=PTT_end)
            except sr.WaitTimeoutError:
                print("[Info] Speech Recognition Timeout")
                print("")
                continue
            except sr.StopperSet:
                print("[Info] Successfully stopped listening")
                print("")
            
            if stop_event.is_set():
                break
            recognize_and_send(r, audio)

    print("[Info] OSChat-SRTC Thread terminated")

def start():
    global onoff

    onoff = True
    button_stat.config(text="Stop", command=lambda: stop())
    stop_event.clear()
    client.send_message("/avatar/parameters/SRTC/OnOff", onoff)

    is_alive = False

    for thread in threading.enumerate():
        if thread is threading.current_thread():
            continue
        if(thread.name == "OSChat-SRTC"):
            is_alive = thread.is_alive()

    if not is_alive:
        t=threading.Thread(target=mainfunc, name="OSChat-SRTC")
        t.daemon = True
        t.start()
    

def stop():
    global onoff

    onoff = False
    button_stat.config(text="Start", command=lambda: start())

    client.send_message("/avatar/parameters/SRTC/OnOff", onoff)
    stop_event.set()
    print ('[Info] Stopping...')

def on_closing():
    stop_event.set()
    tk.destroy()
    os.kill(os.getpid(), 9)

def main_window():
    global tk
    global button_stat
    global combobox
    global sourceBox
    global targetBox
    global romajiModeCheck
    global speechBox
    global translatorBox

    global romajiMode

    tk = Tk()
    tk.iconbitmap(resource_path("resources/logo.ico"))
    tk.title("OSC-SRTC")
    tk.geometry("220x260")
    #tk.resizable(0, 0)

    mic_label = Label(tk, text="Microphone")
    combobox = ttk.Combobox(tk, height = 5,width=210, values=sr.Microphone.list_microphone_names(), state="readonly")

    speech_label = Label(tk, text="Speech Recognition")
    speechBox = ttk.Combobox(tk, height = 5,width=210, values=speech_recog_list, state="readonly")

    source_label = Label(tk, text="Source")
    sourceBox = ttk.Combobox(tk, height = 5, values=lang_list, state="readonly")

    target_label = Label(tk, text="Target")
    targetBox = ttk.Combobox(tk, height = 5, values=lang_list, state="readonly")

    sourceBox.bind("<<ComboboxSelected>>", checkBoxChanged)
    targetBox.bind("<<ComboboxSelected>>", checkBoxChanged)


    translator_label = Label(tk, text="Translator")
    translatorBox = ttk.Combobox(tk, height = 5, width=210, values=translator_list, state="readonly")

    translatorBox.bind("<<ComboboxSelected>>", checkBoxChanged)

    combobox.current(0)
    sourceBox.current(0)
    targetBox.current(0)
    speechBox.current(0)
    translatorBox.current(0)

    romajiMode = IntVar()
    romajiModeCheck = Checkbutton(tk, text="Romaji Mode (Ja)", variable=romajiMode)
    romajiModeCheck.config(state=DISABLED)

    speech_label.pack()
    speechBox.pack()

    translator_label.pack()
    translatorBox.pack()
    
    mic_label.pack()
    combobox.pack()

    source_label.pack()
    sourceBox.pack()

    target_label.pack()
    targetBox.pack()

    romajiModeCheck.pack()

    button_stat = Button(tk, text="Start", command=lambda: start())
    button_stat.pack()


    tk.protocol("WM_DELETE_WINDOW", on_closing)
    tk.mainloop()


'''
splash = Tk()
width = 400
height = 400
screen_width = splash.winfo_screenwidth()
screen_height = splash.winfo_screenheight()
x = (screen_width/2) - (width/2)
y = (screen_height/2) - (height/2)


splash.title('OSC-SRTC')
splash.geometry("%dx%d+%d+%d" % (width, height, x, y))
splash.configure(bg='gray')
splash.overrideredirect(True)

splash_image_photo = PhotoImage(resource_path("resources/logo.jpg"))
splash_image_label = Label(splash, image=splash_image_photo, width=400, height=400)
splash_image_label.pack()

splash.after(2000, lambda: main_window())
splash.after(2000, lambda: splash.destroy())
splash.mainloop()
'''

def set_target_lang(*data):
    (link, lang_id) = data

    global targetBox
    if targetBox.current() != int(lang_id):
        targetBox.current(int(lang_id))
        checkBoxChanged()

def set_source_lang(*data):
    (link, lang_id) = data

    global sourceBox
    if sourceBox.current() != int(lang_id):
        sourceBox.current(int(lang_id))
        checkBoxChanged()

def set_on_off(*data):
    (link, on_off) = data

    global now
    if on_off == True:
        if onoff == False:
            start()
    else:
        if onoff == True:
            stop()

def set_PTTmode(*data):
    (link, mode) = data

    global PTTmode
    PTTmode = mode

def set_PTT(*data):
    (link, PTT) = data

    global PTT_end
    if PTT == True:
        print("[INFO] PTT Start")
        PTT_end.clear()
    else:
        print("[INFO] PTT End")
        PTT_end.set()



check_update()
check_api_settings()

disp = dispatcher.Dispatcher()
disp.map("/avatar/parameters/SRTC/TLang", set_target_lang)
disp.map("/avatar/parameters/SRTC/SLang", set_source_lang)
disp.map("/avatar/parameters/SRTC/OnOff", set_on_off)

disp.map("/avatar/parameters/SRTC/PTTMode", set_PTTmode)
disp.map("/avatar/parameters/SRTC/PTT", set_PTT)

server = osc_server.ThreadingOSCUDPServer((osc_serv_ip, osc_serv_port), disp)
threading.Thread(target=server.serve_forever).start()

client = udp_client.SimpleUDPClient(osc_ip, osc_port)
main_window()