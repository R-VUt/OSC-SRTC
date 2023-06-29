import customtkinter as ctk
from PIL import Image
import i18n

from modules.SRTC_Utils import resource_path
from modules.SRTC_Localize import (
    SUPPORTED_UI_LANGUAGES,
    get_saved_language,
    save_language,
)


class SRTC_GUI(ctk.CTk):
    def get_property_value(self, key: str):
        """Get the value of the specified property"""
        return self._properties[key].get()

    def set_property_value(self, key: str, value):
        """Set the value of the specified property"""
        self._properties[key].set(value)

    def set_listbox_list(self, key: str, change: list):
        """Set the list of the specified listbox"""
        self._properties[key].configure(values=change)
        self._properties[key].set(change[0])

    def set_callback(self, key: str, callback):
        """Set the callback function of the specified property"""
        if key == "exit":
            self.protocol("WM_DELETE_WINDOW", callback)
        elif key == "option_changed":
            self._properties["option_changed_callback"] = callback
        else:
            self._properties[key].configure(command=callback)

    def set_ui_state(self, key: str, state: str):
        """Set the state of the specified property"""
        self._properties[key].configure(state=state)

    def set_ui_text(self, key: str, text: str):
        """Set the text of the specified property"""
        self._properties[key].configure(text=text)

    def _option_changed(self, *args):
        if "option_changed_callback" in self._properties:
            self._properties["option_changed_callback"]()

    def _option_changed_ui_language(self, *args):
        print("[Stelth] UI Language Changed")
        save_language(self._UI_Language_Selection.get())
        i18n.set("locale", SUPPORTED_UI_LANGUAGES[self._UI_Language_Selection.get()])

        self._mic_label.configure(text=i18n.t("gui_microphone"))
        self._speech_label.configure(text=i18n.t("gui_recognizer"))
        self._translator_label.configure(text=i18n.t("gui_translator"))
        self._ui_language_label.configure(text=i18n.t("gui_ui_language"))
        self._source_label.configure(text=i18n.t("gui_source_language"))
        self._target_label.configure(text=i18n.t("gui_target_language"))
        self._target2_label.configure(text=i18n.t("gui_target2_language"))
        self._Romaji_Mode_Checkbox.configure(text=i18n.t("gui_romaji_mode"))
        if self._Button_Start._text == i18n.t("gui_start_button"):
            self._Button_Start.configure(text=i18n.t("gui_stop_button"))
        else:
            self._Button_Start.configure(text=i18n.t("gui_start_button"))
        self._option_changed()

    def print_log(self, type: str, i18n_key: str, **kwargs):
        """Print the log to the log textbox"""
        if self._log_textbox is None:
            self._log_temp += "[" + type + "] " + i18n.t(i18n_key, kwargs=kwargs) + "\n"
        else:
            self._log_textbox.configure(state="normal")
            if not self._log_temp_printed:
                self._log_textbox.insert("end", self._log_temp)
                self._log_temp_printed = True

            self._log_textbox.insert(
                "end", "[" + type + "] " + i18n.t(i18n_key, kwargs=kwargs) + "\n"
            )
            self._log_textbox.see("end")
            self._log_textbox.configure(state="disabled")

    def clear_log(self):
        """Clear the log textbox"""
        self._log_textbox.configure(state="normal")
        self._log_textbox.delete("1.0", "end")
        self._log_textbox.configure(state="disabled")

    def __init__(self):
        super().__init__()

        self._log_temp = ""
        self._log_temp_printed = False

        self._properties = {}
        self.iconbitmap(resource_path("resources/logo.ico"))
        self.title("OSC-SRTC")

        self.geometry("700x490")
        self.minsize(300, 490)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._logo_image = ctk.CTkImage(
            light_image=Image.open(resource_path("resources/logo.jpg")),
            dark_image=Image.open(resource_path("resources/logo.jpg")),
            size=(150, 150),
        )

        self._navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self._navigation_frame_label = ctk.CTkLabel(
            self._navigation_frame,
            image=self._logo_image,
            compound="top",
            font=ctk.CTkFont(size=17, weight="bold"),
        )

        self._settings_tab = ctk.CTkTabview(self._navigation_frame, width=220)
        self._settings_tab.add("system")
        self._settings_tab.add("output")

        self._mic_label = ctk.CTkLabel(
            self._settings_tab.tab("system"), text=i18n.t("gui_microphone"), height=25
        )
        self._Device_Selection = ctk.CTkOptionMenu(
            self._settings_tab.tab("system"),
            width=200,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._speech_label = ctk.CTkLabel(
            self._settings_tab.tab("system"), text=i18n.t("gui_recognizer"), height=25
        )
        self._Recognizer_Selection = ctk.CTkOptionMenu(
            self._settings_tab.tab("system"),
            width=200,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._translator_label = ctk.CTkLabel(
            self._settings_tab.tab("system"), text=i18n.t("gui_translator"), height=25
        )
        self._Translator_Selection = ctk.CTkOptionMenu(
            self._settings_tab.tab("system"),
            width=200,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._ui_language_label = ctk.CTkLabel(
            self._settings_tab.tab("system"), text=i18n.t("gui_ui_language"), height=25
        )
        self._UI_Language_Selection = ctk.CTkOptionMenu(
            self._settings_tab.tab("system"),
            values=list(SUPPORTED_UI_LANGUAGES),
            width=150,
            command=self._option_changed_ui_language,
            dynamic_resizing=False,
            height=25,
        )
        self._UI_Language_Selection.set(get_saved_language())
        self._source_label = ctk.CTkLabel(
            self._settings_tab.tab("output"),
            text=i18n.t("gui_source_language"),
            height=25,
        )
        self._Source_Selection = ctk.CTkOptionMenu(
            self._settings_tab.tab("output"),
            width=150,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._target_label = ctk.CTkLabel(
            self._settings_tab.tab("output"),
            text=i18n.t("gui_target_language"),
            height=25,
        )
        self._Target_Selection = ctk.CTkOptionMenu(
            self._settings_tab.tab("output"),
            width=150,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._target2_label = ctk.CTkLabel(
            self._settings_tab.tab("output"),
            text=i18n.t("gui_target2_language"),
            height=25,
        )
        self._Target2_Selection = ctk.CTkOptionMenu(
            self._settings_tab.tab("output"),
            width=150,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._Romaji_Mode = ctk.IntVar()
        self._Romaji_Mode.set(0)
        self._Romaji_Mode_Checkbox = ctk.CTkCheckBox(
            self._settings_tab.tab("output"),
            text=i18n.t("gui_romaji_mode"),
            variable=self._Romaji_Mode,
            command=self._option_changed,
            height=25,
        )
        self._Button_Start = ctk.CTkButton(
            self._navigation_frame, text=i18n.t("gui_start_button")
        )

        self._properties["version_label"] = self._navigation_frame_label
        self._properties["mic_option"] = self._Device_Selection
        self._properties["recognizer_option"] = self._Recognizer_Selection
        self._properties["translator_option"] = self._Translator_Selection
        self._properties["source_option"] = self._Source_Selection
        self._properties["target_option"] = self._Target_Selection
        self._properties["target2_option"] = self._Target2_Selection
        self._properties["romaji_mode"] = self._Romaji_Mode
        self._properties["start_button"] = self._Button_Start

        self._home_frame = ctk.CTkFrame(self, corner_radius=0)
        self._home_frame.grid_columnconfigure(0, weight=1)
        self._home_frame.grid_rowconfigure(0, weight=1)

        self._log_textbox = ctk.CTkTextbox(
            self._home_frame, state="disabled", width=400, corner_radius=0
        )

        self._dummy_label = ctk.CTkLabel(self._navigation_frame, text="", height=1)
        self._dummy_label.pack()

        self._navigation_frame.grid(row=0, column=0, sticky="nsew")
        self._home_frame.grid(row=0, column=1, sticky="nsew")
        self._log_textbox.grid(row=0, column=0, sticky="nsew")

        self._navigation_frame_label.pack()

        self._settings_tab.pack(expand=True, fill="both")

        self._speech_label.pack()
        self._Recognizer_Selection.pack()

        self._translator_label.pack()
        self._Translator_Selection.pack()

        self._mic_label.pack()
        self._Device_Selection.pack()

        self._ui_language_label.pack()
        self._UI_Language_Selection.pack()

        self._source_label.pack()
        self._Source_Selection.pack()

        self._target_label.pack()
        self._Target_Selection.pack()

        self._target2_label.pack()
        self._Target2_Selection.pack()

        dummy_label = ctk.CTkLabel(self._settings_tab.tab("output"), text="", height=1)
        dummy_label.pack()

        self._Romaji_Mode_Checkbox.pack()

        self._Button_Start.pack(pady=10)
