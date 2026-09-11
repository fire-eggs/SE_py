import random

from entities import *
from components import *
from economy import *
from config import *


def run_computer_turn(game, player: Player):
    if not player.alive or not player.is_computer:
        return

    bonus = game.get_comp_bonus()

    # Design ships
    _ai_design_ships(game, player)

    # Purchase ships
    _ai_purchase(game, player, bonus)

    # Buy tech
    if random.random() < 0.5 * bonus:
        if buy_tech(player):
            game._update_avail_components()

    # Move ships
    _ai_move_ships(game, player)

    # Attack
    _ai_attack(game, player)


def _ai_design_ships(game, player: Player):
    existing = [c for c in game.ship_classes if c.owner == player.index]
    if len(existing) >= 5:
        return

    hull = random.choice(HULL_TYPES[:8])
    avail = [c for c in ALL_COMPONENTS if c.tech <= player.tech and player.avail_compo[c.index]]

    weapons = [c for c in avail if c.category == "W"]
    engines = [c for c in avail if c.category == "E"]
    others = [c for c in avail if c.category not in ("W", "E")]

    compos = []
    used_space = hull["size"]

    if engines:
        max_eng = min(hull["max_eng"], hull["size"] // 2)
        num_eng = min(max_eng, len(engines))
        for _ in range(num_eng):
            if engines:
                e = random.choice(engines)
                compos.append(e.index)
                used_space -= e.size

    num_weapons = random.randint(1, max(1, used_space // 3))
    for _ in range(num_weapons):
        if weapons and used_space > 0:
            w = random.choice(weapons)
            if w.size <= used_space:
                compos.append(w.index)
                used_space -= w.size

    if others and used_space > 2:
        fill = random.choice(others)
        if fill.size <= used_space:
            compos.append(fill.index)

    type_name = random.choice(["ATK", "DEF"])
    class_name = f"AI-{hull['abbr']}-{random.randint(1, 99)}"
    shields = random.randint(0, min(10, used_space))

    cls = game._create_class(player.index, hull, type_name, class_name, compos, shields)


def _ai_purchase(game, player: Player, bonus: float):
    classes = [c for c in game.ship_classes if c.owner == player.index and not c.obsolete]
    if not classes:
        return

    home_sys = player.home_system
    for cls in classes:
        cost = int(cls.cost * 0.03 * (0.5 if game.computer_difficulty == 3 else 1.0))
        if player.money >= cls.cost * 2:
            for _ in range(random.randint(1, 3)):
                ship = Ship(
                    name=f"{player.name}-{random.randint(100, 999)}",
                    ship_id=game._next_ship_id,
                    class_id=cls.class_index,
                    system=home_sys,
                    sector=40,
                    owner=player.index,
                )
                game._next_ship_id += 1
                game.ships.append(ship)
                player.money -= cls.cost


def _ai_move_ships(game, player: Player):
    ships = game.get_player_ships(player.index)
    for ship in ships:
        if random.random() < 0.3:
            continue
        sys = game.systems[ship.system]
        sector = random.randint(0, MAX_SECTORS - 1)
        ship.sector = sector

        if random.random() < 0.2 and sys.warp_dest:
            dest = random.choice(sys.warp_dest)
            ship.system = dest
            ship.sector = random.randint(0, MAX_SECTORS - 1)

        if random.random() < 0.15:
            cls = game.get_ship_class(ship.class_id)
            if cls:
                compos = [get_compo(i) for i in cls.compo_set]
                planets = game.get_planets_in_system(ship.system)
                for p in planets:
                    if p.owner == 0 and can_colonize(p, compos):
                        game.colonize_planet(ship)
                        break


def _ai_attack(game, player: Player):
    ships = game.get_player_ships(player.index)
    if not ships:
        return
    for ship in ships:
        enemies = [s for s in game.ships if s.owner != player.index and s.system == ship.system and s.sector == ship.sector]
        if enemies:
            target = random.choice(enemies)
        else:
            # Move towards enemy territory
            for other_sys in range(len(game.systems)):
                enemy_ships = [s for s in game.ships if s.owner != player.index and s.system == other_sys]
                if enemy_ships:
                    ship.system = other_sys
                    ship.sector = random.randint(0, MAX_SECTORS - 1)
                    break
