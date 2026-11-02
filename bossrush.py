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
BOSS_COLOR_4 = (24, 208, 188)      # VERDE-ÁGUA (SOMBRA, O GATO NINJA)
BOSS_COLOR_5 = (110, 170, 255)     # AZUL-CÉU (MADAME ASPIRINA)
ENEMY_BULLET = (255, 50, 80)
HUD_BG = (10, 12, 18)
ITEM_COLOR = (0, 255, 160)

# SPRITES DO SUPERCAT (PASTA assets/ AO LADO DESTE ARQUIVO)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
# ======================= MODO DE TESTE =======================
# PRA TESTAR OS CHEFES SEM SUAR: MULTIPLICA O DANO DAS BOLAS DE PELO DO SUPERCAT.
# APERTE F1 DURANTE O JOGO (OU NO MENU) PRA LIGAR/DESLIGAR. AQUI EMBAIXO DÁ PRA DEIXAR LIGADO DE SAÍDA.
MODO_TESTE = False          # True = O JOGO JÁ ABRE COM O MODO DE TESTE LIGADO
DANO_MODO_TESTE = 10        # MULTIPLICADOR DO DANO NO MODO DE TESTE (10 = DEZ VEZES MAIS FORTE)
TEST_MODE = {"on": MODO_TESTE, "toast": 0.0}


def player_hit_damage(p):
    # DANO DE UMA BOLA DE PELO, JÁ COM O MODO DE TESTE APLICADO
    return p.damage * (DANO_MODO_TESTE if TEST_MODE["on"] else 1)


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

# ======================= SPRITES DOS INIMIGOS (FEITOS NO ASEPRITE) =======================
# CADA PNG É UMA TIRA HORIZONTAL COM OS FRAMES LADO A LADO (EXPORTADA DO .aseprite EM assets/aseprite/)
BOSS_SCALE = 1.5  # MESMA ESCALA DO GATO, PRA O PIXEL TER O MESMO TAMANHO NA TELA


def load_strip(name, frame_w, scale=BOSS_SCALE):
    # DEVOLVE (FRAMES, FRAMES_BRANCOS) OU None SE O ARQUIVO NAO EXISTIR
    sheet = load_sprite(name)
    if sheet is None:
        return None
    w, h = sheet.get_size()
    frames, flashes = [], []
    for i in range(w // frame_w):
        f = sheet.subsurface((i * frame_w, 0, frame_w, h)).copy()
        f = pygame.transform.scale(f, (round(frame_w * scale), round(h * scale)))
        frames.append(f)
        # VERSAO TODA BRANCA PRA PISCAR QUANDO LEVA TIRO
        flashes.append(pygame.mask.from_surface(f).to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)))
    return frames, flashes


PRISM_SPRITES = load_strip("boss_prisma.png", 60)      # 0-3 PARADO, 4 PULO, 5-8 FÚRIA, 9 PULO FÚRIA, 10 DERROTA
ORBITAL_SPRITES = load_strip("boss_orbital.png", 56)   # 0-3 PARADO, 4-7 FÚRIA, 8 DERROTA
DRONE_SPRITES = load_strip("drone.png", 28)            # RATOS DE CORDA: 0-3 ORBITANDO, 4-7 ATACANDO (OLHANDO PRA ESQUERDA)
DRONE_SPRITES_RIGHT = [pygame.transform.flip(f, True, False) for f in DRONE_SPRITES[0]] if DRONE_SPRITES else []
CORE_SPRITES = load_strip("boss_nucleo.png", 72)       # 0-3 PULSO, 4 PISCANDO, 5-8 FÚRIA, 9 DERROTA
NINJA_SPRITES = load_strip("boss_ninja.png", 60)       # 0-3 PARADO, 4 ATAQUE, 5-8 FÚRIA, 9 ATAQUE FÚRIA, 10 DERROTA
DUCHESS_SPRITES = load_strip("boss_duquesa.png", 76)   # 0-3 PARADO, 4-7 ASPIRANDO, 8-11 FÚRIA, 12 DERROTA


# ANIMAÇÃO DE VOO DO SUPERCAT: 4 FRAMES POR EXPRESSÃO (CAPA ONDULANDO + PATINHAS)
# supercat_voando.png = normal(4) + feliz(4) + triste(4), FEITO NO ASEPRITE (assets/aseprite/supercat.aseprite)
FLY_FRAME_TIME = 0.1
_fly = load_strip("supercat_voando.png", 50, CAT_SCALE)
CAT_FLY = {}
CAT_FLY_LEFT = {}
if _fly:
    for i, mood in enumerate(("normal", "feliz", "triste")):
        CAT_FLY[mood] = _fly[0][i * 4:(i + 1) * 4]
        CAT_FLY_LEFT[mood] = [pygame.transform.flip(f, True, False) for f in CAT_FLY[mood]]

# TIROS DOS CHEFES
SHOT_FISH = load_strip("tiro_peixe.png", 15)      # FODÂO: ESPINHA DE PEIXE
SHOT_LASER = load_strip("tiro_laser.png", 13)     # FODINHA: PONTINHO DE LASER (2 FRAMES)
SHOT_YARN = load_strip("tiro_novelo.png", 14)     # RAINHA MIAUGIA: NOVELO DE LÃ
SHOT_SHURIKEN = load_strip("tiro_shuriken.png", 15)  # SHURIKEN BUMERANGUE (DISPONÍVEL, SEM USO NO MOMENTO)
SHOT_CLAW = load_strip("tiro_garra.png", 14)         # SOMBRA: GARRA EM MEIA-LUA
SHOT_DUST = load_strip("tiro_poeira.png", 16)        # MADAME ASPIRINA: BOLA DE POEIRA (SE DIVIDE)
_shot_cache = {}
SHOT_ANGLE_STEPS = 24


def get_rotated_shot(kind, angle):
    strip = {"peixe": SHOT_FISH, "novelo": SHOT_YARN, "shuriken": SHOT_SHURIKEN, "garra": SHOT_CLAW,
             "poeira": SHOT_DUST, "poeirinha": SHOT_DUST}.get(kind)
    if not strip:
        return None
    step = int(round(angle / (360 / SHOT_ANGLE_STEPS))) % SHOT_ANGLE_STEPS
    key = (kind, step)
    if key not in _shot_cache:
        base = strip[0][0]
        if kind == "poeirinha":  # POEIRINHA = BOLA DE POEIRA PEQUENA
            base = pygame.transform.scale(base, (base.get_width() * 3 // 5, base.get_height() * 3 // 5))
        _shot_cache[key] = pygame.transform.rotate(base, step * (360 / SHOT_ANGLE_STEPS))
    return _shot_cache[key]


# CENÁRIOS (480x320 NO ASEPRITE, AMPLIADOS 2x PRA TELA)
def load_arena(name):
    img = load_sprite(name)
    if img is None:
        return None
    return pygame.transform.scale(img, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT))


ARENAS = [load_arena("cenario_ringue.png"), load_arena("cenario_laboratorio.png"), load_arena("cenario_trono.png"),
          load_arena("cenario_telhado.png"), load_arena("cenario_sala.png")]


def blit_center(surface, strip, index, x, y, flash=False):
    frames, flashes = strip
    img = (flashes if flash else frames)[index]
    surface.blit(img, img.get_rect(center=(int(x), int(y))))
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
    update_fx(dt)
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
# ======================= DIREÇÃO DE ARTE: FONTE, LUZ, EFEITOS, HUD =======================
FONT_DIR = os.path.join(ASSETS_DIR, "fontes")


def pixel_font(size, bold=True):
    # SILKSCREEN (OFL) É TODA EM PIXEL; USAR EM MÚLTIPLOS DE 8 PRA FICAR NÍTIDA
    path = os.path.join(FONT_DIR, "Silkscreen-Bold.ttf" if bold else "Silkscreen-Regular.ttf")
    try:
        return pygame.font.Font(path, size)
    except (FileNotFoundError, OSError):
        return pygame.font.SysFont("consolas", size, bold=True)


def load_plain_strip(name, frame_w, scale):
    strip = load_strip(name, frame_w, scale)
    return strip[0] if strip else None


# ---------- BRILHO (LUZ ADITIVA) ----------
_glow_cache = {}


def get_glow(radius, color, strength=1.0):
    # DEGRADÊ REDONDO EM DEGRAUS (CARA DE PIXEL ART), SOMADO NA TELA COM BLEND_ADD
    key = (int(radius), color, round(strength, 2))
    if key not in _glow_cache:
        r = int(radius)
        surf = pygame.Surface((r * 2, r * 2))
        surf.fill((0, 0, 0))
        steps = 6 if r < 60 else 14   # LUZ GRANDE COM MAIS DEGRAUS PRA NAO VIRAR "ALVO"
        for i in range(steps):
            k = (i + 1) / steps
            rr = int(r * (1.0 - i / steps))
            a = (k ** 2) * 0.55 * strength
            c = tuple(min(255, int(ch * a)) for ch in color)
            pygame.draw.circle(surf, c, (r, r), rr)
        _glow_cache[key] = surf
    return _glow_cache[key]


def add_glow(surface, x, y, radius, color, strength=1.0):
    g = get_glow(radius, color, strength)
    surface.blit(g, g.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_ADD)


# ---------- EFEITOS ANIMADOS (FEITOS NO ASEPRITE) ----------
FX_FRAMES = {
    "poeira": (load_plain_strip("fx_poeira.png", 16, 3), 0.06),
    "explosao": (load_plain_strip("fx_explosao.png", 32, 3), 0.06),
    "explosao_p": (load_plain_strip("fx_explosao.png", 32, 1.5), 0.05),
    "impacto": (load_plain_strip("fx_impacto.png", 13, 2), 0.045),
    "brilho": (load_plain_strip("fx_brilho.png", 7, 2), 0.08),
}
effects = []


class FX:
    def __init__(self, kind, x, y, vx=0.0, vy=0.0, delay=0.0, flip=False):
        self.frames, self.ft = FX_FRAMES.get(kind, (None, 0.1))
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vx, vy)
        self.t = -delay
        self.flip = flip
        self.done = self.frames is None

    def update(self, dt):
        self.t += dt
        if self.t > 0:
            self.pos += self.vel * (dt * 60.0)
            if int(self.t / self.ft) >= len(self.frames):
                self.done = True

    def draw(self, surface):
        if self.done or self.t < 0:
            return
        img = self.frames[min(len(self.frames) - 1, int(self.t / self.ft))]
        if self.flip:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, img.get_rect(center=(int(self.pos.x), int(self.pos.y))))


def spawn_fx(kind, x, y, **kw):
    if len(effects) < 120:
        effects.append(FX(kind, x, y, **kw))


def spawn_dust(x, y, count=2, spread=26):
    # POEIRA PROS DOIS LADOS (ATERRISSAGEM, PULO)
    for i in range(count):
        side = -1 if i % 2 == 0 else 1
        spawn_fx("poeira", x + side * random.uniform(spread * 0.4, spread), y + random.uniform(-4, 4),
                 vx=side * random.uniform(0.6, 1.2), vy=-0.15, flip=(side < 0))


def spawn_big_explosion(x, y):
    spawn_fx("explosao", x, y)
    for i in range(5):
        a = random.uniform(0, math.tau)
        d = random.uniform(25, 60)
        spawn_fx("explosao_p", x + math.cos(a) * d, y + math.sin(a) * d, delay=0.05 + i * 0.07)


def update_fx(dt):
    for e in effects[:]:
        e.update(dt)
        if e.done:
            effects.remove(e)


# ---------- HUD ----------
HUD_TOP = load_sprite("hud_topo.png", 2)
HUD_BOTTOM = load_sprite("hud_base.png", 2)
HUD_BOSS_BAR = load_sprite("hud_barra_chefe.png", 2)
HUD_PORTRAIT = load_sprite("hud_retrato.png", 2)
HUD_PORTRAIT_BG = load_sprite("hud_retrato_fundo.png", 2)
HUD_HEARTS = load_plain_strip("hud_coracao.png", 11, 2)        # CHEIO, MEIO, VAZIO
HUD_WAVES = load_plain_strip("hud_onda.png", 9, 2)             # FUTURA, ATUAL, VENCIDA
CUSHION = load_sprite("prop_almofada.png", 2)
CANDLE = load_plain_strip("prop_vela.png", 10, 2)


def _portraits(strip, crop, n_normal, n_rage):
    # RECORTA O ROSTO DE CADA CHEFE DOS SPRITES JÁ NA ESCALA DO JOGO (1.5x), 24x24 PIXELS DE ARTE = 36x36
    if not strip:
        return None
    cx, cy = crop
    out = []
    for f in (n_normal, n_rage):
        frame = strip[0][f]
        out.append(frame.subsurface((int(cx * BOSS_SCALE), int(cy * BOSS_SCALE), 36, 36)).copy())
    return out


BOSS_PORTRAITS = {
    "BossPrism": _portraits(PRISM_SPRITES, (18, 11), 0, 5),
    "BossOrbital": _portraits(ORBITAL_SPRITES, (16, 10), 0, 4),
    "BossCore": _portraits(CORE_SPRITES, (24, 13), 0, 5),
    "BossNinja": _portraits(NINJA_SPRITES, (18, 10), 0, 5),
    "BossDuchess": _portraits(DUCHESS_SPRITES, (26, 10), 0, 8),
}


# ---------- AMBIENTE DAS ARENAS (LUZ E OBJETOS ANIMADOS) ----------
def _make_vignette():
    v = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
    cx, cy = VIRTUAL_WIDTH / 2, VIRTUAL_HEIGHT / 2
    steps = 10
    for i in range(steps):
        k = i / steps
        a = int(150 * (1.0 - k) ** 2.2)
        w = int(VIRTUAL_WIDTH * (1.25 - k * 0.55))
        h = int(VIRTUAL_HEIGHT * (1.25 - k * 0.55))
        layer = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        layer.fill((6, 4, 14, a))
        pygame.draw.ellipse(layer, (0, 0, 0, 0), (cx - w / 2, cy - h / 2, w, h))
        v.blit(layer, (0, 0))
    return v


VIGNETTE = _make_vignette()
LAB_LIGHTS = [(x, y, random.Random(x * 7 + y).choice([(255, 60, 70), (255, 190, 40), (90, 230, 140)]),
               random.Random(x + y * 3).uniform(0, math.tau))
              for (x, y) in [(20, 120), (20, 300), (20, 470), (940, 160), (940, 360), (940, 520),
                             (150, 20), (330, 20), (610, 20), (800, 20), (220, 620), (720, 620)]]
LAB_TUBES = [(80, 12), (140, 12), (800, 12), (860, 12), (80, 600), (860, 600)]
CANDLES = [(22, y) for y in (110, 230, 350, 470)] + [(938, y) for y in (110, 230, 350, 470)]


def draw_arena_ambience(surface, wave, t, enraged=False):
    # 1 = RINGUE, 2 = LABORATÓRIO, 3 = SALÃO DO TRONO
    if wave == 1:
        # DOIS HOLOFOTES VARRENDO A LONA
        for i, col in enumerate([(255, 120, 190), (200, 200, 255)]):
            sx = VIRTUAL_WIDTH / 2 + math.sin(t * (0.45 + i * 0.2) + i * 2) * 300
            sy = VIRTUAL_HEIGHT / 2 + math.cos(t * (0.35 + i * 0.15) + i) * 150
            add_glow(surface, sx, sy, 130, col, 0.22)
        # FLASHES DE CÂMERA NA PLATEIA
        if random.random() < 0.06:
            side = random.choice(["l", "r", "b"])
            if side == "l":
                fx, fy = random.uniform(6, 36), random.uniform(60, 580)
            elif side == "r":
                fx, fy = random.uniform(924, 954), random.uniform(60, 580)
            else:
                fx, fy = random.uniform(60, 900), random.uniform(596, 600)
            add_glow(surface, fx, fy, 22, (255, 255, 255), 1.0)
            spawn_fx("brilho", fx, fy)
    elif wave == 2:
        for (x, y, col, ph) in LAB_LIGHTS:
            k = (math.sin(t * 3.0 + ph) + 1) / 2
            if k > 0.35:
                add_glow(surface, x, y, 26, col, 0.6 * k)
                pygame.draw.rect(surface, col, (x - 2, y - 2, 4, 4))
        for (x, y) in LAB_TUBES:
            add_glow(surface, x + 8, y + 18, 26, (60, 220, 120), 0.45)
            if random.random() < 0.08 and len(particles) < MAX_PARTICLES:
                particles.append(Particle(x + random.uniform(4, 12), y + 24, 0, -0.5, 0.5, (190, 255, 210), 2))
        # ALARME VERMELHO GIRANDO NA FASE 2
        if enraged:
            ax = VIRTUAL_WIDTH / 2 + math.cos(t * 4) * 420
            add_glow(surface, ax, 24, 90, (255, 30, 40), 0.5)
    elif wave == 3:
        for i, (x, y) in enumerate(CANDLES):
            flick = 0.75 + 0.25 * math.sin(t * 9 + i * 1.7) * math.sin(t * 5.3 + i)
            add_glow(surface, x, y - 12, 46, (255, 170, 70), 0.55 * flick)
            if CANDLE:
                img = CANDLE[int(t / 0.11 + i) % len(CANDLE)]
                surface.blit(img, img.get_rect(midbottom=(x, y + 10)))
        # POEIRINHA DOURADA FLUTUANDO SOBRE O TAPETE
        if random.random() < 0.05:
            spawn_fx("brilho", random.uniform(420, 540), random.uniform(80, 560))
    elif wave == 4:
        # LUA E ESTRELAS PISCANDO EM VOLTA DO TELHADO
        add_glow(surface, 900, 40, 140, (150, 170, 255), 0.35)
        if random.random() < 0.12:
            side = random.random()
            if side < 0.5:
                sx, sy = random.choice([random.uniform(4, 34), random.uniform(926, 956)]), random.uniform(50, 590)
            else:
                sx, sy = random.uniform(40, 920), random.choice([random.uniform(50, 56), random.uniform(596, 600)])
            spawn_fx("brilho", sx, sy)
        # NUVEM PASSANDO NA FRENTE DA LUA (SOMBRA SUAVE ANDANDO NO TELHADO)
        cx = (t * 40) % (VIRTUAL_WIDTH + 400) - 200
        shade = pygame.Surface((260, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(shade, (0, 0, 20, 45), shade.get_rect())
        surface.blit(shade, (cx - 130, 200 + math.sin(t * 0.3) * 80))
    elif wave == 5:
        # LUZ DO SOL ENTRANDO PELA JANELA E POEIRINHA FLUTUANDO NA LUZ
        for i in range(4):
            add_glow(surface, 480 - 60 + i * 40, 90 + i * 90, 110 - i * 8, (255, 220, 160), 0.22)
        if random.random() < 0.1:
            spawn_fx("brilho", random.uniform(380, 640), random.uniform(70, 420))


# ---------- TEXTO COM DEGRADÊ (LOGO) ----------
def gradient_text(font, text, top, bottom):
    base = font.render(text, False, (255, 255, 255)).convert_alpha()
    w, h = base.get_size()
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    band = 4  # DEGRAUS DE 4PX: DEGRADÊ "EM FAIXAS", ESTILO PIXEL
    for y in range(0, h, band):
        k = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3))
        pygame.draw.rect(grad, c, (0, y, w, band))
    grad.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return grad


class Projectile:
    def __init__(self, x, y, vel_x, vel_y, damage, range_limit, color=PLAYER_BULLET, size=6, is_hairball=False, kind=None, homing=None, homing_time=0.0,
                 owner=None, return_after=0.0, split_time=0.0):
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
        self.kind = kind  # "peixe", "laser" OU "novelo" (TIROS DOS CHEFES)
        self.homing = homing          # ALVO (VETOR DA POSIÇÃO DO GATO) PROS NOVELOS TELEGUIADOS
        self.homing_time = homing_time
        self.owner = owner                # SHURIKEN BUMERANGUE VOLTA PRA ESSE CHEFE
        self.return_after = return_after
        self.split_time = split_time      # BOLA DE POEIRA SE DIVIDE DEPOIS DESSE TEMPO
        self.age = 0.0

    def update(self, dt):
        if self.homing is not None and self.homing_time > 0:
            # VAI CURVANDO EM DIREÇÃO AO GATO ATÉ ACABAR O TEMPO
            self.homing_time -= dt
            to = self.homing - self.pos
            if to.length_squared() > 1:
                spd = max(3.6, self.vel.length())
                self.vel = self.vel.lerp(to.normalize() * spd, min(1.0, dt * 2.6))
            if random.random() < 0.4 and len(particles) < MAX_PARTICLES:
                particles.append(Particle(self.pos.x, self.pos.y, 0, 0, 0.25, (230, 150, 255), 3))
        step = self.vel * (dt * 60.0)
        self.pos += step
        self.range_remaining -= step.length()
        self.age += dt
        if self.kind == "novelo":
            self.angle = (self.angle + self.spin * 0.6 * dt) % 360
        elif self.kind == "shuriken":
            self.angle = (self.angle + 900 * dt) % 360
            if self.owner is not None:
                if self.age > self.return_after:
                    # VOLTA PRA MÃO DO NINJA
                    to = self.owner.get_hitbox_pos() - self.pos
                    if to.length() < 26 or self.owner.dying > 0:
                        self.range_remaining = 0
                    elif to.length_squared() > 1:
                        self.vel = self.vel.lerp(to.normalize() * 7.0, min(1.0, dt * 5.0))
                        self.range_remaining = max(self.range_remaining, 60)
                elif self.age > self.return_after * 0.5:
                    self.vel *= math.pow(0.9, dt * 60.0)
        elif self.kind in ("poeira", "poeirinha"):
            self.angle = (self.angle + self.spin * 0.25 * dt) % 360
        elif self.kind == "laser":
            # RASTRINHO VERMELHO DO LASER
            self.trail_timer -= dt
            if self.trail_timer <= 0 and len(particles) < MAX_PARTICLES:
                self.trail_timer = 0.04
                particles.append(Particle(self.pos.x, self.pos.y, 0, 0, 0.15, (255, 60, 70), 3))
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
            add_glow(surface, self.pos.x, self.pos.y, self.size * 2 + 6, (255, 150, 60), 0.35)
            img = get_hairball(self.size, self.angle)
            if img is not None:
                surface.blit(img, img.get_rect(center=(int(self.pos.x), int(self.pos.y))))
                return
        img = None
        glow = {"peixe": (14, (255, 90, 150), 0.6), "laser": (18, (255, 40, 50), 1.0),
                "novelo": (16, (190, 80, 255), 0.7), "shuriken": (14, (24, 208, 188), 0.7), "garra": (16, (24, 208, 188), 0.75),
                "poeira": (18, (140, 170, 230), 0.4), "poeirinha": (10, (140, 170, 230), 0.35)}.get(self.kind)
        if glow:
            add_glow(surface, self.pos.x, self.pos.y, *glow)
        if self.kind in ("peixe", "garra"):
            # A CABEÇA DO PEIXE / A CURVA DA GARRA APONTA PRA ONDE O TIRO VAI
            img = get_rotated_shot(self.kind, -math.degrees(math.atan2(self.vel.y, self.vel.x)))
        elif self.kind in ("novelo", "shuriken", "poeira", "poeirinha"):
            img = get_rotated_shot(self.kind, self.angle)
        elif self.kind == "laser" and SHOT_LASER:
            img = SHOT_LASER[0][int(self.age / 0.08) % 2]
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
        fly = (CAT_FLY_LEFT if draw_left else CAT_FLY).get(self.mood)
        if fly:
            # CAPA BATE MAIS RAPIDO QUANDO ELE TA SE MEXENDO
            speed = 1.6 if self.vel.length_squared() > 0.5 else 1.0
            base = fly[int(self.anim_time * speed / FLY_FRAME_TIME) % len(fly)]

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

def draw_shadow(surface, x, y, w, alpha=80):
    # SOMBRINHA OVAL NO CHÃO (DÁ PESO PROS PERSONAGENS)
    w = max(6, int(w))
    h = max(4, w // 4)
    sh = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, alpha), sh.get_rect())
    surface.blit(sh, sh.get_rect(center=(int(x), int(y))))


class BossBase:
    # TUDO QUE OS 3 CHEFES TÊM EM COMUM: ENTRADA, FÚRIA (METADE DA VIDA), DERROTA E "SQUASH"
    INTRO_TIME = 1.2     # CAINDO DO CÉU
    LAND_AT = 0.25       # QUANDO FALTA ISSO DA ENTRADA, ELE BATE NO CHÃO
    RAGE_TIME = 1.3      # TRANSFORMAÇÃO DA FASE 2 (NÃO ATACA ENQUANTO ISSO)
    DEATH_TIME = 1.3     # ANIMAÇÃO DE DERROTA ANTES DE EXPLODIR
    COLOR = (255, 255, 255)

    def init_base(self):
        self.intro = self.INTRO_TIME
        self.phase = 1
        self.rage_timer = 0.0
        self.dying = 0.0
        self.dead = False
        self.hit_flash = 0.0
        self.squash = 0.0
        self.anim = 0.0
        self.alpha = 255
        self.display_hp = self.hp   # BARRA DE VIDA "ATRASADA" (RASTRO BRANCO)
        self.banner = 0.0           # TEMPO DO AVISO "FÚRIA!" NA TELA

    @property
    def invulnerable(self):
        return self.intro > 0 or self.dying > 0

    @property
    def enraged(self):
        return self.phase == 2

    def on_hit(self):
        self.hit_flash = 0.07
        self.squash = max(self.squash, 0.35)

    def start_dying(self):
        self.dying = self.DEATH_TIME
        self.hp = 0
        add_shake(6, 0.3)

    def on_rage(self):
        pass

    def base_update(self, dt):
        # DEVOLVE True SE O CHEFE PODE AGIR NESSE FRAME
        self.anim += dt
        self.squash = max(0.0, self.squash - dt * 3.5)
        self.display_hp += (self.hp - self.display_hp) * min(1.0, dt * 3.0)
        self.banner = max(0.0, self.banner - dt)
        pos = self.get_hitbox_pos()

        if self.dying > 0:
            self.dying -= dt
            # EXPLOSÕEZINHAS ENQUANTO ELE CAMBALEIA
            if random.random() < 0.35:
                spawn_burst(pos.x + random.uniform(-30, 30), pos.y + random.uniform(-30, 30),
                            [self.COLOR, (255, 255, 255), (255, 220, 120)], 6, speed=3.0, life=0.35, size=5)
            if random.random() < 0.12:
                spawn_fx("explosao_p", pos.x + random.uniform(-36, 36), pos.y + random.uniform(-36, 30))
            if self.dying <= 0:
                self.dead = True
            return False

        if self.intro > 0:
            before = self.intro
            self.intro -= dt
            if before > self.LAND_AT >= self.intro:
                # ATERRISSOU: POEIRA + TREMIDA + ACHATADA
                add_shake(9, 0.3)
                self.squash = 1.0
                spawn_burst(self.pos.x, self.pos.y + self.radius * 0.8, [(120, 110, 130), (180, 170, 190)], 10,
                            speed=4.0, life=0.45, size=6, spread=math.pi, angle=math.pi)
                spawn_dust(self.pos.x, self.pos.y + self.radius * 0.8, 4, 55)
            return False

        if self.phase == 1 and self.hp <= self.max_hp / 2:
            self.phase = 2
            self.rage_timer = self.RAGE_TIME
            self.banner = 1.6
            add_shake(10, 0.7)
            spawn_burst(pos.x, pos.y, [self.COLOR, (255, 255, 255), (255, 60, 60)], 50, speed=6.0, life=0.8, size=7)
            self.on_rage()

        if self.rage_timer > 0:
            self.rage_timer -= dt
            if random.random() < 0.6 and len(particles) < MAX_PARTICLES:
                a = random.uniform(0, math.tau)
                particles.append(Particle(pos.x + math.cos(a) * 50, pos.y + math.sin(a) * 50,
                                          -math.cos(a) * 3, -math.sin(a) * 3, 0.3, random.choice([self.COLOR, (255, 80, 80)]), 5))
            return False
        return True

    def intro_offset(self):
        if self.intro <= self.LAND_AT:
            return 0.0
        t = (self.intro - self.LAND_AT) / (self.INTRO_TIME - self.LAND_AT)
        return -460.0 * t * t

    def draw_ground_shadow(self, surface, extra_w=0):
        k = 1.0
        if self.intro > self.LAND_AT:
            k = 1.0 - (self.intro - self.LAND_AT) / (self.INTRO_TIME - self.LAND_AT)
        draw_shadow(surface, self.pos.x, self.pos.y + self.radius * 0.95, (self.radius * 1.7 + extra_w) * max(0.2, k),
                    int(90 * max(0.2, k) * self.alpha / 255))

    def blit_boss(self, surface, strip, frame, x, y):
        frames, flashes = strip
        white = self.hit_flash > 0 or (self.rage_timer > 0 and int(self.rage_timer * 14) % 2 == 0)
        img = flashes[frame] if white else frames[frame]
        w0, h0 = img.get_size()
        sx = 1.0 + 0.16 * self.squash
        sy = 1.0 - 0.16 * self.squash
        # RESPIRAÇÃO (ESTICA E ENCOLHE DE LEVE)
        breath = math.sin(self.anim * (7.0 if self.enraged else 4.0)) * 0.025
        sx -= breath
        sy += breath
        y += self.intro_offset()
        if self.rage_timer > 0:
            x += random.uniform(-3, 3)
            y += random.uniform(-2, 2)
            grow = 1.0 + 0.12 * math.sin((1.0 - self.rage_timer / self.RAGE_TIME) * math.pi)
            sx *= grow
            sy *= grow
        if self.dying > 0:
            k = self.dying / self.DEATH_TIME
            x += random.uniform(-4, 4) * (1.0 - k)
            if k < 0.3:
                s = max(0.05, k / 0.3)
                sx *= 1.0 + (1.0 - s) * 0.5
                sy *= s
        if abs(sx - 1.0) > 0.01 or abs(sy - 1.0) > 0.01:
            img = pygame.transform.scale(img, (max(1, int(w0 * sx)), max(1, int(h0 * sy))))
        if self.alpha < 255:
            img = img.copy()
            img.set_alpha(self.alpha)
        # ANCORADO NO "PÉ" PRA O SQUASH PARECER PESO DE VERDADE
        surface.blit(img, img.get_rect(midbottom=(int(x), int(y + h0 / 2))))


# ======================= 1) FODÂO =======================
#OS BOSSES SEM CRIATIVIDADE PENSAR É DIFICIL(ODEIO TODOS) (AGORA SÃO GATOS VILÕES)
class BossPrism(BossBase):
    COLOR = BOSS_COLOR_1
    # FRAMES DO boss_prisma.png
    F_IDLE, F_JUMP, F_RAGE, F_RAGE_JUMP, F_DEFEAT = 0, 4, 5, 9, 10

    def __init__(self):
        self.name = "PATADÃO"
        self.title = "O LUTADOR MASCARADO"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 200)
        self.radius = 42
        self.hp = 280
        self.max_hp = 280
        self.init_base()

        self.timer = 0.0
        self.action_timer = 0.0
        self.state = "idle"          # idle / crouch / air / spin
        self.state_timer = 0.0
        self.is_airborne = False
        self.jump_y_offset = 0
        self.jump_target = pygame.math.Vector2(self.pos)
        self.combo_left = 0
        self.spin_angle = 0.0
        self.shot_timer = 0.0

    def get_hitbox_pos(self):
        return pygame.math.Vector2(self.pos.x, self.pos.y - self.jump_y_offset)

    def fan(self, player_pos, enemy_projectiles, count):
        dir_to_p = player_pos - self.pos
        if dir_to_p.length_squared() == 0:
            return
        base_angle = math.atan2(dir_to_p.y, dir_to_p.x)
        for _ in range(count):
            spread = random.uniform(-0.45, 0.45)
            spd = random.uniform(3.5, 6.2)
            enemy_projectiles.append(
                Projectile(self.pos.x, self.pos.y, math.cos(base_angle + spread) * spd,
                           math.sin(base_angle + spread) * spd, 1, 380, ENEMY_BULLET, 5, kind="peixe"))
        self.squash = 0.5

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        if not self.base_update(dt):
            return
        self.action_timer += dt
        self.state_timer += dt

        if self.state == "idle":
            interval = 1.5 if self.enraged else 2.5
            if self.action_timer >= interval:
                self.action_timer = 0.0
                r = random.random()
                if not self.enraged:
                    if r < 0.5:
                        self.fan(player_pos, enemy_projectiles, 8)
                    else:
                        self.start_crouch(1)
                else:
                    # FASE 2: LEQUE DUPLO, COMBO DE 3 PULOS OU FURACÃO DE ESPINHAS
                    if r < 0.33:
                        self.fan(player_pos, enemy_projectiles, 12)
                        self.pending_fan = 0.35
                    elif r < 0.66:
                        self.start_crouch(3)
                    else:
                        self.state = "spin"
                        self.state_timer = 0.0
                        self.spin_angle = random.uniform(0, math.tau)
            # SEGUNDO LEQUE DA FASE 2
            if getattr(self, "pending_fan", 0) > 0:
                self.pending_fan -= dt
                if self.pending_fan <= 0:
                    self.fan(player_pos, enemy_projectiles, 10)

        elif self.state == "crouch":
            # ANTECIPAÇÃO: AGACHA ANTES DE PULAR
            self.squash = max(self.squash, 0.8)
            if self.state_timer >= (0.16 if self.enraged else 0.28):
                self.state = "air"
                self.state_timer = 0.0
                self.is_airborne = True
                self.jump_target = pygame.math.Vector2(player_pos)
                spawn_dust(self.pos.x, self.pos.y + 34, 2, 30)

        elif self.state == "air":
            dur = 0.62 if self.enraged else 0.9
            jump_progress = min(1.0, self.state_timer / dur)
            self.jump_y_offset = math.sin(jump_progress * math.pi) * (130 if self.enraged else 160)
            self.pos += (self.jump_target - self.pos) * (min(1.0, (0.09 if self.enraged else 0.06) * dt * 60.0))
            if jump_progress >= 1.0:
                self.land(enemy_projectiles)

        elif self.state == "spin":
            # FURACÃO DE ESPINHAS: GIRA E SOLTA PEIXE EM ESPIRAL (2 BRAÇOS)
            charge = 0.4
            if self.state_timer > charge:
                self.spin_angle += 4.2 * dt
                self.shot_timer -= dt
                if self.shot_timer <= 0:
                    self.shot_timer = 0.07
                    for arm in range(2):
                        a = self.spin_angle + arm * math.pi
                        enemy_projectiles.append(
                            Projectile(self.pos.x, self.pos.y, math.cos(a) * 4.2, math.sin(a) * 4.2, 1, 420,
                                       ENEMY_BULLET, 5, kind="peixe"))
            if self.state_timer > charge + 1.8:
                self.state = "idle"
                self.action_timer = 0.0

        self.clamp()

    def start_crouch(self, jumps):
        self.combo_left = jumps
        self.state = "crouch"
        self.state_timer = 0.0

    def land(self, enemy_projectiles):
        self.is_airborne = False
        self.jump_y_offset = 0
        self.squash = 1.0
        add_shake(8 if self.enraged else 6, 0.25)
        spawn_burst(self.pos.x, self.pos.y + 30, [(120, 110, 130), (180, 170, 190)], 8, speed=4.5,
                    life=0.45, size=6, spread=math.pi, angle=math.pi)
        spawn_dust(self.pos.x, self.pos.y + 32, 4, 50)
        n = 12 if self.enraged else 8
        off = random.uniform(0, math.tau)
        for i in range(n):
            a = off + i * (math.tau / n)
            enemy_projectiles.append(
                Projectile(self.pos.x, self.pos.y, math.cos(a) * 4, math.sin(a) * 4, 1, 280, ENEMY_BULLET, 5, kind="peixe"))
        self.combo_left -= 1
        if self.combo_left > 0:
            self.state = "crouch"
        else:
            self.state = "idle"
            self.action_timer = 0.0
        self.state_timer = 0.0

    def clamp(self):
        self.pos.x = max(ARENA_MARGIN_X + self.radius, min(VIRTUAL_WIDTH - ARENA_MARGIN_X - self.radius, self.pos.x))
        self.pos.y = max(ARENA_MARGIN_Y + self.radius, min(VIRTUAL_HEIGHT - ARENA_MARGIN_Y - self.radius, self.pos.y))

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y - self.jump_y_offset)
        # SOMBRA: ENCOLHE QUANTO MAIS ALTO ELE TÁ
        if self.is_airborne:
            k = 1.0 - self.jump_y_offset / 200
            draw_shadow(surface, self.pos.x, self.pos.y + 36, 70 * k, 110)
        else:
            self.draw_ground_shadow(surface)

        if PRISM_SPRITES:
            if self.dying > 0:
                frame = self.F_DEFEAT
            elif self.is_airborne or self.state == "crouch":
                frame = self.F_RAGE_JUMP if self.enraged else self.F_JUMP
            else:
                speed = 0.07 if self.state == "spin" else (0.09 if self.enraged else 0.14)
                frame = (self.F_RAGE if self.enraged else self.F_IDLE) + int(self.timer / speed) % 4
            if self.state == "spin" and self.state_timer > 0.4 and self.dying <= 0:
                # BALANÇA DE UM LADO PRO OUTRO ENQUANTO GIRA
                x += int(math.sin(self.timer * 30) * 4)
            self.blit_boss(surface, PRISM_SPRITES, frame, x, y)
            return

        pts = []
        for i in range(8):
            ang = i * (math.tau / 8) + (self.timer * 1.2)
            pts.append((x + math.cos(ang) * self.radius, y + math.sin(ang) * self.radius))
        pygame.draw.polygon(surface, BOSS_COLOR_1, pts, 3)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 8)


# ======================= 2) FODINHA + RATOS-ROBÔ =======================
class OrbitalDrone: #FINALMENTE OS DRONES ESTÃO FUNCIONANDO ADEUS BETINHA (AGORA SÃO RATOS DE CORDA)
    def __init__(self, boss_pos, fast=False):
        self.pos = pygame.math.Vector2(boss_pos)
        self.vel = pygame.math.Vector2(0, 0)
        self.radius = 10
        self.hp = 12
        self.max_hp = 12
        self.angle = random.uniform(0, math.tau)
        self.orbit_dist = 65
        self.is_attacking = False
        self.attack_timer = random.uniform(2.0, 4.0)
        self.fast = fast                 # FASE 2: RATOS MAIS RÁPIDOS
        self.age = 0.0
        self.facing_right = False
        self.last_x = self.pos.x

    def update(self, boss_pos, player_pos, dt):
        self.attack_timer -= dt
        self.age += dt

        if not self.is_attacking:
            # FICA ORBITANDO EM STAND BY SE NÃO TIVER ATACANDO
            self.angle += (2.8 if self.fast else 2.0) * dt
            target_x = boss_pos.x + math.cos(self.angle) * self.orbit_dist
            target_y = boss_pos.y + math.sin(self.angle) * self.orbit_dist
            target = pygame.math.Vector2(target_x, target_y)
            self.pos += (target - self.pos) * 0.15

            if self.attack_timer <= 0:
                self.is_attacking = True
                self.attack_timer = 3.5  #TIMER DO 'ATAQUE'
        else:
            dir_to_player = (player_pos - self.pos)
            top = 4.6 if self.fast else 3.8
            if dir_to_player.length_squared() > 0:
                self.vel += dir_to_player.normalize() * 0.4
                if self.vel.length() > top:
                    self.vel = self.vel.normalize() * top #MOVE EM DIREÇÃO DO PLAYER
            self.pos += self.vel * (dt * 60.0)
            # POEIRINHA DAS RODINHAS
            if random.random() < 0.3 and len(particles) < MAX_PARTICLES:
                particles.append(Particle(self.pos.x, self.pos.y + 10, 0, 0, 0.2, (150, 150, 170), 3))

            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_timer = random.uniform(2.2, 3.6) if self.fast else random.uniform(3.0, 5.0)

        # VIRA PRO LADO QUE TÁ ANDANDO
        dx = self.pos.x - self.last_x
        if abs(dx) > 0.3:
            self.facing_right = dx > 0
        self.last_x = self.pos.x

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        if DRONE_SPRITES:
            t = pygame.time.get_ticks() / 1000
            frame = (4 + int(t / 0.05) % 4) if self.is_attacking else int(t / 0.08 + self.angle) % 4
            img = (DRONE_SPRITES_RIGHT if self.facing_right else DRONE_SPRITES[0])[frame]
            # SURGE "INFLANDO" QUANDO NASCE
            if self.age < 0.25:
                k = max(0.1, self.age / 0.25)
                img = pygame.transform.scale(img, (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k))))
            draw_shadow(surface, x, y + 17, 30, 80)
            surface.blit(img, img.get_rect(center=(x, y + int(math.sin(t * 12 + self.angle) * 1.5))))
            return
        color = (255, 210, 50) if self.is_attacking else BOSS_COLOR_2
        pygame.draw.circle(surface, color, (x, y), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 3)


class BossOrbital(BossBase):
    COLOR = BOSS_COLOR_2
    F_IDLE, F_RAGE, F_DEFEAT = 0, 4, 8

    def __init__(self):
        self.name = "DR. MIAUSTEIN"  # (ERA FODINHA) CIENTISTA MALUCO DO LASER
        self.title = "O GÊNIO DO LASER"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 200)
        self.radius = 38
        self.hp = 360
        self.max_hp = 360
        self.init_base()
        self.timer = 0.0
        self.spawn_timer = 0.0
        self.burst_timer = 0.0
        self.drones = []
        self.max_drones = 4
        # VARREDURA DE LASER (FASE 2)
        self.sweep_timer = 0.0
        self.sweep_state = None      # None / "mira" / "fogo"
        self.sweep_t = 0.0
        self.sweep_angle = 0.0
        self.sweep_shot = 0.0

    def get_hitbox_pos(self):
        return self.pos

    @property
    def minions(self):
        return self.drones

    def on_rage(self):
        self.max_drones = 6
        for d in self.drones:
            d.fast = True

    def start_dying(self):
        super().start_dying()
        for d in self.drones:
            spawn_burst(d.pos.x, d.pos.y, [BOSS_COLOR_2, (255, 230, 120), (255, 255, 255)], 12, speed=4, life=0.4, size=5)
            spawn_fx("explosao_p", d.pos.x, d.pos.y)
        self.drones.clear()

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        can_act = self.base_update(dt)
        if self.dying > 0 or self.intro > 0:
            return
        for drone in self.drones[:]:
            drone.update(self.pos, player_pos, dt)
        if not can_act:
            return
        self.spawn_timer += dt
        self.burst_timer += dt

        # PARADO ENQUANTO FAZ A VARREDURA, SE NÃO FICA FLUTUANDO
        if self.sweep_state is None:
            self.pos.x += math.sin(self.timer * 1.2) * (2.0 * dt * 60.0)
            self.pos.y += math.cos(self.timer * 1.8) * (1.2 * dt * 60.0)
            self.pos.x = max(ARENA_MARGIN_X + 60, min(VIRTUAL_WIDTH - ARENA_MARGIN_X - 60, self.pos.x))
            self.pos.y = max(ARENA_MARGIN_Y + 60, min(VIRTUAL_HEIGHT - ARENA_MARGIN_Y - 80, self.pos.y))

        spawn_every = 1.6 if self.enraged else 2.2
        if self.spawn_timer >= spawn_every and len(self.drones) < self.max_drones:
            self.spawn_timer = 0.0
            self.drones.append(OrbitalDrone(self.pos, fast=self.enraged))

        burst_every = 1.4 if self.enraged else 2.0
        if self.sweep_state is None and self.burst_timer >= burst_every:
            self.burst_timer = 0.0
            n = 10 if self.enraged else 6
            for i in range(n):
                a = (self.timer * 6.0) + (i * math.tau / n)
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.8, math.sin(a) * 3.8, 1, 320, BOSS_COLOR_2, 5, kind="laser")
                )
            self.squash = 0.4

        # FASE 2: VARREDURA DE LASER EM 3 BRAÇOS (COM AVISO ANTES)
        if self.enraged:
            if self.sweep_state is None:
                self.sweep_timer += dt
                if self.sweep_timer >= 5.5:
                    self.sweep_timer = 0.0
                    self.sweep_state = "mira"
                    self.sweep_t = 0.0
                    self.sweep_angle = math.atan2(player_pos.y - self.pos.y, player_pos.x - self.pos.x) + math.pi / 3
            else:
                self.sweep_t += dt
                if self.sweep_state == "mira" and self.sweep_t >= 0.8:
                    self.sweep_state = "fogo"
                    self.sweep_t = 0.0
                    add_shake(4, 0.2)
                elif self.sweep_state == "fogo":
                    self.sweep_angle += 1.5 * dt
                    self.sweep_shot -= dt
                    if self.sweep_shot <= 0:
                        self.sweep_shot = 0.055
                        for arm in range(3):
                            a = self.sweep_angle + arm * (math.tau / 3)
                            enemy_projectiles.append(
                                Projectile(self.pos.x + math.cos(a) * 30, self.pos.y + math.sin(a) * 30,
                                           math.cos(a) * 5.2, math.sin(a) * 5.2, 1, 520, BOSS_COLOR_2, 5, kind="laser"))
                    if self.sweep_t >= 2.2:
                        self.sweep_state = None
                        self.burst_timer = 0.0

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        # A CÁPSULA FLUTUA: SOMBRA PULSA COM A ALTURA
        hover = math.sin(self.anim * 3.0) * 4
        self.draw_ground_shadow(surface, extra_w=-hover * 2)

        # AVISO DA VARREDURA: LINHAS VERMELHAS PISCANDO
        if self.sweep_state == "mira" and int(self.sweep_t * 12) % 2 == 0:
            for arm in range(3):
                a = self.sweep_angle + arm * (math.tau / 3)
                pygame.draw.line(surface, (255, 60, 70), (x, y), (x + math.cos(a) * 900, y + math.sin(a) * 900), 2)

        if ORBITAL_SPRITES:
            if self.dying > 0:
                frame = self.F_DEFEAT
            else:
                frame = (self.F_RAGE if self.enraged else self.F_IDLE) + int(self.timer / (0.08 if self.enraged else 0.12)) % 4
            # O CORPO DESENHADO É UM POUCO MAIS BAIXO QUE O CENTRO (POR CAUSA DA ANTENA)
            self.blit_boss(surface, ORBITAL_SPRITES, frame, x, y - 3 + hover)
        else:
            pygame.draw.circle(surface, BOSS_COLOR_2, (x, y), self.radius, 3)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), 10)

        for drone in self.drones:
            drone.draw(surface)


# ======================= 3) PODER FEMININO =======================
#AMO AS MULHERES
class BossCore(BossBase):
    COLOR = BOSS_COLOR_3
    F_IDLE, F_BLINK, F_RAGE, F_DEFEAT = 0, 4, 5, 9

    def __init__(self):
        self.name = "RAINHA MIAUGIA"  # (ERA PODER FEMININO) MIAU + MAGIA
        self.title = "A FEITICEIRA DA CAIXA"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 40)
        self.radius = 48
        self.hp = 480
        self.max_hp = 480
        self.init_base()
        self.timer = 0.0
        self.radial_timer = 0.0
        self.aimed_timer = 0.0
        self.radial_count = 0
        # TELETRANSPORTE (FASE 2)
        self.tp_timer = 0.0
        self.tp_state = None          # None / "sumindo" / "aparecendo"
        self.tp_t = 0.0

    def get_hitbox_pos(self):
        return self.pos

    def sparkle(self, n=16):
        for _ in range(5):
            spawn_fx("brilho", self.pos.x + random.uniform(-50, 50), self.pos.y + random.uniform(-50, 40),
                     delay=random.uniform(0, 0.2))
        spawn_burst(self.pos.x, self.pos.y, [BOSS_COLOR_3, (255, 200, 255), (255, 230, 120)], n,
                    speed=3.5, life=0.5, size=4)

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        if not self.base_update(dt):
            return

        # FASE 2: SOME E APARECE EM OUTRO LUGAR DA ARENA
        if self.enraged:
            if self.tp_state is None:
                self.tp_timer += dt
                if self.tp_timer >= 4.5:
                    self.tp_timer = 0.0
                    self.tp_state = "sumindo"
                    self.tp_t = 0.0
                    self.sparkle(24)
            else:
                self.tp_t += dt
                if self.tp_state == "sumindo":
                    self.alpha = int(255 * max(0.0, 1.0 - self.tp_t / 0.35))
                    if self.tp_t >= 0.35:
                        for _ in range(20):
                            nx = random.uniform(ARENA_MARGIN_X + 90, VIRTUAL_WIDTH - ARENA_MARGIN_X - 90)
                            ny = random.uniform(ARENA_MARGIN_Y + 90, VIRTUAL_HEIGHT - ARENA_MARGIN_Y - 110)
                            if (pygame.math.Vector2(nx, ny) - player_pos).length() > 230:
                                break
                        self.pos.update(nx, ny)
                        self.tp_state = "aparecendo"
                        self.tp_t = 0.0
                        self.sparkle(24)
                else:
                    self.alpha = int(255 * min(1.0, self.tp_t / 0.35))
                    if self.tp_t >= 0.35:
                        self.alpha = 255
                        self.tp_state = None
                        self.squash = 0.8
                return  # NÃO ATIRA ENQUANTO TELETRANSPORTA

        self.radial_timer += dt
        self.aimed_timer += dt

        radial_every = 1.7 if self.enraged else 1.5
        if self.radial_timer >= radial_every:
            self.radial_timer = 0.0
            self.radial_count += 1
            n = 16 if self.enraged else 12
            off = (math.pi / n) if (self.enraged and self.radial_count % 2) else 0.0
            for i in range(n):
                a = off + i * (math.tau / n)
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.8, math.sin(a) * 3.8, 1, 400, BOSS_COLOR_3, 6, kind="novelo")
                )
            self.squash = 0.5

        aimed_every = 2.6 if self.enraged else 2.16
        if self.aimed_timer >= aimed_every:
            self.aimed_timer = 0.0
            dir_to_p = player_pos - self.pos
            if dir_to_p.length_squared() == 0:
                return
            base_a = math.atan2(dir_to_p.y, dir_to_p.x)
            if self.enraged:
                # NOVELOS TELEGUIADOS: SAEM ABERTOS E VÃO CURVANDO ATÉ O GATO
                for spread in (-1.0, 0.0, 1.0):
                    vx = math.cos(base_a + spread) * 3.6
                    vy = math.sin(base_a + spread) * 3.6
                    enemy_projectiles.append(
                        Projectile(self.pos.x, self.pos.y, vx, vy, 1, 650, BOSS_COLOR_3, 6, kind="novelo",
                                   homing=player_pos, homing_time=1.4))
            else:
                for spread in (-0.15, 0, 0.15):
                    vx = math.cos(base_a + spread) * 5.0
                    vy = math.sin(base_a + spread) * 5.0
                    enemy_projectiles.append(
                        Projectile(self.pos.x, self.pos.y, vx, vy, 1, 400, BOSS_COLOR_3, 6, kind="novelo")
                    )

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        self.draw_ground_shadow(surface, extra_w=10)

        if CORE_SPRITES:
            # PULSO NO MESMO RITMO DO CODIGO ANTIGO; PISCA O OLHO A CADA ~3s
            pulse = (math.sin(self.timer * (10.0 if self.enraged else 7.2)) + 1) / 2   # 0..1
            frame = [0, 1, 2][round(pulse * 2)]
            if self.dying > 0:
                frame = self.F_DEFEAT
            elif self.enraged:
                frame = self.F_RAGE + frame
            elif self.timer % 3.0 > 2.85:
                frame = self.F_BLINK
            self.blit_boss(surface, CORE_SPRITES, frame, x, y)
            return

        r = int(self.radius + math.sin(self.timer * 7.2) * 4)
        pygame.draw.rect(surface, BOSS_COLOR_3, (x - r, y - r, r * 2, r * 2), width=3, border_radius=6)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 12)



# ======================= 4) SOMBRA, O GATO NINJA =======================
def _shadow_frames(strip):
    # VERSÃO "SOMBRA" DOS FRAMES (CLONES E RASTRO DA INVESTIDA)
    if not strip:
        return None
    out = []
    for f in strip[0]:
        c = f.copy()
        c.fill((70, 60, 120), special_flags=pygame.BLEND_RGB_MULT)
        c.fill((0, 40, 40), special_flags=pygame.BLEND_RGB_ADD)
        out.append(c)
    return out


NINJA_SHADOW = _shadow_frames(NINJA_SPRITES)


class BossNinja(BossBase):
    """SOMBRA, O GATO NINJA (dinâmica do bossrushcats.py).

    FASE 1 (igual ao arquivo de referência):
      VISÍVEL  3.2s: persegue o gato devagar e a cada 0.95s lança 3 GARRAS em leque.
                     Só nesse estado ele leva dano e machuca no contato.
      SUMINDO  0.45s: vai ficando transparente.
      ESCONDIDO 0.9s: escolhe um ponto a ~170px do gato (o mais longe entre 6 sorteios)
                     e mostra os OLHOS BRILHANDO lá como aviso; reaparece soltando um ANEL de 8 garras.

    FASE 2 (FÚRIA, adaptada da fase 1):
      tudo mais rápido, leque de 5 garras, anel de 12, um par de OLHOS FALSOS de isca
      (que também solta garras) e às vezes ele some DUAS vezes seguidas.
    """
    COLOR = BOSS_COLOR_4
    F_IDLE, F_ATK, F_RAGE, F_RAGE_ATK, F_DEFEAT = 0, 4, 5, 9, 10

    def __init__(self):
        self.name = "SOMBRA"
        self.title = "O GATO NINJA"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 190)
        self.radius = 36
        self.hp = 520
        self.max_hp = 520
        self.init_base()
        self.timer = 0.0
        self.state = "VISIVEL"     # VISIVEL / SUMINDO / ESCONDIDO
        self.state_t = 0.0
        self.fire_t = 0.0
        self.atk_pose = 0.0        # TEMPO MOSTRANDO A POSE DE GARRA
        self.target = pygame.math.Vector2(self.pos)
        self.decoy = None          # OLHOS FALSOS (FASE 2)
        self.visible_time = 3.2    # MUDA NA FASE 2 / NO "SUMIÇO DUPLO"
        self.echo = []             # SOMBRA QUE FICA PARA TRÁS QUANDO ELE SOME

    # ---- parâmetros por fase ----
    def p(self, normal, furia):
        return furia if self.enraged else normal

    @property
    def minions(self):
        return []

    @property
    def invulnerable(self):
        # SÓ LEVA DANO (E SÓ MACHUCA NO CONTATO) QUANDO ESTÁ VISÍVEL
        return self.intro > 0 or self.dying > 0 or self.state != "VISIVEL"

    def get_hitbox_pos(self):
        return self.pos

    def start_dying(self):
        super().start_dying()
        self.state = "VISIVEL"
        self.alpha = 255
        self.decoy = None

    def keep_in_arena(self, v, r):
        v.x = max(ARENA_MARGIN_X + r, min(VIRTUAL_WIDTH - ARENA_MARGIN_X - r, v.x))
        v.y = max(ARENA_MARGIN_Y + r + 10, min(VIRTUAL_HEIGHT - ARENA_MARGIN_Y - r - 20, v.y))

    def pick_target(self, player_pos, avoid=None):
        # 6 PONTOS EM VOLTA DO GATO (~170px); FICA COM O MAIS LONGE DELE (E DA ISCA, SE HOUVER)
        best, best_d = None, -1.0
        for _ in range(6):
            a = random.uniform(0, math.tau)
            t = pygame.math.Vector2(player_pos) + pygame.math.Vector2(math.cos(a), math.sin(a)) * 170
            self.keep_in_arena(t, self.radius + 5)
            d = (t - player_pos).length()
            if avoid is not None:
                d = min(d, (t - avoid).length())
            if d > best_d:
                best, best_d = t, d
        return best

    def claws(self, shots, origin, base, spreads, speed, rng):
        for s in spreads:
            shots.append(Projectile(origin.x, origin.y, math.cos(base + s) * speed, math.sin(base + s) * speed,
                                    1, rng, BOSS_COLOR_4, 6, kind="garra"))

    def ring(self, shots, origin, n, speed, rng):
        off = random.uniform(0, math.tau)
        for i in range(n):
            a = off + i * math.tau / n
            shots.append(Projectile(origin.x, origin.y, math.cos(a) * speed, math.sin(a) * speed,
                                    1, rng, BOSS_COLOR_4, 6, kind="garra"))

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        self.atk_pose = max(0.0, self.atk_pose - dt)
        for e in self.echo[:]:
            e[2] -= dt * 2.0
            if e[2] <= 0:
                self.echo.remove(e)
        if not self.base_update(dt):
            return
        self.state_t += dt

        if self.state == "VISIVEL":
            self.alpha = 255
            # PERSEGUE DEVAGAR
            d = player_pos - self.pos
            if d.length_squared() > 1:
                self.pos += d.normalize() * self.p(0.9, 1.3) * (dt * 60.0)
            self.keep_in_arena(self.pos, self.radius)
            # GARRAS EM LEQUE
            self.fire_t += dt
            if self.fire_t >= self.p(0.95, 0.7):
                self.fire_t = 0.0
                d = player_pos - self.pos
                base = math.atan2(d.y, d.x) if d.length_squared() > 0 else math.pi / 2
                spreads = (-0.22, 0.0, 0.22) if not self.enraged else (-0.44, -0.22, 0.0, 0.22, 0.44)
                self.claws(enemy_projectiles, self.pos, base, spreads, self.p(6.5, 7.0), 520)
                self.atk_pose = 0.2
                self.squash = 0.3
            if self.state_t >= self.visible_time:
                self.state, self.state_t = "SUMINDO", 0.0
                self.echo.append([self.pos.x, self.pos.y, 1.0])
                spawn_fx("poeira", self.pos.x, self.pos.y + 10)

        elif self.state == "SUMINDO":
            fade = self.p(0.45, 0.3)
            self.alpha = int(255 * max(0.0, 1.0 - self.state_t / fade))
            if self.state_t >= fade:
                self.state, self.state_t = "ESCONDIDO", 0.0
                self.alpha = 0
                self.target = self.pick_target(player_pos)
                # FÚRIA: UM PAR DE OLHOS FALSOS EM OUTRO LUGAR
                self.decoy = self.pick_target(player_pos, avoid=self.target) if self.enraged else None

        else:  # ESCONDIDO
            self.alpha = 0
            if self.state_t >= self.p(0.9, 0.75):
                self.pos = pygame.math.Vector2(self.target)
                self.state, self.state_t = "VISIVEL", 0.0
                self.fire_t = 0.0
                self.ring(enemy_projectiles, self.pos, self.p(8, 12), 5.0, 380)
                spawn_fx("poeira", self.pos.x, self.pos.y + 10)
                self.squash = 0.8
                self.atk_pose = 0.3
                if self.decoy is not None:
                    # A ISCA TAMBÉM ESTOURA EM GARRAS (MAS NÃO TEM CORPO)
                    self.ring(enemy_projectiles, self.decoy, 6, 4.2, 300)
                    spawn_fx("poeira", self.decoy.x, self.decoy.y)
                    self.decoy = None
                # FÚRIA: 40% DE CHANCE DE SUMIR DE NOVO LOGO EM SEGUIDA
                if self.enraged and random.random() < 0.4:
                    self.visible_time = 0.7
                else:
                    self.visible_time = self.p(3.2, 2.4)

    def draw_eyes(self, surface, pos, k):
        # OLHOS BRILHANDO ONDE ELE VAI REAPARECER (AVISO)
        col = (255, 70, 80) if self.enraged else (255, 230, 60)
        for side in (-1, 1):
            ex, ey = pos.x + side * 10, pos.y - 14
            add_glow(surface, ex, ey, 14, col, 0.3 + 0.7 * k)
            r = pygame.Rect(0, 0, 6, 9)
            r.center = (int(ex), int(ey))
            eye = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.ellipse(eye, (*col, int(70 + 185 * k)), eye.get_rect())
            surface.blit(eye, r)

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        # SOMBRA QUE FICA PARA TRÁS AO SUMIR
        if NINJA_SHADOW:
            for e in self.echo:
                img = NINJA_SHADOW[self.F_RAGE if self.enraged else self.F_IDLE]
                img.set_alpha(int(120 * e[2]))
                surface.blit(img, img.get_rect(center=(int(e[0]), int(e[1] - 6 * (1 - e[2])))))
                img.set_alpha(255)
        if self.state == "ESCONDIDO" and self.dying <= 0:
            k = min(1.0, self.state_t / self.p(0.9, 0.75))
            self.draw_eyes(surface, self.target, k)
            if self.decoy is not None:
                self.draw_eyes(surface, self.decoy, k)
        if self.alpha <= 0:
            return
        if self.alpha > 80:
            self.draw_ground_shadow(surface)
        if NINJA_SPRITES:
            if self.dying > 0:
                frame = self.F_DEFEAT
            elif self.atk_pose > 0:
                frame = self.F_RAGE_ATK if self.enraged else self.F_ATK
            else:
                frame = (self.F_RAGE if self.enraged else self.F_IDLE) + int(self.timer / self.p(0.11, 0.08)) % 4
            self.blit_boss(surface, NINJA_SPRITES, frame, x, y)
        else:
            pygame.draw.circle(surface, BOSS_COLOR_4, (x, y), self.radius, 3)


# ======================= 5) MADAME ASPIRINA, A DUQUESA DA FAXINA =======================
class BossDuchess(BossBase):
    COLOR = BOSS_COLOR_5
    F_IDLE, F_SUCK, F_RAGE, F_DEFEAT = 0, 4, 8, 12

    def __init__(self):
        self.name = "MADAME ASPIRINA"
        self.title = "A DUQUESA DA FAXINA"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 230)
        self.radius = 44
        self.hp = 600
        self.max_hp = 600
        self.init_base()
        self.timer = 0.0
        a = random.choice([0.6, 2.5, 3.8, 5.6])
        self.dir = pygame.math.Vector2(math.cos(a), math.sin(a))
        self.spit_t = 0.0
        self.suck_t = 0.0
        self.suck_state = None     # None / "aviso" / "sugando"
        self.suck_s = 0.0
        self.spiral = 0.0
        self.spiral_shot = 0.0

    def get_hitbox_pos(self):
        return self.pos

    def spit(self, player_pos, shots, n=1, spread=0.0):
        d = player_pos - self.pos
        if d.length_squared() < 1:
            return
        base = math.atan2(d.y, d.x)
        for i in range(n):
            s = (i - (n - 1) / 2) * spread
            shots.append(Projectile(self.pos.x, self.pos.y, math.cos(base + s) * 2.7, math.sin(base + s) * 2.7,
                                    1, 700, BOSS_COLOR_5, 9, kind="poeira", split_time=1.05))
        self.squash = 0.5

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        if not self.base_update(dt):
            return
        speed = 3.3 if self.enraged else 2.2

        if self.suck_state is None:
            # PASSEIA COMO ROBÔ ASPIRADOR: RETO ATÉ BATER NA PAREDE
            self.pos += self.dir * speed * (dt * 60.0)
            minx, maxx = ARENA_MARGIN_X + self.radius, VIRTUAL_WIDTH - ARENA_MARGIN_X - self.radius
            miny, maxy = ARENA_MARGIN_Y + self.radius, VIRTUAL_HEIGHT - ARENA_MARGIN_Y - self.radius - 10
            bounced = False
            if self.pos.x < minx or self.pos.x > maxx:
                self.dir.x *= -1
                bounced = True
            if self.pos.y < miny or self.pos.y > maxy:
                self.dir.y *= -1
                bounced = True
            self.pos.x = max(minx, min(maxx, self.pos.x))
            self.pos.y = max(miny, min(maxy, self.pos.y))
            if bounced:
                self.dir = self.dir.rotate(random.uniform(-18, 18))
                self.squash = 0.6
                add_shake(2, 0.1)
                spawn_dust(self.pos.x, self.pos.y + 30, 2, 40)
                if self.enraged:
                    # FASE 2: ESPIRRA POEIRA A CADA BATIDA
                    off = random.uniform(0, math.tau)
                    for i in range(6):
                        a = off + i * math.tau / 6
                        enemy_projectiles.append(Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.2, math.sin(a) * 3.2,
                                                            1, 320, BOSS_COLOR_5, 5, kind="poeirinha"))
            self.spit_t += dt
            if self.spit_t >= (1.6 if self.enraged else 2.3):
                self.spit_t = 0.0
                self.spit(player_pos, enemy_projectiles)
            self.suck_t += dt
            if self.suck_t >= (4.5 if self.enraged else 6.5):
                self.suck_t = 0.0
                self.suck_state, self.suck_s = "aviso", 0.0
        else:
            self.suck_s += dt
            if self.suck_state == "aviso":
                if self.suck_s >= 0.7:
                    self.suck_state, self.suck_s = "sugando", 0.0
            else:
                # ASPIRAÇÃO: PUXA O GATO PRA PERTO (DÁ PRA FUGIR VOANDO CONTRA)
                to = self.pos - player_pos
                d = to.length()
                if d > 1:
                    pull = (1.9 if self.enraged else 1.4) * (0.65 + 0.7 * max(0.0, 1.0 - d / 650))
                    step = to / d * pull * (dt * 60.0)
                    player_pos.x += step.x
                    player_pos.y += step.y
                # PARTÍCULAS DE POEIRA SENDO SUGADAS
                if len(particles) < MAX_PARTICLES:
                    for _ in range(2):
                        a = random.uniform(0, math.tau)
                        r = random.uniform(180, 320)
                        px, py = self.pos.x + math.cos(a) * r, self.pos.y + math.sin(a) * r
                        particles.append(Particle(px, py, -math.cos(a) * r / 18, -math.sin(a) * r / 18, 0.45,
                                                  random.choice([(200, 220, 255), (150, 170, 210), (255, 255, 255)]), 3))
                if self.enraged:
                    self.spiral += 2.6 * dt
                    self.spiral_shot -= dt
                    if self.spiral_shot <= 0:
                        self.spiral_shot = 0.13
                        for arm in range(2):
                            a = self.spiral + arm * math.pi
                            enemy_projectiles.append(Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.0, math.sin(a) * 3.0,
                                                                1, 420, BOSS_COLOR_5, 5, kind="poeirinha"))
                if self.suck_s >= (3.0 if self.enraged else 2.6):
                    # TERMINA CUSPINDO TRÊS BOLAS DE POEIRA
                    self.spit(player_pos, enemy_projectiles, 3, 0.45)
                    self.suck_state = None
                    self.spit_t = 0.0

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        self.draw_ground_shadow(surface, extra_w=24)
        # ANÉIS DE SUCÇÃO SE FECHANDO
        if self.suck_state == "sugando":
            for i in range(3):
                k = 1.0 - ((self.suck_s * 1.5 + i / 3) % 1.0)
                r = int(40 + k * 170)
                pygame.draw.ellipse(surface, (140, 200, 255), (x - r, y + 20 - r * 0.45, r * 2, r * 0.9), 2)
        elif self.suck_state == "aviso" and int(self.suck_s * 12) % 2 == 0:
            pygame.draw.ellipse(surface, (255, 255, 255), (x - 60, y + 6, 120, 54), 2)
        if DUCHESS_SPRITES:
            jitter = random.randint(-1, 1) if self.suck_state == "sugando" else 0
            if self.dying > 0:
                frame = self.F_DEFEAT
            elif self.suck_state is not None:
                frame = self.F_SUCK + int(self.timer / 0.07) % 4
            elif self.enraged:
                frame = self.F_RAGE + int(self.timer / 0.07) % 4
            else:
                frame = self.F_IDLE + int(self.timer / 0.11) % 4
            self.blit_boss(surface, DUCHESS_SPRITES, frame, x + jitter, y - 8)
        else:
            pygame.draw.circle(surface, BOSS_COLOR_5, (x, y), self.radius, 3)


BOSS_COLORS = {BossPrism: BOSS_COLOR_1, BossOrbital: BOSS_COLOR_2, BossCore: BOSS_COLOR_3,
               BossNinja: BOSS_COLOR_4, BossDuchess: BOSS_COLOR_5}

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
    "HEAL": load_item("coracao.png", 34),               # +VIDA       = CORAÇÃO (NOVO, NO MEIO DAS 5 ONDAS)
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
        if CUSHION is not None:
            draw_shadow(surface, x, y + 22, 76, 90)
            surface.blit(CUSHION, CUSHION.get_rect(center=(x, y + 12)))
            if random.random() < 0.04:
                spawn_fx("brilho", x + random.uniform(-30, 30), y + random.uniform(-40, 10))
        else:
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
            txt = font.render("(+FIRE RATE)", False, ITEM_COLOR)
        elif self.item_type == "AMPLIFIER":
            txt = font.render("(+DAMAGE)", False, ITEM_COLOR)
        elif self.item_type == "HEAL":
            txt = font.render("(+VIDA)", False, ITEM_COLOR)
        else:
            txt = font.render("(+RANGE & SIZE)", False, ITEM_COLOR)

        surface.blit(txt, txt.get_rect(center=(x, y + 44)))

def get_scaled_rect(virtual_w, virtual_h, target_w, target_h):
    scale = min(target_w / virtual_w, target_h / virtual_h)
    new_w = int(virtual_w * scale)
    new_h = int(virtual_h * scale)
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    return pygame.Rect(x, y, new_w, new_h)

#MAIN
def draw_text_outline(surface, font, text, color, center, outline=(20, 10, 30), px=3, shadow=True):
    # TEXTO COM CONTORNO GROSSO (ESTILO TÍTULO DE FLIPERAMA)
    base = font.render(text, False, color)
    w, h = base.get_size()
    out = font.render(text, False, outline)
    surf = pygame.Surface((w + px * 2, h + px * 2 + (3 if shadow else 0)), pygame.SRCALPHA)
    if shadow:
        sh = font.render(text, False, (0, 0, 0))
        sh.set_alpha(120)
        surf.blit(sh, (px, px + 3))
    for dx in range(-px, px + 1):
        for dy in range(-px, px + 1):
            if dx * dx + dy * dy <= px * px:
                surf.blit(out, (px + dx, px + dy))
    surf.blit(base, (px, px))
    surface.blit(surf, surf.get_rect(center=center))
    return surf.get_rect(center=center)


MENU_OPTIONS = ["JOGAR", "COMO JOGAR", "SAIR"]


def draw_logo(surface, font, text, center, top, bottom, outline_col):
    fill = gradient_text(font, text, top, bottom)
    out = font.render(text, False, outline_col)
    w, h = fill.get_size()
    px = 4
    logo = pygame.Surface((w + px * 2, h + px * 2 + 6), pygame.SRCALPHA)
    shadow = font.render(text, False, (20, 8, 30))
    for dx in range(-px, px + 1, 2):
        for dy in range(-px, px + 1, 2):
            logo.blit(shadow, (px + dx, px + dy + 6))
    for dx in range(-px, px + 1, 2):
        for dy in range(-px, px + 1, 2):
            logo.blit(out, (px + dx, px + dy))
    logo.blit(fill, (px, px))
    surface.blit(logo, logo.get_rect(center=center))


def draw_menu(surface, fonts, t, selected):
    font_title, font_large, font_mid, font_small = fonts
    # FUNDO: OS 3 CENÁRIOS SE REVEZANDO COM FADE
    idx = int(t / 5) % 3
    nxt = (idx + 1) % 3
    k = (t % 5) / 5
    if ARENAS[idx] is not None:
        surface.blit(ARENAS[idx], (0, 0))
        if k > 0.85 and ARENAS[nxt] is not None:
            over = ARENAS[nxt].copy()
            over.set_alpha(int(255 * (k - 0.85) / 0.15))
            surface.blit(over, (0, 0))
    else:
        surface.fill(BG_COLOR)
    dark = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
    dark.fill((8, 6, 16, 150))
    surface.blit(dark, (0, 0))

    # OS 3 VILÕES NO FUNDO, CADA UM NA SUA ANIMAÇÃO
    villains = [(PRISM_SPRITES, 0, 4, 0.14, 120), (ORBITAL_SPRITES, 0, 4, 0.12, 300), (CORE_SPRITES, 0, 4, 0.12, 480),
                (NINJA_SPRITES, 0, 4, 0.11, 660), (DUCHESS_SPRITES, 0, 4, 0.11, 845)]
    for strip, f0, n, spd, vx in villains:
        if not strip:
            continue
        img = strip[0][f0 + int(t / spd) % n]
        bob = math.sin(t * 2.5 + vx) * 4
        draw_shadow(surface, vx, 574, 90, 90)
        surface.blit(img, img.get_rect(midbottom=(vx, 578 + bob)))

    # LOGO: DEGRADÊ EM FAIXAS + CONTORNO EM BLOCO + SOMBRA (TUDO NÍTIDO, SEM BORRAR)
    bob = int(math.sin(t * 2.2) * 4)
    draw_logo(surface, font_title, "SUPERCAT", (VIRTUAL_WIDTH // 2, 112 + bob),
              (255, 240, 150), (255, 120, 40), (90, 26, 16))
    draw_logo(surface, font_large, "BOSS RUSH", (VIRTUAL_WIDTH // 2, 182 + bob // 2),
              (255, 170, 210), (230, 40, 120), (60, 8, 40))
    if random.random() < 0.08:
        spawn_fx("brilho", VIRTUAL_WIDTH // 2 + random.uniform(-240, 240), 112 + random.uniform(-36, 36))
    for e in effects:
        e.draw(surface)

    # SUPERCAT VOANDO EM OITO PELA TELA
    fly = CAT_FLY.get("normal")
    if fly:
        cx = VIRTUAL_WIDTH // 2 + math.sin(t * 0.9) * 330
        cy = 265 + math.sin(t * 1.8) * 26
        going_left = math.cos(t * 0.9) < 0
        frame = fly[int(t / 0.08) % len(fly)]
        if going_left:
            frame = pygame.transform.flip(frame, True, False)
        frame = pygame.transform.scale(frame, (int(frame.get_width() * 1.4), int(frame.get_height() * 1.4)))
        frame = pygame.transform.rotate(frame, math.cos(t * 1.8) * 8 * (-1 if going_left else 1))
        if random.random() < 0.5 and len(particles) < MAX_PARTICLES:
            particles.append(Particle(cx + (30 if going_left else -30), cy + random.uniform(-10, 10),
                                      (1.5 if going_left else -1.5), 0, 0.35, random.choice(FUR_COLORS), 4))
        surface.blit(frame, frame.get_rect(center=(int(cx), int(cy))))

    # OPÇÕES (A SELECIONADA BALANÇA E GANHA UMA ESPINHA DE PEIXE DE CURSOR)
    for i, opt in enumerate(MENU_OPTIONS):
        y = 318 + i * 42
        sel = (i == selected)
        col = (255, 230, 120) if sel else (190, 180, 210)
        x = VIRTUAL_WIDTH // 2 + (int(math.sin(t * 10) * 3) if sel else 0)
        r = draw_text_outline(surface, font_mid, opt, col, (x, y), outline=(30, 16, 40), px=2)
        if sel:
            fish = get_rotated_shot("peixe", 0)
            if fish is not None:
                fish = pygame.transform.scale(fish, (fish.get_width() * 2 // 1, fish.get_height() * 2 // 1))
                surface.blit(fish, fish.get_rect(midright=(r.left - 14 + int(math.sin(t * 8) * 4), y)))
                fish_l = pygame.transform.flip(fish, True, False)
                surface.blit(fish_l, fish_l.get_rect(midleft=(r.right + 14 - int(math.sin(t * 8) * 4), y)))

    hint = font_small.render("[W/S] ESCOLHER   [ENTER] CONFIRMAR   [F11] TELA CHEIA", False, (170, 170, 200))
    surface.blit(hint, hint.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 22)))


def draw_howto(surface, fonts, t):
    font_title, font_large, font_mid, font_small = fonts
    if ARENAS[0] is not None:
        surface.blit(ARENAS[0], (0, 0))
    else:
        surface.fill(BG_COLOR)
    surface.blit(end_overlay, (0, 0))
    draw_text_outline(surface, font_large, "COMO JOGAR", (255, 178, 64), (VIRTUAL_WIDTH // 2, 70), outline=(110, 30, 20))
    lines = [
        ("WASD", "voar pela arena"),
        ("SETAS / IJKL", "atirar bolas de pelo"),
        ("P / ESC", "pausar"),
        ("M", "menu (no pause e no fim)"),
        ("R", "reiniciar a corrida"),
        ("F11", "tela cheia"),
        ("F1", f"modo de teste (dano x{DANO_MODO_TESTE})"),
    ]
    for i, (k, d) in enumerate(lines):
        y = 120 + i * 28
        kt = font_mid.render(k, False, (255, 230, 120))
        dt_ = font_small.render(d, False, (220, 215, 235))
        surface.blit(kt, kt.get_rect(midright=(VIRTUAL_WIDTH // 2 - 70, y)))
        surface.blit(dt_, dt_.get_rect(midleft=(VIRTUAL_WIDTH // 2 - 50, y + 2)))

    tips = [
        (PRISM_SPRITES, 5, "PATADÃO", "FÚRIA: 3 pulos seguidos + furacão de espinhas"),
        (ORBITAL_SPRITES, 4, "DR. MIAUSTEIN", "FÚRIA: varredura de laser + mais ratos de corda"),
        (CORE_SPRITES, 5, "RAINHA MIAUGIA", "FÚRIA: teletransporte + novelos teleguiados"),
        (NINJA_SPRITES, 5, "SOMBRA", "persegue, garras, some e volta. FÚRIA: olhos falsos"),
        (DUCHESS_SPRITES, 8, "MADAME ASPIRINA", "aspira o gato, poeira se divide. FÚRIA: turbo"),
    ]
    for i, (strip, f, name, desc) in enumerate(tips):
        y = 330 + i * 50
        if strip:
            img = strip[0][f + int(t / 0.1) % 4]
            img = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
            surface.blit(img, img.get_rect(center=(150, y)))
        nt = font_small.render(name, False, BOSS_COLORS_LIST[i])
        surface.blit(nt, (205, y - 16))
        surface.blit(font_small.render(desc, False, (220, 215, 235)), (205, y + 4))

    back = font_small.render("[ESC / ENTER] voltar", False, (170, 170, 200))
    surface.blit(back, back.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 22)))


BOSS_COLORS_LIST = [BOSS_COLOR_1, BOSS_COLOR_2, BOSS_COLOR_3, BOSS_COLOR_4, BOSS_COLOR_5]


TOTAL_WAVES = 5


def draw_test_badge(surface, font_small, font_mid, dt):
    # SELO "MODO TESTE" NO CANTO + AVISO GRANDE QUANDO LIGA/DESLIGA
    if TEST_MODE["on"]:
        txt = font_small.render(f"MODO TESTE  DANO x{DANO_MODO_TESTE}  [F1]", False, (255, 230, 120))
        box = pygame.Rect(56, 54, txt.get_width() + 16, txt.get_height() + 8)
        pygame.draw.rect(surface, (90, 20, 30), box)
        pygame.draw.rect(surface, (255, 90, 90), box, 2)
        surface.blit(txt, (box.x + 8, box.y + 4))
    if TEST_MODE["toast"] > 0:
        TEST_MODE["toast"] = max(0.0, TEST_MODE["toast"] - dt)
        msg = "MODO TESTE LIGADO" if TEST_MODE["on"] else "MODO TESTE DESLIGADO"
        col = (255, 230, 120) if TEST_MODE["on"] else (190, 190, 210)
        draw_text_outline(surface, font_mid, msg, col, (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 90), px=2)


def draw_hud(surface, fonts, player, boss, wave_number, victory):
    font_title, font_large, font_mid, font_small = fonts
    t = pygame.time.get_ticks() / 1000

    # PAINEL DE CIMA
    if HUD_TOP is not None:
        surface.blit(HUD_TOP, (0, 0))
    else:
        pygame.draw.rect(surface, HUD_BG, (0, 0, VIRTUAL_WIDTH, 48))

    # CORAÇÕES (O QUE ACABOU DE PERDER PULSA)
    for i in range(player.max_hp // 2):
        hx, hy = 18 + i * 26, 12
        if HUD_HEARTS:
            if player.hp >= (i + 1) * 2:
                img = HUD_HEARTS[0]
            elif player.hp == i * 2 + 1:
                img = HUD_HEARTS[1]
            else:
                img = HUD_HEARTS[2]
            dy = 0
            if player.hp >= (i + 1) * 2 and player.hp <= 4:
                dy = -2 if int(t * 6 + i) % 2 == 0 else 0   # VIDA BAIXA: CORAÇÕES TREMEM
            if player.iframe > 0 and player.hp in (i * 2, i * 2 + 1) and int(player.iframe * 16) % 2:
                img = pygame.transform.scale(img, (img.get_width() + 4, img.get_height() + 4))
                hx -= 2
                hy -= 2
            surface.blit(img, (hx, hy + dy))

    # ONDAS: 3 PATINHAS (VENCIDA / ATUAL / FUTURA)
    if HUD_WAVES:
        label = font_small.render("ONDA", False, (200, 180, 230))
        surface.blit(label, (VIRTUAL_WIDTH - 236, 15))
        for i in range(TOTAL_WAVES):
            n = i + 1
            if victory or n < wave_number or (n == wave_number and boss is None):
                img = HUD_WAVES[2]
            elif n == wave_number:
                img = HUD_WAVES[1]
            else:
                img = HUD_WAVES[0]
            bob = -2 if (n == wave_number and not victory and int(t * 3) % 2 == 0) else 0
            surface.blit(img, (VIRTUAL_WIDTH - 164 + i * 30, 12 + bob))

    # BARRA DO CHEFE COM RETRATO
    if boss is not None:
        bar_w = 380
        frame_x = (VIRTUAL_WIDTH - 392) // 2
        frame_y = 22
        inner_x, inner_y, inner_h = frame_x + 6, frame_y + 6, 12
        bcol = BOSS_COLORS.get(type(boss), BOSS_COLOR_1)
        pct = max(0.0, boss.hp / boss.max_hp)
        lag = max(0.0, boss.display_hp / boss.max_hp)
        if boss.intro > 0:
            pct = lag = min(1.0, (1.0 - boss.intro / boss.INTRO_TIME) * 1.2)
        if boss.enraged and boss.dying <= 0:
            add_glow(surface, VIRTUAL_WIDTH // 2, frame_y + 12, 200, (255, 30, 40), 0.25 + 0.15 * math.sin(t * 8))
        pygame.draw.rect(surface, (14, 10, 22), (inner_x, inner_y, bar_w, inner_h))
        pygame.draw.rect(surface, (250, 240, 250), (inner_x, inner_y, int(bar_w * lag), inner_h))
        fw = int(bar_w * pct)
        if fw > 0:
            light = tuple(min(255, c + 70) for c in bcol)
            dark = tuple(int(c * 0.6) for c in bcol)
            pygame.draw.rect(surface, bcol, (inner_x, inner_y, fw, inner_h))
            pygame.draw.rect(surface, light, (inner_x, inner_y, fw, 2))
            pygame.draw.rect(surface, dark, (inner_x, inner_y + inner_h - 2, fw, 2))
            # BRILHO CORRENDO NA BARRA
            sx = inner_x + int((t * 160) % (bar_w + 40)) - 20
            if inner_x <= sx < inner_x + fw - 4:
                pygame.draw.rect(surface, (255, 255, 255), (sx, inner_y + 2, 4, inner_h - 4))
        if HUD_BOSS_BAR is not None:
            surface.blit(HUD_BOSS_BAR, (frame_x, frame_y))

        name = boss.name + ("  -  FÚRIA!" if boss.enraged else "")
        col = (255, 120, 130) if boss.enraged else (240, 220, 240)
        txt = font_small.render(name, False, col)
        sh = font_small.render(name, False, (0, 0, 0))
        surface.blit(sh, (frame_x + 2, 5))
        surface.blit(txt, (frame_x, 3))

        portraits = BOSS_PORTRAITS.get(type(boss).__name__)
        px, py = frame_x - 52, 2
        if HUD_PORTRAIT_BG is not None:
            surface.blit(HUD_PORTRAIT_BG, (px + 4, py + 4))
            tint = pygame.Surface((36, 36))
            tint.fill(tuple(int(c * 0.35) for c in bcol))
            surface.blit(tint, (px + 4, py + 4), special_flags=pygame.BLEND_RGB_ADD)
        if portraits:
            img = portraits[1] if boss.enraged else portraits[0]
            jx = random.randint(-1, 1) if (boss.hit_flash > 0 or boss.rage_timer > 0) else 0
            surface.blit(img, (px + 4 + jx, py + 4))
        if HUD_PORTRAIT is not None:
            surface.blit(HUD_PORTRAIT, (px, py))

    # PAINEL DE BAIXO COM OS CONTROLES (TECLA EM AMARELO, AÇÃO EM CINZA)
    if HUD_BOTTOM is not None:
        surface.blit(HUD_BOTTOM, (0, VIRTUAL_HEIGHT - 40))
    else:
        pygame.draw.rect(surface, HUD_BG, (0, VIRTUAL_HEIGHT - 40, VIRTUAL_WIDTH, 40))
    parts = [("WASD", "MOVER"), ("SETAS/IJKL", "ATIRAR"), ("P", "PAUSAR"), ("F11", "TELA CHEIA")]
    surfs = []
    for k, d in parts:
        surfs.append((font_small.render(k, False, (255, 210, 90)), font_small.render(d, False, (170, 160, 200))))
    total = sum(a.get_width() + 8 + b.get_width() for a, b in surfs) + 36 * (len(surfs) - 1)
    x = (VIRTUAL_WIDTH - total) // 2
    for a, b in surfs:
        surface.blit(a, (x, VIRTUAL_HEIGHT - 26))
        x += a.get_width() + 8
        surface.blit(b, (x, VIRTUAL_HEIGHT - 26))
        x += b.get_width() + 36


def main():
    global is_fullscreen, screen

    def reset_game():
        player = PlayerShip(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 120)
        boss_queue = [BossPrism(), BossOrbital(), BossCore(), BossNinja(), BossDuchess()]
        items_queue = ["CADENCE", "AMPLIFIER", "HEAL", "EXTENDER"]
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

    font_title = pixel_font(64)
    font_large = pixel_font(32)
    font_mid = pixel_font(24)
    font_small = pixel_font(16)
    fonts = (font_title, font_large, font_mid, font_small)

    state = "menu"          # menu / howto / game
    menu_sel = 0
    menu_time = 0.0
    fade = 1.0              # ESCURECIDO DE TRANSIÇÃO (1 = PRETO, VAI CLAREANDO)
    end_timer = 0.0         # ANIMAÇÃO DAS TELAS DE FIM
    wave_banner = 1.8       # "ONDA 1 - FODÂO" NO COMEÇO DE CADA LUTA
    wind_timer = 0.0

    def start_game():
        nonlocal player, boss_queue, items_queue, current_boss, active_capsule, player_projectiles
        nonlocal enemy_projectiles, wave_number, game_over, victory, is_paused, fade, end_timer, wave_banner, state
        (player, boss_queue, items_queue, current_boss, active_capsule, player_projectiles, enemy_projectiles,
         wave_number, game_over, victory, is_paused) = reset_game()
        particles.clear()
        effects.clear()
        SHAKE["time"] = 0.0
        fade = 1.0
        end_timer = 0.0
        wave_banner = 1.8
        state = "game"

    def go_menu():
        nonlocal state, fade
        particles.clear()
        effects.clear()
        SHAKE["time"] = 0.0
        state = "menu"
        fade = 1.0

    while True:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1 / 20)  # SE TRAVAR UM POUCO NÃO TELETRANSPORTA TUDO
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    TEST_MODE["on"] = not TEST_MODE["on"]
                    TEST_MODE["toast"] = 1.6
                    continue
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
                    continue

                if state == "menu":
                    if event.key in (pygame.K_w, pygame.K_UP, pygame.K_i):
                        menu_sel = (menu_sel - 1) % len(MENU_OPTIONS)
                    elif event.key in (pygame.K_s, pygame.K_DOWN, pygame.K_k):
                        menu_sel = (menu_sel + 1) % len(MENU_OPTIONS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                        choice = MENU_OPTIONS[menu_sel]
                        if choice == "JOGAR":
                            start_game()
                        elif choice == "COMO JOGAR":
                            state = "howto"
                        else:
                            pygame.quit()
                            sys.exit()
                    continue

                if state == "howto":
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
                        state = "menu"
                    continue

                # ---- JOGO ----
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    if not game_over and not victory:
                        is_paused = not is_paused

                if event.key == pygame.K_m and (is_paused or game_over or victory):
                    go_menu()
                    continue

                if event.key == pygame.K_r:
                    start_game()

        # ======================= MENU =======================
        if state in ("menu", "howto"):
            menu_time += dt
            update_effects(dt)
            if state == "menu":
                draw_menu(canvas, fonts, menu_time, menu_sel)
                for prt in particles:
                    prt.draw(canvas)
            else:
                draw_howto(canvas, fonts, menu_time)
            draw_test_badge(canvas, font_small, font_mid, dt)
            if fade > 0:
                fade = max(0.0, fade - dt * 2.5)
                veil = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                veil.set_alpha(int(255 * fade))
                canvas.blit(veil, (0, 0))
            present_canvas()
            continue

        # ======================= JOGO =======================
        if not is_paused and not game_over and not victory:
            player.handle_input(player_projectiles, dt)
            player.update(dt)
            update_effects(dt)  # PARTICULAS + TREMIDA
            wave_banner = max(0.0, wave_banner - dt)
            if current_boss and getattr(current_boss, "hit_flash", 0) > 0:
                current_boss.hit_flash -= dt

            # VENTINHO ATRÁS DO GATO QUANDO ELE VOA RÁPIDO
            wind_timer -= dt
            if player.vel.length() > 2.5 and wind_timer <= 0 and len(particles) < MAX_PARTICLES:
                wind_timer = 0.04
                back = -player.vel.normalize()
                particles.append(Particle(player.pos.x + back.x * 30 + random.uniform(-8, 8),
                                          player.pos.y + back.y * 30 + random.uniform(-12, 12),
                                          back.x * 2.5, back.y * 2.5, 0.22, (230, 235, 255), 2))

            if current_boss:
                current_boss.update(player.pos, enemy_projectiles, dt)

                # LACAIOS: RATOS DE CORDA (DR. MIAUSTEIN) E CLONES DE SOMBRA (SOMBRA)
                minions = getattr(current_boss, "minions", None)
                if minions is not None:
                    for drone in minions[:]:
                        for p in player_projectiles[:]:
                            if (p.pos - drone.pos).length() < (p.size + drone.radius):
                                drone.hp -= player_hit_damage(p)
                                spawn_burst(p.pos.x, p.pos.y, FUR_COLORS, 5, speed=2.5, life=0.3, size=4)
                                spawn_fx("impacto", p.pos.x, p.pos.y)
                                if p in player_projectiles:
                                    player_projectiles.remove(p)
                                if drone.hp <= 0:
                                    minions.remove(drone)
                                    bc = BOSS_COLORS.get(type(current_boss), (255, 255, 255))
                                    spawn_burst(drone.pos.x, drone.pos.y, [bc, (255, 230, 120), (255, 255, 255)],
                                                16, speed=4.0, life=0.45, size=5)
                                    add_shake(3, 0.12)
                                    spawn_fx("explosao_p" if isinstance(drone, OrbitalDrone) else "poeira",
                                             drone.pos.x, drone.pos.y)
                                    break

                        # DANO DE ENCOSTAR NO LACAIO
                        if drone in minions and player.iframe <= 0 and \
                                (player.pos - drone.pos).length() < (player.radius + drone.radius * 0.8):
                            if player.take_damage():
                                game_over = True

                # DERROTA TERMINOU: EXPLOSÃO GRANDE E POWER-UP
                if current_boss.dead:
                    bcol = BOSS_COLORS.get(type(current_boss), (255, 255, 255))
                    bpos = current_boss.get_hitbox_pos()
                    spawn_burst(bpos.x, bpos.y, [bcol, (255, 255, 255), (255, 220, 120)], 70,
                                speed=7.5, life=1.0, size=8)
                    add_shake(12, 0.5)
                    spawn_big_explosion(bpos.x, bpos.y)
                    current_boss = None
                    if len(items_queue) > 0:
                        active_capsule = UpgradeCapsule(items_queue.pop(0))
                    elif len(boss_queue) == 0:
                        victory = True  # ÚLTIMO CHEFE CAIU
                        end_timer = 0.0

            if current_boss and not current_boss.invulnerable:
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
                        current_boss.hp -= player_hit_damage(p)
                        current_boss.on_hit()  # PISCA BRANCO E ACHATA UM POUQUINHO
                        spawn_burst(p.pos.x, p.pos.y, FUR_COLORS, 6, speed=3.0, life=0.3, size=5)
                        spawn_fx("impacto", p.pos.x, p.pos.y)
                        if p in player_projectiles:
                            player_projectiles.remove(p)

                        if current_boss.hp <= 0:
                            # COMEÇA A ANIMAÇÃO DE DERROTA (OLHOS EM X, CAMBALEIA, DEPOIS EXPLODE)
                            current_boss.start_dying()
                            enemy_projectiles.clear()
                            player.set_mood("feliz", MOOD_HAPPY_TIME)  # BOSS DERROTADO
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
                    elif active_capsule.item_type == "HEAL":
                        player.hp = min(player.max_hp, player.hp + 6)
                        spawn_hearts(player.pos.x, player.pos.y, 5)
                    elif active_capsule.item_type == "EXTENDER":
                        player.proj_range += 140
                        player.proj_size += 3

                    if len(boss_queue) > 0:
                        current_boss = boss_queue.pop(0)
                        wave_number += 1
                        active_capsule = None
                        fade = 0.9          # TROCA DE CENÁRIO COM FADE
                        wave_banner = 1.8
                        particles.clear()
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
                if p.kind == "poeira" and p.split_time and p.age >= p.split_time:
                    # BOLA DE POEIRA ESTOURA EM 6 POEIRINHAS
                    if p in enemy_projectiles:
                        enemy_projectiles.remove(p)
                    off = random.uniform(0, math.tau)
                    for i in range(6):
                        a = off + i * math.tau / 6
                        enemy_projectiles.append(Projectile(p.pos.x, p.pos.y, math.cos(a) * 3.4, math.sin(a) * 3.4,
                                                            1, 320, BOSS_COLOR_5, 5, kind="poeirinha"))
                    spawn_fx("poeira", p.pos.x, p.pos.y)
                    continue

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

            if game_over or victory:
                end_timer = 0.0
                if game_over:
                    spawn_burst(player.pos.x, player.pos.y, HURT_COLORS + FUR_COLORS, 40, speed=6, life=0.8, size=7)
        else:
            if game_over or victory:
                end_timer += dt
                update_effects(dt)
                # CONFETE NA VITÓRIA
                if victory and random.random() < 0.5 and len(particles) < MAX_PARTICLES:
                    particles.append(Particle(random.uniform(0, VIRTUAL_WIDTH), -10, random.uniform(-1, 1),
                                              random.uniform(1.5, 3), 2.5,
                                              random.choice([BOSS_COLOR_1, BOSS_COLOR_2, BOSS_COLOR_3, ITEM_COLOR, (255, 230, 120)]), 5))

        #RENDERIZA O CANVA(NAO ESQUECE DNV)
        canvas.fill(BG_COLOR)

        arena_img = ARENAS[max(0, min(len(ARENAS) - 1, wave_number - 1))]  # UM CENÁRIO POR CHEFE
        if arena_img is not None:
            canvas.blit(arena_img, (0, 0))
        else:
            # SEM IMAGEM: VOLTA PRA ARENA ANTIGA COM GRADE
            pygame.draw.rect(canvas, ARENA_COLOR, (ARENA_MARGIN_X, ARENA_MARGIN_Y, ARENA_WIDTH, ARENA_HEIGHT))
            for x in range(ARENA_MARGIN_X, VIRTUAL_WIDTH - ARENA_MARGIN_X, 50):
                pygame.draw.line(canvas, GRID_LINE, (x, ARENA_MARGIN_Y), (x, VIRTUAL_HEIGHT - ARENA_MARGIN_Y))
            for y in range(ARENA_MARGIN_Y, VIRTUAL_HEIGHT - ARENA_MARGIN_Y, 50):
                pygame.draw.line(canvas, GRID_LINE, (ARENA_MARGIN_X, y), (VIRTUAL_WIDTH - ARENA_MARGIN_X, y))
            pygame.draw.rect(canvas, WALL_COLOR, (ARENA_MARGIN_X, ARENA_MARGIN_Y, ARENA_WIDTH, ARENA_HEIGHT), width=3)

        draw_arena_ambience(canvas, max(1, min(5, wave_number)), pygame.time.get_ticks() / 1000,
                            bool(current_boss and current_boss.enraged))
        # LUZ CENTRAL SUAVE
        add_glow(canvas, VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2, 300, (40, 34, 60), 0.5)

        # NA FASE 2 A ARENA FICA COM UM TOM VERMELHO PULSANDO
        if current_boss and current_boss.enraged and current_boss.dying <= 0:
            tint = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            tint.fill((255, 30, 60, int(18 + math.sin(pygame.time.get_ticks() * 0.006) * 10)))
            canvas.blit(tint, (0, 0))

        if active_capsule:
            active_capsule.draw(canvas, font_small)

        for prt in particles:
            prt.draw(canvas)
        for p in player_projectiles:
            p.draw(canvas)

        if current_boss:
            bc = BOSS_COLORS.get(type(current_boss), (255, 255, 255))
            hb = current_boss.get_hitbox_pos()
            add_glow(canvas, hb.x, hb.y, 110, bc, (0.55 if current_boss.enraged else 0.32) * current_boss.alpha / 255)
        add_glow(canvas, player.pos.x, player.pos.y, 60, (255, 150, 60), 0.18)

        # O GATO FICA ATRÁS DO CHEFE SE ESTIVER MAIS "PRO FUNDO" (Y MENOR)
        boss_first = current_boss is not None and current_boss.pos.y < player.pos.y
        if current_boss and boss_first:
            current_boss.draw(canvas)
        if not game_over and not victory:
            player.draw(canvas)
        if current_boss and not boss_first:
            current_boss.draw(canvas)
        if current_boss:
            has_sprite = {BossPrism: PRISM_SPRITES, BossOrbital: ORBITAL_SPRITES, BossCore: CORE_SPRITES,
                          BossNinja: NINJA_SPRITES, BossDuchess: DUCHESS_SPRITES}.get(type(current_boss))
            if getattr(current_boss, "hit_flash", 0) > 0 and not has_sprite:
                hb = current_boss.get_hitbox_pos()
                pygame.draw.circle(canvas, (255, 255, 255), (int(hb.x), int(hb.y)), current_boss.radius + 3, 3)

        for p in enemy_projectiles:
            p.draw(canvas)
        for e in effects:
            e.draw(canvas)

        # LUZ/ESCURECIDO NAS BORDAS DA ARENA (ANTES DO HUD)
        canvas.blit(VIGNETTE, (0, 0))
        draw_hud(canvas, fonts, player, current_boss, wave_number, victory)
        draw_test_badge(canvas, font_small, font_mid, dt)

        # AVISOS GRANDES: "ONDA X" NA ENTRADA E "FÚRIA!" NA FASE 2
        if current_boss and wave_banner > 0 and not game_over:
            k = min(1.0, wave_banner / 0.3, (1.8 - wave_banner) / 0.25)
            slide = (1.0 - k) * 80
            bcol = BOSS_COLORS.get(type(current_boss), (255, 255, 255))
            draw_text_outline(canvas, font_large, f"ONDA {wave_number}", (255, 255, 255),
                              (VIRTUAL_WIDTH // 2 - slide, VIRTUAL_HEIGHT // 2 - 30))
            draw_text_outline(canvas, font_mid, current_boss.name, bcol, (VIRTUAL_WIDTH // 2 + slide, VIRTUAL_HEIGHT // 2 + 14))
            draw_text_outline(canvas, font_small, getattr(current_boss, "title", ""), (230, 220, 240),
                              (VIRTUAL_WIDTH // 2 - slide, VIRTUAL_HEIGHT // 2 + 44), px=2)
        if current_boss and current_boss.banner > 0:
            k = current_boss.banner / 1.6
            size = 1.0 + max(0.0, (k - 0.85)) * 4
            txt = font_title.render("FÚRIA!", False, (255, 60, 70))
            surf = pygame.Surface((txt.get_width() + 12, txt.get_height() + 12), pygame.SRCALPHA)
            draw_text_outline(surf, font_title, "FÚRIA!", (255, 70, 80), (surf.get_width() // 2, surf.get_height() // 2),
                              outline=(60, 0, 10), px=4)
            surf = pygame.transform.scale(surf, (int(surf.get_width() * size * 0.8), int(surf.get_height() * size * 0.8)))
            if k < 0.25:
                surf.set_alpha(int(255 * k / 0.25))
            canvas.blit(surf, surf.get_rect(center=(VIRTUAL_WIDTH // 2 + random.randint(-2, 2), 150)))

        if is_paused:
            canvas.blit(end_overlay, (0, 0))
            pause_txt = font_large.render("JOGO PAUSADO", False, (0, 240, 255))
            sub_txt = font_small.render("[P/ESC] continuar    [M] menu    [R] reiniciar", False, (200, 200, 200))
            canvas.blit(pause_txt, pause_txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 20)))
            canvas.blit(sub_txt, sub_txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 25)))

        if game_over or victory:
            # OVERLAY ENTRA ESCURECENDO AOS POUCOS
            ov = end_overlay.copy()
            ov.set_alpha(int(min(1.0, end_timer / 0.5) * 255))
            canvas.blit(ov, (0, 0))
            for prt in particles:
                if victory:
                    prt.draw(canvas)

            pop = min(1.0, end_timer / 0.35)
            if game_over:
                draw_text_outline(canvas, font_large, "PATÉTICO:BETINHA DEMAIS", (255, 50, 80),
                                  (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 20 + (1 - pop) * 40), outline=(50, 0, 10))
                sub = font_small.render("[R] tentar novamente    [M] menu", False, (200, 200, 200))
            else:
                draw_text_outline(canvas, font_large, "BOSS RUSH FINALIZADO!", ITEM_COLOR,
                                  (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 20 + (1 - pop) * 40), outline=(0, 50, 30))
                sub = font_small.render("[R] jogar novamente    [M] menu", False, (200, 200, 200))
            canvas.blit(sub, sub.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 25)))

            # SUPERCAT NA TELA FINAL: TRISTE SE PERDEU, FELIZ (E VOANDO) SE GANHOU
            mood = "triste" if game_over else "feliz"
            frames = CAT_FLY.get(mood)
            end_cat = frames[int(end_timer / 0.1) % len(frames)] if frames else CAT_SPRITES.get(mood)
            if end_cat is not None:
                end_cat = pygame.transform.scale(end_cat, (int(end_cat.get_width() * 1.35), int(end_cat.get_height() * 1.35)))
                if victory:
                    end_cat = pygame.transform.rotate(end_cat, math.sin(end_timer * 3) * 10)
                canvas.blit(end_cat, end_cat.get_rect(center=(VIRTUAL_WIDTH // 2,
                                                       VIRTUAL_HEIGHT // 2 - 130 + int(math.sin(pygame.time.get_ticks() * 0.004) * 6))))

        if fade > 0:
            fade = max(0.0, fade - dt * 2.2)
            veil = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            veil.set_alpha(int(255 * fade))
            canvas.blit(veil, (0, 0))

        present_canvas()


def present_canvas():
    target_w, target_h = screen.get_size()
    dest_rect = get_scaled_rect(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, target_w, target_h)

    scaled_canvas = pygame.transform.scale(canvas, dest_rect.size)
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