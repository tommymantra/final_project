# Alaris The Unruly
#### Video Demo:  <https://www.youtube.com/watch?v=MfyO_gPO230>

#### Description:
**Alaris the Unruly** is a 2D side-scrolling action-adventure platformer programmed in Python using Pygame. Players control Alaris – an emperor who escaped an enemy spacecraft and landed on a strange planet named Ioda. Here, users are challenged to traverse difficult terrain containing various enemies and hazards to complete each level.

---

## Play the Game
* **[Download Alaris the Unruly (Windows/Mac)](https://drive.google.com/drive/folders/1wLxpx_V77939LXu_y57Cm1O3lH4jXB18?usp=drive_link)**
* *Note: See the included `GAME_GUIDE` for extraction and security bypass instructions.*

---

## 1. Game Concept
The game is built on high-stakes survival and tactical movement. Players must balance aggression and safety by using a sword and shield to defeat enemies. The world of Ioda is unforgiving. Precise platforming is required to navigate large voids and environmental hazards such as spikes and flying vultures, whom must be avoided entirely. The journey spans two levels that transition in music, visual style, and tone, moving from a somewhat introductory atmosphere to a more intense, challenging environment.

### Core Features
* **Physics:** Smooth player movement and jumping physics.
* **Combat:** Mechanics include sword attacks and blocking.
* **AI:** Diverse enemy types including Minotaurs, Wizards, Snakes, and Vultures.
* **Progression:** A state-driven game loop that transitions seamlessly from the main menu and story intro through two levels of increasing difficulty and a final credits sequence.

---

## 2. Scenes / Game Flow
The game is divided into distinct scenes, each with unique logic:

| Scene | Description / Logic |
| :--- | :--- |
| **Logo** | Game startup splash screen. Handles fade-in/out of logo, then transitions to menu. |
| **Menu** | Main menu. Loads background, title, music, and prompt `[Press SPACE to PLAY]`. |
| **Story** | Story intro pages. Automatic fade-in/out of text (skippable with `SPACE`). |
| **Level 1** | First playable level. Loads background, tilemap, enemies, music, sound effects, and tutorial prompt. |
| **Level 2** | Second playable level. New music and map, harder enemies, and increased hazards. |
| **Credits** | Sequential fade-in/out credits pages. Returns to Menu upon completion. |

---

## 3. Controls & Gameplay Mechanics
| Action | Key(s) |
| :--- | :--- |
| **Move** | `Left` / `Right` or `A` / `D` |
| **Jump** | `SPACE` / `Up` / `W` |
| **Attack** | `C` |
| **Block** | `B` |
| **Skip/Start** | `SPACE` |

### Combat & Physics
* **Sword Attack:** Generates a temporary hitbox. Damages guards and kills snakes instantly.
* **Block:** Negates damage and applies knockback when held while facing enemy.
* **Collision:** Uses feet, head, and body hitboxes to detect environment boundaries.
* **Danger:** Contact with spikes, vultures, or snakes and enemies (unless blocking) results in instant death.
* **Physics:** Gravity is applied at`0.7` per frame with a terminal velocity of `14`.

---

 ## 4. Animation System
The engine uses a **grid-based extraction** method to pull frames from sprite sheets.

* **Slicing:** Frames are cut as subsurfaces (e.g., 64x64 for Alaris) and upscaled by **2.0** for pixel clarity.
* **State Mapping:** A dictionary links game states (`idle`, `run`, `jump`, `fall`, `attack`, `block`, and `die`) to specific sheet rows for instant frame switching.
* **Efficiency:** Uses `.convert_alpha()` and `subsurface` to keep memory usage low and rendering fast.

---

## 5. Enemies

### Guards
* **Behavior:** Patrols set area but will pursue and attack player if they enter specific detection range.
* **Interaction:** Bi-directional knockback system. Player can knock back guards with a successful sword strike, while blocking negates incoming damage and pushes the enemy away.

### Snakes
* **Behavior:** Slithers along a specific range.
* **Interaction:** Instantly killed by sword. Deadly upon contact.

### Vultures
* **Behavior:** Fly across the screen independently.
* **Interaction:** Contact triggers player death.

---

## 6. Known Hazards & Survival Guide

To navigate the world successfully, the player must watch out for the following enemies and environmental threats:

| Hazard | Type | Threat | Survival Tip |
| :--- | :--- | :--- | :--- |
| **Guards** | Combatant | **Lethal** | Minotaurs and Wizards pursue on sight. Await their attack, then strike (`C`) to damage and knockback, and hold (`B`) to block. They possess multiple health points, so be prepared for battle. |
| **Snakes** | Ground | **Lethal** | Vanquish them instantly with a sword strike (`C`) or jump over them. |
| **Vultures** | Aerial | **Lethal** | These fly independently across the screen. Time your movements carefully. |
| **Spikes** | Static | **Lethal** | Do not touch. Use precise jumping to clear. |
| **Pits** | Void | **Lethal** | Falling below the map is fatal and resets the player to the level start. |

---

## 7. Levels & World
* **Tilemaps:** Loaded from CSV files (Ground, Doors, Spikes).
* **Camera:** Follows the player using linear interpolation (Lerp), clamped to map edges.
* **Depth:** Parallax background where distant layers move slower than foreground.

---

## 8. Debug & Development Tools
Debug mode draws colored hitboxes to fine-tune interactions:
* **Red:** Player body / wall collisions
* **Green:** Feet (Ground detection)
* **Blue:** Head (Ceiling detection)
* **White:** Sword attack hitbox
* **Orange:** Guards
* **Yellow:** Snakes
* **Magenta:** Spikes

---

## 9. Music & Sound Effects

### Music
* **Looping:** Menu: "For the King", Level 1: Castle Build.
* **Non-looping:** Level 2: "Destiny" (intro skip applied), Credits: "Gambit".
* **Logic:** Volume control is applied individually per track for balanced immersion.

### SFX
Preloaded as `pygame.mixer.Sound()` objects with specific volume levels:
* Player attack, block, & death
* Enemy attack, damage, & death
* Victory fanfare

---

## 10. Respawn & Death Logic
When Alaris falls below the map or dies:
1. **Reset:** Physics reset, camera re-centers, and enemies return to starting positions.
2. **Spawn Points:**
    * **Level 1:** `(120, 447)`
    * **Level 2:** `(30, 97)`

---

## 11. Draw Order
The game maintains a steady **60 FPS** by rendering elements in the following priority:

1. **Background:** Level-specific environment textures.
2. **World:** Ground tiles, spikes, and interactive doors.
3. **Entities:** Enemies (Guards, Snakes, Vultures) and Alaris.
4. **UI:** Tutorial prompts and screen-space text.
5. **Debug:** Hitbox visualizations (when enabled).
6. **Post-Process:** Global fade-to-black overlays.
7. **Display:** `pygame.display.flip()` to update the window.

---

## 12. Timing & Frame Management
The game uses a fixed-step timing system to maintain consistent gameplay speed:

* **Frame Rate:** Locked to the monitor's refresh rate via `vsync=1` and `clock.tick(60)`.
* **Animations:** Uses fractional frame increments (e.g., `frame += 0.15`) to ensure smooth character movement.
* **Timers:** Handles story page durations and victory sequences using frame counting and `pygame.time.delay`.
* **Transitions:** Fade speeds are calculated per-frame to ensure consistent visual overlays.

---

## 13. Engine Logic
* **Logic-First Rendering:** Game engine calculates physics, input, and hitboxes before drawing to ensure gameplay remains responsive and lag-free.
* **Collision System:** Heavily relies on `pygame.Rect` detection for environmental boundaries and combat interactions.
* **Frame-Synced Combat:** Attack hitboxes and Block windows are tied to specific animation frames to ensure visual and mechanical accuracy.
* **State Management:** Uses a dictionary-driven state machine to transition player between `idle`, `run`, `jump`, `fall`, `attack`, `block`, and `die`.
* **Visibility Control:** The `hidden` state keeps the player active in the game logic while skipping the render phase during transitions.

---

## 14. Technical Specifications
* **Language:** Python 3.9.6
* **Library:** Pygame 2.6.1
* **World Design:** Tile-based system for efficient level mapping and collision detection.
* **Performance:** Optimized for 60 FPS
* **Display:** 1280x720 Virtual Surface (scaled to window)

---

## 15. Credits & Authorship

* **Creator:** Tommy Mantra
* **Course:** CS50 Final Project (2026)
* **Assets:** Full credits for artists and musicians can be found in the in-game "Credits" scene.

> *Alaris the Unruly © 2026 by Tommy Mantra*
