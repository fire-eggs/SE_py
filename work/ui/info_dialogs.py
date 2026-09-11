import tkinter as tk
from tkinter import ttk

from config import PLAYER_COLORS, STELLAR_OBJECTS


class SectorInfo(tk.Toplevel):
    def __init__(self, parent, game, system_idx, sector):
        super().__init__(parent)
        self.title("Sector Info")
        self.geometry("350x300")

        sys = game.systems[system_idx]
        obj_idx = sys.sectors[sector]
        obj_name = STELLAR_OBJECTS[obj_idx] if obj_idx < len(STELLAR_OBJECTS) else "Unknown"

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"System: {sys.name}", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        ttk.Label(frame, text=f"Sector: {sector} ({sector % 9 + 1}, {sector // 9 + 1})").pack(anchor="w")
        ttk.Label(frame, text=f"Terrain: {obj_name}").pack(anchor="w")

        # Ships in sector
        ships = [s for s in game.ships if s.system == system_idx and s.sector == sector]
        if ships:
            ttk.Label(frame, text="\nShips:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
            for s in ships:
                player = game.get_player(s.owner)
                color = PLAYER_COLORS.get(s.owner, "black")
                lbl = ttk.Label(frame, text=f"  {s.name} ({player.name if player else '?'})")
                lbl.pack(anchor="w")

        # Planets in sector
        planets = [p for p in game.planets if p.system == system_idx and p.sector == sector]
        if planets:
            ttk.Label(frame, text="\nPlanets:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
            for p in planets:
                colony = "None"
                if p.colony_type > 0:
                    colony = ["None", "Outpost", "Colony", "Settlement"][p.colony_type]
                ttk.Label(frame, text=f"  {p.name} (Value:{p.value} Pop:{p.population} Colony:{colony})").pack(anchor="w")

        ttk.Button(frame, text="Close", command=self.destroy).pack(pady=10)

        self.transient(parent)
        # KBR 20260910 throws exception, too early self.grab_set()


class EmpireStatus(tk.Toplevel):
    def __init__(self, parent, game, player):
        super().__init__(parent)
        self.title("Empire Status")
        self.geometry("400x350")

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Empire: {player.name}", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")

        info = [
            f"Tech Level: {player.tech}",
            f"Credits: {player.money}",
            f"Turn: {game.turn_num}",
        ]
        for line in info:
            ttk.Label(frame, text=line, font=("TkDefaultFont", 11)).pack(anchor="w", pady=2)

        # Ships
        ships = game.get_player_ships(player.index)
        ttk.Label(frame, text=f"\nShips: {len(ships)}", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        for s in ships[:10]:
            cls = game.get_ship_class(s.class_id)
            name = cls.name if cls else "?"
            ttk.Label(frame, text=f"  {s.name} ({name})").pack(anchor="w")

        # Planets
        planets = [p for p in game.planets if p.owner == player.index]
        ttk.Label(frame, text=f"\nColonies: {len(planets)}", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        for p in planets[:10]:
            colony = ["None", "Outpost", "Colony", "Settlement"][p.colony_type]
            ttk.Label(frame, text=f"  {p.name} (Pop:{p.population} {colony})").pack(anchor="w")

        ttk.Button(frame, text="Close", command=self.destroy).pack(pady=10)

        self.transient(parent)
        self.grab_set()


class ViewShips(tk.Toplevel):
    def __init__(self, parent, game, player):
        super().__init__(parent)
        self.title("Ships")
        self.geometry("500x300")

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        columns = ("name", "class", "system", "sector", "damage")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        tree.heading("name", text="Name")
        tree.heading("class", text="Class")
        tree.heading("system", text="System")
        tree.heading("sector", text="Sector")
        tree.heading("damage", text="Damage")
        tree.column("name", width=120)
        tree.column("class", width=80)
        tree.column("system", width=80)
        tree.column("sector", width=50)
        tree.column("damage", width=60)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for s in game.get_player_ships(player.index):
            cls = game.get_ship_class(s.class_id)
            cls_name = cls.name if cls else "?"
            sys_name = game.systems[s.system].name
            tree.insert("", "end", values=(s.name, cls_name, sys_name, s.sector, s.damage))

        ttk.Button(frame, text="Close", command=self.destroy).pack(pady=5)

        self.transient(parent)
        self.grab_set()


class ViewColonies(tk.Toplevel):
    def __init__(self, parent, game, player):
        super().__init__(parent)
        self.title("Colonies")
        self.geometry("500x300")

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        columns = ("name", "type", "pop", "value", "system")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        tree.heading("name", text="Name")
        tree.heading("type", text="Type")
        tree.heading("pop", text="Population")
        tree.heading("value", text="Value")
        tree.heading("system", text="System")
        tree.column("name", width=120)
        tree.column("type", width=80)
        tree.column("pop", width=80)
        tree.column("value", width=60)
        tree.column("system", width=80)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for p in game.planets:
            if p.owner == player.index:
                colony = ["None", "Outpost", "Colony", "Settlement"][p.colony_type]
                sys_name = game.systems[p.system].name
                tree.insert("", "end", values=(p.name, colony, p.population, p.value, sys_name))

        ttk.Button(frame, text="Close", command=self.destroy).pack(pady=5)

        self.transient(parent)
        self.grab_set()
