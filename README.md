<div align="center">

<img src="docs/sprites/gato_normal.png" alt="Supercat" height="140">

# Supercat: Boss Rush

**Um boss rush 2D em pixel art feito em Python + Pygame.**
Controle o Supercat, desvie de chuvas de tiros e derrote cinco chefes seguidos usando bolas de pelo.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/pygame--ce-2.5-00B140)
![Status](https://img.shields.io/badge/status-beta%20(Sprint%2003)-F5A13A)

<img src="docs/gameplay.gif" alt="Gameplay: o Supercat derrota o primeiro chefe, pega a ração e começa a luta contra o segundo" width="720">

</div>

---

## Sobre o jogo

*Supercat: Boss Rush* é um jogo de ação com visão de cima em que o jogador enfrenta **apenas chefes**, um atrás do outro. Cada chefe tem um padrão de ataque próprio e, ao ser derrotado, deixa um **power-up** que deixa o Supercat mais forte para a próxima luta.

O projeto foi desenvolvido durante a **Sprint 03** como protótipo jogável. Saímos do zero e chegamos a uma versão beta com o jogo completo do início ao fim, o personagem animado e power-ups com arte própria. Os chefes são gatos supervilões em pixel art feitos no Aseprite: o lutador mascarado **PATADÃO**, o cientista maluco **DR. MIAUSTEIN** com seus ratos de corda e a rainha **RAINHA MIAUGIA** na sua caixa mágica Cada chefe tem sua própria arena (o ringue do PATADÃO, o laboratório do DR. MIAUSTEIN, o salão do trono da rainha, o telhado do SOMBRA e a sala de estar da MADAME ASPIRINA) e seu próprio tiro (espinhas de peixe, pontinhos de laser, novelos de lã, garras e bolas de poeira), e o Supercat voa com a capa esvoaçando. Os arquivos editáveis ficam em `assets/aseprite/`.

## Como jogar

### Requisitos

- Python 3.10 ou mais recente
- [pygame-ce](https://pyga.me/) (ou `pygame`)

### Instalação

```bash
git clone https://github.com/<usuario>/<repositorio>.git
cd <repositorio>
pip install pygame-ce
python bossrush.py
```

> A pasta `assets/` precisa ficar ao lado do `bossrush.py`. Se ela faltar, o jogo não quebra: volta a desenhar o jogador como um círculo.

### Controles

| Tecla | Ação |
|---|---|
| `W` `A` `S` `D` | Mover |
| Setas ou `I` `J` `K` `L` | Atirar (4 direções) |
| `P` ou `Esc` | Pausar |
| `F11` | Tela cheia (sem distorcer a imagem) |
| `R` | Reiniciar |
| `M` | Voltar ao menu (no pause e no fim de jogo) |
| `F1` | Liga/desliga o **modo de teste** (dano x10) |

### Modo de teste

Pra testar os chefes rápido, aperte **F1** (no menu ou durante a luta): as bolas de pelo passam a causar **10x mais dano** e aparece o selo "MODO TESTE" no canto da tela. Aperte F1 de novo pra desligar.
No começo do `bossrush.py` dá pra ajustar o multiplicador (`DANO_MODO_TESTE`) ou deixar o modo ligado já ao abrir o jogo (`MODO_TESTE = True`).

## Os chefes

O jogo começa num **menu** (Jogar / Como jogar / Sair). Cada chefe entra caindo do céu e, quando a vida chega na **metade**, entra em **FÚRIA**: muda de visual, a arena fica avermelhada e ele ganha ataques novos.


| Onda | Chefe | Vida | Como ataca |
|:---:|---|:---:|---|
| 1 | **PATADÃO** | 280 | Leque de 8 espinhas de peixe e um **salto** que termina num anel de tiros. **Fúria:** combo de 3 pulos e furacão de espinhas em espiral |
| 2 | **DR. MIAUSTEIN** | 360 | Rajadas de 6 lasers e até **4 ratos de corda** que orbitam e investem. **Fúria:** varredura de laser em 3 braços (com aviso), rajadas de 10 e até 6 ratos mais rápidos |
| 3 | **RAINHA MIAUGIA** | 480 | Anel de 12 novelos e um trio mirado. **Fúria:** teletransporte pela arena, anéis de 16 alternados e novelos teleguiados |
| 4 | **SOMBRA**, o Gato Ninja | 520 | **Persegue** devagar lançando **leques de 3 garras**; depois **some**, mostra os **olhos brilhando** onde vai surgir e reaparece soltando um **anel de 8 garras** (só leva dano quando está visível). **Fúria:** mais rápido, leques de 5, anel de 12, **olhos falsos** de isca e às vezes some duas vezes seguidas |
| 5 | **MADAME ASPIRINA**, a Duquesa da Faxina | 600 | Gata persa num **robô aspirador** que anda reto e quica nas paredes. **Aspira o Supercat** (voe contra!) e cospe **bolas de poeira que se dividem**. **Fúria:** modo turbo, aspira mais vezes, espiral de poeira enquanto suga e poeira a cada batida |

<p align="center">
  <img src="docs/screenshots/onda1_prisma.png" alt="Onda 1: Prisma" width="32%">
  <img src="docs/screenshots/onda2_orbital.png" alt="Onda 2: Orbital com drones" width="32%">
  <img src="docs/screenshots/onda3_nucleo.png" alt="Onda 3: Núcleo" width="32%">
</p>

## Direção de arte

- **Pixel sempre nítido:** a tela é ampliada sem suavização (nada de borrão em tela cheia) e todo texto usa a fonte pixel **Silkscreen** (licença OFL, em `assets/fontes/`).
- **HUD em pixel art:** corações com meia-vida, retrato do chefe (muda na fúria), moldura da barra de vida com marca da metade e indicador de ondas com patinhas.
- **Luz:** brilho aditivo nos tiros, luz colorida embaixo de cada chefe, vinheta nas bordas.
- **Cenários vivos:** holofotes e flashes de câmera no ringue, luzes piscando e tubos borbulhando no laboratório, velas tremulando no salão do trono.
- **Efeitos animados feitos no Aseprite:** poeira, explosão, faísca de impacto, brilhos e a almofada de veludo dos power-ups.

## Power-ups

Depois de cada chefe aparece um power-up no centro da arena. Pegar o item libera a próxima onda.

| | Item | Efeito |
|:---:|---|---|
| <img src="docs/sprites/racao.png" height="56" alt="Ração"> | **Ração** | **+Fire rate**: atira mais rápido |
| <img src="docs/sprites/erva_de_gato.png" height="56" alt="Erva-de-gato"> | **Erva-de-gato** | **+Damage**: +3 de dano por tiro |
| <img src="docs/sprites/bolas_de_pelo_triplas.png" height="56" alt="Três bolas de pelo"> | **3 bolas de pelo** | **+Range & size**: tiros vão mais longe e ficam maiores |
| <img src="docs/sprites/coracao.png" height="40" alt="Coração"> | **Coração** | **+Vida**: recupera 3 corações (aparece depois da onda 3) |

## O Supercat

O herói muda de expressão conforme o que acontece na partida:

| Normal | Triste | Feliz |
|:---:|:---:|:---:|
| <img src="docs/screenshots/supercat_normal.png" alt="Supercat normal" width="260"> | <img src="docs/screenshots/supercat_triste.png" alt="Supercat triste" width="260"> | <img src="docs/screenshots/supercat_feliz.png" alt="Supercat feliz" width="260"> |
| Estado padrão da luta | Ao tomar dano e no game over | Ao derrotar um chefe, pegar power-up e na vitória |

Animações e efeitos:

- Flutua, inclina ao subir ou descer e tem sombra embaixo
- Vira com animação para o lado em que anda ou atira (o tiro tem prioridade, então andar para um lado e atirar para o outro não faz o gato "piscar")
- Tranco e puff de pelo a cada tiro; as bolas de pelo giram e deixam rastro
- Ao tomar dano: pisca em vermelho, solta faíscas e a tela treme
- Coraçõezinhos quando está feliz
- Chefes piscam ao levar tiro e explodem em partículas ao morrer

<p align="center">
  <img src="docs/screenshots/tela_derrota.png" alt="Tela de derrota" width="48%">
  <img src="docs/screenshots/tela_vitoria.png" alt="Tela de vitória" width="48%">
</p>

## Estrutura do projeto

```
.
├── bossrush.py          # jogo completo (loop, jogador, chefes, power-ups, efeitos)
├── assets/              # sprites em pixel art (50×50)
│   ├── gato_normal.png
│   ├── gato_feliz.png
│   ├── gato_triste.png
│   ├── bola_de_pelo.png
│   ├── bolas_de_pelo_triplas.png
│   ├── erva_de_gato.png
│   ├── racao.png
│   └── coracao.png
└── docs/                # imagens usadas neste README
```

### Detalhes técnicos

- **Tela virtual de 960×640**, ampliada para a janela mantendo a proporção (sem esticar no `F11`).
- **Movimento com delta time**, aceleração e atrito, para o jogo rodar igual em qualquer FPS.
- **Colisões entre círculos**: o sprite do Supercat é só o desenho; a hitbox continua um círculo de raio 16.
- **Dano centralizado** em `PlayerShip.take_damage()`, que também troca a expressão do gato.
- **Sprites ampliados sem filtro** (`pygame.transform.scale`), mantendo o pixel art nítido.
- Os ajustes de animação ficam em constantes no topo do arquivo (`CAT_SCALE`, `TURN_TIME`, `BOB_AMP`, `TILT_MAX`, `MAX_PARTICLES`…).

## Próximos passos

- [ ] Usar o coração como vida no HUD, no lugar dos blocos
- [ ] Arte dos 3 chefes, dos drones e da arena
- [ ] Balancear o dano do jogador e definir o número de drones
- [ ] Nomes finais dos chefes e cor própria na barra de vida de cada um
- [ ] Sons e menu inicial

## Equipe

| Integrante | Frente |
|---|---|
| **Henrique Vieira** | Programação: sprites e animações |
| **Nicoly Siqueira** | Arte: Supercat, bolas de pelo e power-ups |
| **Rafael Weykamp** | Game design: organização e jogo base |

---

<div align="center">
<sub>Projeto acadêmico desenvolvido na Sprint 03.</sub>
</div>
