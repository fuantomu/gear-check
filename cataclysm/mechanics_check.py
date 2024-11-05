import json
from helper.log import get_log, get_log_events
from helper.mapper import hostility, playerType, tank_icons, healer_icons


def check_encounter(report, fight):
    checks = get_encounter_check(fight["zoneName"], fight["name"])

    if len(checks) == 0:
        return [], {}, {}, {}
    enemies = get_encounter_enemies(
        report, fight["start_time"], fight["end_time"], checks
    )

    abilities = get_encounter_abilities(report, fight["end_time"], checks)
    interrupts = get_encounter_interrupts(report, fight["end_time"], checks)
    buffs = get_encounter_buffs(report, fight["end_time"], checks)
    debuffs = get_encounter_debuffs(report, fight["end_time"], checks)

    tanks = get_encounter_tanks(report, fight["end_time"])
    healers = get_encounter_healer(report, fight["end_time"])

    activity = []
    for check in checks:
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
            "abilityid": check.get("ability-id"),
            "options": check.get("options", "0"),
        }

        if check.get("phase") is not None:
            args["phase"] = check["phase"]

        target = {"type": None, "data": None}

        if args["by"] == "ability":
            args.pop("by")
            events = get_log_events(report, **args)
            target["type"] = "Ability"
        elif args["by"] == "target" and args["abilityid"] is not None:
            events = get_log_events(report, **args)
            target["type"] = "Ability"
        elif args["event-type"] == "interrupts":
            args.pop("by")
            events = get_log_events(report, **args)["entries"][0]["entries"]
            target["type"] = "Interrupt"
        elif args["event-type"] == "debuffs":
            args.pop("by")
            events = get_log_events(report, **args)
            target["type"] = "Debuff"
        elif args["event-type"] == "buffs":
            args.pop("by")
            events = get_log_events(report, **args)
            target["type"] = "Buff"
        else:
            target["data"] = find_enemy_by_guid(
                enemies, check["target-id"], check.get("phase")
            )

            if len(target["data"]) == 0:
                print(f"WARN: No enemy found for id {check['target-id']}")
                continue

            target["type"] = "Enemy"

            args["start"] = target["data"]["start"]
            args["end"] = target["data"]["end"]
            args["targetid"] = target["data"]["enemyId"].split("-")[0]

            events = get_log_events(report, **args)

        update_event_data(events, check, target, activity)

    conditions = get_encounter_conditions(fight["zoneName"], fight["name"])
    for player in activity:
        if player["playerName"] in tanks:
            player["role"] = "Tank"
        if player["playerName"] in healers:
            player["role"] = "Healer"
        for condition in conditions:
            check_conditions(player, condition)

    return activity, enemies, abilities, interrupts, buffs, debuffs


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

    fights = get_log(report)["fights"]

    for enemy in events.get("entries"):
        if enemy["guid"] not in check_enemies:
            continue

        for check in checks:
            if check.get("target-id") == enemy["guid"]:
                if check.get("phase") is not None:
                    start_time = start
                    end_time = end
                    for fight in fights:
                        if fight.get("kill", False) and fight["name"] == enemy["name"]:
                            for idx, phase in enumerate(fight["phases"]):
                                if phase["id"] == check["phase"]:
                                    start_time = phase["startTime"]

                                    if idx + 1 < len(fight["phases"]):
                                        end_time = fight["phases"][idx + 1]["startTime"]
                                    break

                    entities[f'{enemy["id"]}-{check.get("phase")}'] = {
                        "enemyName": enemy["name"],
                        "enemyId": f'{enemy["id"]}-{check.get("phase")}',
                        "enemyGuid": enemy["guid"],
                        "start": start_time + (check["start"] * 1000),
                        "end": (
                            end_time
                            if check["end"] == -1
                            else start_time + (check["end"] * 1000)
                        ),
                        "checkStart": check["start"] * 1000,
                        "checkEnd": (
                            end_time - start_time + check["end"] * 1000
                            if check["end"] == -1
                            else start_time + check["end"] * 1000
                        ),
                        "abilities": [],
                        "phase": check.get("phase"),
                    }
                else:
                    entities[str(enemy["id"])] = {
                        "enemyName": enemy["name"],
                        "enemyId": str(enemy["id"]),
                        "enemyGuid": enemy["guid"],
                        "start": start + (check["start"] * 1000),
                        "end": (
                            end if check["end"] == -1 else start + (check["end"] * 1000)
                        ),
                        "checkStart": check["start"] * 1000,
                        "checkEnd": (
                            end - start if check["end"] == -1 else check["end"] * 1000
                        ),
                        "abilities": [],
                    }

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

    for ability in events.get("entries"):

        if ability["guid"] not in check_abilites:
            continue

        entities[ability["guid"]] = {
            "abilityName": ability["name"],
            "abilityGuid": ability["guid"],
        }

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

    check_interrupts = [entry.get("ability-id") for entry in checks]

    for interrupt in events.get("entries"):

        if interrupt["guid"] not in check_interrupts:
            continue

        entities[interrupt["guid"]] = {
            "interruptName": interrupt["name"],
            "interruptGuid": interrupt["guid"],
            "spellsCompleted": interrupt["spellsCompleted"],
            "spellsInterrupted": interrupt["spellsInterrupted"],
        }

    return entities


def get_encounter_tanks(report, end):
    args = {"start": 0, "end": end, "event-type": "damage-taken", "hostility": 0}
    events = get_log_events(report, **args)
    sorted_list = sorted(
        [event for event in events.get("entries", []) if event["icon"] in tank_icons],
        key=lambda e: e["total"],
        reverse=True,
    )

    return [player["name"] for player in sorted_list[: min(len(sorted_list), 2)]]


def get_encounter_healer(report, end):
    args = {"start": 0, "end": end, "event-type": "healing", "hostility": 0}
    events = get_log_events(report, **args)
    sorted_list = sorted(
        [event for event in events.get("entries", []) if event["icon"] in healer_icons],
        key=lambda e: e["total"],
        reverse=True,
    )

    return [player["name"] for player in sorted_list[: min(len(sorted_list), 6)]]


def get_encounter_buffs(report, end, checks):
    entities = {}
    args = {
        "start": 0,
        "end": end,
        "event-type": "buffs",
        "hostility": 0,
    }
    events = get_log_events(report, **args)

    check_buffs = [
        entry.get("ability-id") for entry in checks if entry["event-type"] == "buffs"
    ]

    for buff in events.get("auras"):

        if buff["guid"] not in check_buffs:
            continue

        entities[buff["guid"]] = {
            "buffName": buff["name"],
            "buffGuid": buff["guid"],
            "totalUptime": buff["totalUptime"],
            "totalUses": buff["totalUses"],
        }

    return entities


def get_encounter_debuffs(report, end, checks):
    entities = {}
    args = {
        "start": 0,
        "end": end,
        "event-type": "debuffs",
        "hostility": 0,
    }
    events = get_log_events(report, **args)

    check_debuffs = [
        entry.get("ability-id") for entry in checks if entry["event-type"] == "debuffs"
    ]

    for debuff in events.get("auras"):

        if debuff["guid"] not in check_debuffs:
            continue

        entities[debuff["guid"]] = {
            "debuffName": debuff["name"],
            "debuffGuid": debuff["guid"],
            "totalUptime": debuff["totalUptime"],
            "totalUses": debuff["totalUses"],
        }

    return entities


def find_enemy_by_guid(enemies, guid, phase=None) -> dict:
    for enemy in enemies.values():
        if enemy.get("enemyGuid") == guid and enemy.get("phase") == phase:
            return enemy
    return {}


def update_event_data(events, check, target, data):

    if target["type"] == "Interrupt":
        entries = events[0].get("details", [])
    elif target["type"] in ["Debuff", "Buff"]:
        entries = events.get("auras", [])
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
                    "phase": target["data"].get("phase"),
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
        elif target["type"] == "Buff":
            player[check["event-type"]].append(
                {
                    "buffName": check.get("ability-name", None),
                    "buffGuid": check.get("ability-id", None),
                    "totalUses": playerEntry.get("totalUses"),
                    "totalUptime": playerEntry.get("totalUptime"),
                }
            )
        elif target["type"] == "Debuff":
            player[check["event-type"]].append(
                {
                    "debuffName": check.get("ability-name", None),
                    "debuffGuid": check.get("ability-id", None),
                    "totalUses": playerEntry.get("totalUses"),
                    "totalUptime": playerEntry.get("totalUptime"),
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
        if ptype in ["Healer", "Tank"] and ptype != player.get("role", "None"):
            type_included = False
            break
        if player["playerType"] in ptype or player.get("role", "None") in ptype:
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
                or str(event.get("debuffGuid")) == source
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
            elif log_event == "debuffs":
                found_target = condition[4]
            if found_source and found_target:
                break
        # print(
        #     f"{player['playerName']}-{player.get('role')},{found_source},{found_target}"
        # )
        if found_source is not None and found_target is not None:
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
                "debuffGuid": event.get("debuffGuid"),
            }
        )
