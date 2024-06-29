import datetime
import os
import tkinter as tk
from tkinter import ttk, Menu, filedialog
import pandas as pd
import numpy as np
import sv_ttk
from PIL import Image, ImageDraw, ImageTk

import database
from database import add_to_database
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

        self.scrollbar = None
        self.button = None
        self.label = None
        self.main_canvas = None
        self.root = root

        sv_ttk.set_theme("dark")

        self.root.title("Heroes Recapper")
        self.root.geometry("1200x400")

        replays = test_paths
        self.database = pd.DataFrame()

        try:
            self.database = database.load_from_pickle("new_pickle.pkl")
        except FileNotFoundError:
            pass

        self.limit = 0
        self.set_limit()

        # self.database = add_to_database(paths=["test-data/infernal.StormReplay", "test-data/sample0.StormReplay"], matches_database=newDF)
        self.create_widgets()

        print(database)

    def create_widgets(self):
        self.create_menu()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=1)

        self.main_canvas = tk.Canvas(self.frame)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.main_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        self.main_canvas.bind('<Configure>',
                              lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))

        for i in range(self.limit):
            self.show_row(i)

    def create_menu(self):
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Replay", command=self.select_replay)
        file_menu.add_command(label="Select Directory", command=self.select_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)

        settings_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set Constraints")

        about_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="About", menu=about_menu)
        about_menu.add_cascade(label="About")

        help_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="quick guide", command=self.open_help_menu)

    def set_limit(self):
        self.limit = min(20, len(self.database.index))
        print(self.limit)

    def exit_app(self):
        database.save_to_pickle("new_pickle.pkl", self.database)
        print(self.database)
        root.destroy()

    def select_replay(self):
        file_path = filedialog.askopenfilename(filetypes=[("Storm Replay Files", "*.StormReplay")])
        if file_path:
            self.database = add_to_database(paths=[file_path], matches_database=self.database)

        self.refresh_rows()
        self.root.update_idletasks()

    def select_directory(self):
        file_path = filedialog.askdirectory()
        paths = []

        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.endswith(".StormReplay"):
                    paths.append(os.path.join(root, file))

        self.database = database.add_to_database(paths=paths, matches_database=self.database)
        self.refresh_rows()
        self.root.update_idletasks()

        return

    # todo opens a sub-window with a slideshow on how to use basic features
    def open_help_menu(self):
        pass

    def show_row(self, row_number):

        sub_frame = tk.Frame(self.main_canvas)
        sub_frame.pack(pady=10)

        text_widget = tk.Text(sub_frame, wrap="word", height=5, width=50)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, self.database['map'][row_number] + "\n")
        text_widget.insert(tk.END, get_winner(self.database['1_result'][row_number]) + "\n")
        text_widget.insert(tk.END, str(datetime.timedelta(seconds=int(self.database['duration'][row_number]) - 45)))
        text_widget.pack(side=tk.LEFT, padx=10)
        image_container = tk.Frame(sub_frame)
        image_container.pack(side=tk.LEFT, padx=10)

        for i in range(10):
            self.show_hero_icon(image_container, row_number, i)

    def refresh_rows(self):
        self.set_limit()

        for widget in self.main_canvas.winfo_children():
            widget.destroy()

        for i in range(self.limit):
            self.show_row(i)

        print(self.database)

    def show_hero_icon(self, container, row_number, index):
        hero_name = clean_string(self.database[f"{index + 1}_hero"][row_number])
        image_path = f"heroes-talents/images/heroes/{hero_name}.png"

        border_color = "blue"
        if index >= 5:
            border_color = "red"
        circular_image = create_circular_image(image_path, border_color=border_color)

        image_button = tk.Button(container, image=circular_image,
                                 command=lambda hero=hero_name: self.on_hero_click(hero), borderwidth='0')
        image_button.image = circular_image
        image_button.pack(side=tk.LEFT, padx=10)

    def on_hero_click(self, hero_name):
        print(f"Hero clicked: {hero_name}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RecapperGui(root)
    root.mainloop()
