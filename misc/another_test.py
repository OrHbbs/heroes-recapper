import tkinter as tk
from PIL import Image, ImageTk

class ResizableImageCanvas(tk.Tk):
    def __init__(self, image_path):
        super().__init__()

        self.title("Resizable Background Image")
        self.geometry("600x200")

        # Load the image
        self.original_image = Image.open(image_path)
        self.original_image = self.original_image.resize((600, 150), Image.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(self.original_image)

        # Create a canvas widget and set the image as its background
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

        # Bind the configure event to detect window resize
        self.bind("<Configure>", self.on_resize)

        # Bind the ButtonRelease event to resize the image after releasing the mouse
        self.bind("<ButtonRelease-1>", self.on_mouse_release)

        # Flag to control resizing
        self.resizing = False

    def on_resize(self, event):
        # Set resizing flag to True
        self.resizing = True

    def on_mouse_release(self, event):
        if self.resizing:
            self.resizing = False
            # Get the new size of the window
            new_width = self.winfo_width()
            new_height = self.winfo_height()
            self.resize_image(new_width, new_height)

    def resize_image(self, new_width, new_height):
        # Resize the original image to fit the new window size
        resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized_image)

        # Update the canvas image
        self.canvas.itemconfig(self.image_id, image=self.photo_image)
        self.canvas.config(width=new_width, height=new_height)


if __name__ == "__main__":
    app = ResizableImageCanvas("images/alteracpass.png")  # Replace with your image path
    app.mainloop()