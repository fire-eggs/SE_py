import random
import math

from entities import System, Planet
from config import *

SYSTEM_NAMES = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi",
    "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega",
    "Aurora", "Nova", "Vega", "Sirius", "Rigel", "Altair", "Deneb",
    "Polaris", "Capella", "Aldebaran", "Antares", "Arcturus", "Betelgeuse",
    "Canopus", "Castor", "Pollux", "Procyon", "Regulus", "Spica",
    "Achernar", "Fomalhaut", "Mira", "Proxima", "Sol", "Centauri",
    "Andromeda", "Cassiopeia", "Draco", "Phoenix", "Pegasus", "Orion",
    "Lyra", "Cygnus", "Aquila", "Perseus", "Hercules", "Sagittarius",
    "Corvus", "Lupus", "Ara", "Tucana", "Pavo", "Grus", "Indus",
    "Corona", "Serpens", "Scutum", "Sextans", "Antlia", "Pyxis",
    "Vela", "Carina", "Puppis", "Columba", "Lepus", "Canis",
    "Monoceros", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpius", "Ophiuchus", "Aquarius", "Pisces", "Aries", "Taurus",
    "Cepheus", "Lacerta", "Vulpecula", "Sagitta", "Delphinus", "Equuleus",
    "Bootes", "Coma", "Ursa", "Camelopardalis", "Lynx",
]

SYSTEM_GRID_SIZE = 50


def create_system(index: int, x: int, y: int) -> System:
    name = SYSTEM_NAMES[index % len(SYSTEM_NAMES)]
    if index >= len(SYSTEM_NAMES):
        name = f"{name} {index // len(SYSTEM_NAMES) + 1}"
    sys = System(name=name, sys_index=index, draw_x=x, draw_y=y)
    sys.sectors = [0] * MAX_SECTORS
    sys.warp_dest = []
    sys.warp_sector = []
    return sys


def place_stellar_objects(sys: System, planet_id_counter: list):
    for s in range(MAX_SECTORS):
        roll = random.random()
        if roll < 0.05:
            obj = random.choice([1, 2, 3, 4])
            sys.sectors[s] = obj
        elif roll < 0.10:
            sys.sectors[s] = random.choice([6, 7])
        elif roll < 0.13:
            sys.sectors[s] = random.choice([8, 9])
        elif roll < 0.16:
            sys.sectors[s] = random.choice([10, 11])
        elif roll < 0.20:
            obj = random.choice([12, 13, 14, 15, 16, 17])
            sys.sectors[s] = obj
        else:
            sys.sectors[s] = random.choice([0, 19, 20, 21, 22, 23, 24, 25, 26, 27])


def planet_position(population: int) -> int:
    if population < 250:
        return random.randint(1, population) if population > 0 else 0
    elif population < 1000:
        return random.randint(1, max(1, population // 5))
    elif population < 2000:
        return random.randint(1, max(1, population // 20))
    else:
        return random.randint(1, 20)


def get_colony_max_pop(colony_type: int) -> int:
    return COLONY_MAX_POP.get(colony_type, 0)


def generate_warp_points(systems: list[System], warp_freq: int):
    num = len(systems)
    if num < 2:
        return
    min_dist = 4
    max_dist = 18
    attempts_per_system = warp_freq * 3

    for i in range(num):
        sys_a = systems[i]
        target_count = min(warp_freq, 5 - len(sys_a.warp_dest))
        if target_count <= 0:
            continue

        candidates = []
        for j in range(num):
            if j == i:
                continue
            sys_b = systems[j]
            if len(sys_b.warp_dest) >= 5:
                continue
            if j in sys_a.warp_dest:
                continue
            dx = sys_a.draw_x - sys_b.draw_x
            dy = sys_a.draw_y - sys_b.draw_y
            dist = int(math.sqrt(dx * dx + dy * dy))
            if min_dist <= dist <= max_dist:
                candidates.append((dist, j))

        candidates.sort(key=lambda x: x[0])
        selected = candidates[:target_count]

        for dist, j in selected:
            # KBR 20260910 warps go only at edges
            edge_sectors = [s for s in range(MAX_SECTORS) 
               if s % SECTOR_COLS == 0 or s % SECTOR_COLS == SECTOR_COLS - 1
               or s // SECTOR_COLS == 0 or s // SECTOR_COLS == SECTOR_ROWS - 1
               and sys_a.sectors[s] == 0]

            sector_a = random.choice(edge_sectors) # random.randint(0, MAX_SECTORS - 1)
            sys_a.warp_dest.append(j)
            sys_a.warp_sector.append(sector_a)
            sys_a.sectors[sector_a] = 18

            edge_sectors = [s for s in range(MAX_SECTORS) 
               if s % SECTOR_COLS == 0 or s % SECTOR_COLS == SECTOR_COLS - 1
               or s // SECTOR_COLS == 0 or s // SECTOR_COLS == SECTOR_ROWS - 1
               and systems[j].sectors[s] == 0]

            sector_b = random.choice(edge_sectors) # random.randint(0, MAX_SECTORS - 1)
            systems[j].warp_dest.append(i)
            systems[j].warp_sector.append(sector_b)
            systems[j].sectors[sector_b] = 18


def generate_universe(num_systems: int, warp_freq: int, separation: int) -> list[System]:
    systems = []
    planet_id_counter = [0]

    existing_positions = set()

    for i in range(num_systems):
        placed = False
        for _ in range(100):
            x = random.randint(1, SYSTEM_GRID_SIZE - 2)
            y = random.randint(1, SYSTEM_GRID_SIZE - 2)
            valid = True
            for (ex, ey) in existing_positions:
                dx = x - ex
                dy = y - ey
                dist = int(math.sqrt(dx * dx + dy * dy))
                if dist < separation:
                    valid = False
                    break
            if valid:
                existing_positions.add((x, y))
                placed = True
                break
        if not placed:
            x = random.randint(1, SYSTEM_GRID_SIZE - 2)
            y = random.randint(1, SYSTEM_GRID_SIZE - 2)

        sys = create_system(i, x, y)
        place_stellar_objects(sys, planet_id_counter)
        systems.append(sys)

    generate_warp_points(systems, warp_freq)
    return systems


def find_colony_sectors(system: System) -> list[int]:
    sectors = []
    for i, obj in enumerate(system.sectors):
        if 1 <= obj <= 4:
            sectors.append(i)
    return sectors


def find_home_system_candidates(systems: list[System]) -> list[int]:
    candidates = []
    for i, sys in enumerate(systems):
        colony_sectors = find_colony_sectors(sys)
        if colony_sectors and len(sys.warp_dest) > 0:
            candidates.append(i)
    return candidates
