from customtkinter import *
from PIL import Image

from modules.SRTC_Utils import resource_path


class SRTC_GUI(CTk):
    def get_property_value(self, key: str):
        return self._properties[key].get()

    def set_property_value(self, key: str, value):
        self._properties[key].set(value)

    def set_listbox_list(self, key: str, list: list):
        self._properties[key].configure(values=list)
        self._properties[key].set(list[0])

    def set_callback(self, key: str, callback):
        if key == "exit":
            self.protocol("WM_DELETE_WINDOW", callback)
        elif key == "option_changed":
            self._properties["option_changed_callback"] = callback
        else:
            self._properties[key].configure(command=callback)

    def set_ui_state(self, key: str, state: str):
        self._properties[key].configure(state=state)

    def set_ui_text(self, key: str, text: str):
        self._properties[key].configure(text=text)

    def _option_changed(self, *args):
        if "option_changed_callback" in self._properties:
            self._properties["option_changed_callback"]()

    def print_log(self, text):
        if self._log_textbox is None:
            self._log_temp += text + "\n"
        else:
            self._log_textbox.configure(state="normal")
            if not self._log_temp_printed:
                self._log_textbox.insert("end", self._log_temp)
                self._log_temp_printed = True

            self._log_textbox.insert("end", text + "\n")
            self._log_textbox.see("end")
            self._log_textbox.configure(state="disabled")

    def clear_log(self):
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

        self._logo_image = CTkImage(
            light_image=Image.open(resource_path("resources/logo.jpg")),
            dark_image=Image.open(resource_path("resources/logo.jpg")),
            size=(150, 150),
        )

        self._navigation_frame = CTkFrame(self, corner_radius=0)
        self._navigation_frame_label = CTkLabel(
            self._navigation_frame,
            image=self._logo_image,
            compound="top",
            font=CTkFont(size=17, weight="bold"),
        )

        self._settings_tab = CTkTabview(self._navigation_frame, width=220)
        self._settings_tab.add("system")
        self._settings_tab.add("output")

        self._mic_label = CTkLabel(
            self._settings_tab.tab("system"), text="Microphone", height=25
        )
        self._Device_Selection = CTkOptionMenu(
            self._settings_tab.tab("system"),
            width=200,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._speech_label = CTkLabel(
            self._settings_tab.tab("system"), text="Speech Recognition", height=25
        )
        self._Recognizer_Selection = CTkOptionMenu(
            self._settings_tab.tab("system"),
            width=200,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._translator_label = CTkLabel(
            self._settings_tab.tab("system"), text="Translator", height=25
        )
        self._Translator_Selection = CTkOptionMenu(
            self._settings_tab.tab("system"),
            width=200,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._source_label = CTkLabel(
            self._settings_tab.tab("output"), text="Source", height=25
        )
        self._Source_Selection = CTkOptionMenu(
            self._settings_tab.tab("output"),
            width=150,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._target_label = CTkLabel(
            self._settings_tab.tab("output"), text="Target", height=25
        )
        self._Target_Selection = CTkOptionMenu(
            self._settings_tab.tab("output"),
            width=150,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._target2_label = CTkLabel(
            self._settings_tab.tab("output"), text="Target2", height=25
        )
        self._Target2_Selection = CTkOptionMenu(
            self._settings_tab.tab("output"),
            width=150,
            command=self._option_changed,
            dynamic_resizing=False,
            height=25,
        )
        self._Romaji_Mode = IntVar()
        self._Romaji_Mode.set(0)
        self._Romaji_Mode_Checkbox = CTkCheckBox(
            self._settings_tab.tab("output"),
            text="Romaji Mode",
            variable=self._Romaji_Mode,
            command=self._option_changed,
            height=25,
        )
        self._Button_Start = CTkButton(self._navigation_frame, text="Start")

        self._properties["version_label"] = self._navigation_frame_label
        self._properties["mic_option"] = self._Device_Selection
        self._properties["recognizer_option"] = self._Recognizer_Selection
        self._properties["translator_option"] = self._Translator_Selection
        self._properties["source_option"] = self._Source_Selection
        self._properties["target_option"] = self._Target_Selection
        self._properties["target2_option"] = self._Target2_Selection
        self._properties["romaji_mode"] = self._Romaji_Mode
        self._properties["start_button"] = self._Button_Start

        self._home_frame = CTkFrame(self, corner_radius=0)
        self._home_frame.grid_columnconfigure(0, weight=1)
        self._home_frame.grid_rowconfigure(0, weight=1)

        self._log_textbox = CTkTextbox(
            self._home_frame, state="disabled", width=400, corner_radius=0
        )

        self._dummy_label = CTkLabel(self._navigation_frame, text="", height=1)
        self._dummy_label.pack()

        self._navigation_frame.grid(row=0, column=0, sticky="nsew")
        self._home_frame.grid(row=0, column=1, sticky="nsew")
        self._log_textbox.grid(row=0, column=0, sticky="nsew")

        self._navigation_frame_label.pack()

        self._settings_tab.pack(expand=True, fill="both")

        dummy_label = CTkLabel(self._settings_tab.tab("system"), text="", height=1)
        dummy_label.pack()

        self._speech_label.pack()
        self._Recognizer_Selection.pack()

        self._translator_label.pack()
        self._Translator_Selection.pack()

        self._mic_label.pack()
        self._Device_Selection.pack()

        self._source_label.pack()
        self._Source_Selection.pack()

        self._target_label.pack()
        self._Target_Selection.pack()

        self._target2_label.pack()
        self._Target2_Selection.pack()

        dummy_label = CTkLabel(self._settings_tab.tab("output"), text="", height=1)
        dummy_label.pack()

        self._Romaji_Mode_Checkbox.pack()

        self._Button_Start.pack(pady=10)
