import pygame
import sys
import math

# ================= CONFIG =================
WIDTH, HEIGHT = 600, 800
ROWS, COLS = 10, 6
CELL_SIZE = WIDTH // COLS
FPS = 60

# ================= INIT =================
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chain Reaction: Ultimate Fixed")
clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 30, bold=True)
small = pygame.font.SysFont("consolas", 18)
huge = pygame.font.SysFont("consolas", 60, bold=True)

# ================= SOUNDS =================
# Fallback to dummy sounds if files are missing to prevent crash
class DummySound:
    def play(self): pass
    def set_volume(self, v): pass

try:
    move_sound = pygame.mixer.Sound("movement.wav")
    explode_sound = pygame.mixer.Sound("click.wav")
    move_sound.set_volume(0.3)
    explode_sound.set_volume(0.5)
except Exception:
    move_sound = DummySound()
    explode_sound = DummySound()

# ================= COLORS & PLAYER MAPPING =================
PLAYER_COLORS = [
    (255, 60, 60),    # RED    (Player 1)
    (60, 220, 100),   # GREEN  (Player 2)
    (60, 100, 255),   # BLUE   (Player 3)
    (255, 200, 60),   # YELLOW (Player 4)
    (200, 60, 255),   # PURPLE (Player 5)
    (255, 100, 180),  # PINK   (Player 6)
    (60, 220, 220),   # CYAN   (Player 7)
    (220, 220, 220)   # WHITE  (Player 8)
]

# ================= THEMES =================
def theme_colors(theme="dark"):
    if theme == "dark":
        return {"BG": (15, 15, 15), "CELL": (30, 30, 30), "GRID": (50,50,50), "TEXT": (220, 220, 220)}
    else:
        return {"BG": (245, 245, 245), "CELL": (230, 230, 230), "GRID": (200,200,200), "TEXT": (30, 30, 30)}

current_theme = "dark"
colors = theme_colors(current_theme)

# ================= GAME STATE GLOBAL VARIABLES =================
# Board format: board[row][col] = [count, owner_index]
board = [[[0, -1] for _ in range(COLS)] for _ in range(ROWS)]
particles = []

num_players = 2 
players = []    
current_player = 0

player_alive = []
player_has_played = []

game_started = False
winner = None
popup_alpha = 0
turn_pending = False  # Flag to wait for animations before switching turns

# ================= UTIL =================
def capacity(r, c):
    """Returns the critical mass for a cell."""
    if (r in [0, ROWS-1]) and (c in [0, COLS-1]): return 1 # Corner
    if r in [0, ROWS-1] or c in [0, COLS-1]: return 2      # Edge
    return 3                                               # Middle

def center(r, c):
    """Returns pixel coordinates of the center of a grid cell."""
    return (c*CELL_SIZE + CELL_SIZE//2, r*CELL_SIZE + CELL_SIZE//2)

def blend(c1, c2, a=0.4):
    """Blends two RGB colors."""
    return tuple(int(c1[i]*(1-a) + c2[i]*a) for i in range(3))

# ================= DRAWING =================
def draw_cell(r, c):
    rect = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, colors["CELL"], rect)
    pygame.draw.rect(screen, colors["GRID"], rect, 1) # Simple grid border

    # Add a colored glow if owned
    if board[r][c][1] != -1:
        owner_col = players[board[r][c][1]]
        glow_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*owner_col, 30), glow_surf.get_rect())
        screen.blit(glow_surf, rect.topleft)

def draw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            draw_cell(r,c)

def draw_ball(x, y, color, r):
    # Shadow/Stroke
    pygame.draw.circle(screen, (0,0,0), (x+1, y+1), r)
    # Main Body
    pygame.draw.circle(screen, color, (x, y), r)
    # Highlight (Gloss)
    hi = tuple(min(255, v+80) for v in color)
    pygame.draw.circle(screen, hi, (x-r//3, y-r//3), r//3)

# ================= PARTICLES & LOGIC =================
class Particle:
    def __init__(self, start, end, color, target_idx):
        self.x, self.y = start
        self.tx, self.ty = end
        self.color = color
        self.target_idx = target_idx # (row, col, owner_id)
        self.speed = 20 # Increased speed for snappier gameplay

    def update(self):
        dx, dy = self.tx - self.x, self.ty - self.y
        dist = math.hypot(dx, dy)
        if dist < self.speed: 
            return True 
        
        self.x += self.speed * dx / dist
        self.y += self.speed * dy / dist
        return False

    def draw(self):
        draw_ball(int(self.x), int(self.y), self.color, 6)

def explode(r, c):
    explode_sound.play()
    owner = board[r][c][1]
    board[r][c] = [0, -1] # Reset cell
    sx, sy = center(r, c)

    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    for dr, dc in directions:
        nr, nc = r+dr, c+dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            ex, ey = center(nr, nc)
            particles.append(
                Particle((sx, sy), (ex, ey), players[owner], (nr, nc, owner))
            )

def update_particles():
    global turn_pending
    
    # Process particles
    active_particles = []
    explosion_triggered = False

    for p in particles:
        if p.update():
            # Particle reached target
            r, c, owner_id = p.target_idx
            board[r][c][0] += 1
            board[r][c][1] = owner_id 
            
            # Check for recursive explosion
            if board[r][c][0] > capacity(r, c):
                explode(r, c)
                explosion_triggered = True
        else:
            active_particles.append(p)
            
    particles[:] = active_particles

    # While particles exist, the turn is still processing
    if particles or explosion_triggered:
        turn_pending = True

def draw_orbs():
    # Rotational animation
    t = pygame.time.get_ticks() / 300
    for r in range(ROWS):
        for c in range(COLS):
            cnt, own = board[r][c]
            if cnt <= 0: continue
            
            cx, cy = center(r, c)
            cap = capacity(r, c)
            
            # Angle logic for multiple atoms
            if cnt == 1: angs = [0]
            elif cnt == 2: angs = [t, t + math.pi]
            else: angs = [t*3 + i*(2*math.pi/3) for i in range(3)]
            
            # Jitter vibration if critical mass
            vib = int(abs(math.sin(t*8))*3) if cnt == cap else 0
            
            for a in angs:
                ox = cx + int(math.cos(a)*10) + (vib if vib else 0)
                oy = cy + int(math.sin(a)*10) + (vib if vib else 0)
                draw_ball(ox, oy, players[own], 13)

# ================= ELIMINATION & TURNS =================

def check_game_over_state():
    """
    Checks player counts and determines if someone has won.
    Returns: Winner Index or None
    """
    # 1. Count total orbs for each player
    orb_counts = {i: 0 for i in range(num_players)}
    for r in range(ROWS):
        for c in range(COLS):
            owner = board[r][c][1]
            if owner != -1:
                orb_counts[owner] += 1
    
    # 2. Update Alive Status
    # A player is ALIVE if:
    # a) They have orbs on the board.
    # b) OR They haven't played their first turn yet (game start protection).
    
    survivors = []
    for i in range(num_players):
        if player_has_played[i]:
            if orb_counts[i] > 0:
                player_alive[i] = True
                survivors.append(i)
            else:
                player_alive[i] = False # ELIMINATED
        else:
            # Hasn't played yet, so they are safe for now
            player_alive[i] = True
            survivors.append(i)

    # 3. Check for Winner
    # We need at least 2 people to have played to declare a winner.
    if sum(player_has_played) > 1:
        if len(survivors) == 1:
            return survivors[0]
            
    return None

def next_player():
    global current_player
    
    # Cycle through players until we find an alive one
    original_idx = current_player
    for _ in range(num_players):
        current_player = (current_player + 1) % num_players
        if player_alive[current_player]:
            return
            
    # If we loop and find no one (shouldn't happen with win check), stick to original
    current_player = original_idx

def handle_click(pos):
    global turn_pending, player_has_played
    
    # Block input if waiting for animations or game over
    if winner is not None or particles or turn_pending: 
        return

    x, y = pos
    c, r = x // CELL_SIZE, y // CELL_SIZE
    
    # Bounds check
    if not (0 <= r < ROWS and 0 <= c < COLS): return

    cnt, own = board[r][c]
    
    # Valid Move: Empty cell OR cell owned by current player
    if own == -1 or own == current_player:
        move_sound.play()
        
        board[r][c][0] += 1
        board[r][c][1] = current_player
        player_has_played[current_player] = True
        
        # Check for immediate explosion
        if board[r][c][0] > capacity(r, c):
            explode(r, c)
            turn_pending = True 
        else:
            # Even if no explosion, we set this to true so the main loop
            # handles the turn switch logic consistently in one place
            turn_pending = True 

# ================= MENU & UI =================
def draw_menu():
    screen.fill(colors["BG"])
    
    # Card Background
    panel = pygame.Rect(60, 140, 480, 440)
    pygame.draw.rect(screen, (30, 30, 30), panel, border_radius=20)
    pygame.draw.rect(screen, (100, 100, 100), panel, 2, border_radius=20)

    # Title
    title = huge.render("CHAIN REACTION", True, colors["TEXT"])
    s_rect = title.get_rect(center=(WIDTH//2, 100))
    # Simple shadow
    s_shad = huge.render("CHAIN REACTION", True, (0,0,0))
    screen.blit(s_shad, (s_rect.x+3, s_rect.y+3))
    screen.blit(title, s_rect)

    # Player Select
    t_pl = font.render(f"Players: {num_players}", True, (255, 255, 255))
    screen.blit(t_pl, t_pl.get_rect(center=(WIDTH//2, 250)))
    
    # Arrows logic visualized
    pygame.draw.polygon(screen, (200,200,200), [(180, 250), (200, 230), (200, 270)]) # Left arrow
    pygame.draw.polygon(screen, (200,200,200), [(420, 250), (400, 230), (400, 270)]) # Right arrow

    t_help = small.render("(Click Left/Right side to change)", True, (150,150,150))
    screen.blit(t_help, t_help.get_rect(center=(WIDTH//2, 280)))
    
    # Theme Toggle
    t_thm = small.render("[T] Toggle Theme (Dark/Light)", True, (180, 180, 180))
    screen.blit(t_thm, t_thm.get_rect(center=(WIDTH//2, 400)))

    # Start Button
    btn_rect = pygame.Rect(WIDTH//2 - 100, 480, 200, 60)
    pygame.draw.rect(screen, (50, 200, 80), btn_rect, border_radius=10)
    t_start = font.render("START GAME", True, (255,255,255))
    screen.blit(t_start, t_start.get_rect(center=btn_rect.center))
    
    # Player Previews
    gap = 40
    start_x = (WIDTH - (num_players * gap)) // 2 + 20
    for i in range(num_players):
        pygame.draw.circle(screen, PLAYER_COLORS[i], (start_x + i*gap, 210), 12)

def menu_click(pos):
    global num_players, players, game_started, board, player_alive, player_has_played
    x, y = pos
    
    # Player Count Slider
    if 230 < y < 290:
        if x < WIDTH // 2: num_players = max(2, num_players - 1)
        else: num_players = min(8, num_players + 1)
    
    # Start Button
    elif 480 < y < 540 and WIDTH//2 - 100 < x < WIDTH//2 + 100:
        players = PLAYER_COLORS[:num_players]
        reset_game()
        game_started = True

def reset_game():
    global board, particles, current_player, player_alive, player_has_played, winner, popup_alpha, turn_pending
    board = [[[0, -1] for _ in range(COLS)] for _ in range(ROWS)]
    particles.clear()
    current_player = 0
    player_alive = [True] * num_players
    player_has_played = [False] * num_players
    winner = None
    popup_alpha = 0
    turn_pending = False

def draw_winner_popup():
    global popup_alpha
    popup_alpha = min(220, popup_alpha + 5)
    
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(popup_alpha)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    if winner is not None:
        col = players[winner]
        
        # Trophy/Win Text
        win_text = f"PLAYER {winner + 1}"
        sub_text = "WINS THE GAME!"
        
        lbl = huge.render(win_text, True, col)
        lbl2 = font.render(sub_text, True, (255,255,255))
        
        screen.blit(lbl, lbl.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
        screen.blit(lbl2, lbl2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
        
        msg = small.render("Click anywhere to Restart", True, (150, 150, 150))
        screen.blit(msg, msg.get_rect(center=(WIDTH//2, HEIGHT//2 + 80)))

def draw_ui():
    # Bottom UI Bar
    bar_rect = pygame.Rect(0, HEIGHT-50, WIDTH, 50)
    pygame.draw.rect(screen, colors["BG"], bar_rect)
    pygame.draw.line(screen, players[current_player], (0, HEIGHT-50), (WIDTH, HEIGHT-50), 3)

    turn_text = f"PLAYER {current_player + 1}'s TURN"
    tsurf = font.render(turn_text, True, players[current_player])
    screen.blit(tsurf, tsurf.get_rect(center=(WIDTH//2, HEIGHT-25)))

# ================= MAIN LOOP =================
while True:
    dt = clock.tick(FPS)
    screen.fill(colors["BG"])

    # Event Handling
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_t:
                current_theme = "light" if current_theme == "dark" else "dark"
                colors = theme_colors(current_theme)
        if e.type == pygame.MOUSEBUTTONDOWN:
            if not game_started: menu_click(e.pos)
            elif winner is not None: game_started = False # Click to restart
            else: handle_click(e.pos)

    if not game_started:
        draw_menu()
    else:
        # Game Play
        draw_grid()
        draw_orbs()
        
        # Particle Animation
        update_particles()
        for p in particles: p.draw()

        # ================= CORE LOGIC UPDATE =================
        # Only process Game Logic (Winning/Turns) when animations settle
        if turn_pending and len(particles) == 0:
            
            # 1. Check if anyone died or won
            winner = check_game_over_state()
            
            # 2. If game continues, switch to next valid player
            if winner is None:
                next_player()
            
            # 3. Mark turn as fully complete
            turn_pending = False

        # UI Overlays
        if winner is not None:
            draw_winner_popup()
        else:
            draw_ui()

    pygame.display.update()