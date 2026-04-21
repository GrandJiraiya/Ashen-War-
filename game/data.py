import random

CLASS_DATA = {
    "mage": {
        "label": "Mage",
        "hp": 70,
        "attack": 11,
        "defense": 4,
        "crit": 0.15,
        "mana": 30,
        "spell": {
            "name": "Arcane Burst",
            "cost": 20,
            "description": "High arcane damage with a chance to double-cast.",
        },
    },
    "warrior": {
        "label": "Warrior",
        "hp": 95,
        "attack": 9,
        "defense": 7,
        "crit": 0.10,
        "mana": 24,
        "spell": {
            "name": "Shield Slam",
            "cost": 18,
            "description": "Heavy strike that also grants temporary defense.",
        },
    },
    "rogue": {
        "label": "Rogue",
        "hp": 78,
        "attack": 10,
        "defense": 5,
        "crit": 0.22,
        "mana": 26,
        "spell": {
            "name": "Shadow Flurry",
            "cost": 18,
            "description": "Multi-hit burst with high crit pressure.",
        },
    },
}

RARITY_MULTIPLIER = {
    "Common": 1.00,
    "Rare": 1.35,
    "Epic": 1.80,
    "Legendary": 2.40,
}

RARITY_WEIGHTS = [
    ("Common", 60),
    ("Rare", 27),
    ("Epic", 10),
    ("Legendary", 3),
]

WEAPON_NAMES = {
    "mage": ["Oak Staff", "Rune Wand", "Crystal Rod", "Storm Scepter"],
    "warrior": ["Rusty Sword", "Iron Axe", "Battle Hammer", "Knight Blade"],
    "rogue": ["Twin Daggers", "Hook Knives", "Silent Shiv", "Moonfang"],
}

ARMOR_NAMES = {
    "mage": ["Cloth Robe", "Mystic Mantle", "Starweave", "Astral Wrap"],
    "warrior": ["Chain Vest", "Steel Plate", "Warcoat", "Bulwark Mail"],
    "rogue": ["Leather Jerkin", "Shadow Coat", "Nightwrap", "Whisper Vest"],
}

TRINKET_NAMES = {
    "mage": ["Mana Charm", "Spell Ring", "Void Bead", "Astral Sigil"],
    "warrior": ["Iron Crest", "Guard Token", "War Medal", "Lion Emblem"],
    "rogue": ["Lucky Coin", "Smoke Charm", "Serpent Ring", "Thief Mark"],
}

ENEMY_PREFIX = ["Goblin", "Skeleton", "Cultist", "Bandit", "Wisp", "Slime", "Hound"]
ENEMY_SUFFIX = ["Raider", "Stalker", "Bruiser", "Hexer", "Guard", "Fiend", "Maw"]

BOSS_NAMES = [
    "The Bone Tyrant",
    "Grimhook the Collector",
    "The Ember Warden",
    "Voidmaw Herald",
    "Lady Venomgrin",
]

MERCHANT_QUOTES = [
    "Buy something before the goblins mark it up.",
    "Quality gear. Mild curses at no extra charge.",
    "These prices are fair. The dungeon disagrees.",
]


def weighted_rarity(rng: random.Random) -> str:
    roll = rng.randint(1, 100)
    total = 0
    for rarity, weight in RARITY_WEIGHTS:
        total += weight
        if roll <= total:
            return rarity
    return "Common"
