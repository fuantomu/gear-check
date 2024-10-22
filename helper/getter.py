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
        if fight["boss"] != 0 and fight["kill"]:
            boss_fights.append(fight)
    return boss_fights
