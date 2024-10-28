import json
from helper.log import get_log_events
from helper.mapper import hostility, playerType

# encounter_cache = {}


def check_encounter(report, fight):
    # print(fight)
    checks = get_encounter_check(fight["zoneName"], fight["name"])

    if len(checks) == 0:
        return [], {}, {}, {}
    # print(checks)
    enemies = get_encounter_enemies(
        report, fight["start_time"], fight["end_time"], checks
    )
    # print(enemies)

    abilities = get_encounter_abilities(report, fight["end_time"], checks)

    interrupts = get_encounter_interrupts(report, fight["end_time"], checks)

    activity = []
    for check in checks:
        # print(check)
        args = {
            "start": fight["start_time"] + check["start"] * 1000,
            "end": (
                fight["end_time"]
                if check["end"] == -1
                else fight["start_time"] + check["end"] * 1000
            ),
            "event-type": check["event-type"],
            "hostility": hostility.get(check["hostility"], "0"),
            "by": check.get("by", "source"),
            "abilityid": check.get("ability-id", None),
            "options": check.get("options", "0"),
        }

        target = {"type": None, "data": None}

        if args["by"] == "ability":
            args.pop("by")
            events = get_log_events(report, **args)
            target["type"] = "Ability"
        elif args["event-type"] == "interrupts":
            # print(abilities)
            args.pop("by")
            events = get_log_events(report, **args)["entries"][0]["entries"]
            target["type"] = "Interrupt"
        else:
            target["data"] = find_enemy_by_guid(enemies, check["target-id"])
            target["type"] = "Enemy"
            args["targetid"] = target["data"]["enemyId"]
            events = get_log_events(report, **args)

        update_event_data(events, check, target, activity)

    conditions = get_encounter_conditions(fight["zoneName"], fight["name"])
    for player in activity:
        # print(player.keys())
        # print(player)
        for condition in conditions:
            check_conditions(player, condition)
        # print(player)
    return activity, enemies, abilities, interrupts


def get_encounter_check(zone, encounter):
    try:
        zone = zone.replace(" ", "_")
        encounter = encounter.replace(" ", "_")
        with open(f"cataclysm/{zone}/{encounter}/mechanics.json", "r") as f:
            mechanics = json.load(f)
        return mechanics
    except FileNotFoundError as e:
        print(f"Mechanics file for Boss '{encounter}' in '{zone}' does not exist")
    except Exception as e:
        print(e)
    return {}


def get_encounter_conditions(zone, encounter):
    try:
        zone = zone.replace(" ", "_")
        encounter = encounter.replace(" ", "_")
        with open(f"cataclysm/{zone}/{encounter}/conditions.json", "r") as f:
            mechanics = json.load(f)
        return mechanics
    except FileNotFoundError as e:
        print(f"Condition file for Boss '{encounter}' in '{zone}' does not exist")
    except Exception as e:
        print(e)
    return {}


def get_encounter_enemies(report, start, end, checks):
    entities = {}
    args = {"start": start, "end": end, "event-type": "damage-taken", "hostility": 1}
    events = get_log_events(report, **args)
    check_enemies = [
        entry.get("target-id")
        for entry in checks
        if entry["event-type"] in ["damage-done", "damage-taken"]
    ]
    # print(check_enemies)

    for enemy in events.get("entries"):
        if enemy["guid"] not in check_enemies:
            continue

        entities[enemy["id"]] = {
            "enemyName": enemy["name"],
            "enemyId": enemy["id"],
            "enemyGuid": enemy["guid"],
            "abilities": [],
        }
        for check in checks:
            if check.get("target-id") == enemy["guid"]:
                entities[enemy["id"]]["start"] = check["start"]
                entities[enemy["id"]]["end"] = check["end"]
    # print(f"enemies: {entities}")
    return entities


def get_encounter_abilities(report, end, checks):
    entities = {}
    args = {
        "start": 0,
        "end": end,
        "event-type": "damage-done",
        "hostility": 1,
        "by": "ability",
    }
    events = get_log_events(report, **args)
    check_abilites = [entry.get("ability-id") for entry in checks if "by" in entry]
    # print(events)

    for ability in events.get("entries"):
        # print(ability)
        if ability["guid"] not in check_abilites:
            continue

        entities[ability["guid"]] = {
            "abilityName": ability["name"],
            "abilityGuid": ability["guid"],
        }
    # print(f"abilities: {entities}")
    return entities


def get_encounter_interrupts(report, end, checks):
    entities = {}
    args = {
        "start": 0,
        "end": end,
        "event-type": "interrupts",
        "hostility": 0,
    }
    events = get_log_events(report, **args)["entries"][0]
    # print(events)
    check_interrupts = [entry.get("ability-id") for entry in checks]
    # print(events)

    for interrupt in events.get("entries"):
        # print(ability)
        if interrupt["guid"] not in check_interrupts:
            continue

        # print(interrupt)
        entities[interrupt["guid"]] = {
            "interruptName": interrupt["name"],
            "interruptGuid": interrupt["guid"],
            "spellsCompleted": interrupt["spellsCompleted"],
            "spellsInterrupted": interrupt["spellsInterrupted"],
        }
    # print(f"interrupts: {entities}")
    return entities


def find_enemy_by_guid(enemies, guid) -> dict:
    for enemy in enemies.values():
        if enemy.get("enemyGuid") == guid:
            return enemy
    return {}


def update_event_data(events, check, target, data):

    if target["type"] == "Interrupt":
        entries = events[0].get("details", [])
    else:
        entries = events.get("entries", [])
    for playerEntry in entries:

        if playerEntry["type"] not in playerType:
            continue
        player = None
        index = None
        for idx, entry in enumerate(data):
            if entry.get("playerName") == playerEntry["name"]:
                player = entry
                index = idx
                break
        if player is None:
            player = {
                "playerType": playerEntry["type"],
                "playerId": playerEntry["id"],
                "playerName": playerEntry["name"],
                "failedConditions": [],
            }

        if check["event-type"] not in player:
            player[check["event-type"]] = []

        if target["type"] == "Enemy":
            player[check["event-type"]].append(
                {
                    "totalDamage": playerEntry["total"],
                    "activeTime": playerEntry["activeTime"],
                    "enemyId": target["data"].get("enemyId"),
                    "enemyName": target["data"].get("enemyName"),
                    "enemyGuid": target["data"].get("enemyGuid"),
                }
            )
        elif target["type"] == "Ability":
            player[check["event-type"]].append(
                {
                    "totalDamage": playerEntry["total"],
                    "activeTime": playerEntry["activeTime"],
                    "abilityName": check.get("ability-name", None),
                    "abilityGuid": check.get("ability-id", None),
                    "hitCount": playerEntry.get("hitCount"),
                }
            )
        elif target["type"] == "Interrupt":
            player[check["event-type"]].append(
                {
                    "interruptName": check.get("ability-name", None),
                    "interruptGuid": check.get("ability-id", None),
                    "total": playerEntry.get("total"),
                }
            )

        if index is not None:
            data[index] = player
        else:
            data.append(player)


def check_conditions(player, condition):
    # playerType, comma-separated AND list
    #   ! = Not
    #   e.g. !Rogue,!Mage -> playerType != Rogue and != Mage
    # event,key, comma-separated list
    #   e.g. damage-done,totalDamage
    # source guid
    # comparison
    #   e.g. >,>=,=,<=,<,diff >= X
    # target guid
    # name
    # description

    playerTypes = condition[0].split(",")

    type_included = True
    for ptype in playerTypes:
        if player["playerType"] in ptype:
            type_included = not type_included if ptype[0] == "!" else type_included
            break

    if not type_included:
        return

    results = []

    for source in condition[2].split(","):
        found_source = None
        found_target = None
        log_event, key = condition[1].split(",")

        for event in player.get(log_event, []):
            if (
                str(event.get("enemyGuid")) == source
                or str(event.get("abilityGuid")) == source
            ):
                found_source = event[key]
            if log_event == "damage-done":
                if (
                    str(event.get("enemyGuid")) == condition[4]
                    or str(event.get("abilityGuid")) == condition[4]
                ):
                    found_target = event[key]
            elif log_event == "damage-taken":
                found_target = condition[4]
            if found_source and found_target:
                break

        if found_source is not None and found_target is not None:
            # print(player["playerName"], found_source, found_target)
            if "diff" in condition[3]:
                if found_source > found_target:
                    results.append(False)
                else:
                    difference = (
                        abs(int(found_target) - int(found_source)) / found_source
                    ) * 100.0

                    _, evaluation, check_diff = condition[3].split(" ")
                    results.append(eval(f"{difference}{evaluation}{check_diff}"))
            else:
                results.append(eval(f"{found_source}{condition[3]}{found_target}"))
            # print(results)

    if len(results) > 0 and all(results):

        player["failedConditions"].append(
            {
                "name": condition[5],
                "description": condition[6],
                "event": log_event,
                "enemyId": event.get("enemyId"),
                "enemyGuid": event.get("enemyGuid"),
                "abilityGuid": event.get("abilityGuid"),
            }
        )
