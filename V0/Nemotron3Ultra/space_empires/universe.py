"""Universe generation and galaxy management"""
import random
import math
from typing import List, Tuple, Dict, Optional
from space_empires.models import (
    GameState, StarSystem, Planet, StellarObject, StellarType, PlanetType,
    ColonyType, Player, Ship, ShipClass, ShipType, HULL_DEFINITIONS,
    STELLAR_DEFINITIONS, SYSTEM_NAMES, get_stellar_object, get_hull
)


SYSTEM_WIDTH = 9
SYSTEM_HEIGHT = 9
MAX_SECTORS = SYSTEM_WIDTH * SYSTEM_HEIGHT  # 81
MAX_WARPS = 5
MAX_STELLAR_OBJS = 27


def distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Euclidean distance between two points"""
    return int(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))


def angle_between(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate angle between two points in degrees (0-359)"""
    dx = x2 - x1
    dy = y2 - y1
    if dy == 0:
        if dx < 0:
            return 270
        elif dx > 0:
            return 90
        return 0
    angle = int(math.atan(dx / dy) * (180 / math.pi))
    if x2 >= x1 and y2 > y1:
        angle = 180 - angle
    elif x2 < x1 and y2 > y1:
        angle = 180 + angle
    elif x2 < x1 and y2 < y1:
        angle = 360 - angle
    if angle == 360:
        angle = 0
    return angle


def angle_diff(a1: int, a2: int) -> int:
    """Calculate smallest difference between two angles"""
    diff = abs(a1 - a2)
    if a1 > 270 and a2 < 90:
        diff = 360 - a1 + a2
    elif a2 > 270 and a1 < 90:
        diff = 360 - a2 + a1
    return diff


def star_index() -> int:
    """Get the center sector index (where the star is)"""
    return int(SYSTEM_HEIGHT / 2) * SYSTEM_WIDTH + int(SYSTEM_WIDTH / 2)


def create_universe(state: GameState):
    """Generate the galaxy with star systems"""
    state.systems = [None]  # 1-indexed
    state.planets = [None]  # 1-indexed
    state.stellar_objects = STELLAR_DEFINITIONS.copy()
    state.sector_map = {}
    
    # Create systems
    for i in range(1, state.galaxy_size + 1):
        system = StarSystem(index=i, name="", system_index=i)
        state.systems.append(system)
    
    # Assign random positions and names
    used_positions = set()
    name_pool = SYSTEM_NAMES.copy()
    random.shuffle(name_pool)
    
    for i, system in enumerate(state.systems[1:], 1):
        system.name = name_pool[i - 1] if i <= len(name_pool) else f"System {i}"
        
        # Find non-adjacent position
        attempts = 0
        while attempts < 1000:
            x = random.randint(0, 49)  # 50x50 grid
            y = random.randint(0, 49)
            too_close = False
            for other in state.systems[1:]:
                if other.system_index > 0 and other.draw_x == x and other.draw_y == y:
                    too_close = True
                    break
                if other.system_index > 0 and abs(other.draw_x - x) <= 1 and abs(other.draw_y - y) <= 1:
                    too_close = True
                    break
            if not too_close:
                system.draw_x = x
                system.draw_y = y
                break
            attempts += 1
    
    # Initialize system contents
    setup_systems(state)
    
    # Create warp connections
    create_warp_network(state)
    
    # Setup players
    setup_players(state)


def setup_systems(state: GameState):
    """Populate each system with planets, stars, warp points"""
    # Categorize stellar objects by type
    by_type: Dict[int, List[int]] = {}
    for idx, obj in enumerate(state.stellar_objects):
        if obj.type <= 8:  # Planets, stars, etc.
            if obj.type not in by_type:
                by_type[obj.type] = []
            by_type[obj.type].append(idx)
    
    for system in state.systems[1:]:
        # Clear system
        system.stellar_objects = [99] * MAX_SECTORS  # 99 = unassigned
        system.warp_dest = [0] * (MAX_WARPS + 1)
        system.warp_sector = [9999] * (MAX_WARPS + 1)
        system.warp_count = 0
        
        # 80% chance of normal system with star
        if random.random() < 0.8:
            # Place star in center
            center = star_index()
            star_type = random.choice(by_type.get(4, [10]))  # Type 4 = stars
            system.stellar_objects[center] = star_type
            
            # Add 1-9 planets/asteroids
            num_objects = random.randint(1, 9)
            for _ in range(num_objects):
                # Find empty sector (not center, not edge)
                empty_sectors = [s for s in range(MAX_SECTORS) 
                               if system.stellar_objects[s] == 99 
                               and s != center
                               and (s % SYSTEM_WIDTH) not in (0, SYSTEM_WIDTH - 1)
                               and (s // SYSTEM_WIDTH) not in (0, SYSTEM_HEIGHT - 1)]
                if not empty_sectors:
                    break
                sector = random.choice(empty_sectors)
                
                roll = random.randint(1, 15)
                if roll == 1:
                    # Magnetic storm, hydrogen cloud, etc.
                    obj_type = random.choice(by_type.get(3, [12]))
                elif roll <= 3:
                    # Asteroids
                    obj_type = random.choice(by_type.get(2, [4]))
                    create_planet(state, system.system_index, sector, PlanetType.ASTEROID_BELT)
                else:
                    # Regular planet
                    obj_type = random.choice(by_type.get(1, [1]))
                    create_planet(state, system.system_index, sector, PlanetType.PLANET)
                system.stellar_objects[sector] = obj_type
        else:
            # Special system (no star)
            special_type = random.choice([7, 8, 9])  # Collapsing star, nebulae, etc.
            center = star_index()
            system.stellar_objects[center] = random.choice(by_type.get(special_type, [10]))
            
            num_objects = random.randint(1, 9)
            for _ in range(num_objects):
                empty_sectors = [s for s in range(MAX_SECTORS) 
                               if system.stellar_objects[s] == 99]
                if not empty_sectors:
                    break
                sector = random.choice(empty_sectors)
                if special_type == 7:  # Collapsing star
                    system.stellar_objects[sector] = random.choice(by_type.get(2, [4]))
                    create_planet(state, system.system_index, sector, PlanetType.PLANET)
                else:
                    system.stellar_objects[sector] = random.choice(by_type.get(3, [12]))
        
        # Fill remaining with empty space
        empty_type = random.choice(by_type.get(6, [12]))
        for s in range(MAX_SECTORS):
            if system.stellar_objects[s] == 99:
                system.stellar_objects[s] = empty_type
        
        # Add warp points
        num_warps = random.randint(1, 3)
        edge_sectors = [s for s in range(MAX_SECTORS) 
                       if s % SYSTEM_WIDTH == 0 or s % SYSTEM_WIDTH == SYSTEM_WIDTH - 1
                       or s // SYSTEM_WIDTH == 0 or s // SYSTEM_WIDTH == SYSTEM_HEIGHT - 1]
        
        for _ in range(num_warps):
            if not edge_sectors:
                break
            sector = random.choice(edge_sectors)
            edge_sectors.remove(sector)
            if system.stellar_objects[sector] == empty_type:
                system.stellar_objects[sector] = 11  # Warp point type
                system.warp_count += 1
                system.warp_sector[system.warp_count] = sector


def create_planet(state: GameState, system_idx: int, sector: int, ptype: PlanetType):
    """Create a planet in the given system/sector"""
    obj_idx = state.systems[system_idx].stellar_objects[sector]
    stellar_obj = get_stellar_object(obj_idx)
    base_value = stellar_obj.base_value if stellar_obj else 10
    
    value = base_value * 50 + random.randint(0, 99)
    
    planet = Planet(
        index=len(state.planets),
        system=system_idx,
        sector=sector,
        value=value,
        planet_type=ptype,
        name="",
        colony_type=ColonyType.NONE,
        owner=0,
        population=0
    )
    state.planets.append(planet)
    state.sector_map[(system_idx, sector)] = planet.index


def get_planet_at_sector(state: GameState, system_idx: int, sector: int) -> Optional[Planet]:
    """Get planet at system/sector"""
    idx = state.sector_map.get((system_idx, sector))
    if idx and idx < len(state.planets):
        return state.planets[idx]
    return None


def create_warp_network(state: GameState):
    """Connect systems with warp points"""
    # Build list of nearby systems for each system
    nearby: Dict[int, List[int]] = {}
    for sys_a in state.systems[1:]:
        nearby[sys_a.system_index] = []
        for sys_b in state.systems[1:]:
            if sys_a.system_index != sys_b.system_index:
                dist = distance(sys_a.draw_x, sys_a.draw_y, sys_b.draw_x, sys_b.draw_y)
                nearby[sys_a.system_index].append((dist, sys_b.system_index))
        nearby[sys_a.system_index].sort()
        nearby[sys_a.system_index] = [s[1] for s in nearby[sys_a.system_index][:20]]
    
    # Connect warp points
    warp_freq_mod = { -1: 8, 0: 10, 1: 15 }.get(state.warp_point_freq, 10)
    
    for system in state.systems[1:]:
        candidates = nearby[system.system_index][:system.warp_count] if system.warp_count > 0 else []
        
        for i in range(1, system.warp_count + 1):
            if not candidates:
                break
            dest_idx = candidates.pop(0)
            dest_system = state.systems[dest_idx]
            
            if dest_system.warp_count < MAX_WARPS:
                # Connect both ways
                system.warp_dest[i] = dest_idx
                
                dest_system.warp_count += 1
                dest_system.warp_dest[dest_system.warp_count] = system.system_index
                
                # Assign sector in destination
                edge_sectors = [s for s in range(MAX_SECTORS)
                              if dest_system.stellar_objects[s] == 12  # Empty space
                              and (s % SYSTEM_WIDTH == 0 or s % SYSTEM_WIDTH == SYSTEM_WIDTH - 1
                                   or s // SYSTEM_WIDTH == 0 or s // SYSTEM_WIDTH == SYSTEM_HEIGHT - 1)]
                if edge_sectors:
                    sector = random.choice(edge_sectors)
                    dest_system.warp_sector[dest_system.warp_count] = sector
                    dest_system.stellar_objects[sector] = 11  # Warp point
    
    # Ensure connectivity if enabled
    if state.warp_points_connect:
        ensure_warp_connectivity(state)


def ensure_warp_connectivity(state: GameState):
    """Ensure all systems are connected via warp network"""
    # Simple BFS to check connectivity
    visited = set()
    queue = [1]
    visited.add(1)
    
    while queue:
        current = queue.pop(0)
        system = state.systems[current]
        for i in range(1, system.warp_count + 1):
            dest = system.warp_dest[i]
            if dest > 0 and dest not in visited:
                visited.add(dest)
                queue.append(dest)
    
    # Connect disconnected components
    all_systems = set(range(1, len(state.systems)))
    disconnected = all_systems - visited
    
    for sys_idx in disconnected:
        system = state.systems[sys_idx]
        # Find nearest connected system
        best_dist = 999
        best_target = 1
        for target_idx in visited:
            target = state.systems[target_idx]
            dist = distance(system.draw_x, system.draw_y, target.draw_x, target.draw_y)
            if dist < best_dist:
                best_dist = dist
                best_target = target_idx
        
        # Add warp connection
        if system.warp_count < MAX_WARPS:
            system.warp_count += 1
            system.warp_dest[system.warp_count] = best_target
            
            target = state.systems[best_target]
            if target.warp_count < MAX_WARPS:
                target.warp_count += 1
                target.warp_dest[target.warp_count] = sys_idx
                
                # Find empty edge sector
                edge_sectors = [s for s in range(MAX_SECTORS)
                              if target.stellar_objects[s] == 12
                              and (s % SYSTEM_WIDTH == 0 or s % SYSTEM_WIDTH == SYSTEM_WIDTH - 1
                                   or s // SYSTEM_WIDTH == 0 or s // SYSTEM_WIDTH == SYSTEM_HEIGHT - 1)]
                if edge_sectors:
                    sector = random.choice(edge_sectors)
                    target.warp_sector[target.warp_count] = sector
                    target.stellar_objects[sector] = 11


def setup_players(state: GameState):
    """Initialize player empires"""
    state.players = [None]  # 1-indexed
    
    # Human player (1)
    human = Player(
        player_id=1,
        name="Human",
        is_computer=False,
        money=random.randint(500, 700),
        tech_level=state.start_tech,
        color=(196, 64, 0),
        ship_names_file="myth.txt"
    )
    state.players.append(human)
    
    # Computer players
    name_files = ["myth.txt", "animals.txt", "misc.txt", "states.txt"]
    colors = [
        (196, 64, 0),   # Red-orange
        (0, 128, 255),  # Blue
        (0, 255, 0),    # Green
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
    ]
    
    for i in range(2, state.num_players + 1):
        comp = Player(
            player_id=i,
            name=f"AI Empire {i-1}",
            is_computer=True,
            money=random.randint(300, 500),
            tech_level=state.start_tech + random.randint(0, 3),
            color=colors[(i-1) % len(colors)],
            ship_names_file=name_files[(i-1) % len(name_files)]
        )
        state.players.append(comp)
    
    # Place home systems
    available_systems = list(range(1, len(state.systems)))
    random.shuffle(available_systems)
    
    for i, player in enumerate(state.players[1:], 1):
        if not available_systems:
            break
        home_sys_idx = available_systems.pop()
        home_system = state.systems[home_sys_idx]
        
        # Find a planet sector for homeworld
        planet_sectors = [s for s in range(MAX_SECTORS) 
                         if get_planet_at_sector(state, home_sys_idx, s) is not None]
        if not planet_sectors:
            continue
        
        home_sector = random.choice(planet_sectors)
        planet = get_planet_at_sector(state, home_sys_idx, home_sector)
        
        if planet:
            player.home_system = home_sys_idx
            player.home_planet = home_sector
            planet.owner = i
            planet.colony_type = ColonyType.SETTLEMENT
            planet.population = 500
            planet.name = f"{player.name} Homeworld"
            planet.value = player.money
            
            # Create starting ship
            create_starting_ship(state, i, home_sys_idx, home_sector)
            
            # Mark system as explored
            state.systems[home_sys_idx].explored_by = getattr(state.systems[home_sys_idx], 'explored_by', set())
            state.systems[home_sys_idx].explored_by.add(i)


def create_starting_ship(state: GameState, owner: int, system: int, sector: int):
    """Create a starting scout ship for a player"""
    hull = get_hull(1)  # Escort
    if not hull:
        return
    
    ship_class = ShipClass(
        class_index=state.next_class_id,
        owner=owner,
        name="Scout",
        hull_size=1,
        ship_type=ShipType.ATTACK,
        speed=hull.engines_per_move,
        cost=hull.cost,
        functions="En1",
        compo_set="HulEn1",
        shields=0,
        tech_level=1
    )
    state.ship_classes.append(ship_class)
    state.next_class_id += 1
    
    ship = Ship(
        ship_id=state.next_ship_id,
        name="Scout 001",
        class_id=ship_class.class_index,
        system=system,
        sector=sector,
        owner=owner,
        speed=ship_class.speed,
        functions=ship_class.functions
    )
    state.ships.append(ship)
    state.next_ship_id += 1


def is_planet(state: GameState, system: int, sector: int) -> bool:
    """Check if sector contains a colonizable planet"""
    obj_idx = state.systems[system].get_sector_object(sector)
    stellar = get_stellar_object(obj_idx)
    return stellar and stellar.type in (1, 2)  # Terrestroid, Gaseous, etc.


def is_star(state: GameState, system: int, sector: int) -> bool:
    """Check if sector contains a star"""
    obj_idx = state.systems[system].get_sector_object(sector)
    stellar = get_stellar_object(obj_idx)
    return stellar and stellar.type == 4


def is_warp_point(state: GameState, system: int, sector: int) -> bool:
    """Check if sector contains a warp point"""
    obj_idx = state.systems[system].get_sector_object(sector)
    stellar = get_stellar_object(obj_idx)
    return stellar and stellar.type == 5


def is_empty_space(state: GameState, system: int, sector: int) -> bool:
    """Check if sector is empty space"""
    obj_idx = state.systems[system].get_sector_object(sector)
    stellar = get_stellar_object(obj_idx)
    return stellar and stellar.type == 6


def is_cloaking(state: GameState, system: int, sector: int) -> bool:
    """Check if sector has cloaking (magnetic storm)"""
    obj_idx = state.systems[system].get_sector_object(sector)
    stellar = get_stellar_object(obj_idx)
    return stellar and stellar.type == 3


def is_machine(state: GameState, system: int, sector: int) -> bool:
    """Check if sector has machine planet"""
    obj_idx = state.systems[system].get_sector_object(sector)
    stellar = get_stellar_object(obj_idx)
    return stellar and stellar.type == 8


def get_sector_description(state: GameState, system: int, sector: int, show_ships: bool = False) -> str:
    """Get text description of a sector"""
    lines = [f"Sector: {sector}"]
    
    planet = get_planet_at_sector(state, system, sector)
    obj_idx = state.systems[system].get_sector_object(sector)
    stellar = get_stellar_object(obj_idx)
    
    if planet and planet.name:
        lines.append(f"Name: {planet.name}")
        lines.append(f"Value: {planet.value}")
        if stellar:
            lines.append(f"Description: {stellar.description}")
        
        if show_ships and planet.colony_type > 0:
            colony_names = {1: "Outpost", 2: "Colony", 3: "Settlement"}
            lines.append(f"{state.players[planet.owner].name} {colony_names.get(planet.colony_type, '')}")
            lines.append(f"Population: {planet.population:,}M")
    elif stellar:
        if is_warp_point(state, system, sector):
            lines.append(f"Description: {stellar.description} to ")
            for i in range(1, state.systems[system].warp_count + 1):
                if state.systems[system].warp_sector[i] == sector:
                    dest = state.systems[system].warp_dest[i]
                    lines[-1] += state.systems[dest].name
                    break
        else:
            lines.append(f"Description: {stellar.description}")
    
    if show_ships:
        # Find first ship in sector
        for ship in state.ships:
            if ship.system == system and ship.sector == sector and ship.owner > 0:
                hull = get_hull(state.ship_classes[ship.class_id - 1].hull_size) if ship.class_id <= len(state.ship_classes) else None
                lines.append("")
                lines.append(f"{state.players[ship.owner].name} Empire - {ship.name}, {hull.abbrev if hull else '??'}")
                lines.append(f"Mvt:{ship.speed} Dmg:{ship.damage}")
                break
    
    return "\n".join(lines)