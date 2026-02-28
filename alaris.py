# --- IMPORTS ---
import csv  # Reads level data from csv files
import os  # Manages file paths & system-level commands
import pygame  # Primary engine for graphics, sound, and input
import random  # Generates random behavior/numbers
import sys  # Provides tools to interact with computer's operating system
from pygame.locals import * # Loads key constants (e.g. K_w, QUIT)

# Locate game assets whether running as script or standalone app
def resource_path(relative_path):
    try:
        # Check if game is running inside a PyInstaller package
        base_path = sys._MEIPASS  # Use temporary folder created by app
    except Exception:
        # Otherwise, use normal project folder on computer
        base_path = os.path.abspath(".")  # Use current directory
    return os.path.join(base_path, relative_path)  # Link folder path to file name

# --- INITIALIZATION ---
pygame.init()  # Start pygame core systems
pygame.mixer.init()  # Start audio engine

# --- GAME WINDOW SETUP ---
WIDTH, HEIGHT = 1280, 720  # Set standard 720p dimensions

# Create window with scaling & vsync
screen = pygame.display.set_mode((WIDTH, HEIGHT),
    # Display flags: scaling, window resizing, flicker-free rendering
    pygame.SCALED | pygame.RESIZABLE | pygame.DOUBLEBUF,
    vsync=1) # Syncs fps to refresh rate of monitor

pygame.display.set_caption("Alaris the Unruly")  # Set window title

# Internal canvas to render game at fixed resolution regardless of window size
virtual_surface = pygame.Surface((WIDTH, HEIGHT))
# Controls game speed and timing (fps)
clock = pygame.time.Clock()

# --- CONSTANTS & COLORS ---
SCALE = 2.0 # Upscale small pixel art to fit high-resolution screens
tile_size = int(16 * SCALE) # Size of ground blocks
NEW_SIZE = 48 # Unit for character sizing
PLAYER_SPEED = int(2.5 * SCALE) # Calculate movement speed
MUSIC_ENDED = pygame.USEREVENT + 1 # Custom ID to distinguish music events from other game signals
pygame.mixer.music.set_endevent(MUSIC_ENDED) # Trigger event when music stops

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TEA_GREEN = (208, 240, 192)

# --- ASSETS ---
# Load & scale UI, backgrounds, & sprite sheets
logo_img = pygame.image.load(resource_path("assets/logo/mantra_logo.jpg"))
logo_w, logo_h = logo_img.get_size()
logo_scale = 160 / logo_w  # Calculate ratio to force logo to 160px wide
logo_img = pygame.transform.scale(logo_img, (int(logo_w * logo_scale), int(logo_h * logo_scale)))

menu_bg = pygame.image.load(resource_path("assets/backgrounds/menu_bg.png")).convert()
level1_bg = pygame.image.load(resource_path("assets/backgrounds/level1_bg.png")).convert()
level2_bg = pygame.image.load(resource_path("assets/backgrounds/level2_bg.png")).convert()

alaris_sheet = pygame.image.load(resource_path("assets/sprites/knight_sheet.png")).convert_alpha() # Player sheet
FRAME_ORIGINAL_W, FRAME_ORIGINAL_H = 64, 64 # Size of one frame on player sprite sheet
sprite_scaled_w = sprite_scaled_h = int(NEW_SIZE * SCALE) # Player display size after upscaling

# Enemy Sheet Loading
snake_walk_sheet = pygame.image.load(resource_path("assets/sprites/snake_walk.png")).convert_alpha()
snake_death_sheet = pygame.image.load(resource_path("assets/sprites/snake_death.png")).convert_alpha()
vulture_sheet = pygame.image.load(resource_path("assets/sprites/vulture_fly.png")).convert_alpha()
minotaur1_sheet = pygame.image.load(resource_path("assets/sprites/minotaur1_sheet.png")).convert_alpha()
minotaur2_sheet = pygame.image.load(resource_path("assets/sprites/minotaur2_sheet.png")).convert_alpha()
wizard_sheet = pygame.image.load(resource_path("assets/sprites/wizard_sheet.png")).convert_alpha()
GUARD_SRC = 128 # Size of one frame on enemy sprite sheet
MINO_DISP = (int(64 * SCALE), int(64 * SCALE)) # Minotaur display size
WIZ_DISP = (int(68 * SCALE), int(68 * SCALE)) # Wizard display size

# --- HELPER FUNCTIONS: SPRITES & ANIMATIONS ---
def get_player(x_index, y_index):
    # Cut specific frame from player sheet & scales it
    rect = pygame.Rect(
        x_index * FRAME_ORIGINAL_W, y_index * FRAME_ORIGINAL_H, FRAME_ORIGINAL_W, FRAME_ORIGINAL_H)
    return pygame.transform.scale(alaris_sheet.subsurface(rect), (sprite_scaled_w, sprite_scaled_h))

def get_snake_walk(x_index):
    # Cut walk frames for snake
    rect = pygame.Rect(x_index * 48, 0, 48, 48)
    return pygame.transform.scale(snake_walk_sheet.subsurface(rect), (sprite_scaled_w, sprite_scaled_h))

def get_snake_death(x_index):
    # Cut death frames for snake
    rect = pygame.Rect(x_index * 48, 0, 48, 48)
    return pygame.transform.scale(snake_death_sheet.subsurface(rect), (sprite_scaled_w, sprite_scaled_h))

def get_vulture(x_index):
    # Cut fly frames for vulture
    rect = pygame.Rect(x_index * 48, 0, 48, 48)
    return pygame.transform.scale(vulture_sheet.subsurface(rect), (sprite_scaled_w, sprite_scaled_h))

def get_guard(sheet, x_index, y_index, source_size, target_size):
    # Cut frames for guards based on sheet-specific grid sizes
    rect = pygame.Rect(x_index * source_size, y_index * source_size, source_size, source_size)
    # Use try/except to handle multiple sprite sheets (mino & wiz) with varying frame counts
    try:
        return pygame.transform.scale(sheet.subsurface(rect), target_size)
    except ValueError:
        return pygame.Surface(target_size, pygame.SRCALPHA) # Return invisible frame if sprite's missing

# Build animation dictionaries (map state names to lists of images)
player_frames = {name: [get_player(x, y) for x in range(count)] for name, (y, count) in {
    "idle": (0,2), "run": (1,8), "jump": (2,3), "fall": (3,2), "attack": (4,6), "die": (6,7), "block": (7,2)
}.items()}
snake_walk_frames = [get_snake_walk(x) for x in range(4)]
snake_death_frames = [get_snake_death(x) for x in range(4)]
vulture_frames = [get_vulture(x) for x in range(4)]
mino_anims = {"walk": (1, 11), "attack": (2, 5), "die": (4, 5)}
mino1_frames = {name: [get_guard(minotaur1_sheet, x, y, GUARD_SRC, MINO_DISP) for x in range(count)]
                for name, (y, count) in mino_anims.items()}
mino2_frames = {name: [get_guard(minotaur2_sheet, x, y, GUARD_SRC, MINO_DISP) for x in range(count)]
                for name, (y, count) in mino_anims.items()}
wizard_frames = {name: [get_guard(wizard_sheet, x, y, GUARD_SRC, WIZ_DISP) for x in range(count)]
                for name, (y, count) in {"walk": (1,6), "attack": (6,14), "die": (9,6)}.items()}

# --- PLAYER STATE ---
# Player dict containing all physics & status data
player = {"x":120, "y":447, "width":sprite_scaled_w, "height":sprite_scaled_h, "vel_y":0,
          "state":"idle", "frame":0, "anim_speed":0.15, "attacking":False,
          "dead":False, "blocking":False, "hidden": False, "fade_alpha": 255,
          "victory_played": False, "victory_timer": 0}
facing_right = True # Track player flip state
on_ground = False # Physics flag for jumping

# --- CAMERA VARIABLES ---
camera_x = camera_y = 0 # Offsets for scrolling the screen

# --- STORY & CREDITS DATA ---
# Lists containing text for intro & outro sequences
story_pages = [
    [
        "On the booming planet of Theradon in the year 4490,",
        "an evil clan of interstellar raiders attacked a sleeping kingdom",
        "and seized an unruly emperor – his name was Alaris.",
        "While aboard the alien ship, Alaris gazed through a window",
        "at a strange ivory planet below, and remembered",
        "reading about it as a young boy..."
    ],
    [
        "It was Ioda – a mysterious world whose low gravity and",
        "gas-dense atmosphere could absorb the velocity of an asteroid",
        "like a diamond striking wool. Seeing as the ship was passing",
        "over one of the planet's great oceans, he managed to escape",
        "through an emergency airlock and plummetted 300,000 feet",
        "to the emerald waters below..."
    ],
    [
        "Though the atmosphere eased his fall, he was knocked unconscious",
        "and awoke hours later on the golden shores of Ioda. Here is where",
        "the lord's journey truly began – an emperor without his legion,",
        "roaming an unknown planet in search for a way back home.",
        "With the raiders discovering his escape and the dangers of Ioda",
        "lurking in the shadows, the fate of Alaris is in your hands..."
    ]
]

credits_pages = [
    ["TO BE CONTINUED..."],
    [
        "Alaris The Unruly - Prototype"
        "",
        "Created by Tommy Mantra"
    ],
    ["M U S I C"],
    [
        "'For the King', 'Castle Build', 'Destiny', 'Gambit' by Alexandr Zhelanov",
        "Licensed under CC BY 4.0",
        "https://creativecommons.org/licenses/by/4.0/"
    ],
    [
        "'Lovely Meadow Victory Fanfare' by Matthew Pablo",
        "Licensed under CC BY 3.0",
        "https://creativecommons.org/licenses/by/3.0/"
    ],
    ["A S S E T S"],
    [
        "'Animated Knight Character Pack v2.0' by rgsdev",
        "Licensed under CC BY 4.0",
        "https://creativecommons.org/licenses/by/4.0/",
        "https://opengameart.org/content/animated-knight-character-pack-v20"
    ],
    [
        "'Mountains' by kitart360",
        "Licensed under CC BY 3.0",
        "https://creativecommons.org/licenses/by/3.0/"
    ],
    [
        "'Water Falls' by Derio",
        "Licensed under CC BY 3.0",
        "https://creativecommons.org/licenses/by/3.0/",
    ],
    [
        "'door' by MaxFyraZ",
        "Licensed under CC BY 4.0",
        "https://creativecommons.org/licenses/by/4.0/"
    ],
    [
        "Special thank you to Professor David Malan",
        "and the CS50 staff at Harvard University."
    ],
    [
        "And thank you to those who journeyed",
        "briefly through the world of Ioda.",
        "This is but a glimpse into a cosmic ocean.",
        "Many more depths to explore."
    ]
]

# --- UI & TIMING STATE ---
story_page_index = 0 # Current story paragraph
credits_page_index = 0 # Current credits section
alpha = 0 # Transparency for text fading
black_fade_alpha = 0 # Transparency for screen transitions
fade_in = True # Toggle for alpha direction
fade_speed = 3 # Increment/Decrement per frame
STORY_PAGE_DURATION = 15000 # Time (ms) per page
story_fully_visible = False # Completion flag for fade-in
story_timer_start = 0 # Timestamp for page viewing

# --- WORLD DATA LOADING ---
def load_csv(path):
    # Read csv file into 2D list of integers
    with open(path, newline="") as csvfile:
        return [[int(tile) for tile in row] for row in csv.reader(csvfile)]

# Initialize level layouts by loading csv grid data
level1_ground = load_csv(resource_path("assets/tiles/level1/sand.csv"))
level1_door = load_csv(resource_path("assets/tiles/level1/door.csv"))

level2_ground = load_csv(resource_path("assets/tiles/level2/ground.csv"))
level2_door = load_csv(resource_path("assets/tiles/level2/door.csv"))
spike_data = load_csv(resource_path("assets/tiles/level2/spike.csv"))

# --- Snake Class ---
class Snake:
    def __init__(self, x_start, x_end, y, speed=1.5):
        # Initialize position, patrol range, speed, & animation state
        self.x, self.y = x_start, y
        self.x_start, self.x_end = x_start, x_end
        self.speed = speed
        self.direction = 1
        self.frame = 0
        self.alive = True
        self.dying = False  # Play death animation before vanishing

    def update(self):
        if self.dying:
            # Advance death frames & remove from game when finished
            self.frame += 0.2
            if self.frame >= len(snake_death_frames):
                self.dying = False
                self.alive = False # Completely gone
            return

        if not self.alive: return

        # Move horizontally & reverse direction at patrol boundaries
        self.x += self.speed * self.direction
        if self.x >= self.x_end or self.x <= self.x_start:
            self.direction *= -1
        # Loop walk animation frames
        self.frame = (self.frame + 0.1) % len(snake_walk_frames)

    def get_rect(self):
        # Create collision box adjusted to visual position of snake's body
        if self.direction == 1:
            x_off = 2  # Horizontal offset for right-facing
        else:
            x_off = 30  # Horizontal offset for left-facing
        return pygame.Rect(
            self.x + x_off,           # Horizontal position
            self.y + (45 * SCALE),    # Match vertical position to sprite feet
            sprite_scaled_w -30,      # Width of hitbox
            15 * SCALE                # Height of hitbox
        )

    def draw(self, surface, cx):
        if not self.alive and not self.dying: return

        # Choose between walk or death frames based on state
        frames = snake_death_frames if self.dying else snake_walk_frames

        # Ensure frame index stays within valid list range
        idx = int(min(self.frame, len(frames) - 1))
        img = frames[idx]

        # Flip sprite horizontally if moving right
        if self.direction == 1:
            img = pygame.transform.flip(img, True, False)
        # Render sprite relative to camera (cx)
        surface.blit(img, (self.x - cx, self.y + (12 * SCALE)))

# --- Vulture Class ---
class Vulture:
    def __init__(self, speed=4):
        # Setup flight speed & initial animation frame
        self.speed = speed
        self.frame = 0
        self.anim_speed = 0.12
        self.spawn_vulture(0)

    def spawn_vulture(self, current_camera_x):
        # Reset vulture position off-screen from the right at random height
        self.x = current_camera_x + 1300
        self.y = random.choice([200, 250, 300, 350, 400, 450, 500])
        self.active = True

    def update(self, current_camera_x):
        # Move vulture left at a constant speed
        self.x -= int(self.speed)

        # Advance flight animation
        self.frame = (self.frame + self.anim_speed) % len(vulture_frames)

        # Stop spawning if camera has reached map edge
        camera_at_end = (current_camera_x >= MAP_WIDTH - WIDTH)

        # Respawn vulture ahead if it flies too far behind player
        if self.x < current_camera_x - 600:
            if not camera_at_end:
                self.spawn_vulture(current_camera_x)
            else:
                self.x = -2000 # Place vulture far away if level's ending

    def get_rect(self):
        # Create vulture collision box
        return pygame.Rect(self.x + 10, self.y + 40, 90, 50)

    def draw(self, surface, camera_x):
        # Draw current animation frame relative to camera
        img = vulture_frames[int(self.frame)]
        surface.blit(img, (self.x - camera_x, self.y))

# --- Guard Class ---
class Guard:
    def __init__(self, x_start, x_end, y, frames, health=30, speed=1.5, w_scale=0.5, h_scale=0.6, x_offset=0):
        # Initialize shared mino/wizard traits: HP, speed, & hitbox scales
        self.x, self.y = x_start, y
        self.x_start, self.x_end = x_start, x_end
        self.frames = frames  # Reference specific minotaur or wizard images
        self.speed = speed
        self.direction = 1
        self.state = "walk"
        self.frame = 0
        self.anim_speed = 0.15
        self.health = health # Current health (decreases when hit)
        self.max_health = health # Store original HP for level resets
        self.alive = True
        self.dying = False
        self.attack_cooldown = 0
        self.can_be_hit = True
        self.w_scale = w_scale
        self.h_scale = h_scale
        self.x_offset = x_offset

    def take_damage(self, hp):
        if not self.dying:
            self.health -= hp # Subtract hp from current health
            is_wiz = (self.frames == wizard_frames)

            # Check for death & play corresponding sound effect
            if self.health <= 0:
                self.dying = True
                self.state = "die"
                self.frame = 0
                if is_wiz:
                    wizard_death.play()
                else:
                    minotaur_death.play()
            else:
                # Play hurt sound effect
                if is_wiz:
                    wizard_hurt.play()
                else:
                    minotaur_hurt.play()

    def update(self, player_x, player_y):
        if not self.alive: return

        # Handle death animation logic
        if self.dying:
            self.frame += self.anim_speed
            if self.frame >= len(self.frames["die"]):
                self.alive = False
            return

        # Calculate horizontal & vertical distance to player
        dist_x = abs((player_x + 48) - (self.x + (68 if self.frames == wizard_frames else 64)))
        dist_y = abs(self.y - player_y)

        # Trigger attack state if player is within range & cooldown is ready
        if dist_x < 60 and dist_y < 40 and self.attack_cooldown == 0:
            if self.state != "attack":
                self.state = "attack"
                self.frame = 0
                if self.frames == wizard_frames:
                    wizard_attack.play()

        # Handle attack animation timing
        if self.state == "attack":
            if self.frames == wizard_frames:
                self.frame += 0.25 # Wizard attack speed
            else:
                self.frame += 0.15 # Minotaur attack speed

            # Reset to walk state after attack finishes
            if self.frame >= len(self.frames["attack"]):
                self.state = "walk"
                self.frame = 0
                # Wizard cooldown quicker than minotaur
                self.attack_cooldown = 45 if self.frames == wizard_frames else 60

        # Handle AI movement / patrol
        elif self.state == "walk":
            on_same_level = abs(player_y - self.y) < 40
            player_in_zone = self.x_start <= player_x <= self.x_end

            # Face player if nearby, else follow patrol route
            if on_same_level and player_in_zone:
                self.direction = -1 if player_x < self.x else 1
            else:
                if self.x >= self.x_end: self.direction = -1
                if self.x <= self.x_start: self.direction = 1

            # Move towards destination if not close to player
            if dist_x > 40 or not on_same_level:
                self.x += self.speed * self.direction
            # Handle animation looping
            self.frame = (self.frame + self.anim_speed) % len(self.frames["walk"])

        # Reduce cooldown timer every frame
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def get_rect(self):
        # Calculate dynamic hitbox based on guard type & state
        if self.dying or not self.alive:
            return pygame.Rect(-5000, -5000, 0, 0)

        full_w = self.frames[self.state][0].get_width()
        full_h = self.frames[self.state][0].get_height()

        # Wizard hitbox: centered & thin
        if self.frames == wizard_frames:
            rect_w = full_w * 0.15
            rect_h = full_h * 0.6
            total_offset_x = (full_w - rect_w) // 2 - (1 * self.direction)
            offset_y = (full_h - rect_h) // 1.2
        # Minotaur hitbox: scaled based on initialization values
        else:
            rect_w = full_w * self.w_scale
            rect_h = full_h * self.h_scale
            base_x = (full_w - rect_w) // 2
            total_offset_x = base_x + (self.x_offset * self.direction)
            offset_y = (full_h - rect_h) // 1.2

        return pygame.Rect(self.x + total_offset_x, self.y + offset_y, rect_w, rect_h)

    def draw(self, surface, cx):
        if not self.alive: return
        img = self.frames[self.state][int(self.frame)]
        # Flip image to match movement direction
        if self.direction == -1:
            img = pygame.transform.flip(img, True, False)
        # Adjust vertical position to place sprite on ground
        render_y = self.y - (img.get_height() - (60 * SCALE))
        surface.blit(img, (self.x - cx, render_y))

# --- WORLD CLASS ---
class World:
    def __init__(self, ground_data, door_data, tileset_path, spike_data=None, spike_path=None):
        # Store tile maps & load images for ground, doors, & spikes
        self.ground_data = ground_data
        self.door_data = door_data
        self.spike_data = spike_data

        # Load & scale tilesets
        self.tileset_image = pygame.image.load(tileset_path).convert_alpha()
        self.tileset_image = pygame.transform.scale(self.tileset_image,
            (int(self.tileset_image.get_width()*SCALE), int(self.tileset_image.get_height()*SCALE)))

        self.door_image = pygame.image.load(resource_path("assets/tiles/level1/door.png")).convert_alpha()
        self.door_image = pygame.transform.scale(self.door_image,
            (int(self.door_image.get_width()*SCALE), int(self.door_image.get_height()*SCALE)))

        self.spike_mapping = {} # Initialize empty dict to store spike positions for current level
        if spike_path:
            self.spike_image = pygame.image.load(spike_path).convert_alpha()
            self.spike_image = pygame.transform.scale(self.spike_image,
            (int(self.spike_image.get_width()*SCALE), int(self.spike_image.get_height()*SCALE)))

        self.ground_mapping = {} # Initialize empty dict to store ground positions for current level

        # Cut individual tiles from sheet based on specific ID mapping for each level
        if "sand.png" in tileset_path:
            self.ground_mapping = {
                63: self.tileset_image.subsurface(0, 7 * tile_size, tile_size, tile_size),
                72: self.tileset_image.subsurface(0, 8 * tile_size, tile_size, tile_size),
                81: self.tileset_image.subsurface(0, 9 * tile_size, tile_size, tile_size),
                90: self.tileset_image.subsurface(0, 10 * tile_size, tile_size, tile_size),
                99: self.tileset_image.subsurface(0, 11 * tile_size, tile_size, tile_size),
                108: self.tileset_image.subsurface(0, 12 * tile_size, tile_size, tile_size),
                117: self.tileset_image.subsurface(0, 13 * tile_size, tile_size, tile_size),
                126: self.tileset_image.subsurface(0, 14 * tile_size, tile_size, tile_size),
                135: self.tileset_image.subsurface(0, 15 * tile_size, tile_size, tile_size),
                144: self.tileset_image.subsurface(0, 16 * tile_size, tile_size, tile_size)
            }
        elif "ground.png" in tileset_path:
            self.ground_mapping = {
                5: self.tileset_image.subsurface(5 * tile_size, 0, tile_size, tile_size),
                43: self.tileset_image.subsurface(3 * tile_size, 4 * tile_size, tile_size, tile_size),
                59: self.tileset_image.subsurface(9 * tile_size, 5 * tile_size, tile_size, tile_size),
            }
            if spike_path:
                self.spike_mapping = {
                    1291: self.spike_image.subsurface(11 * tile_size, 20 * tile_size, tile_size, tile_size)
                }

        self.door_mapping = {
            4: self.door_image.subsurface(4 * tile_size, 0 * tile_size, tile_size, tile_size),
            9: self.door_image.subsurface(4 * tile_size, 1 * tile_size, tile_size, tile_size)
        }

    def draw(self, surface, camera_x, camera_y):
        # Iterate through map layers & draw assigned tiles at camera-offset positions
        for layer_data, mapping in [
            (self.ground_data, self.ground_mapping),
            (self.door_data,self.door_mapping),
            (self.spike_data, self.spike_mapping)
        ]:
            if layer_data is None: continue
            for row_index, row in enumerate(layer_data):
                for col_index, tile_id in enumerate(row):
                    if tile_id in mapping:
                        surface.blit(
                            mapping[tile_id],
                            (col_index*tile_size - camera_x, row_index*tile_size - camera_y)
                        )

# --- CREATE WORLD, ENEMIES, & BACKGROUNDS ---
scene = "logo"  # Set initial game state
tutorial_completed = False # Track if tutorial finished to prevent repeating instructions
world = World(level1_ground, level1_door, resource_path("assets/tiles/level1/sand.png")) # Load Level 1
# Calculate total map pixel dimensions based on number & size of tiles
MAP_WIDTH, MAP_HEIGHT = max(len(row) for row in world.ground_data) * tile_size, len(world.ground_data)*tile_size
# Optimize backgrounds for performance
level1_bg_scaled = pygame.transform.scale(level1_bg,(MAP_WIDTH,MAP_HEIGHT)).convert()
level2_bg_scaled = pygame.transform.scale(level2_bg,(MAP_WIDTH,MAP_HEIGHT)).convert()
menu_bg_scaled = pygame.transform.scale(menu_bg,(1280,720))

# Lists to track active enemy instances
guards = []
snakes = []
vultures = []

# --- MUSIC & SFX SETUP ---
# Store file paths for all music & sound effects
menu_music = resource_path("assets/music_sfx/for_the_king.ogg")
level1_music = resource_path("assets/music_sfx/castlebuild.wav")
level2_music = resource_path("assets/music_sfx/destiny.wav")
credits_music = resource_path("assets/music_sfx/gambit.wav")
alaris_sfx = resource_path("assets/music_sfx/alaris_sfx.wav")
block_sfx = resource_path("assets/music_sfx/block_sfx.mp3")
block2_sfx = resource_path("assets/music_sfx/block2_sfx.mp3")
minotaur_hurt = resource_path("assets/music_sfx/minotaur_hurt.wav")
minotaur_death = resource_path("assets/music_sfx/minotaur_death.wav")
sword_sfx = resource_path("assets/music_sfx/sword_sfx.mp3")
snake_sfx = resource_path("assets/music_sfx/snake_sfx.mp3")
victory_sfx = resource_path("assets/music_sfx/victory.wav")
wizard_attack = resource_path("assets/music_sfx/wizard_attack.wav")
wizard_hurt = resource_path("assets/music_sfx/wizard_hurt.wav")
wizard_death = resource_path("assets/music_sfx/wizard_death.wav")

# Convert audio files into sound objects for immediate playback
alaris_sfx = pygame.mixer.Sound(alaris_sfx)
block_sfx = pygame.mixer.Sound(block_sfx)
block2_sfx = pygame.mixer.Sound(block2_sfx)
minotaur_hurt = pygame.mixer.Sound(minotaur_hurt)
minotaur_death = pygame.mixer.Sound(minotaur_death)
sword_sfx = pygame.mixer.Sound(sword_sfx)
snake_sfx = pygame.mixer.Sound(snake_sfx)
victory_sfx = pygame.mixer.Sound(victory_sfx)
wizard_attack = pygame.mixer.Sound(wizard_attack)
wizard_hurt = pygame.mixer.Sound(wizard_hurt)
wizard_death = pygame.mixer.Sound(wizard_death)

# Set specific volume for each sound effect
pygame.mixer.music.set_volume(0.9)
alaris_sfx.set_volume(0.5)
block_sfx.set_volume(0.35)
block2_sfx.set_volume(0.3)
minotaur_hurt.set_volume(0.5)
minotaur_death.set_volume(0.5)
sword_sfx.set_volume(0.5)
snake_sfx.set_volume(0.2)
victory_sfx.set_volume(0.5)
wizard_attack.set_volume(0.4)
wizard_hurt.set_volume(0.3)
wizard_death.set_volume(0.6)

# Functions to handle music transitions & looping for specific levels
def start_level1_music():
    pygame.mixer.music.fadeout(2000) # Fade out current track over 2 seconds
    pygame.mixer.music.load(level1_music) # Load level 1 track
    pygame.mixer.music.set_volume(0.4) # Adjust volume
    pygame.mixer.music.play(-1) # Play on an infinite loop

def start_level2_music():
    pygame.mixer.music.fadeout(2000)
    pygame.mixer.music.load(level2_music)
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(0, start=22.0) # Play once, starting 22 seconds into file

def load_level(level_name):
    # Grant access to global lists & map variables
    global snakes, guards, vultures, world, MAP_WIDTH, MAP_HEIGHT

    if level_name == "level1":
        # Load Level 1 tilemap & populate enemy lists with starting positions
        world = World(level1_ground, level1_door, resource_path("assets/tiles/level1/sand.png"))
        guards = [
            Guard(2690, 3100, 455, mino1_frames, w_scale=0.3, h_scale=0.7, x_offset=-15)
        ]
        snakes = [
            Snake(1080, 1159, 330, 1.0),
            Snake(2110, 2185, 520, 1.5),
            Snake(2683, 3112, 455, 2.0),
            Snake(2683, 3112, 455, 2.5),
        ]
        vultures = [Vulture(speed=5)]
        start_level1_music()

    elif level_name == "level2":
        # Load Level 2 tilemap & populate with more enemy variants
        world = World(
            level2_ground, level2_door, resource_path("assets/tiles/level2/ground.png"),
            spike_data, resource_path("assets/tiles/level2/spike.png")
        )
        guards = [
            Guard(1100, 1280, 490, mino1_frames, w_scale=0.3, h_scale=0.7, x_offset=-15),
            Guard(2360, 2600, 135, wizard_frames, health=40, w_scale=0.2, h_scale=0.5, x_offset=-5),
            Guard(2660, 2970, 200, mino2_frames, health=40, w_scale=0.3, h_scale=0.7),
            Guard(3530, 3725, 552, wizard_frames, health=40, w_scale=0.2, h_scale=0.5, x_offset=-5)
        ]
        snakes = [
            Snake(710, 890, 490, 1.5),
            Snake(2710, 2955, 200, 2.0),
            Snake(3566, 3725, 552, 2.0)
        ]
        vultures = [Vulture(speed=6)]
        start_level2_music()

    # Calculate total map pixel dimensions for when map changes
    MAP_WIDTH = max(len(row) for row in world.ground_data) * tile_size
    MAP_HEIGHT = len(world.ground_data) * tile_size

# --- DRAW PLAYER ---
def draw_player(surface, camera_x, facing_right):
    # Select image corresponding to player's current animation & frame count
    current_frame = player_frames[player["state"]][int(player["frame"])]
    # Flip image if player is looking left
    if not facing_right:
        current_frame = pygame.transform.flip(current_frame, True, False)

    # Apply transparency if fade_alpha value has been lowered
    if player["fade_alpha"] < 255:
        current_frame = current_frame.copy()
        current_frame.set_alpha(player["fade_alpha"])

    # Slightly lower sprite using camera offset so feet appear firmly on ground
    visual_offset_y = 12 * SCALE
    surface.blit(current_frame, (player["x"] - camera_x, player["y"] + visual_offset_y))

# --- MAIN GAME LOOP ---
running = True; debug_mode = False; GRAVITY = 0.7
while running:
    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT: # Check if user closed window
            running = False

        if event.type == MUSIC_ENDED: # Check if non-looping song finished
            if scene == "level2" and not player["victory_played"]:
                pygame.mixer.music.play(0, start=22.0) # Play song at 22s in

        elif event.type == pygame.KEYDOWN:
            # Handle state changes when SPACE is pressed
            if event.key == pygame.K_SPACE:
                # Reset game state & return to menu from credits
                if scene == "credits":
                    pygame.mixer.music.fadeout(2000)
                    scene = "menu"
                    credits_page_index = 0
                    story_page_index = 0
                    player.update(
                        {"hidden": False, "dead": False, "victory_played": False, "fade_alpha": 255}
                    )
                    pygame.mixer.music.load(menu_music)
                    pygame.mixer.music.set_volume(0.9)
                    pygame.mixer.music.play(-1)

                # Move from menu to story intro
                elif scene == "menu":
                    scene = "story"
                    story_page_index = 0
                    alpha = 0
                    fade_in = True

                # Skip story text & begin Level 1
                elif scene == "story":
                    scene = "level1"
                    load_level("level1")
                    player.update(
                        {"x": 120, "y": 447, "vel_y": 0, "dead": False, "hidden": False, "fade_alpha": 255}
                    )

    virtual_surface.fill(BLACK) # Clear screen for new frame

    # --- LOGO SCENE ---
    if scene == "logo":
        virtual_surface.fill(BLACK)

        # Handle fade in / fade out
        alpha += fade_speed if fade_in else -fade_speed
        if alpha >= 255: alpha = 255; fade_in = False; pygame.display.flip(); pygame.time.delay(1200)

        # Apply fade in / fade out & center logo on screen
        logo_img.set_alpha(alpha)
        virtual_surface.blit(
            logo_img, (WIDTH//2 - logo_img.get_width()//2, HEIGHT//2 - logo_img.get_height()//2)
        )
        # Transition to menu once logo has faded back to 0
        if alpha <= 0 and not fade_in:
            scene = "menu"; alpha = 255; fade_in = True
            pygame.mixer.music.load(menu_music); pygame.mixer.music.play(-1)

    # --- MENU SCENE ---
    elif scene == "menu":
        # Draw background & render text centered horizontally
        virtual_surface.blit(menu_bg_scaled, (0, 0))
        title_text = pygame.font.Font(
            resource_path("assets/fonts/lohengrin.ttf"), HEIGHT//5).render("Alaris the Unruly", True, WHITE)
        virtual_surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
        prompt_text = pygame.font.Font(
            resource_path("assets/fonts/cardo.ttf"), HEIGHT//20).render("[Press SPACE to PLAY]", True, TEA_GREEN)
        virtual_surface.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, HEIGHT//1.8))

    # --- STORY SCENE ---
    elif scene=="story":
        story_font = pygame.font.Font(resource_path("assets/fonts/cardo.ttf"), HEIGHT//20)
        y = HEIGHT//3.3 # Vertical starting position for text

        # Handle automatic fading cycle for text pages
        if fade_in:
            alpha += fade_speed
            if alpha >= 255:
                alpha=255; fade_in=False; story_fully_visible=True; story_timer_start=pygame.time.get_ticks()
        elif story_fully_visible:
            # Check if duration has passed using millisecond timer
            if pygame.time.get_ticks()-story_timer_start >= STORY_PAGE_DURATION: story_fully_visible=False
        else:
            alpha -= fade_speed
            if alpha <= 0:
                alpha=0
                story_page_index += 1 # Advance to next paragraph
                if story_page_index >= len(story_pages):
                    scene="level1" # Start game if story is over
                    load_level("level1")
                else: fade_in=True

        # Render each line of current story page with transparency
        if story_page_index < len(story_pages):
            for line in story_pages[story_page_index]:
                text_surface = story_font.render(line, True, WHITE).convert_alpha()
                text_surface.set_alpha(alpha)
                virtual_surface.blit(text_surface,(WIDTH//2 - text_surface.get_width()//2, y))
                y += text_surface.get_height() + 5

        # Display UI hint for skipping story
        skip_font = pygame.font.Font(resource_path("assets/fonts/cardo.ttf"), 16)
        skip_text = skip_font.render("[Press SPACE to Skip]", True, (150, 150, 150))
        virtual_surface.blit(skip_text, (WIDTH - skip_text.get_width() - 2, HEIGHT - 20))

    # --- LEVEL1 / LEVEL2 SCENE ---
    elif scene=="level1" or scene=="level2":
        keys = pygame.key.get_pressed() # Check which keys are held down for this frame

        # --- TILE RANGE ---
        # Calculate which grid cells to check for collision based on player position to save performance
        start_col = max(0,int(player["x"]//tile_size))
        end_col = min(len(world.ground_data[0]), int((player["x"]+player["width"])//tile_size)+1)
        start_row = max(0,int(player["y"]//tile_size))
        end_row = min(len(world.ground_data), int((player["y"]+player["height"])//tile_size)+1)

        # --- VERTICAL MOVEMENT ---
        # Apply gravity & terminal velocity
        player["vel_y"]+=GRAVITY
        if player["vel_y"] > 14: player["vel_y"] = 14
        player["y"]+=player["vel_y"]

        # Define specific collision hitboxes for player's head & feet
        feet_rect = pygame.Rect(player["x"]+40, player["y"]+player["height"]-2, player["width"]-80, 10)
        head_rect = pygame.Rect(player["x"]+40, player["y"]+60, player["width"]-80,5)

        # Check for collisions with solid ground tiles
        for row in range(start_row,end_row):
            for col in range(start_col,end_col):
                tile_id = world.ground_data[row][col]
                if tile_id in world.ground_mapping:
                    tile_rect = pygame.Rect(col*tile_size,row*tile_size,tile_size,tile_size)
                    # Reset player position & velocity upon hitting floor
                    if (feet_rect.colliderect(tile_rect) and
                        player["vel_y"]>0 and tile_rect.top>player["y"]+(player["height"]/2)):
                        player["y"]=tile_rect.top - player["height"]; player["vel_y"]=0; on_ground=True; break
                    # Stop upward momentum if hitting ceiling
                    elif head_rect.colliderect(tile_rect) and player["vel_y"]<0:
                        player["y"]=tile_rect.bottom-60; player["vel_y"]=0; break

        # Handle jumping if player is on solid ground & not in hidden state
        if ((keys[K_w] or keys[K_UP] or keys[K_SPACE]) and
            on_ground and not player["hidden"]):
            player["vel_y"]=-12; on_ground=False

        # --- HORIZONTAL MOVEMENT ---
        move_x = 0
        if not player["dead"] and not player["blocking"] and not player["hidden"]:
            # Calculate direction (-1, 0, or 1) based on keyboard input
            move_x = (keys[K_d] or keys[K_RIGHT]) - (keys[K_a] or keys[K_LEFT])
            if move_x<0: player["x"]-=PLAYER_SPEED; facing_right=False
            elif move_x>0: player["x"]+=PLAYER_SPEED; facing_right=True

        # Define side-body hitbox for wall/obstacle collisions
        wall_rect = pygame.Rect(player["x"]+38, player["y"]+70, player["width"]-76, player["height"]-80)
        for row in range(start_row,end_row):
            for col in range(start_col,end_col):
                tile_id = world.ground_data[row][col]
                if tile_id in world.ground_mapping:
                    tile_rect = pygame.Rect(col*tile_size,row*tile_size,tile_size,tile_size)
                    # Prevent player from walking through walls by snapping their x position back
                    if wall_rect.colliderect(tile_rect):
                        if move_x>0: player["x"]=tile_rect.left - player["width"]+40
                        elif move_x<0: player["x"]=tile_rect.right-40

        # Handle shield & sword inputs
        if not player["hidden"]:
            player["blocking"] = keys[K_b] and on_ground
            if keys[K_c] and not player["attacking"] and not player["blocking"] and not player["dead"]:
                player["attacking"]=True; player["frame"]=0; sword_sfx.play()

        # Generate temporary sword hitbox during specific frames of attack animation
        sword_hitbox = None
        if player["attacking"] and 1 <= int(player["frame"]) <= 3:
            sword_offset = 54 if facing_right else 15
            sword_hitbox = pygame.Rect(player["x"] + sword_offset, player["y"] + 60, 27, 40)

        # --- SPIKE COLLISION ---
        current_spike_hitbox = []
        if world.spike_data:
            for row in range(start_row, end_row):
                for col in range(start_col, end_col):
                    s_id = world.spike_data[row][col]
                    if s_id in world.spike_mapping:
                        spike_rect = pygame.Rect(col*tile_size, row*tile_size, tile_size, tile_size)
                        # Shrink hitbox so only center kills player
                        hit_box = spike_rect.inflate(-4.8 * SCALE, -10 * SCALE)
                        hit_box.y += 5 * SCALE
                        current_spike_hitbox.append(hit_box)

                        # Trigger death if touching spikes while alive
                        if wall_rect.colliderect(hit_box) and not player["dead"]:
                            player["dead"] = True
                            player["state"] = "die"
                            player["frame"] = 0
                            alaris_sfx.play()

        # Check for interaction with door tiles to trigger level completion
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if col < len(world.door_data[row]):
                    tile_id = world.door_data[row][col]
                    if tile_id in world.door_mapping:
                        door_tile_rect = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
                        if wall_rect.colliderect(door_tile_rect):
                            player["hidden"] = True # Set flag to start exit sequence

        if player["hidden"]:
            player["vel_y"] = 0 # Freeze physics so player can't continue moving

            # --- AUDIO TRIGGER ---
            # Play victory sound once & fade level music
            if not player["victory_played"]:
                pygame.mixer.music.fadeout(1000)
                victory_sfx.play()
                player["victory_played"] = True
                player["victory_timer"] = pygame.time.get_ticks()

            # --- VISUAL FADE (player) ---
            if player["fade_alpha"] > 0:
                player["fade_alpha"] -= 2.0

            # --- SCREEN FADE TO BLACK ---
            current_time = pygame.time.get_ticks()
            # Delay screen blackout for cinematic effect
            if current_time - player["victory_timer"] > 5000:
                if black_fade_alpha < 255:
                    black_fade_alpha += 3

            # --- FINAL EXIT ---
            # Transition to Level 2 or Credits once screen is fully black
            if black_fade_alpha >= 255:
                if scene == "level1":
                    scene = "level2"
                    load_level("level2")
                    player.update(
                        {"x": 30, "y": 97, "vel_y": 0, "dead": False,
                         "hidden": False, "fade_alpha": 255, "victory_played": False})
                    camera_x = 0
                    black_fade_alpha = 0
                elif scene == "level2":
                    virtual_surface.fill(BLACK)
                    scene = "credits"
                    credits_page_index = 0
                    alpha = 0
                    fade_in = True
                    black_fade_alpha = 0
                    player["victory_played"] = False
                    pygame.mixer.music.load(credits_music)
                    pygame.mixer.music.set_volume(0.7)
                    pygame.mixer.music.play(0)
                    player.update(
                        {"x":30, "y":97, "vel_y":0, "dead":False, "hidden":False, "fade_alpha":255})
                    camera_x = 0
                    continue

        # --- ANIMATION STATE & FRAME ADVANCEMENT ---
        for g in guards:
            g.update(player["x"], player["y"])
        for s in snakes:
            s.update()

        # PLAYER OFFENSE (Sword vs Enemies)
        if sword_hitbox:
            for g in guards:
                # Apply damage & slight knockback to Guards when hit by sword
                if g.alive and not g.dying and g.can_be_hit:
                    if sword_hitbox.colliderect(g.get_rect()):
                        if int(player["frame"]) >= 3:
                            g.take_damage(10)
                            g.can_be_hit = False
                            g.x += 20 if player["x"] < g.x else -20
            for s in snakes:
                # Instantly kill snakes with sword contact
                if s.alive and not s.dying:
                    if sword_hitbox.colliderect(s.get_rect()):
                        s.dying = True; s.frame = 0; snake_sfx.play()

        # Reset damage flag once player attack animation ends
        if not player["attacking"]:
            for g in guards:
                g.can_be_hit = True

        # ENEMY OFFENSE (Enemies vs Player Body)
        if not player["dead"]:
            for g in guards:
                if g.alive and not g.dying:
                    g_rect = g.get_rect()
                    diff_x = (player["x"] + 48) - (g.x + 64)
                    is_facing_enemy = (facing_right and diff_x < 0) or (not facing_right and diff_x > 0)

                    # Handle walking into guard (requires blocking & facing them to survive)
                    if wall_rect.colliderect(g_rect):
                        if player["blocking"] and is_facing_enemy:
                            player["x"] += 35 if diff_x > 0 else -35
                            block2_sfx.play()
                            break
                        else:
                            player["dead"] = True; player["frame"] = 0; alaris_sfx.play()
                            break

                    # Handle being hit by a guard's active attack frames
                    if g.state == "attack":
                        is_wizard = (g.frames == wizard_frames)
                        attack_active = (2 <= int(g.frame) <= 11) if is_wizard else (3 <= int(g.frame) <= 5)
                        attack_range = 60 if is_wizard else 70

                        if attack_active:
                            is_in_front = (g.direction == 1 and diff_x > 0) or (g.direction == -1 and diff_x < 0)
                            if abs(diff_x) < attack_range and abs(player["y"] - g.y) < 50 and is_in_front:
                                # Apply knockback if blocked, otherwise trigger death
                                if player["blocking"] and is_facing_enemy:
                                    if abs(diff_x) < (attack_range - 5):
                                        player["x"] += 35 if diff_x > 0 else -35
                                        block2_sfx.play()
                                        break
                                else:
                                    player["dead"] = True; player["frame"] = 0; alaris_sfx.play()
                                    break

            for snake in snakes:
                # Handle snake body contact
                if snake.alive and not snake.dying:
                    s_rect = snake.get_rect()
                    if wall_rect.colliderect(s_rect):
                        diff_x = player["x"] - snake.x
                        is_facing_enemy = (facing_right and diff_x < 0) or (not facing_right and diff_x > 0)
                        # Pushes snake away if player blocks successfully
                        if player["blocking"] and is_facing_enemy:
                            snake.direction = -1 if snake.x < player["x"] else 1
                            snake.x += snake.speed * snake.direction * 5
                            player["x"] += 2 if player["x"] > snake.x else -2
                            block_sfx.play()
                        else:
                            player["dead"] = True; player["frame"] = 0; alaris_sfx.play()
                            break

        # Finalize player state based on priority (Death > Attack > Block > Air > Run > Idle)
        if player["dead"]: player["state"] = "die"
        elif player["attacking"]: player["state"] = "attack"
        elif player["blocking"]: player["state"] = "block"
        elif not on_ground: player["state"] = "jump" if player["vel_y"] < 0 else "fall"
        elif move_x != 0: player["state"] = "run"
        else: player["state"] = "idle"

        # Advance animation frame based on current state
        if player["state"] == "block":
            # Clamp to last frame to hold shield-up pose
            player["frame"] = min(player["frame"] + player["anim_speed"], len(player_frames["block"]) - 1)
        elif player["state"] == "attack":
            # Speed up frames specifically for sword swing
            player["frame"] += 0.25
        else:
            player["frame"] += player["anim_speed"]

        # Reset or clamp frames for non-looping animations
        if player["frame"] >= len(player_frames[player["state"]]):
            if player["state"] == "attack":
                player["attacking"], player["frame"] = False, 0 # End attack cycle
            elif player["state"] in ["die", "jump", "fall"]:
                player["frame"] = len(player_frames[player["state"]]) - 1 # Stay on final frame
            else:
                player["frame"] = 0 # Loop idle/run

        # --- DEATH / RESPAWN ---
        # Trigger death if player falls below screen limit
        if player["y"] > HEIGHT + 20 and not player["dead"]:
            player["dead"] = True
            alaris_sfx.play()

        # Handle respawn timing & position based on current level
        if player["y"] > HEIGHT + 300 or (player["dead"] and player["frame"] >= len(player_frames["die"]) - 1):
            if scene == "level2":
                spawn_x, spawn_y = 30, 97
            else:
                spawn_x, spawn_y = 120, 447

            # Reset all player status variables to default
            player.update(
                {"x": spawn_x, "y": spawn_y, "vel_y": 0, "dead": False,
                 "state": "idle", "frame": 0, "hidden": False, "fade_alpha": 255})
            camera_x = 0; facing_right = True

            # Reset all level enemies to initial living states
            for s in snakes:
                s.alive = True; s.dying = False; s.frame = 0
            for g in guards:
                g.alive = True; g.dying = False; g.health = g.max_health
                g.state = "walk"; g.frame = 0

        # Clamp player position to ensure they don't walk off map boundaries
        player["x"] = max(-35, min(player["x"], MAP_WIDTH - 60))
        player["y"] = max(-500, (player["y"]))

        # --- CAMERA SCROLLING ---
        # Calculate horizontal target to keep player centered
        target_camera_x = player["x"] - WIDTH/2 + player["width"]/2
        # Apply linear interpolation for smooth camera lag
        camera_x += (target_camera_x - camera_x) * 0.1
        # Final camera X clamped to map edges
        cx = int(max(0,min(camera_x,MAP_WIDTH - WIDTH)))

        # --- Vulture Collision ---
        # Check collisions after player moves bc vultures move independently
        for v in vultures:
            v.update(cx)
            if not player["dead"] and not player["hidden"]:
                if v.get_rect().colliderect(wall_rect):
                    player["dead"] = True
                    player["state"] = "die"
                    player["frame"] = 0
                    alaris_sfx.play()
                    break

        # --- DRAW WORLD, ENEMIES, PLAYER ---
        # Render parallax background based on scene
        if scene == "level1":
            virtual_surface.blit(level1_bg_scaled, (-(cx * 0.4), 0))
        elif scene == "level2":
            virtual_surface.blit(level2_bg_scaled, (-(cx * 0.4), 0))

        # Draw tilemap & all active entities
        world.draw(virtual_surface,cx,0)

        # --- Controls Prompt (Level 1) ---
        if scene == "level1" and not tutorial_completed:
            # Fade out text as Alaris walks to right
            prompt_alpha = max(0, min(255, 255 - (player["x"] - 140) * 0.7))
            if prompt_alpha > 0:
                guide_font = pygame.font.Font(resource_path("assets/fonts/cardo.ttf"), 15)
                controls = "[Arrows]=Move [Space]=Jump [C]=Attack [B]=Block"
                text_surf = guide_font.render(controls, True, BLACK).convert_alpha()
                text_surf.set_alpha(prompt_alpha)
                virtual_surface.blit(text_surf, (5 - cx, 572))
            else:
                tutorial_completed = True # Permanently disable tutorial after first movement

        # Render all entities relative to camera offset (cx)
        for s in snakes:
            s.draw(virtual_surface, cx)
        for g in guards:
            g.draw(virtual_surface, cx)
        for v in vultures:
            v.draw(virtual_surface, cx)
        draw_player(virtual_surface,cx,facing_right)

        # --- DEBUG COLLISION BOXES ---
        # Visualize hitboxes for development & testing
        if debug_mode:
            pygame.draw.rect(
                virtual_surface, (255, 0, 0),
                (wall_rect.x - cx, wall_rect.y, wall_rect.width, wall_rect.height), 2)
            pygame.draw.rect(
                virtual_surface, (0, 255, 0),
                (feet_rect.x - cx, feet_rect.y, feet_rect.width, feet_rect.height), 2)
            pygame.draw.rect(
                virtual_surface, (0, 0, 255),
                (head_rect.x - cx, head_rect.y, head_rect.width, head_rect.height), 2)

            if sword_hitbox:
                pygame.draw.rect(
                    virtual_surface, (255, 255, 255),
                    (sword_hitbox.x - cx, sword_hitbox.y, sword_hitbox.width, sword_hitbox.height), 2)

            for g in guards:
                if g.alive and not g.dying:
                    g_rect = g.get_rect()
                    pygame.draw.rect(
                        virtual_surface, (255, 165, 0), (g_rect.x - cx, g_rect.y, g_rect.width, g_rect.height), 2)

            for s in snakes:
                if s.alive and not s.dying:
                    s_rect = s.get_rect()
                    pygame.draw.rect(
                        virtual_surface, (255, 255, 0), (s_rect.x - cx, s_rect.y, s_rect.width, s_rect.height), 1)

            for s_rect in current_spike_hitbox:
                pygame.draw.rect(
                    virtual_surface, (255, 0, 255), (s_rect.x - cx, s_rect.y, s_rect.width, s_rect.height), 2)

    # --- CREDITS SCENE ---
    elif scene == "credits":
        credit_font = pygame.font.Font(resource_path("assets/fonts/cardo.ttf"), HEIGHT // 25)

        # --- TIMER LOGIC ---
        # Handle sequential fading of credits pages
        if fade_in:
            alpha += fade_speed
            if alpha >= 255:
                alpha = 255; fade_in = False; story_fully_visible = True
                story_timer_start = pygame.time.get_ticks()
        elif story_fully_visible:
            if pygame.time.get_ticks() - story_timer_start >= 4000: # Page visible for 4s
                story_fully_visible = False
        else:
            alpha -= fade_speed
            # Start fading music as final credits page begins to disappear
            if credits_page_index >= len(credits_pages) - 1:
                pygame.mixer.music.fadeout(5000)

            if alpha <= 0:
                alpha = 0
                credits_page_index += 1
                # If credits are finished, return to main menu
                if credits_page_index >= len(credits_pages):
                    scene = "menu"
                    credits_page_index = 0
                    story_page_index = 0
                    player.update({"hidden": False, "dead": False, "victory_played": False, "fade_alpha": 255})
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(menu_music)
                    pygame.mixer.music.set_volume(0.9)
                    pygame.mixer.music.play(-1)
                else:
                    fade_in = True

        # --- DRAWING LOGIC ---
        # Render lines of text for current credits page
        if credits_page_index < len(credits_pages):
            y = HEIGHT // 2.3
            for line in credits_pages[credits_page_index]:
                text_surf = credit_font.render(line, True, WHITE).convert_alpha()
                text_surf.set_alpha(alpha)
                virtual_surface.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, y))
                y += text_surf.get_height() + 10

        # Display UI hint for skipping credits
        skip_font = pygame.font.Font(resource_path("assets/fonts/cardo.ttf"), 16)
        skip_text = skip_font.render("[Press SPACE to Skip]", True, (150, 150, 150))
        virtual_surface.blit(skip_text, (WIDTH - skip_text.get_width() - 2, HEIGHT - 20))

    # --- GLOBAL FADE OVERLAY ---
    # Draw black surface over entire game for transitions
    if black_fade_alpha > 0:
        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill(BLACK)
        fade_surface.set_alpha(black_fade_alpha)
        virtual_surface.blit(fade_surface, (0, 0))

    # --- RENDER TO SCREEN ---
    # Transfer virtual canvas to physical window
    screen.blit(virtual_surface,(0,0))
    pygame.display.flip() # Update full display surface to screen
    clock.tick(60) # Maintain steady 60fps

# --- QUIT ---
pygame.quit() # Uninitialize all pygame modules & close window
