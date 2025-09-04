#!/usr/bin/env python3
"""
faith_cmd.py
Contoh game terminal bergaya horor (inspirasi: Faith) - sederhana, text/ASCII.
Jalankan: python faith_cmd.py
Kontrol:
  W A S D - bergerak
  F - toggle flashlight
  Q - keluar
Fitur:
- Peta grid (terlihat sebagian kalau senter menyala)
- Senter dengan baterai (berkurang tiap langkah)
- Event acak: suara, potongan pesan, musuh muncul
- Musuh bergerak acak; bertemu = game over (atau alternatif ending)
- Beberapa ending berdasarkan item / waktu berjalan
"""
import random
import time
import os
import sys

# ------------------ input single-key (cross-platform) ------------------
try:
    import msvcrt

    def getkey():
        while True:
            k = msvcrt.getch()
            if k in (b'\x00', b'\xe0'):  # special keys
                msvcrt.getch()
                continue
            return k.decode('utf-8', errors='ignore')
except ImportError:
    import tty, termios

    def getkey():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ------------------ game config ------------------
WIDTH, HEIGHT = 21, 11  # odd sizes recommended for aesthetics
VIEW_RADIUS = 3         # radius revealed when flashlight on
MAX_BATTERY = 40        # steps of flashlight life
EVENT_CHANCE = 0.12     # chance each player move to trigger an event
ENEMY_COUNT = 1         # number of wandering entities

# ------------------ map generation ------------------
WALL = '#'
FLOOR = '.'
PLAYER = '@'
ENEMY = 'M'
ALTAR = 'A'
NOTE = '?'

def make_map(w, h):
    # simple rooms + corridors random walk carve
    grid = [[WALL for _ in range(w)] for _ in range(h)]
    # carve using drunkard walk
    x, y = w//2, h//2
    grid[y][x] = FLOOR
    for _ in range(w*h*3):
        dir = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
        x = max(1, min(w-2, x + dir[0]))
        y = max(1, min(h-2, y + dir[1]))
        grid[y][x] = FLOOR
        # sometimes carve a small room
        if random.random() < 0.02:
            rw = random.randint(2,4); rh = random.randint(2,3)
            rx = max(1, min(w-rw-1, x - rw//2))
            ry = max(1, min(h-rh-1, y - rh//2))
            for yy in range(ry, ry+rh):
                for xx in range(rx, rx+rw):
                    grid[yy][xx] = FLOOR
    # place altar and notes
    places = [(i,j) for j in range(h) for i in range(w) if grid[j][i]==FLOOR]
    random.shuffle(places)
    if places:
        ax, ay = places.pop()
        grid[ay][ax] = ALTAR
    for _ in range(max(2, (w*h)//60)):
        if places:
            nx, ny = places.pop()
            grid[ny][nx] = NOTE
    return grid

# ------------------ rendering ------------------
def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def render(grid, px, py, enemies, flashlight_on, battery, discovered):
    clear()
    h = len(grid); w = len(grid[0])
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            visible = discovered[y][x]
            ch = ' '
            if flashlight_on:
                # reveal if inside radius
                dx = x - px; dy = y - py
                if dx*dx + dy*dy <= VIEW_RADIUS*VIEW_RADIUS:
                    visible = True
                    discovered[y][x] = True
            if visible:
                if x==px and y==py:
                    ch = PLAYER
                else:
                    # check enemy
                    found_e = False
                    for ex,ey in enemies:
                        if ex==x and ey==y:
                            ch = ENEMY
                            found_e = True
                            break
                    if not found_e:
                        cell = grid[y][x]
                        if cell==WALL: ch = WALL
                        elif cell==FLOOR: ch = FLOOR
                        elif cell==ALTAR: ch = ALTAR
                        elif cell==NOTE: ch = NOTE
                        else: ch = cell
            else:
                ch = ' '  # dark
            row.append(ch)
        out.append(''.join(row))
    print('\n'.join(out))
    print()
    print(f'Battery: {"|"*(battery//2)} ({battery})   Flashlight: {"ON" if flashlight_on else "OFF"}')
    print("Controls: W/A/S/D move  F toggle flashlight  Q quit")
    print("Explore the map. Be careful of the thing that wanders the dark...")

# ------------------ utilities ------------------
def neighbors(x,y,w,h):
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x+dx, y+dy
        if 0<=nx<w and 0<=ny<h:
            yield nx,ny

def find_floor(grid):
    h=len(grid); w=len(grid[0])
    for y in range(h):
        for x in range(w):
            if grid[y][x]==FLOOR:
                return x,y
    return w//2, h//2

# ------------------ game loop ------------------
def main():
    random.seed()
    grid = make_map(WIDTH, HEIGHT)
    h=len(grid); w=len(grid[0])
    px,py = find_floor(grid)
    # place enemies
    empties = [(x,y) for y in range(h) for x in range(w) if grid[y][x] in (FLOOR,NOTE)]
    enemies = []
    for _ in range(ENEMY_COUNT):
        ex,ey = random.choice(empties)
        # ensure not on player
        if (ex,ey)==(px,py):
            continue
        enemies.append([ex,ey])
    flashlight_on = False
    battery = MAX_BATTERY
    discovered = [[False]*w for _ in range(h)]
    discovered[py][px] = True
    ticks = 0
    notes_found = 0
    visited_altar = False

    messages = [
        "Kamu merasa ada yang mengawasi dari sela pepohonan.",
        "Sebuah bisikan: 'jangan... lihat... belakangmu...'",
        "Suara perekam tua: 'You shouldn't have come here.'",
        "Jejak langkah basah menuju utara.",
    ]

    # intro
    clear()
    print("=== THE LITTLE FAITH-LIKE TEXT ADVENTURE (prototype) ===")
    print("Kamu terjebak di halaman gereja tua. Cari kebenaran atau lari...")
    print("Tekan tombol apa saja untuk mulai...")
    getkey()

    while True:
        render(grid, px, py, enemies, flashlight_on, battery, discovered)
        if battery<=0 and flashlight_on:
            flashlight_on = False
            print("\nBaterai senter habis. Kegelapan menjepitmu.")
            time.sleep(1)
        # check immediate events
        if grid[py][px]==NOTE:
            notes_found += 1
            grid[py][px] = FLOOR
            print("\nKamu menemukan secarik catatan tua. Ada tulisan samar: ")
            print(random.choice(["'...they are under the floor.'", "'...don't trust the light.'", "'Remember the altar.'"]))
            print("(Tekan apapun)")
            getkey()
        if grid[py][px]==ALTAR and not visited_altar:
            visited_altar = True
            print("\nAda altar tua di sini. Sesuatu bergema di dalammu.")
            print("Kamu merasakan pilihan: berdoa atau melarikan diri.")
            print("(Tekan apapun untuk melanjutkan)")
            getkey()

        # enemy encounter?
        for ex,ey in enemies:
            if ex==px and ey==py:
                # if flashlight on maybe scare away sometimes
                if flashlight_on and random.random() < 0.5:
                    print("\nSentermu menyilaukan makhluk itu. Ia mundur ke kegelapan...")
                    # enemy teleports away
                    empt = [(x,y) for y in range(h) for x in range(w) if grid[y][x]==FLOOR and (x,y)!=(px,py)]
                    enemies[0] = list(random.choice(empt))
                    time.sleep(1)
                else:
                    print("\nMakhluk itu menangkapmu... Kamu kehilangan kesadaran.")
                    print("=== GAME OVER ===")
                    print(f"Notes ditemukan: {notes_found}  Langkah: {ticks}")
                    return

        # get input
        k = getkey().lower()
        if k=='q':
            print("Kamu menyerah dan meninggalkan tempat itu...")
            return
        if k=='f':
            if flashlight_on:
                flashlight_on = False
            else:
                if battery>0:
                    flashlight_on = True
                else:
                    print("Baterai kosong.")
                    time.sleep(0.7)
            continue
        dx = dy = 0
        if k in ('w','k','8'):
            dy = -1
        elif k in ('s','j','2'):
            dy = 1
        elif k in ('a','h','4'):
            dx = -1
        elif k in ('d','l','6'):
            dx = 1
        else:
            continue  # ignore other keys

        nx, ny = px+dx, py+dy
        if not (0<=nx<w and 0<=ny<h): 
            continue
        if grid[ny][nx] != WALL:
            px, py = nx, ny
            ticks += 1
            # battery use if flashlight on
            if flashlight_on:
                battery -= 1
                if battery < 0: battery = 0
        # move enemies (simple random walk, prefer floor)
        for i, (ex,ey) in enumerate(enemies):
            moves = [(ex,ey)]
            for nx2,ny2 in neighbors(ex,ey,w,h):
                if grid[ny2][nx2] != WALL:
                    moves.append((nx2,ny2))
            # sometimes move towards player if close
            if abs(ex-px)+abs(ey-py) <= 5 and random.random() < 0.6:
                # move one step towards player
                cand = sorted(moves, key=lambda c: abs(c[0]-px)+abs(c[1]-py))
                enemies[i] = list(cand[0])
            else:
                enemies[i] = list(random.choice(moves))
        # random events
        if random.random() < EVENT_CHANCE:
            ev = random.choice(['whisper','footstep','static','cold'])
            if ev=='whisper':
                print("\nKamu mendengar bisikan samar di belakang tembok...")
                print(random.choice(messages))
            elif ev=='footstep':
                print("\nLangkah jauh terdengar—berhenti—lalu menjauh...")
            elif ev=='static':
                print("\nRadio tua berbunyi: \"...pay...\"")
            else:
                print("\nAngin dingin lewat. Detak jantungmu meningkat.")
            time.sleep(1)
        # discovered reveal around player a little even if flashlight off (small ambient)
        for nx,ny in neighbors(px,py,w,h):
            discovered[ny][nx] = True

        # win condition (example): find altar with some notes
        if visited_altar and notes_found >= 2:
            print("\nKamu meletakkan catatan pada altar dan merasakan sesuatu terlepas.")
            print("Cahaya redup muncul, lalu... damai.")
            print("=== ENDING: PENGAMPUNAN ===")
            print(f"Notes ditemukan: {notes_found}  Langkah: {ticks}")
            return

        # small delay to avoid insane CPU while still responsive
        time.sleep(0.02)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeluar. Sampai jumpa.")
