from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Item:
    slot: str
    name: str
    rarity: str
    atk: int = 0
    defense: int = 0
    hp: int = 0
    crit: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Item"]:
        if not data:
            return None
        return cls(**data)


@dataclass
class Player:
    hero_class: str
    class_label: str
    max_hp: int
    hp: int
    attack: int
    defense: int
    crit: float
    mana: int
    max_mana: int
    gold: int = 0
    potions: int = 2
    room: int = 1
    xp: int = 0
    level: int = 1
    temp_guard: int = 0
    gear: dict = field(default_factory=lambda: {"Weapon": None, "Armor": None, "Trinket": None})

    def gear_items(self) -> dict:
        return {slot: Item.from_dict(item) for slot, item in self.gear.items()}

    def total_attack(self) -> int:
        return self.attack + sum(item.atk for item in self.gear_items().values() if item)

    def total_defense(self) -> int:
        return self.defense + self.temp_guard + sum(item.defense for item in self.gear_items().values() if item)

    def total_max_hp(self) -> int:
        return self.max_hp + sum(item.hp for item in self.gear_items().values() if item)

    def total_crit(self) -> float:
        return self.crit + sum(item.crit for item in self.gear_items().values() if item)

    def to_dict(self) -> dict:
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(**data)


@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    crit: float
    is_boss: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Enemy"]:
        if not data:
            return None
        return cls(
            name=data["name"],
            hp=data["hp"],
            max_hp=data.get("max_hp", data["hp"]),
            attack=data["attack"],
            defense=data["defense"],
            crit=data["crit"],
            is_boss=data.get("is_boss", False),
        )
