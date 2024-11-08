from cataclysm.mechanics_check import check_encounter
from helper.credentials import get_creds
from helper.discord import send_discord_post, update_discord_post
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

from helper.functions import enumerate_step, get_formatted_time
from helper.getter import create_character_list, get_character, get_character_index
from sheet.general import find_sheet_id, get_sheet_ids

_sheets = None
main_sheet = "Overview"


async def create_mechanics_sheet(log, log_title, report):
    creds = get_creds()

    try:
        await update_discord_post(f"Creating Google Sheet")
        service = build("sheets", "v4", credentials=creds)
        title = f"{log_title} Mechanics Sheet"
        spreadsheet = {"properties": {"title": title}}
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )

        await send_discord_post(
            f"https://docs.google.com/spreadsheets/d/{spreadsheet.get('spreadsheetId')}/edit#gid=0"
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
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": 0,
                            "gridProperties": {
                                "frozenRowCount": 1,
                                "hideGridlines": True,
                            },
                        },
                        "fields": "gridProperties(frozenRowCount,hideGridlines)",
                    }
                },
            ]
        }

        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet.get("spreadsheetId"),
                body=request_body,
            ).execute()
        except Exception as e:
            print(e)

        global _sheets

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

        request_body = {
            "valueInputOption": "USER_ENTERED",
            "data": {
                "range": f"{main_sheet}!A1",
                "majorDimension": "COLUMNS",
                "values": [["Encounters"]],
            },
        }

        try:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet.get("spreadsheetId"), body=request_body
            ).execute()
        except Exception as e:
            print(e)

        create_character_list(len(log) + 1)

        if len(log) + 1 > 26:
            try:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet.get("spreadsheetId"),
                    body={
                        "requests": [
                            {
                                "insertDimension": {
                                    "range": {
                                        "sheetId": 0,
                                        "dimension": "COLUMNS",
                                        "startIndex": len(log),
                                        "endIndex": len(log) + 1,
                                    },
                                    "inheritFromBefore": True,
                                }
                            }
                        ]
                    },
                ).execute()
            except Exception as e:
                print(e)

        format_request = {"requests": []}

        for fight_idx, fight in enumerate(log):
            await update_discord_post(
                f"Checking logs for {fight['name']} {'kill' if fight['kill'] else 'wipe'} ({get_formatted_time(fight['start_time'])}-{get_formatted_time(fight['end_time'])})"
            )

            encounter = {
                "name": f"{fight['name']} {'kill' if fight['kill'] else 'wipe'} ({get_formatted_time(fight['start_time'])}-{get_formatted_time(fight['end_time'])})",
                "mechanics": check_encounter(report, fight),
            }

            if all(
                [
                    mechanic == {} or mechanic == []
                    for mechanic in encounter["mechanics"]
                ]
            ):
                continue

            try:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet.get("spreadsheetId"),
                    body={
                        "requests": [
                            {"addSheet": {"properties": {"title": encounter["name"]}}}
                        ]
                    },
                ).execute()
            except Exception as e:
                print(e)

            _sheets = get_sheet_ids(service, spreadsheet.get("spreadsheetId"))

            fails = await update_mechanics_sheet(
                service, spreadsheet.get("spreadsheetId"), encounter, fight_idx
            )

            value_request = {
                "valueInputOption": "USER_ENTERED",
                "data": [],
            }

            player_row = {}
            for idx, entry in enumerate(encounter["mechanics"][0]):
                player_row[entry["playerName"]] = f"{2+idx}"
                value_request["data"].extend(
                    [
                        {
                            "range": f"{main_sheet}!A{2+idx}",
                            "majorDimension": "ROWS",
                            "values": [[entry["playerName"]]],
                        }
                    ]
                )

            value_request["data"].extend(
                [
                    {
                        "range": f"{main_sheet}!{get_character(fight_idx + 1)}{player_row[entry]}",
                        "values": [[fails[entry]]],
                    }
                    for entry in fails
                ]
            )

            try:
                if len(value_request["data"]) > 0:
                    service.spreadsheets().values().batchUpdate(
                        spreadsheetId=spreadsheet.get("spreadsheetId"),
                        body=value_request,
                    ).execute()
            except Exception as e:
                print(e)

        # Format and resize columns in main sheet
        format_request["requests"].extend(
            [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": find_sheet_id(_sheets, main_sheet),
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 75 / 255,
                                    "green": 133 / 255,
                                    "blue": 255 / 255,
                                },
                                "horizontalAlignment": "CENTER",
                                "textFormat": {"fontSize": 14, "bold": True},
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": find_sheet_id(_sheets, main_sheet),
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 1,
                            "endColumnIndex": len(log) + 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "textFormat": {"fontSize": 14, "bold": True},
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,horizontalAlignment)",
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": find_sheet_id(_sheets, main_sheet),
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": len(log) + 1,
                        }
                    }
                },
            ]
        )

        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet.get("spreadsheetId"),
                body=format_request,
            ).execute()
        except Exception as e:
            print(e)

    except HttpError as error:
        print(f"An error occurred: {error}")


async def update_mechanics_sheet(service, spreadsheetId, encounter, encounter_idx):

    request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [],
    }

    format_request = {"requests": []}

    print(f"Processing encounter details for {encounter['name']}")

    await update_discord_post(f"Processing encounter details for {encounter['name']}")

    request_body["data"].append(
        {
            "range": f"{main_sheet}!{get_character(encounter_idx + 1)}1",
            "majorDimension": "COLUMNS",
            "values": [[f'{encounter["name"]}']],
        }
    )

    check_column_length(
        service,
        spreadsheetId,
        encounter["name"],
        start=26,
        end=len(encounter["mechanics"][1]) + 1,
    )

    last_column = 0
    enemy_columns = {}
    for idx, enemy in enumerate(encounter["mechanics"][1]):
        last_column = 1 + idx + 1
        enemy_columns[encounter["mechanics"][1][enemy]["enemyId"]] = get_character(
            last_column
        )

    damage_done_fails = {}
    damage_done_bonus = 0
    if len(encounter["mechanics"][1]) > 0:
        damage_done_bonus = 1
        request_body["data"].extend(
            [
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(enemy_columns))}1",
                    "majorDimension": "ROWS",
                    "values": [[f"Damage Done"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(enemy_columns))}2",
                    "majorDimension": "ROWS",
                    "values": [[f"Active Time"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(enemy_columns)+1)}1",
                    "majorDimension": "ROWS",
                    "values": [
                        [
                            f"{encounter['mechanics'][1][key]['enemyName']} ({encounter['mechanics'][1][key]['enemyGuid']}) {'- Phase ' if encounter['mechanics'][1][key].get('phase') is not None else ''} {encounter['mechanics'][1][key].get('phase') if encounter['mechanics'][1][key].get('phase') is not None else ''}"
                            for key in enemy_columns
                        ]
                    ],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(enemy_columns)+1)}2",
                    "majorDimension": "ROWS",
                    "values": [
                        [
                            f"{get_formatted_time(int(encounter['mechanics'][1][key]['checkStart']))}-{get_formatted_time(int(encounter['mechanics'][1][key]['checkEnd']))}"
                            for key in enemy_columns
                        ]
                    ],
                },
            ]
        )
        format_request["requests"].extend(
            format_encounter_sheet(
                last_column - len(enemy_columns),
                last_column - len(enemy_columns) + 1,
                encounter["name"],
                2 + len(encounter["mechanics"][0]) * 2 + 12,
            )
        )

        damage_done_fails = update_damage_done(
            service, spreadsheetId, encounter, enemy_columns
        )

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

    check_column_length(
        service,
        spreadsheetId,
        encounter["name"],
        start=last_column,
        end=len(encounter["mechanics"][2]) + 1 + len(enemy_columns) + damage_done_bonus,
    )

    ability_columns = {}
    for idx, ability in enumerate(encounter["mechanics"][2]):
        last_column = idx + 1 + len(enemy_columns) + damage_done_bonus
        ability_columns[encounter["mechanics"][2][ability]["abilityGuid"]] = (
            get_character(last_column)
        )

    damage_taken_bonus = 0
    damage_taken_fails = {}
    if len(encounter["mechanics"][2]) > 0:
        damage_taken_bonus = 1
        request_body["data"].extend(
            [
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(ability_columns))}1",
                    "majorDimension": "ROWS",
                    "values": [[f"Damage Taken"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(ability_columns))}2",
                    "majorDimension": "ROWS",
                    "values": [[f"Total Duration"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(ability_columns)+1)}1",
                    "majorDimension": "ROWS",
                    "values": [
                        [
                            f"{encounter['mechanics'][2][key]['abilityName']} ({encounter['mechanics'][2][key]['abilityGuid']})"
                            for key in ability_columns
                        ]
                    ],
                },
            ]
        )
        format_request["requests"].extend(
            format_encounter_sheet(
                last_column - len(ability_columns),
                last_column - len(ability_columns) + 1,
                encounter["name"],
                2 + len(encounter["mechanics"][0]) * 2 + 12,
            )
        )

        damage_taken_fails = update_damage_taken(
            service, spreadsheetId, encounter, ability_columns
        )

    check_column_length(
        service,
        spreadsheetId,
        encounter["name"],
        start=last_column,
        end=len(encounter["mechanics"][3])
        + +1
        + len(enemy_columns)
        + damage_done_bonus
        + len(ability_columns)
        + damage_taken_bonus,
    )

    interrupt_bonus = 0
    interrupt_columns = {}
    for idx, interrupt in enumerate(encounter["mechanics"][3]):
        interrupt_bonus = 1
        last_column = (
            idx
            + 1
            + len(enemy_columns)
            + damage_done_bonus
            + len(ability_columns)
            + damage_taken_bonus
        )
        interrupt_columns[encounter["mechanics"][3][interrupt]["interruptGuid"]] = (
            get_character(last_column)
        )

    if len(encounter["mechanics"][3]) > 0:
        request_body["data"].extend(
            [
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(interrupt_columns))}1",
                    "majorDimension": "ROWS",
                    "values": [[f"Interrupts"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(interrupt_columns))}2",
                    "majorDimension": "ROWS",
                    "values": [[f"Kicked/Total Casts"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(interrupt_columns)+1)}1",
                    "majorDimension": "ROWS",
                    "values": [
                        [
                            f"{encounter['mechanics'][3][key]['interruptName']} ({encounter['mechanics'][3][key]['interruptGuid']})"
                            for key in interrupt_columns
                        ]
                    ],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(interrupt_columns)+1)}2",
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
        format_request["requests"].extend(
            format_encounter_sheet(
                last_column - len(interrupt_columns),
                last_column - len(interrupt_columns) + 1,
                encounter["name"],
                2 + len(encounter["mechanics"][0]) * 2 + 12,
            )
        )

        update_interrupts(service, spreadsheetId, encounter, interrupt_columns)

    check_column_length(
        service,
        spreadsheetId,
        encounter["name"],
        start=last_column,
        end=len(encounter["mechanics"][4])
        + 1
        + len(enemy_columns)
        + damage_done_bonus
        + len(ability_columns)
        + damage_taken_bonus
        + len(interrupt_columns)
        + interrupt_bonus,
    )

    buff_bonus = 0
    buff_columns = {}
    for idx, buff in enumerate(encounter["mechanics"][4]):
        buff_bonus = 1
        last_column = (
            idx
            + 1
            + len(enemy_columns)
            + damage_done_bonus
            + len(ability_columns)
            + damage_taken_bonus
            + len(interrupt_columns)
            + interrupt_bonus
        )
        buff_columns[encounter["mechanics"][4][buff]["buffGuid"]] = get_character(
            last_column
        )

    buff_fails = {}
    if len(encounter["mechanics"][4]) > 0:
        request_body["data"].extend(
            [
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(buff_columns))}1",
                    "majorDimension": "ROWS",
                    "values": [[f"Buffs"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(buff_columns)+1)}1",
                    "majorDimension": "ROWS",
                    "values": [
                        [
                            f"{encounter['mechanics'][4][key]['buffName']} ({encounter['mechanics'][4][key]['buffGuid']})"
                            for key in buff_columns
                        ]
                    ],
                },
            ]
        )
        format_request["requests"].extend(
            format_encounter_sheet(
                last_column - len(buff_columns),
                last_column - len(buff_columns) + 1,
                encounter["name"],
                2 + len(encounter["mechanics"][0]) * 2 + 12,
            )
        )

        buff_fails = update_buffs(service, spreadsheetId, encounter, buff_columns)

    check_column_length(
        service,
        spreadsheetId,
        encounter["name"],
        start=last_column,
        end=len(encounter["mechanics"][5])
        + 1
        + len(enemy_columns)
        + damage_done_bonus
        + len(ability_columns)
        + damage_taken_bonus
        + len(interrupt_columns)
        + interrupt_bonus
        + len(buff_columns)
        + buff_bonus,
    )

    debuff_columns = {}
    for idx, debuff in enumerate(encounter["mechanics"][5]):
        last_column = (
            idx
            + 1
            + len(enemy_columns)
            + damage_done_bonus
            + len(ability_columns)
            + damage_taken_bonus
            + len(interrupt_columns)
            + interrupt_bonus
            + len(buff_columns)
            + buff_bonus
        )
        debuff_columns[encounter["mechanics"][5][debuff]["debuffGuid"]] = get_character(
            last_column
        )

    debuff_fails = {}
    if len(encounter["mechanics"][5]) > 0:
        request_body["data"].extend(
            [
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(debuff_columns))}1",
                    "majorDimension": "ROWS",
                    "values": [[f"Debuffs"]],
                },
                {
                    "range": f"{encounter['name']}!{get_character(last_column-len(debuff_columns)+1)}1",
                    "majorDimension": "ROWS",
                    "values": [
                        [
                            f"{encounter['mechanics'][5][key]['debuffName']} ({encounter['mechanics'][5][key]['debuffGuid']})"
                            for key in debuff_columns
                        ]
                    ],
                },
            ]
        )
        format_request["requests"].extend(
            format_encounter_sheet(
                last_column - len(debuff_columns),
                last_column - len(debuff_columns) + 1,
                encounter["name"],
                2 + len(encounter["mechanics"][0]) * 2 + 12,
            )
        )
        debuff_fails = update_debuffs(service, spreadsheetId, encounter, debuff_columns)

    combined_fails = {}

    for fail in damage_done_fails:
        combined_fails[fail] = damage_done_fails[fail]
    for fail in damage_taken_fails:
        if fail in combined_fails:
            combined_fails[fail] += damage_taken_fails[fail]
        else:
            combined_fails[fail] = damage_taken_fails[fail]
    for fail in buff_fails:
        if fail in combined_fails:
            combined_fails[fail] += buff_fails[fail]
        else:
            combined_fails[fail] = buff_fails[fail]
    for fail in debuff_fails:
        if fail in combined_fails:
            combined_fails[fail] += debuff_fails[fail]
        else:
            combined_fails[fail] = debuff_fails[fail]

    try:
        if len(request_body["data"]) > 0:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheetId, body=request_body
            ).execute()
    except Exception as e:
        print(e)

    # Automatically resize all columns in encounter sheet
    format_request["requests"].append(
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": find_sheet_id(_sheets, encounter["name"]),
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": last_column + 1,
                }
            }
        }
    )

    format_request["requests"].append(
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": find_sheet_id(_sheets, encounter["name"]),
                    "gridProperties": {"frozenRowCount": 2, "hideGridlines": True},
                },
                "fields": "gridProperties(frozenRowCount,hideGridlines)",
            }
        },
    )

    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=format_request
        ).execute()
    except Exception as e:
        print(e)

    await update_discord_post(f"Finished processing encounter")

    return combined_fails


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
        for _, enemy in enumerate(entry.get("damage-done", [])):
            ranking["damage-done"][enemy["enemyId"]][entry["playerName"]] = {
                "totalDamage": enemy.get("totalDamage", 0),
                "activeTime": enemy.get("activeTime", 0),
            }
            request_body["data"].append(
                {
                    "range": f"{encounter['name']}!{enemies[enemy['enemyId']]}{3+idx}",
                    "majorDimension": "COLUMNS",
                    "values": [
                        [
                            enemy.get("totalDamage", 0),
                            f"{get_formatted_time(enemy.get('activeTime', 0))}",
                        ]
                    ],
                }
            )
            for condition in entry["failedConditions"]:
                if condition.get("enemyGuid") == enemy["enemyGuid"] and condition.get(
                    "phase"
                ) == enemy.get("phase"):
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
                                    "startColumnIndex": get_character_index(
                                        enemies[enemy["enemyId"]]
                                    ),
                                    "endColumnIndex": get_character_index(
                                        enemies[enemy["enemyId"]]
                                    )
                                    + 1,
                                },
                            }
                        }
                    )
                    if f'{entry["playerName"]}' not in fails:
                        fails[f'{entry["playerName"]}'] = ""
                    fails[f'{entry["playerName"]}'] += f'{condition["description"]}\n'

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
        for _, ability in enumerate(entry.get("damage-taken", [])):
            ranking["damage-taken"][ability["abilityGuid"]][entry["playerName"]] = {
                "totalDamage": ability.get("totalDamage", 0),
                "hitCount": ability.get("hitCount", 0),
            }
            request_body["data"].append(
                {
                    "range": f"{encounter['name']}!{abilities[ability['abilityGuid']]}{3+idx}",
                    "majorDimension": "COLUMNS",
                    "values": [
                        [
                            ability.get("totalDamage", 0),
                            f"{get_formatted_time(ability.get('activeTime', 0))}",
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
                                    "startColumnIndex": get_character_index(
                                        abilities[ability["abilityGuid"]]
                                    ),
                                    "endColumnIndex": get_character_index(
                                        abilities[ability["abilityGuid"]]
                                    )
                                    + 1,
                                },
                            }
                        }
                    )
                    if f'{entry["playerName"]}' not in fails:
                        fails[f'{entry["playerName"]}'] = ""
                    fails[f'{entry["playerName"]}'] += f'{condition["description"]}\n'

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

    try:
        if len(request_body["data"]) > 0:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheetId, body=request_body
            ).execute()
    except Exception as e:
        print(e)


def update_buffs(service, spreadsheetId, encounter, buffs):
    request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [],
    }
    request_properties_body = []
    last_index = 0
    ranking = {"buffs": {}}

    for buff in buffs:
        ranking["buffs"][buff] = {}

    current_idx = 0
    fails = {}
    for idx, entry in enumerate_step(encounter["mechanics"][0], step=2):
        for _, buff in enumerate(entry.get("buffs", [])):
            ranking["buffs"][buff["buffGuid"]][entry["playerName"]] = {
                "totalUptime": buff.get("totalUptime", 0),
                "totalUses": buff.get("totalUses", 0),
            }
            request_body["data"].append(
                {
                    "range": f"{encounter['name']}!{buffs[buff['buffGuid']]}{3+idx}",
                    "majorDimension": "COLUMNS",
                    "values": [
                        [
                            buff.get("totalUses", 0),
                            f"{get_formatted_time(buff.get('totalUptime', 0))}",
                        ]
                    ],
                }
            )
            for condition in entry["failedConditions"]:
                if condition.get("buffGuid") == buff["buffGuid"]:
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
                                    "startColumnIndex": get_character_index(
                                        buffs[buff["buffGuid"]]
                                    ),
                                    "endColumnIndex": get_character_index(
                                        buffs[buff["buffGuid"]]
                                    )
                                    + 1,
                                },
                            }
                        }
                    )
                    if f'{entry["playerName"]}' not in fails:
                        fails[f'{entry["playerName"]}'] = ""
                    fails[f'{entry["playerName"]}'] += f'{condition["description"]}\n'

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

    for _, buff in enumerate(encounter["mechanics"][4]):
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{buffs[encounter['mechanics'][4][buff]['buffGuid']]}{last_index+1}",
                "majorDimension": "ROWS",
                "values": [
                    [
                        f"=sum(filter({buffs[encounter['mechanics'][4][buff]['buffGuid']]}3:{buffs[encounter['mechanics'][4][buff]['buffGuid']]}{last_index}, isodd(row({buffs[encounter['mechanics'][4][buff]['buffGuid']]}3:{buffs[encounter['mechanics'][4][buff]['buffGuid']]}{last_index}))))",
                    ]
                ],
            }
        )

    for rank in ranking["buffs"]:
        ranks = sorted(
            ranking["buffs"][rank].items(),
            key=lambda item: item[1]["totalUptime"],
            reverse=True,
        )[:10]
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{buffs[encounter['mechanics'][4][rank]['buffGuid']]}{last_index+2}",
                "majorDimension": "ROWS",
                "values": [
                    [f"{player[0]}: {get_formatted_time(player[1]['totalUptime'])}"]
                    for player in ranks
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


def update_debuffs(service, spreadsheetId, encounter, debuffs):
    request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [],
    }
    request_properties_body = []
    last_index = 0
    ranking = {"debuffs": {}}
    for debuff in debuffs:
        ranking["debuffs"][debuff] = {}

    current_idx = 0
    fails = {}
    for idx, entry in enumerate_step(encounter["mechanics"][0], step=2):
        for _, debuff in enumerate(entry.get("debuffs", [])):
            ranking["debuffs"][debuff["debuffGuid"]][entry["playerName"]] = {
                "totalUptime": debuff.get("totalUptime", 0),
                "totalUses": debuff.get("totalUses", 0),
            }
            request_body["data"].append(
                {
                    "range": f"{encounter['name']}!{debuffs[debuff['debuffGuid']]}{3+idx}",
                    "majorDimension": "COLUMNS",
                    "values": [
                        [
                            debuff.get("totalUses", 0),
                            f"{get_formatted_time(debuff.get('totalUptime', 0))}",
                        ]
                    ],
                }
            )
            for condition in entry["failedConditions"]:
                if condition.get("debuffGuid") == debuff["debuffGuid"]:
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
                                    "startColumnIndex": get_character_index(
                                        debuffs[debuff["debuffGuid"]]
                                    ),
                                    "endColumnIndex": get_character_index(
                                        debuffs[debuff["debuffGuid"]]
                                    )
                                    + 1,
                                },
                            }
                        }
                    )
                    if f'{entry["playerName"]}' not in fails:
                        fails[f'{entry["playerName"]}'] = ""
                    fails[f'{entry["playerName"]}'] += f'{condition["description"]}\n'

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

    for _, debuff in enumerate(encounter["mechanics"][5]):
        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{debuffs[encounter['mechanics'][5][debuff]['debuffGuid']]}{last_index+1}",
                "majorDimension": "ROWS",
                "values": [
                    [
                        f"=sum(filter({debuffs[encounter['mechanics'][5][debuff]['debuffGuid']]}3:{debuffs[encounter['mechanics'][5][debuff]['debuffGuid']]}{last_index}, isodd(row({debuffs[encounter['mechanics'][5][debuff]['debuffGuid']]}3:{debuffs[encounter['mechanics'][5][debuff]['debuffGuid']]}{last_index}))))",
                    ]
                ],
            }
        )

    for rank in ranking["debuffs"]:
        ranks = sorted(
            ranking["debuffs"][rank].items(),
            key=lambda item: item[1]["totalUptime"],
            reverse=True,
        )[:10]

        request_body["data"].append(
            {
                "range": f"{encounter['name']}!{debuffs[encounter['mechanics'][5][rank]['debuffGuid']]}{last_index+2}",
                "majorDimension": "ROWS",
                "values": [
                    [f"{player[0]}: {get_formatted_time(player[1]['totalUptime'])}"]
                    for player in ranks
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


def check_column_length(service, spreadsheetId, sheet, start=26, end=27):
    if end + 1 > 26:
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheetId,
                body={
                    "requests": [
                        {
                            "insertDimension": {
                                "range": {
                                    "sheetId": find_sheet_id(_sheets, sheet),
                                    "dimension": "COLUMNS",
                                    "startIndex": start,
                                    "endIndex": end + 1,
                                },
                                "inheritFromBefore": True,
                            }
                        }
                    ]
                },
            ).execute()
        except Exception as e:
            print(e)


def format_encounter_sheet(startColumn, endColumn, encounter, endRow):
    return [
        {
            "repeatCell": {
                "range": {
                    "sheetId": find_sheet_id(_sheets, encounter),
                    "startRowIndex": 0,
                    "endRowIndex": 2,
                    "startColumnIndex": startColumn,
                    "endColumnIndex": endColumn,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 75 / 255,
                            "green": 133 / 255,
                            "blue": 255 / 255,
                        },
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"fontSize": 14, "bold": True},
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": find_sheet_id(_sheets, encounter),
                    "startRowIndex": 2,
                    "endRowIndex": endRow,
                    "startColumnIndex": startColumn,
                    "endColumnIndex": endColumn,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 11 / 255,
                            "green": 83 / 255,
                            "blue": 148 / 255,
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor)",
            }
        },
        {
            "mergeCells": {
                "range": {
                    "sheetId": find_sheet_id(_sheets, encounter),
                    "startRowIndex": 2,
                    "endRowIndex": endRow,
                    "startColumnIndex": startColumn,
                    "endColumnIndex": endColumn,
                },
                "mergeType": "MERGE_ALL",
            }
        },
    ]
