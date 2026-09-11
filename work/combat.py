import random
import math

from entities import *
from components import *
from config import *


class Combat:
    def __init__(self, game, attacking_ships: list[Ship], defending_ships: list[Ship]):
        self.game = game
        self.attackers: list[CombatShip] = []
        self.defenders: list[CombatShip] = []
        self.fighters: list[CombatFighter] = []
        self.phase: int = 0
        self.over: bool = False
        self.attacker_retreated: bool = False
        self.defender_retreated: bool = False
        self.attacker_won: bool = False
        self.attacker_name: str = ""
        self.defender_name: str = ""

        self._init_ships(attacking_ships, self.attackers, True)
        self._init_ships(defending_ships, self.defenders, False)

    def _init_ships(self, ship_list: list[Ship], combat_list: list, is_attacker: bool):
        for i, ship in enumerate(ship_list):
            cls = self.game.get_ship_class(ship.class_id)
            if not cls:
                continue
            compos = [get_compo(idx) for idx in cls.compo_set]
            fc = get_fighter_capacity(compos)
            max_dmg = cls.size

            x = random.randint(0, 2) if is_attacker else random.randint(8, 10)
            y = random.randint(0, 12)

            cs = CombatShip(
                ship_id=ship.ship_id,
                owner=ship.owner,
                name=ship.name,
                class_name=cls.name,
                x=x, y=y,
                damage=ship.damage,
                max_damage=max_dmg,
                speed=cls.speed,
                shields=cls.shields,
                components=compos,
                has_fighters=fc > 0,
                fighter_count=fc,
            )
            combat_list.append(cs)

        player = self.game.get_player(ship_list[0].owner) if ship_list else None
        if is_attacker and player:
            self.attacker_name = player.name
        elif not is_attacker and player:
            self.defender_name = player.name

    def process_phase(self):
        if self.over:
            return

        self.phase += 1
        if self.phase > MAX_COMBAT_PHASES:
            self.over = True
            return

        all_ships = self.attackers + self.defenders
        active = [s for s in all_ships if not s.destroyed]

        # Move fighters
        for f in self.fighters:
            if not f.destroyed:
                self._move_fighter(f)

        # Move ships
        for s in active:
            self._move_ship_combat(s)

        # Fire weapons
        for s in active:
            if not s.fired:
                self._fire_weapons(s)

        # Check for retreats
        self._check_retreat()

        # Check end conditions
        self._check_end()

    def _move_ship_combat(self, ship: CombatShip):
        if ship.speed <= 0 or ship.moved:
            return
        dx = random.choice([-1, 0, 1]) * min(1, ship.speed)
        dy = random.choice([-1, 0, 1]) * min(1, ship.speed)
        ship.x = max(0, min(COMBAT_WIDTH - 1, ship.x + dx))
        ship.y = max(0, min(COMBAT_HEIGHT - 1, ship.y + dy))
        ship.moved = True

    def _move_fighter(self, fighter: CombatFighter):
        if fighter.moved or fighter.destroyed:
            return
        if fighter.target_x >= 0 and fighter.target_y >= 0:
            dx = fighter.target_x - fighter.x
            dy = fighter.target_y - fighter.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= fighter.speed:
                fighter.x, fighter.y = fighter.target_x, fighter.target_y
            else:
                if dist > 0:
                    fighter.x += int(dx / dist * fighter.speed)
                    fighter.y += int(dy / dist * fighter.speed)
        else:
            # Find nearest enemy
            enemies = self.defenders if fighter.owner == 1 else self.attackers
            target = None
            min_dist = 999
            for s in enemies:
                if s.destroyed:
                    continue
                d = math.sqrt((s.x - fighter.x) ** 2 + (s.y - fighter.y) ** 2)
                if d < min_dist:
                    min_dist = d
                    target = s
            if target:
                fighter.target_x = target.x
                fighter.target_y = target.y
        fighter.moved = True

    def _fire_weapons(self, ship: CombatShip):
        enemies = self.defenders if ship in self.attackers else self.attackers
        if not enemies:
            return

        weapons = [c for c in ship.components if c.category == "W"]
        if not weapons:
            return

        for weapon in weapons:
            target = self._pick_target(ship, enemies)
            if not target or target.destroyed:
                continue

            dist = math.sqrt((ship.x - target.x) ** 2 + (ship.y - target.y) ** 2)
            if dist > weapon.range_val:
                continue

            # Shield absorption
            if target.shields > 0:
                absorbed = min(target.shields, weapon.damage)
                target.shields -= absorbed
                dmg = weapon.damage - absorbed
            else:
                dmg = weapon.damage

            if dmg > 0:
                if weapon.fire_type == 1:
                    actual_dmg = int(dmg - (dist * weapon.decrease_dmg) + 0.5)
                else:
                    actual_dmg = dmg - int((dist + 1) * weapon.decrease_dmg)

                actual_dmg = max(0, actual_dmg)
                target.damage += actual_dmg
                if target.damage >= target.max_damage:
                    target.destroyed = True

        ship.fired = True

    def _pick_target(self, ship: CombatShip, enemies: list[CombatShip]) -> CombatShip:
        live = [e for e in enemies if not e.destroyed]
        if not live:
            return None
        return random.choice(live)

    def _check_retreat(self):
        if not self.attackers or not self.defenders:
            return

        att_alive = sum(1 for s in self.attackers if not s.destroyed)
        def_alive = sum(1 for s in self.defenders if not s.destroyed)

        if att_alive == 0:
            self.over = True
            self.attacker_won = False
        elif def_alive == 0:
            self.over = True
            self.attacker_won = True

    def _check_end(self):
        pass

    def apply_results(self):
        all_original_ships = {s.ship_id: s for s in self.game.ships}

        for cs in self.attackers + self.defenders:
            original = all_original_ships.get(cs.ship_id)
            if original:
                if cs.destroyed or cs.damage >= cs.max_damage:
                    if original in self.game.ships:
                        self.game.ships.remove(original)
                else:
                    original.damage = cs.damage

        # Apply fighter damage
        for f in self.fighters:
            if f.destroyed:
                continue
            # Fighters that survive return to carrier (simplified)

    def get_all_ships(self) -> list[CombatShip]:
        return self.attackers + self.defenders
