import pygame
import random
import sys
import math
import pickle
from collections import defaultdict

# ────────────────────────────────────────────────
# 1. AD SYSTEM & SAVE LOGIC
# ────────────────────────────────────────────────
class AdSystem:
    def __init__(self):
        self.interstitial_frequency = 3 
        self.reward_amount = 5          
        
    def show_interstitial(self, current_lvl):
        if current_lvl % self.interstitial_frequency == 0:
            print(f"[ADMOB] Level {current_lvl} Interstitial Triggered")
            return True
        return False

    def show_rewarded_video(self):
        print("[ADMOB] Rewarded Video Playing...")
        return True 

ads = AdSystem()

# ────────────────────────────────────────────────
# 2. SETTINGS & INITIALIZATION
# ────────────────────────────────────────────────
WIDTH, HEIGHT = 600, 780
GRID_SIZE, CELL_SIZE = 8, 60
GRID_OFFSET_X, GRID_OFFSET_Y = (WIDTH - 8 * 60) // 2, 220
FPS = 60

COLORS = [(255, 100, 100), (255, 180, 80), (80, 200, 80), (80, 80, 255), (200, 80, 200), (255, 220, 80), (255, 120, 180)]
BG_COLOR, GRID_COLOR = (10, 15, 30), (40, 50, 75)
WHITE, RED, GREEN, GOLD, BLUE = (245, 245, 245), (255, 80, 80), (80, 220, 80), (255, 215, 0), (80, 150, 255)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 32, bold=True)
small_font = pygame.font.SysFont("arial", 22, bold=True)
tiny_font = pygame.font.SysFont("arial", 18, bold=True)

def play_tone(freq, duration, vol=0.3):
    try:
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            val = int(vol * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            buf[i*2:i*2+2] = val.to_bytes(2, 'little', signed=True)
        pygame.mixer.Sound(buffer=buf).play()
    except: pass

# ────────────────────────────────────────────────
# 3. GAME STATE & SAVE/LOAD
# ────────────────────────────────────────────────
level, score, moves_left = 1, 0, 30
objective_type, objective_target, objective_progress, objective_color_idx = "SCORE", 1000, 0, 0
grid = [[random.randint(0, 6) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
current_theme = 0
THEME_NAMES = ["MODERN", "CLASSIC", "ZEN", "NEON"]
paused, show_roadmap, game_over = False, False, False
selected = None

def save_game_data():
    try:
        data = {"level": level, "score": score, "theme": current_theme}
        with open("savegame.dat", "wb") as f: pickle.dump(data, f)
    except: pass

def load_game_data():
    global level, score, current_theme
    try:
        with open("savegame.dat", "rb") as f:
            data = pickle.load(f)
            level = data.get("level", 1)
            score = data.get("score", 0)
            current_theme = data.get("theme", 0)
    except: pass

load_game_data()

# ────────────────────────────────────────────────
# 4. ENGINE LOGIC
# ────────────────────────────────────────────────
def setup_mission():
    global objective_type, objective_target, objective_progress, objective_color_idx, moves_left, game_over
    objective_progress = 0
    moves_left = 25 + (level * 2)
    game_over = False
    if level % 4 == 0: objective_type = "SPECIAL"; objective_target = 3 + (level // 4)
    elif level % 2 == 0:
        objective_type = "COLOR"; objective_color_idx = random.randint(0, 6); objective_target = 20 + (level * 5)
    else: objective_type = "SCORE"; objective_target = 1000 + (level * 500)
    save_game_data()

def find_matches():
    to_remove = set()
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE-2):
            if grid[r][c] == grid[r][c+1] == grid[r][c+2] and 0 <= grid[r][c] < 7:
                to_remove.update([(r,c), (r,c+1), (r,c+2)])
    for c in range(GRID_SIZE):
        for r in range(GRID_SIZE-2):
            if grid[r][c] == grid[r+1][c] == grid[r+2][c] and 0 <= grid[r][c] < 7:
                to_remove.update([(r,c), (r+1,c), (r+2,c)])
    return list(to_remove)

def refill_grid():
    for c in range(GRID_SIZE):
        col = [grid[r][c] for r in range(GRID_SIZE) if grid[r][c] != -1]
        for r in range(GRID_SIZE - len(col)): grid[r][c] = random.randint(0, 6)
        for i, val in enumerate(col): grid[GRID_SIZE - len(col) + i][c] = val

def process_board():
    global score, objective_progress
    while True:
        matches = find_matches()
        if not matches: break
        play_tone(800 + (len(matches)*50), 0.1)
        for r, c in matches:
            if objective_type == "COLOR" and grid[r][c] == objective_color_idx: objective_progress += 1
            grid[r][c] = -1
        score += len(matches) * 20
        if objective_type == "SCORE": objective_progress += len(matches) * 20
        refill_grid()

def activate_special(r, c):
    global objective_progress, score
    typ = grid[r][c]
    play_tone(400, 0.2, 0.5)
    if typ in [7, 8]:
        for i in range(GRID_SIZE):
            if typ == 7: # H
                if 0 <= grid[r][i] < 7:
                    if objective_type == "COLOR" and grid[r][i] == objective_color_idx: objective_progress += 1
                    score += 10
                grid[r][i] = -1
            else: # V
                if 0 <= grid[i][c] < 7:
                    if objective_type == "COLOR" and grid[i][c] == objective_color_idx: objective_progress += 1
                    score += 10
                grid[i][c] = -1
    elif typ == 9:
        target = random.randint(0,6)
        for rr in range(GRID_SIZE):
            for cc in range(GRID_SIZE):
                if grid[rr][cc] == target: 
                    if objective_type == "COLOR" and target == objective_color_idx: objective_progress += 1
                    grid[rr][cc] = -1; score += 20
    if objective_type == "SPECIAL": objective_progress += 1
    grid[r][c] = -1
    refill_grid()
    process_board()

# ────────────────────────────────────────────────
# 5. UI & RENDERING
# ────────────────────────────────────────────────
def draw_btn(rect, text, color, t_col=WHITE):
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=12)
    txt = tiny_font.render(text, True, t_col)
    screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

def draw_grid():
    pygame.draw.rect(screen, GRID_COLOR, (GRID_OFFSET_X-8, GRID_OFFSET_Y-8, 496, 496), border_radius=15)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            val = grid[r][c]
            if val == -1: continue
            x, y = GRID_OFFSET_X + c*60 + 4, GRID_OFFSET_Y + r*60 + 4
            col = COLORS[val % 7] if val < 7 else WHITE
            if current_theme == 0:
                pygame.draw.rect(screen, col, (x, y, 52, 52), border_radius=12)
                pygame.draw.rect(screen, (255,255,255,80), (x+6, y+6, 40, 15), border_radius=6)
            elif current_theme == 1: pygame.draw.rect(screen, col, (x, y, 52, 52))
            elif current_theme == 2: pygame.draw.circle(screen, col, (x+26, y+26), 24)
            elif current_theme == 3:
                pygame.draw.rect(screen, col, (x, y, 52, 52), 3, border_radius=10)
                pygame.draw.rect(screen, col, (x+22, y+22, 8, 8), border_radius=2)
            if val == 7: pygame.draw.line(screen, WHITE, (x+10, y+26), (x+42, y+26), 6)
            if val == 8: pygame.draw.line(screen, WHITE, (x+26, y+10), (x+26, y+42), 6)
            if val == 9: pygame.draw.circle(screen, GOLD, (x+26, y+26), 18, 4)
            if selected == (r, c): pygame.draw.rect(screen, WHITE, (x-2, y-2, 56, 56), 3, border_radius=12)

# ────────────────────────────────────────────────
# 6. MAIN LOOP
# ────────────────────────────────────────────────
setup_mission()
while True:
    screen.fill(BG_COLOR)
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: save_game_data(); pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: paused = not paused; continue

        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(10, 10, 100, 35).collidepoint(mx, my): paused = not paused; continue
            if pygame.Rect(WIDTH-140, 10, 130, 35).collidepoint(mx, my): 
                current_theme = (current_theme+1)%4; save_game_data(); continue
            
            if paused:
                if WIDTH//2-100 <= mx <= WIDTH//2+100:
                    if 220 <= my <= 270: paused = False
                    if 290 <= my <= 340: show_roadmap = not show_roadmap
                    if 360 <= my <= 410: setup_mission() 
                    if 430 <= my <= 480: level=1; setup_mission()
                    if 500 <= my <= 550: save_game_data(); pygame.quit(); sys.exit()
                continue

            if game_over:
                if 400 <= my <= 450: setup_mission()
                if 470 <= my <= 520 and ads.show_rewarded_video():
                    moves_left += ads.reward_amount; game_over = False; play_tone(1000, 0.2)
                continue

            gx, gy = (mx - GRID_OFFSET_X)//60, (my - GRID_OFFSET_Y)//60
            if 0 <= gx < 8 and 0 <= gy < 8:
                if grid[gy][gx] >= 7: activate_special(gy, gx); moves_left -= 1
                elif selected is None: selected = (gy, gx)
                else:
                    r1, c1 = selected
                    if abs(r1-gy) + abs(c1-gx) == 1:
                        grid[r1][c1], grid[gy][gx] = grid[gy][gx], grid[r1][c1]
                        m = find_matches()
                        if m:
                            moves_left -= 1
                            if len(m) == 4: grid[gy][gx] = 7 if r1==gy else 8
                            if len(m) >= 5: grid[gy][gx] = 9
                            process_board()
                        else: grid[r1][c1], grid[gy][gx] = grid[gy][gx], grid[r1][c1]
                    selected = None

    draw_grid()
    draw_btn(pygame.Rect(10,10,100,35), "PAUSE", GREEN, BG_COLOR)
    draw_btn(pygame.Rect(WIDTH-140, 10, 130, 35), THEME_NAMES[current_theme], GOLD, BG_COLOR)
    
    # MISSION HUD FIX: Showing the Color Target
    mission_text = f"GOAL: {objective_progress} / {objective_target}"
    if objective_type == "COLOR":
        # Draw a preview of the color to collect
        pygame.draw.rect(screen, COLORS[objective_color_idx], (WIDTH//2 + 80, 95, 25, 25), border_radius=5)
        pygame.draw.rect(screen, WHITE, (WIDTH//2 + 80, 95, 25, 25), 1, border_radius=5)

    screen.blit(font.render(f"MOVES: {moves_left}", True, WHITE if moves_left > 5 else RED), (WIDTH//2-100, 150))
    screen.blit(small_font.render(mission_text, True, GOLD), (WIDTH//2-90, 100))
    screen.blit(small_font.render(f"LVL {level}", True, BLUE), (WIDTH//2-30, 70))

    if paused:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,230)); screen.blit(overlay, (0,0))
        if not show_roadmap:
            draw_btn(pygame.Rect(WIDTH//2-100, 220, 200, 50), "RESUME", GREEN, BG_COLOR)
            draw_btn(pygame.Rect(WIDTH//2-100, 290, 200, 50), "ROADMAP", BLUE)
            draw_btn(pygame.Rect(WIDTH//2-100, 360, 200, 50), "RESTART", GOLD, BG_COLOR)
            draw_btn(pygame.Rect(WIDTH//2-100, 430, 200, 50), "RESET GAME", RED)
            draw_btn(pygame.Rect(WIDTH//2-100, 500, 200, 50), "QUIT GAME", (80,80,80))
        else:
            for i in range(1, 8):
                c = GREEN if i < level else GOLD if i == level else WHITE
                screen.blit(small_font.render(f"Level {i}: Target {1000*i}", True, c), (WIDTH//2-100, 180+i*40))

    if moves_left <= 0 and objective_progress < objective_target: game_over = True
    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,240)); screen.blit(overlay, (0,0))
        draw_btn(pygame.Rect(WIDTH//2-120, 400, 240, 50), "RETRY LEVEL", GOLD, BG_COLOR)
        draw_btn(pygame.Rect(WIDTH//2-120, 470, 240, 50), "+5 MOVES (AD)", GREEN, BG_COLOR)

    if objective_progress >= objective_target: 
        play_tone(1200, 0.4); level += 1; ads.show_interstitial(level); setup_mission()

    pygame.display.flip()
    clock.tick(FPS)