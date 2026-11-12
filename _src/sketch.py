"""ZenWrite — hand-drawn ('pencil') SVG generator. Every line is jittered and drawn twice, like ink over pencil.
Paths carry pathLength=1 + --d (delay) so CSS can draw them in order."""
import math, random
from svgpathtools import parse_path

def _r(seed): return random.Random(seed)

PREC = [0]
def _f(v):
    r = f"{v:.{PREC[0]}f}"
    return r[:-2] if r.endswith(".0") else ("0" if r == "-0" else r)

def smooth(pts, closed=False):
    """Catmull-Rom → cubic Bézier path through the points."""
    if len(pts) < 2: return ''
    P = pts[:]
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else: P = [P[0]] + P + [P[-1]]
    d = f'M{_f(P[1][0])} {_f(P[1][1])}'
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{_f(c1[0])} {_f(c1[1])} {_f(c2[0])} {_f(c2[1])} {_f(p2[0])} {_f(p2[1])}'
    return d + ('Z' if closed else '')

def wob_line(a, b, rnd, amp=1.4, over=2.5):
    """one hand-drawn stroke a→b, overshooting the ends a little"""
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = -uy, ux
    o1, o2 = over * rnd.uniform(.2, 1), over * rnd.uniform(.2, 1)
    a2 = (a[0] - ux * o1, a[1] - uy * o1); b2 = (b[0] + ux * o2, b[1] + uy * o2)
    n = max(2, int(L / 38))
    pts = []
    bow = rnd.uniform(-1, 1) * amp * min(1.8, L / 90)
    for i in range(n + 1):
        t = i / n
        k = math.sin(math.pi * t) * bow + (rnd.uniform(-1, 1) * amp * .35 if 0 < i < n else 0)
        pts.append((a2[0] + (b2[0] - a2[0]) * t + nx * k, a2[1] + (b2[1] - a2[1]) * t + ny * k))
    return smooth(pts)

def lines(segs, seed, amp=1.4):
    rnd = _r(seed)
    return ''.join(wob_line(a, b, rnd, amp) for a, b in segs)

def poly(pts, seed, closed=True, amp=1.4):
    segs = list(zip(pts, pts[1:] + ([pts[0]] if closed else [])))
    return lines(segs, seed, amp)

def blob(pts, seed, amp=1.6):
    """closed soft shape (for offset fills)"""
    rnd = _r(seed)
    return smooth([(x + rnd.uniform(-amp, amp), y + rnd.uniform(-amp, amp)) for x, y in pts], closed=True)

def ellipse(cx, cy, rx, ry, seed, amp=.035, turns=1.08, start=None):
    rnd = _r(seed)
    a0 = start if start is not None else rnd.uniform(0, 2 * math.pi)
    n = 26
    pts = []
    for i in range(int(n * turns) + 1):
        a = a0 + 2 * math.pi * i / n
        k = 1 + rnd.uniform(-amp, amp) + .025 * i / n
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return smooth(pts)

def curve(pts, seed, amp=1.2):
    rnd = _r(seed)
    return smooth([(x + rnd.uniform(-amp, amp), y + rnd.uniform(-amp, amp)) for x, y in pts])

def from_d(d, seed, scale=1, dx=0, dy=0, step=4.0, amp=.5):
    """roughen any SVG path (e.g. an icon) — sample every `step` units and jitter"""
    rnd = _r(seed)
    out = ''
    for sub in parse_path(d).continuous_subpaths():
        L = sub.length()
        if L == 0: continue
        n = max(3, int(L * scale / step))
        pts = []
        for i in range(n + 1):
            try: tt = sub.ilength(L * i / n) if i not in (0, n) else (0 if i == 0 else 1)
            except Exception: tt = i / n
            p = sub.point(tt)
            pts.append((p.real * scale + dx + rnd.uniform(-amp, amp), p.imag * scale + dy + rnd.uniform(-amp, amp)))
        out += smooth(pts, closed=sub.isclosed())
    return out

def hatch(x0, y0, x1, y1, gap, seed, ang=-1.0):
    """diagonal shading strokes inside a box"""
    rnd = _r(seed); segs = []
    w = x1 - x0
    k = x0 - (y1 - y0)
    while k < x1:
        a = (max(x0, k), y1 - (max(x0, k) - k)) if ang < 0 else None
        xa, ya = k, y1
        xb, yb = k + (y1 - y0), y0
        # clip to box
        if xa < x0: ya -= (x0 - xa); xa = x0
        if xb > x1: yb += (xb - x1); xb = x1
        if ya > yb: segs.append(((xa + rnd.uniform(-1, 1), ya), (xb + rnd.uniform(-1, 1), yb)))
        k += gap
    return lines(segs, seed, .5)

class Art:
    """collects strokes; render() → SVG markup. kinds: s (stroke), s2 (2nd pencil pass), f (offset fill)"""
    def __init__(self): self.items = []; self.t = 0.0
    def add(self, d, cls='k', w=1.6, dt=.12, fill=None, dur=None):
        self.items.append(('f' if fill else 's', d, cls, w, self.t, fill, dur)); self.t += dt
    def stroke(self, d, cls='k', w=1.6, dt=.12, second=True, dur=None):
        self.items.append(('s', d, cls, w, self.t, None, dur))
        if second: self.items.append(('s2', d, cls, w * .55, self.t + .06, None, dur))
        self.t += dt
    def fill(self, d, color, dt=0):
        self.items.append(('f', d, '', 0, self.t, color, None)); self.t += dt
    def render(self, base=0.0):
        o = []
        for kind, d, cls, w, t, fill, dur in self.items:
            dl = f'{base + t:.2f}s'
            if kind == 'f':
                o.append(f'<path class="df" d="{d}" style="fill:{fill};--d:{dl}"/>')
            else:
                du = f';--u:{dur}s' if dur else ''
                o.append(f'<path class="dr {cls}{" p2" if kind == "s2" else ""}" d="{d}" pathLength="1" style="stroke-width:{w:.2f};--d:{dl}{du}"/>')
        return ''.join(o)

CARD, VERM, VERML, MOSS, MOSSL, INK = '#FCFAF6', '#B0402C', '#EBB9A9', '#5F6B52', '#C9D0BC', '#1B1D21'

# ------------------------------------------------------------------ hero desk scene (viewBox 0 0 640 560)
def hero_scene():
    A = Art()
    # desk
    A.stroke(lines([((14, 478), (626, 474)), ((40, 492), (380, 490))], 1, 1.2), w=2, dt=.25)
    # shadows under objects
    A.stroke(hatch(70, 478, 262, 494, 9, 2), cls='h', w=1, dt=.05, second=False)
    A.stroke(hatch(540, 478, 618, 492, 9, 3), cls='h', w=1, dt=.05, second=False)
    # books stack
    books = [((60, 438), (262, 476), MOSSL), ((74, 404), (248, 438), VERML), ((92, 376), (236, 404), CARD)]
    for i, ((x0, y0), (x1, y1), col) in enumerate(books):
        A.fill(blob([(x0 + 5, y0 + 5), (x1 + 5, y0 + 5), (x1 + 5, y1 + 4), (x0 + 5, y1 + 4)], 10 + i, 1.4), col)
        A.stroke(poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 20 + i), dt=.1)
        A.stroke(lines([((x0 + 14, y0), (x0 + 14, y1)), ((x1 - 30, y0 + (y1 - y0) / 2), (x1 - 8, y0 + (y1 - y0) / 2))], 30 + i, .8), w=1.2, dt=.08, second=False)
    # plant in a pot on the books
    A.fill(blob([(140, 330), (196, 330), (190, 378), (146, 378)], 40), CARD)
    A.stroke(poly([(134, 330), (202, 330), (194, 378), (142, 378)], 41), dt=.1)
    A.stroke(lines([((136, 342), (200, 342))], 42, .6), w=1.1, second=False, dt=.05)
    for j, (tip, c) in enumerate([((120, 250), (128, 300)), ((150, 222), (155, 280)), ((182, 210), (176, 276)), ((222, 236), (196, 290)), ((236, 290), (208, 318))]):
        base = (168, 330)
        mid = ((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2)
        nx, ny = (tip[1] - base[1]), -(tip[0] - base[0])
        L = math.hypot(nx, ny) or 1; nx, ny = nx / L * 13, ny / L * 13
        leaf = [base, (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny)]
        A.fill(blob([(x + 3, y + 3) for x, y in leaf], 50 + j, 1), MOSSL)
        A.stroke(smooth(leaf + [base]), cls='m', w=1.5, dt=.08, second=False)
        A.stroke(curve([base, mid, tip], 60 + j, .4), cls='m', w=.9, dt=.04, second=False)
    # open notebook
    L_ = [(256, 474), (402, 470), (398, 352), (268, 338)]
    R_ = [(402, 470), (552, 474), (542, 336), (406, 352)]
    A.fill(blob([(x + 6, y + 6) for x, y in L_ + R_[1:3]], 70, 1.5), 'rgba(27,29,33,.10)')
    A.fill(blob(L_, 71, 1), CARD); A.fill(blob(R_, 72, 1), CARD)
    A.stroke(poly(L_, 73), dt=.08); A.stroke(poly(R_, 74), dt=.08)
    A.stroke(curve([(402, 470), (401, 412), (402, 352)], 75, .5), w=1.2, dt=.1, second=False)
    for k in range(6):  # handwriting lines (left page)
        y = 362 + k * 16
        x1 = 384 - (26 if k == 5 else (k * 7 % 18))
        pts = [(280 + 4 * k * 0, y + 0)] + [(280 + (x1 - 280) * t / 10, y + math.sin(t * 2.3 + k) * 1.6 - (t * .5)) for t in range(1, 11)]
        A.stroke(smooth(pts), cls='g', w=1.3, dt=.11, second=False)
    # chart on the right page
    for j, h in enumerate([28, 46, 38, 64, 54]):
        x = 424 + j * 22
        A.fill(blob([(x + 2, 450 - h), (x + 15, 450 - h), (x + 15, 452), (x + 2, 452)], 80 + j, .8), VERM if j % 2 == 0 else INK)
        A.stroke(poly([(x, 450 - h - 2), (x + 13, 450 - h - 2), (x + 13, 452), (x, 452)], 90 + j, .8), w=1.1, dt=.06, second=False)
    A.stroke(lines([((416, 360), (416, 456)), ((416, 456), (532, 456))], 99, .6), w=1.3, dt=.08, second=False)
    A.stroke(curve([(422, 430), (446, 410), (468, 418), (492, 386), (520, 372)], 100, .6), cls='v', w=1.8, dt=.2, second=False)
    A.stroke(ellipse(520, 372, 5, 5, 101), cls='v', w=1.4, dt=.05, second=False)
    # pen across the right page
    body = [(462, 322), (476, 314), (568, 438), (556, 446)]
    A.fill(blob(body, 110, .8), INK)
    A.stroke(poly(body, 111), w=1.3, dt=.08, second=False)
    nib = [(556, 446), (568, 438), (574, 468)]
    A.fill(blob(nib, 112, .6), VERM)
    A.stroke(poly(nib, 113), w=1.2, dt=.06, second=False)
    # tea cup + saucer + steam
    A.fill(ellipse(582, 472, 44, 8, 120, .01, 1.0), CARD)
    A.stroke(ellipse(582, 472, 44, 8, 121), dt=.08)
    cup = [(552, 410), (612, 410), (604, 462), (560, 462)]
    A.fill(blob([(x + 4, y + 3) for x, y in cup], 122, 1), VERML)
    A.fill(blob(cup, 123, .8), CARD)
    A.stroke(poly(cup, 124), dt=.08)
    A.stroke(ellipse(582, 410, 30, 6, 125), w=1.3, dt=.06, second=False)
    A.stroke(curve([(610, 422), (630, 424), (628, 444), (606, 448)], 126, .5), w=1.5, dt=.08, second=False)
    steam = ''
    for k in range(3):
        x = 568 + k * 14
        steam += curve([(x, 398), (x - 6, 384), (x + 5, 370), (x - 4, 356), (x + 4, 342)], 130 + k, .4)
    A.stroke(steam, cls='st', w=1.3, dt=.1, second=False)
    # pendant lamp + light cone on the notebook
    A.fill(blob([(452, 194), (532, 194), (566, 352), (414, 356)], 140, 2), 'rgba(232,144,122,.16)')
    A.stroke(lines([((492, -40), (492, 150))], 141, .8), w=1.3, dt=.12, second=False)
    shade = [(470, 150), (514, 150), (536, 194), (448, 194)]
    A.fill(blob([(x + 5, y + 4) for x, y in shade], 142, 1), VERML)
    A.fill(blob(shade, 143, .8), CARD)
    A.stroke(poly(shade, 144), dt=.1)
    A.stroke(ellipse(492, 198, 10, 6, 145), cls='v', w=1.4, dt=.06, second=False)
    A.stroke(lines([((448, 208), (430, 226)), ((492, 214), (492, 236)), ((536, 208), (554, 226))], 146, .3), cls='v', w=1.3, dt=.08, second=False)
    return A

def hero_doodles():
    """floating sketches above the desk — their own layer for depth"""
    A = Art()
    # bell curve with axis
    A.stroke(lines([((52, 168), (182, 168))], 200, .6), w=1.3, dt=.05, second=False)
    pts = [(52 + x, 168 - 64 * math.exp(-((x - 65) / 24) ** 2)) for x in range(0, 131, 10)]
    A.stroke(curve(pts, 201, .5), cls='v', w=1.8, dt=.15)
    A.stroke(lines([((117, 168), (117, 104))], 202, .4), cls='g', w=1, dt=.05, second=False)
    # stars / sparkles
    for j, (x, y, r) in enumerate([(272, 96, 9), (226, 160, 6), (604, 230, 7), (40, 300, 6)]):
        A.stroke(lines([((x - r, y), (x + r, y)), ((x, y - r), (x, y + r)), ((x - r * .6, y - r * .6), (x + r * .6, y + r * .6))], 220 + j, .3), cls='v' if j % 2 == 0 else 'k', w=1.3, dt=.05, second=False)
    # sigma + quotation marks
    A.stroke(poly([(590, 300), (566, 300), (580, 316), (566, 332), (592, 332)], 230, False, .5), w=1.6, dt=.08)
    A.stroke(curve([(312, 150), (306, 140), (312, 132)], 231, .3) + curve([(326, 150), (320, 140), (326, 132)], 232, .3), cls='v', w=2, dt=.06, second=False)
    # arrow + note pointing at the notebook chart
    A.stroke(curve([(352, 214), (392, 236), (422, 280), (440, 318)], 240, .6), w=1.5, dt=.12, second=False)
    A.stroke(lines([((440, 318), (428, 306)), ((440, 318), (446, 302))], 241, .3), w=1.5, dt=.06, second=False)
    # paper airplane + dashed trail
    A.stroke(curve([(240, 70), (300, 40), (360, 60), (330, 92), (300, 70), (360, 34), (420, 40)], 250, .4), cls='tr', w=1.3, dt=.15, second=False)
    plane = [(420, 40), (458, 28), (432, 54)]
    A.fill(blob(plane, 251, .5), CARD)
    A.stroke(poly(plane, 252) + lines([((432, 54), (436, 40)), ((436, 40), (458, 28))], 253, .3), w=1.4, dt=.08, second=False)
    return A

def doodle(kind, seed=0):
    """small margin doodles (viewBox 0 0 80 80)"""
    A = Art()
    if kind == 'star':
        A.stroke(lines([((10, 40), (70, 40)), ((40, 10), (40, 70)), ((19, 19), (61, 61)), ((61, 19), (19, 61))], seed, .6), cls='v', w=2)
    elif kind == 'swirl':
        pts = [(40 + math.cos(a / 3) * a * 1.1, 40 + math.sin(a / 3) * a * 1.1) for a in range(0, 30)]
        A.stroke(curve(pts, seed, .4), w=1.8)
    elif kind == 'arrow':
        A.stroke(curve([(8, 60), (26, 30), (52, 26), (70, 40)], seed, .6) + lines([((70, 40), (56, 30)), ((70, 40), (58, 50))], seed + 1, .3), w=2)
    elif kind == 'leaf':
        A.fill(blob([(14, 66), (34, 20), (68, 10), (52, 52)], seed, 1), MOSSL)
        A.stroke(smooth([(12, 68), (30, 22), (68, 10), (54, 54), (12, 68)]), cls='m', w=1.8)
        A.stroke(curve([(12, 68), (40, 38), (66, 12)], seed + 1, .4), cls='m', w=1.1)
    elif kind == 'bell':
        pts = [(6 + x, 64 - 46 * math.exp(-((x - 34) / 13) ** 2)) for x in range(0, 69, 6)]
        A.stroke(lines([((4, 66), (76, 66))], seed, .4), w=1.4)
        A.stroke(curve(pts, seed + 1, .4), cls='v', w=2)
    elif kind == 'asterisk':
        A.stroke(lines([((40, 14), (40, 66)), ((18, 27), (62, 53)), ((62, 27), (18, 53))], seed, .5), w=2.2)
    elif kind == 'loop':
        A.stroke(curve([(6, 54), (24, 22), (40, 46), (30, 62), (22, 44), (46, 20), (74, 30)], seed, .5), cls='v', w=1.8)
    elif kind == 'check':
        A.stroke(ellipse(40, 40, 30, 28, seed), w=1.6)
        A.stroke(curve([(24, 42), (36, 54), (58, 26)], seed + 1, .5), cls='v', w=2.4)
    return A

def doodle_svg(kind, cls, seed=0, title=None):
    return f'<svg class="dd {cls} draw" viewBox="0 0 80 80" aria-hidden="true">{doodle(kind, seed).render()}</svg>'

def rough_icon(d, seed, size=24, sc=1):
    """icon path (24 grid) → hand-drawn version at viewBox 0 0 48 48"""
    A = Art(); PREC[0] = 1
    A.stroke(from_d(d, seed, scale=2, step=5, amp=.45), w=1.7)
    PREC[0] = 0
    return A

def service_art(icon_d, seed):
    """service hero: a tilted sheet + big hand-drawn icon + doodles (viewBox 0 0 400 400)"""
    A = Art()
    sheet = [(92, 66), (312, 52), (330, 330), (106, 346)]
    A.fill(blob([(x + 10, y + 12) for x, y in sheet], seed, 1.5), 'rgba(27,29,33,.12)')
    A.fill(blob(sheet, seed + 1, 1), CARD)
    A.stroke(poly(sheet, seed + 2), w=1.8, dt=.2)
    A.stroke(lines([((112, 300), (300, 288)), ((114, 318), (250, 310))], seed + 3, .6), cls='g', w=1.2, dt=.1, second=False)
    A.stroke(from_d(icon_d, seed + 4, scale=8.2, dx=113, dy=82, step=9, amp=1.1), w=2.6, dt=.5)
    A.stroke(ellipse(340, 70, 10, 10, seed + 5), cls='v', w=1.6, dt=.05, second=False)
    A.stroke(lines([((40, 210), (62, 210)), ((51, 199), (51, 221))], seed + 6, .3), cls='v', w=1.6, dt=.05, second=False)
    A.stroke(curve([(300, 372), (330, 360), (352, 330), (368, 296)], seed + 7, .5) + lines([((368, 296), (356, 304)), ((368, 296), (370, 310))], seed + 8, .3), w=1.5, dt=.1, second=False)
    return A

def cta_plane():
    """paper plane flying a looping dashed path (viewBox 0 0 900 240)"""
    A = Art()
    A.stroke(curve([(20, 200), (160, 150), (260, 60), (340, 110), (300, 170), (240, 120), (360, 60), (520, 90), (680, 70), (800, 60)], 300, .6), cls='tr', w=1.6, dt=.3, second=False)
    plane = [(800, 60), (870, 36), (824, 88)]
    A.fill(blob(plane, 301, .6), 'rgba(246,242,234,.92)')
    A.stroke(poly(plane, 302) + lines([((824, 88), (830, 62)), ((830, 62), (870, 36))], 303, .3), cls='pp', w=1.6, dt=.1, second=False)
    return A

def rule_line(seed, w=1200):
    rnd = _r(seed)
    pts = [(x, 12 + math.sin(x / 70 + seed) * 4 + rnd.uniform(-1.2, 1.2)) for x in range(0, w + 1, 40)]
    A = Art(); A.stroke(smooth(pts), w=1.6, dt=0); return A

# ------------------------------------------------------------------ statistics hero chart (viewBox 0 0 800 700)
PX0, PX1, PY0, PY1 = 112, 732, 604, 136          # plot box: left, right, bottom, top

def hero_data(n=44, seed=7):
    rnd = _r(seed); pts = []
    for i in range(n):
        x = rnd.uniform(.6, 9.4)
        y = 1.3 + .68 * x + rnd.gauss(0, 1.25)
        pts.append((round(x, 2), round(min(9.7, max(.3, y)), 2)))
    return pts

def mx(x): return PX0 + (PX1 - PX0) * x / 10
def my(y): return PY0 - (PY0 - PY1) * y / 10

def hero_chart():
    pts = hero_data()
    A = Art()
    # axes with arrow heads
    A.stroke(lines([((PX0, PY0 + 6), (PX0, PY1 - 30)), ((PX0 - 6, PY0), (PX1 + 30, PY0))], 400, .8), w=2.2, dt=.18)
    A.stroke(lines([((PX0, PY1 - 30), (PX0 - 8, PY1 - 16)), ((PX0, PY1 - 30), (PX0 + 8, PY1 - 16)),
                    ((PX1 + 30, PY0), (PX1 + 16, PY0 - 8)), ((PX1 + 30, PY0), (PX1 + 16, PY0 + 8))], 401, .3), w=2, dt=.1, second=False)
    ticks = [((mx(k), PY0 - 5), (mx(k), PY0 + 7)) for k in range(1, 11)] + [((PX0 - 7, my(k)), (PX0 + 5, my(k))) for k in range(1, 11)]
    A.stroke(lines(ticks, 402, .3), cls='g', w=1.2, dt=.1, second=False)
    # marginal histogram of X (top)
    bins = [0] * 10
    for x, y in pts: bins[min(9, int(x))] += 1
    m = max(bins)
    for i, b in enumerate(bins):
        h = 62 * b / m
        x0, x1 = mx(i) + 5, mx(i + 1) - 5
        A.fill(blob([(x0 + 3, 112 - h + 3), (x1 + 3, 112 - h + 3), (x1 + 3, 114), (x0 + 3, 114)], 410 + i, .6), 'rgba(176,64,44,.22)')
        A.stroke(poly([(x0, 112 - h), (x1, 112 - h), (x1, 112), (x0, 112)], 420 + i, .5), w=1.2, dt=.035, second=False)
    # marginal density of Y (right) — sideways bell
    bell = [(PX1 + 44 + 46 * math.exp(-((y - 5.2) / 1.9) ** 2), my(y)) for y in [k / 2 for k in range(0, 21)]]
    A.stroke(lines([((PX1 + 44, my(0)), (PX1 + 44, my(10)))], 430, .4), cls='g', w=1.1, dt=.05, second=False)
    A.stroke(curve(bell, 431, .5), cls='v', w=1.8, dt=.2)
    return A, pts

def mini(kind, seed=0):
    """small analysis sketches, viewBox 0 0 120 80"""
    A = Art(); rnd = _r(seed)
    base = lines([((8, 72), (114, 72))], seed + 1, .4)
    if kind == 'bars':
        A.stroke(base, w=1.4)
        for i, h in enumerate([22, 40, 30, 54, 34]):
            x = 16 + i * 19
            A.fill(blob([(x + 3, 72 - h + 3), (x + 14, 72 - h + 3), (x + 14, 72), (x + 3, 72)], seed + 10 + i, .6), VERML if i % 2 else MOSSL)
            A.stroke(poly([(x, 72 - h), (x + 12, 72 - h), (x + 12, 72), (x, 72)], seed + 20 + i, .5), w=1.3, second=False, dt=.05)
    elif kind == 'bell':
        A.stroke(base, w=1.4)
        for i, h in enumerate([6, 14, 28, 44, 50, 42, 26, 13, 5]):
            x = 14 + i * 10.5
            A.stroke(poly([(x, 72 - h), (x + 9, 72 - h), (x + 9, 72), (x, 72)], seed + 30 + i, .3), cls='g', w=1, second=False, dt=.02)
        A.stroke(curve([(10 + k, 72 - 54 * math.exp(-((k - 50) / 19) ** 2)) for k in range(0, 101, 8)], seed + 2, .4), cls='v', w=2)
    elif kind == 'box':
        A.stroke(base, w=1.4)
        for i, (lo, q1, md, q3, hi) in enumerate([(14, 26, 34, 44, 58), (22, 36, 46, 54, 66), (10, 20, 26, 34, 44)]):
            x = 22 + i * 32
            A.stroke(lines([((x + 9, 72 - lo), (x + 9, 72 - q1)), ((x + 9, 72 - q3), (x + 9, 72 - hi)), ((x + 3, 72 - hi), (x + 15, 72 - hi)), ((x + 3, 72 - lo), (x + 15, 72 - lo))], seed + 40 + i, .3), w=1.1, second=False, dt=.04)
            A.fill(blob([(x + 2, 72 - q3 + 2), (x + 20, 72 - q3 + 2), (x + 20, 72 - q1 + 2), (x + 2, 72 - q1 + 2)], seed + 45 + i, .5), VERML if i == 1 else MOSSL)
            A.stroke(poly([(x, 72 - q3), (x + 18, 72 - q3), (x + 18, 72 - q1), (x, 72 - q1)], seed + 50 + i, .4), w=1.3, second=False, dt=.04)
            A.stroke(lines([((x, 72 - md), (x + 18, 72 - md))], seed + 55 + i, .2), cls='v', w=2, second=False, dt=.03)
    elif kind == 'grid':
        for r in range(3):
            for c in range(4):
                x, y = 14 + c * 24, 10 + r * 20
                if (r + c) % 3 == 0: A.fill(blob([(x + 2, y + 2), (x + 22, y + 2), (x + 22, y + 18), (x + 2, y + 18)], seed + 60 + r * 4 + c, .5), VERML)
        segs = [((12, 10 + r * 20), (110, 10 + r * 20)) for r in range(4)] + [((12 + c * 24, 8), (12 + c * 24, 72)) for c in range(5)]
        A.stroke(lines(segs, seed + 3, .6), w=1.2, second=False)
        A.stroke(curve([(70, 34), (76, 26), (82, 34), (88, 26)], seed + 4, .3), cls='v', w=1.6, second=False)
    elif kind in ('scatter', 'reg'):
        A.stroke(lines([((10, 74), (10, 6)), ((8, 72), (114, 72))], seed + 1, .4), w=1.4)
        for i in range(16):
            x = rnd.uniform(16, 106); y = 66 - (x - 10) * .5 + rnd.gauss(0, 7)
            A.fill(ellipse(x, max(10, min(68, y)), 2.6, 2.6, seed + 70 + i, .1, 1.0), INK)
        if kind == 'reg':
            A.stroke(lines([((14, 64), (110, 16))], seed + 5, .8), cls='v', w=2.2)
        else:
            A.stroke(ellipse(60, 42, 50, 18, seed + 6, .04), cls='g', w=1.1, second=False)
    elif kind == 'logit':
        A.stroke(lines([((10, 74), (10, 6)), ((8, 72), (114, 72))], seed + 1, .4), w=1.4)
        A.stroke(lines([((12, 14), (112, 14))], seed + 7, .3), cls='g', w=1, second=False)
        A.stroke(curve([(x, 72 - 58 / (1 + math.exp(-(x - 62) / 9))) for x in range(12, 113, 8)], seed + 8, .3), cls='v', w=2.2)
    elif kind == 'factor':
        for i in range(2):
            A.fill(ellipse(28 + i * 64, 18, 16, 11, seed + 80 + i, .03, 1.0), MOSSL)
            A.stroke(ellipse(28 + i * 64, 18, 16, 11, seed + 82 + i), w=1.4)
        for j in range(6):
            x = 12 + j * 19
            A.stroke(poly([(x, 58), (x + 14, 58), (x + 14, 72), (x, 72)], seed + 90 + j, .4), w=1.2, second=False, dt=.03)
            A.stroke(lines([((28 + (j // 3) * 64, 29), (x + 7, 57))], seed + 100 + j, .3), cls='v', w=1.1, second=False, dt=.03)
    elif kind == 'alpha':
        A.stroke(curve([(18, 66), (40, 24), (60, 14), (80, 24), (102, 66)], seed + 9, .4), cls='g', w=1.4, second=False)
        A.stroke(lines([((60, 66), (86, 30))], seed + 10, .4), cls='v', w=2.4)
        A.fill(ellipse(60, 66, 5, 5, seed + 11, .1, 1.0), INK)
        A.stroke(lines([((18, 66), (24, 60)), ((102, 66), (96, 60)), ((60, 14), (60, 21))], seed + 12, .2), w=1.2, second=False)
    elif kind == 'sem':
        for (x, y) in [(10, 10), (10, 52), (84, 31)]:
            A.fill(blob([(x + 3, y + 3), (x + 30, y + 3), (x + 30, y + 21), (x + 3, y + 21)], seed + int(x + y), .5), VERML if x > 50 else MOSSL)
            A.stroke(poly([(x, y), (x + 27, y), (x + 27, y + 18), (x, y + 18)], seed + 120 + int(x + y), .5), w=1.3)
        A.stroke(lines([((38, 20), (82, 38)), ((38, 60), (82, 44)), ((82, 38), (75, 32)), ((82, 38), (74, 41)), ((82, 44), (74, 41)), ((82, 44), (76, 50))], seed + 13, .3), w=1.4, second=False)
        A.stroke(curve([(6, 26), (0, 40), (6, 54)], seed + 14, .2), cls='v', w=1.3, second=False)
    elif kind == 'med':
        for (x, y, c) in [(10, 52, MOSSL), (46, 8, VERML), (84, 52, MOSSL)]:
            A.fill(ellipse(x + 13, y + 10, 14, 10, seed + 130 + x, .03, 1.0), c)
            A.stroke(ellipse(x + 13, y + 10, 14, 10, seed + 135 + x), w=1.3)
        A.stroke(lines([((26, 54), (50, 26)), ((72, 26), (92, 52)), ((28, 62), (84, 62)), ((84, 62), (76, 57)), ((84, 62), (76, 67)), ((92, 52), (84, 50)), ((92, 52), (91, 44)), ((50, 26), (49, 34)), ((50, 26), (57, 29))], seed + 15, .3), w=1.3, second=False)
    elif kind == 'ts':
        A.stroke(base, w=1.4)
        pts = [(10 + i * 6, 50 - i * .9 - 12 * math.sin(i / 2.2) + rnd.uniform(-2, 2)) for i in range(18)]
        A.stroke(curve(pts, seed + 16, .3), w=1.8)
        A.stroke(lines([((10, 52), (112, 32))], seed + 17, .4), cls='v', w=1.6, second=False)
        A.stroke(curve([(100, 36), (106, 30), (112, 34)], seed + 18, .2) , cls='g', w=1.2, second=False)
    return A
