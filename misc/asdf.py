import tkinter as tk
from tkinter import ttk

class TreeviewExample(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Treeview Font Color Example")
        self.geometry("400x300")

        # Create a Treeview widget
        self.tree = ttk.Treeview(self, columns=("Name", "Age"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Define columns
        self.tree.heading("Name", text="Name")
        self.tree.heading("Age", text="Age")

        # Define tags with different font colors
        self.tree.tag_configure('red', foreground='#000000')
        self.tree.tag_configure('blue', foreground='blue')
        self.tree.tag_configure('green', foreground='green')

        # Insert some items with different tags
        self.tree.insert("", "end", values=("Alice", 25), tags=('red',))
        self.tree.insert("", "end", values=("Bob", 30), tags=('blue',))
        self.tree.insert("", "end", values=("Charlie", 35), tags=('green',))
        self.tree.insert("", "end", values=("Diana", 28), tags=('red',))

if __name__ == "__main__":
    app = TreeviewExample()
    app.mainloop()