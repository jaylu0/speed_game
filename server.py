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
lock = threading.Lock()  # for thread-safe updates

# Flag to indicate a player requested to start/restart a round
start_requested = False


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
    global scores, start_requested

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

            msg_type = msg.get("type")

            # Spam key pressed
            if msg_type == "press":
                with lock:
                    if phase == "playing":
                        scores[player_id] += 1

            # Player pressed SPACE to start/restart
            elif msg_type == "start":
                with lock:
                    # Any player can request start
                    start_requested = True

    except Exception as e:
        print(f"[SERVER] Error from player {player_id}:", e)
    finally:
        print(f"[SERVER] Player {player_id} disconnected")
        file.close()
        conn.close()


def game_loop():
    """
    Runs a single round: countdown -> playing -> finished.
    Called whenever a start is requested.
    """
    global phase, countdown_left, time_left, scores

    print("[SERVER] Starting new round")

    # Reset state for new round
    with lock:
        scores = {1: 0, 2: 0}
        phase = "countdown"
        countdown_left = COUNTDOWN_DURATION
        time_left = ROUND_DURATION

    countdown_start = time.time()

    # --- COUNTDOWN PHASE ---
    while True:
        now = time.time()
        elapsed = now - countdown_start

        with lock:
            countdown_left = max(0.0, COUNTDOWN_DURATION - elapsed)
            local_countdown = countdown_left

        # Broadcast state
        broadcast({
            "type": "state",
            "phase": "countdown",
            "countdown_left": local_countdown,
            "time_left": time_left,
            "p1_score": scores[1],
            "p2_score": scores[2],
        })

        if local_countdown <= 0.0:
            break

        time.sleep(0.05)

    # --- PLAYING PHASE ---
    with lock:
        phase = "playing"
        time_left = ROUND_DURATION

    round_start = time.time()

    while True:
        now = time.time()
        elapsed = now - round_start

        with lock:
            time_left = max(0.0, ROUND_DURATION - elapsed)
            local_time_left = time_left
            p1 = scores[1]
            p2 = scores[2]

        broadcast({
            "type": "state",
            "phase": "playing",
            "countdown_left": 0.0,
            "time_left": local_time_left,
            "p1_score": p1,
            "p2_score": p2,
        })

        if local_time_left <= 0.0:
            break

        time.sleep(0.05)

    # --- FINISHED PHASE ---
    with lock:
        phase = "finished"
        time_left = 0.0
        p1 = scores[1]
        p2 = scores[2]

    if p1 > p2:
        winner = 1
    elif p2 > p1:
        winner = 2
    else:
        winner = 0  # tie

    broadcast({
        "type": "state",
            "phase": "finished",
            "countdown_left": 0.0,
            "time_left": 0.0,
            "p1_score": p1,
            "p2_score": p2,
    })

    broadcast({
        "type": "game_over",
        "p1_score": p1,
        "p2_score": p2,
        "winner": winner,
    })

    print("[SERVER] Round over. Scores:", scores, "Winner:", winner)


def main():
    global phase, start_requested

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

    print("[SERVER] Both players connected.")
    with lock:
        phase = "waiting"
        start_requested = False

    # Broadcast initial waiting state
    broadcast({
        "type": "state",
        "phase": "waiting",
        "countdown_left": COUNTDOWN_DURATION,
        "time_left": ROUND_DURATION,
        "p1_score": scores[1],
        "p2_score": scores[2],
    })

    # Main loop: wait for SPACE from a player, then run a round
    while True:
        # Wait until some client sends "start"
        while True:
            with lock:
                if start_requested:
                    start_requested = False
                    break
            time.sleep(0.1)

        # Run a round (handles countdown -> playing -> finished)
        game_loop()
        # IMPORTANT: do NOT force phase back to "waiting" here.
        # Let clients stay in "finished" until another "start" is requested.
        # The next time someone presses SPACE, we just loop again and call game_loop().


if __name__ == "__main__":
    main()