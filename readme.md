# Heroes Recapper 

Heroes Recapper is an offline replay tracker that has various features. This app currently is only compatible with windows.

Current version is 0.1

# Installation

To build this app, download the repository, copy paste the following line, and run it in terminal

pyinstaller --collect-data sv_ttk --add-data "heroes-talents/hero/*;heroes-talents/hero" --add-data "heroes-talents/images/heroes*;heroes-talents/images/heroes" --add-data "heroes-talents/images/talents*;heroes-talents/images/talents" --add-data "images/*;images" --noconfirm --name "Heroes Recapper" recapper_gui.py

An exe will be created in dist/Heroes Recapper. You can move this folder anywhere you like(make sure the contents inside - 'Heroes Recapper.exe' and the _internal subdirectory - are the same though)

Make sure to have python 3 installed

# Known issues

In order for the app to save processed replays, you must exit the app using File -> Exit. Do not just close the app.

Certain player names might not show up on "Match Details".

# Notes

This app is currently in development. There may be bugs or poor optimizations. 

Data is stored inside C:\Users\[USERNAME]\AppData\Local\Heroes Recapper