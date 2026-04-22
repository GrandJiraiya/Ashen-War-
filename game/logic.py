from __future__ import annotations

import random
from typing import Optional

from .data import (
    ARMOR_NAMES,
    BOSS_NAMES,
    CLASS_DATA,
    ENEMY_PREFIX,
    ENEMY_SUFFIX,
    MERCHANT_QUOTES,
    RARITY_MULTIPLIER,
    TRINKET_NAMES,
    WEAPON_NAMES,
    weighted_rarity,
)
from .models import Enemy, Item, Player

RNG = random.Random()


# ---------- creation / serialization helpers ----------

def create_new_run(hero_class: str) -> dict:
    data = CLASS_DATA[hero_class]
    player = Player(
        hero_class=hero_class,
        class_label=data["label"],
        max_hp=data["hp"],
        hp=data["hp"],
        attack=data["attack"],
        defense=data["defense"],
        crit=data["crit"],
        mana=data["mana"],
        max_mana=data["mana"],
    )
    enemy = make_enemy(player.room)
    return {
        "player": player.to_dict(),
        "enemy": enemy.to_dict(),
        "status": "ready",
        "battle_log": [f"A new run begins. Room {player.room} awaits."],
        "last_reward": None,
        "reward_pending": False,
        "merchant_quote": random.choice(MERCHANT_QUOTES),
        "run_over": False,
        "victory_count": 0,
    }


def get_player(state: dict) -> Player:
    return Player.from_dict(state["player"])


def set_player(state: dict, player: Player) -> None:
    state["player"] = player.to_dict()


def get_enemy(state: dict) -> Optional[Enemy]:
    return Enemy.from_dict(state.get("enemy"))


def set_enemy(state: dict, enemy: Optional[Enemy]) -> None:
    state["enemy"] = enemy.to_dict() if enemy else None


# ---------- generators ----------

def make_enemy(room: int) -> Enemy:
    if room % 5 == 0:
        hp = 55 + room * 16
        return Enemy(
            name=RNG.choice(BOSS_NAMES),
            hp=hp,
            max_hp=hp,
            attack=9 + room * 2,
            defense=3 + room // 3,
            crit=0.12,
            is_boss=True,
        )
    hp = 24 + room * 8 + RNG.randint(-4, 6)
    return Enemy(
        name=f"{RNG.choice(ENEMY_PREFIX)} {RNG.choice(ENEMY_SUFFIX)}",
        hp=hp,
        max_hp=hp,
        attack=5 + room * 2 + RNG.randint(0, 2),
        defense=max(0, 1 + room // 4),
        crit=0.06 + min(0.10, room * 0.002),
    )


def generate_item(hero_class: str, level: int, forced_slot: Optional[str] = None) -> Item:
    slot = forced_slot or RNG.choice(["Weapon", "Armor", "Trinket"])
    rarity = weighted_rarity(RNG)
    mult = RARITY_MULTIPLIER[rarity]
    base = max(1, level)

    if slot == "Weapon":
        return Item(
            slot=slot,
            name=RNG.choice(WEAPON_NAMES[hero_class]),
            rarity=rarity,
            atk=max(1, int((3 + base * 1.5) * mult)),
        )
    if slot == "Armor":
        return Item(
            slot=slot,
            name=RNG.choice(ARMOR_NAMES[hero_class]),
            rarity=rarity,
            defense=max(1, int((2 + base * 1.2) * mult)),
            hp=max(0, int((4 + base * 2.2) * mult)),
        )
    return Item(
        slot=slot,
        name=RNG.choice(TRINKET_NAMES[hero_class]),
        rarity=rarity,
        atk=max(0, int((1 + base * 0.6) * (mult - 0.2))),
        crit=round(min(0.15, 0.01 * base * mult), 2),
    )


# ---------- core logic ----------

def compare_items(new_item: Item, equipped: Optional[Item]) -> float:
    def score(item: Optional[Item]) -> float:
        if not item:
            return -9999
        return item.atk * 2 + item.defense * 1.6 + item.hp * 0.5 + item.crit * 120

    return score(new_item) - score(equipped)


def calc_damage(atk: int, defense: int, crit_chance: float) -> tuple[int, bool]:
    base = max(1, atk - defense + RNG.randint(-2, 3))
    crit = RNG.random() < crit_chance
    if crit:
        return int(base * 1.7), True
    return base, False


def cast_spell(player: Player, enemy: Enemy, battle_log: list[str]) -> None:
    spell = CLASS_DATA[player.hero_class]["spell"]
    if player.mana < spell["cost"]:
        battle_log.append(f"You try to cast {spell['name']}, but your mana taps out.")
        return

    player.mana -= spell["cost"]

    if player.hero_class == "mage":
        damage = player.total_attack() + RNG.randint(12, 22)
        if RNG.random() < 0.25:
            damage *= 2
            battle_log.append(f"{spell['name']} double-casts like it has main-character syndrome.")
        dealt = max(1, damage - enemy.defense)
        enemy.hp -= dealt
        battle_log.append(f"You cast {spell['name']} for {dealt} damage.")
        return

    if player.hero_class == "warrior":
        damage = player.total_attack() + RNG.randint(8, 16)
        dealt = max(1, damage - enemy.defense)
        enemy.hp -= dealt
        player.temp_guard += 3
        battle_log.append(f"You use {spell['name']} for {dealt} damage and gain +3 guard.")
        return

    hits = RNG.randint(2, 4)
    total = 0
    for _ in range(hits):
        hit = max(1, int(player.total_attack() * 0.65) + RNG.randint(1, 4) - enemy.defense)
        if RNG.random() < 0.35:
            hit = int(hit * 1.8)
        total += hit
    enemy.hp -= total
    battle_log.append(f"You unleash {spell['name']} for {total} total damage across {hits} hits.")


def use_potion(player: Player, battle_log: list[str]) -> None:
    if player.potions <= 0:
        battle_log.append("No potions left. Your flask economy is in shambles.")
        return
    player.potions -= 1
    heal = int(player.total_max_hp() * 0.40)
    player.hp = min(player.total_max_hp(), player.hp + heal)
    battle_log.append(f"You drink a potion and restore {heal} HP.")


def resolve_battle(state: dict, action: str = "attack") -> dict:
    if state.get("run_over"):
        return state
    if state.get("reward_pending"):
        state["battle_log"] = ["Choose a reward before entering the next room."]
        return state

    player = get_player(state)
    enemy = get_enemy(state)
    if not enemy:
        enemy = make_enemy(player.room)

    battle_log = [f"Room {player.room}: {'Boss' if enemy.is_boss else 'Enemy'} - {enemy.name}"]

    if action == "spell":
        cast_spell(player, enemy, battle_log)
    elif action == "potion":
        use_potion(player, battle_log)
    else:
        damage, crit = calc_damage(player.total_attack(), enemy.defense, player.total_crit())
        enemy.hp -= damage
        battle_log.append(f"You attack for {damage} damage{' (CRIT)' if crit else ''}.")

    if enemy.hp > 0:
        damage, crit = calc_damage(enemy.attack, player.total_defense(), enemy.crit)
        player.hp -= damage
        battle_log.append(f"{enemy.name} hits you for {damage} damage{' (CRIT)' if crit else ''}.")

    if player.hp <= 0:
        player.hp = 0
        state["run_over"] = True
        state["status"] = "dead"
        battle_log.append("You fall. The dungeon keeps your lunch money.")
        set_player(state, player)
        set_enemy(state, enemy)
        state["battle_log"] = battle_log
        return state

    if enemy.hp <= 0:
        gold_gain = 15 + player.room * 4 + (20 if enemy.is_boss else 0)
        xp_gain = 12 + player.room * 5 + (18 if enemy.is_boss else 0)
        player.gold += gold_gain
        level_up_messages = gain_xp(player, xp_gain)
        battle_log.append(f"You defeated {enemy.name}. +{gold_gain} gold, +{xp_gain} XP.")
        battle_log.extend(level_up_messages)
        state["reward_pending"] = True
        state["status"] = "reward"
        state["last_reward"] = None
        state["victory_count"] += 1
        state["merchant_quote"] = random.choice(MERCHANT_QUOTES)
        set_enemy(state, None)
    else:
        state["status"] = "battle"
        set_enemy(state, enemy)

    set_player(state, player)
    state["battle_log"] = battle_log
    return state


def gain_xp(player: Player, xp_gain: int) -> list[str]:
    messages: list[str] = []
    player.xp += xp_gain
    while player.xp >= player.level * 30:
        player.xp -= player.level * 30
        player.level += 1
        player.max_hp += 8
        player.attack += 2
        player.defense += 1
        player.max_mana += 4
        player.mana = player.max_mana
        player.hp = player.total_max_hp()
        player.potions += 1
        messages.append(f"LEVEL UP! You are now level {player.level}. Free potion awarded.")
    return messages


def choose_reward(state: dict, reward_type: str) -> dict:
    if not state.get("reward_pending") or state.get("run_over"):
        state["battle_log"] = ["No reward is waiting right now."]
        return state

    player = get_player(state)
    battle_log: list[str] = []

    if reward_type == "potion":
        player.potions += 1
        battle_log.append("You stash an extra potion.")
        state["last_reward"] = None
    elif reward_type == "heal":
        heal = int(player.total_max_hp() * 0.35)
        player.hp = min(player.total_max_hp(), player.hp + heal)
        battle_log.append(f"You catch your breath and recover {heal} HP.")
        state["last_reward"] = None
    elif reward_type == "mana":
        player.mana = min(player.max_mana, player.mana + 20)
        battle_log.append("Arcane fumes restore 20 mana.")
        state["last_reward"] = None
    else:
        item = generate_item(player.hero_class, player.level)
        equipped = Item.from_dict(player.gear[item.slot])
        delta = compare_items(item, equipped)
        battle_log.append(f"Loot found: {item.rarity} {item.name} ({item.slot}).")
        if equipped:
            battle_log.append(f"Current {item.slot}: {equipped.rarity} {equipped.name}.")
        battle_log.append("Looks like an upgrade." if equipped is None or delta >= 0 else "Probably worse, but fashion has no spreadsheet.")
        state["last_reward"] = item.to_dict()
        state["status"] = "gear"
        set_player(state, player)
        state["battle_log"] = battle_log
        return state

    advance_to_next_room(state, player, battle_log)
    return state


def handle_gear_choice(state: dict, decision: str) -> dict:
    item_data = state.get("last_reward")
    if not item_data or state.get("run_over"):
        state["battle_log"] = ["No gear choice is waiting."]
        return state

    player = get_player(state)
    item = Item.from_dict(item_data)
    assert item is not None
    battle_log: list[str] = []

    if decision == "equip":
        player.gear[item.slot] = item.to_dict()
        player.hp = min(player.hp, player.total_max_hp())
        battle_log.append(f"You equip {item.rarity} {item.name}.")
    else:
        sell_value = 10 + player.level * 3
        player.gold += sell_value
        battle_log.append(f"You sell {item.name} for {sell_value} gold.")

    state["last_reward"] = None
    advance_to_next_room(state, player, battle_log)
    return state


def advance_to_next_room(state: dict, player: Player, battle_log: list[str]) -> None:
    player.temp_guard = 0
    player.mana = min(player.max_mana, player.mana + 8 + player.level)
    player.hp = min(player.total_max_hp(), player.hp + 4 + player.level)
    player.room += 1
    next_enemy = make_enemy(player.room)
    battle_log.append(f"You descend to room {player.room}. {next_enemy.name} is waiting.")
    state["reward_pending"] = False
    state["status"] = "ready"
    set_player(state, player)
    set_enemy(state, next_enemy)
    state["battle_log"] = battle_log


def shop_action(state: dict, action: str) -> dict:
    if state.get("run_over"):
        return state

    player = get_player(state)
    battle_log: list[str] = []

    if action == "buy_potion":
        if player.gold >= 25:
            player.gold -= 25
            player.potions += 1
            battle_log.append("You buy a potion for 25 gold.")
        else:
            battle_log.append("Not enough gold. The merchant gives you the broke stare.")
    elif action == "buy_gear":
        if player.gold >= 60:
            player.gold -= 60
            item = generate_item(player.hero_class, player.level + 1)
            state["last_reward"] = item.to_dict()
            state["status"] = "gear"
            battle_log.append(f"Merchant offers: {item.rarity} {item.name}.")
            set_player(state, player)
            state["battle_log"] = battle_log
            return state
        battle_log.append("You do not have 60 gold. Commerce remains undefeated.")
    else:
        battle_log.append("You leave the merchant alone with his suspicious inventory.")

    set_player(state, player)
    state["battle_log"] = battle_log
    return state


def state_for_client(state: Optional[dict]) -> dict:
    if not state:
        return {"has_run": False, "classes": CLASS_DATA}

    player = get_player(state)
    enemy = get_enemy(state)

    reward_options = None
    gear_offer = None

    if state.get("status") == "reward" and state.get("reward_pending"):
        reward_options = [
            {"id": "potion", "label": "+1 Potion"},
            {"id": "heal", "label": "Recover 35% HP"},
            {"id": "mana", "label": "+20 Mana"},
            {"id": "loot", "label": "Roll Gear"},
        ]

    if state.get("status") == "gear" and state.get("last_reward"):
        gear_offer = state["last_reward"]

    return {
        "has_run": True,
        "status": state.get("status", "ready"),
        "run_over": state.get("run_over", False),
        "battle_log": state.get("battle_log", []),
        "reward_pending": state.get("reward_pending", False),
        "reward_options": reward_options,
        "gear_offer": gear_offer,
        "merchant_quote": state.get("merchant_quote"),
        "room": player.room,
        "player": {
            **player.to_dict(),
            "class": player.hero_class,
            "display_class": player.class_label,
            "max_hp": player.total_max_hp(),
        },
        "enemy": None if not enemy else enemy.to_dict(),
        "classes": CLASS_DATA,
    }
