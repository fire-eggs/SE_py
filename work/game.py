import random
import os
import pickle

from entities import *
from components import *
from universe import *
from economy import *
from config import *

from typing import Optional


class Game:
    def __init__(self):
        self.systems: list[System] = []
        self.players: list[Player] = []
        self.ships: list[Ship] = []
        self.ship_classes: list[ShipClass] = []
        self.planets: list[Planet] = []
        self.current_player: int = 1
        self.turn_num: int = 1
        self.num_players: int = 0
        self.num_active_players: int = 0
        self.num_comp_players: int = 0
        self.num_systems: int = 0
        self.num_ships: int = 0
        self.num_classes: int = 0
        self.num_planets: int = 0
        self.computer_difficulty: int = 2
        self.game_over: bool = False
        self.neutrals_enabled: bool = False
        self.warp_freq: int = 2
        self.separation: int = 6
        self.message_log: list = []
        self._next_ship_id: int = 1
        self._next_class_id: int = 1

    def init_new_game(self, num_human: int, num_comp: int, map_size: str,
                      warp_freq: int, separation: int, neutrals: bool,
                      difficulty: int, start_tech: int):
        self.neutrals_enabled = neutrals
        self.warp_freq = warp_freq
        self.separation = separation
        self.computer_difficulty = difficulty
        self.turn_num = 1
        self.current_player = 1
        self.game_over = False
        self.message_log = []
        self._next_ship_id = 1
        self._next_class_id = 1

        self.ships = []
        self.ship_classes = []
        self.planets = []

        if map_size == "Small":
            num_sys = 25
        elif map_size == "Medium":
            num_sys = 50
        else:
            num_sys = 80

        self.num_systems = num_sys
        self.systems = generate_universe(num_sys, warp_freq, separation)

        total_players = num_human + num_comp
        if neutrals:
            neut_sys = [s for s in self.systems if len(find_colony_sectors(s)) > 0]
            num_neuts = min(4, len(neut_sys))
            total_players += num_neuts

        self.num_players = total_players
        self.num_active_players = num_human + num_comp
        self.num_comp_players = num_comp + (num_neuts if neutrals else 0)

        self.players = []
        for i in range(total_players):
            p = Player(index=i + 1, tech=start_tech, money=500)
            self.players.append(p)

        for i in range(num_human):
            self.players[i].name = f"Player {i + 1}"
            self.players[i].is_computer = False

        for i in range(num_comp):
            idx = num_human + i
            self.players[idx].name = f"Computer {i + 1}"
            self.players[idx].is_computer = True

        if neutrals:
            self._setup_neutrals(num_human + num_comp, neut_sys, num_neuts)

        self._place_homeworlds()
        self._create_initial_fleets()
        self._update_avail_components()
        self._send_message("New game started", 0)

    def _setup_neutrals(self, start_idx: int, neut_sys: list, count: int):
        random.shuffle(neut_sys)
        for i in range(count):
            idx = start_idx + i
            sys = neut_sys[i]
            self.players[idx].name = sys.name
            self.players[idx].is_computer = True
            self.players[idx].home_system = sys.sys_index
            colony_sectors = find_colony_sectors(sys)
            if colony_sectors:
                sector = random.choice(colony_sectors)
                sys.sectors[sector] = 1
                planet = Planet(
                    planet_id=len(self.planets) + 1,
                    value=random.randint(5, 15),     # TODO VB: l016A = Int(Rnd * 200) + 300
                    type_idx=1, # TODO VB does not change planet type
                    name=f"{sys.name} Prime",
                    colony_type=3,
                    owner=idx + 1,
                    population=500, # as per VB random.randint(100, 500),
                    system=sys.sys_index,
                    sector=sector,
                )
                self.planets.append(planet)

    def _place_homeworlds(self):
        candidates = find_home_system_candidates(self.systems)
        random.shuffle(candidates)

        for i, player in enumerate(self.players):
            if player.index > self.num_active_players and not self.neutrals_enabled:
                break
            if i < len(candidates):
                sys_idx = candidates[i]
            else:
                sys_idx = i % len(self.systems)

            sys = self.systems[sys_idx]
            player.home_system = sys_idx

            colony_sectors = find_colony_sectors(sys)
            if colony_sectors:
                sector = colony_sectors[0]
            else:
                sector = 40

            sys.sectors[sector] = 1

            planet = Planet(
                planet_id=len(self.planets) + 1,
                value=10, # TODO Int(Rnd * 200) + 500
                type_idx=1, # TODO machine planet
                name=f"{sys.name} Prime",
                colony_type=3,
                owner=player.index,
                population=500,
                system=sys_idx,
                sector=sector,
            )
            self.planets.append(planet)
            player.home_planet = planet.planet_id

    def _create_initial_fleets(self):
        for player in self.players:
            if player.index > self.num_active_players and not self.neutrals_enabled:
                break
            sys_idx = player.home_system
            sys = self.systems[sys_idx]
            colony_sectors = find_colony_sectors(sys)
            sector = colony_sectors[0] if colony_sectors else 40

            hull = HULL_TYPES[0]
            cls = self._create_class(player.index, hull, "ATK", f"Scout", [31])
            ship = self._create_ship(f"{player.name}-1", cls.class_index, sys_idx, sector, player.index)
            self.ships.append(ship)

    def _create_class(self, owner: int, hull: dict, type_name: str, name: str,
                      compo_indices: list, shields: int = 0) -> ShipClass:
        cls = ShipClass(
            owner=owner,
            size=hull["size"],
            type_name=type_name,
            name=name,
            class_index=self._next_class_id,
            cost=hull["cost"],
            tech=hull["tech"],
            shields=shields,
            compo_set=compo_indices,
        )
        cls.cost = hull["cost"] + shields * SHIELD_COST_PER_POINT
        total_tech = hull["tech"]
        for ci in compo_indices:
            c = get_compo(ci)
            cls.cost += c.cost
            if c.tech > total_tech:
                total_tech = c.tech
        cls.tech = total_tech

        num_eng = count_engines([get_compo(i) for i in compo_indices])
        if hull["epm"] > 0:
            cls.speed = num_eng // hull["epm"]
        else:
            cls.speed = 0

        self._next_class_id += 1
        self.ship_classes.append(cls)
        return cls

    def _create_ship(self, name: str, class_id: int, system: int,
                     sector: int, owner: int) -> Ship:
        return Ship(
            name=name,
            ship_id=self._next_ship_id,
            class_id=class_id,
            system=system,
            sector=sector,
            owner=owner,
            damage=0,
            speed=0,
        )

    def _update_avail_components(self):
        for player in self.players:
            for i, comp in enumerate(ALL_COMPONENTS):
                if comp.tech <= player.tech:
                    player.avail_compo[i] = True

    def get_player(self, idx: int) -> Optional[Player]:
        for p in self.players:
            if p.index == idx:
                return p
        return None

    def get_ships_in_sector(self, system: int, sector: int) -> list[Ship]:
        return [s for s in self.ships if s.system == system and s.sector == sector]

    def get_ships_in_system(self, system: int) -> list[Ship]:
        return [s for s in self.ships if s.system == system]

    def get_player_ships(self, player: int) -> list[Ship]:
        return [s for s in self.ships if s.owner == player]

    def get_planets_in_system(self, system: int) -> list[Planet]:
        return [p for p in self.planets if p.system == system]

    def get_ship_class(self, class_id: int) -> Optional[ShipClass]:
        for c in self.ship_classes:
            if c.class_index == class_id:
                return c
        return None

    def get_ship(self, ship_id: int) -> Optional[Ship]:
        for s in self.ships:
            if s.ship_id == ship_id:
                return s
        return None

    def _send_message(self, msg: str, player: int = 0):
        self.message_log.append((self.turn_num, player, msg))

    def move_ship(self, ship: Ship, sector: int) -> bool:
        if sector < 0 or sector >= MAX_SECTORS:
            return False
        ship.sector = sector
        return True

    def move_ship_to_system(self, ship: Ship, system_idx: int, sector: int):
        ship.system = system_idx
        ship.sector = sector

    def colonize_planet(self, ship: Ship) -> bool:
        sys = self.systems[ship.system]
        obj = sys.sectors[ship.sector]
        if not (1 <= obj <= 4):
            return False

        for p in self.planets:
            if p.system == ship.system and p.sector == ship.sector:
                return False

        cls = self.get_ship_class(ship.class_id)
        if not cls:
            return False
        compos = [get_compo(i) for i in cls.compo_set]
        colony_type = determine_colony_type(compos)
        if colony_type == 0:
            return False

        names_pool = ["Alpha", "Beta", "Gamma", "Delta", "Prime", "Major", "Minor"]
        name = f"{sys.name} {random.choice(names_pool)}"

        planet = Planet(
            planet_id=len(self.planets) + 1,
            value=random.randint(5, 20),
            type_idx=obj,
            name=name,
            colony_type=colony_type,
            owner=ship.owner,
            population=10,
            system=ship.system,
            sector=ship.sector,
        )
        self.planets.append(planet)
        self.ships.remove(ship)
        self._send_message(f"{ship.name} colonized {name}", ship.owner)
        return True

    def scrap_ship(self, ship: Ship):
        cls = self.get_ship_class(ship.class_id)
        if cls:
            refund = cls.cost // 4
            player = self.get_player(ship.owner)
            if player:
                player.money += refund
        if ship in self.ships:
            self.ships.remove(ship)

    def find_warp_destination(self, system_idx: int, sector: int) -> tuple:
        sys = self.systems[system_idx]
        for i, ws in enumerate(sys.warp_sector):
            if ws == sector and i < len(sys.warp_dest):
                dest_sys = sys.warp_dest[i]
                dest_sectors = self.systems[dest_sys].warp_sector
                if i < len(dest_sectors):
                    return dest_sys, dest_sectors[i]
        return None, None

    def process_turn(self):
        for player in self.players:
            if not player.alive:
                continue

            # Process repairs
            self._process_repairs(player)

            # Process purchases
            self._process_purchases(player)

            # Income
            income = calculate_income(player, self.planets)
            player.money += income

            # Maintenance
            maint = total_maintenance(player, self.ships, self.ship_classes)
            player.money -= maint

            # Population growth
            self._population_growth(player)

            # Execute ship orders
            self._execute_orders(player)

        self.turn_num += 1
        self._check_victory()

    def _process_repairs(self, player: Player):
        for ship in self.ships:
            if ship.owner == player.index and ship.damage > 0:
                sys = self.systems[ship.system]
                repair_rate = 0
                for p in self.planets:
                    if p.system == ship.system and p.owner == player.index:
                        if p.colony_type == 3:
                            repair_rate += 3
                for other in self.ships:
                    if other.system == ship.system and other.owner == player.index and other.ship_id != ship.ship_id:
                        cls = self.get_ship_class(other.class_id)
                        if cls:
                            compos = [get_compo(i) for i in cls.compo_set]
                            repair_rate += count_space_yards(compos) * 3
                if repair_rate > 0:
                    ship.damage = max(0, ship.damage - repair_rate)

    def _process_purchases(self, player: Player):
        pass

    def _population_growth(self, player: Player):
        for p in self.planets:
            if p.owner == player.index and p.colony_type > 0:
                growth = planet_position(p.population)
                p.population += growth
                max_pop = get_colony_max_pop(p.colony_type)
                if p.population > max_pop:
                    p.population = max_pop

    def _execute_orders(self, player: Player):
        for ship in self.ships:
            if ship.owner == player.index and ship.orders:
                self._execute_next_order(ship)

    def _execute_next_order(self, ship: Ship):
        if not ship.orders:
            return
        order = ship.orders[0]
        parts = order.split()
        if not parts:
            return

        cmd = parts[0]
        if cmd == "HLD":
            ship.orders = []
        elif cmd == "MOV" and len(parts) >= 3:
            try:
                target_sys = int(parts[1])
                target_sec = int(parts[2])
                ship.system = target_sys
                ship.sector = target_sec
                ship.orders.pop(0)
            except ValueError:
                ship.orders.pop(0)
        elif cmd == "CLN" and len(parts) >= 3:
            try:
                target_sys = int(parts[1])
                target_sec = int(parts[2])
                ship.system = target_sys
                ship.sector = target_sec
                self.colonize_planet(ship)
                ship.orders.pop(0)
            except ValueError:
                ship.orders.pop(0)
        else:
            ship.orders.pop(0)

    def _check_victory(self):
        alive_humans = 0
        alive_total = 0
        for p in self.players:
            if p.alive:
                alive_total += 1
                if not p.is_computer:
                    alive_humans += 1
        if self.turn_num >= 10 and alive_humans == 0:
            self.game_over = True
            self._send_message("All human players eliminated!", 0)
        elif self.turn_num >= 10 and alive_total <= 1:
            self.game_over = True
            for p in self.players:
                if p.alive:
                    self._send_message(f"{p.name} wins!", 0)
    def get_comp_bonus(self) -> float:
        if self.computer_difficulty == 1:
            return 0.75
        elif self.computer_difficulty == 2:
            return 1.0
        elif self.computer_difficulty == 3:
            return 1.5
        return 1.0
