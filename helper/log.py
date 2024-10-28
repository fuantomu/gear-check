import requests
import os

token = None
warcraft_logs_url = "https://www.warcraftlogs.com:443/v1/report/"


def get_log(report: str):
    url = f'{warcraft_logs_url}fights/{report}?api_key={os.getenv("WCL_USERID")}'
    log_data = requests.get(url)
    return log_data.json()


def get_log_summary(report: str):
    url = f'{warcraft_logs_url}tables/summary/{report}?start=0&end=999999999999&api_key={os.getenv("WCL_USERID")}'
    log_data = requests.get(url)
    return log_data.json().get("playerDetails")


def get_log_events(report: str, **kwargs):
    url = f"{warcraft_logs_url}tables/EVENT-TYPE/{report}?"
    # print(kwargs)
    for key, item in kwargs.items():
        # print(f"{key}: {item}")
        if key == "event-type":
            url = url.replace("EVENT-TYPE", item)
        else:
            url = f"{url}{key}={item}&"

    url = url.replace("EVENT-TYPE", "summary")

    # url = f'{url}{kwargs.get("start", 0)}&end={kwargs.get("end", 999999999)}'

    url = f'{url}api_key={os.getenv("WCL_USERID")}'
    print(url)
    log_data = requests.get(url)
    # print(len(log_data.json().get("entries")))
    return log_data.json()


warcraft_logs_url_v2 = "https://www.warcraftlogs.com/api/v2/client"


def get_log_v2(report: str):
    body = """ 
        query { 
            reportData { 
                report(code:"REPLACE") {
                    *
                }
            } 
        } 
    """.replace(
        "REPLACE", report
    )
    global token
    result = requests.get(
        warcraft_logs_url_v2,
        json={"query": body},
        headers={"Authorization": f"Bearer {token}"},
    )
    # print(result.text)


def get_wcl_oauth():
    url = "https://www.warcraftlogs.com/oauth/token"
    global token
    token = requests.post(
        url,
        data={"grant_type": "client_credentials"},
        auth=requests.auth.HTTPBasicAuth(
            os.getenv("WCL_CLIENT_ID"), os.getenv("WCL_CLIENT_SECRET")
        ),
    )
    if token.status_code != 200:
        raise token.text
    else:
        token = token.json().get("access_token")
