from entities import Component
from config import MAX_COMPONENTS

ALL_COMPONENTS: list[Component] = []


def init_components():
    ALL_COMPONENTS.clear()
    ALL_COMPONENTS.extend([
        Component(0, "Armor", "H", 1, 1, 1),
        Component(1, "Ion Engine", "E", 2, 10, 1),
        Component(2, "Cargo Hold", "C", 2, 5, 1),
        Component(3, "Space Yard 1", "Y", 3, 50, 1, comp_type=1),
        Component(4, "Space Yard 2", "Y", 4, 80, 5, comp_type=2),
        Component(5, "Space Yard 3", "Y", 5, 120, 10, comp_type=3),
        Component(6, "Fighter Bay 1", "V", 3, 30, 3, comp_type=6),
        Component(7, "Fighter Bay 2", "V", 4, 50, 7, comp_type=12),
        Component(8, "Fighter Bay 3", "V", 5, 80, 11, comp_type=18),
        Component(9, "Cloaking Device", "K", 3, 60, 6),
        Component(10, "Combat Sensors 1", "S", 1, 10, 2),
        Component(11, "Combat Sensors 2", "S", 1, 25, 5),
        Component(12, "Combat Sensors 3", "S", 1, 50, 9),
        Component(13, "ECM 1", "X", 1, 10, 3),
        Component(14, "ECM 2", "X", 1, 25, 6),
        Component(15, "ECM 3", "X", 1, 50, 10),
        Component(16, "Multiplex Tracking 2", "T", 1, 25, 2),
        Component(17, "Multiplex Tracking 3", "T", 1, 50, 3),
        Component(18, "Multiplex Tracking 4", "T", 1, 75, 4),
        Component(19, "Multiplex Tracking 5", "T", 1, 100, 5),
        Component(20, "Multiplex Tracking 6", "T", 1, 150, 6),
        Component(21, "Multiplex Tracking 7", "T", 1, 200, 7),
        Component(22, "Multiplex Tracking 8", "T", 1, 250, 8),
        Component(23, "Multiplex Tracking 9", "T", 1, 300, 9),
        Component(24, "Open Warp Point", "O", 2, 40, 5),
        Component(25, "Close Warp Point", "L", 2, 20, 5),
        Component(26, "Outpost Module", "M", 3, 20, 2),
        Component(27, "Colony Module", "M", 5, 50, 5),
        Component(28, "Settlement Module", "M", 10, 150, 10),
        Component(29, "Sun Destroyer", "D", 10, 500, 10),
        Component(30, "Disrupter 1", "W", 2, 15, 2, 20, 3, 6, 1),
        Component(31, "Disrupter 2", "W", 2, 25, 4, 28, 4, 6, 1),
        Component(32, "Disrupter 3", "W", 2, 40, 7, 38, 5, 6, 1),
        Component(33, "Wave-Motion Gun", "W", 5, 200, 10, 80, 8, 6, 1),
        Component(34, "Capital Ship Missile 1", "W", 3, 30, 3, 35, 8, 3, 1, 2, 2),
        Component(35, "Capital Ship Missile 2", "W", 3, 55, 6, 50, 10, 3, 1, 3, 2),
        Component(36, "Capital Ship Missile 3", "W", 3, 90, 9, 65, 12, 3, 1, 4, 2),
        Component(37, "Ripper Beam 1", "W", 2, 20, 2, 18, 2, 8, 1),
        Component(38, "Ripper Beam 2", "W", 2, 35, 5, 26, 3, 8, 1),
        Component(39, "Ripper Beam 3", "W", 2, 55, 8, 36, 4, 8, 1),
        Component(40, "Mass Driver 1", "W", 2, 15, 3, 16, 2, 5, 2, 1, 2),
        Component(41, "Mass Driver 2", "W", 2, 30, 6, 24, 3, 5, 2, 2, 2),
        Component(42, "Mass Driver 3", "W", 2, 50, 9, 32, 4, 5, 2, 3, 2),
        Component(43, "Mauler Beam", "W", 4, 100, 9, 50, 5, 5, 1),
        Component(44, "Phaser 1", "W", 1, 10, 1, 10, 1, 1, 1),
        Component(45, "Phaser 2", "W", 1, 15, 2, 14, 2, 2, 1),
        Component(46, "Phaser 3", "W", 1, 20, 3, 18, 3, 2, 1),
        Component(47, "Phaser 4", "W", 1, 28, 4, 22, 3, 3, 1),
        Component(48, "Phaser 5", "W", 1, 35, 5, 26, 4, 3, 1),
        Component(49, "Phaser 6", "W", 1, 45, 6, 30, 4, 4, 1),
        Component(50, "Phaser 7", "W", 1, 55, 7, 35, 5, 4, 1),
        Component(51, "Phaser 8", "W", 1, 70, 8, 40, 5, 5, 1),
        Component(52, "Phaser 9", "W", 1, 90, 9, 45, 6, 5, 1),
        Component(53, "Point-Defense 1", "W", 1, 15, 2, 8, 1, 1, 1),
        Component(54, "Point-Defense 2", "W", 1, 25, 3, 12, 1, 1, 1),
        Component(55, "Point-Defense 3", "W", 1, 40, 5, 16, 1, 1, 1),
        Component(56, "Point-Defense 4", "W", 1, 60, 7, 20, 1, 1, 1),
        Component(57, "Point-Defense 5", "W", 1, 90, 9, 25, 1, 1, 1),
        Component(58, "Psionic Blast 1", "W", 1, 20, 3, 15, 2, 3, 1),
        Component(59, "Psionic Blast 2", "W", 1, 35, 5, 22, 3, 3, 1),
        Component(60, "Psionic Blast 3", "W", 1, 50, 7, 28, 4, 3, 1),
        Component(61, "Psionic Blast 4", "W", 1, 70, 9, 35, 5, 3, 1),
        Component(62, "Psionic Blast 5", "W", 1, 100, 11, 45, 6, 3, 1),
    ])

    for i, c in enumerate(ALL_COMPONENTS):
        c.index = i


def get_compo(index: int) -> Component:
    if 0 <= index < len(ALL_COMPONENTS):
        return ALL_COMPONENTS[index]
    return Component(index, "Unknown", "?", 0, 0, 0)


def get_components_for_tech(tech: int, avail: list) -> list:
    return [c for c in ALL_COMPONENTS if c.tech <= tech and avail[c.index]]


def get_weapons(ship_compos: list) -> list:
    return [c for c in ship_compos if c.category == "W"]


def count_engines(ship_compos: list) -> int:
    return sum(1 for c in ship_compos if c.category == "E")


def count_space_yards(ship_compos: list) -> int:
    return sum(c.comp_type for c in ship_compos if c.category == "Y")


def count_fighter_bays(ship_compos: list) -> int:
    return sum(1 for c in ship_compos if c.category == "V")


def get_fighter_capacity(ship_compos: list) -> int:
    return sum(c.comp_type for c in ship_compos if c.category == "V")


def has_colony_module(ship_compos: list) -> bool:
    return any(c.category == "M" for c in ship_compos)


def has_sensors(ship_compos: list) -> bool:
    return any(c.category == "S" for c in ship_compos)


def has_ecm(ship_compos: list) -> bool:
    return any(c.category == "X" for c in ship_compos)


def has_cloak(ship_compos: list) -> bool:
    return any(c.category == "K" for c in ship_compos)
