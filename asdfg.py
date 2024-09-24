import tkinter as tk
from custom_hovertip import CustomTooltipLabel

def create_hover_area(root, area_coords, tooltip_text):
    x1, y1, x2, y2 = area_coords

    # Create an invisible label that acts as the hover area
    hover_area = tk.Label(root, bg="white")  # Make this visible for testing by changing the bg color
    hover_area.place(x=x1, y=y1, width=x2-x1, height=y2-y1)

    # Attach the CustomTooltipLabel to this hover area
    CustomTooltipLabel(hover_area,
                       text=tooltip_text,
                       hover_delay=300,
                       justify="center",
                       wraplength=300,
                       background="#1c1c1c",
                       foreground="white",
                       border=1,
                       relief='groove')

# Main application
root = tk.Tk()
root.geometry("400x300")

# Define the area for hover tooltip (x1, y1, x2, y2)
hover_area_coords = (100, 100, 300, 200)

# Define tooltip text
tooltip_text = "This is a hover tooltip!"

# Create the hover area and attach the tooltip
create_hover_area(root, hover_area_coords, tooltip_text)

root.mainloop()