import pickle
import json
import tkinter as tk
from tkinter import ttk, messagebox

from entities import Ship, ShipClass
from components import get_compo, has_colony_module, count_engines
from config import *
from ui.setup_dialog import SetupDialog
from ui.design_dialog import DesignDialog
from ui.purchase_dialog import PurchaseDialog
from ui.combat_view import CombatView
from ui.info_dialogs import SectorInfo, EmpireStatus, ViewShips, ViewColonies


class MainWindow(tk.Tk):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.title("Space Empires II")
        self.geometry("900x700")

        self.current_system = 0
        self.selected_sector = 40
        self.selected_ship = None
        self.sector_from = None

        self._build_ui()
        # KBR 20260913 start in the player's home system
        target = game.players[0].home_system
        self.GotoSystem(target)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Menu
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="End Turn", command=self._end_turn, accelerator="F10")
        game_menu.add_separator()
        game_menu.add_command(label="Save Game", command=self._save_game)
        game_menu.add_command(label="Load Game", command=self._load_game)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self._on_close)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Ships", command=self._view_ships)
        view_menu.add_command(label="Colonies", command=self._view_colonies)
        view_menu.add_command(label="Empire Status", command=self._empire_status)
        view_menu.add_command(label="Messages", command=self._view_messages)

        orders_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Orders", menu=orders_menu)
        orders_menu.add_command(label="Move to Sector", command=self._order_move)
        orders_menu.add_command(label="Colonize", command=self._order_colonize)
        orders_menu.add_command(label="Scrap Ship", command=self._order_scrap)
        orders_menu.add_command(label="Clear Orders", command=self._order_clear)

        shipyard_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Shipyard", menu=shipyard_menu)
        shipyard_menu.add_command(label="Design Ships", command=self._design_ships)
        shipyard_menu.add_command(label="Purchase Ships", command=self._purchase_ships)

        # Main layout
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True)

        # Left panel - sector map
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)

        # System info
        sys_frame = ttk.Frame(left_frame)
        sys_frame.pack(fill="x", pady=2)

        sys_inner = ttk.Frame(sys_frame)
        sys_inner.pack(fill="x")
        self.sys_label = ttk.Label(sys_inner, text="System: ", font=("TkDefaultFont", 12, "bold"))
        self.sys_label.pack(side="left", padx=5)
        self.player_label = ttk.Label(sys_inner, text="Player: ", font=("TkDefaultFont", 10))
        self.player_label.pack(side="right", padx=5)

        # Nav buttons
        nav_frame = ttk.Frame(sys_frame)
        nav_frame.pack(fill="x")
        ttk.Button(nav_frame, text="< Prev", command=self._prev_system).pack(side="left", padx=2)
        ttk.Button(nav_frame, text="Next >", command=self._next_system).pack(side="left", padx=2)
        self.sys_num_label = ttk.Label(nav_frame, text="")
        self.sys_num_label.pack(side="left", padx=10)

        # Sector grid canvas
        grid_frame = ttk.LabelFrame(left_frame, text="Sector Map", padding=2)
        grid_frame.pack(fill="both", expand=True, pady=5)

        self.cell_size = 50
        cw = SECTOR_COLS * self.cell_size
        ch = SECTOR_ROWS * self.cell_size
        self.sector_canvas = tk.Canvas(grid_frame, width=cw, height=ch, bg="black", highlightthickness=0)
        self.sector_canvas.pack(padx=5, pady=5)
        self.sector_canvas.bind("<Button-1>", self._on_sector_click)

        # Right panel
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        # Player info
        info_frame = ttk.LabelFrame(right_frame, text="Empire Info", padding=5)
        info_frame.pack(fill="x", pady=2)

        self.info_text = tk.Text(info_frame, height=8, width=35, state="disabled", wrap="word")
        self.info_text.pack(fill="x")

        # Strategic map
        strat_frame = ttk.LabelFrame(right_frame, text="Strategic Map", padding=2)
        strat_frame.pack(fill="both", expand=True, pady=5)

        self.strat_canvas = tk.Canvas(strat_frame, bg="#000011", highlightthickness=0)
        self.strat_canvas.pack(fill="both", expand=True)
        self.strat_canvas.bind("<Button-1>", self._on_strat_click)

        # Selected ship info
        ship_frame = ttk.LabelFrame(right_frame, text="Selected Ship", padding=5)
        ship_frame.pack(fill="x", pady=2)

        self.ship_info_text = tk.Text(ship_frame, height=4, width=35, state="disabled", wrap="word")
        self.ship_info_text.pack(fill="x")

        # Bottom status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", side="bottom")

        self.turn_label = ttk.Label(status_frame, text="Turn: 1", relief="sunken", anchor="w")
        self.turn_label.pack(side="left", fill="x", expand=True)

        self.money_label = ttk.Label(status_frame, text="Credits: 0", relief="sunken", anchor="w")
        self.money_label.pack(side="left", fill="x", expand=True)

        self.tech_label = ttk.Label(status_frame, text="Tech: 1", relief="sunken", anchor="w")
        self.tech_label.pack(side="left", fill="x", expand=True)

        end_turn_btn = ttk.Button(status_frame, text="End Turn (F10)", command=self._end_turn)
        end_turn_btn.pack(side="right", padx=5)

        self.bind("<F10>", lambda e: self._end_turn())

    def _update_display(self):
        player = self.game.get_player(self.game.current_player)
        if not player:
            return

        self.title(f"Space Empires II - {player.name} (Turn {self.game.turn_num})")
        self.sys_label.config(text=f"System: {self.game.systems[self.current_system].name}")
        self.player_label.config(text=f"Player: {player.name}")
        self.sys_num_label.config(text=f"({self.current_system + 1}/{len(self.game.systems)})")
        self.turn_label.config(text=f"Turn: {self.game.turn_num}")
        self.money_label.config(text=f"Credits: {player.money}")
        self.tech_label.config(text=f"Tech: {player.tech}")

        self._draw_sector_grid()
        self._draw_strategic_map()
        self._update_info_text()
        self._update_ship_info()

    def _draw_sector_grid(self):
        self.sector_canvas.delete("all")
        sys = self.game.systems[self.current_system]

        for s in range(MAX_SECTORS):
            row = s // SECTOR_COLS
            col = s % SECTOR_COLS
            x1 = col * self.cell_size
            y1 = row * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size

            obj = sys.sectors[s]
            color = self._sector_color(obj)
            self.sector_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#333", width=1)

            # Draw terrain symbol
            self._draw_terrain(s, x1, y1, obj)

            # Highlight selected
            if s == self.selected_sector:
                self.sector_canvas.create_rectangle(x1, y1, x2, y2, outline="yellow", width=3)

            # Draw ships
            ships = self.game.get_ships_in_sector(self.current_system, s)
            if ships:
                colors_used = set()
                for ship in ships:
                    pc = PLAYER_COLORS.get(ship.owner, "white")
                    if pc not in colors_used:
                        cx = x1 + 10 + len(colors_used) * 12
                        cy = y1 + 10
                        pts = [cx, cy-3, cx-2, cy+3, cx+2, cy+3]
                        self.sector_canvas.create_polygon(pts,fill=pc,outline="white",width=1)
                        #self.sector_canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=pc, outline="white")
                        colors_used.add(pc)

            # Draw planets
            planets = [p for p in self.game.planets if p.system == self.current_system and p.sector == s]
            for p in planets:
                cx = x1 + self.cell_size // 2
                cy = y1 + self.cell_size // 2 + 8
                marker = "O" if p.colony_type == 1 else "C" if p.colony_type == 2 else "S"
                pc = PLAYER_COLORS.get(p.owner, "gray")
                self.sector_canvas.create_text(cx, cy, text=marker, fill=pc, font=("TkDefaultFont", 10, "bold"))

    def _sector_color(self, obj: int) -> str:
        if obj == 0 or (19 <= obj <= 28):
            return "#000010"
        elif 1 <= obj <= 4:
            return "#001800"
        elif 6 <= obj <= 7:
            return "#332200"
        elif 8 <= obj <= 9:
            return "#222233"
        elif 10 <= obj <= 11:
            return "#330033"
        elif 12 <= obj <= 17:
            if obj == 12:
                return "#441111"
            elif obj == 13:
                return "#444400"
            elif obj == 14:
                return "#444455"
            elif obj == 15:
                return "#111144"
            elif obj == 16:
                return "#222288"
            elif obj == 17:
                return "#441111"
        elif obj == 18:
            return "#004444"
        return "#000010"

    def _draw_terrain(self, sector: int, x: int, y: int, obj: int):
        cx = x + self.cell_size // 2
        cy = y + self.cell_size // 2 - 6
        if 1 <= obj <= 4:
            colors = ["#44aa44", "#44cc44", "#aaaa44", "#aaaacc"]
            self.sector_canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=colors[min(obj - 1, len(colors) - 1)])
        elif 6 <= obj <= 7: # KBR 20260910
            self.sector_canvas.create_text(cx, cy, text="a", fill="#ffffff", font=("TkDefaultFont", 12, "bold"))
        elif 8 <= obj <= 9: # KBR 20260910
            self.sector_canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill="#ffffff")
        elif obj == 10: # KBR 20260910
            self.sector_canvas.create_text(cx, cy, text="ms", fill="#ffffff", font=("TkDefaultFont", 12))
        elif obj == 11: # KBR 20260910
            self.sector_canvas.create_text(cx, cy, text="hc", fill="#ffffff", font=("TkDefaultFont", 12))
        elif obj == 18:
            self.sector_canvas.create_text(cx, cy, text="W", fill="#00ffff", font=("TkDefaultFont", 12, "bold"))
        elif 12 <= obj <= 17:
            self.sector_canvas.create_text(cx, cy, text="*", fill="#ffff00", font=("TkDefaultFont", 14))

    def _draw_strategic_map(self):
        self.strat_canvas.delete("all")
        cw = self.strat_canvas.winfo_width() or 200
        ch = self.strat_canvas.winfo_height() or 300
        self.strat_canvas.config(width=cw, height=ch)

        if not self.game.systems:
            return

        # Scale systems to fit canvas
        min_x = min(s.draw_x for s in self.game.systems)
        max_x = max(s.draw_x for s in self.game.systems)
        min_y = min(s.draw_y for s in self.game.systems)
        max_y = max(s.draw_y for s in self.game.systems)
        range_x = max(max_x - min_x, 1)
        range_y = max(max_y - min_y, 1)
        margin = 20
        scale_x = (cw - margin * 2) / range_x
        scale_y = (ch - margin * 2) / range_y

        def to_canvas(dx, dy):
            return margin + (dx - min_x) * scale_x, margin + (dy - min_y) * scale_y

        # Draw warp lines
        for s in self.game.systems:
            x1, y1 = to_canvas(s.draw_x, s.draw_y)
            for dest_idx in s.warp_dest:
                if dest_idx < len(self.game.systems):
                    dest = self.game.systems[dest_idx]
                    x2, y2 = to_canvas(dest.draw_x, dest.draw_y)
                    self.strat_canvas.create_line(x1, y1, x2, y2, fill="#333366", width=1)

        # Draw systems
        for s in self.game.systems:
            x, y = to_canvas(s.draw_x, s.draw_y)
            r = 5 if s.sys_index != self.current_system else 8
            color = "#6666ff" if s.sys_index != self.current_system else "#ffff00"
            if s.sys_index == self.current_system:
                color = "#ff4444"
            self.strat_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="white")
            self.strat_canvas.create_text(x, y - r - 4, text=s.name, fill="#aaaaff", font=("TkDefaultFont", 6))

    def _update_info_text(self):
        player = self.game.get_player(self.game.current_player)
        if not player:
            return
        ships = self.game.get_player_ships(player.index)
        planets = [p for p in self.game.planets if p.owner == player.index]
        income = sum(p.value * (p.population // 500) for p in planets if p.population >= 500)
        maint = sum(self._get_maint(s) for s in ships)

        self.info_text.config(state="normal")
        self.info_text.delete(1.0, "end")
        info = [
            f"Credits: {player.money}",
            f"Tech Level: {player.tech}",
            f"Ships: {len(ships)}",
            f"Colonies: {len(planets)}",
            f"Income: {income}/turn",
            f"Maintenance: {maint}/turn",
            f"Net: {income - maint}/turn",
        ]
        self.info_text.insert(1.0, "\n".join(info))
        self.info_text.config(state="disabled")

    def _get_maint(self, ship: Ship) -> int:
        cls = self.game.get_ship_class(ship.class_id)
        if cls:
            return int(cls.cost * MAINTENANCE_RATE)
        return 0

    def _update_ship_info(self):
        self.ship_info_text.config(state="normal")
        self.ship_info_text.delete(1.0, "end")
        if self.selected_ship:
            ship = self.selected_ship
            cls = self.game.get_ship_class(ship.class_id)
            cls_name = cls.name if cls else "?"
            sys_name = self.game.systems[ship.system].name
            info = [
                f"Ship: {ship.name}",
                f"Class: {cls_name}",
                f"Location: {sys_name} Sec:{ship.sector}",
                f"Damage: {ship.damage} | Orders: {len(ship.orders)}",
            ]
            self.ship_info_text.insert(1.0, "\n".join(info))
        self.ship_info_text.config(state="disabled")

    def _on_sector_click(self, event):
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if 0 <= col < SECTOR_COLS and 0 <= row < SECTOR_ROWS:
            sector = row * SECTOR_COLS + col
            self.selected_sector = sector
            self._update_display()

            # Show sector info on right-click equivalent
            SectorInfo(self, self.game, self.current_system, sector)

    def _on_strat_click(self, event):
        cw = self.strat_canvas.winfo_width() or 200
        ch = self.strat_canvas.winfo_height() or 300

        if not self.game.systems:
            return

        min_x = min(s.draw_x for s in self.game.systems)
        max_x = max(s.draw_x for s in self.game.systems)
        min_y = min(s.draw_y for s in self.game.systems)
        max_y = max(s.draw_y for s in self.game.systems)
        range_x = max(max_x - min_x, 1)
        range_y = max(max_y - min_y, 1)
        margin = 20
        scale_x = (cw - margin * 2) / range_x
        scale_y = (ch - margin * 2) / range_y

        def from_canvas(cx, cy):
            return (cx - margin) / scale_x + min_x, (cy - margin) / scale_y + min_y

        mx, my = from_canvas(event.x, event.y)

        closest = 0
        closest_dist = 999999
        for i, s in enumerate(self.game.systems):
            dx = s.draw_x - mx
            dy = s.draw_y - my
            dist = dx * dx + dy * dy
            if dist < closest_dist:
                closest_dist = dist
                closest = i

        if closest_dist < 100:
            self.current_system = closest
            self.selected_sector = 40
            self._update_display()

    def _prev_system(self):
        if self.current_system > 0:
            self.current_system -= 1
        else: # KBR 20260910 wrap
            self.current_system = len(self.game.systems) - 1
        self.selected_sector = 40
        self._update_display()

    def _next_system(self):
        if self.current_system < len(self.game.systems) - 1:
            self.current_system += 1
        else: # KBR 20260910 wrap
            self.current_system = 0
        self.selected_sector = 40
        self._update_display()

    def _end_turn(self):
        player = self.game.get_player(self.game.current_player)
        if not player:
            return

        # Check for combat
        sys_ships = self.game.get_ships_in_system(self.current_system)
        player_ships = [s for s in sys_ships if s.owner == self.game.current_player]
        enemy_ships = [s for s in sys_ships if s.owner != self.game.current_player]

        if player_ships and enemy_ships:
            result = messagebox.askyesno("Combat!", "Enemy ships detected! Engage?")
            if result:
                from combat import Combat
                combat = Combat(self.game, player_ships, enemy_ships)
                CombatView(self, combat, self.game)
                combat.apply_results()

        # Process AI
        from ai import run_computer_turn
        for p in self.game.players:
            if p.index != self.game.current_player and p.is_computer:
                run_computer_turn(self.game, p)

        # Process turn
        self.game.process_turn()

        # Find next living human player
        found = False
        for _ in range(len(self.game.players)):
            next_p = self.game.current_player % len(self.game.players) + 1
            self.game.current_player = next_p
            player = self.game.get_player(next_p)
            if player and player.alive:
                if not player.is_computer:
                    found = True
                    break
                else:
                    run_computer_turn(self.game, player)

        if not found:
            messagebox.showinfo("Game Over", "No human players remaining!")
            self._on_close()
            return

        self.selected_ship = None
        self._update_display()

    def _design_ships(self):
        player = self.game.get_player(self.game.current_player)
        if not player:
            return
        dlg = DesignDialog(self, self.game, player)
        self.wait_window(dlg)
        if dlg.result_class:
            hull = dlg.result_class["hull"]
            cls = self.game._create_class(
                player.index, hull,
                dlg.result_class["type_name"],
                dlg.result_class["name"],
                dlg.result_class["compos"],
                dlg.result_class["shields"],
            )
            messagebox.showinfo("Design Complete", f"Class {cls.name} created (Cost: {cls.cost})")

    def _purchase_ships(self):
        player = self.game.get_player(self.game.current_player)
        if not player:
            return
        PurchaseDialog(self, self.game, player)
        self._update_display()

    def _order_move(self):
        if not self.selected_ship:
            messagebox.showwarning("No Ship", "Select a ship first")
            return
        ship = self.selected_ship
        order = f"MOV {self.current_system} {self.selected_sector}"
        ship.orders.append(order)
        messagebox.showinfo("Order", f"Move order added to {ship.name}")

    def _order_colonize(self):
        if not self.selected_ship:
            messagebox.showwarning("No Ship", "Select a ship first")
            return
        ship = self.selected_ship
        cls = self.game.get_ship_class(ship.class_id)
        if not cls:
            return
        compos = [get_compo(i) for i in cls.compo_set]
        if not has_colony_module(compos):
            messagebox.showwarning("No Colony Module", "This ship has no colony module")
            return
        order = f"CLN {self.current_system} {self.selected_sector}"
        ship.orders.append(order)
        messagebox.showinfo("Order", f"Colonize order added to {ship.name}")

    def _order_scrap(self):
        if not self.selected_ship:
            messagebox.showwarning("No Ship", "Select a ship first")
            return
        if messagebox.askyesno("Confirm", f"Scrap {self.selected_ship.name}?"):
            self.game.scrap_ship(self.selected_ship)
            self.selected_ship = None
            self._update_display()

    def _order_clear(self):
        if not self.selected_ship:
            messagebox.showwarning("No Ship", "Select a ship first")
            return
        self.selected_ship.orders = []
        messagebox.showinfo("Orders Cleared", f"All orders removed from {self.selected_ship.name}")
        self._update_ship_info()

    def _view_ships(self):
        player = self.game.get_player(self.game.current_player)
        if player:
            ViewShips(self, self.game, player)

    def _view_colonies(self):
        player = self.game.get_player(self.game.current_player)
        if player:
            ViewColonies(self, self.game, player)

    def _empire_status(self):
        player = self.game.get_player(self.game.current_player)
        if player:
            EmpireStatus(self, self.game, player)

    def _view_messages(self):
        msg_win = tk.Toplevel(self)
        msg_win.title("Messages")
        msg_win.geometry("500x300")
        frame = ttk.Frame(msg_win, padding=10)
        frame.pack(fill="both", expand=True)

        text = tk.Text(frame, wrap="word")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for turn, player, msg in self.game.message_log:
            pname = self.game.get_player(player).name if self.game.get_player(player) else "Game"
            text.insert("end", f"[Turn {turn}] {pname}: {msg}\n")
        text.config(state="disabled")

    def _save_game(self):
        try:
            with open("se_save.sav", "wb") as f:
                pickle.dump(self.game, f)
            messagebox.showinfo("Saved", "Game saved to se_save.sav")
            self.jdump()
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

    def _load_game(self):
        import pickle
        try:
            with open("se_save.sav", "rb") as f:
                self.game = pickle.load(f)
            self._update_display()
            messagebox.showinfo("Loaded", "Game restored from se_save.sav")
        except FileNotFoundError:
            messagebox.showwarning("Not Found", "No save file found")
        except Exception as e:
            messagebox.showerror("Error", f"Load failed: {e}")

    def _on_close(self):
        if messagebox.askokcancel("Quit", "Are you sure?"):
            self.destroy()

    def jdump(self):
        g = self.game
        data = {
        'current_player': g.current_player,
        'turn_num': g.turn_num,
        'num_play': g.num_players,
        'num_act_play': g.num_active_players,
        'num_com_play': g.num_comp_players,
        'num_sys': g.num_systems,
        'num_ship': g.num_ships,
        'num_class': g.num_classes,
        'num_plan': g.num_planets,
        'comp_diff': g.computer_difficulty,
        'game_over': g.game_over,
        'neut': g.neutrals_enabled,
        'warp_f': g.warp_freq,
        'separate': g.separation,
        
        'systems': [],
        'players': [],
        'ships': [],
        'classes': [],
        'planets': [],
        'msg': []
        }
        
        for i in range(g.num_systems):
            sys = g.systems[i]
            data['systems'].append({'index': i, 'name': sys.name, 'warp_sect': sys.warp_sector, 'sectors': sys.sectors})
            
        with open("se_save.json", 'w') as f:
            json.dump(data, f, indent=2)
        
    def GotoSystem(self, sysid):
        # TODO use in _next_system, _prev_system
        # KBR 20260910 change the active system view
        self.current_system = sysid
        self.selected_sector = 40 # TODO target sector
        self._update_display()
