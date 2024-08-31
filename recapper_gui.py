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

import pprint

__version__ = "0.4.1"


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

        self.tab_replays = None
        self.tab_match_details = None
        self.tab_hero_stats = None
        self.tab_player_stats = None

        self.inner_frame = None
        self.inner_frame_id = None
        self.notebook = None
        self.scrollbar = None
        self.button = None
        self.label = None

        self.observer = None  # used for watchdog process

        self.tab1_filters = {
            'mode': 'all',
            'maps': 'all',
            'names': ['any'] * 10,
            'heroes': ['any'] * 10,
        }

        self.mode_var = None
        self.map_var = None

        self.root = root
        self.hero_table = None

        sv_ttk.set_theme("dark")

        self.root.title(f"Heroes Recapper {__version__}")
        self.root.geometry("850x700")

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        try:
            with open(f"{self.recapper_dir}/replay_data.json", 'r') as f:
                temp = utils.load_partial_json(f"{self.recapper_dir}/replay_data.json")
                self.sorted_data = temp['sorted_data']
                self.end_position = temp['end_position']

                print(f"replays: {len(self.sorted_data)}")
        except FileNotFoundError:
            self.sorted_data = SortedDict(lambda x: -x)
            self.end_position = 0

        self.selected_match = None

        self.create_widgets()

    def on_closing(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            dat = dict(self.sorted_data)

            with open(f"{self.recapper_dir}/replay_data.json", "w") as f:
                json.dump(dat, f)
            print("Closing Heroes Recapper")
            root.destroy()

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
        settings_menu.add_command(label="Set Constraints")

        about_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="About", menu=about_menu)
        about_menu.add_cascade(label="About")

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="quick guide", command=self.open_help_menu)

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

    def on_tab_selected(self, event):
        selected_tab = event.widget.select()
        selected_tab_widget = self.notebook.nametowidget(selected_tab)

        if selected_tab_widget.winfo_id() == self.tab_match_details.frame.winfo_id():
            self.tab_match_details.refresh_tables()

    def exit_without_saving(self):
        print("exiting without saving")

        try:
            shutil.copy(f"{self.recapper_dir}/temp_hero_table.json", f"{self.recapper_dir}/hero_table.json")
        except FileNotFoundError:
            print("temp_hero_table.json not found")
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

    def select_directory(self):
        file_path = tk.filedialog.askdirectory()

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

    def process_sorted_replays(self, paths: list[str], ):
        database.add_to_container_and_update_tables(
            paths=paths, sorted_dict=self.sorted_data, recapper_dir=self.recapper_dir, hero_table=self.hero_table)
        self.tab_replays.refresh_rows()
        self.root.update_idletasks()

        # utils.update_player_tables()

    def start_watching_directory(self, directory):
        event_handler = ReplayHandler(self.process_sorted_replays)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=directory, recursive=False)
        self.observer.start()

    def stop_watching_directory(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

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
        self.bg_image_cache = {}

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

        num_replays_label = ttk.Label(filters_frame, text=f"Processed Replays: {len(self.sorted_data)}")
        num_replays_label.grid(row=2, column=5)

        # button to apply filters
        filter_button = ttk.Button(filters_frame, text='Apply Filters', command=self.apply_filters, cursor='hand2')
        filter_button.grid(row=2, column=8, columnspan=2, pady=10)

        # button for limit per page
        limit_label = ttk.Label(filters_frame, text='Limit: ')
        limit_label.grid(row=2, column=10)
        self.limit_var = tk.IntVar(value=self.limit)
        limit_combobox = ttk.Combobox(filters_frame, textvariable=self.limit_var, values=[5, 10, 25, 50], state="readonly", width=3)
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

        for i in range(min(self.limit, len(self.sorted_data))):
            self.create_row(match_data=database.get_nth_value(self.sorted_data, i))

    def apply_filters(self):
        self.replay_filters['mode'] = self.mode_var.get()
        self.replay_filters['maps'] = self.map_var.get()
        self.limit = self.limit_var.get()

        filtered_data = []
        num_replays = len(self.sorted_data)

        print(f"num_replays: {num_replays}")

        i = 0
        while len(filtered_data) < self.limit and i != num_replays:
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
            left_color = "#00008B"
            right_color = "#FFB6C1"
        else:
            left_color = "#ADD8E6"
            right_color = "#8B0000"

        sub_canvas.create_rectangle(0, 0, 100, row_height, fill=left_color, outline="")
        sub_canvas.create_rectangle(row_width, 0, row_width + 100, row_height, fill=right_color, outline="")

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
                                                       f"{match_data['1_name']}       {match_data['6_name']}\n"
                                                       f"{match_data['2_name']}       {match_data['7_name']}\n"
                                                       f"{match_data['3_name']}       {match_data['8_name']}\n"
                                                       f"{match_data['4_name']}       {match_data['9_name']}\n"
                                                       f"{match_data['5_name']}       {match_data['10_name']}\n",
                                         fill="white", font=("Segoe UI", 15, "bold"), justify="center", anchor="n")

        sub_canvas.bind("<Button-1>", lambda e, match=match_data: self.set_selected_match(match))

    def refresh_rows(self):

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for i in range(self.limit):
            self.create_row(match_data=database.get_nth_value(self.sorted_data, i))

    def set_selected_match(self, match):
        if RecapperGui.selected_match != match:
            RecapperGui.selected_match = match

        self.tabs.select(1)  # setting selected tab to "Match Details"

    def create_hero_icon(self, canvas, match_data, index, x_pos, y_pos):
        hero_name = utils.clean_entity_name(match_data[f"{index + 1}_hero"])

        border_color = "blue" if index < 5 else "red"

        # Check if the hero icon is already in the cache
        if hero_name not in self.hero_icon_cache:
            image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"
            img = draw_image(image_path=image_path, border_color=border_color, shape="circle")
            self.hero_icon_cache[hero_name] = img
        else:
            img = self.hero_icon_cache[hero_name]

        image_button = tk.Button(canvas, highlightcolor=border_color, image=img,
                                 command=lambda hero=hero_name: self.on_hero_click(hero), borderwidth='2')
        image_button.image = img

        CustomTooltipLabel(image_button,
                           text=match_data[f"{index + 1}_name"],
                           hover_delay=300,
                           justify="center",
                           background="#1c1c1c",
                           foreground="white",
                           border=1,
                           relief='groove')

        canvas.create_window(x_pos, y_pos, anchor='nw', window=image_button)

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

        self.frame = tk.Frame(parent)

        self.match_details_canvas = tk.Canvas(self.frame, relief=tk.SUNKEN)
        self.match_details_canvas.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()

    def create_widgets(self):

        if RecapperGui.selected_match is not None:
            self.create_score_table()

            self.toggle_talent_button = ttk.Button(self.match_details_canvas, text="Show Talents",
                                                   command=self.open_talent_viewer, cursor='hand2')
            self.toggle_talent_button.pack(pady=5)

            self.toggle_extras_button = ttk.Button(self.match_details_canvas, text="Show Advanced Stats",
                                                   command=self.open_extras_viewer, cursor='hand2')
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

        columns = ["Number", "Player", "Hero", "Kills", "Assists", "Deaths", "Hero Dmg", "Siege Dmg", "Healing",
                   "Dmg Taken", "XP"]
        column_widths = [10, 80, 60, 5, 5, 5, 30, 30, 30, 30, 20]

        self.score_subframe = tk.Frame(self.match_details_canvas)
        self.score_subframe.pack(fill=tk.BOTH, expand=True)

        self.score_tree = ttk.Treeview(self.score_subframe, columns=columns, show="tree headings")
        self.score_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for col, width in zip(columns, column_widths):
            self.score_tree.heading(col, text=col,
                                    command=lambda _col=col: sort_by_column(col=_col, tab_tree=self.score_tree,
                                                                            tab_sort_state=self.score_sort_state))
            self.score_tree.column(col, anchor="center", width=width, )

        self.hero_images = {}

        self.score_tree.tag_configure('blue_row', background='#08075e')
        self.score_tree.tag_configure('red_row', background='#731009')

        for i in range(1, 11):  # assuming 10 players
            prefix = f"{i}_"
            hero_name = utils.clean_entity_name(match_data.get(f"{prefix}hero"))
            row = [
                i,
                match_data.get(f"{prefix}battletag"),
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

            # determining position based on team (left or right column)
            column = 0 if i <= 5 else 11
            row = (i - 1) % 5

            frame_color = "#08075e" if i <= 5 else "#731009"
            player_frame = tk.Frame(talent_subframe, bg=frame_color)
            player_frame.grid(row=row, column=column, columnspan=7, padx=5, pady=5, sticky="ew")

            hero_image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"
            hero_img = draw_image(hero_image_path, border_width=0, size=icon_size)
            hero_label = tk.Label(player_frame, image=hero_img, bg=frame_color)
            hero_label.image = hero_img
            hero_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")

            name_label = tk.Label(player_frame, text=player_name, width=20, anchor="w", bg=frame_color, fg="white")
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
        self.frame = tk.Frame(parent)
        self.sorted_data = sorted_data
        self.hero_stats_sort_state = {"column": None, "ascending": False}

        try:
            with open(f"{RecapperGui.recapper_dir}/hero_table.json", 'r') as f:
                self.hero_table = json.load(f)
                shutil.copy(f"{RecapperGui.recapper_dir}/hero_table.json",
                            f"{RecapperGui.recapper_dir}/temp_hero_table.json")
        except FileNotFoundError:
            self.hero_table = utils.create_empty_hero_table()

        self.create_widgets()

    def create_widgets(self):

        # todo from here until next todo block should be its own function, called by tab3 when a button is clicked

        asdf = False
        if asdf:
            with open('heroes-talents/hero/genji.json', 'r') as f:
                hero_talents = json.load(f)

            talent = {
                'icons': [],
                'names': [],
                'descriptions': [],
                'cooldown': [],
                'games': [],
                'wins': [],
                'popularity': [],
                'winrate': []
            }

            hero_id = utils.get_id_by_hero('genji')

            for i in range(len(utils.talent_tiers)):
                for key in talent:
                    talent[key].append([])
                tier_i_talents = hero_talents["talents"][utils.talent_tiers[i]]
                for j in range(len(tier_i_talents)):
                    talent['icons'][i].append(
                        f"{self.dist_prefix}/heroes-talents/images/talents/{tier_i_talents[j]['icon']}")
                    talent['names'][i].append(tier_i_talents[j]['name'])
                    talent['descriptions'][i].append(tier_i_talents[j]['description'])

                    if tier_i_talents[j].get('cooldown') is not None:
                        talent['cooldown'][i].append(tier_i_talents[j]['cooldown'])
                    else:
                        talent['cooldown'][i].append('')

                    games_played = self.hero_table[hero_id - 1]['talentGames'][i][j]
                    games_won = self.hero_table[hero_id - 1]['talentWins'][i][j]

                    talent['games'][i].append(games_played)
                    talent['wins'][i].append(games_won)
                    talent['winrate'][i].append(
                        f"{100 * round(games_won / games_played, 4) if games_played != 0 else 0}%")

        # todo until here should be own function

        label = tk.Label(self.frame, text="Hero Stats")
        label.pack(pady=20, padx=20)

        self.tab3_canvas = tk.Canvas(self.frame, relief=tk.SUNKEN)
        self.tab3_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hero_stats_subframe = tk.Frame(self.tab3_canvas)
        self.hero_stats_subframe.pack(fill=tk.BOTH, expand=True)

        columns = ["Hero", "Winrate %", "Confidence", "Popularity %", "Pick Rate %", "Ban Rate %", "Influence",
                   "Games Played"]
        column_widths = [50, 100, 80, 80, 100, 100, 100, 100, 100, 120]

        style = ttk.Style()
        style.configure("Treeview", rowheight=40)

        scrollbar = tk.Scrollbar(self.hero_stats_subframe, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tab3_tree = ttk.Treeview(self.hero_stats_subframe, columns=columns, selectmode='none',
                                      show="tree headings",
                                      yscrollcommand=scrollbar.set, height=50)
        self.tab3_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tab3_tree.yview)

        for col, width in zip(columns, column_widths):
            self.tab3_tree.heading(col, text=col,
                                   command=lambda _col=col: sort_by_column(col=_col, tab_tree=self.tab3_tree,
                                                                           tab_sort_state=self.hero_stats_sort_state))
            self.tab3_tree.column(col, anchor="w", width=width)

        ht = self.hero_table
        total_games = len(self.sorted_data)
        self.tab3_data = []

        self.tab3_hero_images = {}

        for i, hero in enumerate(ht):
            games_played = hero.get("gamesPlayed")
            games_won = hero.get('gamesWon', 0)
            pick_rate = hero.get('gamesPlayed', 0) / total_games if total_games != 0 else 0
            ban_rate = hero.get('gamesBanned', 0) / total_games if total_games != 0 else 0

            hero_name = utils.clean_entity_name(hero.get("name"))

            row = [
                hero_name,
                f"{round(100 * (games_won / games_played) if games_played != 0 else 0, 3)}",
                f"±{round(100 * utils.wald_interval(x=games_won, n=games_played), 3)} ",
                f"{round(100 * (pick_rate + ban_rate), 3)}",
                f"{round(100 * pick_rate, 3)}",
                f"{round(100 * ban_rate, 3)}",
                "influence",  # need to calculate later
                games_played
            ]

            image_path = f"{RecapperGui.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"

            img = draw_image(image_path, border_width=0, size=40)
            self.tab3_hero_images[hero_name] = img
            self.tab3_tree.insert("", tk.END, text='', values=row, image=self.tab3_hero_images[hero_name])
            self.tab3_tree.heading('#0', text='Icon', anchor='center')
            self.tab3_tree.column('#0', width=50)

        self.tab3_canvas.update_idletasks()


class TabPlayerStats:
    def __init__(self, parent, sorted_data):
        self.frame = tk.Frame(parent)
        self.sorted_data = sorted_data

    def create_tab4_content(self):
        label = tk.Label(self.frame, text="Player Stats")
        label.pack(pady=20, padx=20)

        self.player_stats_canvas = tk.Canvas(self.frame, relief=tk.SUNKEN)
        self.player_stats_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.player_stats_subframe = tk.Frame(self.player_stats_canvas)
        self.player_stats_subframe.pack(fill=tk.BOTH, expand=True)

        self.tree = tk.ttk.Treeview(self.player_stats_subframe)
        self.tree.pack(fill=tk.BOTH, expand=True)


def draw_image(image_path: str, border_color: str = "black", border_width: int = 2, size=50, shape="circle"):
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

    try:
        data.sort(key=lambda x: int(x[0]), reverse=tab_sort_state.get(col, True))
    except ValueError:
        data.sort(key=lambda x: x[0], reverse=tab_sort_state.get(col, True))

    for index, (val, child) in enumerate(data):
        tab_tree.move(child, '', index)

    tab_sort_state[col] = not tab_sort_state.get(col, True)

    for column in tab_tree["columns"]:
        if column == col:
            direction = "▲" if tab_sort_state[col] else "▼"
            tab_tree.heading(column, text=f"{col} {direction}")
        else:
            tab_tree.heading(column, text=column)


if __name__ == "__main__":
    root = tk.Tk()
    app = RecapperGui(root)
    root.mainloop()
