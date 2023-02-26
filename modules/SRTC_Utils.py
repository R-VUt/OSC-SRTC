import sys
import os
import json

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_settings() -> dict:
    settings = {}
    try:
        with open("./api_settings.json", "r") as f:
            settings = json.load(f)
    except Exception:
        pass
    return settings

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")