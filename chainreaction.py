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
pygame.display.set_caption("Chain Reaction 3D")
clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 30)
small = pygame.font.SysFont("consolas", 18)
huge = pygame.font.SysFont("consolas", 60)

# ================= SOUNDS =================
# Added try/except so game runs even if sound files are missing
try:
    move_sound = pygame.mixer.Sound("movement.wav")
    explode_sound = pygame.mixer.Sound("click.wav")
    move_sound.set_volume(0.3)
    explode_sound.set_volume(0.6)
except Exception as e:
    print("Sound files not found, running in silent mode.")
    class DummySound:
        def play(self): pass
        def set_volume(self, v): pass
    move_sound = DummySound()
    explode_sound = DummySound()

# ================= COLORS & NAMES =================
# Mapped specific names to the colors for the Win Message
PLAYER_COLORS = [
    (255, 80, 80),    # RED
    (80, 220, 120),   # GREEN
    (80, 120, 255),   # BLUE
    (255, 200, 80),   # YELLOW
    (200, 80, 255),   # PURPLE
    (255, 120, 180),  # PINK
    (80, 220, 220),   # CYAN
    (220, 220, 220)   # WHITE
]

PLAYER_NAMES = [
    "RED", "GREEN", "BLUE", "YELLOW", 
    "PURPLE", "PINK", "CYAN", "WHITE"
]

# ================= THEMES =================
def theme_colors(theme="dark"):
    if theme == "dark":
        return {"BG": (10,10,10), "CELL": (30,30,30), "TEXT": (220,220,220)}
    else:
        return {"BG": (245,245,245), "CELL": (220,220,220), "TEXT": (30,30,30)}

current_theme = "dark"
colors = theme_colors(current_theme)

# ================= GAME STATE =================
board = [[[0, -1] for _ in range(COLS)] for _ in range(ROWS)]
particles = []

num_players = 2
players = []       # Stores active colors
player_names = []  # Stores active names
current_player = 0

player_alive = []
player_has_played = []

game_started = False
initial_phase = True
winner = None
popup_alpha = 0

# ================= UTIL =================
def capacity(r, c):
    """ Returns the max atoms a cell can hold before exploding """
    if (r in [0, ROWS-1]) and (c in [0, COLS-1]): return 1 # Corners
    if r in [0, ROWS-1] or c in [0, COLS-1]: return 2      # Edges
    return 3                                               # Middle

def center(r, c):
    return (c*CELL_SIZE + CELL_SIZE//2,
            r*CELL_SIZE + CELL_SIZE//2)

def blend(c1, c2, a=0.4):
    return tuple(int(c1[i]*(1-a) + c2[i]*a) for i in range(3))

# ================= DRAW GRID =================
def draw_cell(r, c):
    rect = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, colors["CELL"], rect)

    # Grid lines color is based on current player turn
    col = players[current_player]
    sh = blend(col, (0,0,0), 0.6)

    pygame.draw.line(screen, col, rect.topleft, rect.topright, 2)
    pygame.draw.line(screen, col, rect.topleft, rect.bottomleft, 2)
    pygame.draw.line(screen, sh, rect.bottomleft, rect.bottomright, 2)
    pygame.draw.line(screen, sh, rect.topright, rect.bottomright, 2)

def draw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            draw_cell(r,c)

def draw_ball(x,y,color,r):
    pygame.draw.circle(screen,(0,0,0),(x+3,y+3),r)
    pygame.draw.circle(screen,color,(x,y),r)
    hi = tuple(min(255,v+60) for v in color)
    pygame.draw.circle(screen,hi,(x-r//3,y-r//3),r//3)

# ================= PARTICLES =================
class Particle:
    def __init__(self,start,end,color,target):
        self.x,self.y = start
        self.tx,self.ty = end
        self.color = color
        self.target = target # (row, col, owner_id)
        self.speed = 15 # Increased speed slightly for better feel

    def update(self):
        dx,dy = self.tx-self.x, self.ty-self.y
        d = math.hypot(dx,dy)
        if d < self.speed: return True
        self.x += self.speed*dx/d
        self.y += self.speed*dy/d
        return False

    def draw(self):
        draw_ball(int(self.x),int(self.y),self.color,10)

# ================= GAME LOGIC =================
def explode(r,c):
    explode_sound.play()
    owner = board[r][c][1]
    board[r][c] = [0,-1] # Reset the exploding cell
    sx,sy = center(r,c)

    # Create particles for neighbors
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr,nc = r+dr,c+dc
        if 0<=nr<ROWS and 0<=nc<COLS:
            ex,ey = center(nr,nc)
            particles.append(
                Particle((sx,sy),(ex,ey),players[owner],(nr,nc,owner))
            )

def update_particles():
    # Process particles
    for p in particles[:]:
        if p.update():
            r,c,o = p.target
            
            # ATOM CAPTURE LOGIC
            # If particle hits a cell, it increases count and changes owner
            board[r][c][0]+=1
            board[r][c][1]=o 
            
            # Check for chain reaction
            if board[r][c][0] > capacity(r,c):
                explode(r,c)
            
            particles.remove(p)

def draw_orbs():
    t = pygame.time.get_ticks()/300
    for r in range(ROWS):
        for c in range(COLS):
            cnt,own = board[r][c]
            if cnt<=0: continue
            cx,cy = center(r,c)
            cap = capacity(r,c)

            # Spin logic
            if cnt==1:
                angs=[0]
            elif cnt==2:
                angs=[t,t+math.pi]
            else:
                angs=[t*3+i*2*math.pi/3 for i in range(3)]

            # Jitter if critical mass
            vib = int(abs(math.sin(t*4))*6) if cnt==cap else 1
            
            for a in angs:
                draw_ball(
                    cx+int(math.cos(a)*8)+vib,
                    cy+int(math.sin(a)*8)+vib,
                    players[own],15
                )

# ================= TURN & ELIMINATION =================
def next_player():
    global current_player
    # Cycle through players until we find one that is alive
    while True:
        current_player = (current_player + 1) % num_players
        if player_alive[current_player]: 
            break

def handle_click(pos):
    global initial_phase
    if winner is not None: return

    x,y=pos
    c,r=x//CELL_SIZE,y//CELL_SIZE
    if r>=ROWS or c>=COLS: return

    cnt,own=board[r][c]
    
    # Valid Move: Empty cell OR Cell owned by current player
    if own in (-1,current_player):
        move_sound.play()
        board[r][c][0]+=1
        board[r][c][1]=current_player
        player_has_played[current_player]=True
        
        # Check instant explosion on placement
        if board[r][c][0]>capacity(r,c):
            explode(r,c)
            
        # End initial phase if everyone has played at least once
        if initial_phase and all(player_has_played):
            initial_phase=False
            
        next_player()

def check_winner():
    # Don't check for elimination until everyone has placed their first orb
    if initial_phase: return None
    
    # Calculate which players still have orbs on the board
    alive_indices = set()
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c][0] > 0:
                alive_indices.add(board[r][c][1])
    
    # Update global elimination status
    for i in range(num_players):
        player_alive[i] = (i in alive_indices)
        
    # Win condition: Only 1 player remains in the alive set
    if len(alive_indices) == 1:
        return alive_indices.pop()
        
    return None

# ================= MENU =================
def draw_menu():
    screen.fill(colors["BG"])
    panel = pygame.Rect(80,140,440,420)
    pygame.draw.rect(screen,(20,20,20),panel, border_radius=20)
    pygame.draw.rect(screen,(80,80,80),panel,2, border_radius=20)

    screen.blit(font.render("CHAIN REACTION",True,colors["TEXT"]),(170,170))
    screen.blit(font.render(f"Players: {num_players}",True,colors["TEXT"]),(210,240))
    screen.blit(small.render("Click LEFT / RIGHT to change",True,colors["TEXT"]),(180,270))
    screen.blit(small.render("Press T : Toggle Theme",True,colors["TEXT"]),(200,310))
    screen.blit(font.render("CLICK TO START",True,colors["TEXT"]),(185,360))

def menu_click(pos):
    global num_players, players, player_names, game_started
    x,y=pos
    if 230<y<280:
        if x<WIDTH//2: num_players=max(2,num_players-1)
        else: num_players=min(8,num_players+1)
    elif y>340:
        # Initialize players and names based on selection
        players = PLAYER_COLORS[:num_players]
        player_names = PLAYER_NAMES[:num_players]
        reset_game()
        game_started=True

def reset_game():
    global board,particles,current_player,player_alive,player_has_played,initial_phase,winner,popup_alpha
    board=[[[0,-1] for _ in range(COLS)] for _ in range(ROWS)]
    particles.clear()
    current_player=0
    player_alive=[True]*num_players
    player_has_played=[False]*num_players
    initial_phase=True
    winner=None
    popup_alpha=0

# ================= WIN POPUP =================
def draw_winner_popup():
    global popup_alpha
    popup_alpha=min(180,popup_alpha+2)

    overlay=pygame.Surface((WIDTH,HEIGHT))
    overlay.set_alpha(popup_alpha)
    overlay.fill((0,0,0))
    screen.blit(overlay,(0,0))

    scale=1+popup_alpha/300
    
    # Display the specific color name
    win_name = player_names[winner]
    text = huge.render(f"{win_name} WINS!", True, players[winner])
    
    rect=text.get_rect(center=(WIDTH//2,HEIGHT//2))
    screen.blit(text,rect)
    
    sub = small.render("Click to Restart", True, (200,200,200))
    sub_rect = sub.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
    screen.blit(sub, sub_rect)

# ================= MAIN LOOP =================
while True:
    clock.tick(FPS)
    screen.fill(colors["BG"])

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if e.type==pygame.KEYDOWN and e.key==pygame.K_t:
            current_theme="light" if current_theme=="dark" else "dark"
            colors=theme_colors(current_theme)
        if e.type==pygame.MOUSEBUTTONDOWN:
            if not game_started: 
                menu_click(e.pos)
            elif winner is not None: 
                game_started = False # Click after win goes back to menu
            else: 
                handle_click(e.pos)

    if not game_started:
        draw_menu()
    else:
        draw_grid()
        draw_orbs()
        update_particles()
        for p in particles: p.draw()

        if winner is None:
            winner = check_winner()
            
        if winner is not None:
            draw_winner_popup()

    pygame.display.update()