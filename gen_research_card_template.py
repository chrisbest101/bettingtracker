"""
GemBets Research Card Template — v2.0
Last updated: 10 May 2026

LAYOUT STANDARDS (do not change without framework update):
- Badge circles spaced ~200px apart, "vs" centred between them
- Team name labels centred on badge cx using textbbox width
- No underlines anywhere
- 3 reasons: bold red heading + body text, no numbering
- Risk block: red-tinted background, red left accent bar
- Form pills: W=green, D=amber, L=red — last 5 newest first (left to right)
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
HOME_TEAM_ID    = 563
AWAY_TEAM_ID    = 57
HOME_COLOUR     = (122, 38, 58)
AWAY_COLOUR     = (200, 16, 46)

PLAYER          = "BUKAYO SAKA"
MARKET          = "1+ SHOT ON TARGET"
PLATFORM        = "Sky Bet"
COMPETITION     = "Premier League"
MATCH_DATE      = "Sun 10 May 2026"
KO_TIME         = "16:30 BST"

HOME_FORM       = ["L", "L", "D", "L", "W"]   # oldest -> newest, left to right
AWAY_FORM       = ["W", "W", "W", "D", "W"]
HOME_FORM_NOTE  = "Relegation battle, low confidence"
AWAY_FORM_NOTE  = "Title race leaders. CL finalists."

REASON_1_HEAD   = "SOT per 90 well above threshold"
REASON_1_BODY   = "1.18 SOT per 90 this season (Fotmob). Threshold is 1.0. Comfortably qualifies on our primary metric."

REASON_2_HEAD   = "Arsenal chasing the title — Saka starts"
REASON_2_BODY   = "Win today and Arsenal are champions. Confirmed in the XI. Motivation and quality both point one way."

REASON_3_HEAD   = "West Ham wide open on the flanks"
REASON_3_BODY   = "Saka cuts inside from the right — West Ham's 3-4-2-1 leaves space in behind. He thrives in this setup."

RISK_LINE_1     = "Minute management risk · CL Final May 30 · Recent sub-60 min appearances"
RISK_LINE_2     = "Factored in. Rating: 7/10. Stake: £5."

OUTPUT_PATH     = "/mnt/user-data/outputs/gembets_research_card.png"
# ─────────────────────────────────────────────────────────────────────────────

W, H = 1080, 1080

RED        = (204, 0, 0)
RED_DARK   = (160, 0, 0)
WHITE      = (255, 255, 255)
OFF_WHITE  = (248, 248, 248)
LIGHT_GREY = (230, 230, 230)
MID_GREY   = (170, 170, 170)
DARK_GREY  = (70, 70, 70)
BLACK      = (20, 20, 20)

img  = Image.new("RGB", (W, H), OFF_WHITE)
draw = ImageDraw.Draw(img)

# ── GRADIENT HEADER ───────────────────────────────────────────────────────────
for y in range(220):
    t = y / 220
    r = int(HOME_COLOUR[0] + (AWAY_COLOUR[0] - HOME_COLOUR[0]) * t)
    g = int(HOME_COLOUR[1] + (AWAY_COLOUR[1] - HOME_COLOUR[1]) * t)
    b = int(HOME_COLOUR[2] + (AWAY_COLOUR[2] - HOME_COLOUR[2]) * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

draw.rectangle([0, 0,      W, 5],  fill=RED_DARK)
draw.rectangle([0, H - 60, W, H],  fill=RED_DARK)

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

# ── HEADER TEXT ───────────────────────────────────────────────────────────────
title = "RESEARCH CARD"
bbox  = draw.textbbox((0,0), title, font=load_font(28, bold=True))
draw.text(((W-(bbox[2]-bbox[0]))//2, 16), title, font=load_font(28, bold=True), fill=WHITE)

player_line = f"{PLAYER}  ·  {MARKET}"
bbox = draw.textbbox((0,0), player_line, font=load_font(22, bold=True))
draw.text(((W-(bbox[2]-bbox[0]))//2, 56), player_line, font=load_font(22, bold=True), fill=WHITE)

comp = f"{HOME_TEAM} v {AWAY_TEAM}  ·  {COMPETITION}  ·  {PLATFORM}  ·  {KO_TIME}"
bbox = draw.textbbox((0,0), comp, font=load_font(16))
draw.text(((W-(bbox[2]-bbox[0]))//2, 92), comp, font=load_font(16), fill=(230,200,200))

# ── BADGES ────────────────────────────────────────────────────────────────────
WH_CX, ARS_CX, BADGE_CY, BADGE_R = 148, 348, 155, 44

def fetch_badge(team_id, size=70):
    url = f"https://crests.football-data.org/{team_id}.png"
    r   = requests.get(url, timeout=15)
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
        bbox = draw.textbbox((0,0), initials, font=load_font(16, bold=True))
        draw.text((cx-(bbox[2]-bbox[0])//2, BADGE_CY-(bbox[3]-bbox[1])//2),
                  initials, font=load_font(16, bold=True), fill=col)

# "vs" centred between badges
vs_cx = (WH_CX + ARS_CX) // 2
bbox  = draw.textbbox((0,0), "vs", font=load_font(18))
draw.text((vs_cx-(bbox[2]-bbox[0])//2, 146), "vs", font=load_font(18), fill=WHITE)

# ── FORM SECTION ──────────────────────────────────────────────────────────────
fy = 215
draw.rectangle([40, fy, W-40, fy+1], fill=LIGHT_GREY)
draw.text((50, fy+12), "RECENT FORM", font=load_font(16, bold=True), fill=MID_GREY)

def draw_pill(x, y, result):
    c = {"W": (0,160,60), "D": (180,140,0), "L": (200,0,0)}.get(result, (150,150,150))
    draw.rounded_rectangle([x, y, x+36, y+26], radius=6, fill=c)
    bbox = draw.textbbox((0,0), result, font=load_font(16, bold=True))
    draw.text((x+(36-(bbox[2]-bbox[0]))//2, y+(26-(bbox[3]-bbox[1]))//2),
              result, font=load_font(16, bold=True), fill=WHITE)

draw.text((50, fy+32), HOME_TEAM, font=load_font(17, bold=True), fill=BLACK)
for i, r in enumerate(HOME_FORM):
    draw_pill(50+i*44, fy+58, r)
draw.text((50+5*44+8, fy+62), HOME_FORM_NOTE, font=load_font(15), fill=DARK_GREY)

draw.text((50, fy+100), AWAY_TEAM, font=load_font(17, bold=True), fill=BLACK)
for i, r in enumerate(AWAY_FORM):
    draw_pill(50+i*44, fy+126, r)
draw.text((50+5*44+8, fy+130), AWAY_FORM_NOTE, font=load_font(15), fill=DARK_GREY)

# ── DIVIDER ───────────────────────────────────────────────────────────────────
div_y = 438
draw.rectangle([40, div_y, W-40, div_y+1], fill=LIGHT_GREY)

# ── 3 REASONS ─────────────────────────────────────────────────────────────────
ry = div_y + 16
draw.text((50, ry), "WHY WE'RE BACKING IT", font=load_font(17, bold=True), fill=MID_GREY)
ry += 32

def draw_reason(heading, body):
    global ry
    draw.text((50, ry), heading, font=load_font(19, bold=True), fill=RED)
    ry += 28
    words, line = body.split(), ""
    for w in words:
        test = line + w + " "
        bbox = draw.textbbox((0,0), test, font=load_font(17))
        if bbox[2]-bbox[0] > W-100:
            draw.text((50, ry), line.strip(), font=load_font(17), fill=DARK_GREY)
            ry += 24
            line = w + " "
        else:
            line = test
    if line.strip():
        draw.text((50, ry), line.strip(), font=load_font(17), fill=DARK_GREY)
        ry += 24
    ry += 12

draw_reason(REASON_1_HEAD, REASON_1_BODY)
draw_reason(REASON_2_HEAD, REASON_2_BODY)
draw_reason(REASON_3_HEAD, REASON_3_BODY)

# ── RISK BLOCK ────────────────────────────────────────────────────────────────
risk_y = ry + 8
draw.rounded_rectangle([40, risk_y, W-40, risk_y+95], radius=12, fill=(255,230,230))
draw.rounded_rectangle([40, risk_y, W-40, risk_y+95], radius=12, outline=(220,160,160), width=1)
draw.rounded_rectangle([40, risk_y, 46,   risk_y+95], radius=4,  fill=RED)
draw.text((58, risk_y+10), "RISK FLAGS", font=load_font(17, bold=True), fill=RED)
draw.text((58, risk_y+38), RISK_LINE_1,  font=load_font(17),            fill=DARK_GREY)
draw.text((58, risk_y+64), RISK_LINE_2,  font=load_font(17, bold=True), fill=BLACK)

# ── BOTTOM BAR ────────────────────────────────────────────────────────────────
draw.text((20, H-44),    "💎 @gembets_",          font=load_font(20, bold=True), fill=WHITE)
draw.text((W-180, H-44), "18+ | T&Cs Apply | Ad", font=load_font(16),            fill=(220,200,200))

img.save(OUTPUT_PATH, quality=95)
print(f"Research card saved to {OUTPUT_PATH}")
