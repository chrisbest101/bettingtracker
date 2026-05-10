"""
GemBets Bet Card Template — v2.0
Last updated: 10 May 2026

LAYOUT STANDARDS (do not change without framework update):
- Badge circles spaced ~200px apart, "vs" centred between them
- Team name labels centred on badge cx using textbbox width
- No underlines on player name or market header
- Sub-label sits 26px below player name bottom
- Red left accent bar on selection card
- Platform badge top right
- @gembets_ branding bottom left
- 18+ disclaimer bottom right
- Gradient: home team colour (left) -> away team colour (right)
"""

from PIL import Image, ImageDraw, ImageFont
import requests
import io

# ── CONFIG — edit these per bet ──────────────────────────────────────────────
HOME_TEAM       = "West Ham"
AWAY_TEAM       = "Arsenal"
HOME_TEAM_ID    = 563          # football-data.org crest ID
AWAY_TEAM_ID    = 57
HOME_COLOUR     = (122, 38, 58)    # West Ham claret
AWAY_COLOUR     = (200, 16, 46)    # Arsenal red

PLAYER          = "BUKAYO SAKA"
MARKET          = "1+ SHOT ON TARGET"
SUBLABEL        = "To have 1 or more shots on target"
PLATFORM        = "Sky Bet"
COMPETITION     = "Premier League"
MATCH_DATE      = "Sun 10 May 2026"
KO_TIME         = "16:30 BST"

ODDS_WAS        = "1.4"
ODDS_BOOSTED    = "2.0"
STAKE           = "£5"
TO_WIN          = "£5.00"

STAT1_VAL       = "1.18"
STAT1_LBL       = "SOT per 90"
STAT1_SUB       = "Season avg"

STAT2_VAL       = "7"
STAT2_LBL       = "Goals"
STAT2_SUB       = "2025/26 PL"

STAT3_VAL       = "+19%"
STAT3_LBL       = "Edge"
STAT3_SUB       = "vs implied odds"

NARRATIVE_1     = "1.18 SOT per 90. Arsenal chasing the title today."
NARRATIVE_2     = "Saka starts. West Ham at home. Sky Bet boosted to 2.0."

RATING          = "7/10"
STAKE_DISPLAY   = "£5"

OUTPUT_PATH     = "/mnt/user-data/outputs/gembets_bet_card.png"
# ─────────────────────────────────────────────────────────────────────────────

W, H = 1080, 1080

RED       = (204, 0, 0)
RED_DARK  = (160, 0, 0)
WHITE     = (255, 255, 255)
OFF_WHITE = (248, 248, 248)
LIGHT_GREY = (230, 230, 230)
MID_GREY  = (180, 180, 180)
DARK_GREY = (80, 80, 80)
BLACK     = (20, 20, 20)

img  = Image.new("RGB", (W, H), WHITE)
draw = ImageDraw.Draw(img)

# ── GRADIENT HEADER ───────────────────────────────────────────────────────────
for y in range(320):
    t = y / 320
    r = int(HOME_COLOUR[0] + (AWAY_COLOUR[0] - HOME_COLOUR[0]) * t)
    g = int(HOME_COLOUR[1] + (AWAY_COLOUR[1] - HOME_COLOUR[1]) * t)
    b = int(HOME_COLOUR[2] + (AWAY_COLOUR[2] - HOME_COLOUR[2]) * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

draw.rectangle([0, 320, W, H], fill=OFF_WHITE)
draw.rectangle([0, 0, W, 6],      fill=RED_DARK)
draw.rectangle([0, H - 70, W, H], fill=RED_DARK)

# ── FONTS ─────────────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
    ]
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except: continue
    return ImageFont.load_default()

# ── PLATFORM BADGE ────────────────────────────────────────────────────────────
pb_w, pb_h = 130, 36
pb_x, pb_y = W - pb_w - 24, 18
draw.rounded_rectangle([pb_x, pb_y, pb_x+pb_w, pb_y+pb_h], radius=6, fill=WHITE)
bbox = draw.textbbox((0,0), PLATFORM, font=load_font(18, bold=True))
draw.text((pb_x+(pb_w-(bbox[2]-bbox[0]))//2, pb_y+(pb_h-(bbox[3]-bbox[1]))//2),
          PLATFORM, font=load_font(18, bold=True), fill=RED)

# ── COMPETITION LINE ──────────────────────────────────────────────────────────
comp = f"{COMPETITION}  ·  {MATCH_DATE}  ·  KO {KO_TIME}"
bbox = draw.textbbox((0,0), comp, font=load_font(17))
draw.text(((W-(bbox[2]-bbox[0]))//2, 26), comp, font=load_font(17), fill=(230,210,210))

# ── BADGES ────────────────────────────────────────────────────────────────────
# Centres: home=122, away=322, vs centred at 222
WH_CX, ARS_CX, BADGE_CY, BADGE_R = 122, 322, 165, 56

def fetch_badge(team_id, size=88):
    url = f"https://crests.football-data.org/{team_id}.png"
    r = requests.get(url, timeout=15)
    badge = Image.open(io.BytesIO(r.content)).convert("RGBA")
    return badge.resize((size, size), Image.LANCZOS)

def draw_badge_circle(cx, cy, radius, badge):
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=WHITE)
    img.paste(badge, (cx-badge.width//2, cy-badge.height//2), badge)

try:
    draw_badge_circle(WH_CX,  BADGE_CY, BADGE_R, fetch_badge(HOME_TEAM_ID))
    draw_badge_circle(ARS_CX, BADGE_CY, BADGE_R, fetch_badge(AWAY_TEAM_ID))
except Exception as e:
    print(f"Badge fetch failed: {e} — using initials")
    for cx, initials, col in [(WH_CX, HOME_TEAM[:3].upper(), HOME_COLOUR),
                               (ARS_CX, AWAY_TEAM[:3].upper(), AWAY_COLOUR)]:
        draw.ellipse([cx-BADGE_R, BADGE_CY-BADGE_R, cx+BADGE_R, BADGE_CY+BADGE_R], fill=WHITE)
        bbox = draw.textbbox((0,0), initials, font=load_font(20, bold=True))
        draw.text((cx-(bbox[2]-bbox[0])//2, BADGE_CY-(bbox[3]-bbox[1])//2),
                  initials, font=load_font(20, bold=True), fill=col)

# "vs" centred between badges
vs_cx = (WH_CX + ARS_CX) // 2
bbox = draw.textbbox((0,0), "vs", font=load_font(20))
draw.text((vs_cx-(bbox[2]-bbox[0])//2, 155), "vs", font=load_font(20), fill=WHITE)

# Team labels centred on badge cx — ALWAYS use textbbox for centering
LABEL_Y = 232
for cx, name in [(WH_CX, HOME_TEAM), (ARS_CX, AWAY_TEAM)]:
    bbox = draw.textbbox((0,0), name, font=load_font(16))
    draw.text((cx-(bbox[2]-bbox[0])//2, LABEL_Y), name, font=load_font(16), fill=WHITE)

# ── MARKET HEADER — no underline ──────────────────────────────────────────────
bbox = draw.textbbox((0,0), MARKET, font=load_font(36, bold=True))
mx = (W-(bbox[2]-bbox[0]))//2
draw.text((mx, 268), MARKET, font=load_font(36, bold=True), fill=WHITE)

# ── SELECTION CARD ────────────────────────────────────────────────────────────
draw.rounded_rectangle([40, 338, W-40, 490], radius=16, fill=WHITE)
draw.rounded_rectangle([40, 338, W-40, 490], radius=16, outline=LIGHT_GREY, width=2)
draw.rounded_rectangle([40, 338, 46, 490],   radius=4,  fill=RED)

# Player name — no underline
bbox = draw.textbbox((0,0), PLAYER, font=load_font(66, bold=True))
draw.text((70, 348), PLAYER, font=load_font(66, bold=True), fill=BLACK)

# Sub-label 26px below player name bottom
sub_y = 348 + (bbox[3]-bbox[1]) + 26
draw.text((70, sub_y), SUBLABEL, font=load_font(24), fill=DARK_GREY)

# ── ODDS ROW ──────────────────────────────────────────────────────────────────
odds_y    = 514
section_w = (W-80)//4
labels    = ["WAS",     "BOOSTED",     "STAKE", "TO WIN"]
values    = [ODDS_WAS,  ODDS_BOOSTED,  STAKE,   TO_WIN]
colors    = [MID_GREY,  RED,           BLACK,   (0,140,60)]
strike    = [True,      False,         False,   False]

for i, (lbl, val, col, stk) in enumerate(zip(labels, values, colors, strike)):
    sx = 40 + i*section_w
    if i > 0:
        draw.line([(sx, odds_y), (sx, odds_y+82)], fill=LIGHT_GREY, width=1)
    bbox = draw.textbbox((0,0), lbl, font=load_font(17))
    draw.text((sx+(section_w-(bbox[2]-bbox[0]))//2, odds_y+8), lbl, font=load_font(17), fill=MID_GREY)
    vf   = load_font(34, bold=True)
    bbox = draw.textbbox((0,0), val, font=vf)
    vx   = sx+(section_w-(bbox[2]-bbox[0]))//2
    vy   = odds_y+34
    draw.text((vx, vy), val, font=vf, fill=col)
    if stk:
        mid_y = vy+(bbox[3]-bbox[1])//2
        draw.line([(vx-2, mid_y), (vx+(bbox[2]-bbox[0])+2, mid_y)], fill=MID_GREY, width=3)

# ── STAT BOXES ────────────────────────────────────────────────────────────────
stats = [
    (STAT1_VAL, STAT1_LBL, STAT1_SUB),
    (STAT2_VAL, STAT2_LBL, STAT2_SUB),
    (STAT3_VAL, STAT3_LBL, STAT3_SUB),
]
box_y = 622
box_w = (W-100)//3

for i, (val, label, sub) in enumerate(stats):
    bx = 50 + i*(box_w+10)
    draw.rounded_rectangle([bx, box_y, bx+box_w, box_y+110], radius=12, fill=WHITE)
    draw.rounded_rectangle([bx, box_y, bx+box_w, box_y+110], radius=12, outline=LIGHT_GREY, width=2)
    draw.rounded_rectangle([bx, box_y, bx+box_w, box_y+5],   radius=4,  fill=RED)
    bbox = draw.textbbox((0,0), val, font=load_font(38, bold=True))
    draw.text((bx+(box_w-(bbox[2]-bbox[0]))//2, box_y+14), val, font=load_font(38, bold=True), fill=RED)
    bbox = draw.textbbox((0,0), label, font=load_font(17, bold=True))
    draw.text((bx+(box_w-(bbox[2]-bbox[0]))//2, box_y+60), label, font=load_font(17, bold=True), fill=BLACK)
    bbox = draw.textbbox((0,0), sub, font=load_font(16))
    draw.text((bx+(box_w-(bbox[2]-bbox[0]))//2, box_y+84), sub, font=load_font(16), fill=MID_GREY)

# ── NARRATIVE BLOCK ───────────────────────────────────────────────────────────
draw.rounded_rectangle([40, 754, W-40, 844], radius=12, fill=(250,240,240))
draw.rounded_rectangle([40, 754, W-40, 844], radius=12, outline=(220,180,180), width=1)
bbox = draw.textbbox((0,0), NARRATIVE_1, font=load_font(22, bold=True))
draw.text(((W-(bbox[2]-bbox[0]))//2, 768), NARRATIVE_1, font=load_font(22, bold=True), fill=RED)
bbox = draw.textbbox((0,0), NARRATIVE_2, font=load_font(20))
draw.text(((W-(bbox[2]-bbox[0]))//2, 806), NARRATIVE_2, font=load_font(20), fill=DARK_GREY)

# ── RATING ROW ────────────────────────────────────────────────────────────────
draw.text((50,      872), f"⚡ Rating: {RATING}",       font=load_font(28, bold=True), fill=BLACK)
draw.text((W//2+20, 872), f"💰 Stake: {STAKE_DISPLAY}", font=load_font(28, bold=True), fill=BLACK)

# ── BOTTOM BAR ────────────────────────────────────────────────────────────────
draw.text((20, H-48), "💎 @gembets_", font=load_font(20, bold=True), fill=WHITE)
draw.text((W-340, H-46), "18+ | T&Cs Apply | Ad | Gamble responsibly", font=load_font(15), fill=(220,200,200))

img.save(OUTPUT_PATH, quality=95)
print(f"Card saved to {OUTPUT_PATH}")
