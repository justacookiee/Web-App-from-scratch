import mimetypes
import os
import socket
import typing

# Constants
SERVER_ROOT = os.path.abspath("www")
HOST = "127.0.0.1"
PORT = 9000

FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")

RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

BAD_REQUEST_RESPONSE = b"""\
HTTP/1.1 400 Bad Request
"""

NOT_FOUND_RESPONSE = b"""\
HTTP/1.1 404 Not Found
Content-type: text/plain
Content-length: 9

Not Found""".replace(b"\n", b"\r\n")

METHOD_NOT_ALLOWED_RESPONSE = b"""\
HTTP/1.1 405 Method Not Allowed
Content-type: text/plain
Content-length: 17

Method Not Allowed""".replace(b"\n", b"\r\n")

# /Constants

# Methods
def iter_lines(socket_instance: socket.socket, buffer_size: int = 16_384) -> typing.Generator[bytes, None, bytes]:
    buffer = b""
    while True:
        data = socket_instance.recv(buffer_size)
        if not data:
            return b""
        buffer += data
        while True:
            try:
                i = buffer.index(b"\r\n")
                line, buffer = buffer[:i], buffer[i + 2:]
                if not line:
                    return buffer
                yield line
            except IndexError:
                break

def server_file(socket_instance: socket.socket, path: str) -> None:
    if path == '/':
        path = "/index.html"
    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        socket_instance.sendall(NOT_FOUND_RESPONSE)
        return
    try:
        with open(abspath, "rb") as f:
            stat = os.fstat(f.fileno())
            content_type, encoding = mimetypes.guess_type(abspath)
            if content_type is None:
                content_type = "application/octet-stream"
            if encoding is not None:
                content_type += f"; charset={encoding}"
            response_headers = FILE_RESPONSE_TEMPLATE.format(
                content_type=content_type,
                content_length=stat.st_size,
            ).encode("ascii")
            socket_instance.sendall(response_headers)
            socket_instance.sendfile(f)
    except FileNotFoundError:
        socket_instance.sendall(NOT_FOUND_RESPONSE)
        return
# /Methods

# Classes
class Request(typing.NamedTuple):
    method: str
    path: str
    headers: typing.Mapping[str, str]

    @classmethod
    def from_socket(cls, socket_instance: socket.socket) -> "Request":
        lines = iter_lines(socket_instance)
        try:
            request_line = next(lines).decode("ascii")
        except StopIteration:
            raise ValueError("Request line missing.")
        try:
            method, path, _ = request_line.split(" ")
        except ValueError:
            raise ValueError(f"Malformed request line {request_line!r}.")
        headers = {}
        for line in lines:
            try:
                name, _, value = line.decode("ascii").partition(":")
                headers[name.lower()] = value.lstrip()
            except ValueError:
                raise ValueError(f"Malformed header line {line!r}.")
        return cls(method=method.upper(), path=path, headers=headers)
# /Classes

# Main
with socket.socket() as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(0)

    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_socket, client_address = server_socket.accept()

        print(f"New connection from {client_address}")

        with client_socket:
            try:
                request = Request.from_socket(client_socket)
                if request.method != "GET":
                    client_socket.sendall(NOT_FOUND_RESPONSE)
                    continue
                server_file(client_socket, request.path)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                client_socket.sendall(BAD_REQUEST_RESPONSE)
# /Main