import json
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_datetime
from urllib.parse import parse_qs
import requests
from LambdaPage import LambdaPage
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import base64
from io import BytesIO


murd_url = "https://uym92tuf5i.execute-api.us-east-1.amazonaws.com/prod/murd"


###############################################################################
# Utilities

def get_page(PageName):
    with open("Pages/{}.html".format(PageName), "r") as f:
        page = f.read()

    return str(page)


###############################################################################
# Endpoints


def heartbeat_handler(event):
    body = json.loads(event['body'])
    print("Received: {}".format(body))
    state = body['state']
    mems = [{"ROW": "TRELLIS",
             "COL": datetime.utcnow().isoformat(), "STATE": state}]

    resp = requests.put(murd_url, json={"mems": json.dumps(mems)})
    if resp.status_code != 200:
        raise Exception("Failed to store heartbeat")

    resp = requests.post(murd_url, json={"row": "TRELLIS", "col": "DESIRED"})
    if resp.status_code != 200:
        raise Exception("Failed to get desired trellis state")
    desired_state = resp.json()[0]['STATE']

    return 200, json.dumps({"desired_state": desired_state})


def login_handler(event=None, message=None):
    """ Generate WebApp Login Page

        The login page is the default landing location of the page. It
        allows a user to enter the system with a valid username and
        password. This page also provides access to account creation
        and account recovery.
    """
    print("Retreiving login page")
    raw_page = get_page("Login")

    message = message + "<br>" if message is not None else ""
    formatted_page = raw_page.replace("{message}", message)

    page = BeautifulSoup(formatted_page, 'html.parser')

    return str(page)


def nerodia_console(message=""):
    print("Building Nerodia Console")

    print("Gathering Nerodia Status")
    resp = requests.post(murd_url, json={"row": "TRELLIS", "col": "DESIRED"})
    desired_state = resp.json()[0]['STATE']
    now = datetime.utcnow()
    thirty_days = timedelta(days=30)
    past_month = (now - thirty_days).strftime("%Y-%m")
    next_month = (now + thirty_days).strftime("%Y-%m")
    resp = requests.post(murd_url, json={"row": "TRELLIS",
                                         "greater_than_col": past_month,
                                         "less_than_col": next_month})
    data = resp.json()
    last_hearbeat = data[0]
    status = last_hearbeat['STATE']

    def status_to_action(status):
        return 'OPENING' if status == 'OPEN' else 'CLOSING'

    different_state = 'CLOSED' if desired_state == 'OPEN' else 'OPEN'
    heartbeat_timestamp = last_hearbeat['COL']
    planned_action = status_to_action(desired_state) \
        if status is not desired_state \
        else None
    print("Recent status: {}".format(heartbeat_timestamp))

    x = [parse_datetime(datum['COL']) for datum in data]
    y = sorted([datum['STATE'] for datum in data])
    fig, ax = plt.subplots()
    ax.plot(x, y)
    plt.title("Nerodia Valve State over Time")
    plt.ylabel("Valve State")
    plt.xlabel("Time (UTC)")
    fig.autofmt_xdate()
    plt.tight_layout()

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    historical_base64 = figdata_png.decode('utf-8')

    print("Rendering page")
    raw_page = get_page("Nerodia")
    formatted_page = raw_page.replace("{message}", message)
    formatted_page = formatted_page.replace("{status}", status)
    formatted_page = formatted_page.replace("{status_timestamp}",
                                            heartbeat_timestamp)
    formatted_page = formatted_page.replace("{planned_action}", planned_action)
    formatted_page = formatted_page.replace("{different_state}",
                                            different_state)
    formatted_page = formatted_page.replace("{historical_base64}",
                                            historical_base64)
    page = BeautifulSoup(formatted_page, 'html.parser')

    print("Returning")
    return str(page)


def webapp_handler(event):
    print("Handling Login Submission")
    # Check password
    try:
        print("Decoding credentials")
        body = parse_qs(event['body'])
        if type(body) is bytes:
            body = body.decode()
        password = body['password'][0] if 'password' in body \
            else body['token'][0]
    except Exception as e:
        print("Password decoding generated exception: {}".format(e))
        password = None

    if password != "nerodiapw":
        print("Password {} invalid".format(password))
        return 200, login_handler(message="Incorrect Password")
    else:
        if 'desired_state' in body and 'token' in body:
            print("Setting desired state to {}".format(
                  body['desired_state'][0]))
            requests.put(murd_url, json={"mems": json.dumps(
                [{
                    "ROW": "TRELLIS",
                    "COL": "DESIRED",
                    "STATE": body['desired_state'][0]
                }]
            )})
        return 200, nerodia_console()


def create_lambda_page():
    page = LambdaPage()
    page.add_endpoint("post", "/heartbeat",
                      heartbeat_handler, 'application/json')
    page.add_endpoint("get", "/webapp", login_handler, 'text/html')
    page.add_endpoint("post", "/webapp", webapp_handler, 'text/html')

    return page


def lambda_handler(event, handler):
    page = create_lambda_page()
    print("Received Event:\n{}".format(event))
    return page.handle_request(event)
