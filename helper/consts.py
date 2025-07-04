zones = {
    1023: {"version": "cataclysm", "min": 346, "max": 372, "gem_primary_min": 40, "gem_secondary_min": 20},  # 25-player BWD/TOFW/BOT
    1024: {"version": "cataclysm", "min": 346, "max": 372, "gem_primary_min": 40, "gem_secondary_min": 20},  # 10-player BWD/TOFW/BOT
    1027: {"version": "cataclysm", "min": 372, "max": 391, "gem_primary_min": 40, "gem_secondary_min": 20},  # Firelands
    1033: {"version": "cataclysm", "min": 384, "max": 410, "gem_primary_min": 40, "gem_secondary_min": 20, "gem_primary_max": 50, "gem_secondary_max": 25}   # Dragon Soul
}

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

main_attributes = ["int", "str", "agi", "spi", "sta"]

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
    "Monk": 2
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
    "Hunter-BeastMastery": {
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
    "Monk-Brewmaster": {
        "mainstat": ["agi", "sta"],
        "gems": [
            ["sta"]
        ]
    },
    "Monk-Windwalker": {
        "mainstat": ["agi"],
        "gems": [
            ["agi"]
        ]
    },
    "Monk-Mistweaver": {
        "mainstat": ["int"],
        "gems": [
            ["int"]
        ]
    }
}

roles = {
    "tank": ["Blood", "Guardian", "Protection", "Brewmaster"],
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
        "Windwalker"
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
        "Windwalker"
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
        "Windwalker"
    ],
    "ranged": ["Beastmastery", "Survival", "Marksmanship"],
    "healer": ["Restoration", "Holy", "Discipline", "Mistweaver"],
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
        "Windwalker"
    ],
}

spec_stats = {"Guardian": "agility"}

def get_leatherworking_enchants(version: str)-> dict:
    match version:
        case "cataclysm":
            return {
                "legs": [4439, 4440],
                "wrists": [4189, 4190, 4191, 4192]
            }
        case "mop":
            return {
                "legs": [4881,4882,4880],
                "wrists": [4875,4879,4878,4877]
            }
        case _:
            return {
                "legs": [],
                "wrists": []
            }
        
def get_tailoring_enchants(version: str) -> dict:
    match version:
        case "cataclysm":
            return {
                "legs": [4113, 4114],
                "cloak": [4115, 4116, 4118]
            }
        case "mop":
            return {
                "legs": [4896,4895],
                "cloak": [4893,4892,4894]
            }
        case _:
            return {
                "legs": [],
                "cloak": []
            }
        
def get_inscription_enchants(version: str)-> dict:
    match version:
        case "cataclysm":
            return {
                "shoulders": [4193, 4194, 4195, 4196]
            }
        case "mop":
            return {
                "shoulders": [4915,4912,4914,4913]
            }
        case _:
            return {
                "shoulders": []
            }
        
def get_alchemy_trinket(version: str) -> list:
    match version:
        case "cataclysm": return [58483, 68775, 68776, 68777]
        case "mop": return [75274]
        case _: return []

def get_leg_enchants(version: str)-> dict:
    match version:
        case "cataclysm": return {
            "leatherworking": [4127, 4126, 4270], # leatherworking created enchants
            "caster": [4109, 4110, 4111, 4112, 4113, 4114], # all existing caster enchants
            "tailoring": [4110, 4112], # tailoring created enchants
            "physical": [4122, 4124, 4126, 4127, 4126, 4270, 4438, 4439, 4440] # all existing physical enchants
        }
        case "mop": return {
            "leatherworking": [4823,4824,4822],
            "caster": [4825, 4826,5003, 5004, 4896, 4895],
            "tailoring": [4825, 4826],
            "physical": [4823,4824,4822,4881,4882,4880,4872,4871,4870]
        }
        case _: return {
            "physical": [],
            "caster": []
        }