import socket
import threading
import json
import math
import pygame
import sys

# Pygame setup
pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spam Game (Online)")

clock = pygame.time.Clock()

font_title = pygame.font.Font(None, 80)
font_big = pygame.font.Font(None, 64)
font_medium = pygame.font.Font(None, 42)
font_small = pygame.font.Font(None, 30)

# Key bindings
SPAM_KEYS = {pygame.K_LEFT, pygame.K_RIGHT}


def draw_text(text, font, color, center):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    screen.blit(surf, rect)


# Different states received from server
state = {
    "player_id": None,
    "phase": "waiting",
    "countdown_left": 3.0,
    "time_left": 10.0,
    "p1_score": 0,
    "p2_score": 0,
    "winner": None,
}

sock = None


def send_json(obj):
    """Send a JSON message to the server."""
    global sock
    if not sock:
        return
    try:
        data = (json.dumps(obj) + "\n").encode("utf-8")
        sock.sendall(data)
    except OSError:
        pass


def listener():
    """Background thread that receives updates from the server."""
    global state, sock

    file = sock.makefile("r")
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

            if msg_type == "hello":
                state["player_id"] = msg.get("player_id")

            elif msg_type == "state":
                state["phase"] = msg.get("phase", state["phase"])
                state["countdown_left"] = msg.get("countdown_left", state["countdown_left"])
                state["time_left"] = msg.get("time_left", state["time_left"])
                state["p1_score"] = msg.get("p1_score", state["p1_score"])
                state["p2_score"] = msg.get("p2_score", state["p2_score"])

            elif msg_type == "game_over":
                state["p1_score"] = msg.get("p1_score", state["p1_score"])
                state["p2_score"] = msg.get("p2_score", state["p2_score"])
                state["winner"] = msg.get("winner")
                state["phase"] = "finished"
                state["time_left"] = 0.0
                state["countdown_left"] = 0.0

    except Exception as e:
        print("[CLIENT] Listener error:", e)

    finally:
        print("[CLIENT] Disconnected from server.")
        pygame.quit()
        sys.exit()


def main():
    global sock, state

    # Asking user for server IP
    SERVER_HOST = input("Enter server IP: ").strip()
    SERVER_PORT = 5000

    # Connecting to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
    except Exception as e:
        print(f"Failed to connect to server at {SERVER_HOST}:{SERVER_PORT}")
        print("Error:", e)
        sys.exit()

    print(f"[CLIENT] Connected to server at {SERVER_HOST}:{SERVER_PORT}")

    # Starting listener thread
    threading.Thread(target=listener, daemon=True).start()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break

                # SPACE starts/restarts a round (request to server)
                if event.key == pygame.K_SPACE and state["phase"] in ("waiting", "finished"):
                    send_json({"type": "start"})

                # During playing phase, send "press" event for spam keys
                if state["phase"] == "playing" and event.key in SPAM_KEYS:
                    send_json({"type": "press"})

        # Map server state to display
        phase = state["phase"]
        countdown_left = max(0.0, state["countdown_left"])
        time_left = max(0.0, state["time_left"])

        # Timer display & color
        if phase == "countdown":
            display_time = int(math.ceil(countdown_left))
            if display_time in (3, 2):
                timer_color = (255, 0, 0)      
            elif display_time == 1:
                timer_color = (0, 180, 0)     
            else:
                timer_color = (0, 0, 0)

        elif phase == "playing":
            display_time = int(math.ceil(time_left))
            timer_color = (0, 0, 0)

        elif phase == "finished":
            display_time = 0
            timer_color = (0, 0, 0)

        else:  # waiting
            display_time = 10
            timer_color = (0, 0, 0)

        screen.fill((230, 230, 230))

        # Title
        draw_text("SPAM GAME", font_title, (0, 0, 0), (WIDTH // 2, 60))

        # Center text (instructions OR winner message)
        if phase in ("waiting", "countdown", "playing"):
            # Original three-line description
            draw_text("TAP Left and Right arrow keys", font_medium, (0, 0, 0),
                      (WIDTH // 2, 150))
            draw_text("AS FAST", font_medium, (0, 0, 0),
                      (WIDTH // 2, 190))
            draw_text("AS POSSIBLE", font_medium, (0, 0, 0),
                      (WIDTH // 2, 230))

        elif phase == "finished":
            # Winner logic
            p1 = state["p1_score"]
            p2 = state["p2_score"]

            if p1 > p2:
                winner_msg = "Player 1 wins!"
            elif p2 > p1:
                winner_msg = "Player 2 wins!"
            else:
                winner_msg = "Tie Game!"

            # Replace instructions with winner message
            draw_text(winner_msg, font_big, (0, 0, 0),
                      (WIDTH // 2, 180))

        # Scores
        draw_text("P1", font_big, (0, 0, 0), (WIDTH // 4 - 60, 160))
        draw_text(f"{state['p1_score']:02d}", font_big, (0, 0, 0),
                  (WIDTH // 4 - 60, 230))

        draw_text("P2", font_big, (0, 0, 0), (3 * WIDTH // 4 + 60, 160))
        draw_text(f"{state['p2_score']:02d}", font_big, (0, 0, 0),
                  (3 * WIDTH // 4 + 60, 230))

        # Timer box
        box_width, box_height = 140, 80
        box_rect = pygame.Rect(
            WIDTH // 2 - box_width // 2,
            320,
            box_width,
            box_height,
        )
        pygame.draw.rect(screen, (255, 255, 255), box_rect, border_radius=15)
        pygame.draw.rect(screen, (0, 0, 0), box_rect, width=3, border_radius=15)

        draw_text(str(display_time), font_big, timer_color, box_rect.center)

        # Bottom message
        if state["player_id"] is None:
            bottom_msg = "Connecting..."
        elif phase == "waiting":
            bottom_msg = f"Press SPACE to start. You are Player {state['player_id']}."
        elif phase == "countdown":
            bottom_msg = "Get ready..."
        elif phase == "playing":
            bottom_msg = "Spam LEFT and RIGHT!"
        else:  # finished
            bottom_msg = "Press SPACE to play again, or ESC to quit."

        draw_text(bottom_msg, font_small, (0, 0, 0),
                  (WIDTH // 2, HEIGHT - 40))

        pygame.display.flip()

    pygame.quit()
    try:
        sock.close()
    except OSError:
        pass
    sys.exit()


if __name__ == "__main__":
    main()
