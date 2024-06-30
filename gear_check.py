import requests
import xmltodict
import ast
import re
import json

slots = {
    0 : "Helmet",
    1 : "Neck",
    2 : "Shoulder",
    3 : "Shirt",
    4 : "Chest",
    5 : "Belt",
    6 : "Pants",
    7 : "Boots",
    8 : "Bracers",
    9 : "Gloves",
    10 : "Finger 1",
    11 : "Finger 2",
    12 : "Trinket 1",
    13 : "Trinket 2",
    14 : "Cloak",
    15 : "Mainhand",
    16 : "Offhand",
    17 : "Ranged/Relic",
    18 : "Tabard"
}

ignore_slots = [3,18]

ignore_enchant = [1,5,12,13,17]

wowhead_link = 'https://www.wowhead.com/cata/item=ITEMID?xml'

zone_itemlevel = {
    1023: { # 25-player BWD/TOFW/BOT
        "min": 346,  
        "max": 372
    },
    1024: { # 10-player BWD/TOFW/BOT
        "min": 346,  
        "max": 372
    }
}

gem_class = {
    0: [0], # Red
    1: [1], # Blue
    2: [2], # Yellow
    3: [0,1], # Purple
    4: [1,2], # Green
    5: [0,2] # Orange
}

roles = {
    "tank": ["Blood","Guardian","Protection"],
    "caster": ["Fire","Arcane","Frost","Affliction","Demonology","Destruction","Elemental","Shadow","Balance","Restoration","Holy","Discipline"],
    "physical": ["Enhancement","Feral","Fury","Arms","Assassination","Combat","Subtlety","Unholy","Frost","Retribution","Beastmastery","Survival","Marksmanship"],
    "dps": ["Enhancement","Feral","Fury","Arms","Assassination","Combat","Subtlety","Unholy","Frost","Retribution","Fire","Arcane","Frost","Affliction","Demonology","Destruction","Elemental","Shadow","Balance","Beastmastery","Survival","Marksmanship"],
    "melee": ["Enhancement","Feral","Fury","Arms","Assassination","Combat","Subtlety","Unholy","Frost","Retribution"],
    "ranged": ["Beastmastery","Survival","Marksmanship"],
    "healer": ["Restoration","Holy","Discipline"]
}

class_types = {
    "strength": ["Unholy","Frost","Retribution","Fury","Arms"],
    "agility": ["Enhancement","Feral","Beastmastery","Survival","Marksmanship","Assassination","Combat","Subtlety"]
}

spec_stats = {
    "Guardian": "agility"
}


item_cache = {}
with open("cataclysm/items.json", "r") as f:
    item_cache = json.load(f)
    print(f"Loaded {len(item_cache)} items from cache")

enchants = {}
def load_enchants():
    try:
        global enchants
        enchants = requests.get('https://raw.githubusercontent.com/fuantomu/envy-armory/main/enchants.json').json()
        print(f"Loaded {sum([len(enchants[slot]) for slot in enchants])} enchants")
    except:
        print("ERROR: Could not load enchants")
load_enchants()

def check_gear(character, zone):
    print(f"Checking gear of player {character['name']}")
    output = {
        "minor": "",
        "major": "",
        "extreme": ""
    }
    sockets = {0:0,1:0,2:0}
    professions = {
        "enchanting": {"found": 0, "items": []}, 
        "blacksmithing": {"found": 0, "items": []}, 
        "jewelcrafting": {"found": 0, "items": []}, 
        "tailoring": {"found": 0, "items": []}, 
        "engineering": {"found": 2, "items": []}, 
        "inscription": {"found": 0, "items": []}, 
        "leatherworking": {"found": 0, "items": []}, 
        "alchemy": {"found": 0, "items": []}
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
        
        if item["itemLevel"] < zone_itemlevel[zone]["min"]:
            output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) itemlevel is < {zone_itemlevel[zone]['min']}\n"
        
        # Check if resilience rating on gem
        if "resirtng" in item_stats.keys():
            output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) is a PvP item\n"
        
        if item["slot"] not in ignore_enchant:
            if item.get("permanentEnchant") is None: 
                if not item["slot"] in [10,11]: # if ring, ignore the no enchant rule
                    output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) missing enchant\n"
                else:
                    professions["enchanting"]["items"].append(item)
                    
                if item["slot"] == 14:
                    professions["tailoring"]["items"].append(item)
                elif item["slot"] == 6:
                    professions["leatherworking"]["items"].append(item)
                    professions["tailoring"]["items"].append(item)
            else:
                found_enchant = False
                for enchant in enchants[str(item["slot"])]:
                    if enchant["id"] == item["permanentEnchant"]:
                        
                        found_enchant = True
                        if enchant["tier"] >= 2:
                            if item["itemLevel"] >= zone_itemlevel[zone]["max"]:
                                output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) itemlevel is {zone_itemlevel[zone]['max']} or higher and has a very low level enchant: {enchant['name']}\n"
                            else:
                                output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) has a very low level enchant: {enchant['name']}\n"
                        if enchant["tier"] == 1:
                            if item["itemLevel"] == zone_itemlevel[zone]["max"]:
                                output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) itemlevel is {zone_itemlevel[zone]['max']} and has a low level enchant: {enchant['name']}\n"
                            else:
                                output["minor"] += f"{item.get('name', '')} ({slots[item['slot']]}) has a low level enchant: {enchant['name']}\n"
                        
                        unsuited_enchant_found = False
                        if enchant.get("role") is not None:
                            if spec not in roles[enchant["role"]] and spec != enchant.get("spec"):
                                unsuited_enchant_found = True
                                output["minor"] += f"{item.get('name', '')} ({slots[item['slot']]}) has an enchant that is not suited for their role ({spec}): {enchant['name']} ({enchant['role']})\n"
                        if enchant.get("type") is not None and not unsuited_enchant_found:
                            if spec not in class_types[enchant["type"]] and spec != enchant.get("spec") and spec_stats.get(spec) != enchant.get("type"):
                                output["minor"] += f"{item.get('name', '')} ({slots[item['slot']]}) has an enchant that is not suited for their type ({spec}): {enchant['name']} ({enchant['type']})\n"
                        
                        # Check if ring has enchant
                        if item["slot"] in [10,11]:
                            professions["enchanting"]["found"] += 1
                        
                        # Check if tailoring/leatherworking leg enchant exists
                        if item["slot"] == 6:
                            if enchant["id"] in [4439,4440]:
                                professions["leatherworking"]["found"] += 1
                            else:
                                professions["leatherworking"]["items"].append(item)
                            if enchant["id"] in [4113,4114]:
                                professions["tailoring"]["found"] += 1
                            else:
                                professions["tailoring"]["items"].append(item)
                        # Check if leatherworking bracer enchant exists
                        if item["slot"] == 8:
                            if enchant["id"] in [4189,4190,4191,4192]:
                                professions["leatherworking"]["found"] += 1
                            else:
                                professions["leatherworking"]["items"].append(item)
                        # Check if inscription shoulder enchant exists
                        if item["slot"] == 2:
                            if enchant["id"] in [4193,4194,4195,4196]:
                                professions["inscription"]["found"] += 1
                            else:
                                professions["inscription"]["items"].append(item)
                        # Check if tailoring cloak enchant exist
                        if item["slot"] == 14:
                            if enchant["id"] in [4115,4116,4118]:
                                # If class main stat is agility/strength, ignore tailoring leg enchant
                                if spec in class_types["agility"] or spec in class_types["strength"]:
                                    professions["tailoring"]["found"] += 2
                                else:
                                    professions["tailoring"]["found"] += 1
                            else:
                                professions["tailoring"]["items"].append(item)
                
                # If enchants are used that are not registered in the cache, extract the id and name
                if not found_enchant:
                    output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) has an incorrect enchant (Unknown enchant or low level)\n"
                    with open(f"unknown_enchants","a") as f:
                        f.write(f"\n{slots[item['slot']]}\n")
                        f.write(f'{str(item["permanentEnchant"])} - {str(item.get("permanentEnchantName", "Unknown name"))}')
                
            
        if item["slot"] == 5 and item.get("onUseEnchant") != 4223: # Nitro Boosts
            item["missing"] = "Nitro Boosts"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item)
        if item["slot"] == 9 and item.get("onUseEnchant") != 4179 and spec not in ["Guardian","Blood","Protection"] : # Synapse Springs
            item["missing"] = "Synapse Springs"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item)
        elif item["slot"] == 9 and item.get("onUseEnchant") not in [4179,4180] and spec in ["Guardian","Blood","Protection"] : # Quickflip Deflection Plates
            item["missing"] = "Quickflip Deflection Plates"
            professions["engineering"]["found"] -= 1
            professions["engineering"]["items"].append(item)

        # Check if socket amount in belt is higher than base socket amount in item
        if item["slot"] == 5 and len(item.get("gems", [])) < item_stats.get("nsockets", 0)+1:
            output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) missing a belt buckle\n"
        
        if item.get("gems") is not None:
            if any([gem["itemLevel"] < 85 for gem in item["gems"]]):
                output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) has a low level gem\n"
            for gem in item["gems"]:
                gem_stats = get_wowhead_item(gem["id"])
                if "meta" in gem_stats.keys():
                    meta = gem_stats
                    continue
                
                if "dragonseye" in gem["icon"]:
                    professions["jewelcrafting"]["found"] += 1
                    existing_item = [found_item for found_item in professions["jewelcrafting"]["items"] if found_item["id"] == item["id"]]
                    if len(existing_item) == 0:
                        professions["jewelcrafting"]["items"].append(item)
                
                # Only add actual colored gems
                if gem_stats["color"] != 10 :
                    for color in gem_class[gem_stats["color"]]:
                        sockets[color] += 1
                # Check if resilience rating on gem
                if "resirtng" in gem_stats.keys():
                    output["major"] += f"{item.get('name', '')} ({slots[item['slot']]}) has a PvP gem\n"

        # Check if socketed gem amount is equal to socket amount in item
        if len(item.get("gems", [])) < item_stats.get("nsockets", 0):
            output["extreme"] += f"{item.get('name', '')} ({slots[item['slot']]}) has {item_stats['nsockets']-len(item.get('gems', []))} empty socket(s)\n"
        
        # Find blacksmithing sockets in bracers/gloves
        if item["slot"] in [8,9]:
            if len(item.get("gems", [])) > item_stats.get("nsockets", 0):
                professions["blacksmithing"]["found"] +=1
            else:
                professions["blacksmithing"]["items"].append(item)
        
        # Find alchemy trinket
        if item["slot"] in [12,13]:
            if item["id"] in [58483,68775,68776,68777]:
                professions["alchemy"]["found"] +=1

    total_professions = [profession[0].capitalize() for profession in professions.items() if profession[1]["found"] > 0]
    for profession in professions.items():
        if profession[1]['found'] > 0:
            if profession[0] == "enchanting" and profession[1]['found'] < 2:
                archaeology_ring = [other_finger for other_finger in gear if other_finger["id"] == 64904]
                if len(archaeology_ring) == 0:
                    output["major"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing enchanting-specific enchant\n"
            if profession[0] == "blacksmithing" and profession[1]['found'] < 2:
                output["major"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing blacksmithing socket\n"
            if profession[0] == "jewelcrafting" and profession[1]['found'] < 3:
                item_text = ','.join([f"{found_item.get('name', '')} ({slots[found_item['slot']]})" for found_item in profession[1]['items']])
                output["major"] += f"Gear missing {3-profession[1]['found']} jewelcrafting gem(s) (only found gem(s) in {item_text})\n"
            if profession[0] == "engineering" and profession[1]['found'] < 2:
                output["major"] += ','.join([f"{found_item.get('name', '')} ({slots[found_item['slot']]}) missing engineering enchant: {found_item['missing']}\n" for found_item in profession[1]['items']])
            if profession[0] == "leatherworking" and profession[1]['found'] < 2:
                other_leg_enchant = [other_enchant for other_enchant in profession[1]['items'] if other_enchant.get("permanentEnchant") in [4127,4126,4270] or (other_enchant.get("permanentEnchant") in [4109,4110,4111,4112,4113,4114] and spec in roles["caster"])]
                if len(other_leg_enchant) == 0:
                    try:
                        output["major"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing leatherworking enchant\n"
                    except:
                        output["major"] += f"Missing Cloak/Leg leatherworking enchant\n"
                    
            if profession[0] == "tailoring" and profession[1]['found'] < 2:
                other_leg_enchant = [other_enchant for other_enchant in profession[1]['items'] if other_enchant.get("permanentEnchant") in [4110,4112] or (other_enchant.get("permanentEnchant") in [4122,4124,4126,4127,4126,4270,4439,4440] and spec in roles["physical"])]
                if len(other_leg_enchant) == 0:
                    try:
                        output["major"] += f"{profession[1]['items'][0].get('name', '')} ({slots[profession[1]['items'][0]['slot']]}) missing tailoring enchant\n"
                    except:
                        output["major"] += f"Missing Cloak/Leg tailoring enchant\n"
                    
    
    if len(total_professions) == 1:
        output["extreme"] += f"Only one primary profession bonus found: {','.join(total_professions)}\n"
    elif len(total_professions) == 0:
        output["extreme"] += f"No primary profession bonus found\n"

    if meta is None:
        output["extreme"] += f"No meta gem\n"
    else:
        if any([sockets[int(k)] < v for k,v in meta["meta"].items()]):
            output["extreme"] += f"Meta gem is not active!\n"
    
    for item,id in found_items.items():
        if item in ignore_slots:
            continue
        if id == 0:
            if item == 16 and found_items[15] != 0:
                continue
            output["extreme"] += f"Missing item item in {slots[item]}"
            
    with open("cataclysm/items.json", "w") as f:
        json.dump(item_cache, f)

    return output

def get_wowhead_item(id):
    if item_cache.get(str(id)) is None:
        print(f"Requesting item {id} from wowhead")
        wowhead_response = requests.get(wowhead_link.replace("ITEMID", str(id)))
        parsed_xml = xmltodict.parse(wowhead_response.content)
        
        parsed_item = ast.literal_eval("{ " + parsed_xml["wowhead"]["item"]["jsonEquip"] + " }")
        if parsed_xml["wowhead"]["item"]["class"]['#text'] == "Gems":
            # if item is gem, parse html data for meta requirements
            if parsed_xml["wowhead"]["item"]["subclass"]['#text'] == "Meta Gems":
                parsed_item["meta"] = {}

                requirements = re.findall(r'<div class="q0">(.*?)<\/div>', parsed_xml["wowhead"]["item"]["htmlTooltip"])[0].split("<br />")
                for entry in requirements:
                    if "Red" in entry:
                        parsed_item["meta"][0] = int(re.findall(r'([0-9])', entry)[0])
                    elif "Blue" in entry:
                        parsed_item["meta"][1] = int(re.findall(r'([0-9])', entry)[0])
                    elif "Yellow" in entry:
                        parsed_item["meta"][2] = int(re.findall(r'([0-9])', entry)[0])
            else:
                parsed_item["color"] = int(parsed_xml["wowhead"]["item"]["subclass"]['@id'])
        item_cache[str(id)] = parsed_item
    return item_cache[str(id)]