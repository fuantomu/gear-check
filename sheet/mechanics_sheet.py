from string import ascii_uppercase
from cataclysm.mechanics_check import check_encounter
from helper.credentials import get_creds
from helper.discord import send_discord_post, update_discord_post
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

from helper.functions import enumerate_step
from helper.getter import get_boss_fights
from sheet.general import find_sheet_id, get_sheet_ids

_sheets = None
main_sheet = "Overview"
characters = list(ascii_uppercase)
encounter_column = {}


async def create_mechanics_sheet(log, report):
    creds = get_creds()

    try:
        await update_discord_post(f"Creating Google Sheet")
        service = build("sheets", "v4", credentials=creds)
        title = f"{log.get('title')} Mechanics Sheet"
        spreadsheet = {"properties": {"title": title}}
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )

        await send_discord_post(
            f"https://docs.google.com/spreadsheets/d/{spreadsheet.get('spreadsheetId')}/edit#gid=0"
        )

        boss_fights = get_boss_fights(log.get("fights"))
        encounters = []
        for idx, fight in enumerate(boss_fights):
            encounter_column[fight["name"]] = characters[idx + 1]
            encounters.append(
                {"name": fight["name"], "mechanics": check_encounter(report, fight)}
            )

        # Rename first sheet to first encounter name
        request_body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": 0,
                            "title": main_sheet,
                        },
                        "fields": "title",
                    }
                }
            ]
        }

        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet.get("spreadsheetId"),
                body=request_body,
            ).execute()
        except Exception as e:
            print(e)

        # Create sheet tabs with encounter names
        if len(encounters) > 0:
            request_body = [
                {"addSheet": {"properties": {"title": encounter["name"]}}}
                for encounter in encounters
            ]

            try:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet.get("spreadsheetId"),
                    body={"requests": request_body},
                ).execute()
            except Exception as e:
                print(e)

        global _sheets
        _sheets = get_sheet_ids(service, spreadsheet.get("spreadsheetId"))

        # Connect to Google Drive and make spreadsheet public
        await update_discord_post(f"Making Google Sheet public")
        drive_client = build("drive", "v3", credentials=creds)

        files = (
            drive_client.files()
            .list(
                q=f"name contains '{title}'",
                spaces="drive",
                fields="nextPageToken, files(id, name)",
            )
            .execute()
            .get("files")
        )

        user_permission = {"type": "anyone", "role": "writer"}
        drive_client.permissions().create(
            fileId=files[0]["id"],
            body=user_permission,
            fields="id",
        ).execute()

        await update_discord_post(f"Processing encounter details")

        await update_mechanics_sheet(
            service, spreadsheet.get("spreadsheetId"), encounters
        )
    except HttpError as error:
        print(f"An error occurred: {error}")


async def update_mechanics_sheet(service, spreadsheetId, encounters):

    request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [],
    }
    for idx, encounter in enumerate(encounters):
        request_body["data"].append(
            {
                "range": f"{main_sheet}!{characters[idx + 1]}1",
                "majorDimension": "COLUMNS",
                "values": [[f'{encounter["name"]}']],
            }
        )

    for encounter in encounters:
        print(f"Processing encounter details for {encounter['name']}")
        await update_discord_post(
            f"Processing encounter details for {encounter['name']}"
        )

        if all(
            [mechanic == {} or mechanic == [] for mechanic in encounter["mechanics"]]
        ):
            continue

        last_column = 0
        enemy_columns = {}
        for idx, enemy in enumerate(encounter["mechanics"][1]):
            enemy_columns[encounter["mechanics"][1][enemy]["enemyId"]] = characters[
                idx + 1
            ]
            last_column = idx + 1
        print(f"{enemy_columns}, {last_column}")

        damage_done_fails = {}
        damage_done_bonus = 0
        if len(encounter["mechanics"][1]) > 0:
            damage_done_bonus = 1
            request_body["data"].extend(
                [
                    {
                        "range": f"{encounter['name']}!{characters[last_column-len(enemy_columns)+1]}1",
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{encounter['mechanics'][1][key]['enemyName']} ({encounter['mechanics'][1][key]['enemyGuid']})"
                                for key in enemy_columns
                            ]
                        ],
                    },
                    {
                        "range": f"{encounter['name']}!{characters[last_column-len(enemy_columns)+1]}2",
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{divmod(int(encounter['mechanics'][1][key]['start']),60)[0]:02d}:{divmod(int(encounter['mechanics'][1][key]['start']),60)[1]:02d}-{divmod(int(encounter['mechanics'][1][key]['end']),60)[0]:02d}:{divmod(int(encounter['mechanics'][1][key]['end']),60)[1]:02d}"
                                for key in enemy_columns
                            ]
                        ],
                    },
                ]
            )

            damage_done_fails = update_damage_done(
                service, spreadsheetId, encounter, enemy_columns
            )

        # print(encounter["mechanics"][0])

        request_body["data"].extend(
            [
                {
                    "range": f"{encounter['name']}!A{3+idx}",
                    "majorDimension": "ROWS",
                    "values": [[entry["playerName"]]],
                }
                for idx, entry in enumerate_step(encounter["mechanics"][0], step=2)
            ]
        )

        request_body["data"].extend(
            [
                {
                    "range": f"{main_sheet}!A{2+idx}",
                    "majorDimension": "ROWS",
                    "values": [[entry["playerName"]]],
                }
                for idx, entry in enumerate(encounter["mechanics"][0])
            ]
        )

        ability_columns = {}
        for idx, ability in enumerate(encounter["mechanics"][2]):
            ability_columns[encounter["mechanics"][2][ability]["abilityGuid"]] = (
                characters[idx + 1 + len(enemy_columns) + damage_done_bonus]
            )
            last_column = idx + 1 + len(enemy_columns) + damage_done_bonus
        print(f"{ability_columns}, {last_column}")

        damage_taken_bonus = 0
        damage_taken_fails = {}
        if len(encounter["mechanics"][2]) > 0:
            damage_taken_bonus = 1
            request_body["data"].extend(
                [
                    {
                        "range": f"{encounter['name']}!{characters[last_column-len(ability_columns)+1]}1",
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{encounter['mechanics'][2][key]['abilityName']} ({encounter['mechanics'][2][key]['abilityGuid']})"
                                for key in ability_columns
                            ]
                        ],
                    }
                ]
            )
            damage_taken_fails = update_damage_taken(
                service, spreadsheetId, encounter, ability_columns
            )

        interrupt_columns = {}
        for idx, interrupt in enumerate(encounter["mechanics"][3]):
            interrupt_columns[encounter["mechanics"][3][interrupt]["interruptGuid"]] = (
                characters[
                    idx
                    + 1
                    + len(enemy_columns)
                    + damage_done_bonus
                    + len(ability_columns)
                    + damage_taken_bonus
                ]
            )
            last_column = (
                idx
                + 1
                + len(enemy_columns)
                + damage_done_bonus
                + len(ability_columns)
                + damage_taken_bonus
            )

        print(f"{interrupt_columns}, {last_column}")

        if len(encounter["mechanics"][3]) > 0:
            request_body["data"].extend(
                [
                    {
                        "range": f"{encounter['name']}!{characters[last_column-len(interrupt_columns)+1]}1",
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{encounter['mechanics'][3][key]['interruptName']} ({encounter['mechanics'][3][key]['interruptGuid']})"
                                for key in interrupt_columns
                            ]
                        ],
                    },
                    {
                        "range": f"{encounter['name']}!{characters[last_column-len(interrupt_columns)+1]}2",
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{encounter['mechanics'][3][key]['spellsInterrupted']}/{encounter['mechanics'][3][key]['spellsCompleted']+encounter['mechanics'][3][key]['spellsInterrupted']} interrupted"
                                for key in interrupt_columns
                            ]
                        ],
                    },
                ]
            )
            update_interrupts(service, spreadsheetId, encounter, interrupt_columns)

        combined_fails = {}

        for fail in damage_done_fails:
            combined_fails[fail] = damage_done_fails[fail]
        for fail in damage_taken_fails:
            if fail in combined_fails:
                combined_fails[fail] += damage_taken_fails[fail]
            else:
                combined_fails[fail] = damage_taken_fails[fail]

        request_body["data"].extend(
            [
                {
                    "range": f"{main_sheet}!{entry}",
                    "values": [[combined_fails[entry]]],
                }
                for entry in combined_fails
            ]
        )
        # print(request_body)
        try:
            if len(request_body["data"]) > 0:
                service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheetId, body=request_body
                ).execute()
        except Exception as e:
            print(e)

    await update_discord_post(f"Finished processing {len(encounters)} encounter(s)")


def update_damage_done(service, spreadsheetId, encounter, enemies):
    request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [],
    }
    request_properties_body = []
    last_index = 0
    ranking = {"damage-done": {}}
    for enemy in enemies:
        ranking["damage-done"][enemy] = {}

    current_idx = 0
    fails = {}
    for idx, entry in enumerate_step(encounter["mechanics"][0], step=2):
        # print(f'Checking damage-done of player {entry["playerName"]}')
        for _, enemy in enumerate(entry.get("damage-done", [])):
            ranking["damage-done"][enemy["enemyId"]][entry["playerName"]] = {
                "totalDamage": enemy.get("totalDamage", 0),
                "activeTime": enemy.get("activeTime", 0),
            }
            seconds, _ = divmod(int(enemy.get("activeTime", 0)), 1000)
            request_body["data"].append(
                {
                    "range": f"{encounter['name']}!{enemies[enemy['enemyId']]}{3+idx}",
                    "majorDimension": "COLUMNS",
                    "values": [
                        [
                            enemy.get("totalDamage", 0),
                            f"{divmod(seconds,60)[0]:02d}:{divmod(seconds,60)[1]:02d}",
                        ]
                    ],
                }
            )
            for condition in entry["failedConditions"]:
                if condition.get("enemyGuid") == enemy["enemyGuid"]:
                    request_properties_body.append(
                        {
                            "repeatCell": {
                                "cell": {
                                    "userEnteredFormat": {
                                        "backgroundColor": {
                                            "red": 0.918,
                                            "green": 0.3412,
                                            "blue": 0.3412,
                                        }
                                    }
                                },
                                "fields": "userEnteredFormat.backgroundColor",
                                "range": {
                                    "sheetId": find_sheet_id(
                                        _sheets, encounter["name"]
                                    ),
                                    "startRowIndex": 2 + idx,
                                    "endRowIndex": 2 + idx + 1,
                                    "startColumnIndex": characters.index(
                                        enemies[enemy["enemyId"]]
                                    ),
                                    "endColumnIndex": characters.index(
                                        enemies[enemy["enemyId"]]
                                    )
                                    + 1,
                                },
                            }
                        }
                    )
                    if (
                        f'{encounter_column[encounter["name"]]}{2+current_idx}'
                        not in fails
                    ):
                        fails[
                            f'{encounter_column[encounter["name"]]}{2+current_idx}'
                        ] = ""
                    fails[
                        f'{encounter_column[encounter["name"]]}{2+current_idx}'
                    ] += f'{condition["description"]}\n'
        # request_body["data"].append(
        #     {
        #         "range": f'{main_sheet}!{encounter_column[encounter["name"]]}{2+current_idx}',
        #         "values": [fails],
        #     }
        # )
        current_idx += 1
        last_index = max(last_index, idx + 5)

    request_body["data"].append(
        {
            "range": f"{encounter['name']}!A{last_index+1}",
            "majorDimension": "ROWS",
            "values": [
                ["Total"],
                ["Top 10"],
            ],
        }
    )

    for _, enemy in enumerate(encounter["mechanics"][1]):
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{enemies[encounter['mechanics'][1][enemy]['enemyId']]}{last_index+1}",
                "majorDimension": "ROWS",
                "values": [
                    [
                        f"=sum(filter({enemies[encounter['mechanics'][1][enemy]['enemyId']]}3:{enemies[encounter['mechanics'][1][enemy]['enemyId']]}{last_index}, isodd(row({enemies[encounter['mechanics'][1][enemy]['enemyId']]}3:{enemies[encounter['mechanics'][1][enemy]['enemyId']]}{last_index}))))",
                    ]
                ],
            }
        )

    for rank in ranking["damage-done"]:
        ranks = sorted(
            ranking["damage-done"][rank].items(),
            key=lambda item: item[1]["totalDamage"],
            reverse=True,
        )[:10]
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{enemies[encounter['mechanics'][1][rank]['enemyId']]}{last_index+2}",
                "majorDimension": "ROWS",
                "values": [
                    [f"{player[0]}: {player[1]['totalDamage']}"] for player in ranks
                ],
            }
        )

    try:
        if len(request_body["data"]) > 0:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheetId, body=request_body
            ).execute()
    except Exception as e:
        print(e)

    try:
        if len(request_properties_body) > 0:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId, body={"requests": request_properties_body}
            ).execute()
    except Exception as e:
        print(e)

    return fails


def update_damage_taken(service, spreadsheetId, encounter, abilities):
    request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [],
    }
    request_properties_body = []
    last_index = 0
    ranking = {"damage-taken": {}}
    for ability in abilities:
        ranking["damage-taken"][ability] = {}

    current_idx = 0
    fails = {}
    for idx, entry in enumerate_step(encounter["mechanics"][0], step=2):
        # print(f'Checking damage-taken of player {entry["playerName"]}')
        for _, ability in enumerate(entry.get("damage-taken", [])):
            ranking["damage-taken"][ability["abilityGuid"]][entry["playerName"]] = {
                "totalDamage": ability.get("totalDamage", 0),
                "hitCount": ability.get("hitCount", 0),
            }
            seconds, _ = divmod(int(ability.get("activeTime", 0)), 1000)
            request_body["data"].append(
                {
                    "range": f"{encounter['name']}!{abilities[ability['abilityGuid']]}{3+idx}",
                    "majorDimension": "COLUMNS",
                    "values": [
                        [
                            ability.get("totalDamage", 0),
                            f"{divmod(seconds,60)[0]:02d}:{divmod(seconds,60)[1]:02d}",
                        ]
                    ],
                }
            )
            for condition in entry["failedConditions"]:
                if condition.get("abilityGuid") == ability["abilityGuid"]:
                    request_properties_body.append(
                        {
                            "repeatCell": {
                                "cell": {
                                    "userEnteredFormat": {
                                        "backgroundColor": {
                                            "red": 0.918,
                                            "green": 0.3412,
                                            "blue": 0.3412,
                                        }
                                    }
                                },
                                "fields": "userEnteredFormat.backgroundColor",
                                "range": {
                                    "sheetId": find_sheet_id(
                                        _sheets, encounter["name"]
                                    ),
                                    "startRowIndex": 2 + idx,
                                    "endRowIndex": 2 + idx + 1,
                                    "startColumnIndex": characters.index(
                                        abilities[ability["abilityGuid"]]
                                    ),
                                    "endColumnIndex": characters.index(
                                        abilities[ability["abilityGuid"]]
                                    )
                                    + 1,
                                },
                            }
                        }
                    )
                    if (
                        f'{encounter_column[encounter["name"]]}{2+current_idx}'
                        not in fails
                    ):
                        fails[
                            f'{encounter_column[encounter["name"]]}{2+current_idx}'
                        ] = ""
                    fails[
                        f'{encounter_column[encounter["name"]]}{2+current_idx}'
                    ] += f'{condition["description"]}\n'

        current_idx += 1
        last_index = max(last_index, idx + 5)

    request_body["data"].append(
        {
            "range": f"{encounter['name']}!A{last_index+1}",
            "majorDimension": "ROWS",
            "values": [
                ["Total"],
                ["Top 10"],
            ],
        }
    )

    for _, ability in enumerate(encounter["mechanics"][2]):
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{abilities[encounter['mechanics'][2][ability]['abilityGuid']]}{last_index+1}",
                "majorDimension": "ROWS",
                "values": [
                    [
                        f"=sum(filter({abilities[encounter['mechanics'][2][ability]['abilityGuid']]}3:{abilities[encounter['mechanics'][2][ability]['abilityGuid']]}{last_index}, isodd(row({abilities[encounter['mechanics'][2][ability]['abilityGuid']]}3:{abilities[encounter['mechanics'][2][ability]['abilityGuid']]}{last_index}))))",
                    ]
                ],
            }
        )

    for rank in ranking["damage-taken"]:
        ranks = sorted(
            ranking["damage-taken"][rank].items(),
            key=lambda item: item[1]["totalDamage"],
            reverse=True,
        )[:10]
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{abilities[encounter['mechanics'][2][rank]['abilityGuid']]}{last_index+2}",
                "majorDimension": "ROWS",
                "values": [
                    [f"{player[0]}: {player[1]['totalDamage']}"] for player in ranks
                ],
            }
        )

    try:
        if len(request_body["data"]) > 0:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheetId, body=request_body
            ).execute()
    except Exception as e:
        print(e)

    try:
        if len(request_properties_body) > 0:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId, body={"requests": request_properties_body}
            ).execute()
    except Exception as e:
        print(e)

    return fails


def update_interrupts(service, spreadsheetId, encounter, interrupts):
    request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [],
    }

    last_index = 0
    ranking = {"interrupts": {}}
    for interrupt in interrupts:
        ranking["interrupts"][interrupt] = {}

    for idx, entry in enumerate_step(encounter["mechanics"][0], step=2):
        for _, interrupt in enumerate(entry.get("interrupts", [])):
            ranking["interrupts"][interrupt["interruptGuid"]][entry["playerName"]] = {
                "total": interrupt.get("total", 0)
            }

            request_body["data"].append(
                {
                    "range": f"{encounter['name']}!{interrupts[interrupt['interruptGuid']]}{3+idx}",
                    "majorDimension": "COLUMNS",
                    "values": [[interrupt.get("total", 0)]],
                }
            )

        last_index = max(last_index, idx + 5)

    request_body["data"].append(
        {
            "range": f"{encounter['name']}!A{last_index+1}",
            "majorDimension": "ROWS",
            "values": [
                ["Total"],
                ["Top 10"],
            ],
        }
    )

    for _, interrupt in enumerate(encounter["mechanics"][3]):
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{interrupts[encounter['mechanics'][3][interrupt]['interruptGuid']]}{last_index+1}",
                "majorDimension": "ROWS",
                "values": [
                    [
                        f"=sum(filter({interrupts[encounter['mechanics'][3][interrupt]['interruptGuid']]}3:{interrupts[encounter['mechanics'][3][interrupt]['interruptGuid']]}{last_index}, isodd(row({interrupts[encounter['mechanics'][3][interrupt]['interruptGuid']]}3:{interrupts[encounter['mechanics'][3][interrupt]['interruptGuid']]}{last_index}))))",
                    ]
                ],
            }
        )

    for rank in ranking["interrupts"]:
        ranks = sorted(
            ranking["interrupts"][rank].items(),
            key=lambda item: item[1]["total"],
            reverse=True,
        )[:10]
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{interrupts[encounter['mechanics'][3][rank]['interruptGuid']]}{last_index+2}",
                "majorDimension": "ROWS",
                "values": [[f"{player[0]}: {player[1]['total']}"] for player in ranks],
            }
        )

    # print(request_body)
    try:
        if len(request_body["data"]) > 0:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheetId, body=request_body
            ).execute()
    except Exception as e:
        print(e)
