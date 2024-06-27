import tkinter as tk
from tkinter import ttk, Menu, filedialog
import pandas as pd
import numpy as np
import sv_ttk
from PIL import Image, ImageDraw, ImageTk

from database import add_to_database
from utils import clean_string, test_paths


def create_circular_image(image_path: str):
    img = Image.open(image_path).resize((50, 50), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
    img.putalpha(mask)
    return ImageTk.PhotoImage(img)

def get_winner(side: int):
    if side == 1:
        return "blue"
    return "red"

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
        newDF = pd.DataFrame()
        self.database = add_to_database(replays, newDF)
        self.create_widgets()

    def create_widgets(self):
        self.create_menu()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=1)

        self.main_canvas = tk.Canvas(self.frame)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.main_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        self.main_canvas.bind('<Configure>', lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))

        limit = min(20, len(self.database.index))

        for i in range(limit):
            self.show_row(i)

    def create_menu(self):
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Replay", command=self.select_replay)
        file_menu.add_command(label="Select Directory", command=self.select_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        settings_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set Constraints")

        about_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="About", menu=about_menu)
        about_menu.add_cascade(label="About", menu=settings_menu)

        help_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="quick guide", command=self.open_help_menu)

    def select_replay(self):
        file_path = filedialog.askopenfilename(filetypes=[("Storm Replay Files", "*.StormReplay")])
        if file_path:
            self.display_replays(file_path)

    # todo
    def select_directory(self):
        file_path = filedialog.askdirectory()
        return

    # todo opens a sub-window with a slideshow on how to use basic features
    def open_help_menu(self):
        pass

    # todo
    def display_replays(self, replays):
        pass

    def show_hero_icon(self, hero_name, row_number):
        self.image = tk.PhotoImage(file="heroes-talents/images/heroes/alarak.png")

        self.label = tk.Label(self.root, image=self.image)
        self.label.pack()

    def show_row(self, row_number):

        sub_frame = tk.Frame(self.main_canvas)
        sub_frame.pack(pady=10)

        text_widget = tk.Text(sub_frame, wrap="word", height=5, width=50)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, self.database['map'][row_number] + "\n")
        text_widget.insert(tk.END, get_winner(self.database['1_result'][row_number]))
        text_widget.pack(side=tk.LEFT, padx=10)
        image_container = tk.Frame(sub_frame)
        image_container.pack(side=tk.LEFT, padx=10)

        for i in range(10):
            self.show_hero_icon(image_container, row_number, i)

    def show_hero_icon(self, container, row_number, index):
        hero_name = clean_string(self.database[f"{index + 1}_hero"][row_number])
        image_path = f"heroes-talents/images/heroes/{hero_name}.png"
        circular_image = create_circular_image(image_path)

        image_button = tk.Button(container, image=circular_image, command=lambda hero=hero_name: self.on_hero_click(hero), borderwidth='0')
        image_button.image = circular_image
        image_button.pack(side=tk.LEFT, padx=10)

    def on_hero_click(self, hero_name):
        print(f"Hero clicked: {hero_name}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RecapperGui(root)
    root.mainloop()