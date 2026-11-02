-- Arte dos inimigos do Supercat: Boss Rush
-- Cada sprite e montado pixel a pixel em grades (por camada e por frame) e
-- depois gravado como .aseprite pelo make_sprites.lua (rodando dentro do Aseprite).

local A = {}

-------------------------------------------------------------------------------
-- utilitarios de grade
-------------------------------------------------------------------------------
local function grid(w, h)
  local g = { w = w, h = h }
  for y = 0, h - 1 do g[y] = {} end
  return g
end

local function set(g, x, y, c)
  if x >= 0 and y >= 0 and x < g.w and y < g.h then g[y][x] = c end
end

local function get(g, x, y)
  if x >= 0 and y >= 0 and x < g.w and y < g.h then return g[y][x] end
end

local function copy(g)
  local n = grid(g.w, g.h)
  for y = 0, g.h - 1 do for x = 0, g.w - 1 do n[y][x] = g[y][x] end end
  return n
end

-- contorno de 1px em volta de tudo que nao e vazio (vizinhanca de 4)
local function outline(g, col)
  local o = copy(g)
  for y = 0, g.h - 1 do
    for x = 0, g.w - 1 do
      if not g[y][x] then
        if get(g, x - 1, y) or get(g, x + 1, y) or get(g, x, y - 1) or get(g, x, y + 1) then
          o[y][x] = col
        end
      end
    end
  end
  return o
end

-- carimba um desenho em texto; map: caractere -> cor (espaco e '.' = nada)
local function stamp(g, ox, oy, rows, map, mirror)
  for j, row in ipairs(rows) do
    local n = #row
    for i = 1, n do
      local ch = row:sub(i, i)
      local c = map[ch]
      if c then
        local x = mirror and (ox + n - i) or (ox + i - 1)
        set(g, x, oy + j - 1, c)
      end
    end
  end
end

local function mirror_rows(rows)
  local r = {}
  for i, row in ipairs(rows) do r[i] = row:reverse() end
  return r
end

local function clamp(v, a, b) if v < a then return a elseif v > b then return b end return v end

-------------------------------------------------------------------------------
-- paletas (mesma linguagem do Supercat: contorno colorido escuro, sem preto puro)
-------------------------------------------------------------------------------
local function rgb(r, g, b) return { r, g, b } end

local PINK = {
  rgb(92, 14, 52),    -- 1 contorno
  rgb(156, 22, 82),   -- 2 sombra forte
  rgb(206, 34, 108),  -- 3 sombra
  rgb(255, 64, 140),  -- 4 base (BOSS_COLOR_1 do jogo, suavizado)
  rgb(255, 128, 180), -- 5 luz
  rgb(255, 190, 220), -- 6 brilho
  rgb(255, 240, 248), -- 7 reflexo
}
local AMBER = {
  rgb(98, 46, 10),
  rgb(170, 88, 8),
  rgb(222, 132, 4),
  rgb(255, 180, 0),
  rgb(255, 212, 80),
  rgb(255, 236, 160),
  rgb(255, 250, 225),
}
local PURPLE = {
  rgb(48, 10, 84),
  rgb(88, 20, 150),
  rgb(128, 30, 210),
  rgb(170, 64, 255),
  rgb(200, 132, 255),
  rgb(228, 196, 255),
  rgb(248, 236, 255),
}
local FACE = {
  k = rgb(54, 18, 40),     -- traco do rosto
  w = rgb(255, 255, 255),  -- branco do olho / dente
  m = rgb(150, 24, 48),    -- boca por dentro
  t = rgb(232, 70, 90),    -- lingua
}
local METAL = {
  rgb(44, 40, 62),
  rgb(74, 70, 98),
  rgb(116, 112, 142),
  rgb(170, 168, 196),
}
local LASER = {
  rgb(120, 6, 24),
  rgb(214, 20, 46),
  rgb(255, 72, 72),
  rgb(255, 170, 160),
}

A.palettes = { PINK, AMBER, PURPLE, METAL, LASER }
A.face = FACE


-------------------------------------------------------------------------------
-- ferramentas de desenho por partes (cada parte ganha contorno proprio e e
-- empilhada de tras pra frente, assim cabeca/braco ficam separados do corpo)
-------------------------------------------------------------------------------
local BLACKCAT = {
  rgb(16, 8, 28),     -- 1 contorno
  rgb(30, 18, 48),    -- 2
  rgb(44, 28, 68),    -- 3
  rgb(62, 42, 92),    -- 4 base do pelo
  rgb(88, 64, 124),   -- 5
  rgb(122, 98, 162),  -- 6
  rgb(170, 150, 210), -- 7
}
local GOLD = {
  rgb(110, 58, 6), rgb(176, 104, 10), rgb(226, 150, 20), rgb(255, 196, 40),
  rgb(255, 226, 110), rgb(255, 244, 190), rgb(255, 255, 240),
}
local CAPE = {
  rgb(36, 10, 40), rgb(64, 16, 66), rgb(96, 24, 92), rgb(128, 36, 118),
}
local MASK = rgb(40, 12, 46)
local EYE_Y = { rgb(255, 230, 60), rgb(200, 255, 80), rgb(255, 250, 200) } -- olho de vilao
local WHITE = rgb(255, 255, 255)

local function tone_of(l)
  if l > 0.80 then return 6 elseif l > 0.52 then return 5 elseif l > 0.18 then return 4
  elseif l > -0.18 then return 3 else return 2 end
end

local function light(dx, dy, rx, ry)
  local nx, ny = dx / rx, dy / ry
  local nz = math.sqrt(math.max(0, 1 - nx * nx - ny * ny))
  return (-0.55 * nx) + (-0.62 * ny) + (0.56 * nz)
end

-- elipse sombreada numa parte nova
local function ell(w, h, cx, cy, rx, ry, pal, shift)
  local g = grid(w, h)
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      local dx, dy = x + 0.5 - cx, y + 0.5 - cy
      if (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1 then
        g[y][x] = pal[clamp(tone_of(light(dx, dy, rx, ry)) + (shift or 0), 2, 7)]
      end
    end
  end
  return g
end

-- pinta uma elipse dentro de uma parte ja existente (sem sombreado)
local function ell_into(g, cx, cy, rx, ry, col, only_on_existing)
  for y = 0, g.h - 1 do
    for x = 0, g.w - 1 do
      local dx, dy = x + 0.5 - cx, y + 0.5 - cy
      if (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1 then
        if not only_on_existing or g[y][x] then g[y][x] = col end
      end
    end
  end
end

local function tri_into(g, ax, ay, bx, by, cx, cy, colfn)
  for y = 0, g.h - 1 do
    for x = 0, g.w - 1 do
      local px, py = x + 0.5, y + 0.5
      local d1 = (px - bx) * (ay - by) - (ax - bx) * (py - by)
      local d2 = (px - cx) * (by - cy) - (bx - cx) * (py - cy)
      local d3 = (px - ax) * (cy - ay) - (cx - ax) * (py - ay)
      local neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
      local pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
      if not (neg and pos) then g[y][x] = colfn(x, y) end
    end
  end
end

-- cola src por cima de dst
local function over(dst, src)
  for y = 0, dst.h - 1 do
    for x = 0, dst.w - 1 do
      local c = src[y][x]
      if c then dst[y][x] = c end
    end
  end
  return dst
end

-- cabeca de gato: elipse + orelhas (com parte de dentro), ja com contorno
local function cat_head(w, h, cx, cy, rx, ry, pal, inner, ear)
  ear = ear or {}
  local g = ell(w, h, cx, cy, rx, ry, pal)
  local up = ear.up or (ry + 7)
  local spread = ear.spread or (rx * 0.62)
  local base = ear.base or (rx * 0.62)
  for _, s in ipairs({ -1, 1 }) do
    local tipx, tipy = cx + s * (spread + 2), cy - up
    local b1x, b1y = cx + s * (spread - base * 0.55), cy - ry * 0.55
    local b2x, b2y = cx + s * (rx + 0.5), cy - ry * 0.05
    tri_into(g, tipx, tipy, b1x, b1y, b2x, b2y, function(x, y)
      return (s < 0) and pal[5] or pal[3]
    end)
    -- parte de dentro da orelha
    local ix, iy = tipx + s * -0.6, tipy + 3.2
    tri_into(g, ix, iy, b1x + s * 1.8, b1y + 0.2, b2x - s * 2.6, b2y - 1.5, function() return inner end)
  end
  -- refaz a elipse por cima pra a base das orelhas ficar limpa
  over(g, ell(w, h, cx, cy, rx, ry, pal))
  return g
end

-- tracos grossos (rabo, antena...): circulos ao longo de pontos
local function blob_line(g, pts, r, colfn)
  for i, p in ipairs(pts) do
    for y = math.floor(p[2] - r - 1), math.ceil(p[2] + r + 1) do
      for x = math.floor(p[1] - r - 1), math.ceil(p[1] + r + 1) do
        local dx, dy = x + 0.5 - p[1], y + 0.5 - p[2]
        if dx * dx + dy * dy <= r * r then set(g, x, y, colfn(i, dx, dy)) end
      end
    end
  end
end

local function sym(rows)
  -- recebe a metade esquerda e devolve a linha inteira espelhada
  local r = {}
  for i, row in ipairs(rows) do r[i] = row .. row:reverse() end
  return r
end

-------------------------------------------------------------------------------
-- 1) FODAO - gatao rosa brutamontes, com mascara, capa e coleira de espinhos
-------------------------------------------------------------------------------
local function fodao_body(frame, jumping)
  local W, H = 60, 60
  local g = grid(W, H)

  -- capa (atras de tudo), a barra balanca com o frame
  local cape = grid(W, H)
  local wave = { 0, 1, 2, 1 }
  local wv = wave[(frame % 4) + 1]
  for y = 24, 57 do
    local t = (y - 24) / 33
    local half = 12 + t * 15
    local swing = math.floor(math.sin(t * 3 + frame * 1.6) * (1 + t * 2))
    for x = math.floor(30 - half) + swing, math.floor(30 + half) + swing do
      local bottom = 57 - ((x + frame * 2) % 6 < 3 and 0 or 1) - (math.abs(x - 30) > half - 2 and wv or 0)
      if y <= bottom then
        local edge = (x - (30 + swing)) / half
        local c = CAPE[3]
        if edge < -0.55 then c = CAPE[4] elseif edge > 0.45 then c = CAPE[2] end
        set(cape, x, y, c)
      end
    end
  end
  over(g, outline(cape, CAPE[1]))

  -- rabo (sai pela direita, balanca)
  local tail = grid(W, H)
  local pts = {}
  local sway = ({ 0, 1.5, 2.5, 1.5 })[(frame % 4) + 1]
  for i = 0, 12 do
    local t = i / 12
    pts[#pts + 1] = { 44 + t * 9 + sway * t, 48 - t * 22 + math.sin(t * 3.1) * 2 - sway * t * t * 1.5 }
  end
  blob_line(tail, pts, 2.6, function(i, dx, dy)
    if i >= 11 then return PINK[2] end            -- ponta escura
    if dx + dy < -0.5 then return PINK[5] end
    return (i % 4 < 2) and PINK[4] or PINK[3]       -- listrinhas
  end)
  over(g, outline(tail, PINK[1]))

  -- pes
  for _, fx in ipairs({ 21, 39 }) do
    local foot = ell(W, H, fx, 54.5, 6, 3.5, PINK)
    over(g, outline(foot, PINK[1]))
  end

  -- corpo gordo + barriga clara
  local body = ell(W, H, 30, 41, 18, 14, PINK)
  ell_into(body, 30, 44, 10.5, 9, PINK[6], true)
  ell_into(body, 31.5, 46, 8, 6.5, PINK[5], true)
  over(g, outline(body, PINK[1]))

  -- bracos (punhos fechados); no pulo vao pra cima
  for _, s in ipairs({ -1, 1 }) do
    local ax, ay = 30 + s * 17, jumping and 26 or 42
    local arm = ell(W, H, ax, ay, 5, jumping and 6 or 5.5, PINK, s > 0 and -1 or 0)
    -- dedinhos
    set(arm, math.floor(ax) - 1, math.floor(ay) + (jumping and -4 or 3), PINK[2])
    set(arm, math.floor(ax) + 1, math.floor(ay) + (jumping and -4 or 3), PINK[2])
    over(g, outline(arm, PINK[1]))
  end

  -- cabeca
  local head = cat_head(W, H, 30, 21, 16, 12.5, PINK, PINK[6], { up = 19, spread = 9.5, base = 8 })
  over(g, outline(head, PINK[1]))

  -- coleira de espinhos
  local collar = grid(W, H)
  for x = 18, 41 do
    set(collar, x, 32, METAL[3]); set(collar, x, 33, METAL[2])
  end
  for _, x in ipairs({ 20, 25, 34, 39 }) do
    set(collar, x, 34, METAL[4]); set(collar, x, 35, METAL[3])
  end
  -- pingente de caveira-de-peixe dourado
  stamp(collar, 28, 33, { "abba", "abbd", " dd " }, { a = GOLD[6], b = GOLD[4], d = GOLD[2] })
  over(g, outline(collar, METAL[1]))

  -- brilho que corre na capa no frame 2
  return g
end

local function fodao_face(jumping)
  local g = grid(60, 60)
  local map = { m = MASK, y = EYE_Y[1], p = MASK, w = WHITE, k = PINK[1], n = PINK[2],
    f = WHITE, o = FACE.m, t = FACE.t, s = PINK[7] }
  -- mascara de vilao (metade esquerda espelhada)
  local mask = jumping and sym({
    " mmm          ",
    "mmmmmm        ",
    "mmmmmmmmm     ",
    "mmmwwwwmmmmmmm",
    "mmwyyyywmmmmmm",
    "mmwyyppywmmmmm",
    "mmwyyppywmmmmm",
    "mmmwyyyymmmmmm",
    " mmmwwwmmm  mm",
    "   mmmm       ",
  }) or sym({
    "mm            ",
    "mmmmm         ",
    "mmmmmmmm      ",
    "mmmmmmmmmmmmmm",
    "mmyyyymmmmmmmm",
    "mmyyyyypmmmmmm",
    "mmyyyyppmmmmmm",
    " mmyyyppmmmmmm",
    "  mmmmmmmm  mm",
    "    mmm       ",
  })
  stamp(g, 16, 14, mask, map)
  -- reflexinho no olho
  if not jumping then set(g, 19, 18, WHITE); set(g, 40, 18, WHITE) end
  -- nariz e boca
  if jumping then
    stamp(g, 25, 24, {
      "    nn    ",
      "  kkkkkk  ",
      " kfoooofk ",
      " kooooook ",
      " koottook ",
      "  kkkkkk  ",
    }, map)
  else
    stamp(g, 24, 24, {
      "     nn     ",
      "      k     ",
      "  k  k k  k ",
      "   kk   kk  ",
      "   f     f  ",
    }, map)
  end
  -- bigodes
  for _, row in ipairs({ { 25, -1 }, { 27, 0 }, }) do
    local y, dy = row[1], row[2]
    for i = 0, 6 do
      set(g, 9 + i, y + ((i < 3) and dy or 0), PINK[7])
      set(g, 50 - i, y + ((i < 3) and dy or 0), PINK[7])
    end
  end
  return g
end

local function make_prism()
  local frames = {}
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 140, layers = { corpo = fodao_body(i, false), rosto = fodao_face(false) } }
  end
  frames[#frames + 1] = { dur = 140, layers = { corpo = fodao_body(1, true), rosto = fodao_face(true) } }
  return {
    name = "boss_prisma", w = 60, h = 60, frames = frames,
    tags = { { name = "parado", from = 1, to = 4 }, { name = "pulo", from = 5, to = 5 } },
  }
end

-------------------------------------------------------------------------------
-- 2) FODINHA - gato cientista maluco na capsula voadora, monoculo-laser
-------------------------------------------------------------------------------
local function fodinha_body(frame)
  local W, H = 56, 56
  local g = grid(W, H)

  -- jato embaixo da capsula
  local flame = grid(W, H)
  local fl = ({ 4, 6, 5, 7 })[(frame % 4) + 1]
  for i = 0, fl do
    local hw = math.max(0, 3 - i * 0.45)
    for x = math.floor(28 - hw), math.floor(27 + hw) do
      set(flame, x, 48 + i, (i < 2) and GOLD[7] or ((i < 4) and GOLD[5] or LASER[3]))
    end
  end
  over(g, flame)

  -- bracos/patas apoiadas na borda (ficam atras da borda da capsula)
  local cat = cat_head(W, H, 28, 22, 14, 11.5, AMBER, PINK[5], { up = 18, spread = 8, base = 7 })
  -- listras de gato laranja-tigrado na testa
  for _, st in ipairs({ { 27, 11 }, { 28, 11 }, { 24, 12 }, { 31, 12 }, { 27, 13 }, { 28, 13 } }) do
    set(cat, st[1], st[2], AMBER[3])
  end
  over(g, outline(cat, AMBER[1]))

  -- capsula (meia esfera de metal) por cima do pescoco
  local pod = grid(W, H)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local dx, dy = x + 0.5 - 28, y + 0.5 - 33
      if dy >= 0 and (dx * dx) / (23 * 23) + (dy * dy) / (14 * 14) <= 1 then
        local tone = clamp(tone_of(light(dx, dy - 4, 23, 14)), 1, 4)
        pod[y][x] = METAL[clamp(tone - 1, 1, 4)]
      end
    end
  end
  -- borda de cima da capsula (anel ambar com luzinhas que andam)
  for x = 5, 50 do
    set(pod, x, 33, AMBER[5]); set(pod, x, 34, AMBER[4]); set(pod, x, 35, AMBER[3])
    if (x + frame * 3) % 7 == 0 and x > 7 and x < 48 then set(pod, x, 34, LASER[3]) end
  end
  -- simbolo de patinha na frente da capsula
  stamp(pod, 24, 39, {
    " r r ",
    "r   r",
    " rrr ",
    "rrrrr",
    " rrr ",
  }, { r = LASER[2] })
  over(g, outline(pod, METAL[1]))

  -- patinhas segurando a borda
  for _, px in ipairs({ 17, 39 }) do
    local paw = ell(W, H, px, 32.5, 3.6, 2.6, AMBER)
    set(paw, px - 1, 34, AMBER[2]); set(paw, px + 1, 34, AMBER[2])
    over(g, outline(paw, AMBER[1]))
  end

  -- antena com luz que pisca
  local on = (frame % 2 == 0)
  for y = 3, 8 do set(g, 34, y, METAL[3]); set(g, 35, y, METAL[1]) end
  stamp(g, 32, 0, { " kk ", "kabk", "kbck", " kk " },
    { k = LASER[1], a = on and LASER[4] or LASER[2], b = on and LASER[3] or LASER[2], c = on and LASER[2] or LASER[1] })
  return g
end

local function fodinha_face(frame)
  local g = grid(56, 56)
  -- olho esquerdo bravo (sobrancelha de cientista maluco)
  stamp(g, 17, 15, {
    "kk     ",
    " kkkk  ",
    "  kkkkk",
    " kyyykk",
    " kyypk ",
    "  kkk  ",
  }, { k = AMBER[1], y = EYE_Y[2], p = MASK })
  -- monoculo-laser no olho direito (com corrente)
  stamp(g, 29, 14, {
    "  kkkkk  ",
    " kdrrrdk ",
    "kdroworrk",
    "kdrooorrk",
    "kdrrorrrk",
    " kdrrrdk ",
    "  kkkkk  ",
  }, { k = METAL[1], d = METAL[3], r = LASER[2], o = LASER[3], w = LASER[4] })
  local gl = ({ { 32, 16 }, { 33, 16 }, { 32, 17 }, { 31, 17 } })[(frame % 4) + 1]
  set(g, gl[1], gl[2], WHITE)
  for i = 0, 5 do set(g, 37 + math.floor(i / 2), 21 + i, GOLD[3]) end
  -- nariz, bigode de vilao enrolado e sorriso maligno
  stamp(g, 21, 21, {
    "      nn      ",
    "  ss   k   ss ",
    " s  ssk kss  s",
    "  s  kf  fk s ",
    "      kkk     ",
  }, { n = PINK[2], k = AMBER[1], s = AMBER[6], f = WHITE })
  return g
end

local function make_orbital()
  local frames = {}
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 120, layers = { corpo = fodinha_body(i), rosto = fodinha_face(i) } }
  end
  return {
    name = "boss_orbital", w = 56, h = 56, frames = frames,
    tags = { { name = "parado", from = 1, to = 4 } },
  }
end


local function metal_ell(w, h, cx, cy, rx, ry)
  local g = grid(w, h)
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      local dx, dy = x + 0.5 - cx, y + 0.5 - cy
      if (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1 then
        local l = light(dx, dy, rx, ry)
        g[y][x] = (l > 0.55) and METAL[4] or ((l > 0.05) and METAL[3] or METAL[2])
      end
    end
  end
  return g
end

-- rato-robo (os "drones" do FODINHA)
local function mouse_frame(frame, attack)
  local W, H = 22, 20
  local g = grid(W, H)
  -- rabinho de fio
  local wig = (frame % 2 == 0) and 0 or 1
  local tail = grid(W, H)
  for i = 0, 6 do set(tail, 15 + i, 13 - math.floor(i / 2) + ((i % 3 == 1) and wig or 0), METAL[2]) end
  over(g, tail)
  -- orelhas redondas
  for _, ex in ipairs({ 6, 14 }) do
    local ear = metal_ell(W, H, ex, 5, 3.2, 3.2)
    ell_into(ear, ex, 5.5, 1.6, 1.6, PINK[5], true)
    over(g, outline(ear, METAL[1]))
  end
  -- corpo de metal com faixa ambar
  local body = metal_ell(W, H, 10, 12, 7.5, 5.5)
  -- METAL tem so 4 tons: remapeia
  for y = 0, H - 1 do for x = 0, W - 1 do
    local c = body[y][x]
    if c then
      local l = light(x + 0.5 - 10, y + 0.5 - 12, 7.5, 5.5)
      body[y][x] = (l > 0.5) and METAL[4] or ((l > 0) and METAL[3] or METAL[2])
      if attack and l > 0 then body[y][x] = AMBER[5] end
    end
  end end
  for y = 9, 15 do if body[y][12] then body[y][12] = AMBER[4]; body[y][13] = AMBER[3] end end
  over(g, outline(body, METAL[1]))
  -- focinho, olho e dentes
  set(g, 2, 13, PINK[4]); set(g, 3, 13, PINK[4])
  if attack then
    stamp(g, 4, 9, { "kk  ", " rrk", " rwk", "    " }, { k = MASK, r = LASER[3], w = LASER[4] })
    set(g, 4, 15, WHITE); set(g, 6, 15, WHITE)
  else
    stamp(g, 5, 10, { "rk", "wr" }, { k = MASK, r = LASER[2], w = LASER[4] })
  end
  -- rodinhas/patas
  local fy = (frame % 2 == 0) and 17 or 18
  set(g, 7, fy, METAL[1]); set(g, 13, fy, METAL[1]); set(g, 8, fy, METAL[1]); set(g, 14, fy, METAL[1])
  return g
end

local function make_drone()
  local frames = {}
  for i = 0, 1 do frames[#frames + 1] = { dur = 90, layers = { corpo = mouse_frame(i, false) } } end
  for i = 0, 1 do frames[#frames + 1] = { dur = 70, layers = { corpo = mouse_frame(i, true) } } end
  return {
    name = "drone", w = 22, h = 20, frames = frames,
    tags = { { name = "orbitando", from = 1, to = 2 }, { name = "atacando", from = 3, to = 4 } },
  }
end

-------------------------------------------------------------------------------
-- 3) PODER FEMININO - rainha gata preta numa caixa magica roxa que pulsa
-------------------------------------------------------------------------------
local function queen_body(pulse, frame)
  local W, H = 72, 72
  local g = grid(W, H)
  local bx0, bx1 = 11 - pulse, 60 + pulse      -- caixa
  local by0, by1 = 34 - pulse, 66 + pulse

  -- brilhos magicos girando em volta
  local spark = { { 6, 30 }, { 64, 22 }, { 4, 58 }, { 67, 50 }, { 14, 12 }, { 58, 6 } }
  for i, p in ipairs(spark) do
    if (i + frame) % 3 ~= 0 then
      local c = ((i + frame) % 2 == 0) and PURPLE[7] or GOLD[5]
      set(g, p[1], p[2], c); set(g, p[1] - 1, p[2], PURPLE[5]); set(g, p[1] + 1, p[2], PURPLE[5])
      set(g, p[1], p[2] - 1, PURPLE[5]); set(g, p[1], p[2] + 1, PURPLE[5])
    end
  end

  -- aba de tras da caixa (aparece atras da gata)
  local flapb = grid(W, H)
  tri_into(flapb, bx0 + 6, by0, bx1 - 6, by0, 36, by0 - 7, function() return PURPLE[3] end)
  over(g, outline(flapb, PURPLE[1]))

  -- gata: cabeca com coroa, olhos ficam no rosto
  local head = cat_head(W, H, 36, 25, 16, 12, BLACKCAT, PINK[4], { up = 16, spread = 11, base = 7 })
  over(g, outline(head, BLACKCAT[1]))
  -- coroa
  local crown = grid(W, H)
  stamp(crown, 28, 6, {
    "a   a   a   a   a",
    "aa  aa aaa aa  aa",
    "aaa abaaaaabaaaaa",
    "bbbbbbbbbbbbbbbbb",
    "bccbbbbbgbbbbbccb",
    "ddddddddddddddddd",
  }, { a = GOLD[5], b = GOLD[4], c = GOLD[6], d = GOLD[2], g = PINK[4] })
  set(crown, 36, 9, PINK[6]); set(crown, 36, 10, PINK[3])
  over(g, outline(crown, GOLD[1]))

  -- caixa
  local box = grid(W, H)
  for y = by0, by1 do
    for x = bx0, bx1 do
      local tone = 4
      local t = ((x - bx0) / (bx1 - bx0)) + ((y - by0) / (by1 - by0))
      if t < 0.55 then tone = 5 elseif t > 1.5 then tone = 3 end
      if y <= by0 + 2 then tone = 6 end             -- borda de cima clara
      if x <= bx0 + 1 then tone = 5 end
      if x >= bx1 - 1 then tone = 2 end
      if y >= by1 - 1 then tone = 2 end
      box[y][x] = PURPLE[tone]
    end
  end
  -- fita dourada vertical
  for y = by0 + 3, by1 - 2 do set(box, 35, y, GOLD[5]); set(box, 36, y, GOLD[4]); set(box, 37, y, GOLD[3]) end
  -- emblema de patinha que acende com o pulso
  local glow = ({ PURPLE[6], PURPLE[7], GOLD[6], PURPLE[7] })[(frame % 4) + 1]
  for _, side in ipairs({ -1, 1 }) do
    local cx = 36 + side * 13
    stamp(box, cx - 3, by0 + 12, {
      " a a ",
      "a   a",
      " aaa ",
      "aaaaa",
      " aaa ",
    }, { a = glow })
  end
  over(g, outline(box, PURPLE[1]))

  -- abas da frente abertas pros lados
  local flap = grid(W, H)
  tri_into(flap, bx0, by0, bx0 + 14, by0, bx0 - 7, by0 - 6, function() return PURPLE[5] end)
  tri_into(flap, bx1 + 1, by0, bx1 - 13, by0, bx1 + 8, by0 - 6, function() return PURPLE[3] end)
  over(g, outline(flap, PURPLE[1]))

  -- patinhas da rainha na borda
  for _, px in ipairs({ 27, 45 }) do
    local paw = ell(W, H, px, by0 + 0.5, 4, 2.8, BLACKCAT)
    set(paw, px - 2, by0 + 2, BLACKCAT[2]); set(paw, px, by0 + 2, BLACKCAT[2]); set(paw, px + 1, by0 + 2, BLACKCAT[2])
    over(g, outline(paw, BLACKCAT[1]))
  end
  return g
end

local function queen_face(frame, blink)
  local g = grid(72, 72)
  local iris = ({ EYE_Y[1], EYE_Y[3], EYE_Y[1], EYE_Y[2] })[(frame % 4) + 1]
  local map = { k = BLACKCAT[1], y = iris, p = MASK, w = WHITE, l = BLACKCAT[1], n = PINK[4], m = BLACKCAT[6] }
  if blink then
    stamp(g, 23, 21, sym({
      "l            ",
      " ll          ",
      "  ll         ",
      "    kkkk     ",
      "   k    k    ",
      "             ",
    }), map)
  else
    -- olhos de gata com cilios (rainha), pupila em fenda
    stamp(g, 23, 21, sym({
      "l            ",
      " ll   kk     ",
      "  lkkkyyk    ",
      "   kyyypyk   ",
      "   kyyypyk   ",
      "    kkkkk    ",
    }), map)
    set(g, 29, 24, WHITE); set(g, 42, 24, WHITE)
  end
  -- nariz e sorriso de canto
  stamp(g, 31, 28, {
    "    nn    ",
    "     k    ",
    "  kkk kkk ",
    "        k ",
  }, map)
  -- bigodes
  for i = 0, 5 do
    set(g, 15 + i, 29, BLACKCAT[6]); set(g, 15 + i, 31 + ((i < 3) and 1 or 0), BLACKCAT[6])
    set(g, 56 - i, 29, BLACKCAT[6]); set(g, 56 - i, 31 + ((i < 3) and 1 or 0), BLACKCAT[6])
  end
  return g
end

local function make_core()
  local frames = {}
  local pulses = { 0, 1, 2, 1 }
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 120, layers = { corpo = queen_body(pulses[i + 1], i), rosto = queen_face(i, false) } }
  end
  frames[#frames + 1] = { dur = 120, layers = { corpo = queen_body(1, 1), rosto = queen_face(1, true) } }
  return {
    name = "boss_nucleo", w = 72, h = 72, frames = frames,
    tags = { { name = "parado", from = 1, to = 4 }, { name = "piscar", from = 5, to = 5 } },
  }
end


-------------------------------------------------------------------------------
-- TIROS DOS CHEFES
-------------------------------------------------------------------------------
-- FODAO: espinha de peixe (aponta pra direita; o jogo gira pro lado do tiro)
local function make_peixe()
  local W, H = 15, 9
  local g = grid(W, H)
  local B1, B2, B3 = rgb(255, 246, 250), rgb(240, 214, 228), rgb(214, 170, 196)
  -- espinha
  for x = 3, 10 do set(g, x, 4, B2) end
  -- costelas
  for _, x in ipairs({ 5, 7, 9 }) do
    for y = 2, 6 do set(g, x, y, (y < 4) and B1 or B3) end
  end
  -- rabo
  tri_into(g, 3.5, 4.5, 0, 0.6, 0, 8.4, function(x, y) return (y < 4) and B1 or B3 end)
  -- cabeca
  ell_into(g, 12, 4.5, 2.8, 3.3, B1)
  set(g, 13, 5, B3); set(g, 12, 6, B3); set(g, 13, 6, B3)
  set(g, 12, 3, PINK[1]) -- olhinho
  g = outline(g, PINK[2])
  return { name = "tiro_peixe", w = W, h = H, frames = { { dur = 100, layers = { corpo = g } } }, tags = {} }
end

-- FODINHA: pontinho de laser (2 frames pulsando, com halo translucido)
local function laser_frame(big)
  local W, H = 13, 13
  local g = grid(W, H)
  local c = 6.5
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local dx, dy = x + 0.5 - c, y + 0.5 - c
      local d = math.sqrt(dx * dx + dy * dy)
      local col
      if d <= 1.6 then col = rgb(255, 255, 255)
      elseif d <= 2.8 then col = rgb(255, 170, 160)
      elseif d <= 4.0 then col = rgb(255, 50, 66)
      elseif d <= (big and 6.4 or 5.4) then col = { 255, 40, 60, big and 70 or 110 }
      end
      if col then g[y][x] = col end
    end
  end
  return g
end

local function make_laser()
  return {
    name = "tiro_laser", w = 13, h = 13,
    frames = { { dur = 80, layers = { corpo = laser_frame(false) } }, { dur = 80, layers = { corpo = laser_frame(true) } } },
    tags = { { name = "pulsar", from = 1, to = 2 } },
  }
end

-- PODER FEMININO: novelo de la roxo (o jogo gira ele)
local function make_novelo()
  local W, H = 14, 14
  local g = ell(W, H, 6.5, 6.5, 5.6, 5.6, PURPLE)
  -- fios do novelo (listras curvas)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      if g[y][x] then
        local dx, dy = x + 0.5 - 6.5, y + 0.5 - 6.5
        if math.floor(dx * 0.8 + dy + dx * dx * 0.08 + 20) % 3 == 0 then g[y][x] = (dx + dy < -2) and PURPLE[4] or PURPLE[2] end
      end
    end
  end
  -- uma volta de fio atravessada
  for x = 2, 11 do
    local y = math.floor(4 + (x - 2) * 0.55 + 0.5)
    if g[y][x] then g[y][x] = PURPLE[6] end
  end
  set(g, 4, 3, PURPLE[7]); set(g, 3, 4, PURPLE[7])
  g = outline(g, PURPLE[1])
  -- pontinha do fio solto
  set(g, 12, 10, PURPLE[5]); set(g, 13, 11, PURPLE[5]); set(g, 13, 12, PURPLE[4])
  return { name = "tiro_novelo", w = W, h = H, frames = { { dur = 100, layers = { corpo = g } } }, tags = {} }
end

-------------------------------------------------------------------------------
-- CENARIOS (480x320, o jogo amplia 2x pra 960x640)
-- area jogavel: x 25..454, y 25..294 (as paredes do jogo ficam em 50px na tela)
-------------------------------------------------------------------------------
local AW, AH = 480, 320
local IX0, IY0, IX1, IY1 = 25, 25, 454, 294

local function hash(x, y, s)
  local n = (x * 374761393 + y * 668265263 + (s or 0) * 2147483647) % 4294967296
  n = ((n ~ (n >> 13)) * 1274126177) % 4294967296
  return (n % 1000) / 1000
end

local function mix(c, d, t)
  return { math.floor(c[1] + (d[1] - c[1]) * t), math.floor(c[2] + (d[2] - c[2]) * t), math.floor(c[3] + (d[3] - c[3]) * t) }
end

local function inside(x, y) return x >= IX0 and x <= IX1 and y >= IY0 and y <= IY1 end

-- patinha grande (decoracao no chao)
local function paw_mask(x, y, cx, cy, s)
  local function e(px, py, rx, ry)
    local dx, dy = (x + 0.5 - px) / rx, (y + 0.5 - py) / ry
    return dx * dx + dy * dy <= 1
  end
  if e(cx, cy + 6 * s, 13 * s, 10.5 * s) then return true end
  for _, t in ipairs({ { -15, -8, 5.0, 6.5 }, { -6, -16, 5.0, 6.5 }, { 6, -16, 5.0, 6.5 }, { 15, -8, 5.0, 6.5 } }) do
    if e(cx + t[1] * s, cy + t[2] * s, t[3] * s, t[4] * s) then return true end
  end
  return false
end

-- 1) RINGUE DO FODAO
local function arena_ringue()
  local g = grid(AW, AH)
  local MAT, MAT2, LOGO, LINE = rgb(54, 30, 52), rgb(58, 33, 56), rgb(66, 37, 62), rgb(76, 42, 70)
  local CROWD, CROWD2 = rgb(22, 13, 26), rgb(34, 19, 38)
  local APRON, APRON2 = rgb(84, 26, 62), rgb(62, 18, 46)
  for y = 0, AH - 1 do
    for x = 0, AW - 1 do
      local c
      if inside(x, y) then
        -- lona com textura de tecido
        c = ((x + y) % 4 == 0 or hash(x, y) > 0.93) and MAT2 or MAT
        -- circulo central + patinha
        local dx, dy = x + 0.5 - 240, y + 0.5 - 160
        local d = math.sqrt(dx * dx + dy * dy)
        if math.abs(d - 62) < 1.6 or math.abs(d - 70) < 0.8 then c = LINE end
        if paw_mask(x, y, 240, 162, 1.7) then c = LOGO end
        -- marcas de canto
        if (math.abs(x - IX0 - 22) < 1 or math.abs(x - IX1 + 22) < 1) and (y < IY0 + 40 or y > IY1 - 40) then c = LINE end
      elseif x >= IX0 - 9 and x <= IX1 + 9 and y >= IY0 - 9 and y <= IY1 + 9 then
        -- avental do ringue
        c = ((x + y) % 6 < 3) and APRON or APRON2
      else
        -- plateia no escuro: cabecinhas de gato
        c = CROWD
        local cx, cy = (x // 12) * 12 + 6, (y // 12) * 12 + 6
        local jit = hash(x // 12, y // 12, 3)
        if jit > 0.35 then
          local dx, dy = x + 0.5 - cx, y + 0.5 - cy - 1
          if dx * dx + dy * dy <= 12 or (dy < -2 and dy > -6 and math.abs(math.abs(dx) - 2.5) < (dy + 6) * 0.45) then c = CROWD2 end
          -- olhinhos brilhando no escuro
          if jit > 0.9 and dy > -1.5 and dy < 0 and math.abs(math.abs(dx) - 1.5) < 0.6 then c = rgb(150, 120, 40) end
        end
      end
      g[y][x] = c
    end
  end
  -- cordas (rosa / branca / rosa) com sombra
  local ropes = { { 1, rgb(232, 70, 140) }, { 5, rgb(226, 214, 226) }, { 9, rgb(232, 70, 140) } }
  for _, r in ipairs(ropes) do
    local k, col = r[1], r[2]
    local dark = mix(col, rgb(0, 0, 0), 0.45)
    for x = IX0 - 2, IX1 + 2 do
      set(g, x, IY0 - 6 + k, col); set(g, x, IY0 - 5 + k, dark)
      set(g, x, IY1 + 4 - k, col); set(g, x, IY1 + 5 - k, dark)
    end
    for y = IY0 - 2, IY1 + 2 do
      set(g, IX0 - 6 + k, y, col); set(g, IX0 - 5 + k, y, dark)
      set(g, IX1 + 4 - k, y, col); set(g, IX1 + 5 - k, y, dark)
    end
  end
  -- postes de canto
  for _, p in ipairs({ { IX0 - 4, IY0 - 4 }, { IX1 + 4, IY0 - 4 }, { IX0 - 4, IY1 + 4 }, { IX1 + 4, IY1 + 4 } }) do
    for y = -6, 6 do for x = -6, 6 do
      local d = x * x + y * y
      if d <= 36 then
        local t = (x + y < -3) and rgb(255, 170, 210) or ((x + y > 4) and rgb(150, 20, 80) or rgb(230, 60, 130))
        if d > 26 then t = rgb(70, 10, 40) end
        set(g, p[1] + x, p[2] + y, t)
      end
    end end
  end
  return g
end

-- 2) LABORATORIO DO FODINHA
local function arena_lab()
  local g = grid(AW, AH)
  local P, PL, PD, SEAM = rgb(36, 40, 54), rgb(44, 49, 66), rgb(31, 34, 46), rgb(24, 26, 36)
  local WALL, WALL2 = rgb(26, 28, 38), rgb(32, 35, 48)
  local HZ1, HZ2 = rgb(150, 100, 12), rgb(30, 26, 22)
  for y = 0, AH - 1 do
    for x = 0, AW - 1 do
      local c
      if inside(x, y) then
        local px, py = (x - IX0) % 36, (y - IY0) % 36
        c = P
        if px == 0 or py == 0 then c = SEAM
        elseif px == 1 or py == 1 then c = PL
        elseif px == 35 or py == 35 then c = PD
        end
        -- rebites
        if (px == 4 or px == 31) and (py == 4 or py == 31) then c = PL end
        -- algumas placas com piso antiderrapante
        local tile = hash((x - IX0) // 36, (y - IY0) // 36, 7)
        if tile > 0.72 and px > 3 and py > 3 and px < 33 and py < 33 and ((px + py) % 6 == 0) and (px % 3 == 0) then c = PL end
        -- alvo central (o laser mira aqui)
        local dx, dy = x + 0.5 - 240, y + 0.5 - 160
        local d = math.sqrt(dx * dx + dy * dy)
        if math.abs(d - 50) < 1.2 or math.abs(d - 30) < 0.9 or math.abs(d - 70) < 0.7 then c = rgb(70, 34, 40) end
        if (math.abs(dx) < 0.9 or math.abs(dy) < 0.9) and d < 78 and d > 10 then c = rgb(70, 34, 40) end
        -- faixa zebrada de perigo na borda
        local e = math.min(x - IX0, IX1 - x, y - IY0, IY1 - y)
        if e < 5 then c = (((x + y) // 5) % 2 == 0) and HZ1 or HZ2 end
        if e == 5 then c = SEAM end
      else
        -- paredes de metal com paineis, canos e luzinhas
        c = (((x // 20) + (y // 20)) % 2 == 0) and WALL or WALL2
        if x % 20 == 0 or y % 20 == 0 then c = SEAM end
        local h = hash(x // 20, y // 20, 11)
        if h > 0.75 and x % 20 == 10 and y % 20 == 10 then
          c = (h > 0.92) and rgb(255, 60, 70) or ((h > 0.84) and rgb(255, 190, 40) or rgb(90, 230, 140))
        end
      end
      g[y][x] = c
    end
  end
  -- canos nas paredes laterais
  for _, x0 in ipairs({ 6, 462 }) do
    for y = 0, AH - 1 do
      for k = 0, 7 do
        local col = (k < 2) and rgb(120, 126, 150) or ((k < 5) and rgb(84, 90, 112) or rgb(56, 60, 78))
        if y % 40 < 3 then col = rgb(150, 110, 30) end
        set(g, x0 + k, y, col)
      end
    end
  end
  -- tubos de ensaio com liquido verde nos cantos de cima/baixo
  for _, t in ipairs({ { 40, 6 }, { 70, 6 }, { 400, 6 }, { 430, 6 }, { 40, 300 }, { 430, 300 } }) do
    for y = 0, 13 do for x = 0, 7 do
      local col
      if x == 0 or x == 7 or y == 13 then col = rgb(140, 160, 190)
      elseif y > 4 then col = (x < 3) and rgb(120, 255, 170) or rgb(60, 200, 120)
      else col = rgb(70, 80, 100) end
      set(g, t[1] + x, t[2] + y, col)
    end end
  end
  return g
end

-- 3) SALAO DO TRONO DA RAINHA
local function arena_trono()
  local g = grid(AW, AH)
  local T1, T2, VEIN = rgb(42, 27, 60), rgb(34, 21, 50), rgb(52, 36, 74)
  local RUG, RUG2, RUGD = rgb(74, 18, 58), rgb(84, 22, 66), rgb(56, 12, 44)
  local GOLDL, GOLDD = rgb(176, 128, 34), rgb(110, 74, 16)
  local WALL, WALL2 = rgb(24, 14, 34), rgb(30, 18, 42)
  for y = 0, AH - 1 do
    for x = 0, AW - 1 do
      local c
      if inside(x, y) then
        local tx, ty = (x - IX0) // 22, (y - IY0) // 22
        c = ((tx + ty) % 2 == 0) and T1 or T2
        -- veios de marmore
        local v = (x * 3 + y * 7 + math.floor(hash(tx, ty, 5) * 40)) % 37
        if v == 0 and hash(x, y) > 0.3 then c = VEIN end
        -- tapete vermelho-real no meio
        local rx = math.abs(x + 0.5 - 240)
        if rx < 34 then
          c = ((x // 2 + y // 2) % 2 == 0) and RUG or RUG2
          if rx > 29 then c = GOLDD end
          if rx > 30 and rx < 32 then c = GOLDL end
          if rx >= 32 then c = RUGD end
          -- losangos dourados no tapete
          local dy = (y - IY0) % 40
          if rx < 26 and math.abs(rx) + math.abs(dy - 20) < 6 and math.abs(rx) + math.abs(dy - 20) >= 4.5 then c = GOLDD end
        end
        -- borda dourada
        local e = math.min(x - IX0, IX1 - x, y - IY0, IY1 - y)
        if e < 3 then c = (e == 1) and GOLDL or GOLDD end
      else
        -- papel de parede com listras e flor-de-lis em patinha
        c = ((x // 6) % 2 == 0) and WALL or WALL2
        if (y % 24 == 12) and (x % 24 == 12) then c = rgb(80, 56, 30) end
      end
      g[y][x] = c
    end
  end
  -- caixas de papelao nos cantos de fora (gato ama caixa)
  for _, b in ipairs({ { 2, 2 }, { 456, 2 }, { 2, 296 }, { 456, 296 } }) do
    for y = 0, 21 do for x = 0, 21 do
      local col = rgb(150, 104, 60)
      if y < 4 then col = rgb(186, 136, 84) end
      if x > 17 then col = rgb(116, 78, 42) end
      if x == 0 or y == 0 or x == 21 or y == 21 then col = rgb(70, 44, 22) end
      if x == 10 or x == 11 then col = rgb(206, 180, 120) end
      set(g, b[1] + x, b[2] + y, col)
    end end
  end
  return g
end

local function arena(name, fn)
  return { name = name, w = AW, h = AH, frames = { { dur = 100, layers = { corpo = fn() } } }, tags = {} }
end


-------------------------------------------------------------------------------
-- FURIA (fase 2) E DERROTA - variacoes dos chefes
-------------------------------------------------------------------------------
-- troca cores por identidade (cada cor das grades e uma referencia das paletas)
local function recolor(g, pairs_list)
  local map = {}
  for _, p in ipairs(pairs_list) do
    for i = 1, #p[1] do map[p[1][i]] = p[2][i] end
  end
  for y = 0, g.h - 1 do
    for x = 0, g.w - 1 do
      local c = g[y][x]
      if c and map[c] then g[y][x] = map[c] end
    end
  end
  return g
end

local function clear(g, x0, y0, x1, y1)
  for y = y0, y1 do for x = x0, x1 do set(g, x, y, nil) end end
end

local function fill(g, x0, y0, x1, y1, c)
  for y = y0, y1 do for x = x0, x1 do set(g, x, y, c) end end
end

local RAGEPINK = {
  rgb(92, 8, 22), rgb(156, 16, 38), rgb(206, 30, 52), rgb(244, 58, 70),
  rgb(255, 118, 118), rgb(255, 178, 170), rgb(255, 232, 226),
}
local RAGEAMBER = {
  rgb(100, 30, 8), rgb(172, 58, 10), rgb(226, 92, 20), rgb(255, 128, 36),
  rgb(255, 172, 88), rgb(255, 214, 158), rgb(255, 242, 222),
}
local RAGEPURPLE = {
  rgb(70, 6, 58), rgb(122, 14, 108), rgb(172, 28, 158), rgb(216, 58, 198),
  rgb(240, 128, 228), rgb(255, 194, 244), rgb(255, 236, 252),
}
local RED_EYE = rgb(255, 64, 64)
local MAGENTA_EYE = rgb(255, 92, 214)
local STEAM1, STEAM2 = rgb(240, 232, 240), rgb(188, 176, 196)
local VEIN = rgb(255, 40, 64)
local STAR = rgb(255, 230, 90)

-- simbolo de raiva (veia de anime)
local function anger(g, x, y)
  stamp(g, x, y, { "rr rr", "r   r", "     ", "r   r", "rr rr" }, { r = VEIN })
end

local function steam(g, x, y, f)
  local r = ({ 2.6, 2.2, 1.8, 1.2 })[(f % 4) + 1]
  local yy = y - (f % 4) * 2
  for dy = -3, 3 do for dx = -3, 3 do
    local d = dx * dx + dy * dy
    if d <= r * r then set(g, x + dx, yy + dy, (dx + dy < 0) and STEAM1 or STEAM2) end
  end end
end

local function x_eye(g, x, y, col)
  stamp(g, x, y, { "c  c", " cc ", " cc ", "c  c" }, { c = col })
end

local function dizzy(g, cx, cy, f)
  for i = 0, 2 do
    local a = f * 0.9 + i * (math.pi * 2 / 3)
    local x = math.floor(cx + math.cos(a) * 12 + 0.5)
    local y = math.floor(cy + math.sin(a) * 3 + 0.5)
    stamp(g, x - 1, y - 1, { " s ", "sss", " s " }, { s = STAR })
  end
end

-- FODAO -----------------------------------------------------------------------
local function fodao_rage_body(f, jumping)
  return recolor(fodao_body(f, jumping), { { PINK, RAGEPINK } })
end

local function fodao_rage_face(f, jumping)
  local g = recolor(fodao_face(jumping), { { EYE_Y, { RED_EYE, EYE_Y[2], EYE_Y[3] } }, { PINK, RAGEPINK } })
  if not jumping then
    clear(g, 24, 24, 35, 28)
    stamp(g, 24, 24, {
      "     nn     ",
      "  kkkkkkkk  ",
      "  kwkwkwkk  ",
      "  kkkkkkkk  ",
    }, { n = RAGEPINK[2], k = RAGEPINK[1], w = WHITE })
  end
  anger(g, 37, 9)
  steam(g, 12, 9, f)
  steam(g, 48, 9, f + 2)
  return g
end

local function fodao_defeat_face()
  local g = fodao_face(false)
  fill(g, 18, 17, 24, 22, MASK); fill(g, 35, 17, 41, 22, MASK)
  x_eye(g, 19, 18, WHITE); x_eye(g, 37, 18, WHITE)
  clear(g, 24, 24, 35, 28)
  stamp(g, 24, 24, {
    "     nn     ",
    "  k k  k k  ",
    "   k kk k   ",
    "      tt    ",
    "      tt    ",
  }, { n = PINK[2], k = PINK[1], t = FACE.t })
  dizzy(g, 30, 5, 0)
  return g
end

local function make_prism2()
  local frames = {}
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 140, layers = { corpo = fodao_body(i, false), rosto = fodao_face(false) } }
  end
  frames[#frames + 1] = { dur = 140, layers = { corpo = fodao_body(1, true), rosto = fodao_face(true) } }
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 90, layers = { corpo = fodao_rage_body(i, false), rosto = fodao_rage_face(i, false) } }
  end
  frames[#frames + 1] = { dur = 140, layers = { corpo = fodao_rage_body(1, true), rosto = fodao_rage_face(1, true) } }
  frames[#frames + 1] = { dur = 200, layers = { corpo = fodao_body(0, false), rosto = fodao_defeat_face() } }
  return {
    name = "boss_prisma", w = 60, h = 60, frames = frames,
    tags = {
      { name = "parado", from = 1, to = 4 }, { name = "pulo", from = 5, to = 5 },
      { name = "furia", from = 6, to = 9 }, { name = "pulo_furia", from = 10, to = 10 },
      { name = "derrota", from = 11, to = 11 },
    },
  }
end

-- FODINHA ---------------------------------------------------------------------
local function fodinha_rage_body(f)
  local g = recolor(fodinha_body(f), { { AMBER, RAGEAMBER }, { PINK, RAGEPINK } })
  -- luzes da capsula todas vermelhas e piscando
  for x = 8, 47 do
    if (x + f) % 3 == 0 then set(g, x, 34, LASER[3]) end
  end
  -- jato maior
  for i = 0, 3 do
    set(g, 26, 52 + i, LASER[3]); set(g, 29, 52 + i, LASER[3])
  end
  return g
end

local function fodinha_rage_face(f)
  local g = recolor(fodinha_face(f), { { EYE_Y, { EYE_Y[1], RED_EYE, EYE_Y[3] } }, { AMBER, RAGEAMBER }, { PINK, RAGEPINK } })
  -- brilho em volta do monoculo
  local glow = { 255, 60, 60, (f % 2 == 0) and 120 or 70 }
  for y = 8, 26 do for x = 25, 42 do
    local dx, dy = x + 0.5 - 33.5, y + 0.5 - 17.5
    local d = math.sqrt(dx * dx + dy * dy)
    if d > 4.6 and d < 6.6 and not g[y][x] then g[y][x] = glow end
  end end
  -- dentes cerrados
  fill(g, 25, 24, 31, 24, RAGEAMBER[1])
  stamp(g, 25, 24, { "kwkwkwk", "kkkkkkk" }, { k = RAGEAMBER[1], w = WHITE })
  -- gota de suor
  stamp(g, 15, 9 + (f % 2), { " b ", "bbb", "bwb", " b " }, { b = rgb(120, 200, 255), w = WHITE })
  return g
end

local function fodinha_defeat_face()
  local g = fodinha_face(0)
  -- monoculo rachado
  for y = 15, 19 do for x = 30, 36 do
    if g[y][x] then g[y][x] = METAL[2] end
  end end
  for i = 0, 4 do set(g, 31 + i, 15 + i, WHITE) end
  set(g, 34, 16, WHITE); set(g, 35, 16, WHITE)
  -- olho esquerdo em X
  clear(g, 17, 17, 23, 20)
  x_eye(g, 18, 17, AMBER[1])
  -- boca tremida
  clear(g, 24, 24, 31, 25)
  stamp(g, 24, 24, { "k k k k", " k k k " }, { k = AMBER[1] })
  dizzy(g, 28, 6, 1)
  return g
end

local function make_orbital2()
  local frames = {}
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 120, layers = { corpo = fodinha_body(i), rosto = fodinha_face(i) } }
  end
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 80, layers = { corpo = fodinha_rage_body(i), rosto = fodinha_rage_face(i) } }
  end
  frames[#frames + 1] = { dur = 200, layers = { corpo = fodinha_body(0), rosto = fodinha_defeat_face() } }
  return {
    name = "boss_orbital", w = 56, h = 56, frames = frames,
    tags = {
      { name = "parado", from = 1, to = 4 }, { name = "furia", from = 5, to = 8 },
      { name = "derrota", from = 9, to = 9 },
    },
  }
end

-- PODER FEMININO --------------------------------------------------------------
local function queen_rage_body(pulse, f)
  local g = recolor(queen_body(pulse, f), { { PURPLE, RAGEPURPLE } })
  -- aura magica extra
  for i = 0, 7 do
    local a = f * 0.4 + i * (math.pi / 4)
    local x = math.floor(36 + math.cos(a) * 33 + 0.5)
    local y = math.floor(40 + math.sin(a) * 30 + 0.5)
    if not get(g, x, y) then
      set(g, x, y, RAGEPURPLE[6]); set(g, x + 1, y, RAGEPURPLE[4]); set(g, x, y + 1, RAGEPURPLE[4])
    end
  end
  return g
end

local function queen_rage_face(f)
  local g = queen_face(f, false)
  -- olhos acesos em magenta (pupila tambem brilha)
  recolor(g, { { EYE_Y, { MAGENTA_EYE, MAGENTA_EYE, MAGENTA_EYE } }, { { MASK }, { rgb(255, 228, 250) } } })
  -- rosnado com presas
  clear(g, 31, 28, 41, 31)
  stamp(g, 31, 28, {
    "    nn    ",
    "  kkkkkk  ",
    "  kw  wk  ",
    "   kkkk   ",
  }, { n = PINK[4], k = BLACKCAT[1], w = WHITE })
  anger(g, 44, 14)
  return g
end

local function queen_defeat_face()
  local g = queen_face(1, false)
  clear(g, 24, 21, 47, 27)
  x_eye(g, 27, 22, BLACKCAT[7]); x_eye(g, 41, 22, BLACKCAT[7])
  clear(g, 31, 30, 41, 31)
  stamp(g, 31, 30, { "  k k k k ", "   k k k  " }, { k = BLACKCAT[1] })
  dizzy(g, 36, 3, 2)
  return g
end

local function make_core2()
  local frames = {}
  local pulses = { 0, 1, 2, 1 }
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 120, layers = { corpo = queen_body(pulses[i + 1], i), rosto = queen_face(i, false) } }
  end
  frames[#frames + 1] = { dur = 120, layers = { corpo = queen_body(1, 1), rosto = queen_face(1, true) } }
  for i = 0, 3 do
    frames[#frames + 1] = { dur = 90, layers = { corpo = queen_rage_body(pulses[i + 1], i), rosto = queen_rage_face(i) } }
  end
  frames[#frames + 1] = { dur = 200, layers = { corpo = queen_body(0, 0), rosto = queen_defeat_face() } }
  return {
    name = "boss_nucleo", w = 72, h = 72, frames = frames,
    tags = {
      { name = "parado", from = 1, to = 4 }, { name = "piscar", from = 5, to = 5 },
      { name = "furia", from = 6, to = 9 }, { name = "derrota", from = 10, to = 10 },
    },
  }
end

function A.extras()
  return {
    make_peixe(), make_laser(), make_novelo(),
    arena("cenario_ringue", arena_ringue),
    arena("cenario_laboratorio", arena_lab),
    arena("cenario_trono", arena_trono),
  }
end


-------------------------------------------------------------------------------
-- HUD, EFEITOS E OBJETOS DE CENARIO (direcao de arte v2)
-------------------------------------------------------------------------------
local function one(name, w, h, g)
  return { name = name, w = w, h = h, frames = { { dur = 100, layers = { corpo = g } } }, tags = {} }
end

local function anim(name, w, h, grids, dur, tagname)
  local frames = {}
  for _, g in ipairs(grids) do frames[#frames + 1] = { dur = dur, layers = { corpo = g } } end
  return { name = name, w = w, h = h, frames = frames, tags = { { name = tagname or "anim", from = 1, to = #grids } } }
end

local function disc(g, cx, cy, r, colfn)
  for y = math.floor(cy - r - 1), math.ceil(cy + r + 1) do
    for x = math.floor(cx - r - 1), math.ceil(cx + r + 1) do
      local dx, dy = x + 0.5 - cx, y + 0.5 - cy
      local d = math.sqrt(dx * dx + dy * dy)
      if d <= r then
        local c = colfn(dx, dy, d)
        if c then set(g, x, y, c) end
      end
    end
  end
end

-- CORACOES DO HUD (cheio / meio / vazio) ----------------------------------------
local HEART = {
  "..kkk.kkk..",
  ".krrrkrrrk.",
  "krwwrrrrrrk",
  "krwrrrrrrdk",
  "krrrrrrrrdk",
  ".krrrrrrdk.",
  "..krrrrdk..",
  "...krrdk...",
  "....kdk....",
  ".....k.....",
}
local function heart(kind)
  local g = grid(11, 10)
  local full = { k = rgb(70, 10, 30), r = rgb(236, 44, 66), d = rgb(168, 22, 46), w = rgb(255, 214, 220) }
  local empty = { k = rgb(40, 30, 52), r = rgb(64, 54, 82), d = rgb(52, 44, 68), w = rgb(84, 74, 104) }
  for j, row in ipairs(HEART) do
    for i = 1, #row do
      local ch = row:sub(i, i)
      if ch ~= "." then
        local pal = full
        if kind == "vazio" or (kind == "meio" and i > 6) then pal = empty end
        if ch == "k" then pal = (kind == "vazio") and empty or full end
        g[j - 1][i - 1] = pal[ch]
      end
    end
  end
  return g
end

-- POEIRA (aterrissagem / pulo) ---------------------------------------------------
local function puff_frame(f)
  local g = grid(16, 16)
  local L, M, D = rgb(226, 216, 228), rgb(178, 166, 186), rgb(120, 110, 132)
  local r = ({ 3.0, 4.6, 5.6, 5.2, 3.8 })[f + 1]
  local spread = ({ 1.5, 3.0, 4.2, 5.0, 5.6 })[f + 1]
  local blobs = { { 8 - spread, 9 }, { 8 + spread, 9 }, { 8, 8 - spread * 0.4 } }
  for _, b in ipairs(blobs) do
    disc(g, b[1], b[2], r * ((b[2] < 8) and 0.8 or 1.0), function(dx, dy, d)
      if f >= 3 and (d > r * 0.75) and ((math.floor(dx * 3 + dy * 2) % 3) == 0) then return nil end
      if dx + dy < -r * 0.4 then return L elseif dx + dy > r * 0.5 then return D end
      return M
    end)
  end
  if f == 4 then
    for y = 0, 15 do for x = 0, 15 do if g[y][x] and (x + y) % 2 == 0 then g[y][x] = nil end end end
  end
  return outline(g, rgb(90, 80, 104))
end

-- EXPLOSAO (morte de chefe / rato) -------------------------------------------------
local function boom_frame(f)
  local g = grid(32, 32)
  local W1, Y1, O1, O2, R1 = rgb(255, 255, 240), rgb(255, 230, 110), rgb(255, 160, 40), rgb(230, 90, 30), rgb(150, 40, 30)
  local S1, S2, S3 = rgb(150, 140, 160), rgb(110, 100, 124), rgb(74, 66, 88)
  if f == 0 then
    disc(g, 16, 16, 6, function(dx, dy, d) return d < 4 and W1 or Y1 end)
  elseif f == 1 then
    disc(g, 16, 16, 10, function(dx, dy, d) return d < 5 and W1 or (d < 8 and Y1 or O1) end)
  elseif f == 2 then
    disc(g, 16, 16, 13, function(dx, dy, d)
      local n = hash(math.floor(dx + 16), math.floor(dy + 16), 9)
      if d < 5 then return Y1 elseif d < 9 then return (n > 0.7) and Y1 or O1 elseif d < 12 then return O2 end
      return R1
    end)
  elseif f == 3 then
    disc(g, 16, 16, 14, function(dx, dy, d)
      local n = hash(math.floor(dx + 16), math.floor(dy + 16), 4)
      if d < 6 then return (n > 0.5) and S1 or S2 end
      if d < 10 then return (n > 0.35) and O1 or O2 end
      if n > 0.55 then return nil end
      return R1
    end)
  else
    -- fumaca se espalhando em bolinhas
    local k = f - 4
    local ring = 9 + k * 3
    local rr = 4.5 - k * 1.2
    for i = 0, 7 do
      local a = i * (math.pi / 4) + k * 0.3
      local cx, cy = 16 + math.cos(a) * ring * 0.8, 16 + math.sin(a) * ring * 0.8
      disc(g, cx, cy, rr, function(dx, dy) return (dx + dy < 0) and S1 or ((dx + dy > 1.5) and S3 or S2) end)
    end
  end
  return outline(g, (f <= 2) and R1 or rgb(56, 48, 70))
end

-- FAISCA DE IMPACTO ----------------------------------------------------------------
local function spark_frame(f)
  local g = grid(13, 13)
  local W1, Y1, O1 = rgb(255, 255, 255), rgb(255, 236, 140), rgb(255, 170, 60)
  local c = 6
  if f == 0 then
    for i = -5, 5 do set(g, c + i, c, (math.abs(i) < 3) and W1 or Y1); set(g, c, c + i, (math.abs(i) < 3) and W1 or Y1) end
    set(g, c - 1, c - 1, W1); set(g, c + 1, c - 1, W1); set(g, c - 1, c + 1, W1); set(g, c + 1, c + 1, W1)
  elseif f == 1 then
    for i = 2, 5 do
      set(g, c + i, c + i, Y1); set(g, c - i, c - i, Y1); set(g, c + i, c - i, Y1); set(g, c - i, c + i, Y1)
    end
    for i = 3, 4 do set(g, c + i, c, O1); set(g, c - i, c, O1); set(g, c, c + i, O1); set(g, c, c - i, O1) end
  else
    for _, p in ipairs({ { 5, 0 }, { -5, 0 }, { 0, 5 }, { 0, -5 }, { 4, 4 }, { -4, -4 }, { 4, -4 }, { -4, 4 } }) do
      set(g, c + p[1], c + p[2], O1)
    end
  end
  return g
end

-- BRILHINHO (estrela que pisca) -----------------------------------------------------
local function twinkle_frame(f)
  local g = grid(7, 7)
  local W1, C1 = rgb(255, 255, 255), rgb(255, 236, 170)
  local len = ({ 1, 2, 3, 2 })[f + 1]
  set(g, 3, 3, W1)
  for i = 1, len do
    local col = (i == len) and C1 or W1
    set(g, 3 + i, 3, col); set(g, 3 - i, 3, col); set(g, 3, 3 + i, col); set(g, 3, 3 - i, col)
  end
  return g
end

-- VELA (salao da rainha) ---------------------------------------------------------------
local function candle_frame(f)
  local g = grid(10, 22)
  local WAX, WAX2, WAX3 = rgb(250, 238, 214), rgb(226, 206, 176), rgb(186, 160, 128)
  for y = 9, 18 do for x = 3, 6 do g[y][x] = (x == 3) and WAX or ((x == 6) and WAX3 or WAX2) end end
  set(g, 4, 10, WAX); set(g, 4, 11, WAX); set(g, 6, 9, WAX); set(g, 6, 10, WAX2) -- pingos
  -- castical dourado
  for x = 1, 8 do set(g, x, 19, GOLD[(x < 4) and 5 or 3]); set(g, x, 20, GOLD[2]) end
  for x = 3, 6 do set(g, x, 21, GOLD[2]) end
  g = outline(g, rgb(60, 36, 20))
  -- pavio e chama
  set(g, 5, 8, rgb(50, 30, 30))
  local sway = ({ 0, 1, 0, -1 })[f + 1]
  local h = ({ 6, 7, 6, 5 })[f + 1]
  for i = 0, h - 1 do
    local yy = 7 - i
    local w = (i < 2) and 1 or ((i < h - 2) and 1 or 0)
    local xs = 5 + ((i > 2) and sway or 0)
    for dx = -w, w do
      local col = GOLD[6]
      if i == 0 or math.abs(dx) == w and w > 0 then col = rgb(255, 150, 40) end
      if i >= h - 2 then col = rgb(255, 110, 40) end
      set(g, xs + dx, yy, col)
    end
  end
  set(g, 5, 6, WHITE)
  return g
end

-- ALMOFADA DE VELUDO (pedestal dos power-ups) -------------------------------------------
local function cushion()
  local W, H = 34, 18
  local g = grid(W, H)
  local V = { rgb(70, 10, 40), rgb(110, 20, 60), rgb(150, 34, 84), rgb(190, 56, 110), rgb(222, 100, 150) }
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local dx, dy = (x + 0.5 - 17) / 15.5, (y + 0.5 - 8.5) / 6.8
      -- forma de almofada "estufada" (superelipse)
      if math.abs(dx) ^ 3 + math.abs(dy) ^ 3 <= 1 then
        local l = -dx * 0.4 - dy * 0.8
        local tone = (l > 0.5) and 5 or ((l > 0.1) and 4 or ((l > -0.35) and 3 or 2))
        g[y][x] = V[tone]
      end
    end
  end
  -- costura e botao central
  for x = 6, 27 do if x % 2 == 0 then set(g, x, 9, V[5]) end end
  stamp(g, 15, 7, { " kk ", "kbbk", " kk " }, { k = V[1], b = GOLD[5] })
  g = outline(g, V[1])
  -- borlas douradas nos cantos
  for _, p in ipairs({ { 1, 12 }, { 30, 12 }, { 1, 2 }, { 30, 2 } }) do
    stamp(g, p[1], p[2], { "a ", "aa", "bb", "b " }, { a = GOLD[5], b = GOLD[3] })
  end
  return g
end

-- PAINEIS DO HUD (480 x 24 em cima, 480 x 20 embaixo; o jogo amplia 2x) ------------------
local HUD1, HUD2, HUD3 = rgb(16, 12, 26), rgb(24, 18, 38), rgb(34, 26, 52)
local TRIM1, TRIM2 = rgb(196, 146, 48), rgb(120, 82, 22)
local function hud_top()
  local W, H = 480, 24
  local g = grid(W, H)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local c = (y < 2) and HUD3 or (((x // 2 + y // 2) % 2 == 0) and HUD1 or HUD2)
      if y >= H - 3 then c = TRIM2 end
      if y == H - 2 then c = TRIM1 end
      if y == H - 1 then c = rgb(8, 6, 14) end
      g[y][x] = c
    end
  end
  -- ornamentos de patinha nas pontas da faixa dourada
  for _, cx in ipairs({ 6, 473 }) do
    stamp(g, cx - 3, H - 6, { " a a ", "a   a", " aaa ", "aaaaa" }, { a = TRIM1 })
  end
  return g
end

local function hud_bottom()
  local W, H = 480, 20
  local g = grid(W, H)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local c = ((x // 2 + y // 2) % 2 == 0) and HUD1 or HUD2
      if y <= 2 then c = TRIM2 end
      if y == 1 then c = TRIM1 end
      if y == 0 then c = rgb(8, 6, 14) end
      g[y][x] = c
    end
  end
  return g
end

-- MOLDURA DA BARRA DE VIDA DO CHEFE (196 x 12; miolo vazio em x 3..192, y 3..8) ------------
local function boss_bar()
  local W, H = 196, 12
  local g = grid(W, H)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local inner = x >= 3 and x <= 192 and y >= 3 and y <= 8
      if not inner then
        local c = rgb(28, 20, 40)
        if y == 0 or y == H - 1 or x == 0 or x == W - 1 then c = rgb(8, 6, 14)
        elseif y == 1 or x == 1 then c = TRIM1
        elseif y == H - 2 or x == W - 2 then c = TRIM2 end
        g[y][x] = c
      end
    end
  end
  -- marquinha da metade (onde comeca a furia)
  for y = 0, 2 do set(g, 97, y, rgb(255, 240, 200)); set(g, 98, y, rgb(255, 240, 200)) end
  for y = 9, 11 do set(g, 97, y, rgb(255, 240, 200)); set(g, 98, y, rgb(255, 240, 200)) end
  return g
end

-- MEDALHAO DO RETRATO DO CHEFE (22 x 22, miolo 18x18 em 2..19) -----------------------------
local function portrait_frame()
  local g = grid(22, 22)
  for y = 0, 21 do
    for x = 0, 21 do
      local inner = x >= 2 and x <= 19 and y >= 2 and y <= 19
      if not inner then
        local c = TRIM1
        if x == 0 or y == 0 or x == 21 or y == 21 then c = rgb(8, 6, 14)
        elseif x == 20 or y == 20 then c = TRIM2 end
        -- cantos chanfrados
        if (x <= 1 or x >= 20) and (y <= 1 or y >= 20) then c = nil end
        g[y][x] = c
      end
    end
  end
  return g
end

-- FUNDO DO RETRATO (cor de cada chefe sai do codigo; aqui so a textura) ---------------------
local function portrait_bg()
  local g = grid(18, 18)
  for y = 0, 17 do for x = 0, 17 do
    g[y][x] = ((x + y) % 4 < 2) and rgb(40, 30, 58) or rgb(32, 24, 48)
  end end
  return g
end

-- ICONES DE ONDA (patinha cheia / vazia / caveira de peixe pra chefe derrotado) -------------
local function wave_icon(kind)
  local g = grid(9, 9)
  local col = (kind == "atual") and rgb(255, 210, 80) or ((kind == "vencida") and rgb(110, 220, 160) or rgb(70, 62, 92))
  stamp(g, 0, 0, {
    " a  a  a ",
    " a  a  a ",
    "         ",
    "  aaaaa  ",
    " aaaaaaa ",
    " aaaaaaa ",
    "  aaaaa  ",
  }, { a = col })
  if kind == "vencida" then
    stamp(g, 1, 3, { "w     w", " w   w ", "  w w  ", "   w   " }, { w = rgb(255, 255, 255) })
  end
  return outline(g, rgb(10, 8, 18))
end

function A.fx()
  local puffs, booms, sparks, twinkles, candles = {}, {}, {}, {}, {}
  for f = 0, 4 do puffs[#puffs + 1] = puff_frame(f) end
  for f = 0, 6 do booms[#booms + 1] = boom_frame(f) end
  for f = 0, 2 do sparks[#sparks + 1] = spark_frame(f) end
  for f = 0, 3 do twinkles[#twinkles + 1] = twinkle_frame(f) end
  for f = 0, 3 do candles[#candles + 1] = candle_frame(f) end
  return {
    anim("hud_coracao", 11, 10, { heart("cheio"), heart("meio"), heart("vazio") }, 100, "cheio_meio_vazio"),
    anim("fx_poeira", 16, 16, puffs, 60),
    anim("fx_explosao", 32, 32, booms, 60),
    anim("fx_impacto", 13, 13, sparks, 50),
    anim("fx_brilho", 7, 7, twinkles, 90),
    anim("prop_vela", 10, 22, candles, 110),
    one("prop_almofada", 34, 18, cushion()),
    one("hud_topo", 480, 24, hud_top()),
    one("hud_base", 480, 20, hud_bottom()),
    one("hud_barra_chefe", 196, 12, boss_bar()),
    one("hud_retrato", 22, 22, portrait_frame()),
    one("hud_retrato_fundo", 18, 18, portrait_bg()),
    anim("hud_onda", 9, 9, { wave_icon("futura"), wave_icon("atual"), wave_icon("vencida") }, 100, "futura_atual_vencida"),
  }
end


-------------------------------------------------------------------------------
-- RATOS DE CORDA (drones do cientista) - v2
-- brinquedo de lata: corpo em gota, orelha grande, chave de corda nas costas,
-- rodinhas, rabo de fio com plugue e olho de LED. Olhando pra ESQUERDA.
-------------------------------------------------------------------------------
local TIN = {
  rgb(36, 38, 58),    -- 1 contorno
  rgb(70, 76, 102),   -- 2
  rgb(108, 116, 146), -- 3
  rgb(150, 160, 188), -- 4
  rgb(196, 204, 226), -- 5
  rgb(236, 240, 250), -- 6
}

local function tin_tone(l)
  if l > 0.78 then return 6 elseif l > 0.5 then return 5 elseif l > 0.15 then return 4
  elseif l > -0.2 then return 3 else return 2 end
end

local function mouse2_frame(f, attack)
  local W, H = 28, 24
  local g = grid(W, H)
  local lean = attack and -1 or 0           -- no ataque o corpo vai pra frente
  local bob = (f % 2 == 0) and 0 or 1       -- sacode no ritmo das rodinhas

  -- RABO de fio (atras de tudo), balancando, com plugue dourado na ponta
  local tail = grid(W, H)
  local wig = ({ 0, 1, 0, -1 })[f + 1]
  local pts = {}
  for i = 0, 8 do
    local t = i / 8
    pts[#pts + 1] = { 21 + t * 5, 14 + bob - t * 4 + math.sin(t * 5 + f * 1.6) * (attack and 1.6 or 1.0) + wig * t }
  end
  for _, p in ipairs(pts) do set(tail, math.floor(p[1] + 0.5), math.floor(p[2] + 0.5), TIN[2]) end
  local e = pts[#pts]
  local ex, ey = math.floor(e[1] + 0.5), math.floor(e[2] + 0.5)
  set(tail, ex, ey - 1, GOLD[5]); set(tail, ex, ey, GOLD[3]); set(tail, ex - 1, ey - 1, GOLD[4])
  over(g, tail)

  -- RODINHAS (raios giram)
  for _, wx in ipairs({ 9, 19 }) do
    local wh = grid(W, H)
    disc(wh, wx + lean, 20.5, 2.6, function(dx, dy, d)
      if d > 1.6 then return TIN[2] end
      return TIN[4]
    end)
    -- raio girando
    local a = f * (math.pi / 4)
    set(wh, math.floor(wx + lean + math.cos(a) * 1.2 + 0.5), math.floor(20.5 + math.sin(a) * 1.2), TIN[1])
    set(wh, math.floor(wx + lean), 20, TIN[5])
    over(g, outline(wh, TIN[1]))
  end

  -- CORPO: cupula nas costas + focinho em cone pra esquerda
  local body = grid(W, H)
  local cx, cy = 16 + lean, 14 + bob
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local dx, dy = x + 0.5 - cx, y + 0.5 - cy
      local inside = (dx * dx) / (9.5 * 9.5) + (dy * dy) / (7.2 * 7.2) <= 1 and dy < 5.5
      -- cone do focinho: de (cx-4, topo..base) ate a ponta (4, cy+1.5)
      local tip_x, tip_y = 3.5 + lean, cy + 1.5
      if x + 0.5 < cx - 3 and x + 0.5 > tip_x then
        local t = ((x + 0.5) - tip_x) / ((cx - 3) - tip_x)
        local top = tip_y - t * 6.0
        local bot = tip_y + t * 3.0
        if y + 0.5 >= top and y + 0.5 <= bot then inside = true end
      end
      if inside then
        local l = light(dx, dy + 1, 10, 8)
        body[y][x] = TIN[tin_tone(l)]
        if dy > 3.5 then body[y][x] = TIN[2] end -- barriga/sombra embaixo
      end
    end
  end
  -- plaquinha ambar com parafuso (cara de brinquedo de lata)
  disc(body, cx + 2.5, cy + 0.5, 2.6, function(dx, dy, d)
    if d < 0.9 then return AMBER[1] end
    return (dx + dy < 0) and AMBER[5] or AMBER[3]
  end)
  set(body, math.floor(cx + 2), math.floor(cy), AMBER[1])
  -- costura de rebites na linha do corpo
  for x = math.floor(cx - 6), math.floor(cx + 7), 3 do
    local yy = math.floor(cy - 4.5 + math.abs(x - cx) * 0.18)
    if body[yy] and body[yy][x] then body[yy][x] = TIN[3] end
  end
  over(g, outline(body, TIN[1]))

  -- ORELHA grande redonda
  local ear = grid(W, H)
  disc(ear, 13 + lean, 6 + bob, 4.2, function(dx, dy, d)
    if d < 2.1 then return PINK[5] end
    return (dx + dy < 0) and TIN[5] or TIN[3]
  end)
  over(g, outline(ear, TIN[1]))

  -- CHAVE DE CORDA nas costas (gira: larga, media, de lado, media)
  local key = grid(W, H)
  local kx, ky = 21 + lean, 4 + bob
  set(key, kx, ky + 2, GOLD[2]); set(key, kx, ky + 3, GOLD[2])
  local shape = ({ { "aa.aa", "abcba", "aa.aa" }, { ".a.a.", ".bcb.", ".a.a." }, { "..a..", "..c..", "..a.." }, { ".a.a.", ".bcb.", ".a.a." } })[f + 1]
  stamp(key, kx - 2, ky - 1, shape, { a = GOLD[5], b = GOLD[4], c = GOLD[3] })
  over(g, outline(key, GOLD[1]))

  -- FOCINHO, BIGODES DE ARAME, OLHO DE LED
  local nx, ny = 4 + lean, 14 + bob
  set(g, nx, ny, PINK[4]); set(g, nx - 1, ny, PINK[3]); set(g, nx, ny - 1, PINK[5])
  for i = 1, 4 do set(g, nx - i, ny - 1 - math.floor(i / 2), TIN[4]); set(g, nx - i, ny + 1 + math.floor(i / 3), TIN[4]) end
  local ex2, ey2 = 8 + lean, 11 + bob
  if attack then
    -- sobrancelha brava + olho vermelho aceso + boca com dentes
    stamp(g, ex2 - 1, ey2 - 2, {
      "kk...",
      ".kkk.",
      "krrwk",
      "krrrk",
      ".kkk.",
    }, { k = TIN[1], r = LASER[3], w = WHITE })
    stamp(g, 5 + lean, 16 + bob, { "kkkkk", "kwkwk" }, { k = TIN[1], w = WHITE })
  else
    stamp(g, ex2 - 1, ey2 - 1, {
      ".kkk.",
      "krrwk",
      "krrrk",
      ".kkk.",
    }, { k = TIN[1], r = LASER[2], w = LASER[4] })
  end
  -- faiscas saindo da chave quando ataca
  if attack then
    local sp = ({ { 25, 2 }, { 26, 5 }, { 24, 1 }, { 26, 3 } })[f + 1]
    set(g, sp[1], sp[2], GOLD[6]); set(g, sp[1] - 1, sp[2] + 1, GOLD[5])
    set(g, 27, 12 + ((f % 2 == 0) and 1 or -1), GOLD[6])
  end
  return g
end

local function make_drone2()
  local frames = {}
  for f = 0, 3 do frames[#frames + 1] = { dur = 80, layers = { corpo = mouse2_frame(f, false) } } end
  for f = 0, 3 do frames[#frames + 1] = { dur = 50, layers = { corpo = mouse2_frame(f, true) } } end
  return {
    name = "drone", w = 28, h = 24, frames = frames,
    tags = { { name = "orbitando", from = 1, to = 4 }, { name = "atacando", from = 5, to = 8 } },
  }
end


-------------------------------------------------------------------------------
-- CHEFES NOVOS: 4) SOMBRA, O GATO NINJA   5) MADAME ASPIRINA, A DUQUESA DA FAXINA
-------------------------------------------------------------------------------
local NAVY = {
  rgb(8, 10, 22), rgb(20, 24, 42), rgb(32, 38, 62), rgb(46, 54, 84),
  rgb(66, 76, 110), rgb(94, 106, 144), rgb(138, 150, 188),
}
local TEAL = {
  rgb(0, 54, 58), rgb(0, 104, 104), rgb(0, 156, 146), rgb(24, 208, 188),
  rgb(110, 240, 220), rgb(190, 255, 240), rgb(236, 255, 250),
}
local SKY = {
  rgb(18, 36, 76), rgb(36, 74, 134), rgb(64, 114, 186), rgb(104, 164, 238),
  rgb(156, 202, 255), rgb(212, 232, 255), rgb(244, 250, 255),
}
local FLUFF = {
  rgb(96, 84, 120), rgb(150, 140, 176), rgb(190, 184, 214), rgb(222, 218, 240),
  rgb(240, 238, 250), rgb(252, 250, 255), rgb(255, 255, 255),
}
local NIGHT_EYE = rgb(255, 236, 120)

-- ======================= 4) SOMBRA =======================
local function ninja_body(f, pose, rage)
  local W, H = 60, 60
  local g = grid(W, H)
  local acc = rage and { rgb(120, 10, 20), rgb(190, 20, 40), rgb(230, 40, 60), rgb(255, 70, 80), rgb(255, 140, 140), rgb(255, 200, 200), WHITE } or TEAL

  -- faixa da bandana esvoacando (atras de tudo)
  local band = grid(W, H)
  local pts = {}
  for i = 0, 12 do
    local t = i / 12
    local amp = rage and 3.2 or 2.0
    pts[#pts + 1] = { 41 + t * 16, 14 + t * 6 + math.sin(t * 6 + f * 1.7) * amp * t }
  end
  blob_line(band, pts, 1.6, function(i) return (i % 3 == 0) and acc[3] or acc[4] end)
  local pts2 = {}
  for i = 0, 9 do
    local t = i / 9
    pts2[#pts2 + 1] = { 41 + t * 12, 16 + t * 10 + math.sin(t * 6 + f * 1.7 + 1.5) * 1.8 * t }
  end
  blob_line(band, pts2, 1.3, function() return acc[3] end)
  over(g, outline(band, acc[1]))

  -- rabo com ponta colorida
  local tail = grid(W, H)
  local tp = {}
  local sway = ({ 0, 1.5, 2.5, 1.5 })[(f % 4) + 1]
  for i = 0, 11 do
    local t = i / 11
    tp[#tp + 1] = { 16 - t * 10 - sway * t, 48 - t * 18 + math.sin(t * 3) * 2 }
  end
  blob_line(tail, tp, 2.3, function(i) return (i >= 10) and acc[4] or ((i % 4 < 2) and NAVY[4] or NAVY[3]) end)
  over(g, outline(tail, NAVY[1]))

  -- cabo da katana atras do ombro
  local kat = grid(W, H)
  for i = 0, 10 do
    local x, y = 37 + i * 0.9, 27 - i
    set(kat, math.floor(x), math.floor(y), (i % 2 == 0) and rgb(120, 70, 40) or rgb(170, 110, 60))
    set(kat, math.floor(x) + 1, math.floor(y), rgb(90, 50, 30))
  end
  stamp(kat, 35, 26, { "aaaa", "abba" }, { a = GOLD[4], b = GOLD[2] })
  over(g, outline(kat, NAVY[1]))

  -- pes
  for _, fx in ipairs({ 22, 38 }) do over(g, outline(ell(W, H, fx, 55, 5.5, 3, NAVY), NAVY[1])) end
  -- corpo agachado + faixa da cintura
  local body = ell(W, H, 30, 43, 14, 11.5, NAVY)
  for x = 0, W - 1 do
    for y = 41, 43 do if body[y][x] then body[y][x] = (y == 41) and acc[5] or acc[3] end end
  end
  stamp(body, 32, 42, { "aa", "ab", " b" }, { a = acc[4], b = acc[2] })
  over(g, outline(body, NAVY[1]))

  -- bracos: no ataque o direito sobe com as garras de fora
  local throw = (pose == "ataque")
  for _, s in ipairs({ -1, 1 }) do
    local ax, ay = 30 + s * 15, 43
    if throw and s > 0 then ax, ay = 47, 30 end
    local arm = ell(W, H, ax, ay, 4.5, 5, NAVY, (s > 0) and -1 or 0)
    over(g, outline(arm, NAVY[1]))
    if throw and s > 0 then
      -- pata erguida com as garras pra fora (golpe de garra)
      stamp(g, ax - 3, ay - 8, { "w.w.w", "w.w.w", "c.c.c" }, { w = WHITE, c = acc[5] })
    end
  end

  -- cabeca com capuz
  local head = cat_head(W, H, 30, 22, 14, 11.5, NAVY, NAVY[2], { up = 18, spread = 8.5, base = 7 })
  -- abertura do capuz nos olhos (pelo cinza)
  for y = 18, 24 do for x = 18, 42 do
    if head[y][x] and math.abs(x + 0.5 - 30) < 11.5 - math.abs(y - 21) * 0.6 then head[y][x] = NAVY[6] end
  end end
  -- bandana na testa
  for y = 13, 15 do for x = 0, W - 1 do
    if head[y][x] then head[y][x] = (y == 13) and acc[5] or ((y == 14) and acc[4] or acc[3]) end
  end end
  -- plaquinha de metal da bandana
  stamp(head, 27, 13, { "mmmmmm", "mnmmnm", "mmmmmm" }, { m = rgb(176, 186, 210), n = rgb(110, 120, 150) })
  over(g, outline(head, NAVY[1]))
  -- no de bandana do lado
  stamp(g, 40, 12, { " aa ", "abba", " aa " }, { a = acc[4], b = acc[2] })
  return g
end

local function ninja_face(pose, rage, defeat)
  local g = grid(60, 60)
  local eye = rage and rgb(255, 60, 60) or NIGHT_EYE
  if defeat then
    stamp(g, 21, 19, { "w.w", ".w.", "w.w" }, { w = WHITE })
    stamp(g, 36, 19, { "w.w", ".w.", "w.w" }, { w = WHITE })
    for i = 0, 2 do
      local a = i * 2.1
      stamp(g, math.floor(30 + math.cos(a) * 12) - 1, math.floor(5 + math.sin(a) * 3) - 1, { " s ", "sss", " s " }, { s = rgb(255, 230, 90) })
    end
    return g
  end
  -- olhos puxados e bravos, pupila em fenda
  local L = {
    "yy....",
    "yyyyk.",
    ".yypyy",
    "..kkkk",
  }
  if pose == "ataque" then L = { "yy....", "yyyyyk", "yyypyy", ".kkkkk" } end
  stamp(g, 20, 18, L, { y = eye, p = NAVY[1], k = NAVY[2] })
  stamp(g, 34, 18, mirror_rows(L), { y = eye, p = NAVY[1], k = NAVY[2] })
  if rage then
    -- marquinhas de energia em volta dos olhos
    for _, p in ipairs({ { 17, 17 }, { 43, 17 }, { 18, 23 }, { 42, 23 } }) do set(g, p[1], p[2], { 255, 60, 60, 160 }) end
  end
  return g
end

local function make_ninja()
  local frames = {}
  for f = 0, 3 do frames[#frames + 1] = { dur = 110, layers = { corpo = ninja_body(f, "parado", false), rosto = ninja_face("parado", false) } } end
  frames[#frames + 1] = { dur = 120, layers = { corpo = ninja_body(1, "ataque", false), rosto = ninja_face("ataque", false) } }
  for f = 0, 3 do frames[#frames + 1] = { dur = 80, layers = { corpo = ninja_body(f, "parado", true), rosto = ninja_face("parado", true) } } end
  frames[#frames + 1] = { dur = 120, layers = { corpo = ninja_body(1, "ataque", true), rosto = ninja_face("ataque", true) } }
  frames[#frames + 1] = { dur = 200, layers = { corpo = ninja_body(0, "parado", false), rosto = ninja_face("parado", false, true) } }
  return {
    name = "boss_ninja", w = 60, h = 60, frames = frames,
    tags = {
      { name = "parado", from = 1, to = 4 }, { name = "ataque", from = 5, to = 5 },
      { name = "furia", from = 6, to = 9 }, { name = "ataque_furia", from = 10, to = 10 },
      { name = "derrota", from = 11, to = 11 },
    },
  }
end

-- ======================= 5) MADAME ASPIRINA =======================
-- bolinha "fofa": elipse com borda ondulada
local function fluff(w, h, cx, cy, rx, ry, pal, bumps, amp, seed)
  local g = grid(w, h)
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      local dx, dy = x + 0.5 - cx, y + 0.5 - cy
      local a = math.atan(dy, dx)
      local wob = 1 + amp * math.sin(a * bumps + (seed or 0))
      if (dx * dx) / (rx * rx * wob * wob) + (dy * dy) / (ry * ry * wob * wob) <= 1 then
        g[y][x] = pal[clamp(tone_of(light(dx, dy, rx, ry)) + 1, 2, 7)]
      end
    end
  end
  return g
end

local function duchess_body(f, pose, rage)
  local W, H = 76, 68
  local g = grid(W, H)
  local led = rage and LASER[3] or SKY[5]
  local plastic = rage and { rgb(60, 20, 40), rgb(110, 30, 60), rgb(160, 50, 90), rgb(210, 80, 120), rgb(240, 140, 170), rgb(255, 200, 220), WHITE } or SKY
  local cx, top_y, rx, ry, depth = 38, 50, 33, 11.5, 7

  -- ROBO ASPIRADOR: lateral (parede do disco) + tampa
  local vac = grid(W, H)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local dx = x + 0.5 - cx
      if math.abs(dx) <= rx then
        local half = ry * math.sqrt(math.max(0, 1 - (dx * dx) / (rx * rx)))
        local ytop, ybot = top_y - half, top_y + half
        local yy = y + 0.5
        if yy >= ytop and yy <= ybot then
          local l = light(dx, yy - top_y, rx, ry)
          vac[y][x] = plastic[clamp(tone_of(l) + 1, 3, 6)]
        elseif yy > ybot and yy <= ybot + depth then
          -- parede lateral: para-choque escuro com faixa
          local k = (yy - ybot) / depth
          vac[y][x] = (k < 0.35) and plastic[3] or ((k < 0.8) and rgb(52, 50, 70) or rgb(34, 32, 48))
        end
      end
    end
  end
  -- anel de LEDs que gira
  for i = 0, 15 do
    local a = i * (math.pi * 2 / 16)
    local x = math.floor(cx + math.cos(a) * rx * 0.78 + 0.5)
    local y = math.floor(top_y + math.sin(a) * ry * 0.78 + 0.5)
    local on = ((i + f * 2) % 8) < 3
    if vac[y] and vac[y][x] then vac[y][x] = on and led or plastic[3] end
  end
  -- botao / logo de patinha na frente da tampa
  stamp(vac, cx - 3, top_y + 4, { " a a ", "a   a", " aaa ", "aaaaa" }, { a = plastic[2] })
  -- escova lateral girando na frente
  local brush = grid(W, H)
  local bx, by = cx - 24, top_y + 13
  for i = 0, 2 do
    local a = f * 0.8 + i * (math.pi * 2 / 3)
    for r = 1, 5 do set(brush, math.floor(bx + math.cos(a) * r + 0.5), math.floor(by + math.sin(a) * r * 0.5 + 0.5), rgb(200, 190, 210)) end
  end
  set(brush, bx, by, rgb(80, 80, 100))
  over(g, outline(vac, plastic[1]))
  over(g, brush)
  -- bocal aspirando (frente) acende quando suga
  if pose == "aspirando" then
    for x = cx - 10, cx + 10 do
      for y = top_y + 12, top_y + 14 do set(g, x, y, ((x + f) % 3 == 0) and SKY[7] or rgb(120, 230, 255)) end
    end
  end

  -- GATA PERSA BRANCA sentada em cima
  local lean = (pose == "aspirando") and -1 or 0
  local body = fluff(W, H, cx + lean, 36, 16, 11, FLUFF, 11, rage and 0.12 or 0.06, f * 0.4)
  over(g, outline(body, FLUFF[1]))
  -- patinhas na tampa
  for _, px in ipairs({ cx - 8, cx + 8 }) do
    local paw = ell(W, H, px + lean, 45, 4, 2.5, FLUFF)
    over(g, outline(paw, FLUFF[1]))
  end
  -- espanador de penas na pata (ergue quando aspira)
  local up = (pose == "aspirando") and -6 or 0
  local dust = grid(W, H)
  for i = 0, 9 do set(dust, cx + 16 - math.floor(i * 0.3), 44 - i + up, rgb(150, 100, 60)) end
  local feather = { rgb(255, 120, 170), rgb(255, 200, 90), rgb(120, 220, 255), rgb(190, 140, 255) }
  for i = 0, 7 do
    local a = -math.pi / 2 + (i - 3.5) * 0.32 + math.sin(f * 1.3 + i) * 0.08
    for r = 2, 6 do set(dust, math.floor(cx + 13 + math.cos(a) * r), math.floor(33 + up + math.sin(a) * r), feather[(i % 4) + 1]) end
  end
  over(g, outline(dust, rgb(70, 40, 40)))
  -- cabeca fofa com orelhinhas pequenas
  local head = fluff(W, H, cx + lean, 22, 14, 11, FLUFF, 13, rage and 0.1 or 0.05, f * 0.3)
  for _, s in ipairs({ -1, 1 }) do
    tri_into(head, cx + lean + s * 11, 9, cx + lean + s * 6, 14, cx + lean + s * 13.5, 16, function() return FLUFF[3] end)
    tri_into(head, cx + lean + s * 10.6, 11, cx + lean + s * 7.5, 14.5, cx + lean + s * 12, 15.5, function() return PINK[5] end)
  end
  over(g, outline(head, FLUFF[1]))
  -- laco rosa na cabeca e colar de perolas
  stamp(g, cx + lean + 5, 9, { "aa.aa", "abcba", "aa.aa" }, { a = PINK[4], b = PINK[3], c = PINK[2] })
  for i = -5, 5 do
    local x = cx + lean + i * 2
    local y = 32 + math.floor((i * i) / 9)
    set(g, x, y, (i % 2 == 0) and WHITE or rgb(255, 220, 230))
  end
  return g
end

local function duchess_face(pose, rage, defeat)
  local g = grid(76, 68)
  local cx = 38 + ((pose == "aspirando") and -1 or 0)
  local map = { k = FLUFF[1], b = rgb(90, 160, 255), r = rgb(255, 70, 80), w = WHITE, n = PINK[4], m = rgb(150, 40, 70) }
  if defeat then
    stamp(g, cx - 9, 19, { "k.k", ".k.", "k.k" }, map)
    stamp(g, cx + 6, 19, { "k.k", ".k.", "k.k" }, map)
    stamp(g, cx - 3, 26, { "k.k.k.k", ".k.k.k." }, map)
    for i = 0, 2 do
      local a = i * 2.1 + 0.5
      stamp(g, math.floor(cx + math.cos(a) * 14) - 1, math.floor(6 + math.sin(a) * 3) - 1, { " s ", "sss", " s " }, { s = rgb(255, 230, 90) })
    end
    return g
  end
  if rage then
    -- olhos arregalados vermelhos, boca sibilando
    local E = { ".kkk.", "kwrwk", "kwrrk", ".kkk." }
    stamp(g, cx - 10, 18, E, map); stamp(g, cx + 5, 18, mirror_rows(E), map)
    stamp(g, cx - 11, 16, { "kk...", "..kkk" }, map); stamp(g, cx + 6, 16, { "...kk", "kkk.." }, map)
    stamp(g, cx - 3, 24, { "..nn..", ".kkkk.", "kmwwmk", ".kkkk." }, map)
  else
    -- olhos semicerrados de esnobe (azuis), nariz arrebitado, boquinha torta
    local E = { "kkkkk", "kbbwk", ".kkk." }
    if pose == "aspirando" then E = { ".kkk.", "kbbwk", "kbbbk", ".kkk." } end
    stamp(g, cx - 10, 19, E, map); stamp(g, cx + 5, 19, mirror_rows(E), map)
    -- cilios
    set(g, cx - 11, 18, map.k); set(g, cx + 10, 18, map.k)
    stamp(g, cx - 2, 24, { ".nn.", "..k.", ".kk." }, map)
  end
  return g
end

local function make_duchess()
  local frames = {}
  for f = 0, 3 do frames[#frames + 1] = { dur = 110, layers = { corpo = duchess_body(f, "parado", false), rosto = duchess_face("parado", false) } } end
  for f = 0, 3 do frames[#frames + 1] = { dur = 70, layers = { corpo = duchess_body(f, "aspirando", false), rosto = duchess_face("aspirando", false) } } end
  for f = 0, 3 do frames[#frames + 1] = { dur = 70, layers = { corpo = duchess_body(f, "parado", true), rosto = duchess_face("parado", true) } } end
  frames[#frames + 1] = { dur = 200, layers = { corpo = duchess_body(0, "parado", false), rosto = duchess_face("parado", false, true) } }
  return {
    name = "boss_duquesa", w = 76, h = 68, frames = frames,
    tags = {
      { name = "parado", from = 1, to = 4 }, { name = "aspirando", from = 5, to = 8 },
      { name = "furia", from = 9, to = 12 }, { name = "derrota", from = 13, to = 13 },
    },
  }
end

-- ======================= TIROS =======================
local function make_shuriken()
  local g = grid(15, 15)
  stamp(g, 0, 0, {
    "       a       ",
    "       a       ",
    "      aab      ",
    "      aab      ",
    "     aaabb     ",
    "     aabbb     ",
    "  aaaaccccbbbb ",
    "aaaaaaccdccbbbbb",
    " bbbbccccaaaa  ",
    "     bbbaa     ",
    "     bbaaa     ",
    "      baa      ",
    "      baa      ",
    "       b       ",
    "       b       ",
  }, { a = rgb(220, 228, 244), b = rgb(130, 140, 172), c = TEAL[4], d = TEAL[1] })
  g = outline(g, NAVY[1])
  return { name = "tiro_shuriken", w = 15, h = 15, frames = { { dur = 100, layers = { corpo = g } } }, tags = {} }
end

local function make_dust_bunny()
  local g = fluff(16, 16, 8, 8.5, 6.2, 5.8, { rgb(70, 64, 84), rgb(110, 104, 126), rgb(150, 144, 166), rgb(186, 180, 200), rgb(214, 210, 226), rgb(236, 234, 244), WHITE }, 9, 0.14, 0.7)
  g = outline(g, rgb(52, 46, 64))
  -- carinha brava de bola de poeira
  stamp(g, 4, 6, { "k....k", ".k..k.", "kk..kk" }, { k = rgb(40, 34, 52) })
  -- fiapos soltos
  set(g, 1, 3, rgb(150, 144, 166)); set(g, 14, 12, rgb(150, 144, 166)); set(g, 13, 2, rgb(150, 144, 166))
  return { name = "tiro_poeira", w = 16, h = 16, frames = { { dur = 100, layers = { corpo = g } } }, tags = {} }
end

-- ======================= ARENAS =======================
local function arena_telhado()
  local g = grid(AW, AH)
  local T1, T2, T3, TD = rgb(66, 30, 36), rgb(74, 36, 40), rgb(84, 42, 46), rgb(44, 20, 26)
  local SKYN, SKYN2 = rgb(10, 12, 28), rgb(14, 18, 38)
  local LEDGE, LEDGE2, LEDGE3 = rgb(70, 72, 92), rgb(54, 56, 74), rgb(38, 40, 56)
  for y = 0, AH - 1 do
    for x = 0, AW - 1 do
      local c
      if inside(x, y) then
        -- telhas em escama: fileiras de 10px, telhas de 16px, deslocadas a cada fileira
        local row = (y - IY0) // 10
        local off = (row % 2) * 8
        local tx = ((x - IX0) + off) % 16
        local ty = (y - IY0) % 10
        local dx = tx - 7.5
        local curve = 9 - (dx * dx) / 12
        c = T2
        if ty < 2 then c = T3 end
        if ty >= curve then c = TD end
        if tx == 0 then c = TD end
        -- variacao de cor por telha
        if hash((x - IX0 + off) // 16, row, 3) > 0.8 and c == T2 then c = T1 end
        -- lua crescente pintada no meio (simbolo do cla)
        local mx, my = x + 0.5 - 240, y + 0.5 - 160
        local d1 = math.sqrt(mx * mx + my * my)
        local d2 = math.sqrt((mx - 14) * (mx - 14) + (my + 8) * (my + 8))
        if d1 < 46 and d2 > 40 then c = (c == TD) and rgb(70, 40, 44) or rgb(96, 58, 56) end
        -- borda: calha de metal
        local e = math.min(x - IX0, IX1 - x, y - IY0, IY1 - y)
        if e < 3 then c = (e == 0) and LEDGE3 or LEDGE2 end
      elseif x >= IX0 - 8 and x <= IX1 + 8 and y >= IY0 - 8 and y <= IY1 + 8 then
        -- mureta de pedra
        local bx = (x + ((y // 4) % 2) * 4) % 8
        c = (bx == 0 or y % 4 == 0) and LEDGE3 or ((((x // 8) + (y // 4)) % 3 == 0) and LEDGE or LEDGE2)
      else
        -- cidade a noite: ceu com estrelas e predios com janelas acesas
        c = (((x + y) // 3) % 2 == 0) and SKYN or SKYN2
        if hash(x, y, 21) > 0.985 then c = rgb(200, 210, 255) end
        local col = x // 14
        local bh = 6 + math.floor(hash(col, 1, 22) * 14)
        local edge = math.min(y, AH - 1 - y, x, AW - 1 - x)
        if edge < bh then
          c = rgb(20, 22, 40)
          if (x % 4 == 1) and (y % 4 == 1) and hash(x, y, 23) > 0.55 then c = rgb(255, 214, 120) end
        end
      end
      g[y][x] = c
    end
  end
  return g
end

local function arena_sala()
  local g = grid(AW, AH)
  local W1, W2, W3, WD = rgb(64, 44, 36), rgb(70, 48, 39), rgb(60, 41, 34), rgb(54, 37, 31)
  local RUG1, RUG2, RUG3 = rgb(40, 58, 96), rgb(50, 72, 116), rgb(64, 90, 140)
  local WALL1, WALL2 = rgb(56, 40, 52), rgb(64, 46, 60)
  for y = 0, AH - 1 do
    for x = 0, AW - 1 do
      local c
      if inside(x, y) then
        -- taco em espinha de peixe (blocos 16x4 alternando direcao)
        local bx, by = (x - IX0), (y - IY0)
        local cell = ((bx // 16) + (by // 16)) % 2
        local u = (cell == 0) and ((bx + by) % 16) or ((bx - by + 160) % 16)
        local v = (cell == 0) and (by % 4) or (bx % 4)
        c = ({ W1, W2, W3 })[(((bx // 4) * 7 + (by // 4) * 3) % 3) + 1]
        if v == 0 then c = WD end
        if u == 0 then c = WD end
        -- tapete redondo no centro
        local dx, dy = (x + 0.5 - 240) / 120, (y + 0.5 - 160) / 76
        local d = math.sqrt(dx * dx + dy * dy)
        if d < 1 then
          c = RUG2
          if d > 0.9 then c = RUG1 end
          if math.abs(d - 0.75) < 0.03 or math.abs(d - 0.45) < 0.035 then c = RUG3 end
          if d < 0.2 then c = RUG1 end
          -- franja
          if d > 0.96 and (x + y) % 2 == 0 then c = rgb(150, 160, 190) end
        end
        -- rodape
        local e = math.min(x - IX0, IX1 - x, y - IY0, IY1 - y)
        if e < 3 then c = (e == 0) and rgb(110, 100, 120) or rgb(150, 140, 160) end
      else
        -- papel de parede listrado
        c = ((x // 5) % 2 == 0) and WALL1 or WALL2
        if (x % 20 == 10) and (y % 20 == 10) then c = rgb(90, 62, 80) end
      end
      g[y][x] = c
    end
  end
  -- quadrinhos na parede e uma janela iluminada
  local function frame(x0, y0, w, h, inner)
    for y = 0, h - 1 do for x = 0, w - 1 do
      local col = inner(x, y)
      if x == 0 or y == 0 or x == w - 1 or y == h - 1 then col = GOLD[3] end
      set(g, x0 + x, y0 + y, col)
    end end
  end
  frame(60, 4, 22, 16, function(x, y) return (y > 9) and rgb(80, 140, 90) or rgb(130, 180, 230) end)
  frame(390, 4, 22, 16, function(x, y) return ((x - 11) ^ 2 + (y - 8) ^ 2 < 20) and rgb(255, 255, 255) or rgb(120, 80, 140) end)
  frame(200, 2, 80, 20, function(x, y) return (x % 20 == 0 or y == 10) and rgb(200, 190, 210) or rgb(170, 210, 255) end)
  frame(4, 140, 16, 30, function() return rgb(120, 70, 50) end)
  frame(460, 140, 16, 30, function() return rgb(120, 70, 50) end)
  return g
end


local function make_garra()
  local W, H = 14, 18
  local g = grid(W, H)
  -- meia-lua: arco branco por fora, verde-agua por dentro (corte de garra)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local dx, dy = x + 0.5 - 2, y + 0.5 - 9
      local d = math.sqrt(dx * dx + dy * dy)
      local a = math.atan(dy, dx)
      if math.abs(a) < 1.15 then
        if d >= 9.6 and d < 11.4 then g[y][x] = WHITE
        elseif d >= 8.0 and d < 9.6 then g[y][x] = TEAL[5]
        elseif d >= 6.6 and d < 8.0 and math.abs(a) < 0.8 then g[y][x] = TEAL[3] end
      end
    end
  end
  g = outline(g, NAVY[1])
  return { name = "tiro_garra", w = W, h = H, frames = { { dur = 100, layers = { corpo = g } } }, tags = {} }
end

function A.novos()
  return {
    make_ninja(), make_duchess(), make_shuriken(), make_dust_bunny(), make_garra(),
    { name = "cenario_telhado", w = AW, h = AH, frames = { { dur = 100, layers = { corpo = arena_telhado() } } }, tags = {} },
    { name = "cenario_sala", w = AW, h = AH, frames = { { dur = 100, layers = { corpo = arena_sala() } } }, tags = {} },
  }
end

function A.all()
  return { make_prism2(), make_orbital2(), make_drone2(), make_core2() }
end

return A
