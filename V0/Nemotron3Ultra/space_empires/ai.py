"""AI for computer players"""
import random
from typing import List, Dict, Optional, Tuple
from space_empires.models import (
    GameState, Player, Ship, ShipClass, Planet, PlanetType, ColonyType,
    ShipType, Component, get_hull, get_component, COMPONENT_DEFINITIONS,
    HULL_DEFINITIONS
)
from space_empires.universe import (
    get_planet_at_sector, is_planet, is_warp_point, is_empty_space,
    is_cloaking, is_machine, distance, star_index, SYSTEM_WIDTH, SYSTEM_HEIGHT
)
from space_empires.game_logic import (
    player_lives, calculate_money, create_ship, get_ship_class,
    colonize_planet, move_ship, explore_system, can_see_system
)


def computer_turn(state: GameState, player_id: int):
    """Execute AI turn for a computer player"""
    player = state.players[player_id]
    if not player or not player.is_computer:
        return
    
    # Update money
    player.money += calculate_money(state, player_id)
    
    # Build ships at colonies with shipyards
    build_ships(state, player_id)
    
    # Move ships
    move_ships_ai(state, player_id)
    
    # Colonize planets
    colonize_ai(state, player_id)
    
    # Research (simplified - just increase tech occasionally)
    if random.random() < 0.1 and player.tech_level < 25:
        player.tech_level += 1
        update_available_components(state, player_id, player.tech_level)
    
    # Handle combat
    handle_combat_ai(state, player_id)
    
    # Repair ships
    repair_ships(state, player_id)


def build_ships(state: GameState, player_id: int):
    """Build ships at shipyards"""
    player = state.players[player_id]
    
    for planet in state.planets[1:]:
        if not planet or planet.owner != player_id or planet.colony_type == ColonyType.NONE:
            continue
            
        # Check for shipyard
        has_shipyard = False
        yard_level = 0
        for ship in state.ships:
            if ship.system == planet.system and ship.sector == planet.sector and ship.owner == player_id:
                ship_class = get_ship_class(state, ship.class_id)
                if ship_class and 'Sy' in ship_class.functions:
                    has_shipyard = True
                    # Determine yard level
                    for i in range(0, len(ship_class.functions), 3):
                        comp = ship_class.functions[i:i+3]
                        if comp.startswith('Sy'):
                            yard_level = max(yard_level, int(comp[2:]) if comp[2:].isdigit() else 1)
        
        if not has_shipyard:
            continue
            
        # Decide what to build
        if player.money < 100:
            continue
            
        # Simple build logic - build escorts/frigates early, cruisers later
        hull_choices = []
        if player.tech_level >= 1:
            hull_choices.append(1)  # Escort
        if player.tech_level >= 2:
            hull_choices.append(2)  # Frigate
        if player.tech_level >= 3:
            hull_choices.append(3)  # Destroyer
        if player.tech_level >= 4:
            hull_choices.append(4)  # Light Cruiser
        if player.tech_level >= 5:
            hull_choices.append(5)  # Cruiser
            
        if not hull_choices:
            continue
            
        # Weight by tech level and money
        hull = random.choice(hull_choices)
        hull_def = get_hull(hull)
        if not hull_def or hull_def.cost > player.money:
            continue
            
        # Design ship
        ship_class = design_ship(state, player_id, hull, yard_level)
        if not ship_class:
            continue
            
        # Build it
        create_ship(state, player_id, ship_class.class_index, planet.system, planet.sector)
        player.money -= hull_def.cost


def design_ship(state: GameState, player_id: int, hull_id: int, yard_level: int) -> Optional[ShipClass]:
    """Design a ship class for AI"""
    player = state.players[player_id]
    hull = get_hull(hull_id)
    if not hull:
        return None
    
    # Available components for this tech level
    available = [abbrev for abbrev, comp in COMPONENT_DEFINITIONS.items() 
                 if comp.tech_level <= player.tech_level]
    
    # Must have engine
    engines = [a for a in available if get_component(a) and get_component(a).comp_type == 'E']
    if not engines:
        return None
    
    engine = max(engines, key=lambda a: get_component(a).tech_level)
    engine_comp = get_component(engine)
    num_engines = min(hull.max_engines, max(1, hull.size // 5))
    
    # Add weapons
    weapons = [a for a in available if get_component(a) and get_component(a).comp_type in ('W', 'P', 'M', 'V')]
    weapon = random.choice(weapons) if weapons else None
    num_weapons = min(3, hull.size // 10)
    
    # Add shields/armor
    defense = [a for a in available if get_component(a) and get_component(a).comp_type in ('A', 'B')]
    shield = random.choice(defense) if defense else None
    num_shields = min(2, hull.size // 15)
    
    # Build component string
    compo_parts = ["Hul"]
    compo_parts.extend([engine] * num_engines)
    
    if weapon:
        compo_parts.extend([weapon] * num_weapons)
    if shield:
        compo_parts.extend([shield] * num_shields)
        
    # Fill remaining space with armor
    remaining_space = hull.size - len(compo_parts)
    armor = next((a for a in available if get_component(a) and get_component(a).comp_type == 'A'), None)
    if armor and remaining_space > 0:
        compo_parts.extend([armor] * min(remaining_space, 3))
    
    compo_set = ''.join(compo_parts)
    
    # Calculate stats
    speed = num_engines // hull.engines_per_move
    shields = num_shields * (get_component(shield).damage if shield else 0)
    cost = hull.cost + num_engines * engine_comp.cost
    if weapon:
        cost += num_weapons * get_component(weapon).cost
    if shield:
        cost += num_shields * get_component(shield).cost
    
    ship_class = ShipClass(
        class_index=state.next_class_id,
        owner=player_id,
        name=f"AI_{hull.name}_{state.next_class_id:03d}",
        hull_size=hull_id,
        ship_type=ShipType.ATTACK,
        speed=speed,
        cost=cost,
        functions=''.join([c for c in compo_parts if get_component(c) and get_component(c).comp_type in ('E', 'W', 'P', 'M', 'V')]),
        compo_set=compo_set,
        shields=shields,
        tech_level=player.tech_level
    )
    
    state.ship_classes.append(ship_class)
    state.next_class_id += 1
    return ship_class


def move_ships_ai(state: GameState, player_id: int):
    """Move ships strategically"""
    player = state.players[player_id]
    if not player:
        return
        
    my_ships = [s for s in state.ships if s.owner == player_id and s.owner > 0]
    
    for ship in my_ships:
        if ship.speed <= 0:
            continue
            
        ship_class = get_ship_class(state, ship.class_id)
        if not ship_class:
            continue
            
        # Determine mission based on ship type
        mission = ship_class.ship_type
        
        if mission == ShipType.COLONIZE:
            move_colonizer(state, ship, player_id)
        elif mission == ShipType.ATTACK:
            move_attacker(state, ship, player_id)
        elif mission == ShipType.DEFEND:
            move_defender(state, ship, player_id)
        else:
            move_explorer(state, ship, player_id)


def move_colonizer(state: GameState, ship: Ship, player_id: int):
    """Move colonizer to uncolonized planet"""
    # Find nearest colonizable planet
    best_dist = 999
    best_target = None
    
    for planet in state.planets[1:]:
        if not planet or planet.owner != 0 or planet.colony_type != ColonyType.NONE:
            continue
        if not is_planet(state, planet.system, planet.sector):
            continue
            
        dist = distance(
            state.systems[ship.system].draw_x, state.systems[ship.system].draw_y,
            state.systems[planet.system].draw_x, state.systems[planet.system].draw_y
        )
        if dist < best_dist:
            best_dist = dist
            best_target = planet
    
    if best_target:
        # Move toward target system
        move_toward_system(state, ship, best_target.system)


def move_attacker(state: GameState, ship: Ship, player_id: int):
    """Move attack ship toward enemy"""
    # Find enemy systems
    enemy_systems = []
    for sys in state.systems[1:]:
        if not sys:
            continue
        # Check if enemy has ships or colonies there
        has_enemy = False
        for s in state.ships:
            if s.system == sys.system_index and s.owner != player_id and s.owner > 0:
                has_enemy = True
                break
        if not has_enemy:
            for p in state.planets[1:]:
                if p and p.system == sys.system_index and p.owner != player_id and p.owner > 0:
                    has_enemy = True
                    break
        if has_enemy:
            enemy_systems.append(sys)
    
    if enemy_systems:
        target = min(enemy_systems, key=lambda s: distance(
            state.systems[ship.system].draw_x, state.systems[ship.system].draw_y,
            s.draw_x, s.draw_y
        ))
        move_toward_system(state, ship, target.system_index)


def move_defender(state: GameState, ship: Ship, player_id: int):
    """Move defender to protect colonies"""
    # Find own colonies that need protection
    for planet in state.planets[1:]:
        if planet and planet.owner == player_id and planet.colony_type > 0:
            # Check for nearby enemies
            for other_ship in state.ships:
                if other_ship.system == planet.system and other_ship.owner != player_id and other_ship.owner > 0:
                    move_toward_system(state, ship, planet.system)
                    return
    # Patrol home system
    if ship.system != player.home_system:
        move_toward_system(state, ship, player.home_system)


def move_explorer(state: GameState, ship: Ship, player_id: int):
    """Move explorer to unexplored systems"""
    unexplored = []
    for sys in state.systems[1:]:
        if not can_see_system(state, sys.system_index, player_id):
            unexplored.append(sys)
    
    if unexplored:
        target = min(unexplored, key=lambda s: distance(
            state.systems[ship.system].draw_x, state.systems[ship.system].draw_y,
            s.draw_x, s.draw_y
        ))
        move_toward_system(state, ship, target.system_index)


def move_toward_system(state: GameState, ship: Ship, target_system: int):
    """Move ship one step toward target system"""
    if ship.system == target_system:
        return
        
    # Find warp path (simplified - just jump if connected)
    current_sys = state.systems[ship.system]
    
    # Check for direct warp
    for i in range(1, current_sys.warp_count + 1):
        if current_sys.warp_dest[i] == target_system:
            # Move to warp point
            warp_sector = current_sys.warp_sector[i]
            if ship.sector != warp_sector:
                move_ship_in_system(state, ship, warp_sector)
            else:
                # Use warp
                ship.system = target_system
                dest_sys = state.systems[target_system]
                # Find matching warp sector
                for j in range(1, dest_sys.warp_count + 1):
                    if dest_sys.warp_dest[j] == ship.system:
                        ship.sector = dest_sys.warp_sector[j]
                        break
                else:
                    ship.sector = star_index()
            ship.speed -= 1
            return
    
    # No direct warp - move toward nearest warp leading closer
    # Simplified: just pick a random warp
    if current_sys.warp_count > 0:
        warp_idx = random.randint(1, current_sys.warp_count)
        warp_sector = current_sys.warp_sector[warp_idx]
        move_ship_in_system(state, ship, warp_sector)


def move_ship_in_system(state: GameState, ship: Ship, target_sector: int):
    """Move ship within a system (simplified)"""
    if ship.sector == target_sector:
        return
    # Just teleport for AI
    ship.sector = target_sector
    ship.speed -= 1


def colonize_ai(state: GameState, player_id: int):
    """AI colonization logic"""
    player = state.players[player_id]
    if not player:
        return
        
    for ship in state.ships:
        if ship.owner != player_id or ship.owner <= 0:
            continue
        ship_class = get_ship_class(state, ship.class_id)
        if not ship_class or ship_class.ship_type != ShipType.COLONIZE:
            continue
            
        # Check if on colonizable planet
        planet = get_planet_at_sector(state, ship.system, ship.sector)
        if planet and planet.owner == 0 and planet.colony_type == ColonyType.NONE:
            if is_planet(state, ship.system, ship.sector) or is_machine(state, ship.system, ship.sector):
                # Attempt colonization
                colonize_planet(state, ship.system, ship.sector, player_id, [ship.ship_id])


def handle_combat_ai(state: GameState, player_id: int):
    """Handle combat for AI"""
    # Check for enemy ships in same sector
    for ship in state.ships:
        if ship.owner != player_id or ship.owner <= 0:
            continue
            
        # Check for enemies in same sector
        for enemy in state.ships:
            if enemy.owner != player_id and enemy.owner > 0 and enemy.system == ship.system and enemy.sector == ship.sector:
                # Initiate combat
                from space_empires.combat import setup_combat
                setup_combat(state, ship.system, ship.sector, player_id, enemy.owner)
                return  # One combat per turn for simplicity


def repair_ships(state: GameState, player_id: int):
    """Repair damaged ships (simplified)"""
    # This is handled in game_logic.do_repair
    pass


def update_available_components(state: GameState, player_id: int, tech_level: int):
    """Update available components for player"""
    player = state.players[player_id]
    if not player:
        return
    player.available_components = {}
    for i, (abbrev, comp) in enumerate(COMPONENT_DEFINITIONS.items(), 1):
        player.available_components[i] = (comp.tech_level <= tech_level)