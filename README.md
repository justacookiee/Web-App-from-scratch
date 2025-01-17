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