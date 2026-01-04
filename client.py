import socket
import selectors
import types

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 3000  # The port used by the server
CONN_ID = 1

sel = selectors.DefaultSelector()
messages = []


def service_conn(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(2048)  # Should be ready to read
        if recv_data:
            decoded = recv_data.decode().strip()
            print(f"Received: {decoded}")

            data.recv_total += len(recv_data)
        msg = input("Type in a message (or 'exit' to quit): ")
        if msg.lower() == "exit":
            sel.unregister(sock)
            sock.close()
            # sel.unregister(sock)
            print(f"Closing connection {data.connid}")
            return
        data.messages.append(msg.encode())
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print(f"Sending: {data.outb!r}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Starting connection {CONN_ID} to {HOST}:{PORT}")
    s.setblocking(False)
    s.connect_ex((HOST, PORT))
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        connid=CONN_ID,
        recv_total=0,
        messages=messages.copy(),
        outb=b"",
    )
    sel.register(s, events, data=data)
    try:
        while True:
            events = sel.select(timeout=1)
            if not events:
                print("No events, waiting...")
            for key, mask in events:
                service_conn(key, mask)
            if not sel.get_map():
                break

    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


print(f"Received {data!r}")
