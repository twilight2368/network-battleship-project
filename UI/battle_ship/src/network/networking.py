# src/network/networking.py

import json
import socket
import sys

# Network Constants
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
BUFFER_SIZE = 1024

# ==========================================
# JSON SEND/RECV (Keywords are unchanged)
# ==========================================
def send_json(sock, obj):
    """Gửi đối tượng Python dưới dạng chuỗi JSON qua socket."""
    try:
        print(f"Sending: {obj}")  # Debug
        sock.sendall(json.dumps(obj).encode("utf-8"))
    except:
        pass

def recv_json(sock):
    """Nhận và parse một đối tượng JSON hoàn chỉnh từ socket."""
    data = ""
    brace_count = 0
    inside_json = False

    while True:
        try:
            # Dùng sys.exit(0) để thoát nếu không còn chunk
            chunk = sock.recv(BUFFER_SIZE).decode("utf-8")
            if not chunk:
                return None

            data += chunk
            for ch in chunk:
                if ch == "{":
                    brace_count += 1
                    inside_json = True
                elif ch == "}":
                    brace_count -= 1

            # Kết thúc khi tìm thấy một đối tượng JSON hoàn chỉnh
            if inside_json and brace_count == 0:
                break
        except:
            return None

    try:
        return json.loads(data)
    except:
        return None