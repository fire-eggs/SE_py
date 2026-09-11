"""Tactical combat system"""
import random
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from space_empires.models import (
    GameState, CombatShip, ShipClass, ShipHull, Component,
    ShipType, get_hull, get_component, COMPONENT_DEFINITIONS,
    HULL_DEFINITIONS
)

MAP_WIDE = 11
MAP_HIGH = 13
MAX_MAP_INDEX = MAP_WIDE * MAP_HIGH  # 143


@dataclass
class WeapInfo:
    """Weapon info for combat calculations"""
    damage: int = -9999
    decrease_dmg: int = 0
    spdrge: int = 0  # speed or range depending on fire type
    fire_type: int = 1  # 1=direct, 2=seeker


def get_combat_speed(ship: CombatShip) -> int:
    """Calculate combat speed for a ship"""
    if ship.speed <= 0:
        return 0
    if ship.damage == 0:
        return ship.speed
    # Calculate based on functional engines
    # Simplified - use stored max_speed
    return min(ship.speed, ship.max_speed)


def setup_combat(state: GameState, system: int, sector: int, attacker: int, defender: int):
    """Initialize tactical combat"""
    state.in_combat = True
    state.combat_system = system
    state.combat_sector = sector
    state.combat_attacker = attacker
    state.combat_defender = defender
    state.combat_ships = []
    state.combat_fighters = []
    state.combat_missiles = []
    state.combat_stellar_type = 0
    state.combat_planet_population = 0
    
    # Get stellar object type at combat location
    sys_obj = state.systems[system]
    obj_idx = sys_obj.get_sector_object(sector)
    stellar = state.stellar_objects[obj_idx] if obj_idx < len(state.stellar_objects) else None
    state.combat_stellar_type = stellar.type if stellar else 0
    
    # Check for planet population
    if state.combat_stellar_type in (1, 2, 8):  # Planet types
        planet = get_planet_at_sector(state, system, sector)
        if planet and planet.colony_type > 0:
            state.combat_planet_population = planet.population
    
    # Collect combatants
    attacker_ships = []
    defender_ships = []
    
    for ship in state.ships:
        if ship.system == system and ship.sector == sector:
            if ship.owner == attacker:
                attacker_ships.append(ship)
            elif ship.owner == defender:
                defender_ships.append(ship)
    
    # Convert to combat ships
    for i, ship in enumerate(attacker_ships + defender_ships):
        is_attacker = i < len(attacker_ships)
        owner = attacker if is_attacker else defender
        ship_class = get_ship_class_by_id(state, ship.class_id)
        hull = get_hull(ship_class.hull_size) if ship_class else None
        
        combat_ship = CombatShip(
            ship_id=ship.ship_id,
            class_id=ship.class_id,
            owner=owner,
            name=ship.name,
            size=hull.size if hull else 1,
            speed=get_combat_speed_from_state(ship, ship_class, state),
            max_speed=get_combat_speed_from_state(ship, ship_class, state),
            damage=ship.damage,
            shields=ship_class.shields if ship_class else 0,
            hull_integrity=hull.size if hull else 10,
            map_index=0,
            functions=ship_class.compo_set if ship_class else "",
            component_damage=ship_class.compo_set if ship_class else "",
            is_fighter=False
        )
        state.combat_ships.append(combat_ship)
    
    # Place ships on map
    place_combat_ships(state)
    place_stellar_objects(state)


def get_ship_class_by_id(state: GameState, class_id: int) -> Optional[ShipClass]:
    """Find ship class by index"""
    for sc in state.ship_classes:
        if sc.class_index == class_id:
            return sc
    return None


def get_combat_speed_from_state(ship, ship_class, state):
    """Calculate combat speed from ship state"""
    if ship.damage == 0:
        return ship_class.speed if ship_class else 0
    if not ship_class or ship_class.speed == 0:
        return 0
    
    # Count functional engines
    engine_count = 0
    hull = get_hull(ship_class.hull_size)
    if not hull:
        return 0
    
    for i in range(0, len(ship_class.compo_set), 3):
        comp_abbrev = ship_class.compo_set[i:i+3]
        comp = get_component(comp_abbrev)
        if comp and comp.comp_type == 'E':
            engine_count += 1
    
    return int(engine_count / hull.engines_per_move + 0.5)


def place_combat_ships(state: GameState):
    """Place ships on combat map"""
    num_ships = len(state.combat_ships)
    if num_ships == 0:
        return
    
    # Attacker on left, defender on right
    attacker_ships = [s for s in state.combat_ships if s.owner == state.combat_attacker]
    defender_ships = [s for s in state.combat_ships if s.owner == state.combat_defender]
    
    # Place attacker ships on left side (columns 1-2)
    for i, ship in enumerate(attacker_ships):
        row = (i % MAP_HIGH) + 1
        col = 1 + (i // MAP_HIGH)
        if col > 2:
            col = 2
        ship.map_index = (row - 1) * MAP_WIDE + (col - 1)
    
    # Place defender ships on right side (columns 9-10)
    for i, ship in enumerate(defender_ships):
        row = (i % MAP_HIGH) + 1
        col = MAP_WIDE - 1 - (i // MAP_HIGH)
        if col < MAP_WIDE - 2:
            col = MAP_WIDE - 2
        ship.map_index = (row - 1) * MAP_WIDE + (col - 1)


def place_stellar_objects(state: GameState):
    """Place planets/stars on combat map"""
    state.combat_map_objects = [[-999 for _ in range(MAP_WIDE)] for _ in range(MAP_HIGH)]
    
    if state.combat_stellar_type == 2 or state.combat_stellar_type == 3:
        # Asteroids or nebulous - scatter
        for x in range(MAP_WIDE):
            for y in range(MAP_HIGH):
                if random.random() < 0.5:
                    state.combat_map_objects[y][x] = state.combat_stellar_obj_index
        if state.combat_planet_population > 0:
            cx = MAP_WIDE // 2
            cy = MAP_HIGH // 4 - 1
            state.combat_map_objects[cy][cx] = state.combat_stellar_obj_index
            state.combat_planet_map_index = cy * MAP_WIDE + cx
    elif state.combat_stellar_type == 5:
        # Warp point
        if state.combat_attacker_system != state.combat_system:
            cx = MAP_WIDE // 2
            cy = 3 * MAP_HIGH // 4 + 3
        else:
            cx = MAP_WIDE // 2
            cy = MAP_HIGH // 4 - 1
        state.combat_map_objects[cy][cx] = state.combat_stellar_obj_index
    elif state.combat_stellar_type not in (6, 0):  # Not empty
        cx = MAP_WIDE // 2
        cy = MAP_HIGH // 4 - 1
        state.combat_map_objects[cy][cx] = state.combat_stellar_obj_index
        if state.combat_planet_population > 0:
            state.combat_planet_map_index = cy * MAP_WIDE + cx


def make_weapon_list(ship: CombatShip) -> Tuple[int, List[WeapInfo]]:
    """Create weapon list for combat calculations"""
    weapons = []
    compo_set = ship.component_damage
    
    for i in range(0, len(compo_set), 3):
        comp_abbrev = compo_set[i:i+3]
        if comp_abbrev.startswith("*"):
            weapons.append(WeapInfo())
            continue
            
        comp = get_component(comp_abbrev)
        if comp and comp.comp_type in ('W', 'V'):  # Weapon or seeker
            w = WeapInfo()
            w.damage = comp.damage
            w.decrease_dmg = comp.decrease_dmg
            if comp.fire_type == 2:
                w.spdrge = comp.speed
            else:
                w.spdrge = comp.range
            w.fire_type = comp.fire_type
            weapons.append(w)
        else:
            weapons.append(WeapInfo())
    
    return len(weapons), weapons


def calculate_weapon_damage(weapcount: int, weaplist: List[WeapInfo], 
                          target_map_index: int, ship: CombatShip, 
                          owner: int, attacker: int) -> int:
    """Calculate total weapon damage a ship can deal to a target square"""
    total_damage = 0
    
    for i in range(weapcount):
        w = weaplist[i]
        if w.damage == -9999:
            continue
            
        target_ship_idx = get_target_at(state, target_map_index, owner)
        if target_ship_idx == 0:
            continue
            
        if attacker == 1:  # CombatAttacker
            ship_speed = get_combat_speed(state.combat_ships[target_ship_idx])
        else:
            ship_speed = 0
            
        dist = map_distance(ship.map_index, target_ship_idx) + ship_speed
        
        if dist < 0:
            dist = 0
        if dist > w.spdrge:
            continue
            
        damage = w.damage
        if w.decrease_dmg != 0:
            damage = int(damage - (dist * w.decrease_dmg) + 0.5)
        if damage < 0:
            damage = 0
            
        total_damage += damage
    
    return total_damage


def map_distance(idx1: int, idx2: int) -> int:
    """Calculate distance between two map indices"""
    x1 = idx1 % MAP_WIDE
    y1 = idx1 // MAP_WIDE
    x2 = idx2 % MAP_WIDE
    y2 = idx2 // MAP_WIDE
    return max(abs(x1 - x2), abs(y1 - y2))


def get_target_at(state: GameState, map_index: int, owner: int) -> int:
    """Get combat ship index at map location for given owner"""
    # Simplified - return first enemy ship at location
    for i, ship in enumerate(state.combat_ships):
        if ship.map_index == map_index and ship.owner != owner and ship.owner > 0:
            return i + 1
    return 0


def auto_move_ship(state: GameState, ship_idx: int, player: int, danger_map: List[List[int]]) -> int:
    """Auto-move a ship (AI)"""
    ship = state.combat_ships[ship_idx]
    if ship.owner != player:
        return ship.map_index
    
    # Simplified AI - move toward nearest enemy
    weapcount, weaplist = make_weapon_list(ship)
    
    if weapcount > 0 and ship.owner == state.combat_attacker:
        # Attacker with weapons - move to engage
        best_dist = 9999
        best_pos = ship.map_index
        
        for y in range(MAP_HIGH):
            for x in range(MAP_WIDE):
                idx = y * MAP_WIDE + x
                if danger_map[y][x] == 0:
                    dist = map_distance(idx, get_nearest_enemy(state, ship_idx))
                    if dist < best_dist and dist <= ship.speed:
                        best_dist = dist
                        best_pos = idx
        
        if best_pos != ship.map_index:
            ship.map_index = best_pos
            ship.speed = 0
        return best_pos
    
    return ship.map_index


def get_nearest_enemy(state: GameState, ship_idx: int) -> int:
    """Find nearest enemy ship"""
    ship = state.combat_ships[ship_idx]
    best_dist = 9999
    best_idx = ship.map_index
    
    for i, s in enumerate(state.combat_ships):
        if s.owner != ship.owner and s.owner > 0:
            dist = map_distance(ship.map_index, s.map_index)
            if dist < best_dist:
                best_dist = dist
                best_idx = s.map_index
    
    return best_idx


def resolve_combat_round(state: GameState):
    """Resolve one round of combat (missiles, fighters, ships fire)"""
    # Move missiles
    move_missiles(state)
    
    # Fighters fire
    fighter_combat(state)
    
    # Ships fire
    ship_combat(state)
    
    # Check victory
    return check_combat_end(state)


def move_missiles(state: GameState):
    """Move all missiles toward targets"""
    for missile in state.combat_missiles:
        if missile.owner <= 0 or missile.target_ship <= 0:
            continue
            
        target = state.combat_ships[missile.target_ship - 1] if missile.target_ship <= len(state.combat_ships) else None
        if not target or target.owner <= 0:
            missile.owner = -999
            continue
            
        # Move toward target
        speed = missile.speed
        while speed > 0 and missile.map_index != target.map_index:
            # Simple pathfinding
            mx = missile.map_index % MAP_WIDE
            my = missile.map_index // MAP_WIDE
            tx = target.map_index % MAP_WIDE
            ty = target.map_index // MAP_WIDE
            
            if mx < tx:
                mx += 1
            elif mx > tx:
                mx -= 1
            if my < ty:
                my += 1
            elif my > ty:
                my -= 1
                
            missile.map_index = my * MAP_WIDE + mx
            speed -= 1
            
            # Check for impact
            if missile.map_index == target.map_index:
                # Hit!
                damage_ship(state, target, missile.damage, missile.owner)
                missile.owner = -999
                break
            
            # Check for asteroid/nebula damage
            obj = state.combat_map_objects[my][mx]
            if obj > 0 and state.combat_stellar_type in (2, 3):
                missile.damage -= 2
                if missile.damage <= 0:
                    missile.owner = -999
                    break


def fighter_combat(state: GameState):
    """Resolve fighter attacks"""
    for fighter in state.combat_fighters:
        if fighter.owner <= 0 or fighter.target_ship <= 0 or fighter.speed <= 0:
            continue
            
        target = state.combat_ships[fighter.target_ship - 1] if fighter.target_ship <= len(state.combat_ships) else None
        if not target or target.owner <= 0:
            fighter.target_ship = 0
            continue
            
        dist = map_distance(fighter.map_index, target.map_index)
        if dist <= fighter.range:
            # Attack
            damage_ship(state, target, fighter.damage, fighter.owner)
            fighter.speed = 0


def ship_combat(state: GameState):
    """Resolve ship weapon fire"""
    # Determine firing order (alternating attacker/defender)
    attacker_ships = [i for i, s in enumerate(state.combat_ships) if s.owner == state.combat_attacker and s.owner > 0]
    defender_ships = [i for i, s in enumerate(state.combat_ships) if s.owner == state.combat_defender and s.owner > 0]
    
    # Reset weapon cooldowns
    for ship in state.combat_ships:
        ship.weapons_fired = {}
    
    # Fire weapons
    max_rounds = max(len(attacker_ships), len(defender_ships))
    for round_num in range(max_rounds):
        if round_num < len(attacker_ships):
            fire_ship_weapons(state, attacker_ships[round_num], state.combat_defender)
        if round_num < len(defender_ships):
            fire_ship_weapons(state, defender_ships[round_num], state.combat_attacker)


def fire_ship_weapons(state: GameState, ship_idx: int, enemy_owner: int):
    """Fire all weapons on a ship"""
    ship = state.combat_ships[ship_idx]
    weapcount, weaplist = make_weapon_list(ship)
    
    for w_idx, weapon in enumerate(weaplist):
        if weapon.damage == -9999:
            continue
            
        # Check cooldown
        cooldown = ship.weapons_fired.get(w_idx, 0)
        if cooldown > 0:
            ship.weapons_fired[w_idx] = cooldown - 1
            continue
            
        # Find target
        target_idx = find_best_target(state, ship_idx, weapon)
        if target_idx == -1:
            continue
            
        target = state.combat_ships[target_idx]
        dist = map_distance(ship.map_index, target.map_index)
        
        if dist > weapon.spdrge:
            continue
            
        # Calculate damage
        damage = weapon.damage
        if weapon.decrease_dmg != 0:
            damage = int(damage - (dist * weapon.decrease_dmg) + 0.5)
        if damage < 0:
            damage = 0
            
        # Apply damage
        damage_ship(state, target, damage, ship.owner)
        
        # Set cooldown
        rate = get_component_rate(ship, w_idx)
        ship.weapons_fired[w_idx] = rate


def find_best_target(state: GameState, ship_idx: int, weapon: WeapInfo) -> int:
    """Find best target for weapon"""
    ship = state.combat_ships[ship_idx]
    best_score = -1
    best_target = -1
    
    for i, target in enumerate(state.combat_ships):
        if target.owner != ship.owner and target.owner > 0:
            dist = map_distance(ship.map_index, target.map_index)
            if dist <= weapon.spdrge:
                # Prefer damaged targets, high value targets
                score = (target.hull_integrity - target.damage) * 10 + target.size * 5 - dist * 2
                if score > best_score:
                    best_score = score
                    best_target = i
    
    return best_target


def get_component_rate(ship: CombatShip, weapon_idx: int) -> int:
    """Get firing rate for weapon"""
    # Parse component set
    for i in range(0, len(ship.component_damage), 3):
        if i // 3 == weapon_idx:
            comp_abbrev = ship.component_damage[i:i+3]
            comp = get_component(comp_abbrev)
            if comp:
                return comp.rate
    return 1


def damage_ship(state: GameState, target: CombatShip, damage: int, attacker: int):
    """Apply damage to a ship"""
    target.damage += damage
    
    # Update component damage string
    shield_absorb = min(damage, target.shields)
    damage -= shield_absorb
    
    if target.shields > 0:
        target.shields = max(0, target.shields - shield_absorb)
    
    if damage > 0:
        # Mark components as damaged
        comp_list = list(target.component_damage)
        damaged_slots = damage * 3  # 3 chars per component
        for i in range(min(damaged_slots, len(comp_list))):
            if comp_list[i] != '*':
                comp_list[i] = '*'
        target.component_damage = ''.join(comp_list)
    
    # Check destruction
    hull = get_hull(target.size)  # This is wrong - need ship class
    max_damage = target.shields + (hull.size if hull else 10)
    if target.damage >= max_damage:
        target.owner = -999
        target.map_index = -999
        # Clear targeting
        clear_targeting(state, target, attacker)


def clear_targeting(state: GameState, destroyed_ship: CombatShip, attacker: int):
    """Clear targeting on destroyed ship"""
    for ship in state.combat_ships:
        if ship.owner == attacker:
            for w_idx in list(ship.weapons_fired.keys()):
                if ship.weapons_fired[w_idx] == destroyed_ship.ship_id:
                    ship.weapons_fired[w_idx] = 0
    
    for fighter in state.combat_fighters:
        if fighter.owner == attacker and fighter.target_ship == destroyed_ship.ship_id:
            fighter.target_ship = 0
            
    for missile in state.combat_missiles:
        if missile.owner == attacker and missile.target_ship == destroyed_ship.ship_id:
            missile.owner = -999


def check_combat_end(state: GameState) -> bool:
    """Check if combat has ended"""
    attacker_alive = any(s.owner == state.combat_attacker and s.owner > 0 for s in state.combat_ships)
    defender_alive = any(s.owner == state.combat_defender and s.owner > 0 for s in state.combat_ships)
    
    attacker_alive |= any(f.owner == state.combat_attacker and f.owner > 0 for f in state.combat_fighters)
    defender_alive |= any(f.owner == state.combat_defender and f.owner > 0 for f in state.combat_fighters)
    
    if state.combat_planet_population > 0:
        defender_alive = True
        
    if not attacker_alive and not defender_alive:
        state.combat_winner = 0
        return True
    elif not attacker_alive:
        state.combat_winner = state.combat_defender
        return True
    elif not defender_alive:
        state.combat_winner = state.combat_attacker
        return True
        
    return False


def end_combat(state: GameState):
    """Clean up after combat and apply results to strategic layer"""
    winner = state.combat_winner
    
    # Update ship damage/ownership in strategic layer
    for cship in state.combat_ships:
        sship = next((s for s in state.ships if s.ship_id == cship.ship_id), None)
        if sship:
            if cship.owner <= 0:
                sship.owner = -999
                sship.system = -999
                sship.sector = -999
            else:
                sship.damage = cship.damage
                sship.functions = cship.component_damage
                sship.speed = min(sship.speed, cship.max_speed)
    
    # Update planet
    if state.combat_stellar_type in (1, 2, 8):
        planet = get_planet_at_sector(state, state.combat_system, state.combat_sector)
        if planet:
            planet.population = state.combat_planet_population
            if planet.population <= 0:
                planet.colony_type = ColonyType.NONE
                planet.owner = 0
                planet.population = 0
    
    # Update system ownership
    if winner == state.combat_attacker:
        update_system_ownership(state, state.combat_system, state.combat_sector, winner)
    elif winner == state.combat_defender:
        update_system_ownership(state, state.combat_defender_system, state.combat_defender_sector, winner)
    
    state.in_combat = False


def update_system_ownership(state: GameState, system: int, sector: int, owner: int):
    """Update sector ownership after combat"""
    # Update all ships in sector
    for ship in state.ships:
        if ship.system == system and ship.sector == sector:
            if ship.owner > 0:
                ship.owner = owner


def get_planet_at_sector(state: GameState, system_idx: int, sector: int):
    """Get planet at sector"""
    from space_empires.universe import get_planet_at_sector
    return get_planet_at_sector(state, system_idx, sector)


# Need to import ColonyType
from space_empires.models import ColonyType