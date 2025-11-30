import socket
import threading
import json
import time

HOST = "0.0.0.0"
PORT = 5000

ROUND_DURATION = 10.0       # seconds for main round
COUNTDOWN_DURATION = 3.0    # seconds before round starts

# Global game state
scores = {1: 0, 2: 0}
phase = "waiting"           # "waiting", "countdown", "playing", "finished"
countdown_left = COUNTDOWN_DURATION
time_left = ROUND_DURATION

clients = {}   # player_id -> socket
lock = threading.Lock()  # for thread-safe score updates


def send_json(conn, obj):
    try:
        data = (json.dumps(obj) + "\n").encode("utf-8")
        conn.sendall(data)
    except OSError:
        pass


def broadcast(obj):
    for conn in clients.values():
        send_json(conn, obj)


def handle_client(conn, player_id):
    global scores

    print(f"[SERVER] Player {player_id} handler started")
    file = conn.makefile("r")

    # Tell this client their player ID
    send_json(conn, {"type": "hello", "player_id": player_id})

    try:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "press":
                with lock:
                    if phase == "playing":
                        scores[player_id] += 1

    except Exception as e:
        print(f"[SERVER] Error from player {player_id}:", e)
    finally:
        print(f"[SERVER] Player {player_id} disconnected")
        file.close()
        conn.close()


def game_loop():
    global phase, countdown_left, time_left, scores

    print("[SERVER] Starting game loop")

    # Reset state
    scores = {1: 0, 2: 0}
    phase = "countdown"
    countdown_start = time.time()
    countdown_left = COUNTDOWN_DURATION
    time_left = ROUND_DURATION

    # --- COUNTDOWN PHASE ---
    while countdown_left > 0:
        now = time.time()
        elapsed = now - countdown_start
        countdown_left = max(0.0, COUNTDOWN_DURATION - elapsed)

        broadcast({
            "type": "state",
            "phase": "countdown",
            "countdown_left": countdown_left,
            "time_left": time_left,
            "p1_score": scores[1],
            "p2_score": scores[2],
        })

        time.sleep(0.05)

    # --- PLAYING PHASE ---
    phase = "playing"
    round_start = time.time()
    time_left = ROUND_DURATION

    while time_left > 0:
        now = time.time()
        elapsed = now - round_start
        time_left = max(0.0, ROUND_DURATION - elapsed)

        broadcast({
            "type": "state",
            "phase": "playing",
            "countdown_left": 0.0,
            "time_left": time_left,
            "p1_score": scores[1],
            "p2_score": scores[2],
        })

        time.sleep(0.05)

    # --- FINISHED PHASE ---
    phase = "finished"
    time_left = 0.0

    if scores[1] > scores[2]:
        winner = 1
    elif scores[2] > scores[1]:
        winner = 2
    else:
        winner = 0  # tie

    broadcast({
        "type": "state",
        "phase": "finished",
        "countdown_left": 0.0,
        "time_left": 0.0,
        "p1_score": scores[1],
        "p2_score": scores[2],
    })

    broadcast({
        "type": "game_over",
        "p1_score": scores[1],
        "p2_score": scores[2],
        "winner": winner,
    })

    print("[SERVER] Game over. Scores:", scores, "Winner:", winner)


def main():
    global phase

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)

    print(f"[SERVER] Listening on {HOST}:{PORT}")
    print("[SERVER] Waiting for 2 players to connect...")

    # Accept exactly two players
    for player_id in (1, 2):
        conn, addr = server.accept()
        print(f"[SERVER] Player {player_id} connected from {addr}")
        clients[player_id] = conn
        threading.Thread(target=handle_client, args=(conn, player_id), daemon=True).start()

    print("[SERVER] Both players connected. Starting game in 2 seconds...")
    phase = "waiting"
    time.sleep(2)

    # Start the game
    game_loop()

    print("[SERVER] Done. Press Ctrl+C to quit.")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
