import json
from helper.log import get_log_events
from helper.mapper import hostility, playerType


def check_encounter(report, fight):
    # print(fight)
    checks = get_encounter_check(fight["zoneName"], fight["name"])
    enemies = get_encounter_enemies(
        report, fight["start_time"], fight["end_time"], checks
    )
    # print(enemies)

    activity = []
    for check in checks:
        # print(check)
        args = {
            "start": fight["start_time"] + check["start"] * 1000,
            "end": fight["start_time"] + check["end"] * 1000,
            "event-type": check["event-type"],
            "hostility": hostility.get(check["hostility"], "0"),
            "by": check.get("by", "source"),
            "options": check.get("options", "0"),
        }

        enemy = find_enemy_by_guid(enemies, check["target-id"])

        args["targetid"] = enemy["id"]
        events = get_log_events(report, **args)

        for playerEntry in events.get("entries", []):

            if playerEntry["type"] not in playerType:
                continue
            player = None
            index = None
            for idx, entry in enumerate(activity):
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
            player[check["event-type"]].append(
                {
                    "totalDamage": playerEntry["total"],
                    "activeTime": playerEntry["activeTime"],
                    "enemyId": enemy["id"],
                    "enemyName": enemy["name"],
                    "enemyGuid": enemy["guid"],
                }
            )

            if index is not None:
                activity[index] = player
            else:
                activity.append(player)

    for player in activity:
        # playerType, comma-separated AND list
        #   ! = Not
        #   e.g. !Rogue,!Mage -> playerType != Rogue and != Mage
        # event,key, comma-separated list
        #   e.g. damage-done,totalDamage
        # source guid
        # comparison
        #   e.g. >,>=,=,<=,<
        # target guid
        # name
        # description
        conditions = get_encounter_conditions(fight["zoneName"], fight["name"])
        for condition in conditions:
            playerTypes = condition[0].split(",")

            type_included = True
            for ptype in playerTypes:
                if player["playerType"] in ptype:
                    type_included = (
                        not type_included if ptype[0] == "!" else type_included
                    )
                    break

            if not type_included:
                break

            results = []
            for source in condition[2].split(","):
                found_source = None
                found_target = None
                log_event, key = condition[1].split(",")

                for event in player[log_event]:
                    if str(event.get("enemyGuid")) == source:
                        found_source = event[key]
                    if str(event.get("enemyGuid")) == condition[4]:
                        found_target = event[key]
                    if found_source and found_target:
                        break

                if found_source is not None and found_target is not None:

                    if "diff" in condition[3]:
                        if found_source > found_target:
                            results.append(False)
                        else:
                            difference = (
                                abs(int(found_target) - int(found_source))
                                / found_source
                            ) * 100.0

                            _, evaluation, check_diff = condition[3].split(" ")
                            results.append(
                                eval(f"{difference}{evaluation}{check_diff}")
                            )
                    else:
                        results.append(
                            eval(f"{found_source}{condition[3]}{found_target}")
                        )

            if all(results):

                player["failedConditions"].append(
                    {
                        "name": condition[5],
                        "description": condition[6],
                        "event": log_event,
                        "enemyId": event["enemyId"],
                        "enemyGuid": event["enemyGuid"],
                    }
                )

    return activity, enemies


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
    enemies = {}
    args = {"start": start, "end": end, "event-type": "damage-taken", "hostility": 1}
    events = get_log_events(report, **args)
    check_enemies = [entry["target-id"] for entry in checks]
    # print(check_enemies)

    for enemy in events.get("entries"):
        if enemy["guid"] not in check_enemies:
            continue

        enemies[enemy["id"]] = {
            "name": enemy["name"],
            "id": enemy["id"],
            "guid": enemy["guid"],
        }
        for check in checks:
            if check["target-id"] == enemy["guid"]:
                enemies[enemy["id"]]["start"] = check["start"]
                enemies[enemy["id"]]["end"] = check["end"]
    return enemies


def find_enemy_by_guid(enemies, guid) -> dict:
    for enemy in enemies.values():
        if enemy.get("guid") == guid:
            return enemy
    return {}
