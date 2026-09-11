"""Main window with galaxy map and system view"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Tuple
import math

from space_empires.models import (
    GameState, StarSystem, Planet, Ship, Player, ShipType,
    ColonyType, PlanetType, StellarType
)
from space_empires.universe import (
    get_planet_at_sector, get_sector_description, is_planet,
    is_warp_point, is_star, is_empty_space, is_cloaking, is_machine,
    distance, star_index, SYSTEM_WIDTH, SYSTEM_HEIGHT, MAX_SECTORS
)
from space_empires.game_logic import (
    next_player, player_lives, calculate_money, check_victory,
    do_repair, grow_population, explore_system, can_see_system,
    get_visible_systems, get_ships_in_system, get_ships_in_sector,
    move_ship, create_ship, scrap_ships, colonize_planet,
    close_warp_point
)
from space_empires.ai import computer_turn
from space_empires.combat import setup_combat


SECTOR_SIZE = 32
MAP_PADDING = 10


class GalaxyMapCanvas(tk.Canvas):
    """Canvas for displaying the strategic galaxy map"""
    
    def __init__(self, parent, state: GameState, app, **kwargs):
        super().__init__(parent, bg='#1a1a2e', highlightthickness=0, **kwargs)
        self.state = state
        self.app = app
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start = None
        self.selected_system = None
        
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<MouseWheel>', self.on_zoom)
        self.bind('<Configure>', self.on_resize)
        
    def on_resize(self, event):
        self.draw()
        
    def on_click(self, event):
        self.drag_start = (event.x, event.y)
        self.check_system_click(event.x, event.y)
        
    def on_drag(self, event):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self.drag_start = (event.x, event.y)
            self.draw()
            
    def on_release(self, event):
        self.drag_start = None
        
    def on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale = max(0.5, min(3.0, self.scale * factor))
        self.draw()
        
    def screen_to_galaxy(self, x: int, y: int) -> Tuple[float, float]:
        """Convert screen coordinates to galaxy coordinates"""
        gx = (x - self.offset_x - self.winfo_width() / 2) / self.scale + self.winfo_width() / 2
        gy = (y - self.offset_y - self.winfo_height() / 2) / self.scale + self.winfo_height() / 2
        return gx, gy
        
    def galaxy_to_screen(self, gx: float, gy: float) -> Tuple[int, int]:
        """Convert galaxy coordinates to screen coordinates"""
        x = int((gx - self.winfo_width() / 2) * self.scale + self.winfo_width() / 2 + self.offset_x)
        y = int((gy - self.winfo_height() / 2) * self.scale + self.winfo_height() / 2 + self.offset_y)
        return x, y
        
    def check_system_click(self, x: int, y: int):
        """Check if a system was clicked"""
        gx, gy = self.screen_to_galaxy(x, y)
        
        for system in self.state.systems[1:]:
            if not system:
                continue
            sx, sy = self.galaxy_to_screen(system.draw_x * 20 + 200, system.draw_y * 20 + 200)
            dist = math.hypot(sx - x, sy - y)
            if dist < 10 * self.scale:
                self.selected_system = system.system_index
                self.app.on_system_selected(system.system_index)
                break
        else:
            self.selected_system = None
            self.app.on_system_selected(None)
        self.draw()
        
    def draw(self):
        """Draw the galaxy map"""
        self.delete('all')
        
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
            
        cx = w / 2
        cy = h / 2
        
        player = self.state.players[self.state.current_player]
        if not player:
            return
            
        visible_systems = get_visible_systems(self.state, self.state.current_player)
        
        # Draw warp lines first (behind systems)
        for system in self.state.systems[1:]:
            if not system or system.system_index not in visible_systems:
                continue
                
            sx, sy = self.galaxy_to_screen(system.draw_x * 20 + 200, system.draw_y * 20 + 200)
            
            for i in range(1, system.warp_count + 1):
                dest_idx = system.warp_dest[i]
                if dest_idx <= 0 or dest_idx >= len(self.state.systems):
                    continue
                dest = self.state.systems[dest_idx]
                if not dest or dest.system_index not in visible_systems:
                    continue
                    
                dx, dy = self.galaxy_to_screen(dest.draw_x * 20 + 200, dest.draw_y * 20 + 200)
                self.create_line(sx, sy, dx, dy, fill='#444466', width=1, dash=(4, 4))
        
        # Draw systems
        for system in self.state.systems[1:]:
            if not system:
                continue
                
            sx, sy = self.galaxy_to_screen(system.draw_x * 20 + 200, system.draw_y * 20 + 200)
            
            # Check if explored
            explored = system.system_index in visible_systems
            has_ships = bool(get_ships_in_system(self.state, system.system_index, self.state.current_player))
            
            if not explored and not has_ships:
                # Draw as dot for last known
                last_known = False
                for p_id in range(1, len(self.state.players)):
                    if hasattr(system, 'last_known') and p_id in getattr(system, 'last_known', set()):
                        last_known = True
                        break
                if last_known:
                    self.create_oval(sx-3, sy-3, sx+3, sy+3, fill='#444444', outline='#666666')
                continue
            
            # Determine color
            color = '#888888'  # default
            if has_ships:
                # Check who has ships
                for ship in self.state.ships:
                    if ship.system == system.system_index and ship.owner > 0:
                        p = self.state.players[ship.owner]
                        if p:
                            color = f'#{p.color[0]:02x}{p.color[1]:02x}{p.color[2]:02x}'
                        break
            elif system.system_index == self.state.active_system:
                color = '#00ffff'
            elif explored:
                color = '#666666'
                
            radius = max(4, int(6 * self.scale))
            
            # Draw system circle
            if system.system_index == self.selected_system:
                self.create_oval(sx-radius-2, sy-radius-2, sx+radius+2, sy+radius+2, 
                               outline='#ffff00', width=2)
            
            self.create_oval(sx-radius, sy-radius, sx+radius, sy+radius, 
                           fill=color, outline='#ffffff' if explored else '#444444')
            
            # Draw name if explored
            if explored:
                self.create_text(sx, sy - radius - 8, text=system.name, 
                               fill='#ffffff', font=('Arial', 8), anchor='s')
        
        # Draw selection indicator
        if self.state.active_system > 0:
            system = self.state.systems[self.state.active_system]
            if system:
                sx, sy = self.galaxy_to_screen(system.draw_x * 20 + 200, system.draw_y * 20 + 200)
                radius = max(6, int(8 * self.scale))
                self.create_oval(sx-radius, sy-radius, sx+radius, sy+radius, 
                               outline='#00ffff', width=2, dash=(4, 4))


class SystemMapCanvas(tk.Canvas):
    """Canvas for displaying the tactical system map (9x9 grid)"""
    
    def __init__(self, parent, state: GameState, app, **kwargs):
        super().__init__(parent, bg='#2a2a3e', highlightthickness=1, highlightbackground='#444466', **kwargs)
        self.state = state
        self.app = app
        self.selected_sector = 9999
        self.hover_sector = -1
        
        self.bind('<Button-1>', self.on_click)
        self.bind('<Motion>', self.on_motion)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Configure>', self.on_resize)
        
    def on_resize(self, event):
        self.draw()
        
    def on_click(self, event):
        sector = self.get_sector_at(event.x, event.y)
        if sector >= 0:
            self.selected_sector = sector
            self.state.selected_sector = sector
            self.app.on_sector_selected(sector)
            self.draw()
            
    def on_motion(self, event):
        sector = self.get_sector_at(event.x, event.y)
        if sector != self.hover_sector:
            self.hover_sector = sector
            self.draw()
            if sector >= 0:
                self.app.update_sector_info(sector)
                
    def on_leave(self, event):
        self.hover_sector = -1
        self.draw()
        
    def get_sector_at(self, x: int, y: int) -> int:
        """Get sector index at screen coordinates"""
        w = self.winfo_width()
        h = self.winfo_height()
        cell_w = (w - 2 * MAP_PADDING) / SYSTEM_WIDTH
        cell_h = (h - 2 * MAP_PADDING) / SYSTEM_HEIGHT
        
        col = int((x - MAP_PADDING) / cell_w)
        row = int((y - MAP_PADDING) / cell_h)
        
        if 0 <= col < SYSTEM_WIDTH and 0 <= row < SYSTEM_HEIGHT:
            return row * SYSTEM_WIDTH + col
        return -1
        
    def get_sector_rect(self, sector: int) -> Tuple[int, int, int, int]:
        """Get screen rectangle for a sector"""
        w = self.winfo_width()
        h = self.winfo_height()
        cell_w = (w - 2 * MAP_PADDING) / SYSTEM_WIDTH
        cell_h = (h - 2 * MAP_PADDING) / SYSTEM_HEIGHT
        
        col = sector % SYSTEM_WIDTH
        row = sector // SYSTEM_WIDTH
        
        x1 = MAP_PADDING + col * cell_w
        y1 = MAP_PADDING + row * cell_h
        x2 = x1 + cell_w
        y2 = y1 + cell_h
        
        return int(x1), int(y1), int(x2), int(y2)
        
    def draw(self):
        """Draw the system map"""
        self.delete('all')
        
        system = self.state.systems[self.state.active_system]
        if not system:
            return
            
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
            
        cell_w = (w - 2 * MAP_PADDING) / SYSTEM_WIDTH
        cell_h = (h - 2 * MAP_PADDING) / SYSTEM_HEIGHT
        
        player = self.state.players[self.state.current_player]
        if not player:
            return
            
        # Draw grid and sectors
        for row in range(SYSTEM_HEIGHT):
            for col in range(SYSTEM_WIDTH):
                sector = row * SYSTEM_WIDTH + col
                x1, y1, x2, y2 = self.get_sector_rect(sector)
                
                # Base color
                obj_idx = system.get_sector_object(sector)
                stellar = self.state.stellar_objects[obj_idx] if obj_idx < len(self.state.stellar_objects) else None
                
                # Determine base color
                if stellar:
                    if stellar.type == 4:  # Star
                        base_color = '#ffaa00'
                    elif stellar.type == 5:  # Warp point
                        base_color = '#00ffff'
                    elif stellar.type == 1:  # Planet
                        base_color = '#0088ff'
                    elif stellar.type == 2:  # Gas giant
                        base_color = '#aa66ff'
                    elif stellar.type == 3:  # Nebula/storm
                        base_color = '#8844aa'
                    elif stellar.type == 6:  # Empty
                        base_color = '#1a1a2e'
                    elif stellar.type == 8:  # Machine
                        base_color = '#ff4444'
                    else:
                        base_color = '#333344'
                else:
                    base_color = '#1a1a2e'
                
                # Draw sector background
                fill_color = base_color
                outline_color = '#444466'
                outline_width = 1
                
                # Highlight selected
                if sector == self.selected_sector:
                    outline_color = '#ffff00'
                    outline_width = 2
                elif sector == self.hover_sector:
                    outline_color = '#8888ff'
                    outline_width = 2
                    
                self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=outline_color, width=outline_width)
                
                # Draw object icon/text
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                if stellar:
                    if stellar.type == 4:  # Star
                        self.create_oval(cx-8, cy-8, cx+8, cy+8, fill='#ffaa00', outline='#ff8800')
                        self.create_oval(cx-4, cy-4, cx+4, cy+4, fill='#ffff88', outline='')
                    elif stellar.type == 5:  # Warp point
                        self.create_oval(cx-6, cy-6, cx+6, cy+6, outline='#00ffff', width=2)
                        self.create_text(cx, cy, text='⟳', fill='#00ffff', font=('Arial', 10))
                    elif stellar.type in (1, 2, 8):  # Planet types
                        planet = get_planet_at_sector(self.state, system.system_index, sector)
                        if planet and planet.owner > 0:
                            p = self.state.players[planet.owner]
                            color = f'#{p.color[0]:02x}{p.color[1]:02x}{p.color[2]:02x}'
                            self.create_oval(cx-6, cy-6, cx+6, cx+6, fill=color, outline='#ffffff')
                            # Colony indicator
                            if planet.colony_type > 0:
                                self.create_text(cx, cy, text=str(planet.colony_type), fill='#ffffff', font=('Arial', 7, 'bold'))
                        else:
                            self.create_oval(cx-6, cy-6, cx+6, cy+6, fill='#0088ff', outline='#00aaff')
                    elif stellar.type == 3:  # Nebula
                        self.create_oval(cx-6, cy-6, cx+6, cy+6, fill='#8844aa', outline='#aa66cc', stipple='gray50')
                    elif stellar.type == 6:  # Empty
                        pass  # Just background
                        
                # Draw ships in sector
                ships = get_ships_in_sector(self.state, system.system_index, sector, self.state.current_player)
                if ships:
                    for i, ship in enumerate(ships[:3]):
                        sx = x1 + 4 + i * 10
                        sy = y2 - 10
                        self.create_rectangle(sx, sy, sx+8, sy+8, fill='#00ff00', outline='#00aa00')
                        self.create_text(sx+4, sy+4, text=str(i+1), fill='#000000', font=('Arial', 6))
                        
                # Enemy ships
                for p_id in range(1, len(self.state.players)):
                    if p_id == self.state.current_player:
                        continue
                    enemy_ships = get_ships_in_sector(self.state, system.system_index, sector, p_id)
                    if enemy_ships:
                        ex = x2 - 12
                        ey = y1 + 4
                        p = self.state.players[p_id]
                        if p:
                            color = f'#{p.color[0]:02x}{p.color[1]:02x}{p.color[2]:02x}'
                            self.create_rectangle(ex, ey, ex+8, ey+8, fill=color, outline='#ffffff')
                            self.create_text(ex+4, ey+4, text='E', fill='#ffffff', font=('Arial', 6))
                        break


class MainWindow:
    """Main application window"""
    
    def __init__(self, root: tk.Tk, state: GameState):
        self.root = root
        self.state = state
        self.setup_ui()
        self.update_ui()
        
    def setup_ui(self):
        """Create the main UI layout"""
        # Main paned window
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Galaxy map and controls
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=2)
        
        # Galaxy map
        map_frame = ttk.LabelFrame(left_frame, text="Galaxy Map", padding=5)
        map_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.galaxy_canvas = GalaxyMapCanvas(map_frame, self.state, self, width=600, height=500)
        self.galaxy_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Galaxy controls
        gal_ctrl = ttk.Frame(left_frame)
        gal_ctrl.pack(fill=tk.X, pady=5)
        
        ttk.Button(gal_ctrl, text="Center on Home", command=self.center_on_home).pack(side=tk.LEFT, padx=2)
        ttk.Button(gal_ctrl, text="Show All", command=self.show_all_systems).pack(side=tk.LEFT, padx=2)
        
        self.turn_label = ttk.Label(gal_ctrl, text="Turn: 1  Player: Human")
        self.turn_label.pack(side=tk.RIGHT, padx=10)
        
        # Right panel - System map and info
        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=1)
        
        # System map
        sys_frame = ttk.LabelFrame(right_pane, text="System Map", padding=5)
        right_pane.add(sys_frame, weight=3)
        
        self.system_canvas = SystemMapCanvas(sys_frame, self.state, self, width=400, height=400)
        self.system_canvas.pack(fill=tk.BOTH, expand=True)
        
        # System controls
        sys_ctrl = ttk.Frame(sys_frame)
        sys_ctrl.pack(fill=tk.X, pady=5)
        
        ttk.Button(sys_ctrl, text="Build Ship", command=self.show_build_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(sys_ctrl, text="Colonize", command=self.do_colonize).pack(side=tk.LEFT, padx=2)
        ttk.Button(sys_ctrl, text="Close Warp", command=self.do_close_warp).pack(side=tk.LEFT, padx=2)
        ttk.Button(sys_ctrl, text="End Turn", command=self.end_turn).pack(side=tk.RIGHT, padx=2)
        
        # Info panel
        info_frame = ttk.LabelFrame(right_pane, text="Sector Info", padding=5)
        right_pane.add(info_frame, weight=1)
        
        self.info_text = tk.Text(info_frame, height=10, wrap=tk.WORD, font=('Consolas', 9))
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Ship list
        ship_frame = ttk.LabelFrame(right_pane, text="Ships in System", padding=5)
        right_pane.add(ship_frame, weight=1)
        
        # Treeview for ships
        columns = ('Name', 'Type', 'Owner', 'Damage', 'Speed', 'Orders')
        self.ship_tree = ttk.Treeview(ship_frame, columns=columns, show='headings', height=8)
        for col in columns:
            self.ship_tree.heading(col, text=col)
            self.ship_tree.column(col, width=80)
        self.ship_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bottom status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
    def update_ui(self):
        """Update all UI elements"""
        self.galaxy_canvas.draw()
        self.system_canvas.draw()
        self.update_ship_list()
        self.update_turn_display()
        
    def update_turn_display(self):
        """Update turn/player display"""
        player = self.state.players[self.state.current_player]
        name = player.name if player else "Unknown"
        self.turn_label.config(text=f"Turn: {self.state.turn_number}  Player: {name}")
        
    def update_ship_list(self):
        """Update ship list for active system"""
        self.ship_tree.delete(*self.ship_tree.get_children())
        
        if self.state.active_system <= 0:
            return
            
        ships = get_ships_in_system(self.state, self.state.active_system, self.state.current_player)
        for ship in ships:
            ship_class = self.get_ship_class(ship.class_id)
            hull = self.get_hull(ship_class.hull_size) if ship_class else None
            type_str = hull.name if hull else "Unknown"
            
            owner_name = "You" if ship.owner == self.state.current_player else "Enemy"
            if ship.owner > 0 and ship.owner < len(self.state.players):
                p = self.state.players[ship.owner]
                if p:
                    owner_name = p.name
                    
            self.ship_tree.insert('', tk.END, values=(
                ship.name, type_str, owner_name, ship.damage, ship.speed, ship.orders or "None"
            ))
            
    def get_ship_class(self, class_id: int):
        for sc in self.state.ship_classes:
            if sc.class_index == class_id:
                return sc
        return None
        
    def get_hull(self, hull_id: int):
        from space_empires.models import get_hull
        return get_hull(hull_id)
        
    def on_system_selected(self, system_idx: Optional[int]):
        """Handle system selection"""
        if system_idx and system_idx != self.state.active_system:
            self.state.active_system = system_idx
            self.state.selected_sector = 9999
            self.system_canvas.selected_sector = 9999
            self.update_ui()
            self.update_sector_info(9999)
            
    def on_sector_selected(self, sector: int):
        """Handle sector selection"""
        self.update_sector_info(sector)
        
    def update_sector_info(self, sector: int):
        """Update sector info panel"""
        if self.state.active_system <= 0:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "No system selected")
            return
            
        if sector == 9999:
            # System overview
            system = self.state.systems[self.state.active_system]
            if not system:
                return
                
            text = f"System: {system.name}\n"
            text += f"Position: ({system.draw_x}, {system.draw_y})\n"
            text += f"Warp Points: {system.warp_count}\n\n"
            
            for i in range(1, system.warp_count + 1):
                dest = self.state.systems[system.warp_dest[i]]
                if dest:
                    text += f"  Warp {i}: Sector {system.warp_sector[i]} -> {dest.name}\n"
                    
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, text)
        else:
            # Sector detail
            desc = get_sector_description(self.state, self.state.active_system, sector, True)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, desc)
            
    def center_on_home(self):
        """Center galaxy map on home system"""
        player = self.state.players[self.state.current_player]
        if player and player.home_system > 0:
            system = self.state.systems[player.home_system]
            if system:
                w = self.galaxy_canvas.winfo_width()
                h = self.galaxy_canvas.winfo_height()
                cx = system.draw_x * 20 + 200
                cy = system.draw_y * 20 + 200
                self.galaxy_canvas.offset_x = w/2 - cx * self.galaxy_canvas.scale
                self.galaxy_canvas.offset_y = h/2 - cy * self.galaxy_canvas.scale
                self.galaxy_canvas.draw()
                
    def show_all_systems(self):
        """Show all systems (cheat/surrender mode)"""
        self.state.surrender_condition = True
        self.galaxy_canvas.draw()
        
    def show_build_dialog(self):
        """Show ship building dialog"""
        if self.state.active_system <= 0:
            return
            
        # Find colonies with shipyards
        colonies = []
        for planet in self.state.planets[1:]:
            if (planet and planet.system == self.state.active_system 
                and planet.owner == self.state.current_player
                and planet.colony_type > 0):
                colonies.append(planet)
                
        if not colonies:
            messagebox.showinfo("Build Ship", "No colonies with shipyards in this system")
            return
            
        # Simple dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Build Ship")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Colony:").pack(pady=5)
        colony_var = tk.StringVar()
        colony_combo = ttk.Combobox(dialog, textvariable=colony_var, state='readonly')
        colony_combo['values'] = [f"{p.name} (System {p.system}, Sector {p.sector})" for p in colonies]
        colony_combo.pack(pady=5)
        if colonies:
            colony_combo.current(0)
            
        ttk.Label(dialog, text="Ship Class:").pack(pady=5)
        class_var = tk.StringVar()
        class_combo = ttk.Combobox(dialog, textvariable=class_var, state='readonly')
        # Get available classes for player
        player_classes = [sc for sc in self.state.ship_classes if sc.owner == self.state.current_player]
        class_combo['values'] = [f"{sc.name} ({sc.cost} creds)" for sc in player_classes]
        class_combo.pack(pady=5)
        if player_classes:
            class_combo.current(0)
            
        def do_build():
            if not colonies or not player_classes:
                return
            col_idx = colony_combo.current()
            cls_idx = class_combo.current()
            if col_idx >= 0 and cls_idx >= 0:
                colony = colonies[col_idx]
                ship_class = player_classes[cls_idx]
                player = self.state.players[self.state.current_player]
                if player.money >= ship_class.cost:
                    create_ship(self.state, self.state.current_player, ship_class.class_index,
                              colony.system, colony.sector)
                    player.money -= ship_class.cost
                    self.update_ui()
                    dialog.destroy()
                else:
                    messagebox.showerror("Build Ship", "Not enough money!")
                    
        ttk.Button(dialog, text="Build", command=do_build).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)
        
    def do_colonize(self):
        """Attempt to colonize selected sector"""
        if self.state.active_system <= 0 or self.state.selected_sector == 9999:
            return
            
        sector = self.state.selected_sector
        planet = get_planet_at_sector(self.state, self.state.active_system, sector)
        
        if not planet or planet.colony_type > 0 or planet.owner != 0:
            messagebox.showinfo("Colonize", "Cannot colonize this sector")
            return
            
        # Find colony ships in sector
        ships = get_ships_in_sector(self.state, self.state.active_system, sector, self.state.current_player)
        colony_ships = []
        for ship in ships:
            sc = self.get_ship_class(ship.class_id)
            if sc and sc.ship_type == ShipType.COLONIZE:
                colony_ships.append(ship.ship_id)
                
        if not colony_ships:
            messagebox.showinfo("Colonize", "No colony ships in this sector")
            return
            
        if colonize_planet(self.state, self.state.current_player, self.state.active_system, sector, colony_ships):
            messagebox.showinfo("Colonize", "Planet colonized successfully!")
            self.update_ui()
        else:
            messagebox.showerror("Colonize", "Colonization failed!")
            
    def do_close_warp(self):
        """Close warp point in selected sector"""
        if self.state.active_system <= 0 or self.state.selected_sector == 9999:
            return
            
        if not is_warp_point(self.state, self.state.active_system, self.state.selected_sector):
            messagebox.showinfo("Close Warp", "No warp point in this sector")
            return
            
        if close_warp_point(self.state, self.state.current_player, self.state.active_system, self.state.selected_sector):
            messagebox.showinfo("Close Warp", "Warp point closed!")
            self.update_ui()
        else:
            messagebox.showerror("Close Warp", "Failed to close warp point!")
            
    def end_turn(self):
        """End current player's turn"""
        self.status_var.set("Processing turn...")
        self.root.update()
        
        # Process current player's turn end
        player = self.state.players[self.state.current_player]
        if player and not player.is_computer:
            # Human player - process repairs, income, population growth
            do_repair(self.state, self.state.current_player)
            player.money += calculate_money(self.state, self.state.current_player)
            grow_population(self.state, self.state.current_player)
            
        # Move to next player
        self.state.current_player = next_player(self.state)
        
        # Check victory
        winner = check_victory(self.state)
        if winner:
            winner_name = self.state.players[winner].name if winner < len(self.state.players) else "Unknown"
            messagebox.showinfo("Game Over", f"{winner_name} wins!")
            self.root.quit()
            return
            
        # Process AI turns until human player
        while self.state.current_player < len(self.state.players):
            player = self.state.players[self.state.current_player]
            if player and player.is_computer:
                computer_turn(self.state, self.state.current_player)
                # Check if game ended
                winner = check_victory(self.state)
                if winner:
                    winner_name = self.state.players[winner].name if winner < len(self.state.players) else "Unknown"
                    messagebox.showinfo("Game Over", f"{winner_name} wins!")
                    self.root.quit()
                    return
                self.state.current_player = next_player(self.state)
            else:
                break
                
        # Process human player start of turn
        player = self.state.players[self.state.current_player]
        if player and not player.is_computer:
            do_repair(self.state, self.state.current_player)
            player.money += calculate_money(self.state, self.state.current_player)
            grow_population(self.state, self.state.current_player)
            explore_system(self.state, self.state.active_system, self.state.current_player)
            
        self.update_ui()
        self.status_var.set("Ready")


def run_game():
    """Run the game"""
    root = tk.Tk()
    root.title("Space Empires - 4X Strategy")
    root.geometry("1400x900")
    root.minsize(1024, 768)
    
    state = GameState()
    state.galaxy_size = 50
    state.num_players = 4
    state.max_players = 20
    
    from space_empires.universe import create_universe
    create_universe(state)
    
    app = MainWindow(root, state)
    root.mainloop()


if __name__ == "__main__":
    run_game()