def update_class_color(
    service,
    spreadsheetId,
    players,
    sheetId=0,
    offsetRow=1,
    offsetColumnStart=0,
    offsetColumnEnd=0,
):
    class_colors = {
        "Warrior": {"red": 198, "green": 155, "blue": 109},
        "Hunter": {"red": 170, "green": 211, "blue": 114},
        "Warlock": {"red": 135, "green": 136, "blue": 238},
        "Druid": {"red": 255, "green": 124, "blue": 10},
        "Mage": {"red": 63, "green": 199, "blue": 235},
        "Rogue": {"red": 252, "green": 252, "blue": 2},
        "Priest": {"red": 255, "green": 255, "blue": 254},
        "Shaman": {"red": 31, "green": 105, "blue": 235},
        "Paladin": {"red": 244, "green": 140, "blue": 186},
        "DeathKnight": {"red": 196, "green": 30, "blue": 58},
        "Unknown": {"red": 255, "green": 0, "blue": 0},
    }
    request_body = [
        {
            "repeatCell": {
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": class_colors[player["type"]].get("red", 255) / 255,
                            "green": class_colors[player["type"]].get("green", 255)
                            / 255,
                            "blue": class_colors[player["type"]].get("blue", 255) / 255,
                        }
                    }
                },
                "fields": "userEnteredFormat.backgroundColor",
                "range": {
                    "sheetId": sheetId,
                    "startRowIndex": index + offsetRow,
                    "endRowIndex": index + offsetRow + 1,
                    "startColumnIndex": offsetColumnStart,
                    "endColumnIndex": offsetColumnEnd + 1,
                },
            }
        }
        for index, player in enumerate(players)
    ]
    request_body.append(
        {
            "repeatCell": {
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 1,
                            "green": 1,
                            "blue": 1,
                        }
                    }
                },
                "fields": "userEnteredFormat.backgroundColor",
                "range": {
                    "sheetId": sheetId,
                    "startRowIndex": len(players) + offsetRow,
                    "endRowIndex": len(players) + offsetRow + 15,
                    "startColumnIndex": offsetColumnStart,
                    "endColumnIndex": offsetColumnEnd + 1,
                },
            }
        }
    )

    body = {"requests": request_body}

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()


def update_background_color(service, spreadsheetId, range, color, sheetId=0):
    request_body = {
        "repeatCell": {
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {
                        "red": color.get("red", 0),
                        "green": color.get("green", 0),
                        "blue": color.get("blue", 0),
                    }
                }
            },
            "fields": "userEnteredFormat.backgroundColor",
            "range": {
                "sheetId": sheetId,
                "startRowIndex": range.get("row_start", 0),
                "endRowIndex": range.get("row_end", range.get("row_start", 0) + 1),
                "startColumnIndex": range.get("column_start", 0),
                "endColumnIndex": range.get("column_end", 0),
            },
        }
    }

    body = {"requests": request_body}

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()


def update_cell_width(service, spreadsheetId, sheetId=0):
    column_widths = [
        {"columnNumber": 1, "width": 180},
        {"columnNumber": 2, "width": 120},
        {"columnNumber": 3, "width": 120},
        {"columnNumber": 4, "width": 450},
        {"columnNumber": 5, "width": 450},
        {"columnNumber": 6, "width": 450},
    ]
    request_body = [
        {
            "updateDimensionProperties": {
                "properties": {"pixelSize": e["width"]},
                "range": {
                    "dimension": "COLUMNS",
                    "sheetId": sheetId,
                    "startIndex": e["columnNumber"] - 1,
                    "endIndex": e["columnNumber"],
                },
                "fields": "pixelSize",
            }
        }
        for e in column_widths
    ]

    body = {"requests": request_body}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()


def update_wrap(service, spreadsheetId, range, sheetId=0):
    request_body = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheetId,
                    "startRowIndex": range.get("row_start", 0),
                    "endRowIndex": range.get("row_end", range.get("row_start", 0) + 1),
                    "startColumnIndex": range.get("column_start", 0),
                    "endColumnIndex": range.get("column_end", 0),
                },
                "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                "fields": "userEnteredFormat.wrapStrategy",
            }
        }
    ]

    body = {"requests": request_body}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()


def update_text_format(service, spreadsheetId, range, sheetId=0):
    request_body = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheetId,
                    "startRowIndex": range.get("row_start", 0),
                    "endRowIndex": range.get("row_end", range.get("row_start", 0) + 1),
                    "startColumnIndex": range.get("column_start", 0),
                    "endColumnIndex": range.get("column_end", 0),
                },
                "cell": {
                    "textFormatRuns": [
                        {"startIndex": 0, "format": {"fontFamily": "Roboto"}}
                    ]
                },
                "fields": "textFormatRuns",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheetId,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6,
                },
                "cell": {
                    "textFormatRuns": [
                        {"startIndex": 0, "format": {"bold": True, "fontSize": 14}}
                    ]
                },
                "fields": "textFormatRuns",
            }
        },
    ]

    body = {"requests": request_body}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()


def update_alignment(service, spreadsheetId, range, sheetId=0):
    request_body = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheetId,
                    "startRowIndex": range.get("row_start", 0),
                    "endRowIndex": range.get("row_end", range.get("row_start", 0) + 1),
                    "startColumnIndex": range.get("column_start", 0),
                    "endColumnIndex": range.get("column_end", 0),
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                    }
                },
                "fields": "userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
            }
        }
    ]

    body = {"requests": request_body}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()


def get_sheet_ids(service, spreadsheetId):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
    sheets = []
    for _sheet in spreadsheet["sheets"]:
        sheets.append(
            {
                "sheetName": _sheet["properties"]["title"],
                "sheetId": _sheet["properties"]["sheetId"],
            }
        )
    return sheets


def find_sheet_id(sheets, sheetName):
    sheetId = None
    for sheet in sheets:
        if sheet["sheetName"] == sheetName:
            return sheet["sheetId"]
    return sheetId
