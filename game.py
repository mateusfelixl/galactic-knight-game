import pgzrun
import random
from pygame import Rect

# --- CONFIGURATION ---
WIDTH = 1408
HEIGHT = 768
TITLE = "Galactic Knight: Monster Hunter"

# Game Constants
GRAVITY = 1
DEBUG_MODE = False  # Set to True to visualize hitboxes

# Global State
game_state = "MENU"
sound_on = True

# --- LEVEL DESIGN ---
# Defined as Rect(x, y, width, height)
platforms = [
    Rect((0, 660), (1408, 48)),    # 1. Main Ground
    Rect((5, 390), (350, 30)),     # 2. Left Platform
    Rect((1070, 390), (350, 30)),  # 3. Right Platform
    Rect((495, 295), (415, 30)),   # 4. Center Isle
    Rect((210, 120), (280, 30)),   # 5. Top Left
    Rect((920, 115), (270, 30)),   # 6. Top Right
    Rect((945, 520), (120, 30)),   # 7. Ruins Right
    Rect((1300, 230), (150, 30))   # 8. Ruins Left (New)
]

# --- UI ELEMENTS ---
btn_start = Rect((WIDTH/2 - 150, 350), (300, 60))
btn_sound = Rect((WIDTH/2 - 150, 430), (300, 60))
btn_quit  = Rect((WIDTH/2 - 150, 510), (300, 60))
btn_back_menu = Rect((WIDTH - 120, 20), (100, 40))
btn_try_again = Rect((WIDTH/2 - 150, 450), (300, 60))

# Colors (RGB)
C_SHADOW = (20, 20, 20)
C_BTN_NORMAL = (50, 50, 200)
C_BTN_SOUND = (0, 180, 0)
C_BTN_OFF = (180, 0, 0)
C_TEXT = (255, 255, 255)


class Character:
    """
    Base class for all entities in the game (Hero and Enemies).
    Handles physics, gravity, and platform collisions.
    """
    def __init__(self, x, y):
        self.vx = 0
        self.vy = 0
        self.is_grounded = False
        self.direction = "r"
        self.state = "idle"
        self.anim_timer = 0
        self.hurt_timer = 0
        
    def apply_physics(self):
        """Applies gravity and handles collisions with map platforms."""
        self.vy += GRAVITY
        self.actor.x += self.vx
        self.actor.y += self.vy

        # Keep character inside screen boundaries
        if self.actor.left < 0:
            self.actor.left = 0
        if self.actor.right > WIDTH:
            self.actor.right = WIDTH

        # Platform collision logic (only when falling)
        self.is_grounded = False
        if self.vy > 0:
            for plat in platforms:
                if self.actor.colliderect(plat):
                    # Tolerance check to ensure feet land on top
                    if self.actor.bottom - self.vy <= plat.top + 20:
                        self.actor.bottom = plat.top
                        self.vy = 0
                        self.is_grounded = True

    def get_hitbox(self):
        """
        Returns a modified hitbox smaller than the sprite image.
        This prevents collisions with the empty transparent borders.
        """
        base_rect = Rect(
            self.actor.left, 
            self.actor.top, 
            self.actor.width, 
            self.actor.height
        )
        return base_rect.inflate(-60, -20)


class Hero(Character):
    """
    The player controlled character. 
    Handles input, combat logic, and specific animations.
    """
    def __init__(self):
        super().__init__(50, 600)
        self.actor = Actor("hero_idle1_r")
        self.actor.anchor = ("center", "bottom") 
        self.speed = 7
        self.jump_strength = -22
        self.hp = 6
        self.attack_cooldown = 0
        self.inv_timer = 0 
        
    def take_damage(self):
        """Reduces HP and applies knockback if not invincible."""
        if self.inv_timer > 0 or self.state == "attack":
            return
        
        self.hp -= 1
        self.state = "hurt"
        self.hurt_timer = 0.5
        self.inv_timer = 2.0  # Invincibility frame
        self.vy = -12
        self.vx = -10 if self.direction == "r" else 10
        
        if sound_on: 
            try:
                sounds.hit.play()
            except:
                pass

    def attack(self, enemies):
        """Checks for collision between sword hitbox and enemies."""
        if self.attack_cooldown <= 0 and self.state != "hurt":
            self.state = "attack"
            self.anim_timer = 0
            self.attack_cooldown = 0.4
            
            # Create a sword hitbox in front of the player
            hitbox_x = self.actor.x + (60 if self.direction == "r" else -60)
            sword_hitbox = Rect((0, 0), (80, 80))
            sword_hitbox.center = (hitbox_x, self.actor.y - 40)
            
            for e in enemies:
                if e.get_hitbox().colliderect(sword_hitbox) and e.state != "hurt":
                    e.take_damage(self.actor.x)

    def update(self, enemies):
        if self.inv_timer > 0:
            self.inv_timer -= 1/60
        
        # Lock movement if hurt
        if self.state == "hurt":
            self.hurt_timer -= 1/60
            if self.hurt_timer <= 0: 
                self.state = "idle"
            else:
                self.apply_physics()
                self.animate()
                return

        # Lock movement if attacking
        if self.state == "attack":
            self.attack_cooldown -= 1/60
            if self.attack_cooldown <= 0: 
                self.state = "idle"
            self.vx = 0 
            self.apply_physics()
            self.animate()
            return

        # Input Handling
        if keyboard.left:
            self.vx = -self.speed
            self.direction = "l"
            self.state = "run"
        elif keyboard.right:
            self.vx = self.speed
            self.direction = "r"
            self.state = "run"
        else:
            self.vx = 0
            self.state = "idle"

        if keyboard.up and self.is_grounded:
            self.vy = self.jump_strength
            self.is_grounded = False
            if sound_on: 
                try:
                    sounds.jump.play()
                except:
                    pass

        if not self.is_grounded:
            self.state = "jump"
        
        if keyboard.space:
            self.attack(enemies)

        self.apply_physics()
        self.animate()

    def animate(self):
        # Slower animation for idle breathing, faster for running
        speed = 0.05 if self.state == "idle" else 0.2
        self.anim_timer += speed

        try:
            if self.state == "idle":
                f = 1 if int(self.anim_timer) % 2 == 0 else 2
                self.actor.image = f"hero_idle{f}_{self.direction}"
            elif self.state == "run":
                f = (int(self.anim_timer) % 3) + 1 
                self.actor.image = f"hero_run{f}_{self.direction}"
            elif self.state == "jump":
                self.actor.image = f"hero_jump_{self.direction}"
            elif self.state == "attack":
                f = 1 if self.attack_cooldown > 0.2 else 2
                self.actor.image = f"hero_attack{f}_{self.direction}"
            elif self.state == "hurt":
                self.actor.image = f"hero_hurt_{self.direction}"
            
            self.actor.anchor = ("center", "bottom")
        except:
            pass 

    def draw(self):
        # Flicker effect when invincible
        if self.inv_timer > 0 and int(self.inv_timer * 10) % 2 == 0:
            return
        self.actor.draw()
        
        if DEBUG_MODE:
            screen.draw.rect(self.get_hitbox(), "green")


class Enemy(Character):
    """
    AI-controlled entity. Capable of patrolling, chasing, and jumping.
    """
    def __init__(self, x, y, delay=0):
        super().__init__(x, y)
        self.actor = Actor("enemy_idle1_l")
        self.actor.pos = (x, y) 
        self.actor.anchor = ("center", "bottom")
        self.speed = random.uniform(2.5, 3.8)
        self.jump_strength = -21
        self.hp = 3
        self.jump_cooldown = 0
        self.start_delay = delay 
        
    def take_damage(self, hero_x):
        self.hp -= 1
        self.state = "hurt"
        self.hurt_timer = 0.4
        self.start_delay = 0 # Wake up immediately if hit
        self.vy = -8
        self.vx = 8 if hero_x < self.actor.x else -8
        
        if sound_on:
            try:
                sounds.hit.play()
            except:
                pass

    def update(self, hero, others):
        # Hurt State
        if self.state == "hurt":
            self.hurt_timer -= 1/60
            if self.hurt_timer <= 0: 
                self.state = "idle"
                self.vx = 0
            self.apply_physics()
            self.animate()
            return

        # Start Delay (Sniper Logic)
        if self.start_delay > 0:
            self.start_delay -= 1/60
            self.vx = 0
            self.state = "idle"
            # Face the hero while waiting
            if self.actor.x < hero.actor.x:
                self.direction = "r"
            else:
                self.direction = "l"
            
            self.apply_physics()
            self.animate()
            return

        # --- AI & PURSUIT LOGIC ---
        dist_x = abs(self.actor.x - hero.actor.x)
        dist_y = abs(self.actor.y - hero.actor.y)
        hero_is_above = hero.actor.y < self.actor.y - 50

        # Run towards hero if far or if hero is above (to find a jump spot)
        if dist_x > 50 or hero_is_above:
            if self.actor.x < hero.actor.x:
                self.vx = self.speed
                self.direction = "r"
                self.state = "run"
            else:
                self.vx = -self.speed
                self.direction = "l"
                self.state = "run"
        else:
            # Attack if close horizontally AND vertically
            if dist_y < 50:
                self.vx = 0
                self.state = "attack"
            else:
                self.state = "idle"

        # Platforming: Jump if hero is above
        if hero_is_above and self.is_grounded and self.jump_cooldown <= 0:
            self.vy = self.jump_strength
            self.is_grounded = False
            self.jump_cooldown = 1.2

        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1/60
        
        # Simple separation logic to avoid stacking
        for o in others:
            if o != self and self.actor.colliderect(o.actor):
                if self.actor.x < o.actor.x:
                    self.actor.x -= 2
                else:
                    self.actor.x += 2

        self.apply_physics()
        self.animate()

    def animate(self):
        speed = 0.05 if self.state == "idle" else 0.2
        self.anim_timer += speed

        try:
            if self.state == "idle":
                f = 1 if int(self.anim_timer) % 2 == 0 else 2
                self.actor.image = f"enemy_idle{f}_{self.direction}"
            elif self.state == "run":
                f = (int(self.anim_timer) % 3) + 1 
                self.actor.image = f"enemy_run{f}_{self.direction}"
            elif self.state == "attack":
                f = 1 if int(self.anim_timer) % 2 == 0 else 2
                self.actor.image = f"enemy_attack{f}_{self.direction}"
            elif self.state == "hurt":
                self.actor.image = f"enemy_hurt_{self.direction}"
            
            self.actor.anchor = ("center", "bottom")
        except:
            self.actor.image = f"enemy_idle1_{self.direction}"

    def draw(self):
        self.actor.draw()
        if DEBUG_MODE:
            screen.draw.rect(self.get_hitbox(), "red")


# --- GAME INITIALIZATION ---
hero = Hero()
enemies = []

def reset_game():
    """Resets the game state, hero position, and enemy spawns."""
    global hero, enemies, game_state
    hero = Hero()
    hero.actor.pos = (50, 660)
    
    enemies = []
    
    # Standard Ground Enemies
    enemies.append(Enemy(600, 600))   
    enemies.append(Enemy(1200, 600))  
    enemies.append(Enemy(700, 250))   
    
    # Sniper Enemies (Top Platforms with 5s Delay)
    enemies.append(Enemy(300, 80, delay=5.0)) 
    enemies.append(Enemy(1000, 80, delay=5.0))
    
    game_state = "GAME"
    if sound_on:
        try:
            if not music.is_playing('music'):
                music.play('music')
        except:
            pass

def on_mouse_down(pos):
    """Handles mouse clicks for menu navigation."""
    global game_state, sound_on
    
    if game_state == "MENU":
        if btn_start.collidepoint(pos):
            reset_game()
        elif btn_sound.collidepoint(pos):
            sound_on = not sound_on
            if not sound_on:
                music.stop()
            else: 
                try:
                    music.play('music')
                except:
                    pass
        elif btn_quit.collidepoint(pos):
            quit()
            
    elif game_state == "GAME":
        if btn_back_menu.collidepoint(pos):
            game_state = "MENU"
            
    elif game_state in ["GAME_OVER", "WIN"]:
        if btn_try_again.collidepoint(pos):
            reset_game()

def draw_button(rect, color, text):
    """Helper function to draw stylized buttons."""
    screen.draw.filled_rect(Rect((rect.x+5, rect.y+5), (rect.w, rect.h)), C_SHADOW)
    screen.draw.filled_rect(rect, color)
    screen.draw.text(text, center=rect.center, fontsize=35, color=C_TEXT, shadow=(1,1), scolor="black")

def draw():
    """Main draw loop."""
    screen.clear()
    try:
        screen.blit("background", (0, 0))
    except:
        screen.fill((30, 30, 50))

    if DEBUG_MODE and game_state == "GAME":
        for plat in platforms:
            screen.draw.filled_rect(plat, (255, 0, 0, 100))

    if game_state == "MENU":
        screen.draw.filled_rect(Rect((0,0), (WIDTH, HEIGHT)), (0, 0, 0, 0.7))
        screen.draw.text(TITLE, center=(WIDTH/2, 120), fontsize=80, color="cyan", shadow=(2,2), scolor="black")
        
        screen.draw.text("CONTROLS:", center=(WIDTH/2, 220), fontsize=40, color="yellow")
        screen.draw.text("Arrows: Move/Jump | Space: Attack", center=(WIDTH/2, 260), fontsize=30, color="white")
        
        draw_button(btn_start, C_BTN_NORMAL, "START HUNT")
        txt = "SOUND: ON" if sound_on else "SOUND: OFF"
        draw_button(btn_sound, C_BTN_SOUND if sound_on else C_BTN_OFF, txt)
        draw_button(btn_quit, (100, 100, 100), "EXIT")

    elif game_state == "GAME":
        hero.draw()
        for e in enemies:
            e.draw()
        
        # HUD
        screen.draw.text(f"LIVES: {hero.hp}", (20, 20), fontsize=40, color="white", shadow=(1,1), scolor="black")
        screen.draw.text(f"ENEMIES: {len(enemies)}", (20, 60), fontsize=40, color="red", shadow=(1,1), scolor="black")
        screen.draw.filled_rect(btn_back_menu, C_BTN_OFF)
        screen.draw.text("MENU", center=btn_back_menu.center, fontsize=25)

    elif game_state == "GAME_OVER":
        screen.draw.filled_rect(Rect((0,0), (WIDTH, HEIGHT)), (50, 0, 0, 0.8))
        screen.draw.text("GAME OVER", center=(WIDTH/2, 300), fontsize=80, color="red", shadow=(2,2), scolor="black")
        draw_button(btn_try_again, C_BTN_SOUND, "TRY AGAIN")

    elif game_state == "WIN":
        screen.draw.filled_rect(Rect((0,0), (WIDTH, HEIGHT)), (0, 50, 0, 0.8))
        screen.draw.text("VICTORY!", center=(WIDTH/2, 250), fontsize=100, color="yellow", shadow=(2,2), scolor="black")
        screen.draw.text("Dungeon Cleared.", center=(WIDTH/2, 350), fontsize=40, color="white")
        draw_button(btn_try_again, C_BTN_NORMAL, "PLAY AGAIN")

def update():
    """Main update loop handling game logic."""
    global game_state
    
    if sound_on:
        try:
            if not music.is_playing('music'):
                music.play('music')
        except:
            pass

    if game_state == "GAME":
        if len(enemies) == 0:
            game_state = "WIN"

        if hero.hp > 0:
            hero.update(enemies)
        else:
            game_state = "GAME_OVER"
        
        # Update enemies and check collisions
        for e in enemies[:]:
            e.update(hero, enemies)
            if e.hp <= 0:
                enemies.remove(e)
            
            # Safe Collision Check using reduced hitbox
            if hero.get_hitbox().colliderect(e.get_hitbox()) and e.state != "hurt":
                hero.take_damage()

pgzrun.go()