"""Text-based runner for Space Empires"""
import sys
from space_empires.models import GameState, ShipType, ColonyType, PlanetType
from space_empires.universe import (
    create_universe, get_sector_description, get_planet_at_sector,
    is_planet, is_warp_point, distance, star_index,
    SYSTEM_WIDTH, SYSTEM_HEIGHT
)
from space_empires.game_logic import (
    next_player, calculate_money, do_repair, grow_population, 
    check_victory, player_lives, create_ship, get_ship_class,
    get_ships_in_system, get_ships_in_sector, colonize_planet,
    close_warp_point, move_ship, explore_system, can_see_system,
    get_visible_systems
)
from space_empires.ai import computer_turn


def print_header(text):
    print(f"\n{'='*50}")
    print(f" {text}")
    print(f"{'='*50}")


def print_system_map(state, system_idx):
    """Print a text representation of the system map"""
    system = state.systems[system_idx]
    if not system:
        return
    
    print(f"\n=== {system.name} (System {system_idx}) ===")
    print(f"  Position: ({system.draw_x}, {system.draw_y})  Warps: {system.warp_count}")
    
    # Legend
    print("  Legend: . = empty  o = planet  * = star  ~ = warp  # = nebula  @ = machine")
    
    for row in range(SYSTEM_HEIGHT):
        line = f"  {row} "
        for col in range(SYSTEM_WIDTH):
            sector = row * SYSTEM_WIDTH + col
            obj_idx = system.get_sector_object(sector)
            stellar = state.stellar_objects[obj_idx] if obj_idx < len(state.stellar_objects) else None
            
            if not stellar:
                ch = '.'
            elif stellar.type == 1:  # Planet
                planet = get_planet_at_sector(state, system_idx, sector)
                if planet and planet.owner > 0:
                    ch = str(planet.owner)
                else:
                    ch = 'o'
            elif stellar.type == 2:  # Gas giant
                ch = 'o'
            elif stellar.type == 3:  # Nebula/storm
                ch = '#'
            elif stellar.type == 4:  # Star
                ch = '*'
            elif stellar.type == 5:  # Warp
                ch = '~'
            elif stellar.type == 6:  # Empty
                ch = '.'
            elif stellar.type == 8:  # Machine
                ch = '@'
            else:
                ch = '?'
            
            # Show ships
            ships = get_ships_in_sector(state, system_idx, sector, state.current_player)
            if ships:
                ch = '+'
            else:
                for p_id in range(1, len(state.players)):
                    if p_id != state.current_player:
                        e_ships = get_ships_in_sector(state, system_idx, sector, p_id)
                        if e_ships:
                            ch = 'x'
                            break
            
            line += ch + ' '
        print(line)


def print_galaxy_map(state, player_id):
    """Print galaxy map with visible systems"""
    print(f"\n=== Galaxy Map (Player {player_id}) ===")
    visible = get_visible_systems(state, player_id)
    
    for sys in state.systems[1:]:
        if not sys:
            continue
        marker = "> " if sys.system_index == state.active_system else "  "
        if sys.system_index in visible:
            ships_here = any(s.system == sys.system_index and s.owner == player_id for s in state.ships)
            ship_marker = " [YOUR SHIPS]" if ships_here else ""
            print(f"  {marker}{sys.system_index:3d}: {sys.name:20s} ({sys.draw_x:2d},{sys.draw_y:2d}){ship_marker}")
        else:
            print(f"  {marker}{sys.system_index:3d}: {'UNEXPLORED':20s}")


def print_status(state, player_id):
    """Print player status"""
    player = state.players[player_id]
    if not player:
        return
    
    # Count systems, ships
    systems = sum(1 for p in state.planets[1:] if p and p.owner == player_id and p.colony_type > 0)
    ships = sum(1 for s in state.ships if s.owner == player_id and s.owner > 0)
    
    print(f"\n=== {player.name} Empire ===")
    print(f"  Money: {player.money:,}  |  Tech Level: {player.tech_level}")
    print(f"  Systems: {systems}  |  Ships: {ships}")
    print(f"  Home: {state.systems[player.home_system].name if player.home_system > 0 else 'Unknown'}")


def get_sector_info(state, system_idx, sector):
    """Get detailed sector info"""
    return get_sector_description(state, system_idx, sector, True)


def handle_command(state, cmd, player_id):
    """Handle player command"""
    parts = cmd.strip().split()
    if not parts:
        return True
    
    cmd = parts[0].lower()
    
    if cmd == 'q' or cmd == 'quit':
        return False
    
    elif cmd == 's' and len(parts) > 1:
        # Select system
        try:
            sys_idx = int(parts[1])
            if 1 <= sys_idx < len(state.systems) and state.systems[sys_idx]:
                if can_see_system(state, sys_idx, player_id) or any(s.system == sys_idx and s.owner == player_id for s in state.ships):
                    state.active_system = sys_idx
                    state.selected_sector = 9999
                    print(f"Selected system: {state.systems[sys_idx].name}")
                else:
                    print("You cannot see that system!")
            else:
                print("Invalid system number!")
        except ValueError:
            print("Usage: s <system_number>")
    
    elif cmd == 'm' and len(parts) > 1:
        # Move ship in system
        if state.active_system <= 0:
            print("No system selected!")
        else:
            try:
                sector = int(parts[1])
                if 0 <= sector < SYSTEM_WIDTH * SYSTEM_HEIGHT:
                    # Find player's ships in current sector
                    ships = get_ships_in_sector(state, state.active_system, state.selected_sector if state.selected_sector != 9999 else star_index(), player_id)
                    if ships:
                        ship = ships[0]
                        if move_ship(state, ship.ship_id, state.active_system, sector):
                            state.selected_sector = sector
                            print(f"Moved {ship.name} to sector {sector}")
                        else:
                            print("Cannot move there (no movement points or invalid destination)")
                    else:
                        print("No ships in current sector!")
                else:
                    print("Invalid sector!")
            except ValueError:
                print("Usage: m <sector>")
    
    elif cmd == 'w' and len(parts) > 1:
        # Warp to connected system
        if state.active_system <= 0 or state.selected_sector == 9999:
            print("Select a system and warp point sector first!")
        else:
            try:
                target_sys = int(parts[1])
                system = state.systems[state.active_system]
                # Check if current sector has warp to target
                warp_idx = -1
                for i in range(1, system.warp_count + 1):
                    if system.warp_sector[i] == state.selected_sector and system.warp_dest[i] == target_sys:
                        warp_idx = i
                        break
                
                if warp_idx > 0:
                    # Move all player ships in this sector
                    ships = get_ships_in_sector(state, state.active_system, state.selected_sector, player_id)
                    for ship in ships:
                        ship.system = target_sys
                        dest_sys = state.systems[target_sys]
                        # Find matching warp sector
                        for j in range(1, dest_sys.warp_count + 1):
                            if dest_sys.warp_dest[j] == state.active_system:
                                ship.sector = dest_sys.warp_sector[j]
                                break
                        else:
                            ship.sector = star_index()
                        ship.speed -= 1
                    
                    state.active_system = target_sys
                    state.selected_sector = star_index()
                    print(f"Warped to {state.systems[target_sys].name}!")
                else:
                    print("No warp connection to that system from this sector!")
            except ValueError:
                print("Usage: w <system>")
    
    elif cmd == 'c' and len(parts) > 1:
        # Colonize
        if state.active_system <= 0 or state.selected_sector == 9999:
            print("Select a system and planet sector first!")
        else:
            try:
                sector = int(parts[1])
                ships = get_ships_in_sector(state, state.active_system, sector, player_id)
                colony_ships = []
                for ship in ships:
                    sc = get_ship_class(ship.class_id)
                    if sc and sc.ship_type == ShipType.COLONIZE:
                        colony_ships.append(ship.ship_id)
                
                if not colony_ships:
                    print("No colony ships in that sector!")
                else:
                    if colonize_planet(state, player_id, state.active_system, sector, colony_ships):
                        print("Planet colonized successfully!")
                    else:
                        print("Colonization failed!")
            except ValueError:
                print("Usage: c <sector>")
    
    elif cmd == 'b':
        # Build ship
        if state.active_system <= 0:
            print("Select a system first!")
        else:
            # Find colonies with shipyards
            colonies = []
            for planet in state.planets[1:]:
                if planet and planet.system == state.active_system and planet.owner == player_id and planet.colony_type > 0:
                    # Check for shipyard
                    has_yard = False
                    for ship in state.ships:
                        if ship.system == planet.system and ship.sector == planet.sector and ship.owner == player_id:
                            sc = get_ship_class(ship.class_id)
                            if sc and 'Sy' in sc.functions:
                                has_yard = True
                                break
                    if has_yard:
                        colonies.append(planet)
            
            if not colonies:
                print("No colonies with shipyards in this system!")
            else:
                print("Colonies with shipyards:")
                for i, p in enumerate(colonies):
                    print(f"  {i}: {p.name} (Sector {p.sector})")
                
                try:
                    choice = int(input("Select colony: "))
                    if 0 <= choice < len(colonies):
                        colony = colonies[choice]
                        # Show available ship classes
                        player_classes = [sc for sc in state.ship_classes if sc.owner == player_id]
                        if not player_classes:
                            print("No ship designs available!")
                        else:
                            print("Available designs:")
                            for i, sc in enumerate(player_classes):
                                print(f"  {i}: {sc.name} - Cost: {sc.cost}, Speed: {sc.speed}")
                            cls_choice = int(input("Select design: "))
                            if 0 <= cls_choice < len(player_classes):
                                sc = player_classes[cls_choice]
                                player = state.players[player_id]
                                if player.money >= sc.cost:
                                    create_ship(state, player_id, sc.class_index, colony.system, colony.sector)
                                    player.money -= sc.cost
                                    print(f"Built {sc.name}!")
                                else:
                                    print("Not enough money!")
                    else:
                        print("Invalid selection!")
                except (ValueError, IndexError):
                    print("Invalid input!")
    
    elif cmd == 'i':
        # Info on selected sector
        if state.active_system > 0 and state.selected_sector != 9999:
            info = get_sector_info(state, state.active_system, state.selected_sector)
            print(info)
        elif state.active_system > 0:
            system = state.systems[state.active_system]
            print(f"\nSystem: {system.name}")
            print(f"Position: ({system.draw_x}, {system.draw_y})")
            print(f"Warp Points: {system.warp_count}")
            for i in range(1, system.warp_count + 1):
                dest = state.systems[system.warp_dest[i]]
                if dest:
                    print(f"  Warp {i}: Sector {system.warp_sector[i]} -> {dest.name}")
        else:
            print("No system selected!")
    
    elif cmd == 'n':
        # Next turn
        return 'next_turn'
    
    elif cmd == 'h' or cmd == 'help':
        print("""
Commands:
  s <num>      - Select system
  m <sector>   - Move selected ship to sector (in same system)
  w <num>      - Warp to connected system (from warp point sector)
  c <sector>   - Colonize planet (with colony ship in sector)
  b            - Build ship at colony with shipyard
  i            - Show info on selected sector/system
  n            - Next turn
  q            - Quit
  h            - This help
        """)
    
    else:
        print("Unknown command. Type 'h' for help.")
    
    return True


def text_main():
    """Main text-mode game loop"""
    print_header("SPACE EMPIRES - Text Mode")
    print("A 4X space strategy game inspired by the classic VB6 version")
    
    # Initialize game
    state = GameState()
    state.galaxy_size = 30
    state.num_players = 4
    state.max_players = 20
    
    print("\nGenerating universe...")
    create_universe(state)
    print(f"Universe created: {len(state.systems)-1} systems, {len(state.planets)-1} planets")
    print(f"Players: 1 Human + {state.num_players-1} AI")
    
    # Game loop
    while True:
        player_id = state.current_player
        player = state.players[player_id]
        
        if player.is_computer:
            # AI turn
            print(f"\n--- Turn {state.turn_number}: {player.name} (AI) ---")
            computer_turn(state, player_id)
            
            # Check victory
            winner = check_victory(state)
            if winner:
                winner_name = state.players[winner].name if winner < len(state.players) else "Unknown"
                print_header(f"GAME OVER - {winner_name} WINS!")
                break
                
            state.current_player = next_player(state)
            continue
        
        # Human turn
        print_header(f"TURN {state.turn_number} - {player.name}")
        
        # Start of turn processing
        do_repair(state, player_id)
        player.money += calculate_money(state, player_id)
        grow_population(state, player_id)
        if state.active_system > 0:
            explore_system(state, state.active_system, player_id)
        
        print_status(state, player_id)
        print_galaxy_map(state, player_id)
        
        if state.active_system > 0:
            print_system_map(state, state.active_system)
            if state.selected_sector != 9999:
                info = get_sector_info(state, state.active_system, state.selected_sector)
                print(f"\nSector {state.selected_sector}: {info.split(chr(10))[0]}")
        
        print("\nCommands: s=select system, m=move, w=warp, c=colonize, b=build, i=info, n=next turn, q=quit, h=help")
        
        while True:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue
                
                result = handle_command(state, cmd, player_id)
                if result == False:
                    print("Thanks for playing!")
                    return
                elif result == 'next_turn':
                    break
                    
            except KeyboardInterrupt:
                print("\nUse 'q' to quit")
            except EOFError:
                print("\nGoodbye!")
                return
        
        # Check victory
        winner = check_victory(state)
        if winner:
            winner_name = state.players[winner].name if winner < len(state.players) else "Unknown"
            print_header(f"GAME OVER - {winner_name} WINS!")
            break
        
        # Move to next player
        state.current_player = next_player(state)


if __name__ == "__main__":
    text_main()