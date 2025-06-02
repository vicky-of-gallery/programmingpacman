import pygame
import random
import sys

# --- Settings ---
TILE_SIZE = 24
WIDTH, HEIGHT = 28 * TILE_SIZE, 31 * TILE_SIZE
FPS = 60
GHOST_COLORS = [(255,0,0), (255,184,255), (0,255,255), (255,184,82)]
PLAYER_COLOR = (255, 255, 0)
PELLET_COLOR = (255, 255, 255)
POWER_COLOR = (0, 0, 255)
BG_COLOR = (0, 0, 0)
FONT_NAME = 'arial'

# --- Level Map (0=wall, 1=pellet, 2=power pellet, 9=empty) ---
LEVEL = [
    "0000000000000000000000000000",
    "0111111110111111111011111110",
    "0120000010100000010100000210",
    "0111111110111111111011111110",
    "0100000010001000001000000010",
    "0111111011111111101111111110",
    "0000010100001000100001000000",
    "1111010111110111101111011111",
    "0001010000010000100001010000",
    "0111111110111111111011111110",
    "0100000010100000010100000010",
    "0111111110111111111011111110",
    "0000000000000000000000000000",
] * 2  # Repeat for more vertical space

LEVEL = LEVEL[:31]  # Ensure height matches classic Pac-Man

# --- Helper functions ---
def draw_text(screen, text, size, x, y, color=(255,255,255)):
    font = pygame.font.SysFont(FONT_NAME, size, True)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    screen.blit(text_surface, text_rect)

def load_sounds():
    pygame.mixer.init()
    sounds = {
        "chomp": pygame.mixer.Sound(pygame.mixer.Sound("chomp.wav")),
        "eat_ghost": pygame.mixer.Sound(pygame.mixer.Sound("eat_ghost.wav")),
        "death": pygame.mixer.Sound(pygame.mixer.Sound("death.wav")),
        "power": pygame.mixer.Sound(pygame.mixer.Sound("power.wav"))
    }
    return sounds

# --- Sprite Classes ---
class Wall(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((33,33,255))
        self.rect = self.image.get_rect(topleft=pos)

class Pellet(pygame.sprite.Sprite):
    def __init__(self, pos, power=False):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        color = POWER_COLOR if power else PELLET_COLOR
        radius = 7 if power else 3
        pygame.draw.circle(self.image, color, (TILE_SIZE//2, TILE_SIZE//2), radius)
        self.rect = self.image.get_rect(topleft=pos)
        self.power = power

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PLAYER_COLOR, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2-2)
        self.rect = self.image.get_rect(topleft=pos)
        self.dir = pygame.Vector2(1, 0)
        self.next_dir = self.dir
        self.speed = 2.7
        self.lives = 3
        self.score = 0
        self.power_timer = 0

    def update(self, walls):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:    self.next_dir = pygame.Vector2(0, -1)
        if keys[pygame.K_DOWN]:  self.next_dir = pygame.Vector2(0, 1)
        if keys[pygame.K_LEFT]:  self.next_dir = pygame.Vector2(-1, 0)
        if keys[pygame.K_RIGHT]: self.next_dir = pygame.Vector2(1, 0)
        # Try to turn
        if self.can_move(self.next_dir, walls):
            self.dir = self.next_dir
        # Move
        if self.can_move(self.dir, walls):
            self.rect.x += self.dir.x * self.speed
            self.rect.y += self.dir.y * self.speed
        # Wrap
        self.rect.x %= WIDTH
        self.rect.y %= HEIGHT

    def can_move(self, direction, walls):
        next_rect = self.rect.move(direction.x * self.speed, direction.y * self.speed)
        return not pygame.sprite.spritecollideany(WallSprite(next_rect), walls)

class WallSprite(pygame.sprite.Sprite):
    # Helper for collision checking
    def __init__(self, rect):
        super().__init__()
        self.rect = rect

class Ghost(pygame.sprite.Sprite):
    def __init__(self, pos, color, ai_type="random"):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2-2)
        self.rect = self.image.get_rect(topleft=pos)
        self.init_pos = pos
        self.dir = pygame.Vector2(1, 0)
        self.speed = 2.3
        self.ai_type = ai_type
        self.frightened = False
        self.frightened_timer = 0

    def update(self, player, walls):
        if self.frightened:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.frightened = False
        # AI: random or chase
        dirs = [pygame.Vector2(1,0), pygame.Vector2(-1,0), pygame.Vector2(0,1), pygame.Vector2(0,-1)]
        valid_dirs = [d for d in dirs if self.can_move(d, walls)]
        if self.ai_type=="chase" and not self.frightened:
            # Move towards player (simple: pick best axis)
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            prefer = pygame.Vector2((dx>0)-(dx<0), (dy>0)-(dy<0))
            if prefer in valid_dirs:
                self.dir = prefer
            else:
                self.dir = random.choice(valid_dirs) if valid_dirs else self.dir
        else:
            if random.random()<0.1:
                self.dir = random.choice(valid_dirs) if valid_dirs else self.dir
        # Move
        self.rect.x += self.dir.x * self.speed
        self.rect.y += self.dir.y * self.speed
        # Wrap
        self.rect.x %= WIDTH
        self.rect.y %= HEIGHT

    def can_move(self, direction, walls):
        next_rect = self.rect.move(direction.x * self.speed, direction.y * self.speed)
        return not pygame.sprite.spritecollideany(WallSprite(next_rect), walls)

    def set_frightened(self):
        self.frightened = True
        self.frightened_timer = FPS * 8  # 8 seconds

    def reset(self):
        self.rect.topleft = self.init_pos
        self.frightened = False

# --- Main Game ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pac-Man Clone - Python/Pygame")
    clock = pygame.time.Clock()
    #sounds = load_sounds()  # Uncomment if you add sound files

    # Sprite groups
    walls = pygame.sprite.Group()
    pellets = pygame.sprite.Group()
    ghosts = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()

    # Build level
    for y, row in enumerate(LEVEL):
        for x, c in enumerate(row):
            pos = (x*TILE_SIZE, y*TILE_SIZE)
            if c == '0':
                wall = Wall(pos)
                walls.add(wall)
                all_sprites.add(wall)
            elif c == '1':
                pellet = Pellet(pos)
                pellets.add(pellet)
                all_sprites.add(pellet)
            elif c == '2':
                pellet = Pellet(pos, power=True)
                pellets.add(pellet)
                all_sprites.add(pellet)

    # Player and Ghosts
    player = Player((TILE_SIZE*14, TILE_SIZE*23))
    all_sprites.add(player)
    for i in range(4):
        ghost = Ghost((TILE_SIZE*(13+i), TILE_SIZE*14), GHOST_COLORS[i], ai_type="chase" if i==0 else "random")
        ghosts.add(ghost)
        all_sprites.add(ghost)

    running = True
    game_over = False

    while running:
        clock.tick(FPS)
        screen.fill(BG_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not game_over:
            player.update(walls)
            ghosts.update(player, walls)

            # Pellet collision
            hit = pygame.sprite.spritecollide(player, pellets, True)
            for p in hit:
                if p.power:
                    for g in ghosts:
                        g.set_frightened()
                    #sounds["power"].play()
                    player.score += 50
                else:
                    #sounds["chomp"].play()
                    player.score += 10

            # Ghost collision
            for g in ghosts:
                if player.rect.colliderect(g.rect):
                    if g.frightened:
                        g.reset()
                        g.frightened = False
                        #sounds["eat_ghost"].play()
                        player.score += 200
                    else:
                        #sounds["death"].play()
                        player.lives -= 1
                        player.rect.topleft = (TILE_SIZE*14, TILE_SIZE*23)
                        for gi, ghost in enumerate(ghosts):
                            ghost.reset()
                            ghost.rect.topleft = (TILE_SIZE*(13+gi), TILE_SIZE*14)
                        if player.lives <= 0:
                            game_over = True

            # Win check
            if not pellets:
                draw_text(screen, "YOU WIN!", 64, WIDTH//2, HEIGHT//2-32)
                pygame.display.flip()
                pygame.time.wait(4000)
                running = False

        all_sprites.draw(screen)
        # HUD
        draw_text(screen, f"Score: {player.score}", 24, 60, 5)
        draw_text(screen, f"Lives: {player.lives}", 24, WIDTH-60, 5)
        if game_over:
            draw_text(screen, "GAME OVER", 56, WIDTH//2, HEIGHT//2-32, (255,0,0))
            draw_text(screen, "Press ESC to quit", 32, WIDTH//2, HEIGHT//2+32)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                running = False

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()