import tkinter as tk
from tkinter import ttk, messagebox

from economy import purchase_ship, buy_tech, get_tech_cost
from config import HULL_TYPES


class PurchaseDialog(tk.Toplevel):
    def __init__(self, parent, game, player):
        super().__init__(parent)
        self.title("Purchase Items")
        self.game = game
        self.player = player
        self.geometry("500x400")

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        info_frame = ttk.Frame(frame)
        info_frame.pack(fill="x")
        self.money_label = ttk.Label(info_frame, text=f"Credits: {player.money}")
        self.money_label.pack(side="left", padx=5)
        self.tech_label = ttk.Label(info_frame, text=f"Tech Level: {player.tech}")
        self.tech_label.pack(side="left", padx=5)
        ttk.Button(info_frame, text="Buy Tech", command=self._buy_tech).pack(side="right", padx=5)

        # Ship classes
        class_frame = ttk.LabelFrame(frame, text="Available Ship Classes", padding=5)
        class_frame.pack(fill="both", expand=True, pady=5)

        columns = ("name", "type", "cost", "speed", "size")
        self.tree = ttk.Treeview(class_frame, columns=columns, show="headings", height=8)
        self.tree.heading("name", text="Class Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("cost", text="Cost")
        self.tree.heading("speed", text="Speed")
        self.tree.heading("size", text="Size")
        self.tree.column("name", width=150)
        self.tree.column("type", width=80)
        self.tree.column("cost", width=60)
        self.tree.column("speed", width=60)
        self.tree.column("size", width=60)

        scrollbar = ttk.Scrollbar(class_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        qty_frame = ttk.Frame(frame)
        qty_frame.pack(fill="x", pady=5)
        ttk.Label(qty_frame, text="Quantity:").pack(side="left")
        self.qty_var = tk.IntVar(value=1)
        ttk.Spinbox(qty_frame, from_=1, to=20, textvariable=self.qty_var, width=5).pack(side="left", padx=5)
        ttk.Button(qty_frame, text="Purchase", command=self._purchase).pack(side="left", padx=10)
        ttk.Button(qty_frame, text="Close", command=self.destroy).pack(side="right", padx=5)

        for cls in game.ship_classes:
            if cls.owner == player.index and not cls.obsolete:
                self.tree.insert("", "end", values=(cls.name, cls.type_name, cls.cost, cls.speed, cls.size))

        self.transient(parent)
        self.grab_set()

    def _purchase(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a ship class to purchase")
            return
        item = self.tree.item(sel[0])
        class_name = item["values"][0]
        cls = None
        for c in self.game.ship_classes:
            if c.name == class_name and c.owner == self.player.index:
                cls = c
                break
        if not cls:
            return
        qty = self.qty_var.get()
        cost = cls.cost * qty
        if self.player.money < cost:
            messagebox.showwarning("Insufficient Funds", f"Need {cost} credits, have {self.player.money}")
            return

        for _ in range(qty):
            from entities import Ship
            ship = Ship(
                name=f"{self.player.name}-{self.game._next_ship_id}",
                ship_id=self.game._next_ship_id,
                class_id=cls.class_index,
                system=self.player.home_system,
                sector=40,
                owner=self.player.index,
            )
            self.game._next_ship_id += 1
            self.game.ships.append(ship)

        self.player.money -= cost
        self.money_label.config(text=f"Credits: {self.player.money}")
        messagebox.showinfo("Purchase Complete", f"Purchased {qty} {class_name}(s)")

    def _buy_tech(self):
        cost = get_tech_cost(self.player)
        if cost < 0:
            messagebox.showinfo("Max Tech", "Already at maximum tech level")
            return
        if self.player.money < cost:
            messagebox.showwarning("Insufficient Funds", f"Need {cost} credits for next tech level")
            return
        if buy_tech(self.player):
            self.tech_label.config(text=f"Tech Level: {self.player.tech}")
            self.money_label.config(text=f"Credits: {self.player.money}")
            messagebox.showinfo("Tech Purchased", f"Advanced to Tech Level {self.player.tech}")
