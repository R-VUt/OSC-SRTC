from modules.SRTC_Utils import save_internal_settings, load_internal_settings

SUPPORTED_UI_LANGUAGES = {"English": "en", "한국어": "ko", "日本語": "ja"}


def get_saved_language():
    """
    Get saved language from internal_settings.json
    If not exists, return default language
    """
    return (
        load_internal_settings().get("ui_language") or list(SUPPORTED_UI_LANGUAGES)[0]
    )


def save_language(language: str):
    """
    Save language to internal_settings.json
    """
    settings = load_internal_settings()
    settings["ui_language"] = language
    save_internal_settings(settings)
