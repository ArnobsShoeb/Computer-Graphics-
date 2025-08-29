from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from math import atan2 
from math import sin, cos, radians, sqrt
import random
import time



# ---------------------------
# Template Globals (kept)
# ---------------------------
camera_pos = (0, 500, 500)
fovY = 120  # Field of view
GRID_LENGTH = 600  # Length of grid lines
rand_var = 423

# ---------------------------
# Enemy spawn timer for continuous spawn
# ---------------------------
enemy_spawn_timer = 0.0       # counts time since last spawn
enemy_spawn_interval = 7.0  


# ---------------------------
# Enemy Globals
# ---------------------------
enemies = []  # list of dicts {pos:[x,y,z], speed, health, cooldown, target_pos}
enemy_spawned = False
enemy_speed = 8.0
enemy_bullets = []  # bullets fired by enemies
enemy_fire_cooldown = 1.5  # seconds

# ---------------------------
# Game Globals (added)
# ---------------------------
window_w, window_h = 1000, 800

# Player state
player_pos = [0.0, 570.0, 0.0]   # x, y, z
player_dir = -90.0               # degrees (facing direction in XY plane)
player_speed = 18.0
player_rot_speed = 12.0
player_radius = 25.0

# Vertical movement (jump)
is_jumping = False
vertical_velocity = 0.0
gravity = -1.2
jump_strength = 22.0
ground_z = 0.0
player_height = 140.0  # camera/head offset in 3rd person

# Camera & view
first_person = False
camera_follow = True
cam_fov = fovY
cam_pos = list(camera_pos)


# Game stats
lives = 5
health = 100
score = 0
current_level = 1
max_levels = 3
game_over = False
level_complete = False
cheat_mode = False
next_jump_tile = None 

# Entities
bullets = []  
collectibles = []  
walls = []  
moving_hazards = [] 
falling_tiles = {}  
goal_zone = {'center': (0, -550), 'radius_x': 150, 'radius_y': 150, 'z': 0}

# Timing for animations
last_time = time.time()
animation_counter = 0

# Misc
random.seed(423)



# ---------------------------
# World / level setup
# ---------------------------
def generate_level(level):
    """Populate walls, collectibles, hazards, tiles based on level."""
    global walls, collectibles, moving_hazards, falling_tiles, goal_zone

    walls = []
    collectibles = []
    moving_hazards = []
    falling_tiles = {}

    # Base walls - different for each level (simple but varied)
    if level == 1:
        # Simple corridors
        walls.extend([
            {'x1': -600, 'y1': 400, 'x2': -250, 'y2': 400},  # top left
            {'x1': 0, 'y1': 400, 'x2': 600, 'y2': 400},  # top right
            {'x1': -400, 'y1': 400, 'x2': -400, 'y2': 150},
            {'x1': -400, 'y1': 0, 'x2': -400, 'y2': -300},
            {'x1': -600, 'y1': 0, 'x2': 0, 'y2': 0},
            {'x1': 200, 'y1': 0, 'x2': 600, 'y2': 0},
            {'x1': 200, 'y1': 0, 'x2': 200, 'y2': -150},
            {'x1': 200, 'y1': -100, 'x2': 200, 'y2': -400},
            {'x1': -600, 'y1': -300, 'x2': -200, 'y2': -300},
            {'x1': 0, 'y1': -300, 'x2': 600, 'y2': -300},
        ])
        # collectibles
        for i in range(8):
            x = random.randint(-500, 500)
            y = random.randint(-500, 500)
            collectibles.append({'pos': [x, y, 20], 'type': 'coin', 'active': True})
    elif level == 2:
        walls.extend([
            {'x1': -600, 'y1': 400, 'x2': -200, 'y2': 400},
            {'x1': -100, 'y1': 400, 'x2': 600, 'y2': 400},
            {'x1': -100, 'y1': 400, 'x2': -100, 'y2': 300},
            {'x1': -100, 'y1': 200, 'x2': -100, 'y2': -300},
            {'x1': -600, 'y1': 200, 'x2': -50, 'y2': 200},
            {'x1': 100, 'y1': 200, 'x2': 600, 'y2': 200},
            {'x1': 200, 'y1': 200, 'x2': 200, 'y2': 0},
            {'x1': 200, 'y1': -100, 'x2': 200, 'y2': -300},
            {'x1': -400, 'y1': 0, 'x2': -100, 'y2': 0},
            {'x1': 0, 'y1': 0, 'x2': 200, 'y2': 0},
            {'x1': -400, 'y1': 0, 'x2': -400, 'y2': -200},
            {'x1': -400, 'y1': -300, 'x2': -400, 'y2': -600},
            {'x1': -400, 'y1': -300, 'x2': 0, 'y2': -300},
            {'x1': 100, 'y1': -300, 'x2': 600, 'y2': -300},
        ])
        for i in range(10):
            x = random.randint(-500, 500)
            y = random.randint(-500, 500)
            t = 'coin' if random.random() < 0.7 else 'health'
            collectibles.append({'pos': [x, y, 20], 'type': t, 'active': True})
        # moving hazards
        moving_hazards.append({'pos': [-300.0, 100.0, 25.0], 'size': 30.0, 'path': [(-300,100), (-100,100)], 'speed': 1.6, 't': 0.0})
        moving_hazards.append({'pos': [200.0, -100.0, 25.0], 'size': 30.0, 'path': [(200,-100),(200,-300)], 'speed': 1.0, 't': 0.0})
    else:
        # Level 3: more hazards and falling tiles
        walls.extend([
            {'x1': -600, 'y1': 400, 'x2': 600, 'y2': 400},
            {'x1': -600, 'y1': -400, 'x2': 600, 'y2': -400},
            {'x1': -600, 'y1': -400, 'x2': -600, 'y2': 400},
            {'x1': 600, 'y1': -400, 'x2': 600, 'y2': 400},
            # some internal walls
            {'x1': -200, 'y1': 200, 'x2': 200, 'y2': 200},
            {'x1': -200, 'y1': -200, 'x2': 200, 'y2': -200},
        ])
        for i in range(12):
            x = random.randint(-500, 500)
            y = random.randint(-500, 500)
            t = 'coin' if random.random() < 0.6 else 'health'
            collectibles.append({'pos': [x, y, 20], 'type': t, 'active': True})
        moving_hazards.append({'pos': [0.0, 0.0, 40.0], 'size': 40.0, 'path': [(-200,0),(200,0)], 'speed': 2.4, 't': 0.0})
        # falling tiles: grid of tiles that may disappear
        for i in range(-GRID_LENGTH, GRID_LENGTH, 100):
            for j in range(-GRID_LENGTH, GRID_LENGTH, 100):
                falling_tiles[(i//100, j//100)] = {'active': True, 'timer': 0}

    # goal zone slightly changes per level
    if level == 1:
        goal_zone['center'] = (0, -550)
    elif level == 2:
        goal_zone['center'] = (0, -450)
    else:
        goal_zone['center'] = (0, -350)


# initialize first level
generate_level(current_level)








# ---------------------------
# Drawing & Rendering
# ---------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draw 2D text on screen at pixel (x, y)."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1.0, 1.0, 1.0)  # White text
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)



def draw_player():
    """Draw the player as stacked cubes/cylinders and allow orientation by player_dir."""
    glPushMatrix()
    x, y, z = player_pos
    glTranslatef(x, y, z)
    glRotatef(180, 0, 0, 1)
    glRotatef(player_dir, 0, 0, 1)
    # main body
    glColor3f(0.0, 0.5, 0.5)
    glTranslatef(0, 0, 90)
    glutSolidCube(50)
    glTranslatef(0, 0, -90)
    # arms (cylinders)
    glColor3f(0.0, 0.0, 1.0)
    glPushMatrix()
    glTranslatef(0, 10, 50)
    glRotatef(180, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 10, 5, 50, 8, 2)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, -10, 50)
    gluCylinder(gluNewQuadric(), 10, 5, 50, 8, 2)
    glPopMatrix()
    # head
    glColor3f(1.0, 0.5, 0.0)
    glTranslatef(0, 0, 140)
    gluSphere(gluNewQuadric(), 15, 10, 10)
    glPopMatrix()

def spawn_random_enemy():
    """Spawn a single enemy at a random edge of the map with random speed based on level."""
    global enemies
    side = random.choice(['top','bottom','left','right'])
    x, y = 0, 0

    if side == 'top':
        x = random.randint(-GRID_LENGTH, GRID_LENGTH)
        y = GRID_LENGTH
    elif side == 'bottom':
        x = random.randint(-GRID_LENGTH, GRID_LENGTH)
        y = -GRID_LENGTH
    elif side == 'left':
        x = -GRID_LENGTH
        y = random.randint(-GRID_LENGTH, GRID_LENGTH)
    elif side == 'right':
        x = GRID_LENGTH
        y = random.randint(-GRID_LENGTH, GRID_LENGTH)

    # Enemy speed depends on level
    spd = enemy_speed + (current_level - 1) * 2 + random.random() * 2

    enemies.append({'pos': [x, y, 0], 'speed': spd, 'health': 50 + current_level*10, 'cooldown': 0})





    def draw_walls():
        """Draw static walls as raised quads."""
    glColor3f(0.5, 0.5, 0.5)
    height = 50
    for w in walls:
        x1, y1 = w['x1'], w['y1']
        x2, y2 = w['x2'], w['y2']
        # draw vertical wall as a thick quad (extruded)
        glBegin(GL_QUADS)
        # base
        glVertex3f(x1, y1, 0)
        glVertex3f(x2, y2, 0)
        glVertex3f(x2, y2, height)
        glVertex3f(x1, y1, height)
        glEnd()


def draw_collectibles():
    """Draw coins and health pickups."""
    for c in collectibles:
        if not c.get('active', True):
            continue
        x, y, z = c['pos']
        # pulse
        pulse = 0.6 + 0.4 * (0.5 + 0.5 * sin(animation_counter * 0.12 + x * 0.01))
        if c['type'] == 'coin':
            glColor3f(1.0 * pulse, 0.9 * pulse, 0.0)
            glPushMatrix()
            glTranslatef(x, y, 20 + 8 * sin(animation_counter * 0.12 + x * 0.01))
            glutSolidSphere(8, 8, 8)
            glPopMatrix()
        else:
            glColor3f(0.0, 1.0 * pulse, 0.3)
            glPushMatrix()
            glTranslatef(x, y, 20 + 8 * sin(animation_counter * 0.14 + y * 0.01))
            glutSolidSphere(10, 10, 10)
            glPopMatrix()


def draw_goal():
    """Pulsing red quad area marks the goal zone."""
    cx, cy = goal_zone['center']
    rx, ry = goal_zone['radius_x'], goal_zone['radius_y']
    # glow factor
    glow = 0.6 + 0.4 * (0.5 + 0.5 * sin(animation_counter * 0.14))
    glColor3f(glow, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(cx, cy, 1)
    glBegin(GL_QUADS)
    glVertex3f(-rx, -ry, 0)
    glVertex3f(rx, -ry, 0)
    glVertex3f(rx, ry, 0)
    glVertex3f(-rx, ry, 0)
    glEnd()
    glPopMatrix()


def draw_bullets():
    glColor3f(1.0, 0.6, 0.2)
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['pos'][0], b['pos'][1], b['pos'][2])
        glutSolidSphere(6, 8, 8)
        glPopMatrix()


def draw_moving_hazards():
    glColor3f(0.8, 0.3, 0.3)
    for h in moving_hazards:
        glPushMatrix()
        glTranslatef(h['pos'][0], h['pos'][1], h['pos'][2])
        glutSolidCube(h['size'])
        glPopMatrix()

