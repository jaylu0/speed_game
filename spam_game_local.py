import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spam Game (Local)")

clock = pygame.time.Clock()

# Fonts
font_title = pygame.font.Font(None, 80)
font_big = pygame.font.Font(None, 64)
font_medium = pygame.font.Font(None, 42)
font_small = pygame.font.Font(None, 30)

# --- Game config ---
ROUND_DURATION = 10.0       # seconds for main round
COUNTDOWN_DURATION = 3.0    # seconds before round starts

# --- Key bindings ---
P1_KEYS = {pygame.K_a, pygame.K_d}                  # Player 1: A / D
P2_KEYS = {pygame.K_LEFT, pygame.K_RIGHT}           # Player 2: ← / →

# --- Game state ---
scores = {1: 0, 2: 0}

phase = "waiting"           # "waiting", "countdown", "playing", "finished"
start_time = None           # for main round
countdown_start = None      # for pre-round countdown
time_left = ROUND_DURATION  # main timer
countdown_left = COUNTDOWN_DURATION


def draw_text(text, font, color, center):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    screen.blit(surf, rect)


running = True
while running:
    dt = clock.tick(60) / 1000.0  # delta time in seconds

    # ------------- EVENTS -------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                break

            # SPACE starts a new round from waiting/finished
            if event.key == pygame.K_SPACE and phase in ("waiting", "finished"):
                scores = {1: 0, 2: 0}
                phase = "countdown"
                countdown_start = pygame.time.get_ticks() / 1000.0
                countdown_left = COUNTDOWN_DURATION
                time_left = ROUND_DURATION

            # During active main round, count presses
            if phase == "playing":
                if event.key in P1_KEYS:
                    scores[1] += 1
                if event.key in P2_KEYS:
                    scores[2] += 1

    # ------------- UPDATE TIMERS -------------
    now_sec = pygame.time.get_ticks() / 1000.0

    if phase == "countdown":
        elapsed = now_sec - countdown_start
        countdown_left = max(0.0, COUNTDOWN_DURATION - elapsed)
        if countdown_left <= 0:
            # Switch into main round
            phase = "playing"
            start_time = now_sec
            time_left = ROUND_DURATION

    elif phase == "playing":
        elapsed = now_sec - start_time
        time_left = max(0.0, ROUND_DURATION - elapsed)
        if time_left <= 0:
            time_left = 0.0
            phase = "finished"

    # Decide what to show in the timer box
    if phase == "countdown":
        display_time = int(math.ceil(countdown_left))

        # ---------- NEW COLOR LOGIC ----------
        if display_time in (3, 2):
            timer_color = (255, 0, 0)     # red
        elif display_time == 1:
            timer_color = (0, 180, 0)     # green
        else:
            timer_color = (0, 0, 0)
        # -------------------------------------

    elif phase == "playing":
        display_time = int(math.ceil(time_left))
        timer_color = (0, 0, 0)    # black during round

    elif phase == "finished":
        display_time = 0
        timer_color = (0, 0, 0)

    else:  # waiting
        display_time = 10
        timer_color = (0, 0, 0)

    # ------------- DRAW UI -------------
    screen.fill((230, 230, 230))  # light background

    # Title (top center)
    draw_text("SPAM GAME", font_title, (0, 0, 0), (WIDTH // 2, 60))

    # Center instructions
    # Center text changes depending on phase
    if phase in ("waiting", "countdown", "playing"):
        # Original instructions
        draw_text("TAP Left and Right arrow keys", font_medium, (0, 0, 0), (WIDTH // 2, 150))
        draw_text("AS FAST", font_medium, (0, 0, 0), (WIDTH // 2, 190))
        draw_text("AS POSSIBLE", font_medium, (0, 0, 0), (WIDTH // 2, 230))

    elif phase == "finished":
        # Winner logic
        if scores[1] > scores[2]:
            winner_msg = "Player 1 wins!"
        elif scores[2] > scores[1]:
            winner_msg = "Player 2 wins!"
        else:
            winner_msg = "Tie Game!"

        draw_text(winner_msg, font_big, (0, 0, 0), (WIDTH // 2, 180))

    # P1 label and score (left side)
    draw_text("P1", font_big, (0, 0, 0), (WIDTH // 4 - 60, 160))
    draw_text(f"{scores[1]:02d}", font_big, (0, 0, 0),
              (WIDTH // 4 - 60, 230))

    # P2 label and score (right side)
    draw_text("P2", font_big, (0, 0, 0), (3 * WIDTH // 4 + 60, 160))
    draw_text(f"{scores[2]:02d}", font_big, (0, 0, 0),
              (3 * WIDTH // 4 + 60, 230))

    # Timer box in the lower middle
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

    # Bottom hint text
    if phase == "waiting":
        draw_text("Press SPACE to start", font_small, (0, 0, 0),
                  (WIDTH // 2, HEIGHT - 40))
    elif phase == "countdown":
        draw_text("Get ready...", font_small, (0, 0, 0),
                  (WIDTH // 2, HEIGHT - 40))
    elif phase == "playing":
        draw_text("P1: A / D     P2: <- / ->",
                  font_small, (0, 0, 0), (WIDTH // 2, HEIGHT - 40))
    elif phase == "finished":
        draw_text("Time's up! Press SPACE to play again, ESC to quit.",
                  font_small, (0, 0, 0), (WIDTH // 2, HEIGHT - 40))

    pygame.display.flip()

pygame.quit()
sys.exit()

