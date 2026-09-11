from entities import Player, Planet, Ship, ShipClass
from components import *
from config import *


def calculate_income(player: Player, planets: list[Planet]) -> int:
    income = 0
    for p in planets:
        if p.owner == player.index and p.colony_type > 0:
            if p.population >= 500:
                income += p.value * (p.population // 500)
    return income


def calc_maintenance(class_ref: ShipClass) -> int:
    return int(class_ref.cost * MAINTENANCE_RATE)


def total_maintenance(player: Player, ships: list[Ship], classes: list[ShipClass]) -> int:
    total = 0
    for ship in ships:
        if ship.owner == player.index:
            for cls in classes:
                if cls.class_index == ship.class_id:
                    total += calc_maintenance(cls)
                    break
    return total


def buy_tech(player: Player) -> bool:
    if player.tech >= MAX_TECH:
        return False
    cost = (player.tech + 1) * TECH_COST_MULTIPLIER
    if player.money < cost:
        return False
    player.money -= cost
    player.tech += 1
    return True


def get_tech_cost(player: Player) -> int:
    if player.tech >= MAX_TECH:
        return -1
    return (player.tech + 1) * TECH_COST_MULTIPLIER


def can_afford_ship(player: Player, class_ref: ShipClass, quantity: int = 1) -> bool:
    return player.money >= class_ref.cost * quantity


def purchase_ship(player: Player, class_ref: ShipClass, quantity: int = 1) -> bool:
    cost = class_ref.cost * quantity
    if player.money < cost:
        return False
    player.money -= cost
    return True


def can_colonize(planet: Planet, ship_compos: list) -> bool:
    if planet.colony_type > 0:
        return False
    if not (1 <= planet.type_idx <= 4):
        return False
    return has_colony_module(ship_compos)


def determine_colony_type(ship_compos: list) -> int:
    for c in ship_compos:
        if c.category == "M":
            if c.name == "Settlement Module":
                return 3
            elif c.name == "Colony Module":
                return 2
            elif c.name == "Outpost Module":
                return 1
    return 0
