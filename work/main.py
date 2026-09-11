import tkinter as tk
from tkinter import messagebox

from components import init_components
from entities import load_ship_names
from game import Game
from ui.main_window import MainWindow
from ui.setup_dialog import SetupDialog


def main():
    init_components()
    load_ship_names()

    root = tk.Tk()
    #root.withdraw()
    root.title("Space Empires")
    root.geometry("1400x900")
    root.minsize(1024, 768)
    

    dlg = SetupDialog(root)
    root.update()

    if dlg.result is None:
        root.destroy()
        return

    params = dlg.result
    root.destroy()

    game = Game()
    game.init_new_game(
        num_human=params["humans"],
        num_comp=params["comps"],
        map_size=params["map_size"],
        warp_freq=params["warp_freq"],
        separation=params["separation"],
        neutrals=params["neutrals"],
        difficulty=params["difficulty"],
        start_tech=params["start_tech"],
    )

    app = MainWindow(game)
    app.mainloop()


if __name__ == "__main__":
    main()
