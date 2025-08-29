from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
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