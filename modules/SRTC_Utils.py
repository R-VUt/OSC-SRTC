import sys
import os
import json

default_settings = '''
{
	"osc_ip" : "127.0.0.1",
	"osc_port" : 9000,
	
	"osc_serv_ip" : "127.0.0.1",
	"osc_serv_port" : 9001,
	
	"azure_key" : "",
	"azure_location" : "",
	
	"etri_key" : "",
	
	"papago_id" : "",
	"papago_secret" : ""
}
'''

def make_default_settings():
    with open("./api_settings.json", "w") as f:
        f.write(default_settings)

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_settings() -> dict:
    settings = {}
    if not os.path.exists("./api_settings.json"):
        make_default_settings()
        
    try:
        with open("./api_settings.json", "r") as f:
            settings = json.load(f)
    except Exception:
        pass
    return settings

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def update_check(ver: int) -> None:
    import requests
    from bs4 import BeautifulSoup
    from CTkMessagebox import CTkMessagebox
    try:
        url = "https://rera-c.booth.pm/items/4217922"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        sections = soup.find_all("section")
        chk = False
        for section in sections:
            try:
                title = section.find("h2")
                if title.text == "RCUPDCHK":
                    version = section.find("p").text
                    print("[Log-Stelth] 업데이트 확인 성공: " + version)
                    if int(version) > ver:
                        msg = CTkMessagebox(title="OSC-SRTC", message="New update found! \nDo you want to check the booth page?", option_1="No", option_2="Yes", icon="question")
                        response = msg.get()
                        if response == "Yes":
                            os.startfile(url)
                    chk = True
            except Exception:
                pass
        if not chk:
            print("[Log-Stelth] 업데이트 확인 실패")
    finally:
        print("[Log-Stelth] 업데이트 확인 프로세스 종료")
