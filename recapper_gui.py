import datetime
import json
import threading
import os
import time
import tkinter as tk
import tkinter.filedialog
import pandas as pd
import sv_ttk
from PIL import Image, ImageDraw, ImageTk
from sortedcontainers import SortedDict
from tksheet import Sheet
from tktooltip import ToolTip

import database
import utils
from utils import clean_string, test_paths, get_winner


def create_circular_image(image_path: str, border_color: str = "black", border_width: int = 2):
    img = Image.open(image_path).resize((50, 50), Image.LANCZOS).convert("RGBA")

    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((border_width, border_width, img.size[0] - border_width, img.size[1] - border_width), fill=255)
    bordered_img = Image.new("RGBA", img.size, (255, 255, 255, 0))
    border_draw = ImageDraw.Draw(bordered_img)
    border_draw.ellipse((0, 0, img.size[0], img.size[1]), fill=border_color)
    border_draw.ellipse((border_width, border_width, img.size[0] - border_width, img.size[1] - border_width),
                        fill=(0, 0, 0, 0))

    bordered_img.paste(img, (0, 0), mask=mask)

    return ImageTk.PhotoImage(bordered_img)


class RecapperGui:

    def __init__(self, root):

        self.tab2_tree = None
        self.tab3_tree = None

        self.tab2_data = None
        self.tab3_data = None

        self.tab2_frame = None
        self.tab3_frame = None

        self.tab1 = None
        self.tab2 = None
        self.tab3 = None
        self.tab4 = None

        self.inner_frame = None
        self.inner_frame_id = None
        self.notebook = None
        self.scrollbar = None
        self.button = None
        self.label = None
        self.tab1_canvas = None
        self.tab2_canvas = None
        self.tab3_canvas = None

        self.tab2_sort_state = {"column": None, "ascending": False}
        self.tab3_sort_state = {"column": None, "ascending": False}

        self.root = root
        self.hero_table = None

        sv_ttk.set_theme("dark")

        self.root.title("Heroes Recapper")
        self.root.geometry("1200x600")

        replays = test_paths
        self.database = pd.DataFrame()

        try:
            self.database = database.load_from_pickle("new_pickle.pkl")
        except FileNotFoundError:
            pass

        self.sorted_data = SortedDict()

        try:
            with open('gui_output.json', 'r') as openfile:
                self.sorted_data = utils.load_partial_json('gui_output.json')
        except FileNotFoundError:
            pass

        try:
            with open('hero_table.json', 'r') as f:
                self.hero_table = json.load(f)
        except FileNotFoundError:
            self.hero_table = utils.create_empty_hero_table()

        self.selected_match = None

        if len(self.sorted_data) > 0:
            _, self.selected_match = self.sorted_data.peekitem()

        self.limit = 0
        self.set_limit()

        # self.database = add_to_database(paths=["test-data/infernal.StormReplay", "test-data/sample0.StormReplay"], matches_database=newDF)
        self.create_widgets()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Replay", command=self.select_replay)
        file_menu.add_command(label="Select Directory", command=self.select_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)

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

        self.notebook = tk.ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab1 = tk.Frame(self.notebook)
        self.tab2 = tk.Frame(self.notebook)
        self.tab3 = tk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="Replays")
        self.notebook.add(self.tab2, text="Match Details")
        self.notebook.add(self.tab3, text="Hero Stats")

        self.create_tab1_content()
        self.create_tab2_content()
        self.create_tab3_content()
        # self.create_tab4_content()

    def create_tab1_content(self):
        self.tab1_canvas = tk.Canvas(self.tab1, relief=tk.SUNKEN)
        self.tab1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.tab1, orient=tk.VERTICAL, command=self.tab1_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tab1_canvas.configure(yscrollcommand=scrollbar.set)

        self.inner_frame = tk.Frame(self.tab1_canvas)

        self.inner_frame.bind("<Configure>",
                              lambda e: self.tab1_canvas.configure(scrollregion=self.tab1_canvas.bbox("all")))

        self.inner_frame_id = self.tab1_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.tab1_canvas.bind("<Configure>", self.on_canvas_configure)

        for i in range(self.limit):
            self.create_row(i)

    def on_canvas_configure(self, event):
        canvas_width = event.width - 10
        self.tab1_canvas.itemconfig(self.inner_frame_id, width=canvas_width)

    def create_row(self, row_number):

        sub_frame = tk.Frame(self.inner_frame, bd=2, relief="solid", width=800, height=150)
                              # command=lambda match=database.get_nth_value(self.sorted_data, row_number): self.set_selected_match(match))
        sub_frame.pack(pady=10, fill=tk.X, expand=True)

        match_data = database.get_nth_value(self.sorted_data, row_number)

        text_widget = tk.Label(sub_frame,
                               text=f"{match_data['date']}\n"
                                    f"{match_data['gameMode']}: {match_data['map']}\n"
                                    f"{str(datetime.timedelta(seconds=int(match_data['duration']) - 45))}\n"
                                    f"{get_winner(match_data['1_result'])}\n"
                                    ,
                               justify="center")
        text_widget.pack(pady=5, padx=10)

        image_container = tk.Frame(sub_frame)
        image_container.pack(pady=10, padx=10, anchor="w")

        for i in range(10):
            self.create_hero_icon(image_container, match_data, i)

        self.tab1_canvas.update_idletasks()
        self.tab1_canvas.configure(scrollregion=self.tab1_canvas.bbox("all"))

    def refresh_rows(self):
        self.set_limit()

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for i in range(self.limit):
            self.create_row(i)

        self.hide_loading_screen()

    def set_selected_match(self, match):
        self.selected_match = match
        print(self.selected_match)

        self.refresh_tables()
        return

    def create_hero_icon(self, container, match_data, index):
        hero_name = clean_string(match_data[f"{index + 1}_hero"])
        image_path = f"heroes-talents/images/heroes/{hero_name}.png"

        border_color = "blue"
        if index >= 5:
            border_color = "red"
        circular_image = create_circular_image(image_path, border_color=border_color)

        image_button = tk.Button(container, image=circular_image,
                                 command=lambda hero=hero_name: self.on_hero_click(hero), borderwidth='0')
        image_button.image = circular_image
        ToolTip(image_button, msg=match_data[f"{index + 1}_name"], delay=0.5)

        if index == 5:
            image_button.pack(side=tk.LEFT, padx=(50, 10))
        else:
            image_button.pack(side=tk.LEFT, padx=10)

    def on_hero_click(self, hero_name):
        print(f"Hero clicked: {hero_name}")

    def create_tab2_content(self):

        self.tab2_canvas = tk.Canvas(self.tab2, relief=tk.SUNKEN)
        self.tab2_canvas.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(self.tab2_canvas, text=f"{self.selected_match['date']}\n"
                                                f"{self.selected_match['gameMode']}: {self.selected_match['map']}\n"
                                                f"{str(datetime.timedelta(seconds=int(self.selected_match['duration']) - 45))}\n"
                                                f"{get_winner(self.selected_match['1_result'])}\n"
                         )
        label.pack(pady=20, padx=20)

        self.tab2_frame = tk.Frame(self.tab2_canvas)
        self.tab2_frame.pack(fill=tk.BOTH, expand=True)

        columns = ["Number", "Player", "Hero", "Kills", "Assists", "Deaths", "Hero Damage", "Siege Damage", "Healing",
                   "Damage Taken", "XP Contribution"]
        column_widths = [5, 80, 60, 5, 5, 5, 30, 30, 30, 30, 20]

        self.tab2_tree = tk.ttk.Treeview(self.tab2_frame, columns=columns, show="headings")
        self.tab2_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for col, width in zip(columns, column_widths):
            self.tab2_tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(col=_col, tab_tree=self.tab2_tree, tab_sort_state=self.tab2_sort_state))
            self.tab2_tree.column(col, anchor="center", width=width, )

        scrollbar = tk.ttk.Scrollbar(self.tab2_frame, orient=tk.VERTICAL, command=self.tab2_tree.yview)
        self.tab2_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_tab2_table()

    def refresh_tab2_table(self):

        if not self.selected_match:
            return

        match_data = self.selected_match

        for row in self.tab2_tree.get_children():
            self.tab2_tree.delete(row)

        self.tab2_data = []

        self.tab2_tree.tag_configure('blue_row', background='#08075e')
        self.tab2_tree.tag_configure('red_row', background='#731009')

        for i in range(1, 11):  # assuming 10 players
            prefix = f"{i}_"
            row = [
                i,
                match_data.get(f"{prefix}name", ""),
                match_data.get(f"{prefix}hero", ""),
                match_data.get(f"{prefix}SoloKill", 0),
                match_data.get(f"{prefix}Takedowns", 0),
                match_data.get(f"{prefix}Deaths", 0),
                match_data.get(f"{prefix}HeroDamage", 0),
                match_data.get(f"{prefix}SiegeDamage", 0),
                match_data.get(f"{prefix}Healing", 0),
                match_data.get(f"{prefix}DamageTaken", 0),
                match_data.get(f"{prefix}ExperienceContribution", 0)
            ]
            self.tab2_data.append(row)

            if i <= 5:
                self.tab2_tree.insert("", tk.END, values=row, tags=('blue_row',))
            else:
                self.tab2_tree.insert("", tk.END, values=row, tags=('red_row',))

        self.tab2_canvas.update_idletasks()

    def sort_by_column(self, col, tab_tree, tab_sort_state):
        data = [(tab_tree.set(child, col), child) for child in tab_tree.get_children('')]

        try:
            data.sort(key=lambda x: int(x[0]), reverse=tab_sort_state.get(col, True))
        except ValueError:
            data.sort(key=lambda x: x[0], reverse=tab_sort_state.get(col, True))

        for index, (val, child) in enumerate(data):
            tab_tree.move(child, '', index)

        tab_sort_state[col] = not tab_sort_state.get(col, True)

        # Update the column heading to indicate sorting direction
        for column in tab_tree["columns"]:
            if column == col:
                direction = "▲" if tab_sort_state[col] else "▼"
                tab_tree.heading(column, text=f"{col} {direction}")
            else:
                tab_tree.heading(column, text=column)

    def refresh_tables(self):
        for widget in self.tab2_canvas.winfo_children():
            widget.destroy()

    def create_tab3_content(self):
        label = tk.Label(self.tab3, text="Hero Stats")
        label.pack(pady=20, padx=20)

        self.tab3_canvas = tk.Canvas(self.tab3, relief=tk.SUNKEN)
        self.tab3_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tab3_frame = tk.Frame(self.tab3_canvas)
        self.tab3_frame.pack(fill=tk.BOTH, expand=True)

        columns = ["Hero", "Role", "Winrate %", "Confidence", "Popularity %", "Pick Rate %", "Ban Rate %", "Influence", "Games Played"]
        column_widths = [100, 30, 20, 20, 20, 20, 20, 30, 20]

        scrollbar = tk.Scrollbar(self.tab3_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tab3_tree = tk.ttk.Treeview(self.tab3_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set, )
        self.tab3_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tab3_tree.yview)

        for col, width in zip(columns, column_widths):
            self.tab3_tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(col=_col, tab_tree=self.tab3_tree, tab_sort_state=self.tab3_sort_state))
            self.tab3_tree.column(col, anchor="w", width=width, )

        ht = self.hero_table
        total_games = len(self.sorted_data)

        self.tab3_data = []

        for i in range(len(ht)):
            games_played = ht[i].get("gamesPlayed")
            games_won = ht[i].get('gamesWon', 0)
            pick_rate = ht[i].get('gamesPlayed', 0) / total_games if total_games != 0 else 0
            ban_rate = ht[i].get('gamesBanned', 0) / total_games if total_games != 0 else 0

            row = [
                ht[i].get("name"),
                ht[i].get("role"),
                f"{100 * round(games_won / games_played if games_played != 0 else 0, 4)}",
                f"±{100 * round(utils.wald_interval(x=games_won, n=games_played), 4)} ",
                f"{100 * round(pick_rate + ban_rate, 4)}",
                f"{100 * round(pick_rate, 4)}",
                f"{100 * round(ban_rate, 4)}",
                "influence",  # Adjust if 'influence' needs to be calculated
                games_played
            ]
            self.tab3_data.append(row)
            self.tab3_tree.insert("", tk.END, values=row)

        self.tab3_canvas.update_idletasks()

    def create_tab4_content(self):
        label = tk.Label(self.tab4, text="Player Stats")
        label.pack(pady=20, padx=20)

    def set_limit(self):
        self.limit = min(20, len(self.sorted_data))

    def exit_app(self):
        # database.save_to_pickle("new_pickle.pkl", self.database)

        print("exiting")

        dat = dict(self.sorted_data)

        with open("gui_output.json", "w") as outfile:
            json.dump(dat, outfile)
        root.destroy()

    def show_loading_screen(self):
        self.loading_label = tk.Label(self.root, text="Loading...", font=("Helvetica", 16))
        self.loading_label.pack(pady=20)
        self.root.update_idletasks()

    def hide_loading_screen(self):
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()
            delattr(self, 'loading_label')
        self.root.update_idletasks()

    def select_replay(self):
        path = [tk.filedialog.askopenfilename(filetypes=[("Storm Replay Files", "*.StormReplay")])]

        self.show_loading_screen()

        thread = threading.Thread(target=self.process_sorted_replays(paths=path))
        thread.start()
        # self.process_replays_containers(paths=[paths])

    def select_directory(self):
        file_path = tk.filedialog.askdirectory()
        paths = []

        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.endswith(".StormReplay"):
                    paths.append(os.path.join(root, file))

        start = time.time()
        self.show_loading_screen()
        thread = threading.Thread(target=self.process_sorted_replays(paths=paths))
        thread.start()

        print(f"processing time: {time.time() - start}")

    def process_replays(self, paths: list[str]):
        self.database = database.add_to_container(paths=paths, matches_database=self.database)
        self.refresh_rows()
        self.root.update_idletasks()

    def process_sorted_replays(self, paths: list[str]):
        # self.sorted_data = database.add_to_container(paths=paths, sorted_dict=self.sorted_data)
        self.sorted_data = database.add_to_container_and_update_tables(paths=paths, sorted_dict=self.sorted_data, hero_table=self.hero_table)
        self.refresh_rows()
        self.root.update_idletasks()

        # utils.update_player_tables()

    # todo opens a sub-window with a slideshow on how to use basic features
    def open_help_menu(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = RecapperGui(root)
    root.mainloop()
