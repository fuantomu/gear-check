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

        if encounter["mechanics"][1] == {}:
            continue

        enemy_columns = {
            encounter["mechanics"][1][enemy]["id"]: characters[idx + 1]
            for idx, enemy in enumerate(encounter["mechanics"][1])
        }

        request_body["data"].extend(
            [
                {
                    "range": f"{encounter['name']}!B1",
                    "majorDimension": "ROWS",
                    "values": [
                        [
                            f"{encounter['mechanics'][1][key]['name']} ({encounter['mechanics'][1][key]['guid']})"
                            for key in enemy_columns
                        ]
                    ],
                },
                {
                    "range": f"{encounter['name']}!B2",
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

        try:
            if len(request_body["data"]) == 0:
                continue
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheetId, body=request_body
            ).execute()
        except Exception as e:
            print(e)

        update_damage_done(service, spreadsheetId, encounter, enemy_columns)

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
                        [enemy.get("totalDamage", 0), enemy.get("activeTime", 0)]
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
                    request_body["data"].append(
                        {
                            "range": f'{main_sheet}!{encounter_column[encounter["name"]]}{2+current_idx}',
                            "values": [[f'{condition["description"]}\n']],
                        }
                    )
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
                "range": f"{encounter['name']}!{enemies[encounter['mechanics'][1][enemy]['id']]}{last_index+1}",
                "majorDimension": "ROWS",
                "values": [
                    [
                        f"=sum(filter({enemies[encounter['mechanics'][1][enemy]['id']]}3:{enemies[encounter['mechanics'][1][enemy]['id']]}{last_index}, isodd(row({enemies[encounter['mechanics'][1][enemy]['id']]}3:{enemies[encounter['mechanics'][1][enemy]['id']]}{last_index}))))",
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
                "range": f"{encounter['name']}!{enemies[encounter['mechanics'][1][rank]['id']]}{last_index+2}",
                "majorDimension": "ROWS",
                "values": [
                    [f"{player[0]}: {player[1]['totalDamage']}"] for player in ranks
                ],
            }
        )

    try:
        if len(request_body["data"]) == 0:
            return
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheetId, body=request_body
        ).execute()
    except Exception as e:
        print(e)

    try:
        if len(request_body["data"]) == 0:
            return
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body={"requests": request_properties_body}
        ).execute()
    except Exception as e:
        print(e)
