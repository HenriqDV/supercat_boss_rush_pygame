import math
import os
import random
import sys
import pygame
#IGNORAR OS # ANTIGO, IR NO FINAL DO CODIGO PARA SABER O QUE MUDOU NO CODIGO
pygame.init()

VIRTUAL_WIDTH, VIRTUAL_HEIGHT = 960, 640
canvas = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

ARENA_MARGIN_X = 50
ARENA_MARGIN_Y = 50
ARENA_WIDTH = VIRTUAL_WIDTH - (ARENA_MARGIN_X * 2)
ARENA_HEIGHT = VIRTUAL_HEIGHT - (ARENA_MARGIN_Y * 2)

WINDOWED_WIDTH, WINDOWED_HEIGHT = 960, 640
screen = pygame.display.set_mode(
    (WINDOWED_WIDTH, WINDOWED_HEIGHT), pygame.RESIZABLE
)
pygame.display.set_caption("Boss Rush(Pygame)")
clock = pygame.time.Clock()
FPS = 60

pygame.mouse.set_visible(False)
is_fullscreen = False

end_overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
end_overlay.fill((10, 12, 18, 220))

#PREGUIÇA de pensar em cor pvfr pensar nas cores e cenário
BG_COLOR = (14, 16, 24)
ARENA_COLOR = (22, 26, 38)
GRID_LINE = (32, 38, 54)
WALL_COLOR = (42, 50, 72)

PLAYER_COLOR = (0, 240, 255)       # Cyan,TEMP
PLAYER_BULLET = (120, 220, 255)
BOSS_COLOR_1 = (255, 0, 110)       # Neon Pink,TEMP
BOSS_COLOR_2 = (255, 180, 0)       # Amber,TEMP
BOSS_COLOR_3 = (180, 0, 255)       # Purple,TEMP
ENEMY_BULLET = (255, 50, 80)
HUD_BG = (10, 12, 18)
ITEM_COLOR = (0, 255, 160)

# SPRITES DO SUPERCAT (PASTA assets/ AO LADO DESTE ARQUIVO)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
CAT_SCALE = 1.5          # TAMANHO DO GATO NA TELA (1.5 = 75x75 px), MUDAR AQUI SE FICAR GRANDE/PEQUENO
MOOD_HAPPY_TIME = 1.2    # QUANTO TEMPO ELE FICA FELIZ (BOSS DERROTADO / POWERUP)
MOOD_SAD_TIME = 0.8      # QUANTO TEMPO ELE FICA TRISTE DEPOIS DE TOMAR DANO

# AJUSTES DAS ANIMAÇÕES (TUDO EM SEGUNDOS / PIXELS / GRAUS)
TURN_TIME = 0.14         # TEMPO DA ANIMAÇÃO DE VIRAR (ACHATA E DESACHATA)
SHOOT_FACE_HOLD = 0.3    # DEPOIS DE ATIRAR ELE CONTINUA OLHANDO PRO LADO DO TIRO POR ESSE TEMPO
BOB_SPEED = 5.0          # VELOCIDADE DO "FLUTUAR"
BOB_AMP = 3.0            # ALTURA DO "FLUTUAR"
TILT_MAX = 10            # INCLINAÇÃO MAXIMA QUANDO SOBE/DESCE
RECOIL_TIME = 0.09       # TRANCO DO TIRO
POP_TIME = 0.25          # "PULINHO" QUANDO TROCA DE EXPRESSÃO


def load_sprite(name, scale=1.0):
    # SE A IMAGEM NAO EXISTIR O JOGO NAO QUEBRA, SÓ VOLTA A DESENHAR O CIRCULO
    path = os.path.join(ASSETS_DIR, name)
    try:
        img = pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        print(f"[AVISO] Sprite nao encontrado: {path}")
        return None
    if scale != 1.0:
        w, h = img.get_size()
        img = pygame.transform.scale(img, (round(w * scale), round(h * scale)))  # scale (nao smooth) mantem o pixel art
    return img


CAT_SPRITES = {
    "normal": load_sprite("gato_normal.png", CAT_SCALE),
    "feliz": load_sprite("gato_feliz.png", CAT_SCALE),
    "triste": load_sprite("gato_triste.png", CAT_SCALE),
}
# VERSOES JA VIRADAS PRA ESQUERDA (FEITAS 1 VEZ SÓ, NAO TODO FRAME)
CAT_SPRITES_LEFT = {
    k: (pygame.transform.flip(v, True, False) if v is not None else None) for k, v in CAT_SPRITES.items()
}
HAIRBALL_SPRITE = load_sprite("bola_de_pelo.png")
HEART_SPRITE = load_sprite("coracao.png")
_hairball_cache = {}
HAIRBALL_ANGLE_STEPS = 24  # 15 EM 15 GRAUS


def get_hairball(size, angle=0.0):
    # BOLA DE PELO NO TAMANHO DO TIRO (O EXTENDER AUMENTA O TAMANHO), GIRANDO
    if HAIRBALL_SPRITE is None:
        return None
    diameter = size * 3 + 4  # TIRO 6 = 22px, COM EXTENDER 9 = 31px
    step = int(round(angle / (360 / HAIRBALL_ANGLE_STEPS))) % HAIRBALL_ANGLE_STEPS
    key = (diameter, step)
    if key not in _hairball_cache:
        base = pygame.transform.scale(HAIRBALL_SPRITE, (diameter, diameter))
        _hairball_cache[key] = pygame.transform.rotate(base, step * (360 / HAIRBALL_ANGLE_STEPS))
    return _hairball_cache[key]


# ======================= PARTICULAS E TREMIDA DE TELA =======================
# LISTA GLOBAL PRA QUALQUER PARTE DO CODIGO PODER SOLTAR PARTICULA
particles = []
SHAKE = {"time": 0.0, "dur": 0.0, "power": 0.0}
MAX_PARTICLES = 500  # LIMITE PRA NAO PESAR


class Particle:
    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0, image=None):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vx, vy)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.image = image

    def update(self, dt):
        self.life -= dt
        self.vel.y += self.gravity * dt
        self.vel *= math.pow(0.9, dt * 60.0)  # ARRASTO, PRA PARTICULA "FREIAR"
        self.pos += self.vel * (dt * 60.0)

    def draw(self, surface):
        t = max(0.0, self.life / self.max_life)
        if self.image is not None:
            self.image.set_alpha(int(255 * min(1.0, t * 1.6)))
            surface.blit(self.image, self.image.get_rect(center=(int(self.pos.x), int(self.pos.y))))
            self.image.set_alpha(255)
            return
        s = max(1, int(self.size * t + 0.5))  # VAI DIMINUINDO ATÉ SUMIR (QUADRADINHO = PIXEL ART)
        pygame.draw.rect(surface, self.color, (int(self.pos.x) - s // 2, int(self.pos.y) - s // 2, s, s))


def spawn_burst(x, y, colors, count, speed=3.0, life=0.45, size=5, gravity=0.0, spread=math.tau, angle=0.0):
    if len(particles) > MAX_PARTICLES:
        return
    for _ in range(count):
        a = angle + random.uniform(-spread / 2, spread / 2)
        spd = random.uniform(speed * 0.35, speed)
        particles.append(
            Particle(x, y, math.cos(a) * spd, math.sin(a) * spd, random.uniform(life * 0.6, life),
                     random.choice(colors), random.randint(max(2, size - 2), size), gravity)
        )


def spawn_hearts(x, y, count=3):
    for _ in range(count):
        particles.append(
            Particle(x + random.uniform(-18, 18), y - 20, random.uniform(-0.6, 0.6), random.uniform(-1.6, -0.9),
                     random.uniform(0.6, 0.9), (255, 80, 100), 6, gravity=-0.5, image=HEART_SPRITE)
        )


def add_shake(power, duration):
    # SE JA TA TREMENDO MAIS FORTE NAO DIMINUI
    if power >= SHAKE["power"] or SHAKE["time"] <= 0:
        SHAKE["power"] = power
        SHAKE["time"] = duration
        SHAKE["dur"] = duration


def update_effects(dt):
    for p in particles[:]:
        p.update(dt)
        if p.life <= 0:
            particles.remove(p)
    if SHAKE["time"] > 0:
        SHAKE["time"] -= dt


def get_shake_offset():
    if SHAKE["time"] <= 0:
        return 0, 0
    k = SHAKE["power"] * (SHAKE["time"] / max(0.001, SHAKE["dur"]))
    return int(random.uniform(-k, k)), int(random.uniform(-k, k))


FUR_COLORS = [(247, 160, 70), (230, 120, 40), (255, 205, 140), (180, 90, 40)]
HURT_COLORS = [(255, 70, 90), (255, 255, 255), (255, 150, 160)]

#INSUPORTÁVEL NUNCA MAIS FAZER!!!
class Projectile:
    def __init__(self, x, y, vel_x, vel_y, damage, range_limit, color=PLAYER_BULLET, size=6, is_hairball=False):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.damage = damage
        self.range_remaining = range_limit
        self.color = color
        self.size = size
        self.is_hairball = is_hairball  # TIRO DO SUPERCAT = BOLA DE PELO
        self.angle = random.uniform(0, 360)
        self.spin = 540 if vel_x <= 0 else -540  # GIRA PRO LADO QUE TA INDO
        self.trail_timer = 0.0

    def update(self, dt):
        step = self.vel * (dt * 60.0)
        self.pos += step
        self.range_remaining -= step.length()
        if self.is_hairball:
            self.angle = (self.angle + self.spin * dt) % 360
            # RASTRO DE PELINHO
            self.trail_timer -= dt
            if self.trail_timer <= 0 and len(particles) < MAX_PARTICLES:
                self.trail_timer = 0.025
                particles.append(
                    Particle(self.pos.x + random.uniform(-3, 3), self.pos.y + random.uniform(-3, 3),
                             -self.vel.x * 0.05, -self.vel.y * 0.05, 0.22, random.choice(FUR_COLORS), 4)
                )

    def draw(self, surface):
        if self.is_hairball:
            img = get_hairball(self.size, self.angle)
            if img is not None:
                surface.blit(img, img.get_rect(center=(int(self.pos.x), int(self.pos.y))))
                return
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.size)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), max(1, self.size // 2))

#PLAYER DPS MUDAR TÁ MUITO FORTE
class PlayerShip:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.radius = 16

        self.max_speed = 5.2
        self.accel = 0.8
        self.friction = 0.82

        self.hp = 12
        self.max_hp = 12

        self.damage = 4.0
        self.fire_delay = 0.2
        self.fire_cooldown = 0.0
        self.proj_speed = 9.5
        self.proj_range = 420
        self.proj_size = 6

        self.iframe = 0.0

        # HUMOR DO SUPERCAT: "normal", "feliz" ou "triste"
        self.mood = "normal"
        self.mood_timer = 0.0

        # PRA ONDE ELE OLHA. O SPRITE ORIGINAL OLHA PRA DIREITA
        self.facing_left = False
        self.shoot_face_timer = 0.0  # ENQUANTO > 0 O LADO DO TIRO MANDA, NAO O DO MOVIMENTO
        self.turn_timer = 0.0        # ANIMAÇÃO DE VIRAR

        # ANIMAÇÕES
        self.anim_time = random.uniform(0, 10)
        self.tilt = 0.0
        self.recoil_timer = 0.0
        self.recoil_dir = pygame.math.Vector2(0, 0)
        self.pop_timer = 0.0
        self.heart_timer = 0.0

    def set_mood(self, mood, duration):
        # TRISTE TEM PRIORIDADE: SE TOMOU DANO NAO FICA FELIZ POR CIMA
        if mood == "feliz" and self.mood == "triste" and self.mood_timer > 0:
            return
        if mood != self.mood:
            self.pop_timer = POP_TIME  # PULINHO QUANDO MUDA A CARA
        self.mood = mood
        self.mood_timer = duration
        if mood == "feliz":
            spawn_hearts(self.pos.x, self.pos.y, 3)

    def take_damage(self, amount=1):
        # TODO DANO NO PLAYER PASSA POR AQUI AGORA. RETORNA True SE MORREU
        self.hp -= amount
        self.iframe = 0.5
        self.set_mood("triste", MOOD_SAD_TIME)
        spawn_burst(self.pos.x, self.pos.y, HURT_COLORS, 14, speed=4.5, life=0.4, size=6)
        add_shake(7, 0.25)
        return self.hp <= 0

    def face(self, left):
        # SÓ COMEÇA A ANIMAÇÃO DE VIRAR SE REALMENTE MUDOU DE LADO
        if left != self.facing_left:
            self.facing_left = left
            self.turn_timer = TURN_TIME

    def handle_input(self, projectiles, dt):
        keys = pygame.key.get_pressed()
        move_dir = pygame.math.Vector2(0, 0)

        if keys[pygame.K_w]:
            move_dir.y -= 1
        if keys[pygame.K_s]:
            move_dir.y += 1
        if keys[pygame.K_a]:
            move_dir.x -= 1
        if keys[pygame.K_d]:
            move_dir.x += 1

        if move_dir.length_squared() > 0:
            move_dir = move_dir.normalize()
            self.vel += move_dir * (self.accel * dt * 60.0)
            if self.vel.length() > self.max_speed:
                self.vel = self.vel.normalize() * self.max_speed

        self.vel *= math.pow(self.friction, dt * 60.0)
        self.pos += self.vel * (dt * 60.0)

        #MARGIN DO CENÁRIO SE PÁ MUDAR DEPENDENDO DO BOSS SE ESSE FOR O JOGO
        self.clamp_to_arena()

        shoot_dir = pygame.math.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_j]:
            shoot_dir.x -= 1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_l]:
            shoot_dir.x += 1
        elif keys[pygame.K_UP] or keys[pygame.K_i]:
            shoot_dir.y -= 1
        elif keys[pygame.K_DOWN] or keys[pygame.K_k]:
            shoot_dir.y += 1

        # ===== CORREÇÃO DO BUG DE VIRAR =====
        # ANTES: ANDAR PRA DIREITA VIRAVA O GATO PRA DIREITA E O TIRO PRA ESQUERDA VIRAVA DE VOLTA,
        # TODO FRAME, ENTAO ELE FICAVA PISCANDO DE UM LADO PRO OUTRO.
        # AGORA: SEGURANDO TIRO PRO LADO, O LADO DO TIRO MANDA (E CONTINUA MANDANDO UM POUQUINHO DEPOIS).
        # SÓ QUANDO NAO TA ATIRANDO PRO LADO É QUE O MOVIMENTO DECIDE.
        if shoot_dir.x != 0:
            self.face(shoot_dir.x < 0)
            self.shoot_face_timer = SHOOT_FACE_HOLD
        elif self.shoot_face_timer <= 0 and move_dir.x != 0:
            self.face(move_dir.x < 0)

        if shoot_dir.length_squared() > 0 and self.fire_cooldown <= 0:
            shoot_n = shoot_dir.normalize()
            shoot_vec = shoot_n * self.proj_speed
            final_vel = shoot_vec + (self.vel * 0.3)  # Momentum FODA
            # A BOLA SAI DA FRENTE DO GATO, NAO DO MEIO DA BARRIGA
            spawn = self.pos + shoot_n * 18
            projectiles.append(
                Projectile(
                    spawn.x,
                    spawn.y,
                    final_vel.x,
                    final_vel.y,
                    self.damage,
                    self.proj_range,
                    PLAYER_BULLET,
                    self.proj_size,
                    is_hairball=True,
                )
            )
            self.fire_cooldown = self.fire_delay
            # TRANCO + PUFF DE PELO NA SAIDA DO TIRO
            self.recoil_timer = RECOIL_TIME
            self.recoil_dir = shoot_n
            spawn_burst(spawn.x, spawn.y, FUR_COLORS, 4, speed=2.2, life=0.2, size=4,
                        spread=1.2, angle=math.atan2(shoot_n.y, shoot_n.x))

    def update(self, dt):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt
        if self.iframe > 0:
            self.iframe -= dt
        if self.mood_timer > 0:
            self.mood_timer -= dt
            if self.mood_timer <= 0:
                self.mood = "normal"
                self.pop_timer = POP_TIME
        for attr in ("shoot_face_timer", "turn_timer", "recoil_timer", "pop_timer"):
            v = getattr(self, attr)
            if v > 0:
                setattr(self, attr, max(0.0, v - dt))

        self.anim_time += dt
        # INCLINA SUAVE PRA CIMA/BAIXO CONFORME A VELOCIDADE VERTICAL (LERP PRA NAO DAR TRANCO)
        target = max(-TILT_MAX, min(TILT_MAX, -self.vel.y * 2.2))
        if self.facing_left:
            target = -target
        self.tilt += (target - self.tilt) * min(1.0, dt * 12.0)

        # CORAÇÕEZINHOS ENQUANTO TA FELIZ
        if self.mood == "feliz":
            self.heart_timer -= dt
            if self.heart_timer <= 0:
                self.heart_timer = 0.3
                spawn_hearts(self.pos.x, self.pos.y, 1)

    def draw(self, surface):
        x, y = self.pos.x, self.pos.y
        hurt_flash = self.iframe > 0 and int(self.iframe * 20) % 2 == 0

        base_r = CAT_SPRITES.get(self.mood) or CAT_SPRITES.get("normal")
        if base_r is None:
            # SEM SPRITE: VOLTA PRO CIRCULO ANTIGO (COM O FLICKER ANTIGO)
            if hurt_flash:
                return  # Damage flicker MANEIRINHO
            pygame.draw.circle(surface, PLAYER_COLOR, (int(x), int(y)), self.radius, 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), 5)
            return

        # --- VIRADA: ACHATA ATÉ O MEIO, TROCA O LADO, DESACHATA ---
        sx, sy = 1.0, 1.0
        draw_left = self.facing_left
        if self.turn_timer > 0:
            prog = 1.0 - self.turn_timer / TURN_TIME
            sx = max(0.12, abs(1.0 - 2.0 * prog))
            if prog < 0.5:
                draw_left = not self.facing_left
        base = (CAT_SPRITES_LEFT if draw_left else CAT_SPRITES).get(self.mood) or base_r

        # --- TRANCO DO TIRO (ESTICA UM POUCO) ---
        rec = self.recoil_timer / RECOIL_TIME if self.recoil_timer > 0 else 0.0
        sx *= 1.0 - 0.08 * rec
        sy *= 1.0 + 0.06 * rec

        # --- PULINHO AO TROCAR DE EXPRESSÃO ---
        if self.pop_timer > 0:
            k = self.pop_timer / POP_TIME
            s = 1.0 + 0.22 * math.sin(k * math.pi)
            sx *= s
            sy *= s

        bw, bh = base.get_size()
        img = base
        if abs(sx - 1.0) > 0.01 or abs(sy - 1.0) > 0.01:
            img = pygame.transform.scale(base, (max(1, int(bw * sx)), max(1, int(bh * sy))))
        ang = int(round(self.tilt))
        if ang != 0:
            img = pygame.transform.rotate(img, ang)

        # --- PISCADA DE DANO: AGORA FICA VERMELHO EM VEZ DE SUMIR ---
        if hurt_flash:
            img = img.copy()
            img.fill((150, 30, 30, 0), special_flags=pygame.BLEND_RGBA_ADD)

        bob = math.sin(self.anim_time * BOB_SPEED) * BOB_AMP
        off = -self.recoil_dir * 4 * rec

        # SOMBRA (DÁ IDEIA DE QUE ELE TA VOANDO)
        shadow_w = int(46 - bob * 2)
        shadow = pygame.Surface((shadow_w, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        surface.blit(shadow, shadow.get_rect(center=(int(x), int(y + 34))))

        # A HITBOX CONTINUA SENDO O CIRCULO DE RAIO 16, O SPRITE É SÓ O DESENHO
        surface.blit(img, img.get_rect(center=(int(x + off.x), int(y + bob + off.y))))

    def clamp_to_arena(self):
        self.pos.x = max(
            ARENA_MARGIN_X + self.radius,
            min(VIRTUAL_WIDTH - ARENA_MARGIN_X - self.radius, self.pos.x)
        )
        self.pos.y = max(
            ARENA_MARGIN_Y + self.radius + 10,
            min(VIRTUAL_HEIGHT - ARENA_MARGIN_Y - self.radius - 20, self.pos.y)
        )

#OS BOSSES SEM CRIATIVIDADE PENSAR É DIFICIL(ODEIO TODOS)
class BossPrism:
    def __init__(self):
        self.name = "FODÂO"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 200)
        self.radius = 42
        self.hp = 280
        self.max_hp = 280

        self.timer = 0.0
        self.action_timer = 0.0
        self.is_airborne = False
        self.jump_y_offset = 0
        self.jump_target = pygame.math.Vector2(self.pos)

    def get_hitbox_pos(self):
        return pygame.math.Vector2(self.pos.x, self.pos.y - self.jump_y_offset)

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        self.action_timer += dt

        if not self.is_airborne:
            if self.action_timer >= 2.5:
                self.action_timer = 0.0
                if random.random() < 0.5:
                    dir_to_p = (player_pos - self.pos).normalize()
                    base_angle = math.atan2(dir_to_p.y, dir_to_p.x)
                    for _ in range(8):
                        spread = random.uniform(-0.4, 0.4)
                        spd = random.uniform(3.5, 6.0)
                        vx = math.cos(base_angle + spread) * spd
                        vy = math.sin(base_angle + spread) * spd
                        enemy_projectiles.append(
                            Projectile(self.pos.x, self.pos.y, vx, vy, 1, 380, ENEMY_BULLET, 5)
                        )
                else:
                    self.is_airborne = True
                    self.jump_target = pygame.math.Vector2(player_pos)
                    self.action_timer = 0.0
        else:
            jump_progress = min(1.0, self.action_timer / 0.9)
            self.jump_y_offset = math.sin(jump_progress * math.pi) * 160
            self.pos += (self.jump_target - self.pos) * (0.06 * dt * 60.0)

            if jump_progress >= 1.0:
                self.is_airborne = False
                self.jump_y_offset = 0
                self.action_timer = 0.0
                for i in range(8):
                    a = i * (math.tau / 8)
                    enemy_projectiles.append(
                        Projectile(self.pos.x, self.pos.y, math.cos(a) * 4, math.sin(a) * 4, 1, 280, ENEMY_BULLET, 5)
                    )

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y - self.jump_y_offset)

        if self.is_airborne:
            pygame.draw.ellipse(surface, (10, 10, 15), (int(self.pos.x) - 30, int(self.pos.y) + 20, 60, 20))

        pts = []
        for i in range(8):
            ang = i * (math.tau / 8) + (self.timer * 1.2)
            pts.append((x + math.cos(ang) * self.radius, y + math.sin(ang) * self.radius))

        pygame.draw.polygon(surface, BOSS_COLOR_1, pts, 3)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 8)


class OrbitalDrone: #FINALMENTE OS DRONES ESTÃO FUNCIONANDO ADEUS BETINHA
    def __init__(self, boss_pos):
        self.pos = pygame.math.Vector2(boss_pos)
        self.vel = pygame.math.Vector2(0, 0)
        self.radius = 10
        self.hp = 12
        self.max_hp = 12
        self.angle = random.uniform(0, math.tau)
        self.orbit_dist = 65
        self.is_attacking = False
        self.attack_timer = random.uniform(2.0, 4.0)

    def update(self, boss_pos, player_pos, dt):
        self.attack_timer -= dt

        if not self.is_attacking:
            # FICA ORBITANDO EM STAND BY SE NÃO TIVER ATACANDO
            self.angle += 2.0 * dt

            target_x = boss_pos.x + math.cos(self.angle) * self.orbit_dist
            target_y = boss_pos.y + math.sin(self.angle) * self.orbit_dist
            target = pygame.math.Vector2(target_x, target_y)
            self.pos += (target - self.pos) * 0.15

            if self.attack_timer <= 0:
                self.is_attacking = True
                self.attack_timer = 3.5  #TIMER DO 'ATAQUE'
        else:
            dir_to_player = (player_pos - self.pos)
            if dir_to_player.length_squared() > 0:
                self.vel += dir_to_player.normalize() * 0.4
                if self.vel.length() > 3.8:
                    self.vel = self.vel.normalize() * 3.8 #MOVE EM DIREÇÃO DO PLAYER

            self.pos += self.vel * (dt * 60.0)

            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_timer = random.uniform(3.0, 5.0)

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        color = (255, 210, 50) if self.is_attacking else BOSS_COLOR_2
        pygame.draw.circle(surface, color, (x, y), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 3)


class BossOrbital:
    def __init__(self):
        self.name = "FODINHA" #ADEUS BETINHA, AGORA ELE É O FODINHA
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 200)
        self.radius = 38
        self.hp = 360
        self.max_hp = 360
        self.timer = 0.0
        self.spawn_timer = 0.0
        self.burst_timer = 0.0
        self.drones = []
        self.max_drones = 4

    def get_hitbox_pos(self):
        return self.pos

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        self.spawn_timer += dt
        self.burst_timer += dt

        self.pos.x += math.sin(self.timer * 1.2) * (2.0 * dt * 60.0)
        self.pos.y += math.cos(self.timer * 1.8) * (1.2 * dt * 60.0)

        if self.spawn_timer >= 2.2 and len(self.drones) < self.max_drones:
            self.spawn_timer = 0.0
            self.drones.append(OrbitalDrone(self.pos))

        if self.burst_timer >= 2.0:
            self.burst_timer = 0.0
            for i in range(6):
                a = (self.timer * 6.0) + (i * math.tau / 6)
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.8, math.sin(a) * 3.8, 1, 320, BOSS_COLOR_2, 5)
                )

        for drone in self.drones[:]:
            drone.update(self.pos, player_pos, dt)

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)

        pygame.draw.circle(surface, BOSS_COLOR_2, (x, y), self.radius, 3)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 10)

        for drone in self.drones:
            drone.draw(surface)

#AMO AS MULHERES
class BossCore:
    def __init__(self):
        self.name = "PODER FEMININO"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 40)
        self.radius = 48
        self.hp = 480
        self.max_hp = 480
        self.timer = 0.0
        self.radial_timer = 0.0
        self.aimed_timer = 0.0

    def get_hitbox_pos(self):
        return self.pos

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        self.radial_timer += dt
        self.aimed_timer += dt

        if self.radial_timer >= 1.5:
            self.radial_timer = 0.0
            for i in range(12):
                a = i * (math.tau / 12)
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.8, math.sin(a) * 3.8, 1, 400, BOSS_COLOR_3, 6)
                )

        if self.aimed_timer >= 2.16:
            self.aimed_timer = 0.0
            dir_to_p = (player_pos - self.pos).normalize()
            base_a = math.atan2(dir_to_p.y, dir_to_p.x)
            for spread in [-0.15, 0, 0.15]:
                vx = math.cos(base_a + spread) * 5.0
                vy = math.sin(base_a + spread) * 5.0
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, vx, vy, 1, 400, BOSS_COLOR_3, 6)
                )

    def draw(self, surface):
        r = int(self.radius + math.sin(self.timer * 7.2) * 4)
        x, y = int(self.pos.x), int(self.pos.y)

        pygame.draw.rect(surface, BOSS_COLOR_3, (x - r, y - r, r * 2, r * 2), width=3, border_radius=6)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 12)

BOSS_COLORS = {BossPrism: BOSS_COLOR_1, BossOrbital: BOSS_COLOR_2, BossCore: BOSS_COLOR_3}

#UPGRADES GENERICOS SEM GRAÇA MAS FUNCIONA(+/-)
def load_item(name, target_h=44):
    # CARREGA O SPRITE DO POWERUP JÁ NO TAMANHO CERTO (ALTURA ~44px)
    img = load_sprite(name)
    if img is None:
        return None
    w, h = img.get_size()
    k = target_h / h
    return pygame.transform.scale(img, (max(1, round(w * k)), target_h))


# CADA UPGRADE COM A SUA IMAGEM
ITEM_SPRITES = {
    "CADENCE": load_item("racao.png"),                 # +FIRE RATE  = RAÇÃO
    "AMPLIFIER": load_item("erva_de_gato.png"),        # +DAMAGE     = ERVA DE GATO
    "EXTENDER": load_item("bolas_de_pelo_triplas.png"),  # +RANGE&SIZE = 3 BOLAS DE PELO
}

class UpgradeCapsule:
    def __init__(self, item_type):
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 60)
        self.item_type = item_type
        self.collected = False

    def draw(self, surface, font):
        if self.collected:
            return

        x, y = int(self.pos.x), int(self.pos.y)
        t = pygame.time.get_ticks()
        pygame.draw.rect(surface, (40, 50, 70), (x - 24, y, 48, 18), border_radius=3)

        bob = math.sin(t * 0.005) * 4
        item_y = y - 26 + bob

        img = ITEM_SPRITES.get(self.item_type)
        if img is not None:
            # BRILHO PULSANDO ATRÁS DO ITEM
            glow_r = int(30 + math.sin(t * 0.006) * 4)
            glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*ITEM_COLOR, 45), (glow_r, glow_r), glow_r)
            pygame.draw.circle(glow, (*ITEM_COLOR, 120), (glow_r, glow_r), glow_r, 2)
            surface.blit(glow, glow.get_rect(center=(x, int(item_y))))
            surface.blit(img, img.get_rect(center=(x, int(item_y))))
            # BRILHINHOS SUBINDO
            if random.random() < 0.12 and len(particles) < MAX_PARTICLES:
                particles.append(Particle(x + random.uniform(-22, 22), item_y + random.uniform(-10, 18),
                                          0, random.uniform(-1.2, -0.6), 0.5, random.choice([ITEM_COLOR, (255, 255, 255)]), 3))
        else:
            pygame.draw.circle(surface, ITEM_COLOR, (x, int(item_y)), 10, 2)
            pygame.draw.circle(surface, (255, 255, 255), (x, int(item_y)), 4)

        if self.item_type == "CADENCE":
            txt = font.render("(+FIRE RATE)", True, ITEM_COLOR)
        elif self.item_type == "AMPLIFIER":
            txt = font.render("(+DAMAGE)", True, ITEM_COLOR)
        else:
            txt = font.render("(+RANGE & SIZE)", True, ITEM_COLOR)

        surface.blit(txt, txt.get_rect(center=(x, y + 35)))

def get_scaled_rect(virtual_w, virtual_h, target_w, target_h):
    scale = min(target_w / virtual_w, target_h / virtual_h)
    new_w = int(virtual_w * scale)
    new_h = int(virtual_h * scale)
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    return pygame.Rect(x, y, new_w, new_h)

#MAIN
def main():
    global is_fullscreen, screen

    def reset_game():
        player = PlayerShip(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 120)
        boss_queue = [BossPrism(), BossOrbital(), BossCore()]
        items_queue = ["CADENCE", "AMPLIFIER", "EXTENDER"]
        current_boss = boss_queue.pop(0)
        return player, boss_queue, items_queue, current_boss, None, [], [], 1, False, False, False

    (
        player,
        boss_queue,
        items_queue,
        current_boss,
        active_capsule,
        player_projectiles,
        enemy_projectiles,
        wave_number,
        game_over,
        victory,
        is_paused,
    ) = reset_game()

    font_large = pygame.font.SysFont("consolas", 40, bold=True)
    font_small = pygame.font.SysFont("consolas", 14, bold=True)

    while True:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    if not game_over and not victory:
                        is_paused = not is_paused

                if event.key == pygame.K_F11 or (
                    event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
                ):
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(
                            (WINDOWED_WIDTH, WINDOWED_HEIGHT), pygame.RESIZABLE
                        )

                if event.key == pygame.K_r:
                    (
                        player,
                        boss_queue,
                        items_queue,
                        current_boss,
                        active_capsule,
                        player_projectiles,
                        enemy_projectiles,
                        wave_number,
                        game_over,
                        victory,
                        is_paused,
                    ) = reset_game()
                    particles.clear()
                    SHAKE["time"] = 0.0

        if not is_paused and not game_over and not victory:
            player.handle_input(player_projectiles, dt)
            player.update(dt)
            update_effects(dt)  # PARTICULAS + TREMIDA
            if current_boss and getattr(current_boss, "hit_flash", 0) > 0:
                current_boss.hit_flash -= dt

            if current_boss:
                if isinstance(current_boss, BossOrbital):
                    current_boss.update(player.pos, enemy_projectiles, dt)
                    for drone in current_boss.drones[:]:
                        # DANO DO PLAYER NOS DRONES
                        for p in player_projectiles[:]:
                            if (p.pos - drone.pos).length() < (p.size + drone.radius):
                                drone.hp -= p.damage
                                spawn_burst(p.pos.x, p.pos.y, FUR_COLORS, 5, speed=2.5, life=0.3, size=4)
                                if p in player_projectiles:
                                    player_projectiles.remove(p)
                                if drone.hp <= 0:
                                    current_boss.drones.remove(drone)
                                    spawn_burst(drone.pos.x, drone.pos.y, [BOSS_COLOR_2, (255, 230, 120), (255, 255, 255)],
                                                16, speed=4.0, life=0.45, size=5)
                                    add_shake(3, 0.12)
                                    break

                        # DANO DO DRONE
                        if player.iframe <= 0 and (player.pos - drone.pos).length() < (player.radius + drone.radius):
                            if player.take_damage():
                                game_over = True
                else:
                    current_boss.update(player.pos, enemy_projectiles, dt)

                #COLISÃO BEM FRAQUINHA, FAZ MELHOR PFVR
                boss_hitbox_pos = current_boss.get_hitbox_pos()
                is_grounded = not getattr(current_boss, "is_airborne", False) #tive que mudar como a hitbox dele funciona pq ele tava dando push out of bounds
                if is_grounded:
                    diff = player.pos - boss_hitbox_pos
                    min_dist = player.radius + current_boss.radius
                    dist_sq = diff.length_squared()

                    if dist_sq < min_dist * min_dist:
                        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
                        push_dir = diff / dist if dist_sq > 0 else pygame.math.Vector2(0, 1)
                        overlap = min_dist - dist

                        player.pos += push_dir * overlap
                        player.clamp_to_arena()

                        new_diff = player.pos - boss_hitbox_pos
                        if new_diff.length_squared() < min_dist * min_dist:
                            current_boss.pos -= push_dir * overlap

                            current_boss.pos.x = max(
                                ARENA_MARGIN_X + current_boss.radius,
                                min(VIRTUAL_WIDTH - ARENA_MARGIN_X - current_boss.radius, current_boss.pos.x)
                            )
                            current_boss.pos.y = max(
                                ARENA_MARGIN_Y + current_boss.radius,
                                min(VIRTUAL_HEIGHT - ARENA_MARGIN_Y - current_boss.radius, current_boss.pos.y)
                            )

                        if player.iframe <= 0:
                            if player.take_damage():
                                game_over = True

                for p in player_projectiles[:]:
                    if (p.pos - boss_hitbox_pos).length() < (p.size + current_boss.radius):
                        current_boss.hp -= p.damage
                        current_boss.hit_flash = 0.07  # CONTORNO BRANCO RAPIDINHO QUANDO LEVA TIRO
                        spawn_burst(p.pos.x, p.pos.y, FUR_COLORS, 6, speed=3.0, life=0.3, size=5)
                        if p in player_projectiles:
                            player_projectiles.remove(p)

                        if current_boss.hp <= 0:
                            # EXPLOSÃO DO BOSS
                            bcol = BOSS_COLORS.get(type(current_boss), (255, 255, 255))
                            bpos = current_boss.get_hitbox_pos()
                            spawn_burst(bpos.x, bpos.y, [bcol, (255, 255, 255), (255, 220, 120)], 60,
                                        speed=7.0, life=0.9, size=8)
                            add_shake(10, 0.45)
                            current_boss = None
                            enemy_projectiles.clear()
                            player.set_mood("feliz", MOOD_HAPPY_TIME)  # BOSS DERROTADO

                            if len(items_queue) > 0:
                                active_capsule = UpgradeCapsule(items_queue.pop(0))
                            break

            if active_capsule and not active_capsule.collected:
                if (player.pos - active_capsule.pos).length() < (player.radius + 20):
                    active_capsule.collected = True
                    player.set_mood("feliz", MOOD_HAPPY_TIME)  # PEGOU POWERUP
                    spawn_burst(active_capsule.pos.x, active_capsule.pos.y - 20, [ITEM_COLOR, (255, 255, 255)], 24,
                                speed=4.5, life=0.6, size=5)

                    if active_capsule.item_type == "CADENCE":
                        player.fire_delay = max(0.06, player.fire_delay - 0.06)
                    elif active_capsule.item_type == "AMPLIFIER":
                        player.damage += 3.0
                    elif active_capsule.item_type == "EXTENDER":
                        player.proj_range += 140
                        player.proj_size += 3

                    if len(boss_queue) > 0:
                        current_boss = boss_queue.pop(0)
                        wave_number += 1
                        active_capsule = None
                    else:
                        victory = True

            for p in player_projectiles[:]:
                p.update(dt)
                if (
                    p.range_remaining <= 0
                    or p.pos.x < ARENA_MARGIN_X
                    or p.pos.x > VIRTUAL_WIDTH - ARENA_MARGIN_X
                    or p.pos.y < ARENA_MARGIN_Y
                    or p.pos.y > VIRTUAL_HEIGHT - ARENA_MARGIN_Y
                ):
                    if p in player_projectiles:
                        player_projectiles.remove(p)

            for p in enemy_projectiles[:]:
                p.update(dt)

                if player.iframe <= 0 and (p.pos - player.pos).length() < (p.size + player.radius):
                    died = player.take_damage()  # iframe de 0.5 ta dentro do take_damage
                    if p in enemy_projectiles:
                        enemy_projectiles.remove(p)
                    if died:
                        game_over = True
                    continue

                if (
                    p.range_remaining <= 0
                    or p.pos.x < ARENA_MARGIN_X
                    or p.pos.x > VIRTUAL_WIDTH - ARENA_MARGIN_X
                    or p.pos.y < ARENA_MARGIN_Y
                    or p.pos.y > VIRTUAL_HEIGHT - ARENA_MARGIN_Y
                ):
                    if p in enemy_projectiles:
                        enemy_projectiles.remove(p)

        #RENDERIZA O CANVA(NAO ESQUECE DNV)
        canvas.fill(BG_COLOR)

        pygame.draw.rect(canvas, ARENA_COLOR, (ARENA_MARGIN_X, ARENA_MARGIN_Y, ARENA_WIDTH, ARENA_HEIGHT))
        for x in range(ARENA_MARGIN_X, VIRTUAL_WIDTH - ARENA_MARGIN_X, 50):
            pygame.draw.line(canvas, GRID_LINE, (x, ARENA_MARGIN_Y), (x, VIRTUAL_HEIGHT - ARENA_MARGIN_Y))
        for y in range(ARENA_MARGIN_Y, VIRTUAL_HEIGHT - ARENA_MARGIN_Y, 50):
            pygame.draw.line(canvas, GRID_LINE, (ARENA_MARGIN_X, y), (VIRTUAL_WIDTH - ARENA_MARGIN_X, y))

        pygame.draw.rect(canvas, WALL_COLOR, (ARENA_MARGIN_X, ARENA_MARGIN_Y, ARENA_WIDTH, ARENA_HEIGHT), width=3)

        if active_capsule:
            active_capsule.draw(canvas, font_small)

        for prt in particles:
            prt.draw(canvas)
        for p in player_projectiles:
            p.draw(canvas)
        for p in enemy_projectiles:
            p.draw(canvas)

        if current_boss:
            current_boss.draw(canvas)
            if getattr(current_boss, "hit_flash", 0) > 0:
                hb = current_boss.get_hitbox_pos()
                pygame.draw.circle(canvas, (255, 255, 255), (int(hb.x), int(hb.y)), current_boss.radius + 3, 3)

        if not game_over and not victory:
            player.draw(canvas)

        top_hud = pygame.Rect(0, 0, VIRTUAL_WIDTH, 48)
        pygame.draw.rect(canvas, HUD_BG, top_hud)

        #HP EM BARRINHAS FODINHAS
        for i in range(player.max_hp // 2):
            hx = 20 + (i * 22)
            hy = 24
            if player.hp >= (i + 1) * 2:
                col = PLAYER_COLOR
            elif player.hp == (i * 2) + 1:
                col = (0, 140, 160)
            else:
                col = (30, 40, 50)
            pygame.draw.rect(canvas, col, (hx - 7, hy - 7, 14, 14), border_radius=2)

        #HP DO BOSS EM BARRA SE PÁ TROCAR A COR CONFORME O BOSS MAS SLA PREGUIÇA
        if current_boss:
            bar_w, bar_h = 380, 14
            bar_x = (VIRTUAL_WIDTH - bar_w) // 2
            bar_y = 20
            pct = max(0, current_boss.hp / current_boss.max_hp)
            pygame.draw.rect(canvas, (30, 20, 30), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=3)
            pygame.draw.rect(canvas, BOSS_COLOR_1, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=2)

            boss_txt = font_small.render(f"{current_boss.name} [WAVE {wave_number}/3]", True, (240, 200, 220))
            canvas.blit(boss_txt, (bar_x, bar_y - 15))

        bot_hud = pygame.Rect(0, VIRTUAL_HEIGHT - 40, VIRTUAL_WIDTH, 40)
        pygame.draw.rect(canvas, HUD_BG, bot_hud)
        pygame.draw.line(canvas, WALL_COLOR, (0, VIRTUAL_HEIGHT - 40), (VIRTUAL_WIDTH, VIRTUAL_HEIGHT - 40), 2)

        ctrl_txt = font_small.render("[WASD] Move  |  [←↑↓→/IJKL] Shoot  |  [P] Pause  |  [F11] Fullscreen", True,
                                     (160, 180, 200))
        canvas.blit(ctrl_txt, ctrl_txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 20)))

        if is_paused:
            canvas.blit(end_overlay, (0, 0))
            pause_txt = font_large.render("JOGO PAUSADO", True, (0, 240, 255))
            sub_txt = font_small.render("Pressione 'P' ou 'ESC' para continuar", True, (200, 200, 200))
            canvas.blit(pause_txt, pause_txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 20)))
            canvas.blit(sub_txt, sub_txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 25)))

        if game_over or victory:
            canvas.blit(end_overlay, (0, 0))

            if game_over:
                txt = font_large.render("PATÉTICO:BETINHA DEMAIS", True, (255, 50, 80))
                sub = font_small.render("Pressione 'R' para tentar novamente", True, (200, 200, 200))
            else:
                txt = font_large.render("BOSS RUSH FINALIZADO!", True, ITEM_COLOR)
                sub = font_small.render("Pressione 'R' para jogar novamente", True, (200, 200, 200))

            canvas.blit(txt, txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 20)))
            canvas.blit(sub, sub.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 25)))

            # SUPERCAT NA TELA FINAL: TRISTE SE PERDEU, FELIZ SE GANHOU
            end_cat = CAT_SPRITES.get("triste" if game_over else "feliz")
            if end_cat is not None:
                end_cat = pygame.transform.scale(end_cat, (end_cat.get_width() * 2, end_cat.get_height() * 2))
                canvas.blit(end_cat, end_cat.get_rect(center=(VIRTUAL_WIDTH // 2,
                                                       VIRTUAL_HEIGHT // 2 - 130 + int(math.sin(pygame.time.get_ticks() * 0.004) * 6))))

        target_w, target_h = screen.get_size()
        dest_rect = get_scaled_rect(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, target_w, target_h)

        scaled_canvas = pygame.transform.smoothscale(canvas, dest_rect.size)
        screen.fill((0, 0, 0))
        shx, shy = get_shake_offset()
        if shx or shy:
            scale_k = dest_rect.width / VIRTUAL_WIDTH
            dest_rect = dest_rect.move(int(shx * scale_k), int(shy * scale_k))
        screen.blit(scaled_canvas, dest_rect)
        pygame.display.flip()


if __name__ == "__main__":
    main()
    #ARRUMEI A COLISÃO DO PRIMEIRO BOSS, QUANDO ELE PULAVA A HITBOX DE AINDA FICAVA NO LUGAR,
    #ARRUMEI QUE QUANDO ELE PULA EM CIMA DE TU ENQUANTO TU TÁ PERTO DA PAREDE ELE TE JOGAVA OUT OF BOUNDS,
    #FIZ OS DRONES DO SEGUNDO BOSS, A QUANTIDADE MAXIMA DE QUANTOS ELE PODE CRIAR HÁ DE SER DISCUTIDA,
    #FIZ UM BOTÃO DE PAUSE
    #ARRUMEI O PROBLEMA DA RESOLUÇÃO QUANDO TU CLICA F11, TIREI O STRECH, TÁ MELHOR MAS TALVEZ TENHA UM JEITO MELHOR DE FAZER, VOU DAR UMA PESQUISADA
    #NO MAIS É ISSO QUALQUER DUVIDA É SÓ CHAMAR
    #
    #SPRITES DO SUPERCAT:
    #O PLAYER AGORA É O SUPERCAT (PASTA assets/), A HITBOX CONTINUA O CIRCULO DE RAIO 16
    #NORMAL = ESTADO PADRAO, TRISTE = QUANDO TOMA DANO (0.8s), FELIZ = BOSS DERROTADO OU POWERUP PEGO (1.2s)
    #TRISTE TEM PRIORIDADE SOBRE O FELIZ
    #TODO DANO NO PLAYER AGORA PASSA PELO player.take_damage() (ANTES TAVA REPETIDO EM 3 LUGARES)
    #O GATO VIRA PRO LADO QUE TA ANDANDO/ATIRANDO
    #OS TIROS DO PLAYER VIRARAM BOLAS DE PELO (CRESCEM COM O EXTENDER)
    #TELA DE GAME OVER MOSTRA O GATO TRISTE E A DE VITORIA O FELIZ
    #TAMANHO DO GATO: MUDAR CAT_SCALE LÁ EM CIMA
    #SE A PASTA assets/ SUMIR O JOGO VOLTA A DESENHAR OS CIRCULOS
    #
    #ANIMAÇÕES (ATUALIZAÇÃO 2):
    #BUG ARRUMADO: ANDAR PRA UM LADO E ATIRAR PRO OUTRO FAZIA O GATO FICAR VIRANDO TODO FRAME.
    #  AGORA O LADO DO TIRO TEM PRIORIDADE (E SEGURA POR SHOOT_FACE_HOLD DEPOIS DE SOLTAR), O MOVIMENTO SÓ VIRA QUANDO NAO TA ATIRANDO PRO LADO
    #VIRADA ANIMADA (ACHATA E DESACHATA) EM VEZ DE TROCAR SECO
    #GATO FLUTUA (SOBE/DESCE), INCLINA QUANDO SOBE/DESCE, TEM SOMBRA EMBAIXO
    #TRANCO E PUFF DE PELO QUANDO ATIRA, A BOLA SAI DA FRENTE DO GATO
    #PULINHO QUANDO MUDA A EXPRESSÃO, CORAÇÕEZINHOS QUANDO TA FELIZ
    #DANO: PISCA VERMELHO (ANTES SUMIA), SOLTA FAISCA E A TELA TREME
    #BOLAS DE PELO GIRAM E DEIXAM RASTRO, SOLTAM PELINHO QUANDO ACERTAM
    #BOSS PISCA CONTORNO BRANCO QUANDO LEVA TIRO, EXPLODE QUANDO MORRE (+ TREMIDA)
    #DRONE EXPLODE QUANDO MORRE, CAPSULA SOLTA BRILHO QUANDO PEGA
    #TODOS OS AJUSTES (VELOCIDADE, ALTURA, TEMPO) TAO NAS CONSTANTES LÁ EM CIMA (TURN_TIME, BOB_AMP, TILT_MAX...)
    #PARTICULAS TEM LIMITE (MAX_PARTICLES) PRA NAO PESAR
    #
    #POWERUPS COM IMAGEM: +FIRE RATE = RAÇÃO, +DAMAGE = ERVA DE GATO, +RANGE & SIZE = 3 BOLAS DE PELO
    #O ITEM FLUTUA EM CIMA DO PEDESTAL COM BRILHO PULSANDO E BRILHINHOS (SE A IMAGEM SUMIR VOLTA O CIRCULO)