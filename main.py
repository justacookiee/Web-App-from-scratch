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