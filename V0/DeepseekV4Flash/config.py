MAX_SYSTEMS = 100
MAX_PLAYERS = 20
MAX_ACTIVE_PLAYERS = 4
MAX_SECTORS = 81
SECTOR_ROWS = 9
SECTOR_COLS = 9
MAX_TECH = 11
MAX_COMPONENTS = 72
MAX_SHIP_CLASSES = 200
MAX_SHIPS = 500
MAX_PLANETS = 500
MAX_ORDERS = 50
COMBAT_WIDTH = 11
COMBAT_HEIGHT = 13
MAX_COMBAT_PHASES = 20
MAX_FIGHTERS_PER_SHIP = 40

TECH_COST_MULTIPLIER = 500
MAINTENANCE_RATE = 0.03
SHIELD_COST_PER_POINT = 1

COLORS = {
    0: "gray",
    1: "red",
    2: "green",
    3: "blue",
    4: "magenta",
    5: "cyan",
    6: "brown",
    7: "orange",
    8: "purple",
    9: "yellow",
}

PLAYER_COLORS = {
    1: "#FF0000",
    2: "#00AA00",
    3: "#0000FF",
    4: "#FF00FF",
}

STELLAR_OBJECTS = [
    "Empty Space",          # 0
    "Terrestroid Planet",   # 1
    "Green Planet",         # 2
    "Desert Planet",        # 3
    "Ice Planet",           # 4
    "Gas Giant",            # 5
    "Asteroid",             # 6
    "Asteroid",             # 7
    "Moon",                 # 8
    "Moon",                 # 9
    "Magnetic Storm",       # 10
    "Hydrogen Cloud",       # 11
    "Red Star",             # 12
    "Yellow Star",          # 13
    "White Star",           # 14
    "Blue Star",            # 15
    "Neutron Star",         # 16
    "Collapsing Star",      # 17
    "Warp Point",           # 18
    "Empty Space",          # 19
    "Empty Space",          # 20
    "Empty Space",          # 21
    "Empty Space",          # 22
    "Empty Space",          # 23
    "Empty Space",          # 24
    "Empty Space",          # 25
    "Empty Space",          # 26
    "Empty Space",          # 27
]

COLONY_TYPES = {
    0: "None",
    1: "Outpost",
    2: "Colony",
    3: "Settlement",
}

COLONY_MAX_POP = {0: 0, 1: 250, 2: 500, 3: 3000}

HULL_TYPES = [
    {"abbr": "ES", "name": "Escort",       "size": 6,   "cost": 100,  "tech": 1,  "epm": 1, "max_eng": 6},
    {"abbr": "FG", "name": "Frigate",      "size": 10,  "cost": 150,  "tech": 2,  "epm": 1, "max_eng": 6},
    {"abbr": "DS", "name": "Destroyer",    "size": 15,  "cost": 200,  "tech": 3,  "epm": 1, "max_eng": 6},
    {"abbr": "LC", "name": "Light Cruiser","size": 20,  "cost": 300,  "tech": 4,  "epm": 1, "max_eng": 6},
    {"abbr": "CR", "name": "Cruiser",      "size": 35,  "cost": 400,  "tech": 5,  "epm": 2, "max_eng": 12},
    {"abbr": "BC", "name": "Battle Cruiser","size": 40, "cost": 500,  "tech": 6,  "epm": 2, "max_eng": 12},
    {"abbr": "BB", "name": "Battleship",   "size": 50,  "cost": 700,  "tech": 7,  "epm": 3, "max_eng": 15},
    {"abbr": "DN", "name": "Dreadnought",  "size": 65,  "cost": 1000, "tech": 10, "epm": 5, "max_eng": 20},
    {"abbr": "LX", "name": "Light Carrier","size": 25,  "cost": 300,  "tech": 12, "epm": 1, "max_eng": 6},
    {"abbr": "CX", "name": "Carrier",      "size": 45,  "cost": 500,  "tech": 13, "epm": 2, "max_eng": 12},
    {"abbr": "HX", "name": "Heavy Carrier","size": 75,  "cost": 700,  "tech": 14, "epm": 3, "max_eng": 15},
    {"abbr": "SS", "name": "Space Station","size": 35,  "cost": 200,  "tech": 1,  "epm": 0, "max_eng": 0},
    {"abbr": "BS", "name": "Battle Station","size": 75, "cost": 400,  "tech": 5,  "epm": 0, "max_eng": 0},
    {"abbr": "SB", "name": "Starbase",     "size": 200, "cost": 2000, "tech": 8,  "epm": 0, "max_eng": 0},
]

CLASS_TYPES = {
    "ATK": "Attack",
    "DEF": "Defense",
    "SYD": "Space Yard",
    "COL": "Colonizer",
    "CRG": "Cargo",
}

SHIP_NAME_FILES = ["Myth", "Animals", "Misc", "States"]
