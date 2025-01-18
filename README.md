<aside>
💡

https://defn.io/2018/02/25/web-app-from-scratch-01/

</aside>

<aside>
💡

### PowerShell commands

```powershell

Invoke-WebRequest -Uri "http://127.0.0.1:9000/"
```

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 9000
```

</aside>

### Request format

- request line \r\n
- (0 or more) header line(s) \r\n - \<header name>: \<value>
- \r\n
- (0 or 1) body

### Response format

- status line \r\n
- response headers \r\n
- \r\n
- (0 or 1) response body \<h1>hello\</h1>

### A simple server

```python
import socket

HOST = "127.0.0.1"
PORT = 9000

RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

with socket.socket() as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(0)

    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_socket, client_address = server_socket.accept()

        print(f"New connection from {client_address}")

        with client_socket:
            client_socket.sendall(RESPONSE)
```

### Request Abstraction

```python
import typing

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

```

```python
with socket.socket() as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(0)

    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_socket, client_address = server_socket.accept()

        print(f"New connection from {client_address}")

        with client_socket:
            for request_line in iter_lines(client_socket):
                print(request_line)
            client_socket.sendall(RESPONSE)
```

### A file server

```python
import mimetypes
import os
import socket
import typing

SERVER_ROOT = os.path.abspath("www")

FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")

def serve_file(sock: socket.socket, path: str) -> None:
    """Given a socket and the relative path to a file (relative to
    SERVER_SOCK), send that file to the socket if it exists.  If the
    file doesn't exist, send a "404 Not Found" response.
    """
    if path == "/":
        path = "/index.html"

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        sock.sendall(NOT_FOUND_RESPONSE)
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

            sock.sendall(response_headers)
            sock.sendfile(f)
    except FileNotFoundError:
        sock.sendall(NOT_FOUND_RESPONSE)
        return
```

```python
with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"Received connection from {client_addr}...")
        with client_sock:
            try:
                request = Request.from_socket(client_sock)
                if request.method != "GET":
                    client_sock.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                    continue

                serve_file(client_sock, request.path)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                client_sock.sendall(BAD_REQUEST_RESPONSE)
```