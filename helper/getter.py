from string import ascii_uppercase


def get_players(gear_log):
    players = []
    players.extend(
        [
            character
            for character in gear_log.get("tanks", {})
            if character.get("combatantInfo") != {}
        ]
    )
    players.extend(
        [
            character
            for character in gear_log.get("healers", {})
            if character.get("combatantInfo") != {}
        ]
    )
    players.extend(
        [
            character
            for character in gear_log.get("dps", {})
            if character.get("combatantInfo") != {}
        ]
    )
    players = sorted(players, key=lambda p: (p["type"], p["name"]))
    return players


def get_unique_players(players):
    seen = []
    unique_players = []
    for x in players:
        if x["name"] not in seen:
            unique_players.append(
                {"type": x["type"], "name": x["name"], "server": x["server"]}
            )
            seen.append(x["name"])
    return unique_players


def get_boss_fights(fights):
    boss_fights = []
    for fight in fights:
        if fight.get("boss", 0) != 0:
            boss_fights.append(fight)
    return boss_fights


def filter_fights(fights, filter, fight_order):
    unique_checks = filter.split(",")

    filtered_fights = []
    for check in unique_checks:
        mode = check.split("-")
        # check has a mode (A-,B-,C-,D-)
        if len(mode) > 1:
            if mode[0] in ["A", "B"]:
                filtered_fights.extend(
                    [
                        fight
                        for fight in fights
                        if fight["name"] == fight_order[int(mode[1]) - 1]
                    ]
                )
                continue
            if mode[0] == "C":
                filtered_fights.extend(
                    [
                        fight
                        for fight in fights
                        if fight["kill"]
                        and fight["name"] == fight_order[int(mode[1]) - 1]
                    ]
                )
                continue
            if mode[0] == "D":
                filtered_fights.extend(
                    [
                        fight
                        for fight in fights
                        if not fight["kill"]
                        and fight["name"] == fight_order[int(mode[1]) - 1]
                    ]
                )
                continue
        else:
            if check in ["A", "B"]:
                filtered_fights.extend(fights)
                continue
            if check == "C":
                filtered_fights.extend([fight for fight in fights if fight["kill"]])
                continue
            if check == "D":
                filtered_fights.extend([fight for fight in fights if not fight["kill"]])
                continue
            submode = check.split(".")
            # check has a specific fight (1.1, 2.1, ...)
            if len(submode) > 1:
                try:
                    temp = [
                        fight
                        for fight in fights
                        if fight["name"] == fight_order[int(submode[0]) - 1]
                    ]
                    filtered_fights.append(temp[int(submode[1]) - 1])
                except:
                    pass
                continue

    return filtered_fights


character_list = []


def create_character_list(length):
    global character_list
    ascii_list = list(ascii_uppercase)
    for x in range(max(26, length)):
        try:
            character_list.append(ascii_list[x])
        except:
            character_list.append(
                f"{ascii_list[x//len(ascii_list)-1]}{ascii_list[x%len(ascii_list)]}"
            )


def get_character(idx):
    return character_list[idx]


def get_character_index(value):
    return character_list.index(value)
