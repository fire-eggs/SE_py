"""Core data models for Space Empires"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import IntEnum, Enum
import random


class StellarType(IntEnum):
    """Types of stellar objects"""
    MOON = 1
    TERRESTROID = 2
    GASEOUS = 3
    GREEN = 4
    ASTEROIDS = 5
    PLANETOID = 6
    VAPOR_GIANT = 7
    MAGNETIC_STORM = 8
    HYDROGEN_CLOUD = 9
    COLLAPSING_STAR = 10
    RED_STAR = 11
    WARP_POINT = 12
    EMPTY = 13
    DESERT = 14
    YELLOW_STAR = 15
    SUPER_TERRESTROID = 16
    RINGED_GASEOUS = 17
    RED_PRIMARY = 18
    NEBULAE = 19
    RINGED_GAS = 20
    METHANE_BURNING = 21
    MACHINE_PLANET = 22


class PlanetType(IntEnum):
    """Planet/colony types"""
    NONE = 0
    PLANET = 1
    ASTEROID_BELT = 2
    MACHINE = 8


class ColonyType(IntEnum):
    """Colony development levels"""
    NONE = 0
    OUTPOST = 1
    COLONY = 2
    SETTLEMENT = 3


class ShipType(IntEnum):
    """Ship mission types"""
    NONE = 0
    ATTACK = 1
    DEFEND = 2
    SYARD_DEF = 3
    COLONIZE = 4
    CARGO = 5
    BASE_SYARD = 6
    SPACE_SYARD = 7
    SUN_DESTROY = 8
    OWP = 9
    CWP = 10


class ComponentType(str, Enum):
    """Component type codes"""
    ARMOR = "A"
    SHIELD = "B"
    CLOAK = "C"
    ENGINE = "E"
    HULL = "H"
    SYARD = "S"
    FIGHTER_BAY = "F"
    MINES = "M"
    ECM = "E"
    SENSORS = "S"
    PHASER = "P"
    MISSILE = "M"
    DRONE = "D"
    POINT_DEF = "P"
    PSYCHIC = "P"
    MINE_LAY = "M"
    WAVE = "W"
    DRONE2 = "D"
    REPAIR = "R"


@dataclass
class StellarObject:
    """A stellar object type definition"""
    type: StellarType
    description: str
    base_value: int


@dataclass
class Planet:
    """A planet in a star system"""
    index: int
    system: int
    sector: int
    value: int
    planet_type: PlanetType
    name: str
    colony_type: ColonyType = ColonyType.NONE
    owner: int = 0
    population: int = 0

    @property
    def is_colonized(self) -> bool:
        return self.colony_type != ColonyType.NONE and self.owner > 0

    @property
    def max_population(self) -> int:
        limits = {ColonyType.OUTPOST: 250, ColonyType.COLONY: 500, ColonyType.SETTLEMENT: 3000}
        return limits.get(self.colony_type, 0)


@dataclass
class StarSystem:
    """A star system with sectors"""
    index: int
    name: str
    draw_x: int = 0
    draw_y: int = 0
    stellar_objects: List[int] = field(default_factory=lambda: [99] * 81)  # 9x9 grid
    warp_dest: List[int] = field(default_factory=lambda: [0] * 6)
    warp_sector: List[int] = field(default_factory=lambda: [9999] * 6)
    warp_count: int = 0
    system_index: int = 0

    def get_sector_object(self, sector: int) -> int:
        if 0 <= sector < len(self.stellar_objects):
            return self.stellar_objects[sector]
        return 99

    def set_sector_object(self, sector: int, obj_type: int):
        if 0 <= sector < len(self.stellar_objects):
            self.stellar_objects[sector] = obj_type


@dataclass
class ShipHull:
    """Ship hull definition"""
    hull_id: int
    name: str
    cost: int
    size: int
    engines_per_move: int
    max_engines: int
    tech_level: int
    abbrev: str
    combat_value: int = 5


@dataclass
class Component:
    """Ship component definition"""
    abbrev: str
    name: str
    comp_type: str  # Single char: A,B,C,E,H,S,F,M,W,V,D,P,R
    size: int
    cost: int
    tech_level: int
    damage: int = 0
    range: int = 0
    speed: int = 0
    rate: int = 1
    decrease_dmg: int = 0
    fire_type: int = 1  # 1=direct, 2=seeker


@dataclass
class ShipClass:
    """Player-designed ship class"""
    class_index: int
    owner: int
    name: str
    hull_size: int
    ship_type: ShipType
    speed: int
    cost: int
    functions: str  # Component string
    compo_set: str  # Full component layout
    shields: int
    tech_level: int
    obsolete: bool = False


@dataclass
class Ship:
    """Individual ship instance"""
    ship_id: int
    name: str
    class_id: int
    system: int
    sector: int
    owner: int
    damage: int = 0
    speed: int = 0
    active_function: str = ""
    functions: str = ""
    cargo: str = ""
    orders: str = ""
    combat_map_index: int = -999

    @property
    def is_destroyed(self) -> bool:
        return self.owner <= 0


@dataclass
class Player:
    """Player empire"""
    player_id: int
    name: str
    is_computer: bool = False
    home_system: int = 0
    home_planet: int = 0
    money: int = 500
    tech_level: int = 1
    color: Tuple[int, int, int] = (196, 64, 0)
    ship_names_file: str = "myth.txt"
    available_components: Dict[int, bool] = field(default_factory=dict)
    repair_order: str = "000"


@dataclass
class CombatShip:
    """Ship in tactical combat"""
    ship_id: int
    class_id: int
    owner: int
    name: str
    size: int
    speed: int
    max_speed: int
    damage: int
    shields: int
    hull_integrity: int
    map_index: int
    functions: str
    component_damage: str  # Damaged components marked with *
    target: int = 0
    weapons_fired: Dict[int, int] = field(default_factory=dict)  # weapon_slot -> cooldown
    is_fighter: bool = False
    is_missile: bool = False
    carrier: int = 0


@dataclass
class GameState:
    """Complete game state"""
    # Universe
    systems: List[StarSystem] = field(default_factory=list)
    planets: List[Planet] = field(default_factory=list)
    stellar_objects: List[StellarObject] = field(default_factory=list)
    sector_map: Dict[Tuple[int, int], int] = field(default_factory=dict)  # (system, sector) -> planet_index
    
    # Players
    players: List[Player] = field(default_factory=list)
    num_players: int = 4
    max_players: int = 20
    current_player: int = 1
    turn_number: int = 1
    
    # Ships
    ships: List[Ship] = field(default_factory=list)
    ship_classes: List[ShipClass] = field(default_factory=list)
    next_ship_id: int = 1
    next_class_id: int = 1
    
    # Combat
    combat_system: int = 0
    combat_sector: int = 0
    combat_attacker: int = 0
    combat_defender: int = 0
    combat_ships: List[CombatShip] = field(default_factory=list)
    combat_fighters: List[CombatShip] = field(default_factory=list)
    combat_missiles: List[CombatShip] = field(default_factory=list)
    combat_stellar_type: int = 0
    combat_planet_population: int = 0
    in_combat: bool = False
    
    # Game settings
    galaxy_size: int = 50
    warp_point_freq: int = 0  # -1=many, 0=normal, 1=few
    warp_points_connect: bool = True
    empires_same_system: bool = False
    empires_sep_quads: bool = True
    neutrals_allowed: bool = False
    computer_difficulty: int = 3
    auto_save_turns: int = 5
    start_tech: int = 1
    
    # UI state
    active_system: int = 0
    selected_sector: int = 9999
    selected_ships: List[int] = field(default_factory=list)
    surrender_condition: bool = False
    game_over: bool = False
    winner: int = 0


# Stellar object definitions
STELLAR_DEFINITIONS = [
    StellarObject(StellarType.MOON, "Moon", 3),
    StellarObject(StellarType.TERRESTROID, "Terrestroid", 10),
    StellarObject(StellarType.GASEOUS, "Gaseous Planet", 5),
    StellarObject(StellarType.GREEN, "Green Planet", 7),
    StellarObject(StellarType.ASTEROIDS, "Asteroids", 5),
    StellarObject(StellarType.PLANETOID, "Planetoid", 4),
    StellarObject(StellarType.VAPOR_GIANT, "Vapor Giant", 2),
    StellarObject(StellarType.MAGNETIC_STORM, "Magnetic Storm", 0),
    StellarObject(StellarType.HYDROGEN_CLOUD, "Hydrogen Cloud", 0),
    StellarObject(StellarType.COLLAPSING_STAR, "Collapsing Star", 0),
    StellarObject(StellarType.RED_STAR, "Red Star", 0),
    StellarObject(StellarType.WARP_POINT, "Warp Point", 0),
    StellarObject(StellarType.EMPTY, "Empty Space", 0),
    StellarObject(StellarType.EMPTY, "Empty Space", 0),
    StellarObject(StellarType.EMPTY, "Empty Space", 0),
    StellarObject(StellarType.EMPTY, "Empty Space", 0),
    StellarObject(StellarType.DESERT, "Desert Planet", 4),
    StellarObject(StellarType.YELLOW_STAR, "Yellow Star", 0),
    StellarObject(StellarType.SUPER_TERRESTROID, "Super-Terrestroid", 12),
    StellarObject(StellarType.RINGED_GASEOUS, "Ringed Gaseous", 4),
    StellarObject(StellarType.RED_PRIMARY, "Red Primary", 0),
    StellarObject(StellarType.NEBULAE, "Nebulae", 0),
    StellarObject(StellarType.RINGED_GAS, "Ringed Gas Planet", 2),
    StellarObject(StellarType.METHANE_BURNING, "Methane-Burning Planet", 1),
    StellarObject(StellarType.MACHINE_PLANET, "Machine Planet", 15),
    StellarObject(StellarType.MACHINE_PLANET, "Machine Planet", 15),
    StellarObject(StellarType.MACHINE_PLANET, "Machine Planet", 15),
    StellarObject(StellarType.MACHINE_PLANET, "Machine Planet", 15),
]

# System names
SYSTEM_NAMES = [
    "Alpha Majori", "Altair", "Andromeda", "Ankel", "Arakis", "Arturous", "Bajor",
    "Beta Stromgren", "Betazed", "Binar", "Bradley Prime", "Burundi", "Bzintus",
    "Caprica", "Cardassia", "Carnak", "Centauri", "Chilk", "Cintak", "Cretanis",
    "Darazat", "Dark Junction", "Denevus", "Desok", "Dorz", "Dtarkn", "Dwerm",
    "Emada", "Estopholes", "Eukrates", "Falack", "Fbebe", "Fortunas", "Fyzan",
    "Gamalon", "Gemhadran", "Gharz", "Gizadra", "Hades", "Hemlock", "Hera",
    "Hneket", "Huju", "Ickyak", "Iman", "Imbari", "Itak", "Lomaz", "Lquanda",
    "Lucitan", "Lyrae", "Maelstrom", "Malfadoris", "Mentara", "Mrkan", "Mysterion",
    "Narcisus", "Nbarum", "Nitok", "Nizarus", "Omega Prime", "Ophidia",
    "Ophiuchi Junction", "Orion", "Orman", "Orzok", "Pandomn", "Pleades", "Praga",
    "Prokalon", "Qazat", "Quilden", "Qwakned", "Rigel", "Risa", "Romulus",
    "Sacnez", "Sentila", "Srutu", "Stalz", "Tchaikan", "Telume", "Terra",
    "Troilus", "Tyran", "Vesuiv", "Vorlon", "Vorva", "Vulcan", "Wada", "Welshra",
    "Wirtuy", "Wolf 359", "Wyukm", "Xtapa", "Xulum", "Xzintus", "Zertak", "Ziinar", "Zoltan"
]

# Ship hulls
HULL_DEFINITIONS = [
    ShipHull(0, "", 0, 0, 0, 0, 0, "", 0),
    ShipHull(1, "Escort", 100, 6, 1, 6, 1, "ES", 5),
    ShipHull(2, "Frigate", 150, 10, 1, 6, 2, "FG", 5),
    ShipHull(3, "Destroyer", 200, 15, 1, 6, 3, "DS", 5),
    ShipHull(4, "Light Cruiser", 300, 20, 1, 6, 4, "LC", 2),
    ShipHull(5, "Cruiser", 400, 35, 2, 12, 5, "CR", 2),
    ShipHull(6, "Battle Cruiser", 500, 40, 2, 12, 6, "BC", 2),
    ShipHull(7, "Battleship", 700, 50, 3, 15, 7, "BB", 2),
    ShipHull(8, "Dreadnought", 1000, 65, 5, 20, 10, "DN", 2),
    ShipHull(9, "Light Carrier", 300, 25, 1, 6, 12, "LX", 1),
    ShipHull(10, "Carrier", 500, 45, 2, 12, 13, "CX", 1),
    ShipHull(11, "Heavy Carrier", 700, 75, 3, 15, 14, "HX", 1),
    ShipHull(12, "Space Station", 200, 35, 0, 0, 1, "SS", 1),
    ShipHull(13, "Battle Station", 400, 75, 0, 0, 5, "BS", 1),
    ShipHull(14, "Starbase", 2000, 200, 0, 0, 8, "SB", 1),
]

# Component definitions
COMPONENT_DEFINITIONS = {
    "Ar1": Component("Ar1", "Armor I", "A", 1, 10, 1, damage=0),
    "Chd": Component("Chd", "Cloaking Device", "C", 5, 100, 10),
    "Cl1": Component("Cl1", "Colonizer I", "C", 10, 200, 1),
    "En1": Component("En1", "Engine I", "E", 1, 20, 1, speed=1),
    "Hul": Component("Hul", "Hull", "H", 1, 0, 1),
    "Sy1": Component("Sy1", "Ship Yard I", "S", 20, 500, 5),
    "Sy2": Component("Sy2", "Ship Yard II", "S", 30, 800, 10),
    "Sy3": Component("Sy3", "Ship Yard III", "S", 50, 1500, 15),
    "Fb1": Component("Fb1", "Fighter Bay I", "F", 10, 200, 8, damage=5, range=10, speed=3),
    "Fb2": Component("Fb2", "Fighter Bay II", "F", 15, 350, 12, damage=10, range=15, speed=4),
    "Fb3": Component("Fb3", "Fighter Bay III", "F", 20, 500, 16, damage=15, range=20, speed=5),
    "MOp": Component("MOp", "Outpost Module", "M", 5, 100, 1),
    "MCl": Component("MCl", "Colony Module", "M", 15, 500, 3),
    "MSt": Component("MSt", "Settlement Module", "M", 30, 1500, 7),
    "Ec1": Component("Ec1", "ECM I", "E", 3, 150, 5),
    "Ec2": Component("Ec2", "ECM II", "E", 5, 300, 10),
    "Ec3": Component("Ec3", "ECM III", "E", 8, 500, 15),
    "Se1": Component("Se1", "Sensors I", "S", 2, 50, 1, range=5),
    "Se2": Component("Se2", "Sensors II", "S", 3, 100, 5, range=10),
    "Se3": Component("Se3", "Sensors III", "S", 5, 200, 10, range=15),
    "Mx2": Component("Mx2", "Minelayer II", "M", 5, 100, 3),
    "Mx3": Component("Mx3", "Minelayer III", "M", 8, 200, 7),
    "Mx4": Component("Mx4", "Minelayer IV", "M", 10, 300, 10),
    "Mx5": Component("Mx5", "Minelayer V", "M", 12, 400, 12),
    "Mx6": Component("Mx6", "Minelayer VI", "M", 15, 500, 14),
    "Mx7": Component("Mx7", "Minelayer VII", "M", 18, 600, 16),
    "Mx8": Component("Mx8", "Minelayer VIII", "M", 20, 800, 18),
    "Mx9": Component("Mx9", "Minelayer IX", "M", 25, 1000, 20),
    "Ow1": Component("Ow1", "Warp Opener I", "W", 10, 500, 8),
    "Cw1": Component("Cw1", "Warp Closer I", "W", 10, 500, 8),
    "Ds1": Component("Ds1", "Self Destruct", "D", 1, 10, 1),
    "Ph1": Component("Ph1", "Phaser I", "P", 3, 100, 1, damage=10, range=3, decrease_dmg=1),
    "Ph2": Component("Ph2", "Phaser II", "P", 4, 200, 4, damage=15, range=4, decrease_dmg=1),
    "Ph3": Component("Ph3", "Phaser III", "P", 5, 350, 7, damage=20, range=5, decrease_dmg=2),
    "Ph4": Component("Ph4", "Phaser IV", "P", 6, 500, 10, damage=25, range=6, decrease_dmg=2),
    "Ph5": Component("Ph5", "Phaser V", "P", 7, 700, 13, damage=30, range=7, decrease_dmg=3),
    "Ph6": Component("Ph6", "Phaser VI", "P", 8, 1000, 16, damage=35, range=8, decrease_dmg=3),
    "Ph7": Component("Ph7", "Phaser VII", "P", 10, 1500, 19, damage=40, range=9, decrease_dmg=4),
    "Ph8": Component("Ph8", "Phaser VIII", "P", 12, 2000, 22, damage=50, range=10, decrease_dmg=5),
    "Ph9": Component("Ph9", "Phaser IX", "P", 15, 3000, 25, damage=60, range=12, decrease_dmg=6),
    "Dr1": Component("Dr1", "Drone I", "D", 5, 200, 5, damage=15, range=8, speed=4),
    "Dr2": Component("Dr2", "Drone II", "D", 7, 350, 9, damage=25, range=10, speed=5),
    "Dr3": Component("Dr3", "Drone III", "D", 10, 500, 13, damage=35, range=12, speed=6),
    "Dr4": Component("Dr4", "Drone IV", "D", 12, 700, 17, damage=50, range=15, speed=7),
    "Dr5": Component("Dr5", "Drone V", "D", 15, 1000, 21, damage=65, range=18, speed=8),
    "Pt1": Component("Pt1", "Point Defense I", "P", 2, 100, 3, damage=5, range=2, rate=2),
    "Pt2": Component("Pt2", "Point Defense II", "P", 3, 200, 7, damage=10, range=3, rate=2),
    "Pt3": Component("Pt3", "Point Defense III", "P", 4, 350, 11, damage=15, range=4, rate=3),
    "Pt4": Component("Pt4", "Point Defense IV", "P", 5, 500, 15, damage=20, range=5, rate=3),
    "Pt5": Component("Pt5", "Point Defense V", "P", 6, 700, 19, damage=25, range=6, rate=4),
    "Ml1": Component("Ml1", "Missile Launcher I", "M", 5, 200, 4, damage=20, range=10, speed=5, fire_type=2),
    "Ml2": Component("Ml2", "Missile Launcher II", "M", 8, 400, 8, damage=35, range=15, speed=6, fire_type=2),
    "Ps1": Component("Ps1", "Psychic I", "P", 5, 300, 12, damage=15, range=5),
    "Ps2": Component("Ps2", "Psychic II", "P", 8, 500, 16, damage=25, range=8),
    "Ps3": Component("Ps3", "Psychic III", "P", 10, 800, 20, damage=35, range=10),
    "Ps4": Component("Ps4", "Psychic IV", "P", 12, 1200, 24, damage=50, range=12),
    "Ps5": Component("Ps5", "Psychic V", "P", 15, 2000, 28, damage=65, range=15),
    "Ma1": Component("Ma1", "Matter Cannon I", "M", 8, 400, 10, damage=25, range=4, decrease_dmg=2),
    "Ma2": Component("Ma2", "Matter Cannon II", "M", 12, 700, 14, damage=40, range=5, decrease_dmg=3),
    "Ma3": Component("Ma3", "Matter Cannon III", "M", 15, 1000, 18, damage=60, range=6, decrease_dmg=4),
    "Wm1": Component("Wm1", "Wave Gun I", "W", 10, 500, 12, damage=30, range=6, decrease_dmg=3),
    "Wm2": Component("Wm2", "Wave Gun II", "W", 15, 800, 16, damage=45, range=8, decrease_dmg=4),
    "Wm3": Component("Wm3", "Wave Gun III", "W", 20, 1200, 20, damage=65, range=10, decrease_dmg=5),
    "Dn1": Component("Dn1", "Drone Fighter I", "D", 5, 200, 8, damage=10, range=8, speed=4),
    "Dn2": Component("Dn2", "Drone Fighter II", "D", 7, 350, 12, damage=20, range=10, speed=5),
    "Dn3": Component("Dn3", "Drone Fighter III", "D", 10, 500, 16, damage=30, range=12, speed=6),
    "Dn4": Component("Dn4", "Drone Fighter IV", "D", 12, 700, 20, damage=40, range=15, speed=7),
    "Dn5": Component("Dn5", "Drone Fighter V", "D", 15, 1000, 24, damage=50, range=18, speed=8),
    "Rb1": Component("Rb1", "Repair Bot I", "R", 3, 150, 6, rate=1),
    "Rb2": Component("Rb2", "Repair Bot II", "R", 5, 300, 11, rate=2),
    "Rb3": Component("Rb3", "Repair Bot III", "R", 7, 500, 16, rate=3),
    "Rb4": Component("Rb4", "Repair Bot IV", "R", 10, 800, 21, rate=5),
}

COMPONENT_ABBREVS = list(COMPONENT_DEFINITIONS.keys())


def get_stellar_object(obj_type: int) -> Optional[StellarObject]:
    """Get stellar object definition by type index"""
    if 0 <= obj_type < len(STELLAR_DEFINITIONS):
        return STELLAR_DEFINITIONS[obj_type]
    return None


def get_hull(hull_id: int) -> Optional[ShipHull]:
    """Get hull definition by ID"""
    for hull in HULL_DEFINITIONS:
        if hull.hull_id == hull_id:
            return hull
    return None


def get_component(abbrev: str) -> Optional[Component]:
    """Get component definition by abbreviation"""
    return COMPONENT_DEFINITIONS.get(abbrev)


def hull_abbrev_to_index(abbrev: str) -> int:
    """Convert hull abbreviation to hull index"""
    for hull in HULL_DEFINITIONS:
        if hull.abbrev == abbrev:
            return hull.hull_id
    return 0