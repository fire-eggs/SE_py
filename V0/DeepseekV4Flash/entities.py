import random
from dataclasses import dataclass, field
from typing import Optional

from config import *


@dataclass
class Component:
    index: int
    name: str
    category: str
    size: int
    cost: int
    tech: int
    damage: int = 0
    range_val: int = 0
    decrease_dmg: int = 0
    rate: int = 0
    speed: int = 0
    fire_type: int = 0
    comp_type: int = 0
    abbr: str = ""


@dataclass
class ShipHull:
    index: int
    abbr: str
    name: str
    size: int
    cost: int
    tech: int
    epm: int
    max_eng: int


@dataclass
class ShipClass:
    owner: int = 0
    size: int = 0
    type_name: str = ""
    name: str = ""
    speed: int = 0
    cost: int = 0
    class_index: int = 0
    functions: int = 0
    compo_set: list = field(default_factory=list)
    shields: int = 0
    tech: int = 0
    obsolete: bool = False


@dataclass
class Ship:
    name: str = ""
    ship_id: int = 0
    class_id: int = 0
    system: int = 0
    sector: int = 0
    owner: int = 0
    damage: int = 0
    speed: int = 0
    active_func: int = 0
    functions: int = 0
    cargo: list = field(default_factory=list)
    orders: list = field(default_factory=list)
    cloaked: bool = False
    fighters: int = 0
    max_fighters: int = 0


@dataclass
class Planet:
    planet_id: int = 0
    value: int = 0
    type_idx: int = 0
    name: str = ""
    colony_type: int = 0
    owner: int = 0
    population: int = 0
    system: int = 0
    sector: int = 0


@dataclass
class System:
    name: str = ""
    sys_index: int = 0
    draw_x: int = 0
    draw_y: int = 0
    warp_dest: list = field(default_factory=list)
    warp_sector: list = field(default_factory=list)
    sectors: list = field(default_factory=list)

    @property
    def warp_count(self):
        return len(self.warp_dest)


@dataclass
class Player:
    index: int = 0
    name: str = ""
    tech: int = 1
    money: int = 0
    home_system: int = 0
    home_planet: int = 0
    ship_name_file: int = 0
    is_computer: bool = False
    alive: bool = True
    turn_to_buy_tech: int = 1
    avail_compo: list = field(default_factory=lambda: [False] * MAX_COMPONENTS)
    ship_names_used: set = field(default_factory=set)


@dataclass
class CombatShip:
    ship_id: int = 0
    owner: int = 0
    name: str = ""
    class_name: str = ""
    x: int = 0
    y: int = 0
    damage: int = 0
    max_damage: int = 0
    speed: int = 0
    moved: bool = False
    fired: bool = False
    destroyed: bool = False
    components: list = field(default_factory=list)
    shields: int = 0
    has_fighters: bool = False
    fighter_count: int = 0


@dataclass
class CombatFighter:
    owner: int = 0
    x: int = 0
    y: int = 0
    damage: int = 5
    speed: int = 3
    range_val: int = 3
    moved: bool = False
    destroyed: bool = False
    target_x: int = -1
    target_y: int = -1


SHIP_NAME_POOLS = {}


def load_ship_names():
    base = "data"
    import os
    files = {
        "Myth": os.path.join(base, "myth.txt"),
        "Animals": os.path.join(base, "animals.txt"),
        "Misc": os.path.join(base, "misc.txt"),
        "States": os.path.join(base, "states.txt"),
    }
    for pool_name, fpath in files.items():
        try:
            with open(fpath) as f:
                names = [line.strip() for line in f if line.strip()]
                SHIP_NAME_POOLS[pool_name] = names
        except FileNotFoundError:
            SHIP_NAME_POOLS[pool_name] = [f"{pool_name}-{i}" for i in range(1, 101)]


def get_ship_name(pool_name: str, used: set) -> str:
    pool = SHIP_NAME_POOLS.get(pool_name, ["Unnamed"])
    available = [n for n in pool if n not in used]
    if not available:
        return f"{pool_name}-{len(used) + 1}"
    name = random.choice(available)
    return name
