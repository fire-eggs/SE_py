import tkinter as tk
from tkinter import ttk

from config import COMBAT_WIDTH, COMBAT_HEIGHT, PLAYER_COLORS


class CombatView(tk.Toplevel):
    def __init__(self, parent, combat, game):
        super().__init__(parent)
        self.title("Combat")
        self.combat = combat
        self.game = game
        self.cell_size = 40
        self.geometry(f"{COMBAT_WIDTH * self.cell_size + 200}x{COMBAT_HEIGHT * self.cell_size + 80}")

        main_frame = ttk.Frame(self, padding=5)
        main_frame.pack(fill="both", expand=True)

        # Info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x")
        self.phase_label = ttk.Label(info_frame, text=f"Phase: {combat.phase}")
        self.phase_label.pack(side="left", padx=5)
        ttk.Label(info_frame, text=f"{combat.attacker_name} vs {combat.defender_name}").pack(side="left", padx=10)

        # Canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, width=COMBAT_WIDTH * self.cell_size,
                                height=COMBAT_HEIGHT * self.cell_size, bg="black")
        self.canvas.pack()

        # Ship list
        list_frame = ttk.LabelFrame(main_frame, text="Ships", padding=5)
        list_frame.pack(side="right", fill="y")

        self.ship_listbox = tk.Listbox(list_frame, width=30, height=15)
        self.ship_listbox.pack()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Next Phase", command=self._next_phase).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Retreat", command=self._retreat).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side="right", padx=5)

        self._draw()

        self.transient(parent)
        self.grab_set()

    def _draw(self):
        self.canvas.delete("all")
        # Grid
        for x in range(COMBAT_WIDTH):
            for y in range(COMBAT_HEIGHT):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                color = "#111122" if x < COMBAT_WIDTH // 2 else "#221111"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#333")

        # Ships
        for cs in self.combat.get_all_ships():
            if cs.destroyed:
                continue
            x = cs.x * self.cell_size + 4
            y = cs.y * self.cell_size + 4
            color = PLAYER_COLORS.get(cs.owner, "white")
            self.canvas.create_oval(x, y, x + self.cell_size - 8, y + self.cell_size - 8,
                                    fill=color, outline="white", width=2)
            self.canvas.create_text(x + self.cell_size // 2 - 4, y + self.cell_size // 2 - 4,
                                    text=cs.name[:2], fill="white", font=("TkDefaultFont", 8, "bold"))

        # Fighters
        for f in self.combat.fighters:
            if f.destroyed:
                continue
            x = f.x * self.cell_size + 14
            y = f.y * self.cell_size + 14
            color = PLAYER_COLORS.get(f.owner, "white")
            self.canvas.create_rectangle(x, y, x + 8, y + 8, fill=color, outline="white")

        # Ship list
        self.ship_listbox.delete(0, "end")
        for cs in self.combat.get_all_ships():
            status = "OK" if not cs.destroyed else "DESTROYED"
            side = "ATK" if cs in self.combat.attackers else "DEF"
            self.ship_listbox.insert("end", f"[{side}] {cs.name} ({cs.class_name}) HP:{cs.max_damage - cs.damage}/{cs.max_damage} {status}")

    def _next_phase(self):
        if self.combat.over:
            return
        self.combat.process_phase()
        self.phase_label.config(text=f"Phase: {self.combat.phase}")
        self._draw()
        if self.combat.over:
            winner = self.combat.attacker_name if self.combat.attacker_won else self.combat.defender_name
            self.phase_label.config(text=f"Combat Over! {winner} wins!")

    def _retreat(self):
        self.combat.over = True
        self._draw()
        self.phase_label.config(text="Retreated!")
