"""Main application entry point"""
import tkinter as tk
from tkinter import ttk, messagebox
from space_empires.models import GameState
from space_empires.universe import create_universe
from space_empires.game_logic import (
    next_player, player_lives, calculate_money, check_victory,
    do_repair, grow_population, explore_system, can_see_system,
    get_visible_systems, get_ships_in_system, get_ships_in_sector
)
from space_empires.ai import computer_turn
from space_empires.gui.main_window import MainWindow


def main():
    """Main entry point"""
    root = tk.Tk()
    root.title("Space Empires")
    root.geometry("1400x900")
    root.minsize(1024, 768)
    
    # Create game state
    state = GameState()
    state.galaxy_size = 50
    state.num_players = 4
    state.max_players = 20
    
    # Generate universe
    create_universe(state)
    
    # Create main window
    app = MainWindow(root, state)
    
    # Start game loop
    root.mainloop()


if __name__ == "__main__":
    main()