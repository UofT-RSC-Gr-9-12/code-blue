import socket
import selectors
import types
from cryptography import x509
from cryptography.hazmat.primitives import serialization

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 3000  # Port to listen on (non-privileged ports are > 1023)
sel = selectors.DefaultSelector()


def accept_conn(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    conn.send(b"Welcome to the echo server!\n")


def service_conn(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            decoded = recv_data.decode().strip()
            print(f"Received {decoded!r} from {data.addr}")
            if decoded.lower().strip() == "meow":
                with open("domain.crt", "rb") as cert_file:
                    cert_data = cert_file.read()
                    cert = x509.load_pem_x509_certificate(
                        cert_data).public_bytes(encoding=serialization.Encoding.PEM)
                    msg = b"Meow! Here's my certificate: \n" + cert + b"\n"
                    data.outb += msg
            else:
                msg = b"Meow! :3\n"
                data.outb += msg
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Sending {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Listening on {(HOST, PORT)}")
    s.setblocking(False)
    sel.register(s, selectors.EVENT_READ, data=None)
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_conn(key.fileobj)
                else:
                    service_conn(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()
