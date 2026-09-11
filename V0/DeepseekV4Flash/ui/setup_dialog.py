import tkinter as tk
from tkinter import ttk


class SetupDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Space Empires II - New Game")
        self.resizable(False, False)
        self.result = None

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Space Empires II", font=("TkDefaultFont", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        r = 1
        ttk.Label(frame, text="Human Players:").grid(row=r, column=0, sticky="w", pady=2)
        self.humans_var = tk.IntVar(value=1)
        ttk.Spinbox(frame, from_=1, to=4, textvariable=self.humans_var, width=5).grid(row=r, column=1, sticky="e", pady=2)

        r += 1
        ttk.Label(frame, text="Computer Players:").grid(row=r, column=0, sticky="w", pady=2)
        self.comps_var = tk.IntVar(value=1)
        ttk.Spinbox(frame, from_=0, to=10, textvariable=self.comps_var, width=5).grid(row=r, column=1, sticky="e", pady=2)

        r += 1
        ttk.Label(frame, text="Map Size:").grid(row=r, column=0, sticky="w", pady=2)
        self.map_var = tk.StringVar(value="Medium")
        ttk.Combobox(frame, textvariable=self.map_var, values=["Small", "Medium", "Large"], state="readonly", width=12).grid(row=r, column=1, sticky="e", pady=2)

        r += 1
        ttk.Label(frame, text="Computer Difficulty:").grid(row=r, column=0, sticky="w", pady=2)
        self.diff_var = tk.IntVar(value=2)
        ttk.Combobox(frame, textvariable=self.diff_var, values=[1, 2, 3], state="readonly", width=5).grid(row=r, column=1, sticky="e", pady=2)

        r += 1
        ttk.Label(frame, text="Warp Frequency:").grid(row=r, column=0, sticky="w", pady=2)
        self.warp_var = tk.IntVar(value=2)
        ttk.Spinbox(frame, from_=1, to=5, textvariable=self.warp_var, width=5).grid(row=r, column=1, sticky="e", pady=2)

        r += 1
        ttk.Label(frame, text="Empire Separation:").grid(row=r, column=0, sticky="w", pady=2)
        self.sep_var = tk.IntVar(value=6)
        ttk.Spinbox(frame, from_=3, to=12, textvariable=self.sep_var, width=5).grid(row=r, column=1, sticky="e", pady=2)

        r += 1
        ttk.Label(frame, text="Starting Tech:").grid(row=r, column=0, sticky="w", pady=2)
        self.tech_var = tk.IntVar(value=1)
        ttk.Spinbox(frame, from_=1, to=11, textvariable=self.tech_var, width=5).grid(row=r, column=1, sticky="e", pady=2)

        r += 1
        self.neutrals_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Include Neutrals", variable=self.neutrals_var).grid(row=r, column=0, columnspan=2, sticky="w", pady=2)

        r += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=r, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="Start Game", command=self._ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel).pack(side="left", padx=5)

        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def _ok(self):
        self.result = {
            "humans": self.humans_var.get(),
            "comps": self.comps_var.get(),
            "map_size": self.map_var.get(),
            "difficulty": self.diff_var.get(),
            "warp_freq": self.warp_var.get(),
            "separation": self.sep_var.get(),
            "start_tech": self.tech_var.get(),
            "neutrals": self.neutrals_var.get(),
        }
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()
