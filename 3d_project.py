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



def draw_grid():
    """Render grid floor with dynamic color changes; handle falling tiles."""
    light_colors = [
        (0.8, 0.8, 1.0), (0.9, 0.8, 0.9), (1.0, 0.9, 0.8),
        (0.8, 1.0, 0.8), (1.0, 1.0, 0.8)
    ]
    global animation_counter
    animation_counter += 1
    glBegin(GL_QUADS)
    for i in range(-GRID_LENGTH, GRID_LENGTH, 100):
        for j in range(-GRID_LENGTH, GRID_LENGTH, 100):
            row = (i + GRID_LENGTH) // 100
            col = (j + GRID_LENGTH) // 100
            pulse = 0.1 * sin(animation_counter * 0.05 + row + col)
            base = light_colors[(row + col) % len(light_colors)]
            color = (clamp(base[0] + pulse, 0, 1), clamp(base[1] + pulse, 0, 1), clamp(base[2] + pulse, 0, 1))

            active = True
            if current_level >= 3:
                key = (i//100, j//100)
                if key in falling_tiles and not falling_tiles[key]['active']:
                    active = False

            # --- CHEAT MODE HIGHLIGHT ---
            if cheat_mode and active:
                px, py = player_pos[0], player_pos[1]
                gx, gy = goal_zone['center']
                tile_center_x = i + 50
                tile_center_y = j + 50
                dx = gx - px
                dy = gy - py
                if dx != 0 or dy != 0:
                    t = ((tile_center_x - px) * dx + (tile_center_y - py) * dy) / (dx*dx + dy*dy)
                    if 0 <= t <= 1:
                        nearest_x = px + t * dx
                        nearest_y = py + t * dy
                        dist2_line = (tile_center_x - nearest_x)**2 + (tile_center_y - nearest_y)**2
                        if dist2_line < 500:  # threshold
                            color = (1.0, 0.0, 0.0)  # red for path

            if active:
                glColor3f(*color)
                glVertex3f(i, j, 0)
                glVertex3f(i + 100, j, 0)
                glVertex3f(i + 100, j + 100, 0)
                glVertex3f(i, j + 100, 0)
    glEnd()



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

# ---------------------------
# Input Handlers (as template)
# ---------------------------
def keyboardListener(key, x, y):
    """W/S forward/back, A/D rotate, space to jump, C cheat toggle, R restart, V toggle view (cheat vision)."""
    global player_pos, player_dir, player_speed, is_jumping, vertical_velocity, cheat_mode
    global lives, health, score, current_level, game_over, first_person

    if game_over:
        # allow restart only
        if key == b'r':
            restart_game()
        return

    if key == b'w':
        # forward relative to player_dir
        dx = player_speed * cos(radians(player_dir))
        dy = player_speed * sin(radians(player_dir))
        try_move(dx, dy)
    elif key == b's':
        dx = player_speed * cos(radians(player_dir))
        dy = player_speed * sin(radians(player_dir))
        try_move(-dx, -dy)
    elif key == b'a':
        player_dir += player_rot_speed
    elif key == b'd':
        player_dir -= player_rot_speed
    elif key == b' ':
        # Jump
        global vertical_velocity, is_jumping, next_jump_tile
        if not is_jumping:
            # compute front tile center
            angle = radians(player_dir)
            # move 1 tile ahead (100 units)
            next_x = player_pos[0] + 100 * cos(angle)
            next_y = player_pos[1] + 100 * sin(angle)
            next_jump_tile = (next_x, next_y)

            # start jump
            is_jumping = True
            vertical_velocity = jump_strength
    elif key == b'c':
        cheat_mode = not cheat_mode
    elif key == b'r':
        restart_game()
    elif key == b'v':
        # cheat vision toggle, just change FOV temporarily
        if cam_pos:
            toggle_fov()
    elif key == b'k':
        global camera_follow
        camera_follow = not camera_follow
        print("Camera follow:", camera_follow)



def specialKeyListener(key, x, y):
    """Arrow keys move camera position when camera_follow is False."""
    global cam_pos

    if camera_follow:
        return  # ignore arrow keys while camera follows player

    if key == GLUT_KEY_UP:
        cam_pos[2] += 12  # move camera up
    elif key == GLUT_KEY_DOWN:
        cam_pos[2] -= 12  # move camera down
    elif key == GLUT_KEY_LEFT:
        cam_pos[0] -= 10  # move camera left
    elif key == GLUT_KEY_RIGHT:
        cam_pos[0] += 10  # move camera right




def mouseListener(button, state, x, y):
    """Left click: fire bullet. Right click: toggle first-person view."""
    global first_person, bullets
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person
        # adjust FOV for first-person
        if first_person:
            set_fov(90)
        else:
            set_fov(fovY)
            
            
# ---------------------------
# Camera & setup (template)
# ---------------------------
def setupCamera():
    """Configures the camera's projection and view settings (uses cam_pos or follows player)."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(cam_fov, float(window_w)/float(window_h), 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Choose camera
    if first_person:
        # first-person camera placed near player's head
        px, py, pz = player_pos
        angle = radians(player_dir)
        offset = 20.0
        camx = px + offset * cos(angle)
        camy = py + offset * sin(angle)
        camz = pz + player_height
        lookx = px + 80.0 * cos(angle)
        looky = py + 80.0 * sin(angle)
        lookz = pz + player_height
        gluLookAt(camx, camy, camz, lookx, looky, lookz, 0, 0, 1)
    else:
        # third-person camera placed at cam_pos and looks at player
        cx, cy, cz = cam_pos
        # make camera smoothly follow player if camera_follow enabled
        if camera_follow:
            # interpolate towards desired third-person position (behind player)
            desired_x = player_pos[0] + -200 * cos(radians(player_dir))
            desired_y = player_pos[1] + -200 * sin(radians(player_dir))
            desired_z = player_pos[2] + player_height
            # simple smoothing
            cx = cx + (desired_x - cx) * 0.06
            cy = cy + (desired_y - cy) * 0.06
            cz = cz + (desired_z - cz) * 0.06
            cam_pos[0], cam_pos[1], cam_pos[2] = cx, cy, cz
        gluLookAt(cx, cy, cz, player_pos[0], player_pos[1], player_pos[2] + 40, 0, 0, 1)


def set_fov(val):
    global cam_fov
    cam_fov = val


def toggle_fov():
    global cam_fov
    cam_fov = 90 if cam_fov == fovY else fovY


# ---------------------------
# Gameplay: physics & updates
# ---------------------------
def try_move(dx, dy):
    """Attempt to move player by dx,dy while checking collisions and falling tiles."""
    new_x = player_pos[0] + dx
    new_y = player_pos[1] + dy
    # bounds check
    if abs(new_x) > GRID_LENGTH or abs(new_y) > GRID_LENGTH:
        apply_damage(1, reason="Out of bounds")
        reset_player_position()
        return
    # wall collision: treat walls as thick lines (approx)
    pad = player_radius
    for w in walls:
        # simple axis-aligned approximation since walls are axis-aligned lines
        x1, y1, x2, y2 = w['x1'], w['y1'], w['x2'], w['y2']
        # if player's new position is near the wall segment
        # approximate by checking if point projects into bounding rect expanded by pad
        minx, maxx = min(x1, x2) - pad, max(x1, x2) + pad
        miny, maxy = min(y1, y2) - pad, max(y1, y2) + pad
        if minx <= new_x <= maxx and miny <= new_y <= maxy:
            # collision -> take damage and don't move
            apply_damage(1, reason="Hit wall")
            return
    # falling tile check (level 3): if tile inactive -> falling
    if current_level >= 3:
        key = (int(new_x)//100, int(new_y)//100)
        if key in falling_tiles and not falling_tiles[key]['active']:
            # fall into hole
            apply_damage(2, reason='Fell in hole')
            reset_player_position()
            return
    # otherwise apply move
    player_pos[0] = new_x
    player_pos[1] = new_y


    
def reset_player_position():
    player_pos[0] = 0.0
    player_pos[1] = 570.0
    player_pos[2] = 0.0


def apply_damage(amount, reason=None):
    global health, lives, game_over
    health -= amount * 20
    if reason and cheat_mode:
        # show debug message in console if cheat mode
        print("Damage:", amount, "Reason:", reason)
    if health <= 0:
        lives -= 1
        health = 100
        if lives <= 0:
            game_over = True

def draw_enemies():
    glColor3f(1.0, 0.0, 0.0)
    for e in enemies:
        glPushMatrix()
        glTranslatef(e['pos'][0], e['pos'][1], 25)
        glScalef(1.0, 1.0, 2.5)
        glutSolidCube(50)
        glPopMatrix()


def update_enemies(dt):
    global enemies, player_pos, health
    for e in enemies[:]:  # iterate over a copy since we may remove items
        # move toward player
        px, py, pz = player_pos
        ex, ey, ez = e['pos']
        dx, dy = px - ex, py - ey
        dist = sqrt(dx*dx + dy*dy)
        if dist > 5:
            e['pos'][0] += (dx / dist) * e['speed'] * dt
            e['pos'][1] += (dy / dist) * e['speed'] * dt

        # collision with player
        if distance2([ex, ey, ez], player_pos) < (player_radius + 25)**2:
            apply_damage(1, reason="Hit by enemy")
            enemies.remove(e)  # REMOVE enemy on collision





def spawn_enemies(level):
    global enemies, enemy_spawned
    enemies = []
    enemy_spawned = True
    if level == 1:
        # spawn 2 enemies at fixed positions
        enemies.append({'pos': [-500, 400, 0], 'speed': enemy_speed, 'health': 50, 'cooldown': 0})
        enemies.append({'pos': [400, -400, 0], 'speed': enemy_speed, 'health': 50, 'cooldown': 0})
    elif level == 2:
        for i in range(3):
            x = random.randint(-500, 500)
            y = random.randint(-500, 500)
            enemies.append({'pos': [x, y, 0], 'speed': enemy_speed+2, 'health': 60, 'cooldown': 0})
    else:
        for i in range(4):
            x = random.randint(-400, 400)
            y = random.randint(-400, 400)
            enemies.append({'pos': [x, y, 0], 'speed': enemy_speed+4, 'health': 70, 'cooldown': 0})


def fire_bullet():
    """Create a bullet sphere moving forward from player."""
    angle = radians(player_dir)
    bx = player_pos[0] + 30 * cos(angle)
    by = player_pos[1] + 30 * sin(angle)
    bz = player_pos[2] + 40  # roughly shoulder height
    speed = 45.0
    vx = speed * cos(angle)
    vy = speed * sin(angle)
    vz = 0.0
    bullets.append({'pos': [bx, by, bz], 'vel': [vx, vy, vz], 'life': 60})


def update_bullets(dt):
    """Move bullets, check collision with enemies, remove bullets/enemies on hit, update score."""
    global bullets, enemies, score

    for b in bullets[:]:
        # Move bullet
        b['pos'][0] += b['vel'][0] * dt
        b['pos'][1] += b['vel'][1] * dt
        b['pos'][2] += b['vel'][2] * dt
        b['life'] -= 1

        bullet_removed = False

        # Remove bullet if out of bounds
        if abs(b['pos'][0]) > GRID_LENGTH or abs(b['pos'][1]) > GRID_LENGTH:
            bullets.remove(b)
            continue

        # Check collision with enemies
        for e in enemies[:]:
            ex, ey, ez = e['pos']
            enemy_half_size = 25  # half of cube width
            enemy_height = 125    # cube height after scaling
            bullet_radius = 6

            # AABB collision detection
            if (abs(b['pos'][0] - ex) <= enemy_half_size + bullet_radius and
                abs(b['pos'][1] - ey) <= enemy_half_size + bullet_radius and
                abs(b['pos'][2] - ez) <= enemy_height/2 + bullet_radius):

                # Enemy hit -> remove enemy and bullet, update score
                enemies.remove(e)
                if b in bullets:
                    bullets.remove(b)
                score += 15
                bullet_removed = True
                break  # stop checking other enemies for this bullet

        # Remove bullet if life expired
        if not bullet_removed and b['life'] <= 0:
            if b in bullets:
                bullets.remove(b)
 


def update_collectibles():
    """Check for collection by player."""
    global collectibles, score, health
    for c in collectibles:
        if not c.get('active', True):
            continue
        if distance2([player_pos[0], player_pos[1], player_pos[2] + 30], [c['pos'][0], c['pos'][1], c['pos'][2]]) < (player_radius + 20)**2:
            # collect
            c['active'] = False
            if c['type'] == 'coin':
                score += 5
            else:
                health = min(100, health + 40)
                score += 8


def update_moving_hazards(dt):
    """Move hazards along their path and check collision with player."""
    global moving_hazards
    for h in moving_hazards:
        # parametric movement along two-point path
        p0 = h['path'][0]
        p1 = h['path'][1]
        # increment t
        h['t'] += h['speed'] * dt
        # ping-pong between 0..1
        t = abs(((h['t'] % 2.0) - 1.0))
        nx = p0[0] + (p1[0] - p0[0]) * t
        ny = p0[1] + (p1[1] - p0[1]) * t
        h['pos'][0] = nx
        h['pos'][1] = ny
        # collision with player
        if distance2(h['pos'], player_pos) < (h['size'] + player_radius)**2:
            apply_damage(1, reason='Hit moving hazard')


def update_falling_tiles(dt):
    """For level 3 certain tiles will begin to fall when stepped on."""
    if current_level < 3:
        return
    # if player steps on a tile, start its timer; when timer > threshold -> deactivate tile
    px, py = int(player_pos[0])//100, int(player_pos[1])//100
    key = (px, py)
    if key in falling_tiles:
        if falling_tiles[key]['active']:
            falling_tiles[key]['timer'] += 1
            if falling_tiles[key]['timer'] > 120:
                # tile falls
                falling_tiles[key]['active'] = False
                falling_tiles[key]['timer'] = 0
    # slowly regenerate some tiles
    for k, v in list(falling_tiles.items()):
        if not v['active']:
            if random.random() < 0.001:
                v['active'] = True


def update_jump(dt):
    global is_jumping, vertical_velocity, player_pos, next_jump_tile
    if is_jumping:
        # vertical motion
        vertical_velocity += gravity * dt * 10.0
        player_pos[2] += vertical_velocity * dt * 20.0

        # horizontal motion toward next tile
        if next_jump_tile:
            target_x, target_y = next_jump_tile
            # smooth interpolation
            player_pos[0] += (target_x - player_pos[0]) * 0.2
            player_pos[1] += (target_y - player_pos[1]) * 0.2

        # land check
        if player_pos[2] <= ground_z:
            player_pos[2] = ground_z
            is_jumping = False
            vertical_velocity = 0.0
            next_jump_tile = None



def check_goal():
    global current_level, level_complete, game_over
    cx, cy = goal_zone['center']
    rx, ry = goal_zone['radius_x'], goal_zone['radius_y']
    if (cx - rx) <= player_pos[0] <= (cx + rx) and (cy - ry) <= player_pos[1] <= (cy + ry):
        # reached goal
        if current_level < max_levels:
            level_complete = True
            advance_level()
        else:
            # last level -> show congratulations
            game_over = True
            level_complete = False
