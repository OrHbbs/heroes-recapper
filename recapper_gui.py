import datetime
import json
import threading
import os
import shutil
import time
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import sv_ttk

from custom_hovertip import CustomTooltipLabel
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
from sortedcontainers import SortedDict
from tkinter import messagebox

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import utils
import database
# import player_stats

import pprint

__version__ = "0.6.0"


class RecapperGui:
    recapper_dir = os.path.join(os.getenv('LOCALAPPDATA'), "Heroes Recapper")

    # todo check if there's a better way to do this (dev vs build difference in paths)
    if os.path.exists("images/not-found.png"):
        dist_prefix = ""
    else:
        dist_prefix = "_internal/"

    selected_match = None

    def __init__(self, root):

        os.makedirs(self.recapper_dir, exist_ok=True)

        self.bg_img = None
        self.tree = None

        if os.path.isfile(f"{self.recapper_dir}/temp_hero_table.json"):
            # edge case handling: if temp_hero_table.json exists, then app was unexpectedly closed last time
            shutil.copy(f"{self.recapper_dir}/temp_hero_table.json", f"{self.recapper_dir}/hero_table.json")

        try:
            with open(f"{self.recapper_dir}/replay_data.json", 'r') as f:
                temp = utils.load_partial_json(f"{self.recapper_dir}/replay_data.json")
                self.sorted_data = temp['sorted_data']
                self.end_position = temp['end_position']

                shutil.copy(f"{self.recapper_dir}/hero_table.json", f"{self.recapper_dir}/temp_hero_table.json")

                print(f"replays: {len(self.sorted_data)}")
        except FileNotFoundError:
            self.sorted_data = SortedDict(lambda x: -x)
            self.end_position = 0

            with open(f"{self.recapper_dir}/temp_hero_table.json", 'w') as f:
                empty_hero_table = utils.create_empty_hero_table()
                json.dump(empty_hero_table, f)

        self.inner_frame = None
        self.inner_frame_id = None
        self.notebook = None
        self.scrollbar = None
        self.button = None
        self.label = None
        self.settings_is_open = False
        self.settings = self.load_settings()
        self.watch_path_var = tk.StringVar(value=self.settings.get("replay_path", ""))

        self.observer = None  # used for watchdog process

        self.tab_replays = None
        self.tab_match_details = None
        self.tab_hero_stats = None
        self.tab_player_stats = None

        self.tab_replays_filters = {
            'mode': 'all',
            'maps': 'all',
            'names': ['any'] * 10,
            'heroes': ['any'] * 10,
        }

        self.mode_var = None
        self.map_var = None

        # self.player_stats = player_stats.PlayerStats(self.recapper_dir)

        self.root = root
        self.hero_table = None

        sv_ttk.set_theme("dark")

        self.root.title(f"Heroes Recapper {__version__}")
        self.root.geometry("850x700")

        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        root.resizable(False, True)

        self.create_widgets()

    def on_closing(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?\nYour changes will be saved."):
            dat = dict(self.sorted_data)

            with open(f"{self.recapper_dir}/replay_data.json", "w") as f:
                json.dump(dat, f)

            if os.path.isfile(f"{self.recapper_dir}/temp_hero_table.json"):
                os.remove(f"{self.recapper_dir}/temp_hero_table.json")

            print("Closing Heroes Recapper")
            root.destroy()

    def create_widgets(self):
        self.create_menu()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_replays = TabReplays(self.notebook, self.sorted_data, self.notebook)
        self.tab_match_details = TabMatchDetails(self.notebook)
        self.tab_hero_stats = TabHeroStats(self.notebook, self.sorted_data)
        self.tab_player_stats = TabPlayerStats(self.notebook, self.sorted_data)

        self.notebook.add(self.tab_replays.frame, text="Replays")
        self.notebook.add(self.tab_match_details.frame, text="Match Details")
        self.notebook.add(self.tab_hero_stats.frame, text="Hero Stats")
        self.notebook.add(self.tab_player_stats.frame, text="Player Stats")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_selected)

        style = ttk.Style()
        style.configure("Treeview", rowheight=40)

        # self.select_directory(self.settings['replay_path'])

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Replay", command=self.select_replay)
        file_menu.add_command(label="Select Directory", command=self.select_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit Without Saving", command=self.exit_without_saving)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change Settings", command=self.open_settings_menu)

        # about_menu = tk.Menu(menu_bar, tearoff=0)
        # menu_bar.add_cascade(label="About", menu=about_menu)
        # about_menu.add_cascade(label="About")
        #
        # help_menu = tk.Menu(menu_bar, tearoff=0)
        # menu_bar.add_cascade(label="Help", menu=help_menu)
        # help_menu.add_command(label="quick guide", command=self.open_help_menu)

    def on_tab_selected(self, event):
        selected_tab = event.widget.select()
        selected_tab_widget = self.notebook.nametowidget(selected_tab)

        if selected_tab_widget.winfo_id() == self.tab_match_details.frame.winfo_id():
            self.tab_match_details.refresh_tables()

        elif selected_tab_widget.winfo_id() == self.tab_hero_stats.frame.winfo_id():
            self.tab_hero_stats.refresh_tables()

    def exit_without_saving(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit \nwithout saving changes?"):
            print("exiting without saving")

            try:
                shutil.copy(f"{self.recapper_dir}/temp_hero_table.json", f"{self.recapper_dir}/hero_table.json")
                os.remove(f"{self.recapper_dir}/temp_hero_table.json")
            except FileNotFoundError:
                print("temp_hero_table.json not found")
                os.remove(f"{self.recapper_dir}/hero_table.json")
                pass

        root.destroy()

    def show_loading_screen(self):
        self.loading_label = tk.Label(self.root, text="Loading...", font=("Segoe UI", 16))
        self.loading_label.pack(pady=20)
        self.root.update_idletasks()

    def hide_loading_screen(self):
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()
            delattr(self, 'loading_label')
        self.root.update_idletasks()

    def select_replay(self):
        path = [tk.filedialog.askopenfilename(filetypes=[("Storm Replay Files", "*.StormReplay")])]

        self.process_sorted_replays(paths=path)

    def select_directory(self, file_path = None):
        if file_path is None:
            file_path = tk.filedialog.askdirectory()

        if not file_path:
            print("invalid file path")
            return

        self.settings["replay_path"] = file_path
        self.watch_path_var.set(file_path)

        # stops observing if user selects a new directory
        if self.observer:
            self.observer.stop()
            self.observer.join()

        paths = []
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.endswith(".StormReplay"):
                    paths.append(os.path.join(root, file))

        start = time.time()
        self.show_loading_screen()
        thread = threading.Thread(target=self.process_sorted_replays, args=(paths,))
        thread.start()

        print(f"processing time: {time.time() - start}")
        self.hide_loading_screen()

        self.start_watching_directory(file_path)

    def process_sorted_replays(self, paths: list[str]):
        self.root.config(cursor='wait')

        database.add_to_container_and_update_tables(
            paths=paths,
            sorted_dict=self.sorted_data,
            recapper_dir=self.recapper_dir,
            hero_table=self.hero_table,
            p_stats=self.player_stats
        )
        self.tab_replays.update_replay_count()
        self.tab_replays.refresh_rows()
        self.root.update_idletasks()

        self.root.config(cursor='')

    def start_watching_directory(self, directory):
        event_handler = ReplayHandler(self.process_sorted_replays)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=directory, recursive=False)
        self.observer.start()

    def stop_watching_directory(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def load_settings(self):
        default_settings = {
            "replay_path": "",
            "low_memory_mode": False,
            "session_recap_mode": False,
            "auto_process": True
        }

        try:
            with open(os.path.join(self.recapper_dir, "settings.txt"), 'r') as f:
                for line in f:
                    key, value = line.strip().split("=", 1)
                    if key in default_settings:
                        if value.lower() in ["true", "false"]:
                            value = value.lower() == "true"
                        default_settings[key] = value
            return default_settings
        except FileNotFoundError:
            return default_settings

    def open_settings_menu(self):
        if self.settings_is_open:
            root.bell()
            return
        self.settings_is_open = True

        settings_window = tk.Toplevel(self.notebook)
        settings_window.title("Settings")

        settings_window.geometry("700x500")

        settings_canvas = tk.Canvas(settings_window, relief=tk.SUNKEN)
        settings_canvas.pack(fill=tk.BOTH, expand=True)

        # replay path
        watch_path_frame = tk.Frame(settings_canvas)
        watch_path_frame.pack(pady=10, padx=10, fill=tk.X)

        path_label = ttk.Label(watch_path_frame, text="File path to watch replays for:")
        path_label.pack(side=tk.LEFT, padx=5)

        self.watch_path_var = tk.StringVar(value=self.settings.get("replay_path", ""))
        path_entry = ttk.Entry(watch_path_frame, textvariable=self.watch_path_var, state="readonly", width=50)
        path_entry.pack(side=tk.LEFT, padx=5)

        select_path_button = ttk.Button(watch_path_frame, text="Select Directory", command=self.select_directory)
        select_path_button.pack(side=tk.LEFT, padx=5)

        # low memory mode
        low_memory_frame = tk.Frame(settings_canvas)
        low_memory_frame.pack(pady=10, padx=10, fill=tk.X)

        self.low_memory_var = tk.BooleanVar(value=self.settings.get("low_memory_mode", False))
        low_memory_checkbox = ttk.Checkbutton(low_memory_frame, text="Low memory mode",
                                              variable=self.low_memory_var)
        low_memory_checkbox.pack(side=tk.LEFT, padx=5)

        CustomTooltipLabel(low_memory_checkbox,
                                                text="Turns off background images for maps in order to save memory. (not functional yet)",
                                                hover_delay=300,
                                                justify="center",
                                                background="#1c1c1c",
                                                foreground="white",
                                                border=1,
                                                relief='groove')

        # session recap mode
        session_recap_frame = tk.Frame(settings_canvas)
        session_recap_frame.pack(pady=10, padx=10, fill=tk.X)

        self.session_recap_var = tk.BooleanVar(value=self.settings.get("session_recap_mode", False))
        session_recap_checkbox = ttk.Checkbutton(session_recap_frame, text="Session Recap Mode",
                                                 variable=self.session_recap_var)
        session_recap_checkbox.pack(side=tk.LEFT, padx=5)

        CustomTooltipLabel(session_recap_checkbox,
                           text="Only show games that were played this session. (not functional yet)",
                           hover_delay=300,
                           justify="center",
                           background="#1c1c1c",
                           foreground="white",
                           border=1,
                           relief='groove')

        # automatically process replays
        auto_process_frame = tk.Frame(settings_canvas)
        auto_process_frame.pack(pady=10, padx=10, fill=tk.X)

        self.auto_process_var = tk.BooleanVar(value=self.settings.get("auto_process", True))
        auto_process_checkbox = ttk.Checkbutton(auto_process_frame, text="Auto Process Replays",
                                                 variable=self.auto_process_var)
        auto_process_checkbox.pack(side=tk.LEFT, padx=5)

        CustomTooltipLabel(auto_process_checkbox,
                           text="Automatically process replays in the provided directory when opening Heroes Recapper. (not functional yet)",
                           hover_delay=300,
                           justify="center",
                           background="#1c1c1c",
                           foreground="white",
                           border=1,
                           relief='groove')

        # save and cancel buttons
        buttons_frame = tk.Frame(settings_canvas)
        buttons_frame.pack(pady=20)

        save_button = ttk.Button(buttons_frame, text="Save", command=lambda: self.save_settings(settings_window))
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = ttk.Button(buttons_frame, text="Cancel", command=settings_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)

        settings_window.protocol("WM_DELETE_WINDOW", lambda: self.close_settings(settings_window))

    def save_settings(self, window):
        self.settings["replay_path"] = self.watch_path_var.get()
        self.settings["low_memory_mode"] = self.low_memory_var.get()
        self.settings["session_recap_mode"] = self.session_recap_var.get()
        self.settings['auto_process'] = self.auto_process_var.get()

        print("saving")
        print(self.settings)

        if not os.path.exists(self.recapper_dir):
            os.makedirs(self.recapper_dir)

        with open(os.path.join(self.recapper_dir, "settings.txt"), 'w') as f:
            for key, value in self.settings.items():
                f.write(f"{key}={value}\n")

        self.close_settings(window)

    def close_settings(self, window):
        self.settings_is_open = False
        window.destroy()

    def open_help_menu(self):
        pass


class ReplayHandler(FileSystemEventHandler):
    def __init__(self, process_replay_callback):
        super().__init__()
        self.process_replay_callback = process_replay_callback

    def on_created(self, event):
        if event.src_path.endswith(".StormReplay"):
            self.process_replay_callback([event.src_path])


class TabReplays:
    def __init__(self, parent, sorted_data, tabs):
        self.replays_canvas = None
        self.frame = tk.Frame(parent)
        self.limit = 10
        self.sorted_data = sorted_data
        self.tabs = tabs
        self.hero_icon_cache = {}
        self.party_cache = {}
        self.bg_image_cache = {}

        self.replay_count = len(sorted_data)

        self.replay_count_var = tk.StringVar()
        self.replay_count_var.set(f"Processed Replays: {len(self.sorted_data)}")

        self.replay_filters = {
            'mode': 'all',
            'maps': 'all',
            'names': ['any'] * 10,
            'heroes': ['any'] * 10,
        }

        self.create_widgets()

    def create_widgets(self):
        filters_frame = ttk.Frame(self.frame)
        filters_frame.pack(pady=10, padx=10, fill=tk.X)

        # game mode filters
        modes = ['All', 'Storm League', 'Quick Match', 'Aram']
        mode_label = ttk.Label(filters_frame, text='Game Mode:')
        mode_label.grid(row=0, column=4, padx=10, pady=5)

        self.mode_var = tk.StringVar(value='All')
        mode_combobox = ttk.Combobox(filters_frame, textvariable=self.mode_var, values=modes, state="readonly")
        mode_combobox.grid(row=0, column=5, padx=10, pady=5)

        # map filters
        maps = list(utils.map_ids.values())
        maps.insert(0, 'All')

        map_label = ttk.Label(filters_frame, text='Map:')
        map_label.grid(row=0, column=8, padx=10, pady=5)
        self.map_var = tk.StringVar(value='All')
        map_combobox = ttk.Combobox(filters_frame, textvariable=self.map_var, values=maps, state="readonly")
        map_combobox.grid(row=0, column=9, padx=10, pady=5)

        # button to open players and heroes filters

        heroes_label = ttk.Label(filters_frame, text='Players & Heroes: ')
        heroes_label.grid(row=0, column=10)
        heroes_button = ttk.Button(filters_frame, text='Set', command=self.open_advanced_filters)
        heroes_button.grid(row=0, column=11, columnspan=2, pady=10)

        num_replays_label = ttk.Label(filters_frame, textvariable=self.replay_count_var)
        num_replays_label.grid(row=2, column=5)

        # button to apply filters
        filter_button = ttk.Button(filters_frame, text='Apply Filters', command=self.apply_filters, cursor='hand2')
        filter_button.grid(row=2, column=8, columnspan=2, pady=10)

        # button for limit per page
        limit_label = ttk.Label(filters_frame, text='Limit: ')
        limit_label.grid(row=2, column=10)
        self.limit_var = tk.IntVar(value=self.limit)
        limit_combobox = ttk.Combobox(filters_frame, textvariable=self.limit_var, values=[5, 10, 25, 50, 100], state="readonly", width=3)
        limit_combobox.grid(row=2, column=11, pady=10)

        self.replays_canvas = tk.Canvas(self.frame, relief=tk.SUNKEN)
        self.replays_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.replays_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.replays_canvas.configure(yscrollcommand=scrollbar.set, yscrollincrement=328)

        self.inner_frame = ttk.Frame(self.replays_canvas)
        self.inner_frame.bind("<Configure>",
                              lambda e: self.replays_canvas.configure(scrollregion=self.replays_canvas.bbox("all")))

        self.inner_frame_id = self.replays_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.replays_canvas.bind("<Configure>", self.on_canvas_configure)

        for i in range(min(self.limit, self.replay_count)):
            self.create_row(match_data=database.get_nth_value(self.sorted_data, i))

    def update_replay_count(self):
        self.replay_count = len(self.sorted_data)
        self.replay_count_var.set(f"Processed Replays: {self.replay_count}")

    def apply_filters(self):
        self.replay_filters['mode'] = self.mode_var.get()
        self.replay_filters['maps'] = self.map_var.get()
        self.limit = self.limit_var.get()

        filtered_data = []

        print(f"num_replays: {self.replay_count}")

        i = 0
        while len(filtered_data) < self.limit and i != self.replay_count:
            match_data = database.get_nth_value(self.sorted_data, i)
            i += 1

            # filter by game mode
            if not (self.replay_filters['mode'] == 'All' or
                    utils.clean_string(self.replay_filters['mode']) == utils.clean_string(match_data['gameMode'])):
                continue

            # filter by map
            if not (self.replay_filters['maps'] == 'All' or
                    utils.clean_string(self.replay_filters['maps']) == utils.clean_string(match_data['map'])):
                continue

            # filter by player names and heroes
            player_match = True
            hero_match = True

            for j in range(10):
                target_name = self.replay_filters['names'][j]
                target_hero = self.replay_filters['heroes'][j]

                if target_name != 'any' or target_hero != 'any':
                    name_hero_pair_found = False

                    for k in range(1, 11):
                        player_key = f"{k}_name"
                        hero_key = f"{k}_hero"

                        if target_name != 'any' and target_hero != 'any':
                            # both player and hero must match
                            if utils.clean_string(match_data[player_key]) == target_name and utils.clean_string(
                                    match_data[hero_key]) == target_hero:
                                name_hero_pair_found = True
                                break
                        elif target_name != 'any':
                            # only player must match
                            if utils.clean_string(match_data[player_key]) == target_name:
                                name_hero_pair_found = True
                                break
                        elif target_hero != 'any':
                            # only hero must match
                            if utils.clean_string(match_data[hero_key]) == target_hero:
                                name_hero_pair_found = True
                                break

                    if not name_hero_pair_found:
                        player_match = False
                        hero_match = False
                        break

            if player_match and hero_match:
                filtered_data.append(match_data)

            # stop if we reach the end of the sorted_data
            if i >= len(self.sorted_data):
                break

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for j in range(min(self.limit, len(filtered_data))):
            self.create_row(match_data=filtered_data[j])

        # todo show the winrates of row that was filtered for

    def clear_filters(self):
        self.replay_filters = {
            'mode': 'all',
            'maps': 'all',
            'players': ['any'] * 10,
            'heroes': ['any'] * 10,
        }

    def open_advanced_filters(self):
        advanced_window = tk.Toplevel(self.frame)
        advanced_window.title("Advanced Filters")

        ttk.Label(advanced_window, text="Player").grid(row=0, column=0, padx=10, pady=5)
        ttk.Label(advanced_window, text="Hero").grid(row=0, column=1, padx=10, pady=5)

        heroes = list(utils.hero_ids.values())

        self.advanced_name_vars = []
        self.advanced_hero_vars = []

        for i in range(10):
            current_name = self.replay_filters['names'][i] if self.replay_filters['names'][i] != 'any' else ''
            current_hero = self.replay_filters['heroes'][i] if self.replay_filters['heroes'][
                                                                   i] != 'any' else 'Select a Hero'

            # Player Entry
            name_var = tk.StringVar(value=current_name)
            name_entry = ttk.Entry(advanced_window, textvariable=name_var)
            name_entry.grid(row=i + 1, column=0, padx=10, pady=5)
            self.advanced_name_vars.append(name_var)

            # Hero Combobox
            hero_var = tk.StringVar(value=current_hero)
            hero_combobox = ttk.Combobox(advanced_window, textvariable=hero_var, values=heroes, state="readonly")
            hero_combobox.grid(row=i + 1, column=1, padx=10, pady=5)
            hero_combobox.configure(height=10)
            self.advanced_hero_vars.append(hero_var)

        apply_button = ttk.Button(advanced_window, text='Save Filters',
                                  command=lambda: self.save_and_close_advanced_filters(advanced_window))
        apply_button.grid(row=11, column=0, padx=10, pady=10)

        reset_button = ttk.Button(advanced_window, text='Reset Fields', command=self.confirm_reset_fields)
        reset_button.grid(row=11, column=1, padx=10, pady=10)

    def save_and_close_advanced_filters(self, advanced_window):
        self.save_advanced_filters()
        advanced_window.destroy()

    def save_advanced_filters(self):
        for i in range(10):
            name_value = self.advanced_name_vars[i].get().strip().lower()
            hero_value = self.advanced_hero_vars[i].get().strip().lower()

            self.replay_filters['names'][i] = name_value if name_value else 'any'
            self.replay_filters['heroes'][i] = hero_value if hero_value and hero_value != 'select a hero' else 'any'

    def confirm_reset_fields(self):
        answer = tk.messagebox.askyesno("Reset Fields",
                                        "Are you sure you want to reset all fields to their default values?")
        if answer:
            self.reset_fields()

    def reset_fields(self):
        # reset to default
        for i in range(10):
            self.advanced_name_vars[i].set('')
            self.advanced_hero_vars[i].set('Select a Hero')

        self.replay_filters['names'] = ['any'] * 10
        self.replay_filters['heroes'] = ['any'] * 10

    def on_canvas_configure(self, event):
        # resizes the subcanvas
        canvas_width = event.width - 10
        self.replays_canvas.itemconfig(self.inner_frame_id, width=canvas_width)

    def create_row(self, match_data):
        row_height = 350
        row_width = 700

        bg_img_src = f"{RecapperGui.dist_prefix}images/{utils.clean_entity_name(match_data['map'])}.png"

        if bg_img_src not in self.bg_image_cache:
            try:
                original_bg_img = Image.open(bg_img_src)

                bg_img = original_bg_img.resize((row_width, row_height), Image.LANCZOS)
                darkened_img = ImageEnhance.Brightness(bg_img).enhance(0.5)

                processed_img = ImageTk.PhotoImage(darkened_img)

                self.bg_image_cache[bg_img_src] = processed_img
            except Exception as e:
                print(f"Image for {bg_img_src} not found or error: {e}")
                processed_img = None
        else:
            processed_img = self.bg_image_cache[bg_img_src]

        sub_frame = tk.Frame(self.inner_frame, bd=2, relief="solid", height=row_height)
        sub_frame.pack(pady=10, fill=tk.X, expand=True)

        sub_canvas = tk.Canvas(sub_frame, height=300, cursor="hand2")
        sub_canvas.pack(fill=tk.BOTH, expand=True)

        if processed_img:
            self.bg_img_id = sub_canvas.create_image(0, 0, anchor="nw", image=processed_img)
            sub_canvas.image = processed_img

        if match_data['1_result'] == 1:
            left_color = utils.color_consts["dark_blue"]
            right_color = utils.color_consts["light_red"]
        else:
            left_color = utils.color_consts["light_blue"]
            right_color = utils.color_consts["dark_red"]

        sub_canvas.create_rectangle(0, 0, 105, row_height, fill=left_color, outline="")
        sub_canvas.create_rectangle(row_width, 0, row_width + 105, row_height, fill=right_color, outline="")

        for i in range(5):
            x_pos = 25
            y_pos = 15 + (i * 55)
            self.create_hero_icon(sub_canvas, match_data, i, x_pos, y_pos)

        for i in range(5, 10):
            x_pos = row_width + 25
            y_pos = 15 + ((i - 5) * 55)
            self.create_hero_icon(sub_canvas, match_data, i, x_pos, y_pos)

        text_id = sub_canvas.create_text(400, 10, text=f"\n"
                                                       f"{match_data['date']}\n"
                                                       f"{match_data['gameMode']}: {match_data['map']}\n"
                                                       f"{str(datetime.timedelta(seconds=int(match_data['duration']) - 45))}\n"
                                                       f"{utils.get_winner(match_data['1_result'])}\n"
                                                       f"{self.add_row_text(match_data['1_name'], match_data['6_name'])}"
                                                       f"{self.add_row_text(match_data['2_name'], match_data['7_name'])}"
                                                       f"{self.add_row_text(match_data['3_name'], match_data['8_name'])}"
                                                       f"{self.add_row_text(match_data['4_name'], match_data['9_name'])}"
                                                       f"{self.add_row_text(match_data['5_name'], match_data['10_name'])}",
                                         fill="white", font=("Segoe UI", 15, "bold"), justify="center", anchor="n")

        sub_canvas.bind("<Button-1>", lambda e, match=match_data: self.set_selected_match(match))

    def add_row_text(self, name1, name2):
        spacing = " " * int(30-len(name1)-len(name2))
        return f"{name1}{spacing}{name2}\n"

    def refresh_rows(self):

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for i in range(min(self.limit, self.replay_count)):
            self.create_row(match_data=database.get_nth_value(self.sorted_data, i))

    def set_selected_match(self, match):
        if RecapperGui.selected_match != match:
            RecapperGui.selected_match = match

        self.tabs.select(1)  # setting selected tab to "Match Details"

    def create_hero_icon(self, canvas, match_data, index, x_pos, y_pos):
        hero_name = utils.clean_entity_name(match_data[f"{index + 1}_hero"])
        border_color = "blue" if index < 5 else "red"

        if hero_name not in self.hero_icon_cache:
            image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"
            img = draw_image(image_path=image_path, shape="square")
            self.hero_icon_cache[hero_name] = img
        else:
            img = self.hero_icon_cache[hero_name]

        image_button = tk.Button(canvas, highlightcolor=border_color, image=img,
                                 command=lambda hero=hero_name: self.on_hero_click(hero), borderwidth='2')
        image_button.image = img

        canvas.create_window(x_pos, y_pos, anchor='nw', window=image_button)

        party_number = match_data.get(f"{index + 1}_party")

        if party_number > 0:
            if party_number not in self.party_cache:
                overlay_image_path = f"{RecapperGui.dist_prefix}images/party-{party_number}.png"
                overlay_img = Image.open(overlay_image_path).resize((20, 20), Image.LANCZOS)
                overlay_img = ImageTk.PhotoImage(overlay_img)
                self.party_cache[party_number] = overlay_img
            else:
                overlay_img = self.party_cache[party_number]

            overlay_label = tk.Label(canvas, image=overlay_img, borderwidth=0)
            overlay_label.image = overlay_img

            overlay_x_pos = x_pos + img.width() if index <= 4 else x_pos - 15
            overlay_y_pos = y_pos + 17

            canvas.create_window(overlay_x_pos, overlay_y_pos, anchor='nw', window=overlay_label)

        CustomTooltipLabel(image_button,
                           text=match_data[f"{index + 1}_name"],
                           hover_delay=300,
                           justify="center",
                           background="#1c1c1c",
                           foreground="white",
                           border=1,
                           relief='groove')

    def reposition_red_icons(self, canvas, window_id, index, y_pos):
        canvas_width = canvas.winfo_width()

        icon_width = 50
        icon_spacing = 60
        icon_start_red_x = canvas_width - (icon_spacing * (10 - index)) + (icon_spacing - icon_width) // 2

        canvas.coords(window_id, icon_start_red_x, y_pos)

    def on_hero_click(self, hero_name):
        print(f"Hero clicked: {hero_name}")


class TabMatchDetails:
    def __init__(self, parent):
        self.hero_images = None
        self.score_subframe = None
        self.score_sort_state = {"column": None, "ascending": False}
        self.extras_sort_state = {"column": None, "ascending": False}
        self.score_tree = None
        self.match_details_canvas = None
        self.toggle_talent_button = None
        self.toggle_extras_button = None
        self.talent_viewer_is_open = False
        self.extras_viewer_is_open = False

        self.left_color = None
        self.right_color = None
        self.left_font_color = None
        self.right_font_color = None

        self.frame = tk.Frame(parent)

        self.match_details_canvas = tk.Canvas(self.frame, relief=tk.SUNKEN)
        self.match_details_canvas.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()

    def create_widgets(self):

        if RecapperGui.selected_match is not None:

            if RecapperGui.selected_match['1_result'] == 1:
                self.left_color = utils.color_consts['dark_blue']
                self.right_color = utils.color_consts['light_red']
                self.left_font_color = utils.color_consts['black']
                self.right_font_color = utils.color_consts['white']
            else:
                self.left_color = utils.color_consts['light_blue']
                self.right_color = utils.color_consts['dark_red']
                self.left_font_color = utils.color_consts['white']
                self.right_font_color = utils.color_consts['black']

            self.create_score_table()

            self.toggle_talent_button = ttk.Button(self.match_details_canvas,
                                                   text="Show Talents",
                                                   command=self.open_talent_viewer,
                                                   cursor='hand2')
            self.toggle_talent_button.pack(pady=5)

            self.toggle_extras_button = ttk.Button(self.match_details_canvas,
                                                   text="Show Advanced Stats",
                                                   command=self.open_extras_viewer,
                                                   cursor='hand2')
            self.toggle_extras_button.pack(pady=5)
        else:

            label = tk.Label(self.match_details_canvas, text="Select a match in the Replays tab to view match details")
            label.pack(pady=20, padx=20)

    def create_score_table(self):

        match_data = RecapperGui.selected_match

        if match_data is None:
            return

        label = tk.Label(self.match_details_canvas, text=f"{match_data.get('date')}\n"
                                                         f"{match_data.get('gameMode')}: {match_data.get('map')}\n"
                                                         f"{str(datetime.timedelta(seconds=int(match_data.get('duration')) - 45))}\n"
                                                         f"{utils.get_winner(match_data.get('1_result'))}\n"
                         )
        label.pack(pady=20, padx=20)

        columns = ["Number", "Player", "Acc. Level", "Hero", "Kills", "Assists", "Deaths", "Hero Dmg", "Siege Dmg",
                   "Healing", "Dmg Taken", "XP"]
        column_widths = [5, 80, 5, 60, 5, 5, 5, 30, 30, 30, 30, 20]

        self.score_subframe = tk.Frame(self.match_details_canvas)
        self.score_subframe.pack(fill=tk.BOTH, expand=True)

        self.score_tree = ttk.Treeview(self.score_subframe, columns=columns, show="tree headings")
        self.score_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.score_tree.bind('<Button-1>', lambda event, tree=self.score_tree: prevent_resize(event, tree))
        self.score_tree.bind('<Motion>', lambda event, tree=self.score_tree: prevent_resize(event, tree))

        for col, width in zip(columns, column_widths):
            self.score_tree.heading(col, text=col,
                                    command=lambda _col=col: sort_by_column(col=_col, tab_tree=self.score_tree,
                                                                            tab_sort_state=self.score_sort_state))
            self.score_tree.column(col, anchor="center", width=width, )

        self.hero_images = {}

        self.score_tree.tag_configure('blue_row', background=self.left_color, foreground=self.left_font_color)
        self.score_tree.tag_configure('red_row', background=self.right_color, foreground=self.right_font_color)

        for i in range(1, 11):  # assuming 10 players
            prefix = f"{i}_"
            hero_name = utils.clean_entity_name(match_data.get(f"{prefix}hero"))
            row = [
                i,
                match_data.get(f"{prefix}battletag"),
                match_data.get(f"{prefix}accountLevel"),
                match_data.get(f"{prefix}hero", ""),
                match_data.get(f"{prefix}SoloKill", 0),
                match_data.get(f"{prefix}Assists", 0),
                match_data.get(f"{prefix}Deaths", 0),
                match_data.get(f"{prefix}HeroDamage", 0),
                match_data.get(f"{prefix}SiegeDamage", 0),
                match_data.get(f"{prefix}Healing", 0),
                match_data.get(f"{prefix}DamageTaken", 0),
                match_data.get(f"{prefix}ExperienceContribution", 0)
            ]

            image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"

            img = draw_image(image_path, border_width=0, size=40)
            self.hero_images[hero_name] = img

            if i <= 5:
                self.score_tree.insert("", tk.END, text='', values=row, image=self.hero_images[hero_name],
                                       tags=('blue_row',))
            else:
                self.score_tree.insert("", tk.END, text='', values=row, image=self.hero_images[hero_name],
                                       tags=('red_row',))

            self.score_tree.heading('#0', text='Icon', anchor='center')
            self.score_tree.column('#0', width=20)

        self.match_details_canvas.update_idletasks()

    def open_talent_viewer(self):
        if self.talent_viewer_is_open:
            root.bell()
            return
        self.talent_viewer_is_open = True

        talent_window = tk.Toplevel(self.frame)
        talent_window.title("Talents")

        talent_window.geometry("1425x425")

        talent_canvas = tk.Canvas(talent_window, relief=tk.SUNKEN)
        talent_canvas.pack(fill=tk.BOTH, expand=True)

        talent_subframe = ttk.Frame(talent_canvas)
        talent_canvas.create_window((0, 0), window=talent_subframe, anchor="nw")

        match_data = RecapperGui.selected_match

        icon_size = 50
        talent_spacing = 25

        for i in range(1, 11):
            prefix = f"{i}_"
            hero_name = utils.clean_entity_name(match_data.get(f"{prefix}hero"))
            player_name = match_data.get(f"{prefix}battletag")
            winner = match_data['1_result']

            # determining position based on team (left or right column)
            column = 0 if i <= 5 else 11
            row = (i - 1) % 5

            frame_color = self.left_color if i <= 5 else self.right_color

            player_frame = tk.Frame(talent_subframe, bg=frame_color)
            player_frame.grid(row=row, column=column, columnspan=7, padx=5, pady=5, sticky="ew")

            hero_image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"
            hero_img = draw_image(hero_image_path, border_width=0, size=icon_size)
            hero_label = tk.Label(player_frame, image=hero_img, bg=frame_color)
            hero_label.image = hero_img
            hero_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")

            fg_color = self.left_font_color if i <= 5 else self.right_font_color
            name_label = tk.Label(player_frame, text=player_name, width=20, anchor="w", bg=frame_color, fg=fg_color)
            name_label.grid(row=0, column=1, padx=(0, 20), pady=10, sticky="w")

            with open(f'{RecapperGui.dist_prefix}heroes-talents/hero/{hero_name}.json', 'r') as f:
                hero_talents = json.load(f)

            for level_index, talent_tier in enumerate(['1', '4', '7', '10', '13', '16', '20']):
                talent_choice = int(match_data.get(f"{prefix}Talents")[level_index])

                if talent_choice != 0:
                    talent_data = hero_talents["talents"][talent_tier][talent_choice - 1]
                    talent_button = self.create_talent_icon(player_frame, talent_data)
                    talent_button.grid(row=0, column=2 + level_index, padx=(0, 10), pady=10)
                else:
                    placeholder_label = tk.Label(player_frame, bg=frame_color, width=7)
                    placeholder_label.grid(row=0, column=2 + level_index, padx=(0, 10), pady=10)

        talent_window.protocol("WM_DELETE_WINDOW", lambda: self.close_talent_viewer(talent_window))

    def close_talent_viewer(self, window):
        self.talent_viewer_is_open = False
        window.destroy()

    def create_talent_icon(self, parent, talent_data):
        image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/talents/{talent_data['icon']}"

        img = draw_image(image_path=image_path, shape="circle", size=50)

        talent_button = tk.Button(parent, image=img, borderwidth='1', relief='solid')
        talent_button.image = img

        CustomTooltipLabel(talent_button,
                           text=f"{talent_data['name']}\n{talent_data['type']}\n{talent_data['description']}",
                           hover_delay=300,
                           justify="center",
                           wraplength=300,
                           background="#1c1c1c",
                           foreground="white",
                           border=1,
                           relief='groove')

        return talent_button

    def open_extras_viewer(self):
        if self.extras_viewer_is_open:
            root.bell()
            return
        self.extras_viewer_is_open = True

        style = ttk.Style()
        style.configure("Treeview", rowheight=40, padding=(0,2), anchor="center")

        extras_window = tk.Toplevel(self.frame)
        extras_window.title("Advanced Stats")

        extras_window.geometry("1450x500")

        tree_frame = tk.Frame(extras_window)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        h_scroll = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        columns = ["Number", "Player", "Physical\nDmg", "Spell Dmg", "Self\nHealing", "Ally\nShielding", "Camp\nCaptures", "Time\nDead",
                   "Teamfight\nHealing", "Teamfight\nDamage", "Teamfight\nDmg Taken", "Clutch\nHeals", "Escapes",
                   "Enemy\nCC Time", "Enemy\nSilence\n Time", "Enemy\nRoot\nTime", "Enemy\nStun\nTime", "Regen\nGlobes", "Time\non Fire", "Minion\nKills"]
        column_widths = [40, 120, 80, 80, 80, 80, 40, 40, 80, 80, 80, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40]

        extras_tree = ttk.Treeview(tree_frame,
                                   columns=columns,
                                   show="tree headings",
                                   height=50,
                                   xscrollcommand=h_scroll.set,)

        h_scroll.config(command=extras_tree.xview)

        extras_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        extras_tree.bind('<Button-1>', lambda event, tree=extras_tree: prevent_resize(event, tree))
        extras_tree.bind('<Motion>', lambda event, tree=extras_tree: prevent_resize(event, tree))


        for col, width in zip(columns, column_widths):
            extras_tree.heading(col, text=col, anchor="center",
                                command=lambda _col=col: sort_by_column(col=_col,
                                                                        tab_tree=extras_tree,
                                                                        tab_sort_state=self.extras_sort_state))
            extras_tree.column(col, anchor="center", width=width)

        match_data = RecapperGui.selected_match

        for i in range(1, 11):
            prefix = f"{i}_"
            hero_name = utils.clean_entity_name(match_data.get(f"{prefix}hero"))
            row = [
                i,
                match_data.get(f"{prefix}battletag"),
                match_data.get(f"{prefix}PhysicalDamage", ""),
                match_data.get(f"{prefix}SpellDamage", ""),
                match_data.get(f"{prefix}SelfHealing", ""),
                match_data.get(f"{prefix}ProtectionGivenToAllies", ""),
                match_data.get(f"{prefix}MercCampCaptures", ""),
                match_data.get(f"{prefix}TimeSpentDead", ""),
                match_data.get(f"{prefix}TeamfightHealingDone", ""),
                match_data.get(f"{prefix}TeamfightHeroDamage", ""),
                match_data.get(f"{prefix}TeamfightDamageTaken", ""),
                match_data.get(f"{prefix}ClutchHealsPerformed", ""),
                match_data.get(f"{prefix}EscapesPerformed", ""),
                match_data.get(f"{prefix}TimeCCdEnemyHeroes", ""),
                match_data.get(f"{prefix}TimeSilencingEnemyHeroes", ""),
                match_data.get(f"{prefix}TimeRootingEnemyHeroes", ""),
                match_data.get(f"{prefix}TimeStunningEnemyHeroes", ""),
                match_data.get(f"{prefix}OnFireTimeOnFire", ""),
                match_data.get(f"{prefix}RegenGlobes", ""),
                match_data.get(f"{prefix}MinionKills", ""),
            ]

            if i <= 5:
                extras_tree.insert("", tk.END, text='', values=row, image=self.hero_images[hero_name],
                                   tags=('blue_row',))
            else:
                extras_tree.insert("", tk.END, text='', values=row, image=self.hero_images[hero_name],
                                   tags=('red_row',))

        extras_tree.heading('#0', text='\nIcon\n', anchor='center')
        extras_tree.column('#0', width=80, anchor='center')

        extras_window.protocol("WM_DELETE_WINDOW", lambda: self.close_extras_viewer(extras_window))

    def close_extras_viewer(self, window):
        self.extras_viewer_is_open = False
        window.destroy()

    def refresh_tables(self):
        for widget in self.match_details_canvas.winfo_children():
            widget.destroy()

        self.create_widgets()

        self.frame.update_idletasks()


class TabHeroStats:
    def __init__(self, parent, sorted_data):
        self.talent_stats = None
        self.scrollbar = None
        self.buttons = []
        self.frame = tk.Frame(parent)
        self.sorted_data = sorted_data
        self.hero_stats_sort_state = {"column": None, "ascending": False}
        self.hero_table = None

        self.hero_stats_canvas = None
        self.hero_stats_subframe = None
        self.hero_stats_tree = None
        self.button_refs = {}
        self.hero_images = {}

        self.talent_frame = None
        self.talent_icons = {}
        self.talent_tree = None
        self.talent_tree_is_open = False

        self.create_widgets()

    def create_widgets(self):

        try:
            with open(f"{RecapperGui.recapper_dir}/hero_table.json", 'r') as f:
                self.hero_table = json.load(f)
        except FileNotFoundError:
            self.hero_table = utils.create_empty_hero_table()

        self.create_hero_stats_table()

    def create_hero_stats_table(self):
        self.hero_stats_canvas = tk.Canvas(self.frame, relief=tk.SUNKEN)
        self.hero_stats_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hero_stats_subframe = tk.Frame(self.hero_stats_canvas)
        self.hero_stats_subframe.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(self.hero_stats_subframe, text="Hero Stats")
        label.pack(pady=15, padx=20)

        columns = ["Hero", "Winrate %", "Confidence", "Popularity %", "Pick Rate %", "Ban Rate %", "Influence", "Games", "Talent Winrates"]
        column_widths = [100, 50, 50, 50, 50, 50, 50, 50, 100]

        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Calibri', 10, 'bold'))

        scrollbar = tk.Scrollbar(self.hero_stats_subframe, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.hero_stats_tree = ttk.Treeview(self.hero_stats_subframe, columns=columns, selectmode='none',
                                            show="tree headings",
                                            yscrollcommand=scrollbar.set, height=50)

        scrollbar.config(command=self.hero_stats_tree.yview)

        for col, width in zip(columns, column_widths):
            self.hero_stats_tree.heading(col, text=col, command=lambda _col=col: sort_by_column(col=_col, tab_tree=self.hero_stats_tree,
                                                                                                tab_sort_state=self.hero_stats_sort_state))
            self.hero_stats_tree.column(col, anchor="center", width=width)

        ht = self.hero_table
        total_games = len(self.sorted_data)

        self.hero_images = {}
        self.button_refs = {}

        for i, hero in enumerate(ht):
            games_played = hero.get("gamesPlayed")
            games_won = hero.get('gamesWon', 0)
            pick_rate = hero.get('gamesPlayed', 0) / total_games if total_games != 0 else 0
            ban_rate = hero.get('gamesBanned', 0) / total_games if total_games != 0 else 0
            winrate = games_won / games_played if games_played != 0 else 0

            influence = 0 if ban_rate == 1 else ((winrate - 0.5) * (100 * pick_rate / (100 - (100 * ban_rate))) * 10000)

            hero_name = utils.clean_entity_name(hero.get("name"))

            row = [
                hero_name,                                                                  # Hero
                f"{'%.1f' % (100 * winrate)}",                                              # Winrate
                f"±{'%.1f' % (100 * utils.wald_interval(x=games_won, n=games_played))}",    # Confidence
                f"{'%.1f' % (100 * (pick_rate + ban_rate))}",                               # Popularity
                f"{'%.1f' % (100 * pick_rate)}",                                            # Pick Rate
                f"{'%.1f' % (100 * ban_rate)}",                                             # Ban Rate
                f"{'%.0f' % influence}",                                                    # Influence
                games_played,                                                               # Games Played
                "Click to View"                                                             # Talent Winrates
            ]

            image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"
            img = draw_image(image_path, border_width=0, size=40)
            self.hero_images[hero_name] = img

            self.hero_stats_tree.insert("", tk.END, text='', values=row, image=self.hero_images[hero_name])
            self.hero_stats_tree.heading('#0', text='Icon', anchor='center')
            self.hero_stats_tree.column('#0', width=50)

        self.hero_stats_tree.pack(fill=tk.BOTH, expand=True)

        self.hero_stats_tree.bind("<Button-1>", self.on_click_talent_winrates)

        # Hacky way of doing the UI for "View Talents". Might want to optimize later
        self.hero_stats_tree.bind("<Motion>", self.on_mouse_motion)
        self.hero_stats_canvas.update_idletasks()

    def on_mouse_motion(self, event):
        if self.hero_stats_tree.identify_region(event.x, event.y) == "separator":
            return "break"

        column = self.hero_stats_tree.identify_column(event.x)

        if column == '#9' and event.y > 33:
            self.hero_stats_tree.config(cursor="hand2")
        else:
            self.hero_stats_tree.config(cursor="")

    def on_click_talent_winrates(self, event):
        if self.hero_stats_tree.identify_region(event.x, event.y) == "separator":
            return "break"

        item = self.hero_stats_tree.identify('item', event.x, event.y)
        column = self.hero_stats_tree.identify_column(event.x)

        if column == '#9' and event.y > 33:
            hero_data = self.hero_stats_tree.item(item, "values")
            hero_name = hero_data[0]

            if self.talent_tree_is_open:
                self.talent_tree.bell()
            else:
                self.open_talent_winrates_window(hero_name)

    def open_talent_winrates_window(self, hero_name):
        win = tk.Toplevel(self.frame)
        win.title(f"{hero_name.capitalize()} Talent Winrates")
        win.geometry("800x700")
        win.resizable(False, True)

        self.talent_tree_is_open = True

        label = tk.Label(win, text=f"Talent Winrates for {hero_name.capitalize()}", font=("Calibri", 12))
        label.pack(pady=20)

        canvas = tk.Canvas(win)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.talent_frame = tk.Frame(canvas)
        self.talent_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        scrollbar = tk.Scrollbar(self.talent_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def resize_canvas(event):
            canvas_width = event.width
            canvas.itemconfig(self.talent_frame_id, width=canvas_width)

        self.talent_frame_id = canvas.create_window((0, 0), window=self.talent_frame, anchor="nw")
        canvas.bind("<Configure>", resize_canvas)

        columns = ["Name", "Winrate", "N. Winrate", "Popularity", "Games Played"]
        column_widths = [150, 50, 50, 50, 50]

        style = ttk.Style()
        style.layout("TalentTreeview", [
            ("Treeview.field", {"sticky": "nswe"})
        ])
        style.configure("TalentTreeview", rowheight=60, padding=(0, 2), anchor="center")

        self.talent_tree = ttk.Treeview(self.talent_frame,
                                        columns=columns,
                                        show='tree headings',
                                        style="TalentTreeview",
                                        yscrollcommand=scrollbar.set)
        self.talent_tree.pack(fill=tk.BOTH, expand=True)

        for col, width in zip(columns, column_widths):
            self.talent_tree.heading(col, text=col)
            self.talent_tree.column(col, anchor="center", width=width)

        talent_stats = self.get_talent_stats(hero_name)
        talent_tiers = [1, 4, 7, 10, 13, 16, 20]
        self.talent_icons = {}

        for i, level in enumerate(talent_tiers):
            divider_text = f"Level {level} Talents"
            self.talent_tree.insert("", "end", values=("", divider_text, "", ""), tags=("divider",))

            for j in range(len(talent_stats['names'][i])):
                talent_name = talent_stats['names'][i][j]
                talent_games_played = talent_stats['games'][i][j]
                total_games_played = sum(talent_stats['games'][i])

                row = [
                    talent_name,
                    talent_stats['winrate'][i][j],
                    talent_stats['normalized_winrate'][i][j],
                    f"{'%.2f' % (100 * talent_games_played / total_games_played)}%" if total_games_played > 0 else "0%",
                    f"{talent_games_played}",
                ]

                if self.talent_icons.get(talent_name) is None:
                    img = draw_image(talent_stats['icons'][i][j], border_width=0, size=50, shape="square")
                    self.talent_icons[talent_name] = img

                self.talent_tree.insert("", tk.END, text='', values=row, image=self.talent_icons[talent_name])
                self.talent_tree.heading('#0', text='Icon', anchor='center')
                self.talent_tree.column('#0', width=30)

        self.talent_tree.tag_configure("divider", background="#1c1cba", font=("Calibri", 10, "bold"))

        self.talent_tree.bind('<Button-1>', lambda event, tree=self.talent_tree: prevent_resize(event, tree))
        self.talent_tree.bind('<Motion>', lambda event, tree=self.talent_tree: self.on_talent_mouse_motion(event))

        scrollbar.config(command=self.talent_tree.yview)

        win.protocol("WM_DELETE_WINDOW", lambda: self.close_talent_stats(win))

    def on_talent_mouse_motion(self, event):
        if self.talent_tree.identify_region(event.x, event.y) == "separator":
            return "break"

        # item = self.talent_tree.identify('item', event.x, event.y)
        # column = self.talent_tree.identify_column(event.x)
        #
        # talent_data = self.talent_tree.item(item, "values")
        # talent_name = talent_data[0]
        #
        # if column == "#0":
        #     pass

    def get_talent_stats(self, hero):
        with open(f'heroes-talents/hero/{hero}.json', 'r') as f:
            hero_talents = json.load(f)

        talent = {
            'icons': [],
            'names': [],
            'descriptions': [],
            'types': [],
            'cooldown': [],
            'games': [],
            'wins': [],
            'winrate': [],
            'normalized_games': [],
            'normalized_wins': [],
            'normalized_winrate': []
        }

        hero_id = utils.get_id_by_hero(hero)

        for i in range(len(utils.talent_tiers)):
            for key in talent:
                talent[key].append([])
            tier_i_talents = hero_talents["talents"][utils.talent_tiers[i]]

            for j in range(len(tier_i_talents)):
                talent['icons'][i].append(
                    f".{RecapperGui.dist_prefix}/heroes-talents/images/talents/{tier_i_talents[j]['icon']}")
                talent['names'][i].append(tier_i_talents[j]['name'])
                talent['descriptions'][i].append(tier_i_talents[j]['description'])
                talent['types'][i].append(tier_i_talents[j]['type'])

                if tier_i_talents[j].get('cooldown') is not None:
                    talent['cooldown'][i].append(tier_i_talents[j]['cooldown'])
                else:
                    talent['cooldown'][i].append('')

                games_played = self.hero_table[hero_id - 1]['talentGames'][i][j]
                games_won = self.hero_table[hero_id - 1]['talentWins'][i][j]
                normalized_games_played = self.hero_table[hero_id - 1]['talentNormalizedGames'][i][j]
                normalized_games_won = self.hero_table[hero_id - 1]['talentNormalizedWins'][i][j]

                talent['games'][i].append(games_played)
                talent['wins'][i].append(games_won)
                talent['winrate'][i].append(
                    f"{'%.2f' % (100 * games_won / games_played)}%" if games_played != 0 else "0.00%"
                )
                talent['normalized_games'][i].append(normalized_games_played)
                talent['normalized_wins'][i].append(normalized_games_won)
                talent['normalized_winrate'][i].append(
                    f"{'%.2f' % (100 * normalized_games_won / normalized_games_played)}%" if normalized_games_played != 0 else "0.00%"
                )

        return talent

    def refresh_tables(self):
        if self.hero_stats_canvas is not None:
            self.hero_stats_canvas.destroy()

        self.create_widgets()

        self.frame.update_idletasks()

    def close_talent_stats(self, window):
        self.talent_icons = {}
        self.talent_trees = {}
        self.talent_tree_sort_state = []
        for widget in self.talent_frame.winfo_children():
            widget.destroy()
        window.destroy()

        self.talent_tree_is_open = False


class TabPlayerStats:
    def __init__(self, parent, sorted_data):
        self.frame = tk.Frame(parent)
        self.sorted_data = sorted_data

    def create_widgets(self):
        label = tk.Label(self.frame, text="Player Stats")
        label.pack(pady=20, padx=20)

        self.player_stats_canvas = tk.Canvas(self.frame, relief=tk.SUNKEN)
        self.player_stats_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.player_stats_subframe = tk.Frame(self.player_stats_canvas)
        self.player_stats_subframe.pack(fill=tk.BOTH, expand=True)

        self.tree = tk.ttk.Treeview(self.player_stats_subframe)
        self.tree.pack(fill=tk.BOTH, expand=True)


def draw_image(image_path: str, border_color: str = "black", border_width: int = 0, size=50, shape="circle"):
    img = Image.open(image_path).resize((size, size), Image.LANCZOS).convert("RGBA")

    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)

    if shape == "circle":
        draw.ellipse((border_width, border_width, img.size[0] - border_width, img.size[1] - border_width), fill=255)
        bordered_img = Image.new("RGBA", img.size, (255, 255, 255, 0))
        border_draw = ImageDraw.Draw(bordered_img)
        border_draw.ellipse((0, 0, img.size[0], img.size[1]), fill=border_color)
        border_draw.ellipse((border_width, border_width, img.size[0] - border_width, img.size[1] - border_width))
    elif shape == "square":
        draw.rectangle((border_width, border_width, img.size[0] - border_width, img.size[1] - border_width),
                       fill=255)
        bordered_img = Image.new("RGBA", img.size, (255, 255, 255, 0))
        border_draw = ImageDraw.Draw(bordered_img)
        border_draw.rectangle((0, 0, img.size[0], img.size[1]), fill=border_color)
        border_draw.rectangle((border_width, border_width, img.size[0] - border_width, img.size[1] - border_width))
    else:
        return

    bordered_img.paste(img, (0, 0), mask=mask)
    return ImageTk.PhotoImage(bordered_img)


def sort_by_column(col, tab_tree, tab_sort_state):
    data = [(tab_tree.set(child, col), child) for child in tab_tree.get_children('')]

    def try_numeric(value):
        try:
            return float(value)
        except ValueError:
            return value

    data.sort(key=lambda x: try_numeric(x[0]), reverse=tab_sort_state.get(col, True))

    for index, (val, child) in enumerate(data):
        tab_tree.move(child, '', index)

    tab_sort_state[col] = not tab_sort_state.get(col, True)

    for column in tab_tree["columns"]:
        if column == col:
            direction = "▲" if tab_sort_state[col] else "▼"
            tab_tree.heading(column, text=f"{col} {direction}")
        else:
            tab_tree.heading(column, text=column)


def prevent_resize(event, tree):
    if tree.identify_region(event.x, event.y) == "separator":
        return "break"


if __name__ == "__main__":
    root = tk.Tk()
    app = RecapperGui(root)
    root.mainloop()
