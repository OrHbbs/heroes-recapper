import datetime
import json
import threading
import os
import time
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import sv_ttk
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
from sortedcontainers import SortedDict
from tktooltip import ToolTip

import utils
import database

__version__ = "0.1.2"


class RecapperGui:

    def __init__(self, root):

        self.recapper_dir = os.path.join(os.getenv('LOCALAPPDATA'), "Heroes Recapper")
        os.makedirs(self.recapper_dir, exist_ok=True)

        # todo check if there's a better way to do this (dev vs build difference in paths)
        if os.path.exists("images/not-found.png"):
            self.dist_prefix = ""
        else:
            self.dist_prefix = "_internal/"

        self.bg_img = None
        self.tree = None
        self.tab2_hero_images = {}
        self.tab3_hero_images = {}

        self.tab1_canvas = None
        self.tab2_canvas = None
        self.tab3_canvas = None
        self.tab4_canvas = None

        self.tab2_tree = None
        self.tab3_tree = None

        self.tab2_data = None
        self.tab3_data = None

        self.tab2_frame = None
        self.tab3_frame = None
        self.tab4_frame = None

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

        self.tab2_sort_state = {"column": None, "ascending": False}
        self.tab3_sort_state = {"column": None, "ascending": False}

        self.root = root
        self.hero_table = None

        sv_ttk.set_theme("dark")

        self.root.title(f"Heroes Recapper {__version__}")
        self.root.geometry("850x700")

        # try:
        #     self.database = database.load_from_pickle("new_pickle.pkl")
        # except FileNotFoundError:
        #     self.database = pd.DataFrame()

        try:
            with open(f"{self.recapper_dir}/gui_output.json", 'r') as f:
                self.sorted_data = utils.load_partial_json(f"{self.recapper_dir}/gui_output.json")
        except FileNotFoundError:
            self.sorted_data = SortedDict(lambda x: -x)

        try:
            with open(f"{self.recapper_dir}/hero_table.json", 'r') as f:
                self.hero_table = json.load(f)
        except FileNotFoundError:
            self.hero_table = utils.create_empty_hero_table()

        self.selected_match = None

        # if len(self.sorted_data) > 0:
        #     _, self.selected_match = self.sorted_data.peekitem()

        self.limit = 0
        self.set_limit()

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

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab1 = tk.Frame(self.notebook)
        self.tab2 = tk.Frame(self.notebook)
        self.tab3 = tk.Frame(self.notebook)
        self.tab4 = tk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="Replays")
        self.notebook.add(self.tab2, text="Match Details")
        self.notebook.add(self.tab3, text="Hero Stats")
        self.notebook.add(self.tab4, text="Player Stats")

        self.create_tab1_content()
        self.create_tab2_content()
        self.create_tab3_content()
        self.create_tab4_content()

    def create_tab1_content(self):
        label = tk.Label(self.tab1, text="Filters")
        label.pack(pady=20, padx=20)

        self.tab1_canvas = tk.Canvas(self.tab1, relief=tk.SUNKEN)
        self.tab1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.tab1, orient=tk.VERTICAL, command=self.tab1_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tab1_canvas.configure(yscrollcommand=scrollbar.set, yscrollincrement=82)

        self.inner_frame = tk.Frame(self.tab1_canvas)
        self.inner_frame.bind("<Configure>",
                              lambda e: self.tab1_canvas.configure(scrollregion=self.tab1_canvas.bbox("all")))

        self.inner_frame_id = self.tab1_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.tab1_canvas.bind("<Configure>", self.on_canvas_configure)

        for i in range(self.limit):
            self.create_row(i)

    def on_canvas_configure(self, event):
        # resizes the subcanvas
        canvas_width = event.width - 10
        self.tab1_canvas.itemconfig(self.inner_frame_id, width=canvas_width)

    def create_row(self, row_number):
        row_height = 350
        row_width = 700
        match_data = database.get_nth_value(self.sorted_data, row_number)

        bg_img_src = f"{self.dist_prefix}images/{utils.clean_string(match_data['map'])}.png"

        try:
            original_bg_img = Image.open(bg_img_src)
            if not hasattr(self, 'original_bg_images'):
                self.original_bg_images = []
            self.original_bg_images.append(original_bg_img)
            bg_img = original_bg_img.resize((row_width, row_height), Image.LANCZOS)
            darkened_img = ImageEnhance.Brightness(bg_img).enhance(0.5)
            bg_img = ImageTk.PhotoImage(darkened_img)
        except Exception as e:
            print(f"Image for {bg_img_src} not found or error: {e}")
            bg_img = None

        sub_frame = tk.Frame(self.inner_frame, bd=2, relief="solid", height=row_height)
        sub_frame.pack(pady=10, fill=tk.X, expand=True)

        sub_canvas = tk.Canvas(sub_frame, height=300)
        sub_canvas.pack(fill=tk.BOTH, expand=True)

        if bg_img:
            self.bg_img_id = sub_canvas.create_image(0, 0, anchor="nw", image=bg_img)
            sub_canvas.image = bg_img

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
        self.set_limit()

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for i in range(self.limit):
            self.create_row(i)

        self.hide_loading_screen()

    def set_selected_match(self, match):
        if self.selected_match != match:
            self.selected_match = match
            self.refresh_tables()
        return

    def create_hero_icon(self, canvas, match_data, index, x_pos, y_pos):
        hero_name = utils.clean_entity_name(match_data[f"{index + 1}_hero"])
        image_path = f"{self.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"

        border_color = "blue" if index < 5 else "red"
        img = self.draw_image(image_path, border_color=border_color, shape="circle")

        image_button = tk.Button(canvas, highlightcolor=border_color, image=img,
                                 command=lambda hero=hero_name: self.on_hero_click(hero), borderwidth='2')
        image_button.image = img
        ToolTip(image_button, msg=match_data[f"{index + 1}_name"], delay=0.5)

        if index < 5:
            canvas.create_window(x_pos, y_pos, anchor='nw', window=image_button)
        else:
            canvas.create_window(x_pos, y_pos, anchor='nw', window=image_button)

    def reposition_red_icons(self, canvas, window_id, index, y_pos):
        canvas_width = canvas.winfo_width()

        icon_width = 50
        icon_spacing = 60
        icon_start_red_x = canvas_width - (icon_spacing * (10 - index)) + (icon_spacing - icon_width) // 2

        canvas.coords(window_id, icon_start_red_x, y_pos)

    def on_hero_click(self, hero_name):
        print(f"Hero clicked: {hero_name}")

    def create_tab2_content(self):

        self.tab2_canvas = tk.Canvas(self.tab2, relief=tk.SUNKEN)
        self.tab2_canvas.pack(fill=tk.BOTH)

        if self.selected_match is not None:
            self.refresh_tab2_table()

    def refresh_tab2_table(self):

        label = tk.Label(self.tab2_canvas, text=f"{self.selected_match.get('date')}\n"
                                                f"{self.selected_match.get('gameMode')}: {self.selected_match.get('map')}\n"
                                                f"{str(datetime.timedelta(seconds=int(self.selected_match.get('duration')) - 45))}\n"
                                                f"{utils.get_winner(self.selected_match.get('1_result'))}\n"
                         )
        label.pack(pady=20, padx=20)

        columns = ["Number", "Player", "Hero", "Kills", "Assists", "Deaths", "Hero Damage", "Siege Damage", "Healing",
                   "Damage Taken", "XP Contribution"]
        column_widths = [5, 80, 60, 5, 5, 5, 30, 30, 30, 30, 20]

        self.tab2_frame = tk.Frame(self.tab2_canvas)
        self.tab2_frame.pack(fill=tk.BOTH, expand=True)

        self.tab2_tree = ttk.Treeview(self.tab2_frame, columns=columns, show="tree headings")
        self.tab2_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for col, width in zip(columns, column_widths):
            self.tab2_tree.heading(col, text=col,
                                   command=lambda _col=col: self.sort_by_column(col=_col, tab_tree=self.tab2_tree,
                                                                                tab_sort_state=self.tab2_sort_state))
            self.tab2_tree.column(col, anchor="center", width=width, )

        scrollbar = ttk.Scrollbar(self.tab2_frame, orient=tk.VERTICAL, command=self.tab2_tree.yview)
        self.tab2_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        match_data = self.selected_match

        for row in self.tab2_tree.get_children():
            self.tab2_tree.delete(row)

        self.tab2_data = []
        self.tab2_hero_images = {}

        self.tab2_tree.tag_configure('blue_row', background='#08075e')
        self.tab2_tree.tag_configure('red_row', background='#731009')

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
            self.tab2_data.append(row)

            image_path = f"{self.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"

            img = self.draw_image(image_path, border_width=0, size=40)
            self.tab2_hero_images[hero_name] = img

            if i <= 5:
                self.tab2_tree.insert("", tk.END, text='', values=row, image=self.tab2_hero_images[hero_name],
                                      tags=('blue_row',))
            else:
                self.tab2_tree.insert("", tk.END, text='', values=row, image=self.tab2_hero_images[hero_name],
                                      tags=('red_row',))

            self.tab2_tree.heading('#0', text='Icon', anchor='center')
            self.tab2_tree.column('#0', width=20)

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

        for column in tab_tree["columns"]:
            if column == col:
                direction = "▲" if tab_sort_state[col] else "▼"
                tab_tree.heading(column, text=f"{col} {direction}")
            else:
                tab_tree.heading(column, text=column)

    def refresh_tables(self):

        for widget in self.tab2_canvas.winfo_children():
            widget.destroy()
        self.tab2_canvas.configure(scrollregion=(0, 0, 0, 0))
        self.refresh_tab2_table()

    def create_tab3_content(self):

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

        label = tk.Label(self.tab3, text="Hero Stats")
        label.pack(pady=20, padx=20)

        self.tab3_canvas = tk.Canvas(self.tab3, relief=tk.SUNKEN)
        self.tab3_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tab3_frame = tk.Frame(self.tab3_canvas)
        self.tab3_frame.pack(fill=tk.BOTH, expand=True)

        columns = ["Hero", "Winrate %", "Confidence", "Popularity %", "Pick Rate %", "Ban Rate %", "Influence",
                   "Games Played"]
        column_widths = [50, 100, 80, 80, 100, 100, 100, 100, 100, 120]

        style = ttk.Style()
        style.configure("Treeview", rowheight=40)

        scrollbar = tk.Scrollbar(self.tab3_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tab3_tree = ttk.Treeview(self.tab3_frame, columns=columns, selectmode='none', show="tree headings",
                                      yscrollcommand=scrollbar.set, height=50)
        self.tab3_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tab3_tree.yview)

        for col, width in zip(columns, column_widths):
            self.tab3_tree.heading(col, text=col,
                                   command=lambda _col=col: self.sort_by_column(col=_col, tab_tree=self.tab3_tree,
                                                                                tab_sort_state=self.tab3_sort_state))
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
                f"{100 * round(games_won / games_played if games_played != 0 else 0, 4)}",
                f"±{100 * round(utils.wald_interval(x=games_won, n=games_played), 4)} ",
                f"{100 * round(pick_rate + ban_rate, 4)}",
                f"{100 * round(pick_rate, 4)}",
                f"{100 * round(ban_rate, 4)}",
                "influence",  # need to calculate later
                games_played
            ]

            image_path = f"{self.dist_prefix}heroes-talents/images/heroes/{hero_name}.png"

            img = self.draw_image(image_path, border_width=0, size=40)
            self.tab3_hero_images[hero_name] = img
            self.tab3_tree.insert("", tk.END, text='', values=row, image=self.tab3_hero_images[hero_name])
            self.tab3_tree.heading('#0', text='Icon', anchor='center')
            self.tab3_tree.column('#0', width=50)

        self.tab3_canvas.update_idletasks()

    def create_tab4_content(self):
        label = tk.Label(self.tab4, text="Player Stats")
        label.pack(pady=20, padx=20)

        self.tab4_canvas = tk.Canvas(self.tab4, relief=tk.SUNKEN)
        self.tab4_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tab4_frame = tk.Frame(self.tab4_canvas)
        self.tab4_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = tk.ttk.Treeview(self.tab4_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def draw_image(self, image_path: str, border_color: str = "black", border_width: int = 2, size=50, shape="circle"):
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

    def set_limit(self):
        self.limit = min(20, len(self.sorted_data))

    def exit_app(self):
        # database.save_to_pickle("new_pickle.pkl", self.database)

        print("exiting")

        dat = dict(self.sorted_data)

        with open(f"{self.recapper_dir}/gui_output.json", "w") as outfile:
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

    # def process_replays(self, paths: list[str]):
    #     self.database = database.add_to_container(paths=paths, matches_database=self.database)
    #     self.refresh_rows()
    #     self.root.update_idletasks()

    def process_sorted_replays(self, paths: list[str], ):
        # self.sorted_data = database.add_to_container(paths=paths, sorted_dict=self.sorted_data)
        self.sorted_data = (database.add_to_container_and_update_tables(
            paths=paths, sorted_dict=self.sorted_data, recapper_dir=self.recapper_dir, hero_table=self.hero_table))
        self.refresh_rows()
        self.root.update_idletasks()

        # utils.update_player_tables()

    def open_help_menu(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = RecapperGui(root)
    root.mainloop()
