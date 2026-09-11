"""Core game logic - turns, players, ships, colonies, economy"""
import random
from typing import List, Dict, Optional, Tuple
from space_empires.models import (
    GameState, Player, Ship, ShipClass, Planet, PlanetType, ColonyType,
    ShipType, Component, get_hull, get_component, COMPONENT_DEFINITIONS,
    HULL_DEFINITIONS, StellarType
)
from space_empires.universe import (
    get_planet_at_sector, is_planet, is_warp_point, is_empty_space,
    is_cloaking, is_machine, star_index, SYSTEM_WIDTH, SYSTEM_HEIGHT, MAX_SECTORS
)


def next_player(state: GameState) -> int:
    """Get next living player"""
    for _ in range(len(state.players) - 1):
        state.current_player += 1
        if state.current_player >= len(state.players):
            state.current_player = 1
            state.turn_number += 1
            do_auto_save(state)
        if player_lives(state, state.current_player):
            return state.current_player
    return 1


def player_lives(state: GameState, player_id: int) -> bool:
    """Check if player still exists"""
    if player_id >= len(state.players) or player_id <= 0:
        return False
    player = state.players[player_id]
    if not player:
        return False
    
    # Check ships
    for ship in state.ships:
        if ship.owner == player_id and ship.owner > 0:
            return True
    
    # Check colonies
    for planet in state.planets[1:]:
        if planet and planet.owner == player_id and planet.colony_type > 0:
            return True
    
    return False


def calculate_money(state: GameState, player_id: int) -> int:
    """Calculate income for player"""
    player = state.players[player_id]
    if not player:
        return 0
    
    income = 0
    for planet in state.planets[1:]:
        if planet and planet.owner == player_id and planet.colony_type > 0:
            # Base income from population
            income += planet.population // 10
            # Bonus for colony type
            income += planet.colony_type * 50
    
    # Maintenance costs
    maintenance = 0
    for ship in state.ships:
        if ship.owner == player_id and ship.owner > 0:
            ship_class = get_ship_class(state, ship.class_id)
            if ship_class:
                maintenance += ship_class.cost // 10
    
    return max(0, income - maintenance)


def get_ship_class(state: GameState, class_id: int) -> Optional[ShipClass]:
    """Get ship class by index"""
    for sc in state.ship_classes:
        if sc.class_index == class_id:
            return sc
    return None


def update_available_components(state: GameState, player_id: int, tech_level: int):
    """Update which components are available to player"""
    player = state.players[player_id]
    if not player:
        return
    player.available_components = {}
    for i, abbrev in enumerate(COMPONENT_DEFINITIONS.keys(), 1):
        comp = COMPONENT_DEFINITIONS[abbrev]
        player.available_components[i] = (comp.tech_level <= tech_level)


def do_repair(state: GameState, player_id: int):
    """Repair damaged ships"""
    player = state.players[player_id]
    if not player:
        return
    
    repair_points = 0
    # Calculate repair capacity
    for ship in state.ships:
        if ship.owner == player_id and ship.owner > 0 and ship.damage > 0:
            ship_class = get_ship_class(state, ship.class_id)
            if ship_class:
                for i in range(0, len(ship_class.compo_set), 3):
                    comp_abbrev = ship_class.compo_set[i:i+3]
                    comp = get_component(comp_abbrev)
                    if comp and comp.comp_type == 'R':  # Repair bot
                        repair_points += comp.rate * 3
    
    # Add colony repair
    for planet in state.planets[1:]:
        if planet and planet.owner == player_id and planet.colony_type == ColonyType.SETTLEMENT:
            repair_points += 3
    
    if repair_points <= 0:
        return
    
    # Repair ships in priority order
    repair_order = player.repair_order or "000"
    priorities = [int(c) for c in repair_order]
    
    damaged_ships = []
    for ship in state.ships:
        if ship.owner == player_id and ship.owner > 0 and ship.damage > 0:
            damaged_ships.append(ship)
    
    # Sort by priority
    def ship_priority(ship):
        ship_class = get_ship_class(state, ship.class_id)
        if not ship_class:
            return 999
        # Priority 0=largest, 1=smallest, 2=most damaged, 3=least damaged
        # This is simplified
        return ship.damage
    
    damaged_ships.sort(key=ship_priority)
    
    for ship in damaged_ships:
        if repair_points <= 0:
            break
        repair_amt = min(ship.damage, repair_points)
        ship.damage -= repair_amt
        repair_points -= repair_amt
        ship.functions = get_ship_functions(state, ship.ship_id)


def grow_population(state: GameState, player_id: int):
    """Grow population on owned colonies"""
    for planet in state.planets[1:]:
        if planet and planet.owner == player_id and planet.colony_type > 0:
            pop = planet.population
            if pop < 250:
                growth = random.randint(1, pop)
            elif pop < 1000:
                growth = random.randint(1, pop // 5)
            elif pop < 2000:
                growth = random.randint(1, pop // 20)
            else:
                growth = random.randint(1, 20)
            
            max_pop = planet.max_population
            if pop + growth > max_pop:
                growth = max_pop - pop
            
            planet.population += growth
            if planet.population > 1000000:
                planet.population = 1000000


def get_ship_functions(state: GameState, ship_id: int) -> str:
    """Get functional component string for ship (damaged marked with *)"""
    ship = next((s for s in state.ships if s.ship_id == ship_id), None)
    if not ship:
        return ""
    ship_class = get_ship_class(state, ship.class_id)
    if not ship_class:
        return ""
    
    compo_set = ship_class.compo_set
    damaged_slots = (ship.damage - ship_class.shields) * 3
    if damaged_slots > 0:
        compo_set = "*" * min(damaged_slots, len(compo_set)) + compo_set[damaged_slots:]
    return compo_set


def create_ship(state: GameState, owner: int, class_id: int, system: int, sector: int, name: str = "") -> Optional[Ship]:
    """Create a new ship instance"""
    ship_class = get_ship_class(state, class_id)
    if not ship_class:
        return None
    
    if not name:
        # Generate name from file
        player = state.players[owner]
        name = f"{ship_class.name} {state.next_ship_id:03d}"
    
    ship = Ship(
        ship_id=state.next_ship_id,
        name=name,
        class_id=class_id,
        system=system,
        sector=sector,
        owner=owner,
        speed=ship_class.speed,
        functions=ship_class.functions
    )
    state.ships.append(ship)
    state.next_ship_id += 1
    return ship


def scrap_ships(state: GameState, ship_ids: List[int], player_id: int) -> int:
    """Scrap ships for money"""
    total_value = 0
    for ship_id in ship_ids:
        ship = next((s for s in state.ships if s.ship_id == ship_id), None)
        if ship and ship.owner == player_id:
            ship_class = get_ship_class(state, ship.class_id)
            if ship_class:
                total_value += int(ship_class.cost * 0.2)
                ship.owner = -999
                ship.system = -999
                ship.sector = -999
    return total_value


def colonize_planet(state: GameState, player_id: int, system: int, sector: int, ship_ids: List[int]) -> bool:
    """Attempt to colonize a planet with colony ships"""
    planet = get_planet_at_sector(state, system, sector)
    if not planet or planet.colony_type > 0:
        return False
    
    best_module = 0
    pop_added = 0
    used_ships = []
    
    for ship_id in ship_ids:
        ship = next((s for s in state.ships if s.ship_id == ship_id), None)
        if not ship or ship.owner != player_id:
            continue
        
        ship_class = get_ship_class(state, ship.class_id)
        if not ship_class:
            continue
        
        for i in range(0, len(ship_class.compo_set), 3):
            comp_abbrev = ship_class.compo_set[i:i+3]
            comp = get_component(comp_abbrev)
            if comp and comp.comp_type == 'M':
                if comp_abbrev == "MOp":
                    mod_level, pop = 1, 1
                elif comp_abbrev == "MCl":
                    mod_level, pop = 2, 50
                elif comp_abbrev == "MSt":
                    mod_level, pop = 3, 200
                else:
                    continue
                
                if planet.planet_type == PlanetType.ASTEROID_BELT and mod_level == 3:
                    # Can't settle asteroids
                    continue
                
                if mod_level > best_module:
                    best_module = mod_level
                pop_added += pop
                used_ships.append(ship_id)
                break
    
    if best_module == 0:
        return False
    
    # Apply colonization
    planet.colony_type = ColonyType(best_module)
    planet.owner = player_id
    planet.population = min(pop_added, planet.max_population)
    
    # Remove used ships
    for ship_id in used_ships:
        ship = next((s for s in state.ships if s.ship_id == ship_id), None)
        if ship:
            ship.owner = -999
            ship.system = -999
            ship.sector = -999
    
    return True


def close_warp_point(state: GameState, player_id: int, system: int, sector: int) -> bool:
    """Close a warp point"""
    if not is_warp_point(state, system, sector):
        return False
    
    sys_obj = state.systems[system]
    warp_idx = -1
    for i in range(1, sys_obj.warp_count + 1):
        if sys_obj.warp_sector[i] == sector:
            warp_idx = i
            break
    
    if warp_idx == -1:
        return False
    
    dest_system_idx = sys_obj.warp_dest[warp_idx]
    dest_system = state.systems[dest_system_idx]
    
    # Find reverse warp
    rev_idx = -1
    for i in range(1, dest_system.warp_count + 1):
        if dest_system.warp_dest[i] == system:
            rev_idx = i
            break
    
    # Replace with empty space
    empty_idx = 12  # Empty space
    sys_obj.stellar_objects[sector] = empty_idx
    sys_obj.warp_sector[warp_idx] = 0
    sys_obj.warp_dest[warp_idx] = 0
    
    # Shift remaining warps down
    for i in range(warp_idx, sys_obj.warp_count):
        sys_obj.warp_sector[i] = sys_obj.warp_sector[i + 1]
        sys_obj.warp_dest[i] = sys_obj.warp_dest[i + 1]
    sys_obj.warp_sector[sys_obj.warp_count] = 9999
    sys_obj.warp_dest[sys_obj.warp_count] = 0
    sys_obj.warp_count -= 1
    
    # Same for destination
    if rev_idx != -1:
        dest_sector = dest_system.warp_sector[rev_idx]
        dest_system.stellar_objects[dest_sector] = empty_idx
        dest_system.warp_sector[rev_idx] = 0
        dest_system.warp_dest[rev_idx] = 0
        for i in range(rev_idx, dest_system.warp_count):
            dest_system.warp_sector[i] = dest_system.warp_sector[i + 1]
            dest_system.warp_dest[i] = dest_system.warp_dest[i + 1]
        dest_system.warp_sector[dest_system.warp_count] = 9999
        dest_system.warp_dest[dest_system.warp_count] = 0
        dest_system.warp_count -= 1
    
    # Stop ships in this sector
    for ship in state.ships:
        if ship.owner == player_id and ship.system == system and ship.sector == sector:
            ship.speed = 0
    
    return True


def do_auto_save(state: GameState):
    """Auto-save game (placeholder)"""
    if state.auto_save_turns > 0 and state.turn_number % state.auto_save_turns == 0:
        # TODO: Implement actual save
        pass


def check_victory(state: GameState) -> Optional[int]:
    """Check if game is won"""
    living_players = [p.player_id for p in state.players[1:] if p and player_lives(state, p.player_id)]
    human_players = [p.player_id for p in state.players[1:] if p and not p.is_computer and player_lives(state, p.player_id)]
    
    if not human_players:
        state.game_over = True
        return living_players[0] if living_players else 0
    
    if len(living_players) == 1:
        state.game_over = True
        state.winner = living_players[0]
        return living_players[0]
    
    return None


def get_ships_in_system(state: GameState, system: int, player_id: int) -> List[Ship]:
    """Get all ships of a player in a system"""
    return [s for s in state.ships if s.system == system and s.owner == player_id and s.owner > 0]


def get_ships_in_sector(state: GameState, system: int, sector: int, player_id: int) -> List[Ship]:
    """Get all ships of a player in a sector"""
    return [s for s in state.ships if s.system == system and s.sector == sector and s.owner == player_id and s.owner > 0]


def move_ship(state: GameState, ship_id: int, dest_system: int, dest_sector: int) -> bool:
    """Move a ship to a new location (strategic movement)"""
    ship = next((s for s in state.ships if s.ship_id == ship_id), None)
    if not ship or ship.speed <= 0:
        return False
    
    # Check if destination is valid (adjacent sector or warp)
    # Simplified - just move if we have movement points
    ship.system = dest_system
    ship.sector = dest_sector
    ship.speed -= 1
    return True


def can_see_system(state: GameState, system: int, player_id: int) -> bool:
    """Check if player has explored a system"""
    sys_obj = state.systems[system]
    explored = getattr(sys_obj, 'explored_by', set())
    return player_id in explored or state.surrender_condition


def explore_system(state: GameState, system: int, player_id: int):
    """Mark system as explored by player"""
    sys_obj = state.systems[system]
    if not hasattr(sys_obj, 'explored_by'):
        sys_obj.explored_by = set()
    sys_obj.explored_by.add(player_id)


def get_visible_systems(state: GameState, player_id: int) -> List[int]:
    """Get list of systems visible to player"""
    visible = []
    for i, sys_obj in enumerate(state.systems):
        if i == 0:
            continue
        if can_see_system(state, i, player_id):
            visible.append(i)
        elif get_ships_in_system(state, i, player_id):
            visible.append(i)
            explore_system(state, i, player_id)
    return visible