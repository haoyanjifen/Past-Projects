import hashlib
import base64
import struct

def compute_accept(websocket_key: str):
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    concat = websocket_key + GUID
    sha1 = hashlib.sha1(concat.encode('utf-8')).digest()
    accept = base64.b64encode(sha1).decode('ascii')
    return accept


class WsFrame:
    def __init__(self, fin_bit, opcode, payload_length, payload):
        self.fin_bit = fin_bit  # 0 or 1
        self.opcode = opcode
        self.payload_length = payload_length# length of unmasked payload in bytes
        self.payload = payload # unmasked payload data



def parse_ws_frame(data: bytes):
    # First byte: FIN, RSV1-3, opcode
    first_byte = data[0]
    fin_bit = (first_byte >> 7) & 0x01
    opcode = first_byte & 0x0F

    # Second byte: MASK, payload length
    second_byte = data[1]
    mask_bit = (second_byte >> 7) & 0x01
    payload_len = second_byte & 0x7F

    # Determine extended payload length
    offset = 2
    if payload_len == 126:
        payload_len = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
    elif payload_len == 127:
        payload_len = struct.unpack('>Q', data[offset:offset+8])[0]
        offset += 8

    # Extract masking key if present
    masking_key = None
    if mask_bit:
        masking_key = data[offset:offset+4]
        offset += 4

    # Extract payload (remaining bytes)
    payload = data[offset:offset+payload_len]

    # Unmask if necessary
    if mask_bit and masking_key:
        unmasked = bytearray(payload_len)
        for i in range(payload_len):
            unmasked[i] = payload[i] ^ masking_key[i % 4]
        payload = bytes(unmasked)

    return WsFrame(fin_bit, opcode, payload_len, payload)

def generate_ws_frame(payload: bytes) -> bytes:
    # First byte: FIN=1, RSV=0, opcode=0x1 (text)
    first_byte = 0x80 | 0x01   # 0x81 = 129 decimal

    # Determine payload length and encoding
    payload_len = len(payload)
    if payload_len < 126:
        second_byte = payload_len
        header = struct.pack('>BB', first_byte, second_byte)
    elif payload_len <= 0xFFFF:
        second_byte = 126
        header = struct.pack('>BBH', first_byte, second_byte, payload_len)
    else:
        second_byte = 127
        header = struct.pack('>BBQ', first_byte, second_byte, payload_len)

    # No masking key so just append payload
    return header + payload