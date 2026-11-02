-- Roda dentro do Aseprite:
--   aseprite -b --script-param src=<assets> --script-param out=<pasta .aseprite> --script hero.lua
-- Pega os 3 desenhos parados do Supercat (normal, feliz, triste) e cria 4 frames de voo
-- para cada um: a capa ondula e as patinhas de tras alternam entre duas poses. Salva tudo num unico
-- supercat.aseprite (uma tag por expressao).

local src = app.params["src"]
local out = app.params["out"]
local moods = { "normal", "feliz", "triste" }
local NF = 4

local CAPE = {
  [app.pixelColor.rgba(221, 37, 40, 255)] = true,
  [app.pixelColor.rgba(149, 25, 29, 255)] = true,
}

-- patas de tras na pose B (colunas 0..19, linhas 29..39); igual nas 3 expressoes
local POSE_Y = 29
local POSE_B = {
  "..eee.......eeeabbbe",
  ".egggeeeeeeebbebbbbb",
  ".egggbebbbbbbeebbbbb",
  ".egggbebeeeeeebbbbbb",
  "..eeeeeee...eebbbbbe",
  "............eebbbbee",
  "...........ebbbbee..",
  "..........egggbe....",
  "..........eggge.....",
  "...........eee......",
  "....................",
}
local LEG = {
  e = app.pixelColor.rgba(225, 103, 26, 255),
  g = app.pixelColor.rgba(255, 201, 130, 255),
  b = app.pixelColor.rgba(253, 161, 55, 255),
  a = app.pixelColor.rgba(176, 62, 17, 255),
}

local function isCape(img, x, y)
  return CAPE[img:getPixel(x, y)] == true
end

local function frameOf(base, f)
  local W, H = base.width, base.height
  local img = Image(W, H, ColorMode.RGB)
  local phase = f * (math.pi * 2 / NF)

  -- 1) tudo que NAO e capa, sem mexer (antes as patas eram deslocadas em blocos e cortavam)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      local c = base:getPixel(x, y)
      if app.pixelColor.rgbaA(c) > 0 and not isCape(base, x, y) then img:drawPixel(x, y, c) end
    end
  end
  -- 2) patas de tras: alterna entre a pose original (A) e a pose B desenhada a mao,
  --    no ritmo A, B, B, A (a perna inteira muda junto, sem emenda)
  if f == 1 or f == 2 then
    for j, row in ipairs(POSE_B) do
      for i = 1, #row do
        local ch = row:sub(i, i)
        local x, y = i - 1, POSE_Y + j - 1
        if ch == "." then img:drawPixel(x, y, app.pixelColor.rgba(0, 0, 0, 0))
        else img:drawPixel(x, y, LEG[ch]) end
      end
    end
  end
  -- 3) capa ondulando: quanto mais longe do pescoco (x~28), mais ela mexe
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      if isCape(base, x, y) then
        local amp = 2.0 * math.max(0, math.min(1, (24 - x) / 24))
        local dy = math.floor(math.sin(phase + x * 0.16) * amp + 0.5)
        local ny = y + dy
        if ny >= 0 and ny < H then img:drawPixel(x, ny, base:getPixel(x, y)) end
      end
    end
  end
  -- 4) onde era capa e ficou vazio mas tem corpo do lado direito, completa com o corpo
  for y = 0, H - 1 do
    for x = 0, W - 2 do
      if isCape(base, x, y) and app.pixelColor.rgbaA(img:getPixel(x, y)) == 0 then
        local r = base:getPixel(x + 1, y)
        if app.pixelColor.rgbaA(r) > 0 and not isCape(base, x + 1, y) then img:drawPixel(x, y, r) end
      end
    end
  end
  -- 5) fecha furinhos de 1px dentro da capa
  for y = 1, H - 2 do
    for x = 0, 30 do
      if app.pixelColor.rgbaA(img:getPixel(x, y)) == 0 then
        local up, dn = img:getPixel(x, y - 1), img:getPixel(x, y + 1)
        if CAPE[up] and CAPE[dn] then img:drawPixel(x, y, dn) end
      end
    end
  end
  return img
end

local spr = nil
local layer = nil
local fi = 0
for mi, mood in ipairs(moods) do
  local base = Image { fromFile = src .. "/gato_" .. mood .. ".png" }
  if spr == nil then
    spr = Sprite(base.width, base.height, ColorMode.RGB)
    layer = spr.layers[1]
    layer.name = "supercat"
  end
  local first = fi + 1
  for f = 0, NF - 1 do
    fi = fi + 1
    if fi > 1 then spr:newEmptyFrame() end
    spr.frames[fi].duration = 0.1
    spr:newCel(layer, spr.frames[fi], frameOf(base, f), Point(0, 0))
  end
  local tag = spr:newTag(first, fi)
  tag.name = mood
end
spr:saveAs(out .. "/supercat.aseprite")
print("salvo: supercat.aseprite (" .. fi .. " frames)")
