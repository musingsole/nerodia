from HTTPServer import HTTPServer, build_response
from Nerodia import Nerodia


msgs = []
Nerodia = Nerodia()


OPEN = 'm1'
CLOSE = 'm2'


def get_page(path="Nerodia.html"):
    with open(path, "r") as f:
        page = f.read()
    return page


def build_console():
    global msgs
    page = get_page()
    page = page.replace("{nerodia}", str(Nerodia))
    page = page.replace("{message}", "<br>".join(msgs))
    msgs = []
    return build_response(body=page)


def main_page(request):
    return build_console()


def motor_endpoint(request):
    global msgs

    endpoint = request['path'].split("/")[-1]
    if endpoint == 'open':
        Nerodia.open()
    elif endpoint == 'close':
        Nerodia.close()
    else:
        msgs.append("{} not found".format(endpoint))
    return build_console()


nerodia_server = HTTPServer(handlers={
    "/": main_page,
    "/open": motor_endpoint,
    "/close": motor_endpoint,
})
