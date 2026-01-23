import asyncio
from decimal import Decimal
from typing import List, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from sanity.db.core import async_session_factory
from sanity.modules.bingo.boss.model import Boss
from sanity.modules.bingo.boss.repository import BossRepository
from sanity.modules.bingo.item.model import Item


class ItemDict(TypedDict):
    name: str
    drop_rate: int
    point_value: int


class BossDict(TypedDict):
    name: str
    ehb: Decimal
    uniques: List[ItemDict]


CATALOGUE_SEED: List[BossDict] = [
    {
        "name": "Abyssal Sire",
        "ehb": Decimal("50.0"),
        "uniques": [
            {"name": "Abyssal orphan", "drop_rate": 2560, "point_value": 0},
            {"name": "Unsired", "drop_rate": 100, "point_value": 0},
        ],
    },
    {
        "name": "Alchemical Hydra",
        "ehb": Decimal("30.0"),
        "uniques": [
            {"name": "Alchemical hydra heads", "drop_rate": 256, "point_value": 0},
            {"name": "Brimstone ring piece", "drop_rate": 181, "point_value": 0},
            {"name": "Hydra's claw", "drop_rate": 1000, "point_value": 0},
            {"name": "Hydra leather", "drop_rate": 512, "point_value": 0},
            {"name": "Hydra tail", "drop_rate": 512, "point_value": 0},
            {"name": "Ikkle hydra", "drop_rate": 3000, "point_value": 0},
            {"name": "Jar of chemicals", "drop_rate": 2000, "point_value": 0},
        ],
    },
    {
        "name": "Amoxliatl",
        "ehb": Decimal("84.0"),
        "uniques": [
            {"name": "Glacial temotli", "drop_rate": 100, "point_value": 0},
            {"name": "Moxi", "drop_rate": 3000, "point_value": 0},
        ],
    },
    {
        "name": "Araxxor",
        "ehb": Decimal("45.0"),
        "uniques": [
            {"name": "Araxyte fang", "drop_rate": 600, "point_value": 0},
            {"name": "Araxyte head", "drop_rate": 250, "point_value": 0},
            {"name": "Jar of venom", "drop_rate": 1500, "point_value": 0},
            {"name": "Nid", "drop_rate": 1500, "point_value": 0},
            {"name": "Noxious blade", "drop_rate": 200, "point_value": 0},
            {"name": "Noxious point", "drop_rate": 200, "point_value": 0},
            {"name": "Noxious pommel", "drop_rate": 200, "point_value": 0},
        ],
    },
    {
        "name": "Artio",
        "ehb": Decimal("60.0"),
        "uniques": [
            {"name": "Callisto cub", "drop_rate": 2800, "point_value": 0},
            {"name": "Claws of callisto", "drop_rate": 618, "point_value": 0},
            {"name": "Dragon 2h sword", "drop_rate": 358, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 358, "point_value": 0},
            {"name": "Tyrannical ring", "drop_rate": 716, "point_value": 0},
            {"name": "Voidwaker hilt", "drop_rate": 912, "point_value": 0},
        ],
    },
    {
        "name": "Callisto",
        "ehb": Decimal("80.0"),
        "uniques": [
            {"name": "Callisto cub", "drop_rate": 1500, "point_value": 0},
            {"name": "Claws of callisto", "drop_rate": 196, "point_value": 0},
            {"name": "Dragon 2h sword", "drop_rate": 256, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 256, "point_value": 0},
            {"name": "Tyrannical ring", "drop_rate": 512, "point_value": 0},
            {"name": "Voidwaker hilt", "drop_rate": 360, "point_value": 0},
        ],
    },
    {
        "name": "Calvarion",
        "ehb": Decimal("55.0"),
        "uniques": [
            {"name": "Dragon 2h sword", "drop_rate": 358, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 358, "point_value": 0},
            {"name": "Ring of the gods", "drop_rate": 716, "point_value": 0},
            {"name": "Skull of vet'ion", "drop_rate": 618, "point_value": 0},
            {"name": "Vet'ion jr.", "drop_rate": 2800, "point_value": 0},
            {"name": "Voidwaker blade", "drop_rate": 912, "point_value": 0},
        ],
    },
    {
        "name": "Cerberus",
        "ehb": Decimal("65.0"),
        "uniques": [
            {"name": "Eternal crystal", "drop_rate": 520, "point_value": 0},
            {"name": "Hellpuppy", "drop_rate": 3000, "point_value": 0},
            {"name": "Jar of souls", "drop_rate": 2000, "point_value": 0},
            {"name": "Pegasian crystal", "drop_rate": 520, "point_value": 0},
            {"name": "Primordial crystal", "drop_rate": 520, "point_value": 0},
            {"name": "Smouldering stone", "drop_rate": 520, "point_value": 0},
        ],
    },
    {
        "name": "Chambers of Xeric",
        "ehb": Decimal("3.5"),
        "uniques": [
            {"name": "Ancestral hat", "drop_rate": 667, "point_value": 0},
            {"name": "Ancestral robe bottom", "drop_rate": 667, "point_value": 0},
            {"name": "Ancestral robe top", "drop_rate": 667, "point_value": 0},
            {"name": "Arcane prayer scroll", "drop_rate": 100, "point_value": 0},
            {"name": "Dexterous prayer scroll", "drop_rate": 100, "point_value": 0},
            {"name": "Dinh's bulwark", "drop_rate": 667, "point_value": 0},
            {"name": "Dragon claws", "drop_rate": 191, "point_value": 0},
            {"name": "Dragon hunter crossbow", "drop_rate": 500, "point_value": 0},
            {"name": "Elder maul", "drop_rate": 1001, "point_value": 0},
            {"name": "Kodai insignia", "drop_rate": 1001, "point_value": 0},
            {"name": "Olmlet", "drop_rate": 1474, "point_value": 0},
            {"name": "Twisted bow", "drop_rate": 1001, "point_value": 0},
            {"name": "Twisted buckler", "drop_rate": 500, "point_value": 0},
        ],
    },
    {
        "name": "Chambers of Xeric (CM)",
        "ehb": Decimal("3.0"),
        "uniques": [
            {"name": "Metamorphic dust", "drop_rate": 400, "point_value": 0},
            {"name": "Twisted ancestral colour kit", "drop_rate": 75, "point_value": 0},
        ],
    },
    {
        "name": "Chaos Elemental",
        "ehb": Decimal("120.0"),
        "uniques": [
            {"name": "Dragon 2h sword", "drop_rate": 64, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 256, "point_value": 0},
            {"name": "Pet chaos elemental", "drop_rate": 300, "point_value": 0},
        ],
    },
    {
        "name": "Commander Zilyana",
        "ehb": Decimal("60.0"),
        "uniques": [
            {"name": "Armadyl crossbow", "drop_rate": 508, "point_value": 0},
            {"name": "Godsword shard 1", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 2", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 3", "drop_rate": 762, "point_value": 0},
            {"name": "Pet zilyana", "drop_rate": 5000, "point_value": 0},
            {"name": "Saradomin hilt", "drop_rate": 508, "point_value": 0},
            {"name": "Saradomin sword", "drop_rate": 127, "point_value": 0},
            {"name": "Saradomin's light", "drop_rate": 254, "point_value": 0},
        ],
    },
    {
        "name": "Corporeal Beast",
        "ehb": Decimal("40.0"),
        "uniques": [
            {"name": "Arcane sigil", "drop_rate": 1365, "point_value": 0},
            {"name": "Elysian sigil", "drop_rate": 4095, "point_value": 0},
            {"name": "Holy elixir", "drop_rate": 171, "point_value": 0},
            {"name": "Jar of spirits", "drop_rate": 1000, "point_value": 0},
            {"name": "Pet dark core", "drop_rate": 5000, "point_value": 0},
            {"name": "Spectral sigil", "drop_rate": 1365, "point_value": 0},
            {"name": "Spirit shield", "drop_rate": 64, "point_value": 0},
        ],
    },
    {
        "name": "Dagannoth Kings",
        "ehb": Decimal("90.0"),
        "uniques": [
            {"name": "Archers ring", "drop_rate": 128, "point_value": 0},
            {"name": "Berserker ring", "drop_rate": 128, "point_value": 0},
            {"name": "Dragon axe", "drop_rate": 128, "point_value": 0},
            {"name": "Pet dagannoth prime", "drop_rate": 5000, "point_value": 0},
            {"name": "Pet dagannoth rex", "drop_rate": 5000, "point_value": 0},
            {"name": "Pet dagannoth supreme", "drop_rate": 5000, "point_value": 0},
            {"name": "Seers ring", "drop_rate": 128, "point_value": 0},
            {"name": "Warrior ring", "drop_rate": 128, "point_value": 0},
        ],
    },
    {
        "name": "Doom of Mokhaiotl",
        "ehb": Decimal("20.0"),
        "uniques": [
            {"name": "Avernic treads", "drop_rate": 160, "point_value": 0},
            {"name": "Eye of ayak (uncharged)", "drop_rate": 148, "point_value": 0},
            {"name": "Mokhaiotl cloth", "drop_rate": 140, "point_value": 0},
        ],
    },
    {
        "name": "Duke Sucellus",
        "ehb": Decimal("40.0"),
        "uniques": [
            {"name": "Baron", "drop_rate": 2500, "point_value": 0},
            {"name": "Chromium ingot", "drop_rate": 240, "point_value": 0},
            {"name": "Eye of the duke", "drop_rate": 720, "point_value": 0},
            {"name": "Virtus mask", "drop_rate": 2160, "point_value": 0},
            {"name": "Virtus robe bottom", "drop_rate": 2160, "point_value": 0},
            {"name": "Virtus robe top", "drop_rate": 2160, "point_value": 0},
        ],
    },
    {
        "name": "General Graardor",
        "ehb": Decimal("58.0"),
        "uniques": [
            {"name": "Bandos boots", "drop_rate": 381, "point_value": 0},
            {"name": "Bandos chestplate", "drop_rate": 381, "point_value": 0},
            {"name": "Bandos hilt", "drop_rate": 508, "point_value": 0},
            {"name": "Bandos tassets", "drop_rate": 381, "point_value": 0},
            {"name": "Godsword shard 1", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 2", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 3", "drop_rate": 762, "point_value": 0},
            {"name": "Pet general graardor", "drop_rate": 5000, "point_value": 0},
        ],
    },
    {
        "name": "Giant Mole",
        "ehb": Decimal("140.0"),
        "uniques": [
            {"name": "Baby mole", "drop_rate": 3000, "point_value": 0},
            {"name": "Curved bone", "drop_rate": 5013, "point_value": 0},
            {"name": "Long bone", "drop_rate": 400, "point_value": 0},
        ],
    },
    {
        "name": "Grotesque Guardians",
        "ehb": Decimal("38.0"),
        "uniques": [
            {"name": "Black tourmaline core", "drop_rate": 500, "point_value": 0},
            {"name": "Granite gloves", "drop_rate": 250, "point_value": 0},
            {"name": "Granite hammer", "drop_rate": 375, "point_value": 0},
            {"name": "Granite ring", "drop_rate": 250, "point_value": 0},
            {"name": "Jar of stone", "drop_rate": 5000, "point_value": 0},
            {"name": "Noon", "drop_rate": 3000, "point_value": 0},
        ],
    },
    {
        "name": "Kalphite Queen",
        "ehb": Decimal("55.0"),
        "uniques": [
            {"name": "Dragon 2h sword", "drop_rate": 256, "point_value": 0},
            {"name": "Dragon chainbody", "drop_rate": 128, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 400, "point_value": 0},
            {"name": "Jar of sand", "drop_rate": 2000, "point_value": 0},
            {"name": "Kalphite princess", "drop_rate": 3000, "point_value": 0},
            {"name": "Kq head", "drop_rate": 256, "point_value": 0},
        ],
    },
    {
        "name": "King Black Dragon",
        "ehb": Decimal("150.0"),
        "uniques": [
            {"name": "Draconic visage", "drop_rate": 5000, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 1000, "point_value": 0},
            {"name": "Prince black dragon", "drop_rate": 3000, "point_value": 0},
        ],
    },
    {
        "name": "Kraken",
        "ehb": Decimal("100.0"),
        "uniques": [
            {"name": "Jar of dirt", "drop_rate": 1000, "point_value": 0},
            {"name": "Kraken tentacle", "drop_rate": 400, "point_value": 0},
            {"name": "Pet kraken", "drop_rate": 3000, "point_value": 0},
            {"name": "Trident of the seas (full)", "drop_rate": 512, "point_value": 0},
        ],
    },
    {
        "name": "Kree'arra",
        "ehb": Decimal("50.0"),
        "uniques": [
            {"name": "Armadyl chainskirt", "drop_rate": 381, "point_value": 0},
            {"name": "Armadyl chestplate", "drop_rate": 381, "point_value": 0},
            {"name": "Armadyl helmet", "drop_rate": 381, "point_value": 0},
            {"name": "Armadyl hilt", "drop_rate": 508, "point_value": 0},
            {"name": "Godsword shard 1", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 2", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 3", "drop_rate": 762, "point_value": 0},
            {"name": "Pet kree'arra", "drop_rate": 5000, "point_value": 0},
        ],
    },
    {
        "name": "K'ril Tsutsaroth",
        "ehb": Decimal("80.0"),
        "uniques": [
            {"name": "Godsword shard 1", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 2", "drop_rate": 762, "point_value": 0},
            {"name": "Godsword shard 3", "drop_rate": 762, "point_value": 0},
            {"name": "Pet k'ril tsutsaroth", "drop_rate": 5000, "point_value": 0},
            {"name": "Staff of the dead", "drop_rate": 508, "point_value": 0},
            {"name": "Steam battlestaff", "drop_rate": 128, "point_value": 0},
            {"name": "Zamorak hilt", "drop_rate": 508, "point_value": 0},
            {"name": "Zamorakian spear", "drop_rate": 128, "point_value": 0},
        ],
    },
    {
        "name": "Nex",
        "ehb": Decimal("14.0"),
        "uniques": [
            {"name": "Ancient hilt", "drop_rate": 516, "point_value": 0},
            {"name": "Nexling", "drop_rate": 500, "point_value": 0},
            {"name": "Nihil horn", "drop_rate": 258, "point_value": 0},
            {"name": "Torva full helm", "drop_rate": 258, "point_value": 0},
            {"name": "Torva platebody", "drop_rate": 258, "point_value": 0},
            {"name": "Torva platelegs", "drop_rate": 258, "point_value": 0},
            {"name": "Zaryte vambraces", "drop_rate": 172, "point_value": 0},
        ],
    },
    {
        "name": "Phantom Muspah",
        "ehb": Decimal("30.0"),
        "uniques": [
            {"name": "Ancient icon", "drop_rate": 50, "point_value": 0},
            {"name": "Magic seeds", "drop_rate": 534, "point_value": 0},
            {"name": "Muphin", "drop_rate": 2500, "point_value": 0},
            {"name": "Venator shard", "drop_rate": 100, "point_value": 0},
        ],
    },
    {
        "name": "Phosani's Nightmare",
        "ehb": Decimal("11.0"),
        "uniques": [
            {"name": "Eldritch orb", "drop_rate": 1600, "point_value": 0},
            {"name": "Harmonised orb", "drop_rate": 1600, "point_value": 0},
            {"name": "Inquisitor's great helm", "drop_rate": 700, "point_value": 0},
            {"name": "Inquisitor's hauberk", "drop_rate": 700, "point_value": 0},
            {"name": "Inquisitor's mace", "drop_rate": 1250, "point_value": 0},
            {"name": "Inquisitor's plateskirt", "drop_rate": 700, "point_value": 0},
            {"name": "Jar of dreams", "drop_rate": 1400, "point_value": 0},
            {"name": "Little nightmare", "drop_rate": 4000, "point_value": 0},
            {"name": "Nightmare staff", "drop_rate": 533, "point_value": 0},
            {"name": "Volatile orb", "drop_rate": 1600, "point_value": 0},
        ],
    },
    {
        "name": "Sarachnis",
        "ehb": Decimal("110.0"),
        "uniques": [
            {"name": "Jar of eyes", "drop_rate": 2000, "point_value": 0},
            {"name": "Sarachnis cudgel", "drop_rate": 384, "point_value": 0},
            {"name": "Sraracha", "drop_rate": 3000, "point_value": 0},
        ],
    },
    {
        "name": "Scorpia",
        "ehb": Decimal("130.0"),
        "uniques": [
            {"name": "Malediction shard 3", "drop_rate": 256, "point_value": 0},
            {"name": "Odium shard 3", "drop_rate": 256, "point_value": 0},
            {"name": "Scorpia's offspring", "drop_rate": 2016, "point_value": 0},
        ],
    },
    {
        "name": "Scurrius",
        "ehb": Decimal("60.0"),
        "uniques": [
            {"name": "Long bone", "drop_rate": 400, "point_value": 0},
            {"name": "Scurry", "drop_rate": 3000, "point_value": 0},
        ],
    },
    {
        "name": "Sol Heredit",
        "ehb": Decimal("2.5"),
        "uniques": [
            {"name": "Sunfire fanatic chausses", "drop_rate": 8, "point_value": 0},
            {"name": "Sunfire fanatic cuirass", "drop_rate": 8, "point_value": 0},
            {"name": "Sunfire fanatic helm", "drop_rate": 8, "point_value": 0},
            {"name": "Dizana's quiver", "drop_rate": 1, "point_value": 0},
            {"name": "Tonalztics of ralos", "drop_rate": 83, "point_value": 0},
            {"name": "Echo crystal", "drop_rate": 12, "point_value": 0},
            {"name": "Smol heredit", "drop_rate": 200, "point_value": 0},
        ],
    },
    {
        "name": "Spindel",
        "ehb": Decimal("55.0"),
        "uniques": [
            {"name": "Dragon 2h sword", "drop_rate": 358, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 358, "point_value": 0},
            {"name": "Fangs of venenatis", "drop_rate": 618, "point_value": 0},
            {"name": "Treasonous ring", "drop_rate": 716, "point_value": 0},
            {"name": "Venenatis spiderling", "drop_rate": 2800, "point_value": 0},
            {"name": "Voidwaker gem", "drop_rate": 912, "point_value": 0},
        ],
    },
    {
        "name": "The Corrupted Gauntlet",
        "ehb": Decimal("7.0"),
        "uniques": [
            {"name": "Crystal armour seed", "drop_rate": 50, "point_value": 0},
            {"name": "Crystal weapon seed", "drop_rate": 50, "point_value": 0},
            {"name": "Enhanced crystal weapon seed", "drop_rate": 400, "point_value": 0},
            {"name": "Youngllef", "drop_rate": 800, "point_value": 0},
        ],
    },
    {
        "name": "The Hueycoatl",
        "ehb": Decimal("20.0"),
        "uniques": [
            {"name": "Dragon hunter wand", "drop_rate": 105, "point_value": 0},
            {"name": "Huberte", "drop_rate": 400, "point_value": 0},
            {"name": "Hueycoatl hide", "drop_rate": 29, "point_value": 0},
            {"name": "Tome of earth", "drop_rate": 90, "point_value": 0},
        ],
    },
    {
        "name": "The Leviathan",
        "ehb": Decimal("30.0"),
        "uniques": [
            {"name": "Chromium ingot", "drop_rate": 256, "point_value": 0},
            {"name": "Leviathan's lure", "drop_rate": 768, "point_value": 0},
            {"name": "Virtus mask", "drop_rate": 2304, "point_value": 0},
            {"name": "Virtus robe bottom", "drop_rate": 2304, "point_value": 0},
            {"name": "Virtus robe top", "drop_rate": 2304, "point_value": 0},
            {"name": "Lil'viathan", "drop_rate": 2500, "point_value": 0},
        ],
    },
    {
        "name": "The Royal Titans",
        "ehb": Decimal("55.0"),
        "uniques": [
            {"name": "Bran", "drop_rate": 1500, "point_value": 0},
        ],
    },
    {
        "name": "The Whisperer",
        "ehb": Decimal("21.0"),
        "uniques": [
            {"name": "Chromium ingot", "drop_rate": 171, "point_value": 0},
            {"name": "Siren's staff", "drop_rate": 512, "point_value": 0},
            {"name": "Virtus mask", "drop_rate": 1536, "point_value": 0},
            {"name": "Virtus robe bottom", "drop_rate": 1536, "point_value": 0},
            {"name": "Virtus robe top", "drop_rate": 1536, "point_value": 0},
            {"name": "Wisp", "drop_rate": 2000, "point_value": 0},
        ],
    },
    {
        "name": "Theatre of Blood",
        "ehb": Decimal("3.5"),
        "uniques": [
            {"name": "Avernic defender hilt", "drop_rate": 79, "point_value": 0},
            {"name": "Ghrazi rapier", "drop_rate": 315, "point_value": 0},
            {"name": "Justiciar chestguard", "drop_rate": 315, "point_value": 0},
            {"name": "Justiciar faceguard", "drop_rate": 315, "point_value": 0},
            {"name": "Justiciar legguards", "drop_rate": 315, "point_value": 0},
            {"name": "Lil' zik", "drop_rate": 650, "point_value": 0},
            {"name": "Sanguinesti staff", "drop_rate": 315, "point_value": 0},
            {"name": "Scythe of vitur", "drop_rate": 630, "point_value": 0},
        ],
    },
    {
        "name": "Theatre of Blood (HM)",
        "ehb": Decimal("3.2"),
        "uniques": [
            {"name": "Holy ornament kit", "drop_rate": 100, "point_value": 0},
            {"name": "Sanguine dust", "drop_rate": 275, "point_value": 0},
            {"name": "Sanguine ornament kit", "drop_rate": 150, "point_value": 0},
        ],
    },
    {
        "name": "Thermonuclear Smoke Devil",
        "ehb": Decimal("110.0"),
        "uniques": [
            {"name": "Dragon chainbody", "drop_rate": 2000, "point_value": 0},
            {"name": "Jar of smoke", "drop_rate": 2000, "point_value": 0},
            {"name": "Occult necklace", "drop_rate": 350, "point_value": 0},
            {"name": "Pet smoke devil", "drop_rate": 3000, "point_value": 0},
            {"name": "Smoke battlestaff", "drop_rate": 512, "point_value": 0},
        ],
    },
    {
        "name": "Tombs of Amascut",
        "ehb": Decimal("3.0"),
        "uniques": [
            {"name": "Elidinis' ward", "drop_rate": 90, "point_value": 0},
            {"name": "Lightbearer", "drop_rate": 39, "point_value": 0},
            {"name": "Masori body", "drop_rate": 135, "point_value": 0},
            {"name": "Masori chaps", "drop_rate": 135, "point_value": 0},
            {"name": "Masori mask", "drop_rate": 135, "point_value": 0},
            {"name": "Osmumten's fang", "drop_rate": 39, "point_value": 0},
            {"name": "Tumeken's guardian", "drop_rate": 315, "point_value": 0},
            {"name": "Tumeken's shadow", "drop_rate": 270, "point_value": 0},
        ],
    },
    {
        "name": "Tzkal-Zuk",
        "ehb": Decimal("1.0"),
        "uniques": [
            {"name": "Infernal cape", "drop_rate": 1, "point_value": 0},
            {"name": "Jal-nib-rek", "drop_rate": 43, "point_value": 0},
        ],
    },
    {
        "name": "TzTok-Jad",
        "ehb": Decimal("3.0"),
        "uniques": [
            {"name": "Fire cape", "drop_rate": 1, "point_value": 0},
            {"name": "Tzrek-jad", "drop_rate": 67, "point_value": 0},
        ],
    },
    {
        "name": "Vardorvis",
        "ehb": Decimal("37.0"),
        "uniques": [
            {"name": "Butch", "drop_rate": 3000, "point_value": 0},
            {"name": "Chromium ingot", "drop_rate": 363, "point_value": 0},
            {"name": "Executioner's axe head", "drop_rate": 1088, "point_value": 0},
            {"name": "Virtus mask", "drop_rate": 3264, "point_value": 0},
            {"name": "Virtus robe bottom", "drop_rate": 3264, "point_value": 0},
            {"name": "Virtus robe top", "drop_rate": 3264, "point_value": 0},
        ],
    },
    {
        "name": "Venenatis",
        "ehb": Decimal("80.0"),
        "uniques": [
            {"name": "Dragon 2h sword", "drop_rate": 256, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 256, "point_value": 0},
            {"name": "Fangs of venenatis", "drop_rate": 196, "point_value": 0},
            {"name": "Treasonous ring", "drop_rate": 512, "point_value": 0},
            {"name": "Venenatis spiderling", "drop_rate": 1500, "point_value": 0},
            {"name": "Voidwaker gem", "drop_rate": 360, "point_value": 0},
        ],
    },
    {
        "name": "Vet'ion",
        "ehb": Decimal("42.0"),
        "uniques": [
            {"name": "Dragon 2h sword", "drop_rate": 256, "point_value": 0},
            {"name": "Dragon pickaxe", "drop_rate": 256, "point_value": 0},
            {"name": "Ring of the gods", "drop_rate": 512, "point_value": 0},
            {"name": "Skull of vet'ion", "drop_rate": 196, "point_value": 0},
            {"name": "Vet'ion jr.", "drop_rate": 1500, "point_value": 0},
            {"name": "Voidwaker blade", "drop_rate": 360, "point_value": 0},
        ],
    },
    {
        "name": "Vorkath",
        "ehb": Decimal("34.0"),
        "uniques": [
            {"name": "Dragonbone necklace", "drop_rate": 1000, "point_value": 0},
            {"name": "Jar of decay", "drop_rate": 3000, "point_value": 0},
            {"name": "Skeletal visage", "drop_rate": 5000, "point_value": 0},
            {"name": "Vorkath's head", "drop_rate": 50, "point_value": 0},
            {"name": "Vorki", "drop_rate": 3000, "point_value": 0},
        ],
    },
    {
        "name": "Yama",
        "ehb": Decimal("20.0"),
        "uniques": [
            {"name": "Oathplate chest", "drop_rate": 600, "point_value": 0},
            {"name": "Oathplate helm", "drop_rate": 600, "point_value": 0},
            {"name": "Oathplate legs", "drop_rate": 600, "point_value": 0},
            {"name": "Soulflame horn", "drop_rate": 300, "point_value": 0},
        ],
    },
    {
        "name": "Zulrah",
        "ehb": Decimal("42.0"),
        "uniques": [
            {"name": "Jar of swamp", "drop_rate": 3000, "point_value": 0},
            {"name": "Magic fang", "drop_rate": 512, "point_value": 0},
            {"name": "Magma mutagen", "drop_rate": 6554, "point_value": 0},
            {"name": "Pet snakeling", "drop_rate": 4000, "point_value": 0},
            {"name": "Serpentine visage", "drop_rate": 512, "point_value": 0},
            {"name": "Tanzanite fang", "drop_rate": 512, "point_value": 0},
            {"name": "Tanzanite mutagen", "drop_rate": 6554, "point_value": 0},
            {"name": "Uncut onyx", "drop_rate": 512, "point_value": 0},
        ],
    },
]


async def create_seed_data(session: AsyncSession):
    """Create catalogue data for development/testing."""

    repository = BossRepository(session)

    for boss_dict in CATALOGUE_SEED:
        try:
            await repository.create(
                Boss(
                    name=boss_dict["name"],
                    ehb=boss_dict["ehb"],
                    uniques=[
                        Item(
                            name=item_dict["name"],
                            drop_rate=item_dict["drop_rate"],
                            point_value=item_dict["point_value"],
                        )
                        for item_dict in boss_dict["uniques"]
                    ],
                )
            )
            await session.flush()
        except Exception:
            await session.rollback()
            print(f"Boss {boss_dict['name']} already exists")

    print("Seed data created successfully!")
    print("Created 50 bosses and their unique items.")


async def main() -> None:
    """Load sample/test data into the database."""

    async with async_session_factory() as session:
        await create_seed_data(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
