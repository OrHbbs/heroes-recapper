import datetime
import threading
import os
import tkinter as tk
import pandas as pd
import sv_ttk
from PIL import Image, ImageDraw, ImageTk
from tktooltip import ToolTip

import database
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

        self.tab1 = None
        self.tab2 = None
        self.tab3 = None
        self.inner_frame = None
        self.inner_frame_id = None
        self.notebook = None
        self.scrollbar = None
        self.button = None
        self.label = None
        self.tab1_canvas = None
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
        self.notebook.add(self.tab3, text="Player Stats")

        self.create_tab1_content()
        self.create_tab2_content()
        self.create_tab3_content()

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
        sub_frame.pack(pady=10, fill=tk.X, expand=True)

        text_widget = tk.Label(sub_frame,
                               text=f"{self.database['map'][row_number]}\n{get_winner(self.database['1_result'][row_number])}\n{str(datetime.timedelta(seconds=int(self.database['duration'][row_number]) - 45))}",
                               justify="center")
        text_widget.pack(pady=5, padx=10)

        image_container = tk.Frame(sub_frame)
        image_container.pack(pady=10, padx=10, anchor="w")

        for i in range(10):
            self.create_hero_icon(image_container, row_number, i)

        self.tab1_canvas.update_idletasks()
        self.tab1_canvas.configure(scrollregion=self.tab1_canvas.bbox("all"))

    def refresh_rows(self):
        self.set_limit()

        for widget in self.tab1_canvas.winfo_children():
            widget.destroy()

        for i in range(self.limit):
            self.create_row(i)

        print(self.database)

        self.hide_loading_screen()

    def create_hero_icon(self, container, row_number, index):
        hero_name = clean_string(self.database[f"{index + 1}_hero"][row_number])
        image_path = f"heroes-talents/images/heroes/{hero_name}.png"

        border_color = "blue"
        if index >= 5:
            border_color = "red"
        circular_image = create_circular_image(image_path, border_color=border_color)

        image_button = tk.Button(container, image=circular_image,
                                 command=lambda hero=hero_name: self.on_hero_click(hero), borderwidth='0')
        image_button.image = circular_image
        ToolTip(image_button, msg=self.database[f"{index + 1}_name"][row_number], delay=0.5)

        if index == 5:
            image_button.pack(side=tk.LEFT, padx=(50, 10))
        else:
            image_button.pack(side=tk.LEFT, padx=10)

    def on_hero_click(self, hero_name):
        print(f"Hero clicked: {hero_name}")

    def create_tab2_content(self):
        label = tk.Label(self.tab2, text="Select A Match")
        label.pack(pady=20, padx=20)

    def create_tab3_content(self):
        label = tk.Label(self.tab3, text="Player Details")
        label.pack(pady=20, padx=20)

    def set_limit(self):
        self.limit = min(20, len(self.database.index))
        print(self.limit)

    def exit_app(self):
        database.save_to_pickle("new_pickle.pkl", self.database)
        print(self.database)
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
        paths = tk.filedialog.askopenfilename(filetypes=[("Storm Replay Files", "*.StormReplay")])

        self.show_loading_screen()

        thread = threading.Thread(target=self.process_replays)
        thread.start()
        self.process_replays([paths])

    def select_directory(self):
        file_path = tk.filedialog.askdirectory()
        paths = []

        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.endswith(".StormReplay"):
                    paths.append(os.path.join(root, file))

        self.show_loading_screen()
        thread = threading.Thread(target=self.process_replays)
        thread.start()
        self.process_replays(paths)

    def process_replays(self, paths: list[str]):
        self.database = database.add_to_database(paths=paths, matches_database=self.database)
        self.refresh_rows()
        self.root.update_idletasks()

    # todo opens a sub-window with a slideshow on how to use basic features
    def open_help_menu(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = RecapperGui(root)
    root.mainloop()
