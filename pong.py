import pygame
import sys
import random
import time

pygame.init()

# ---------------- SCREEN ----------------
WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong | Stranger Mode")

# ---------------- COLORS ----------------
WHITE = (240, 240, 240)
RED = (180, 30, 30)
NEON_RED = (255, 60, 60)
BLUE = (60, 120, 255)
BLACK = (5, 5, 5)

# ---------------- THEMES ----------------
THEMES = {
    "Dark": BLACK,
    "Neon": (20, 0, 0),
    "Retro": (0, 10, 30)
}

BALL_TYPES = ["Classic", "Neon", "Pixel"]

current_theme = "Dark"
current_ball = "Classic"

# ---------------- FONTS ----------------
font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 60)
count_font = pygame.font.Font(None, 120)

clock = pygame.time.Clock()

# ---------------- GAME SETTINGS ----------------
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 80
PADDLE_SPEED = 6
BALL_SIZE = 15

# ---------------- GAME STATE ----------------
menu = True
paused = False
countdown_active = False
countdown_start = 0

customize_menu = False
theme_menu = False
ball_menu = False

# ---------------- BUTTONS ----------------
pause_button = pygame.Rect(WIDTH - 110, 10, 100, 35)
menu_button = pygame.Rect(WIDTH - 230, 10, 110, 35)

# ---------------- GAME OBJECTS ----------------
def reset_game():
    global left_paddle, right_paddle, ball
    global ball_speed_x, ball_speed_y
    global left_score, right_score

    left_paddle = pygame.Rect(30, HEIGHT//2 - PADDLE_HEIGHT//2,
                              PADDLE_WIDTH, PADDLE_HEIGHT)
    right_paddle = pygame.Rect(WIDTH - 40, HEIGHT//2 - PADDLE_HEIGHT//2,
                               PADDLE_WIDTH, PADDLE_HEIGHT)

    ball = pygame.Rect(WIDTH//2, HEIGHT//2, BALL_SIZE, BALL_SIZE)
    ball_speed_x = random.choice([-5, 5])
    ball_speed_y = random.choice([-5, 5])

    left_score = 0
    right_score = 0

reset_game()

# ---------------- UI HELPERS ----------------
def glow(rect, color):
    surf = pygame.Surface((rect.width + 14, rect.height + 14))
    surf.set_alpha(80)
    surf.fill(color)
    screen.blit(surf, (rect.x - 7, rect.y - 7))

def button(text, rect):
    hover = rect.collidepoint(pygame.mouse.get_pos())
    if hover:
        glow(rect, NEON_RED)
        pygame.draw.rect(screen, RED, rect, border_radius=10)
    else:
        pygame.draw.rect(screen, (100, 0, 0), rect, border_radius=10)

    pygame.draw.rect(screen, NEON_RED, rect, 2, border_radius=10)
    label = font.render(text, True, WHITE)
    screen.blit(label, label.get_rect(center=rect.center))

def draw_ball():
    if current_ball == "Classic":
        pygame.draw.ellipse(screen, WHITE, ball)
    elif current_ball == "Neon":
        glow(ball, NEON_RED)
        pygame.draw.ellipse(screen, NEON_RED, ball)
    elif current_ball == "Pixel":
        pygame.draw.rect(screen, WHITE, ball)

def draw_center_line():
    for y in range(0, HEIGHT, 22):
        pygame.draw.line(screen, RED, (WIDTH//2, y), (WIDTH//2, y + 12), 2)

def pause_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(170)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    text = title_font.render("PAUSED", True, NEON_RED)
    screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))

def draw_countdown():
    remaining = 3 - int(time.time() - countdown_start)
    if remaining > 0:
        text = count_font.render(str(remaining), True, NEON_RED)
        screen.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        return True
    return False

# ---------------- MENUS ----------------
def main_menu():
    screen.fill(THEMES[current_theme])
    title = title_font.render("PONG GAME", True, NEON_RED)
    screen.blit(title, title.get_rect(center=(WIDTH//2, 80)))

    btns = {
        "new": pygame.Rect(WIDTH//2 - 100, 160, 200, 45),
        "custom": pygame.Rect(WIDTH//2 - 100, 220, 200, 45),
        "exit": pygame.Rect(WIDTH//2 - 100, 280, 200, 45)
    }

    button("New Game", btns["new"])
    button("Customize", btns["custom"])
    button("Exit", btns["exit"])

    pygame.display.flip()
    return btns

def customize_menu_screen():
    screen.fill(THEMES[current_theme])
    title = title_font.render("CUSTOMIZE", True, NEON_RED)
    screen.blit(title, title.get_rect(center=(WIDTH//2, 80)))

    btns = {
        "theme": pygame.Rect(WIDTH//2 - 100, 180, 200, 45),
        "ball": pygame.Rect(WIDTH//2 - 100, 240, 200, 45),
        "back": pygame.Rect(WIDTH//2 - 100, 300, 200, 45)
    }

    button("Theme", btns["theme"])
    button("Ball", btns["ball"])
    button("Back", btns["back"])

    pygame.display.flip()
    return btns

def theme_menu_screen():
    screen.fill(THEMES[current_theme])
    title = title_font.render("THEMES", True, NEON_RED)
    screen.blit(title, title.get_rect(center=(WIDTH//2, 80)))

    btns = {}
    y = 160
    for theme in THEMES:
        btns[theme] = pygame.Rect(WIDTH//2 - 100, y, 200, 45)
        button(theme, btns[theme])
        y += 60

    btns["back"] = pygame.Rect(WIDTH//2 - 100, y, 200, 45)
    button("Back", btns["back"])

    pygame.display.flip()
    return btns

def ball_menu_screen():
    screen.fill(THEMES[current_theme])
    title = title_font.render("BALLS", True, NEON_RED)
    screen.blit(title, title.get_rect(center=(WIDTH//2, 80)))

    btns = {}
    y = 160
    for b in BALL_TYPES:
        btns[b] = pygame.Rect(WIDTH//2 - 100, y, 200, 45)
        button(b, btns[b])
        y += 60

    btns["back"] = pygame.Rect(WIDTH//2 - 100, y, 200, 45)
    button("Back", btns["back"])

    pygame.display.flip()
    return btns

# ---------------- GAME DRAW ----------------
def draw_game():
    screen.fill(THEMES[current_theme])
    draw_center_line()

    pygame.draw.rect(screen, WHITE, left_paddle, border_radius=4)
    pygame.draw.rect(screen, WHITE, right_paddle, border_radius=4)
    draw_ball()

    score = title_font.render(f"{left_score}   {right_score}", True, RED)
    screen.blit(score, score.get_rect(center=(WIDTH//2, 35)))

    button("Menu", menu_button)
    button("Resume" if paused else "Pause", pause_button)

    pygame.display.flip()

# ---------------- MAIN LOOP ----------------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # MAIN MENU
        if menu and not customize_menu and not theme_menu and not ball_menu and event.type == pygame.MOUSEBUTTONDOWN:
            btn = main_menu()
            if btn["new"].collidepoint(event.pos):
                reset_game()
                menu = False
            elif btn["custom"].collidepoint(event.pos):
                customize_menu = True
            elif btn["exit"].collidepoint(event.pos):
                pygame.quit()
                sys.exit()

        # CUSTOMIZE MENU
        if customize_menu and event.type == pygame.MOUSEBUTTONDOWN:
            btn = customize_menu_screen()
            if btn["theme"].collidepoint(event.pos):
                customize_menu = False
                theme_menu = True
            elif btn["ball"].collidepoint(event.pos):
                customize_menu = False
                ball_menu = True
            elif btn["back"].collidepoint(event.pos):
                customize_menu = False

        # THEME MENU
        if theme_menu and event.type == pygame.MOUSEBUTTONDOWN:
            btn = theme_menu_screen()
            for t in THEMES:
                if btn[t].collidepoint(event.pos):
                    current_theme = t
            if btn["back"].collidepoint(event.pos):
                theme_menu = False
                customize_menu = True

        # BALL MENU
        if ball_menu and event.type == pygame.MOUSEBUTTONDOWN:
            btn = ball_menu_screen()
            for b in BALL_TYPES:
                if btn[b].collidepoint(event.pos):
                    current_ball = b
            if btn["back"].collidepoint(event.pos):
                ball_menu = False
                customize_menu = True

        # IN GAME
        if not menu and event.type == pygame.MOUSEBUTTONDOWN:
            if pause_button.collidepoint(event.pos):
                paused = not paused
                if not paused:
                    countdown_active = True
                    countdown_start = time.time()
            elif menu_button.collidepoint(event.pos):
                menu = True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            paused = not paused
            if not paused:
                countdown_active = True
                countdown_start = time.time()

    # MENU STATES
    if menu:
        if customize_menu:
            customize_menu_screen()
        elif theme_menu:
            theme_menu_screen()
        elif ball_menu:
            ball_menu_screen()
        else:
            main_menu()
        clock.tick(60)
        continue

    if paused:
        draw_game()
        pause_overlay()
        clock.tick(60)
        continue

    if countdown_active:
        draw_game()
        if not draw_countdown():
            countdown_active = False
        pygame.display.flip()
        clock.tick(60)
        continue

    # GAME LOGIC
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and left_paddle.top > 0:
        left_paddle.y -= PADDLE_SPEED
    if keys[pygame.K_s] and left_paddle.bottom < HEIGHT:
        left_paddle.y += PADDLE_SPEED

    if keys[pygame.K_UP] and right_paddle.top > 0:
        right_paddle.y -= PADDLE_SPEED
    if keys[pygame.K_DOWN] and right_paddle.bottom < HEIGHT:
        right_paddle.y += PADDLE_SPEED

    ball.x += ball_speed_x
    ball.y += ball_speed_y

    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_speed_y *= -1

    if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
        ball_speed_x *= -1

    if ball.left <= 0:
        right_score += 1
        ball.center = (WIDTH//2, HEIGHT//2)

    if ball.right >= WIDTH:
        left_score += 1
        ball.center = (WIDTH//2, HEIGHT//2)

    draw_game()
    clock.tick(60)
