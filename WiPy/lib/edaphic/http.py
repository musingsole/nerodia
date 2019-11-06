import _thread
import socket
from network import WLAN


not_configured_response = """HTTP/1.1 404 Not Found
Content-Type: text/html
Connection: close
Server: edaphic

Endpoint not found"""


success = """HTTP/1.1 200 OK
Content-Type: text/html
Connection: close
Access-Control-Allow-Origin: *
Server: edaphic

Successful Operation
"""


failure = """HTTP/1.1 502 OK
Content-Type: text/html
Connection: close
Access-Control-Allow-Origin: *
Server: edaphic

Operation Failed
"""


MAX_HTTP_MESSAGE_LENGTH = 2048


def unquote(s):
    """unquote('abc%20def') -> b'abc def'."""
    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not s:
        return b''

    if isinstance(s, str):
        s = s.encode('utf-8')

    bits = s.split(b'%')
    if len(bits) == 1:
        return s

    res = [bits[0]]
    append = res.append

    # Build cache for hex to char mapping on-the-fly only for codes
    # that are actually used
    hextobyte_cache = {}
    for item in bits[1:]:
        try:
            code = item[:2]
            char = hextobyte_cache.get(code)
            if char is None:
                char = hextobyte_cache[code] = bytes([int(code, 16)])
            append(char)
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)

    return b''.join(res)


def parse_querystring(qs):
    parameters = {}
    ampersandSplit = qs.split("&")
    for element in ampersandSplit:
        equalSplit = element.split("=")
        parameters[equalSplit[0]] = unquote(equalSplit[1].replace("+", " ")).decode()

    return parameters


def set_wlan_to_access_point(
    ssid="wipy_https_server",
    password="micropython",
    host_ip="192.168.4.1",
    log=lambda msg: None
):
    log("Creating Access Point {} with password {}".format(ssid, password))
    wlan = WLAN()
    wlan.deinit()
    wlan.ifconfig(config=(host_ip, '255.255.255.0', '0.0.0.0', '8.8.8.8'))
    wlan.init(mode=WLAN.AP, ssid=ssid, auth=(WLAN.WPA2, password), channel=5, antenna=WLAN.INT_ANT)

    return wlan


def http_daemon(path_to_handler={},
                port=80,
                lock=None,
                log=lambda msg: print(msg)):
    s = socket.socket()
    s.bind(('0.0.0.0', port))

    s.listen(5)
    while lock is None or not lock.locked():
        conn, address = s.accept()

        try:
            log('New connection from {}'.format(address))
            conn.setblocking(False)

            msg = conn.recv(MAX_HTTP_MESSAGE_LENGTH).decode()
            msg = msg.replace("\r\n", "\n")

            log("Received MSG:\n{}".format(msg))

            blank_line_split = msg.split('\n\n')
            if len(blank_line_split) != 2:
                raise Exception("Malformated HTTP request.")

            log("Spawn thread to handle message")
            _thread.start_new_thread(process_message_and_response, (msg, conn, path_to_handler))

        except Exception as e:
            log("Request processing failure: {}".format(e))
            conn.send(failure)
            conn.close()


def process_message_and_response(message, conn, path_to_handler={}, log=print):
    try:
        blank_line_split = message.split('\n\n')
        preamble = blank_line_split[0].split("\n")
        request = preamble[0]
        request_keys = ["method", "path", "version"]
        request_key_value = zip(request_keys, request.split(" "))
        request = {key: value for key, value in request_key_value}

        headers = preamble[1:]
        headers = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in headers}

        for key, value in headers.items():
            request[key] = value

        log("Received Request:\n{}".format(request))

        request['body'] = blank_line_split[1]
        if 'Content-Length' in request:
            content_length = int(request['Content-Length'])

        if len(request['body']) < content_length:
            log("Attempting to retrieve {} ({} remaining) bytes of content".format(content_length, content_length - len(request['body'])))
            while len(request['body']) != content_length:
                new_segment = conn.recv(MAX_HTTP_MESSAGE_LENGTH).decode()
                request['body'] += new_segment

        if request['path'] not in path_to_handler:
            log("{} not found in path_to_handler".format(request['path']))
            response = not_configured_response
        else:
            endpoint_handler = path_to_handler[request['path']]
            log("Path found. Passing to {}".format(endpoint_handler))
            response = endpoint_handler(**request)

            log("Sending response")
            conn.send(response)
            conn.close()
    except Exception as e:
        log("Request processing failure: {}".format(e))
        conn.send(failure)
        conn.close()


def build_response(status_code=200, body=''):
    base = """Content-Type: text/html
Connection: close
Access-Control-Allow-Origin: *
Server: edaphic

"""

    status_line = "HTTP/1.1 {}\n".format(status_code)

    response = status_line + base + body

    return response
