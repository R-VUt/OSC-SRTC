import sys
import os
import json
import webbrowser

import requests
from bs4 import BeautifulSoup
from CTkMessagebox import CTkMessagebox

default_settings = """
{
	"osc_ip" : "127.0.0.1",
	"osc_port" : 9000,

	"osc_serv_ip" : "127.0.0.1",
	"osc_serv_port" : 9001,
    "extension_port" : 9002,

    "mic_vad_thresold" : 300,
    "mic_min_record_time" : 1.0,

	"azure_key" : "",
	"azure_location" : "",

	"etri_key" : "",

	"papago_id" : "",
	"papago_secret" : ""
}
"""


def make_default_settings():
    """Make default settings file"""
    with open("./api_settings.json", "w") as f:
        f.write(default_settings)


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_settings() -> dict:
    """Load settings from api_settings.json"""
    settings = {}
    if not os.path.exists("./api_settings.json"):
        make_default_settings()

    try:
        with open("./api_settings.json", "r") as f:
            settings = json.load(f)
    except Exception:
        return {}
    return settings


def clear_screen():
    """ Clear console (not used)"""
    os.system("cls" if os.name == "nt" else "clear")


def update_check(ver: int) -> None:
    """Check for program updates"""
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
                    print("[Log-Stelth] Update Check Success: " + version)
                    if int(version) > ver:
                        msg = CTkMessagebox(
                            title="OSC-SRTC",
                            message="New update found! \nDo you want to check the booth page?",
                            option_1="No",
                            option_2="Yes",
                            icon="question",
                        )
                        response = msg.get()
                        if response == "Yes":
                            webbrowser.open(url, new=0, autoraise=True)
                    chk = True
            except Exception:
                chk = False
        if not chk:
            print("[Log-Stelth] Update Check Failed")
    finally:
        print("[Log-Stelth] Update Check process finished")
