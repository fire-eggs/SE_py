import tkinter as tk
from tkinter import ttk, messagebox

from config import HULL_TYPES, CLASS_TYPES
from components import ALL_COMPONENTS, get_compo, count_engines


class DesignDialog(tk.Toplevel):
    def __init__(self, parent, game, player):
        super().__init__(parent)
        self.title("Ship Designer")
        self.game = game
        self.player = player
        self.result_class = None
        self.geometry("600x650") # KBR 20260914 initial height too short

        self.compos = []
        self.shields = 0
        self.selected_hull = 0

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        # Hull selection
        hull_frame = ttk.LabelFrame(frame, text="Hull", padding=5)
        hull_frame.pack(fill="x", pady=2)

        self.hull_var = tk.StringVar()
        # KBR 20260914 player can't use hull above their tech level
        hull_names = [f"{h['abbr']} - {h['name']} (S:{h['size']} C:{h['cost']} T:{h['tech']})" for h in HULL_TYPES if h['tech'] <= player.tech]
        self.hull_combo = ttk.Combobox(hull_frame, textvariable=self.hull_var, values=hull_names, state="readonly", width=60)
        self.hull_combo.pack(fill="x")
        self.hull_combo.current(0)
        self.hull_combo.bind("<<ComboboxSelected>>", self._on_hull_change)

        # Class type
        ttk.Label(hull_frame, text="Class Type:").pack(anchor="w")
        self.type_var = tk.StringVar(value="ATK")
        type_frame = ttk.Frame(hull_frame)
        type_frame.pack(fill="x")
        for code, name in CLASS_TYPES.items():
            ttk.Radiobutton(type_frame, text=f"{code} ({name})", variable=self.type_var, value=code).pack(side="left", padx=2)

        # Available components
        compo_frame = ttk.LabelFrame(frame, text="Available Components (double-click to add)", padding=5)
        compo_frame.pack(fill="both", expand=True, pady=2)

        scrollbar = ttk.Scrollbar(compo_frame)
        scrollbar.pack(side="right", fill="y")

        self.compo_listbox = tk.Listbox(compo_frame, yscrollcommand=scrollbar.set, height=8)
        self.compo_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.compo_listbox.yview)
        self.compo_listbox.bind("<Double-Button-1>", self._add_compo)

        # Added components
        added_frame = ttk.LabelFrame(frame, text="Components (double-click to remove)", padding=5)
        added_frame.pack(fill="both", expand=True, pady=2)

        scrollbar2 = ttk.Scrollbar(added_frame)
        scrollbar2.pack(side="right", fill="y")

        self.added_listbox = tk.Listbox(added_frame, yscrollcommand=scrollbar2.set, height=6)
        self.added_listbox.pack(fill="both", expand=True)
        scrollbar2.config(command=self.added_listbox.yview)
        self.added_listbox.bind("<Double-Button-1>", self._remove_compo)

        # Info
        info_frame = ttk.LabelFrame(frame, text="Ship Stats", padding=5)
        info_frame.pack(fill="x", pady=2)

        self.info_var = tk.StringVar(value="Cost: 0 | Space Left: 0 | Speed: 0 | Shields: 0")
        ttk.Label(info_frame, textvariable=self.info_var).pack()

        # Shields
        shield_frame = ttk.Frame(info_frame)
        shield_frame.pack(fill="x")
        ttk.Label(shield_frame, text="Shields:").pack(side="left")
        self.shields_var = tk.IntVar(value=0)
        ttk.Spinbox(shield_frame, from_=0, to=50, textvariable=self.shields_var, width=5, command=self._update_info).pack(side="left", padx=5)
        ttk.Label(shield_frame, text="(1 credit per point)").pack(side="left")

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="Add Class", command=self._ok).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=2)

        self._refresh_components()
        self._update_info()

        self.transient(parent)
        self.grab_set()

    def _on_hull_change(self, event=None):
        self.selected_hull = self.hull_combo.current()
        self.compos.clear() # KBR 20260914 on hull change, reset selected components
        self._refresh_components()
        self._update_info()

    def _selected_hull(self):
        # KBR 20260914 hulls are now filtered, get the actual hull selected
        target_value = self.hull_combo.get()[0:2]
        #hull = HULL_TYPES[self.selected_hull]
        hull = next((x for x in HULL_TYPES if x.get("abbr") == target_value), None)
        return hull

    def _refresh_components(self):
        self.compo_listbox.delete(0, "end")
        
        hull = self._selected_hull()
        hull_space = hull["size"]
        used = sum(get_compo(i).size for i in self.compos) + self.shields
        space_left = hull_space - used
        
        for i, comp in enumerate(ALL_COMPONENTS):
            if not self.player.avail_compo[i]:
                continue
            if comp.size > space_left:
                continue
            if comp.category == "H":
                continue
            if (comp.category == "E" or comp.category == "C" or comp.category == "M") and hull["max_eng"] < 1: # KBR 20260914 no engines/cargo/settle for space stations
                continue
            if comp.category == "E" and hull["max_eng"] > 0:
                eng_count = count_engines([get_compo(c) for c in self.compos])
                if eng_count >= hull["max_eng"]:
                    continue
            self.compo_listbox.insert("end", f"{comp.name} (S:{comp.size} C:{comp.cost} T:{comp.tech})")

    def _add_compo(self, event=None):
        sel = self.compo_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        text = self.compo_listbox.get(idx)

        found = None
        for i, comp in enumerate(ALL_COMPONENTS):
            if comp.name in text and self.player.avail_compo[i]:
                found = comp
                break
        if found is None:
            return

        #hull = HULL_TYPES[self.selected_hull]
        hull = self._selected_hull()
        used = sum(get_compo(i).size for i in self.compos) + self.shields
        if used + found.size > hull["size"]:
            messagebox.showwarning("No Space", "Not enough hull space!")
            return

        self.compos.append(found.index)
        self._refresh_components()
        self._update_info()

    def _remove_compo(self, event=None):
        sel = self.added_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.compos):
            self.compos.pop(idx)
            self._refresh_components()
            self._update_info()

    def _update_info(self):
        #hull = HULL_TYPES[self.selected_hull]
        hull = self._selected_hull()
        used = sum(get_compo(i).size for i in self.compos)
        shield_pts = self.shields_var.get()
        used += shield_pts
        space_left = hull["size"] - used

        cost = hull["cost"] + sum(get_compo(i).cost for i in self.compos) + shield_pts * 1
        eng_count = count_engines([get_compo(i) for i in self.compos])
        speed = eng_count // hull["epm"] if hull["epm"] > 0 else 0

        self.info_var.set(f"Cost: {cost} | Space Left: {space_left} | Speed: {speed} | Shields: {shield_pts}")

        self.added_listbox.delete(0, "end")
        for ci in self.compos:
            comp = get_compo(ci)
            self.added_listbox.insert("end", f"{comp.name} (S:{comp.size} C:{comp.cost})")

    def _ok(self):
        #hull = HULL_TYPES[self.selected_hull]
        hull = self._selected_hull()
        shield_pts = self.shields_var.get()
        cost = hull["cost"] + sum(get_compo(i).cost for i in self.compos) + shield_pts * 1
        if cost <= 0:
            messagebox.showwarning("Invalid", "Ship must have components!")
            return
        self.result_class = {
            "hull": hull,
            "type_name": self.type_var.get(),
            "name": f"{hull['abbr']}-{self.player.index}",
            "compos": self.compos,
            "shields": shield_pts,
        }
        self.destroy()
