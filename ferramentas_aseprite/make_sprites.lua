-- Roda dentro do Aseprite:
--   aseprite -b --script-param out=<pasta> --script make_sprites.lua
-- Cria um .aseprite por inimigo (camadas "corpo" e "rosto", frames e tags de animacao).
package.path = app.fs.joinPath(app.fs.filePath(debug.getinfo(1, "S").source:sub(2)), "?.lua;") .. package.path
local A = require("art")
local out = app.params["out"] or "."

local set_ = app.params["set"]
local list = (set_ == "extras") and A.extras() or ((set_ == "fx") and A.fx() or ((set_ == "novos") and A.novos() or A.all()))
for _, s in ipairs(list) do
  local spr = Sprite(s.w, s.h, ColorMode.RGB)
  spr.filename = out .. "/" .. s.name .. ".aseprite"

  -- paleta com todas as cores usadas (facilita editar na mao depois)
  local cols, seen = {}, {}
  for _, fr in ipairs(s.frames) do
    for _, g in pairs(fr.layers) do
      for y = 0, s.h - 1 do
        for x = 0, s.w - 1 do
          local c = g[y][x]
          if c then
            local k = c[1] .. "," .. c[2] .. "," .. c[3] .. "," .. (c[4] or 255)
            if not seen[k] then seen[k] = true; cols[#cols + 1] = c end
          end
        end
      end
    end
  end
  local pal = Palette(#cols + 1)
  pal:setColor(0, Color { r = 0, g = 0, b = 0, a = 0 })
  for i, c in ipairs(cols) do pal:setColor(i, Color { r = c[1], g = c[2], b = c[3], a = c[4] or 255 }) end
  spr:setPalette(pal)

  -- camadas: "corpo" (a primeira, ja existe) e "rosto" se o inimigo tiver
  local layerCorpo = spr.layers[1]
  layerCorpo.name = "corpo"
  local layerRosto = nil
  if s.frames[1].layers.rosto then
    layerRosto = spr:newLayer()
    layerRosto.name = "rosto"
  end

  for i = 2, #s.frames do spr:newEmptyFrame() end

  for fi, fr in ipairs(s.frames) do
    spr.frames[fi].duration = fr.dur / 1000
    for lname, g in pairs(fr.layers) do
      local layer = (lname == "rosto") and layerRosto or layerCorpo
      local img = Image(s.w, s.h, ColorMode.RGB)
      for y = 0, s.h - 1 do
        for x = 0, s.w - 1 do
          local c = g[y][x]
          if c then img:drawPixel(x, y, app.pixelColor.rgba(c[1], c[2], c[3], c[4] or 255)) end
        end
      end
      spr:newCel(layer, spr.frames[fi], img, Point(0, 0))
    end
  end

  for _, t in ipairs(s.tags) do
    local tag = spr:newTag(t.from, t.to)
    tag.name = t.name
  end

  spr:saveAs(spr.filename)
  spr:close()
  print("salvo: " .. s.name .. ".aseprite")
end
