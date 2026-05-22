import json
import struct
import threading
from util.response import Response
from util.websockets import compute_accept, generate_ws_frame
from util.database import users_collection, drawings_collection
import hashlib

active_connections = {}
active_lock = threading.Lock()

def get_authenticated_user_from_request(request):
    token = request.cookies.get("auth_token")
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = users_collection.find_one({"tokens": token_hash})
    return user["username"] if user else None

def broadcast_to_all(message_bytes):
    with active_lock:
        for sock in list(active_connections.keys()):
            try:
                sock.sendall(message_bytes)
            except:
                # Remove dead socket
                if sock in active_connections:
                    del active_connections[sock]

def broadcast_active_users_list():
    with active_lock:
        users_list = [{"username": username} for username in active_connections.values()]
    payload = {
        "messageType": "active_users_list",
        "users": users_list
    }
    frame = generate_ws_frame(json.dumps(payload).encode('utf-8'))
    broadcast_to_all(frame)

#Helper: read exactly n bytes
def read_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed")
        data += chunk
    return data

#Main WebSocket handler
def websocket_handler(request, handler):
    key = request.headers.get("Sec-WebSocket-Key")

    accept = compute_accept(key)
    res = Response()
    res.set_status("101", "Switching Protocols")
    res.headers({
        "Upgrade": "websocket",
        "Connection": "Upgrade",
        "Sec-WebSocket-Accept": accept,
    })
    handler.request.sendall(res.to_data())

    #Authentication & registration
    username = get_authenticated_user_from_request(request)
    sock = handler.request
    with active_lock:
        active_connections[sock] = username

    # Send init_strokes
    strokes = []
    for doc in drawings_collection.find().sort("_id", 1):  # oldest first
        strokes.append({
            "startX": doc["startX"],
            "startY": doc["startY"],
            "endX": doc["endX"],
            "endY": doc["endY"],
            "color": doc["color"]
        })
    init_payload = {
        "messageType": "init_strokes",
        "strokes": strokes
    }
    init_frame = generate_ws_frame(json.dumps(init_payload).encode('utf-8'))
    sock.sendall(init_frame)

    broadcast_active_users_list()

    #Frame processing loop
    try:
        while True:
            # Read header (2 bytes)
            header = read_exact(sock, 2)
            first_byte, second_byte = header[0], header[1]
            opcode = first_byte & 0x0F
            mask_bit = (second_byte >> 7) & 1
            payload_len = second_byte & 0x7F

            # Extended length
            if payload_len == 126:
                ext = read_exact(sock, 2)
                payload_len = struct.unpack('>H', ext)[0]
            elif payload_len == 127:
                ext = read_exact(sock, 8)
                payload_len = struct.unpack('>Q', ext)[0]

            # Masking key
            if mask_bit:
                mask = read_exact(sock, 4)
            else:
                mask = None

            # Read payload
            payload = read_exact(sock, payload_len)

            # Unmask
            if mask:
                unmasked = bytearray(payload_len)
                for i in range(payload_len):
                    unmasked[i] = payload[i] ^ mask[i % 4]
                payload = bytes(unmasked)

            # Handle close frame
            if opcode == 0x08:
                close_frame = generate_ws_frame(b"")
                sock.sendall(close_frame)
                break

            # Only process text frames
            if opcode != 0x01:
                continue

            #Parse JSON message
            try:
                msg = json.loads(payload.decode('utf-8'))
                msg_type = msg.get("messageType")

                # Echo features
                if msg_type == "echo_client":
                    reply = {
                        "messageType": "echo_server",
                        "text": msg.get("text", "")
                    }
                    reply_frame = generate_ws_frame(json.dumps(reply).encode('utf-8'))
                    sock.sendall(reply_frame)

                #Drawing board feature
                elif msg_type == "drawing":
                    # Extract fields
                    startX = msg.get("startX")
                    startY = msg.get("startY")
                    endX   = msg.get("endX")
                    endY   = msg.get("endY")
                    color  = msg.get("color")
                    # Validate
                    if None not in (startX, startY, endX, endY, color):
                        # Store in database
                        drawings_collection.insert_one({
                            "startX": startX,
                            "startY": startY,
                            "endX": endX,
                            "endY": endY,
                            "color": color
                        })
                        # Broadcast to everyone
                        broadcast_frame = generate_ws_frame(payload)
                        broadcast_to_all(broadcast_frame)

            except Exception:
                # Ignore malformed JSON or other errors
                pass

    except (ConnectionError, BrokenPipeError, OSError):
        pass
    finally:
        # Remove this connection from active set
        with active_lock:
            if sock in active_connections:
                del active_connections[sock]
        # Broadcast updated user list
        broadcast_active_users_list()
        sock.close()