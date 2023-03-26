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