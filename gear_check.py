import requests
import xmltodict
import ast
import re
import json

slots = {
    0: "Helmet",
    1: "Neck",
    2: "Shoulder",
    3: "Shirt",
    4: "Chest",
    5: "Belt",
    6: "Pants",
    7: "Boots",
    8: "Bracers",
    9: "Gloves",
    10: "Finger 1",
    11: "Finger 2",
    12: "Trinket 1",
    13: "Trinket 2",
    14: "Cloak",
    15: "Mainhand",
    16: "Offhand",
    17: "Ranged/Relic",
    18: "Tabard",
}

ignore_slots = [3, 18]

ignore_enchant = [1, 5, 12, 13, 17]

wowhead_link = "https://www.wowhead.com/cata/item=ITEMID?xml"

zone_itemlevel = {
    1023: {"min": 346, "max": 372},  # 25-player BWD/TOFW/BOT
    1024: {"min": 346, "max": 372},  # 10-player BWD/TOFW/BOT
    1027: {"min": 372, "max": 391},  # Firelands
}

gem_class = {
    0: [0],  # Red
    1: [1],  # Blue
    2: [2],  # Yellow
    3: [0, 1],  # Purple
    4: [1, 2],  # Green
    5: [0, 2],  # Orange
    8: [0, 1, 2],  # Prismatic
    10: [],  # Cogwheel
}

main_attributes = ["int", "str", "agi", "spi"]

gem_attributes = [
    "int",
    "str",
    "agi",
    "spi",
    "sta",
    "splhastertng",
    "mlehastertng",
    "rgdhastertng",
    "splhitrtng",
    "mlehitrtng",
    "rgdhitrtng",
    "mastrtng",
    "mlecritstrkrtng",
    "rgdcritstrkrtng",
    "splcritstrkrtng",
    "exprtng",
    "parryrtng",
    "dodgertng",
    "resirtng",
    "splpen",
]

attribute_locale = {
    "int": "Intellect",
    "str": "Strength",
    "agi": "Agility",
    "spi": "Spirit",
    "sta": "Stamina",
    "splhastertng": "Haste rating",
    "mlehastertng": "Haste rating",
    "rgdhastertng": "Haste rating",
    "splhitrtng": "Hit rating",
    "mlehitrtng": "Hit rating",
    "rgdhitrtng": "Hit rating",
    "mastrtng": "Mastery rating",
    "mlecritstrkrtng": "Critical strike rating",
    "rgdcritstrkrtng": "Critical strike rating",
    "splcritstrkrtng": "Critical strike rating",
    "exprtng": "Expertise rating",
    "parryrtng": "Parry rating",
    "dodgertng": "Dodge rating",
    "resirtng": "Resilience rating",
    "splpen": "Spell penetration",
}

armor_type = {
    "Druid": 2,
    "Rogue": 2,
    "Priest": 1,
    "Warrior": 4,
    "Paladin": 4,
    "Warlock": 1,
    "Hunter": 3,
    "DeathKnight": 4,
    "Shaman": 3,
    "Mage": 1,
}

locale_armor_type = {1: "Cloth", 2: "Leather", 3: "Mail", 4: "Plate"}

spec_attributes = {
    "Druid-Balance": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Druid-Feral": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mastrtng"],
        ],
    },
    "Druid-Guardian": {
        "mainstat": ["sta", "agi"],
        "gems": [["sta"], ["mastrtng", "sta"]],
    },
    "Druid-Restoration": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Shaman-Elemental": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Shaman-Enhancement": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mastrtng"],
        ],
    },
    "Shaman-Restoration": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Rogue-Assassination": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mastrtng"],
        ],
    },
    "Rogue-Combat": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mastrtng"],
            ["agi", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Rogue-Subtlety": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mastrtng"],
            ["agi", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Priest-Shadow": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Priest-Discipline": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Priest-Holy": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Mage-Fire": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "mlecritstrkrtng", "rgdcritstrkrtng", "splcritstrkrtng"],
            ["int", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Mage-Frost": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "mlecritstrkrtng", "rgdcritstrkrtng", "splcritstrkrtng"],
            ["int", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Mage-Arcane": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "mastrtng"],
            ["int", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Hunter-Survival": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mlecritstrkrtng", "rgdcritstrkrtng", "splcritstrkrtng"],
        ],
    },
    "Hunter-Marksmanship": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mlecritstrkrtng", "rgdcritstrkrtng", "splcritstrkrtng"],
        ],
    },
    "Hunter-Beastmastery": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"],
            ["agi", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["agi", "mlecritstrkrtng", "rgdcritstrkrtng", "splcritstrkrtng"],
        ],
    },
    "DeathKnight-Unholy": {
        "mainstat": ["str"],
        "gems": [
            ["str"],
            ["str", "splhastertng", "mlehastertng", "rgdhastertng"],
            ["str", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
        ],
    },
    "DeathKnight-Blood": {
        "mainstat": ["str", "sta"],
        "gems": [
            ["mastrtng", "sta"],
            ["exprtng", "sta"],
            ["sta"],
            ["exprtng", "mastrtng"],
            ["mastrtng"],
        ],
    },
    "DeathKnight-Frost": {
        "mainstat": ["str"],
        "gems": [
            ["str"],
            ["str", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["str", "splhastertng", "mlehastertng", "rgdhastertng"],
            ["str", "mastrtng"],
        ],
    },
    "Warrior-Arms": {
        "mainstat": ["str"],
        "gems": [
            ["str"],
            ["str", "mlecritstrkrtng", "rgdcritstrkrtng", "splcritstrkrtng"],
            ["str", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
        ],
    },
    "Warrior-Fury": {
        "mainstat": ["str"],
        "gems": [
            ["str"],
            ["str", "mlecritstrkrtng", "rgdcritstrkrtng", "splcritstrkrtng"],
            ["str", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
        ],
    },
    "Warrior-Protection": {
        "mainstat": ["str", "sta"],
        "gems": [["sta"], ["sta", "mastrtng"], ["sta", "parryrtng"]],
    },
    "Warlock-Demonology": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
            ["int", "mastrtng"],
        ],
    },
    "Warlock-Affliction": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Warlock-Destruction": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Paladin-Holy": {
        "mainstat": ["int"],
        "gems": [
            ["int"],
            ["int", "spi"],
            ["int", "splhastertng", "mlehastertng", "rgdhastertng"],
        ],
    },
    "Paladin-Retribution": {
        "mainstat": ["str"],
        "gems": [
            ["str"],
            ["str", "mastrtng"],
            ["exprtng", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
            ["str", "splhitrtng", "mlehitrtng", "rgdhitrtng"],
        ],
    },
    "Paladin-Protection": {
        "mainstat": ["str", "sta"],
        "gems": [
            ["mastrtng"],
            ["sta"],
            ["mastrtng", "sta"],
            ["exprtng", "mastrtng"],
            ["exprtng", "sta"],
        ],
    },
}

roles = {
    "tank": ["Blood", "Guardian", "Protection"],
    "caster": [
        "Fire",
        "Arcane",
        "Frost",
        "Affliction",
        "Demonology",
        "Destruction",
        "Elemental",
        "Shadow",
        "Balance",
        "Restoration",
        "Holy",
        "Discipline",
    ],
    "physical": [
        "Enhancement",
        "Feral",
        "Fury",
        "Arms",
        "Assassination",
        "Combat",
        "Subtlety",
        "Unholy",
        "Frost",
        "Retribution",
        "Beastmastery",
        "Survival",
        "Marksmanship",
    ],
    "dps": [
        "Enhancement",
        "Feral",
        "Fury",
        "Arms",
        "Assassination",
        "Combat",
        "Subtlety",
        "Unholy",
        "Frost",
        "Retribution",
        "Fire",
        "Arcane",
        "Frost",
        "Affliction",
        "Demonology",
        "Destruction",
        "Elemental",
        "Shadow",
        "Balance",
        "Beastmastery",
        "Survival",
        "Marksmanship",
    ],
    "melee": [
        "Enhancement",
        "Feral",
        "Fury",
        "Arms",
        "Assassination",
        "Combat",
        "Subtlety",
        "Unholy",
        "Frost",
        "Retribution",
    ],
    "ranged": ["Beastmastery", "Survival", "Marksmanship"],
    "healer": ["Restoration", "Holy", "Discipline"],
}

class_types = {
    "strength": ["Unholy", "Frost", "Retribution", "Fury", "Arms"],
    "agility": [
        "Enhancement",
        "Feral",
        "Beastmastery",
        "Survival",
        "Marksmanship",
        "Assassination",
        "Combat",
        "Subtlety",
    ],
}

spec_stats = {"Guardian": "agility"}

item_cache = {}
with open("cataclysm/items.json", "r") as f:
    item_cache = json.load(f)
    print(f"Loaded {len(item_cache)} items from cache")

bis_items = {}
with open("cataclysm/bis_items.json", "r") as f:
    bis_items = json.load(f)
    print(f"Loaded {len(bis_items)} bis items from cache")

enchants = {}


def load_enchants():
    try:
        global enchants
        enchants = requests.get(
            "https://raw.githubusercontent.com/fuantomu/envy-armory/main/enchants.json"
        ).json()
        print(f"Loaded {sum([len(enchants[slot]) for slot in enchants])} enchants")
    except:
        print("ERROR: Could not load enchants")


load_enchants()


def check_gear(character, zone):
    print(f"Checking gear of player {character['name']}")

    if zone not in zone_itemlevel.keys():
        print(f"Zone {zone} is not valid. Defaulting to 25 player BOT/TOFW/BWD")
        zone = 1023

    output = {"minor": "", "major": "", "extreme": ""}

    if character["type"] == "Unknown":
        print(f"Error: Character type is Unknown. Skipping character")
        output["extreme"] += "Error during log import"
        return output

    sockets = {0: 0, 1: 0, 2: 0}
    professions = {
        "enchanting": {"found": 0, "items": []},
        "blacksmithing": {"found": 0, "items": []},
        "jewelcrafting": {"found": 0, "items": []},
        "tailoring": {"found": 0, "items": []},
        "engineering": {"found": 2, "items": []},
        "inscription": {"found": 0, "items": []},
        "leatherworking": {"found": 0, "items": []},
        "alchemy": {"found": 0, "items": []},
    }
    found_items = {}
    spec = character["specs"][0]
    gear = character["combatantInfo"]["gear"]
    meta = None
    for item in gear:
        found_items[item["slot"]] = item["id"]
        if item["slot"] in ignore_slots or item["id"] == 0:
            continue

        item_stats = get_wowhead_item(item["id"])
        if item_stats is None:
            continue

        item_stats["slot"] = item["slot"]
        item_stats["permanentEnchant"] = item.get("permanentEnchant")
        item_stats["permanentEnchantName"] = item.get(
            "permanentEnchantName", "Unknown name"
        )
        item_stats["onUseEnchant"] = item.get("onUseEnchant")
        item_stats["gems"] = item.get("gems", [])

        if item_stats["itemlevel"] < zone_itemlevel[zone]["min"] and item_stats[
            "id"
        ] not in bis_items.get(str(zone), []):
            output[
                "extreme"
            ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) itemlevel is < {zone_itemlevel[zone]['min']}\n"

        # Check if resilience rating on gem
        if "resirtng" in item_stats.keys():
            output[
                "major"
            ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) is a PvP item\n"

        if item_stats["slot"] not in ignore_enchant or (
            item_stats["slot"] == 17 and character["type"] == "Hunter"
        ):
            if item_stats["permanentEnchant"] is None:
                if not item_stats["slot"] in [
                    10,
                    11,
                ]:  # if ring, ignore the no enchant rule
                    output[
                        "extreme"
                    ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) missing enchant\n"
                else:
                    professions["enchanting"]["items"].append(item_stats)

                if item_stats["slot"] == 14:
                    professions["tailoring"]["items"].append(item_stats)
                elif item_stats["slot"] == 6:
                    professions["leatherworking"]["items"].append(item_stats)
                    professions["tailoring"]["items"].append(item_stats)
            else:
                found_enchant = False
                for enchant in enchants[str(item_stats["slot"])]:
                    if enchant["id"] == item_stats["permanentEnchant"]:

                        found_enchant = True
                        if enchant["tier"] >= 2:
                            if item_stats["itemlevel"] >= zone_itemlevel[zone]["max"]:
                                output[
                                    "extreme"
                                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) itemlevel is {zone_itemlevel[zone]['max']} or higher and has a very low level enchant: {enchant['name']}\n"
                            else:
                                output[
                                    "major"
                                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has a very low level enchant: {enchant['name']}\n"
                        if enchant["tier"] == 1:
                            if item_stats["itemlevel"] == zone_itemlevel[zone]["max"]:
                                output[
                                    "major"
                                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) itemlevel is {zone_itemlevel[zone]['max']} and has a low level enchant: {enchant['name']}\n"
                            else:
                                output[
                                    "minor"
                                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has a low level enchant: {enchant['name']}\n"

                        unsuited_enchant_found = False
                        if enchant.get("role") is not None:
                            if spec not in roles[
                                enchant["role"]
                            ] and spec != enchant.get("spec"):
                                unsuited_enchant_found = True
                                output[
                                    "minor"
                                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has an enchant that is not suited for their role ({spec}): {enchant['name']} ({enchant['role']})\n"
                        if (
                            enchant.get("type") is not None
                            and not unsuited_enchant_found
                        ):
                            if (
                                spec not in class_types[enchant["type"]]
                                and spec != enchant.get("spec")
                                and spec_stats.get(spec) != enchant.get("type")
                            ):
                                output[
                                    "minor"
                                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has an enchant that is not suited for their type ({spec}): {enchant['name']} ({enchant['type']})\n"

                        # Check if ring has enchant
                        if item_stats["slot"] in [10, 11]:
                            professions["enchanting"]["found"] += 1

                        # Check if tailoring/leatherworking leg enchant exists
                        if item_stats["slot"] == 6:
                            if enchant["id"] in [4439, 4440]:
                                professions["leatherworking"]["found"] += 1
                            else:
                                professions["leatherworking"]["items"].append(
                                    item_stats
                                )
                            if enchant["id"] in [4113, 4114]:
                                professions["tailoring"]["found"] += 1
                            else:
                                professions["tailoring"]["items"].append(item_stats)
                        # Check if leatherworking bracer enchant exists
                        if item_stats["slot"] == 8:
                            if enchant["id"] in [4189, 4190, 4191, 4192]:
                                professions["leatherworking"]["found"] += 1
                            else:
                                professions["leatherworking"]["items"].append(
                                    item_stats
                                )
                        # Check if inscription shoulder enchant exists
                        if item_stats["slot"] == 2:
                            if enchant["id"] in [4193, 4194, 4195, 4196]:
                                professions["inscription"]["found"] += 1
                            else:
                                professions["inscription"]["items"].append(item_stats)
                        # Check if tailoring cloak enchant exist
                        if item_stats["slot"] == 14:
                            if enchant["id"] in [4115, 4116, 4118]:
                                # If class main stat is agility/strength, ignore tailoring leg enchant
                                if (
                                    spec in class_types["agility"]
                                    or spec in class_types["strength"]
                                ):
                                    professions["tailoring"]["found"] += 2
                                else:
                                    professions["tailoring"]["found"] += 1
                            else:
                                professions["tailoring"]["items"].append(item_stats)

                # If enchants are used that are not registered in the cache, extract the id and name
                if not found_enchant:
                    output[
                        "extreme"
                    ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has an incorrect enchant (Unknown enchant or low level)\n"
                    with open(f"unknown_enchants", "a") as f:
                        f.write(
                            f"\n{character.get('name')} - {slots[item_stats['slot']]}\n"
                        )
                        f.write(
                            f'{str(item_stats["permanentEnchant"])} - {str(item_stats["permanentEnchantName"])}'
                        )

        if item_stats["slot"] == 5 and item.get("onUseEnchant") != 4223:  # Nitro Boosts
            item_stats["missing"] = "Nitro Boosts"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item_stats)
        if (
            item_stats["slot"] == 9
            and item.get("onUseEnchant") != 4179
            and spec not in ["Guardian", "Blood", "Protection"]
        ):  # Synapse Springs
            item_stats["missing"] = "Synapse Springs"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item_stats)
        elif (
            item_stats["slot"] == 9
            and item.get("onUseEnchant") not in [4179, 4180]
            and spec in ["Guardian", "Blood", "Protection"]
        ):  # Quickflip Deflection Plates
            item_stats["missing"] = "Quickflip Deflection Plates"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item_stats)

        # Check if socket amount in belt is higher than base socket amount in item
        if (
            item_stats["slot"] == 5
            and len(item.get("gems", [])) < item_stats.get("nsockets", 0) + 1
        ):
            output[
                "extreme"
            ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) missing a belt buckle\n"

        for gem in item_stats["gems"]:
            gem_stats = get_wowhead_item(gem["id"])
            if gem_stats["itemlevel"] < 85:
                output[
                    "major"
                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has a low level gem ({gem_stats['name']})\n"

            if "meta" in gem_stats.keys():
                meta = gem_stats
                continue

            # if gem requires jewelcrafting
            if gem_stats.get("reqskill") == 755:
                professions["jewelcrafting"]["found"] += 1
                existing_item = [
                    found_item
                    for found_item in professions["jewelcrafting"]["items"]
                    if found_item["id"] == item_stats["id"]
                ]
                if len(existing_item) == 0:
                    professions["jewelcrafting"]["items"].append(item_stats)

            # Ignore cogwheel and meta gems
            if gem_stats["subclass"] not in [6, 10]:
                total_attributes = []
                # Get all gem attributes
                for attr in gem_attributes:
                    if gem_stats.get(attr) is not None:
                        total_attributes.append(attr)
                # Check if gem is a useful stat
                if not any(
                    [
                        all([attr in spec_atr for attr in total_attributes])
                        for spec_atr in spec_attributes[f"{character['type']}-{spec}"][
                            "gems"
                        ]
                    ]
                ):
                    if not any(
                        [
                            attr
                            in spec_attributes[f"{character['type']}-{spec}"][
                                "mainstat"
                            ]
                            for attr in total_attributes
                        ]
                    ):
                        output[
                            "major"
                        ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has a gem that is not their primary stat ({gem_stats['name']})\n"
                    else:
                        attribute_string = " & ".join(
                            set(
                                [
                                    attribute_locale.get(attr)
                                    for attr in total_attributes
                                ]
                            )
                        )
                        output[
                            "minor"
                        ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has a non-optimal gem ({attribute_string})\n"
                # Add color of gem to total sockets
                for color in gem_class[gem_stats["subclass"]]:
                    sockets[color] += 1
            # Check if resilience rating on gem
            if "resirtng" in gem_stats.keys():
                output[
                    "major"
                ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has a PvP gem ({gem_stats['name']})\n"

        # Check if socketed gem amount is equal to socket amount in item
        if len(item_stats["gems"]) < item_stats.get("nsockets", 0):
            output[
                "extreme"
            ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) has {item_stats['nsockets']-len(item_stats['gems'])} empty socket(s)\n"

        # Find blacksmithing sockets in bracers/gloves
        if item_stats["slot"] in [8, 9]:
            if len(item_stats["gems"]) > item_stats.get("nsockets", 0):
                professions["blacksmithing"]["found"] += 1
            else:
                professions["blacksmithing"]["items"].append(item_stats)

        # Find alchemy trinket
        if item_stats["slot"] in [12, 13]:
            if item_stats["id"] in [58483, 68775, 68776, 68777]:
                professions["alchemy"]["found"] += 1

        # Check for incorrect armor type
        if (
            item_stats["slot"] in [0, 2, 4, 5, 6, 7, 8, 9]
            and item_stats["subclass"] != armor_type[character["type"]]
        ):
            output[
                "extreme"
            ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) is not the correct armor type ({locale_armor_type[item_stats['subclass']]})\n"

        item_primary_attribute = None
        # Get all item attributes
        for attr in main_attributes:
            if item_stats.get(attr) is not None:
                item_primary_attribute = attr
                break
        # Check for incorrect primary stat
        if item_primary_attribute and all(
            [
                attr not in item_primary_attribute
                for attr in spec_attributes[f"{character['type']}-{spec}"]["mainstat"]
            ]
        ):
            output[
                "extreme"
            ] += f"{item_stats['name']} ({slots[item_stats['slot']]}) is not the correct primary stat ({attribute_locale[item_primary_attribute]})\n"

    total_professions = [
        profession[0].capitalize()
        for profession in professions.items()
        if profession[1]["found"] > 0
    ]
    for profession in professions.items():
        if profession[1]["found"] > 0:
            if profession[0] == "enchanting" and profession[1]["found"] < 2:
                archaeology_ring = [
                    other_finger for other_finger in gear if other_finger["id"] == 64904
                ]
                if len(archaeology_ring) == 0:
                    output[
                        "major"
                    ] += f"{profession[1]['items'][0]['name']} ({slots[profession[1]['items'][0]['slot']]}) missing enchanting-specific enchant\n"
            if profession[0] == "blacksmithing" and profession[1]["found"] < 2:
                output[
                    "major"
                ] += f"{profession[1]['items'][0]['name']} ({slots[profession[1]['items'][0]['slot']]}) missing blacksmithing socket\n"
            if profession[0] == "jewelcrafting" and profession[1]["found"] < 3:
                item_text = ",".join(
                    [
                        f"{found_item['name']} ({slots[found_item['slot']]})"
                        for found_item in profession[1]["items"]
                    ]
                )
                output[
                    "major"
                ] += f"Gear missing {3-profession[1]['found']} jewelcrafting gem(s) (only found gem(s) in {item_text})\n"
            if profession[0] == "engineering" and profession[1]["found"] < 2:
                output["major"] += ",".join(
                    [
                        f"{found_item['name']} ({slots[found_item['slot']]}) missing engineering enchant: {found_item['missing']}\n"
                        for found_item in profession[1]["items"]
                    ]
                )
            if profession[0] == "leatherworking" and profession[1]["found"] < 2:
                other_leg_enchant = [
                    other_enchant
                    for other_enchant in profession[1]["items"]
                    if other_enchant.get("permanentEnchant") in [4127, 4126, 4270]
                    or (
                        other_enchant.get("permanentEnchant")
                        in [4109, 4110, 4111, 4112, 4113, 4114]
                        and spec in roles["caster"]
                    )
                ]
                if len(other_leg_enchant) == 0:
                    try:
                        output[
                            "major"
                        ] += f"{profession[1]['items'][0]['name']} ({slots[profession[1]['items'][0]['slot']]}) missing leatherworking enchant\n"
                    except:
                        output["major"] += f"Missing Cloak/Leg leatherworking enchant\n"

            if profession[0] == "tailoring" and profession[1]["found"] < 2:
                other_leg_enchant = [
                    other_enchant
                    for other_enchant in profession[1]["items"]
                    if other_enchant.get("permanentEnchant") in [4110, 4112]
                    or (
                        other_enchant.get("permanentEnchant")
                        in [4122, 4124, 4126, 4127, 4126, 4270, 4438, 4439, 4440]
                        and (spec in roles["physical"] or spec in roles["tank"])
                    )
                ]
                if len(other_leg_enchant) == 0:
                    try:
                        output[
                            "major"
                        ] += f"{profession[1]['items'][0]['name']} ({slots[profession[1]['items'][0]['slot']]}) missing tailoring enchant\n"
                    except:
                        output["major"] += f"Missing Cloak/Leg tailoring enchant\n"

    if len(total_professions) == 1:
        output[
            "extreme"
        ] += f"Only one primary profession bonus found: {','.join(total_professions)}\n"
    elif len(total_professions) == 0:
        output["extreme"] += f"No primary profession bonus found\n"

    if meta is None:
        output["extreme"] += f"No meta gem\n"
    else:
        if any([sockets[int(k)] < v for k, v in meta["meta"].items()]):
            output["extreme"] += f"Meta gem is not active!\n"

    for item, id in found_items.items():
        if item in ignore_slots:
            continue
        if id == 0:
            if item == 16 and found_items[15] != 0:
                continue
            output["extreme"] += f"Missing item in {slots[item]}\n"

    with open("cataclysm/items.json", "w") as f:
        json.dump(item_cache, f)

    return output


def get_wowhead_item(id):
    if item_cache.get(str(id)) is None:
        print(f"Requesting item {id} from wowhead")
        wowhead_response = requests.get(wowhead_link.replace("ITEMID", str(id)))

        try:
            parsed_xml = xmltodict.parse(wowhead_response.content)
        except:
            print(f"Error parsing item {id}")
            return None

        parsed_item = ast.literal_eval(
            "{ " + parsed_xml["wowhead"]["item"]["jsonEquip"] + " }"
        )
        parsed_item["id"] = parsed_xml["wowhead"]["item"]["@id"]
        parsed_item["name"] = parsed_xml["wowhead"]["item"]["name"]
        parsed_item["itemlevel"] = int(parsed_xml["wowhead"]["item"]["level"])
        parsed_item["quality"] = int(parsed_xml["wowhead"]["item"]["quality"]["@id"])
        parsed_item["class"] = int(parsed_xml["wowhead"]["item"]["class"]["@id"])
        parsed_item["subclass"] = int(parsed_xml["wowhead"]["item"]["subclass"]["@id"])

        # if item is gem, parse html data for meta requirements
        if parsed_item["class"] == 3 and parsed_item["subclass"] == 6:
            parsed_item["meta"] = {}

            requirements = re.findall(
                r'<div class="q0">(.*?)<\/div>',
                parsed_xml["wowhead"]["item"]["htmlTooltip"],
            )[0].split("<br />")
            for entry in requirements:
                if "Red" in entry:
                    parsed_item["meta"][0] = int(re.findall(r"([0-9])", entry)[0])
                elif "Blue" in entry:
                    parsed_item["meta"][1] = int(re.findall(r"([0-9])", entry)[0])
                elif "Yellow" in entry:
                    parsed_item["meta"][2] = int(re.findall(r"([0-9])", entry)[0])
        item_cache[str(id)] = parsed_item
    return item_cache[str(id)]
