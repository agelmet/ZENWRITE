#!/usr/bin/env python3
"""ZenWrite site generator. python3 build.py  → ../site/"""
import math, os, re, json, shutil, subprocess, html
from data import S, T, GROUPS, DOMAIN, BRAND, EMAIL, PHONE, VIBER, WHATSAPP
import sketch as SK

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'site'))
FS = '/home/claude/tools/node_modules/@fontsource'
TERSER = '/home/claude/tools/node_modules/.bin/terser'
e = lambda s: html.escape(str(s), quote=True)
TODAY = __import__('datetime').date.today().isoformat()

# ---------------------------------------------------------------- ensō
def enso(cx=50, cy=50, R=36, maxw=4.8, a0=208, sweep=318, seed=0.7, steps=96):
    out, inn = [], []
    for i in range(steps + 1):
        t = i / steps
        th = math.radians(a0 + sweep * t)
        r = R + 1.1 * math.sin(3 * th + seed) + .55 * math.sin(7 * th + 2 * seed)
        press = 1.0 if t > .06 else (.55 + .45 * t / .06)          # brush lands
        swell = .62 + .38 * math.sin(math.pi * min(1, t * 1.15)) ** .7
        tail = 1 - max(0, (t - .72) / .28) ** 1.6 * .86              # dry-brush tail
        w = maxw * press * swell * tail
        x, y = math.cos(th), math.sin(th)
        out.append((cx + x * (r + w), cy + y * (r + w)))
        inn.append((cx + x * (r - w * .82), cy + y * (r - w * .82)))
    pts = out + inn[::-1]
    d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + 'Z'
    # dry strands at the tail
    strands = []
    for k, off in enumerate((-.55, .1, .6)):
        sp = []
        for i in range(int(steps * .7), steps + 1):
            t = i / steps
            th = math.radians(a0 + sweep * t + (k - 1) * .8)
            r = R + 1.1 * math.sin(3 * th + seed) + .55 * math.sin(7 * th + 2 * seed) + off * maxw * .9
            sp.append((cx + math.cos(th) * r, cy + math.sin(th) * r))
        strands.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in sp))
    a1 = math.radians(a0); a2 = math.radians(a0 + sweep)
    big = 1 if sweep > 180 else 0
    guide = f'M{cx+R*math.cos(a1):.2f} {cy+R*math.sin(a1):.2f} A{R} {R} 0 {big} 1 {cx+R*math.cos(a2):.2f} {cy+R*math.sin(a2):.2f}'
    return d, strands, guide

ENSO_D, ENSO_ST, ENSO_G = enso()
NIB = 'M43 35h14v8.5c0 7.5-3.4 15.2-7 22.5c-3.6-7.3-7-15-7-22.5Z'

def logo_symbol():
    st = ''.join(f'<path d="{s}" class="st" style="stroke:var(--lg-i,#1B1D21);stroke-width:{w};fill:none;stroke-linecap:round;opacity:{o}"/>'
                 for s, w, o in zip(ENSO_ST, (.6, .45, .55), (.55, .4, .5)))
    return (f'<symbol id="eo" viewBox="0 0 100 100"><path d="{ENSO_D}"/></symbol><symbol id="zw" viewBox="0 0 100 100"><use href="#eo" style="fill:var(--lg-i,#1B1D21)"/>{st}'
            f'<path d="{NIB}" style="fill:var(--lg-v,#B8432F)"/><path d="M50 49v16" style="stroke:var(--lg-p,#F6F2EA);stroke-width:1.5;stroke-linecap:round"/>'
            f'<circle cx="50" cy="47.5" r="2.1" style="fill:var(--lg-p,#F6F2EA)"/></symbol>')

ICONS = {
 'doc': 'M7 3h7l4 4v14H7z M14 3v4h4 M9.5 11h6 M9.5 14h6 M9.5 17h4',
 'cap': 'M2 9l10-5 10 5-10 5z M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5 M22 9v6',
 'book': 'M3 5c3-1 6-1 9 1 3-2 6-2 9-1v14c-3-1-6-1-9 1-3-2-6-2-9-1z M12 6v14',
 'column': 'M3 21h18 M4 8h16 M12 3l9 5H3z M6 8v10 M10 8v10 M14 8v10 M18 8v10 M4 18h16',
 'journal': 'M6 3h11a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6z M6 3a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2 M9 7h6 M9 10h6',
 'chart': 'M4 20V4 M4 20h16 M8 16v-4 M12 16V8 M16 16v-6 M7 9l4-3 4 2 4-4',
 'code': 'M8 7l-5 5 5 5 M16 7l5 5-5 5 M14 4l-4 16',
 'screen': 'M3 4h18v12H3z M12 16v4 M8 20h8 M7 12l3-3 2 2 4-4',
 'nib': 'M12 21l-5-8 2-9h6l2 9z M12 21v-7 M10 4h4',
 'lens': 'M10.5 17a6.5 6.5 0 1 0 0-13a6.5 6.5 0 0 0 0 13z M15.5 15.5L21 21 M8 9h5 M8 12h4',
 'compass': 'M12 21a9 9 0 1 0 0-18a9 9 0 0 0 0 18z M15.5 8.5l-2 5-5 2 2-5z',
 'table': 'M3 4h18v16H3z M3 9h18 M3 14h18 M9 4v16 M15 4v16',
 'clip': 'M8 3h8v3H8z M7 4.5H5v17h14v-17h-2 M8 11l1.5 1.5L12 10 M14 11h3 M8 16l1.5 1.5L12 15 M14 16h3',
 'sem': 'M3 4h6v4H3z M15 4h6v4h-6z M9 16h6v4H9z M9 6h6 M6 8l5 8 M18 8l-5 8',
 'scatter': 'M4 3v17h17 M7 15l1 1 M7 16l1-1 M10 11l1 1 M10 12l1-1 M13 13l1 1 M13 14l1-1 M15 8l1 1 M15 9l1-1 M18 6l1 1 M18 7l1-1 M6 18L20 5',
 'rcode': 'M8 7l-5 5 5 5 M16 7l5 5-5 5 M10.5 17V8h2.5a2.2 2.2 0 0 1 0 4.4h-2.5 M12.5 12.4l2 4.6',
}
def icon(k, cls='ic'):
    paths = ''.join(f'<path d="{p.strip() if p.strip().startswith("M") else "M"+p.strip()}" pathLength="1"/>' for p in re.split(r'\s(?=M)', ICONS[k]))
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{paths}</svg>'

def ricon(k, seed=0, cls='ri'):
    return f'<svg class="{cls} draw" viewBox="0 0 48 48" aria-hidden="true">{SK.rough_icon(ICONS[k], 500 + seed).render()}</svg>'
def dd(kind, cls, seed=0): return SK.doodle_svg(kind, cls, seed)
def scaled(art, speed, base=0.0):
    for i, it in enumerate(art.items):
        art.items[i] = it[:4] + (it[4] * speed,) + it[5:]
    return art.render(base)
HERO_SCENE = scaled(SK.hero_scene(), .34, .1)
_CH, CHART_PTS = SK.hero_chart()
CHART_ART = scaled(_CH, .5, .1)
HERO_DOOD = scaled(SK.hero_doodles(), .45, 2.2)
CTA_PLANE = SK.cta_plane().render()

FLAG = {
 'el': '<svg viewBox="0 0 27 18" preserveAspectRatio="xMidYMid slice" style="display:block;width:100%;height:100%"><rect width="27" height="18" fill="#0D5EAF"/><path d="M0 3h27M0 7h27M0 11h27M0 15h27" stroke="#fff" stroke-width="2"/><rect width="10" height="10" fill="#0D5EAF"/><path d="M5 0v10M0 5h10" stroke="#fff" stroke-width="2"/></svg>',
 'en': '<svg viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" style="display:block;width:100%;height:100%"><clipPath id="uk"><path d="M0 0v30h60V0z"/></clipPath><g clip-path="url(#uk)"><path d="M0 0v30h60V0z" fill="#012169"/><path d="M0 0l60 30m0-30L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0l60 30m0-30L0 30" stroke="#C8102E" stroke-width="4"/><path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/><path d="M30 0v30M0 15h60" stroke="#C8102E" stroke-width="6"/></g></svg>',
}

# ---------------------------------------------------------------- paths
def spath(s, lang): return ('' if lang == 'el' else 'en/') + (s['slug_' + lang] + '/')
def homepath(lang): return '' if lang == 'el' else 'en/'
def rel(frm, to):
    depth = frm.count('/')
    r = '../' * depth + to
    return r or './'
def absu(p): return DOMAIN + '/' + p

# ---------------------------------------------------------------- fonts
FACES = [('Source Serif 4', 'source-serif-4', 300, 'normal'), ('Source Serif 4', 'source-serif-4', 300, 'italic'),
         ('Source Serif 4', 'source-serif-4', 400, 'normal'), ('Commissioner', 'commissioner', 400, 'normal'),
         ('Commissioner', 'commissioner', 600, 'normal')]
RANGES = {'greek': 'U+0370-0377,U+037A-037F,U+0384-038A,U+038C,U+038E-03A1,U+03A3-03FF',
          'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'}
def fonts(pref):
    """one merged Greek+Latin file per face (src/fonts, built with fontTools.merge from @fontsource subsets)"""
    os.makedirs(f'{OUT}/assets/fonts', exist_ok=True)
    css = []
    for fam, pkg, w, st in FACES:
        fn = f'{pkg}-el-{w}-{st}.woff2'
        shutil.copy(f'{HERE}/fonts/{fn}', f'{OUT}/assets/fonts/{fn}')
        css.append(f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};font-display:swap;src:url({pref}assets/fonts/{fn}) format('woff2');unicode-range:{RANGES['latin']},{RANGES['greek']}}}")
    return ''.join(css)

def minify_css(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*([{}:;,>])\s*', r'\1', s)
    return s.replace(';}', '}').strip()

CSS = minify_css(open(f'{HERE}/style.css').read())
JS_SRC = open(f'{HERE}/script.js').read()
JS = subprocess.run([TERSER, '-c', '-m', '--ecma', '2018'], input=JS_SRC, capture_output=True, text=True, check=True).stdout.strip()

GUARD = ('<script id="advon-draft-guard">/* Advon: drafts stay out of Google; the real domain is untouched */'
         '(function(h){if(/(^|\\.)(drafts\\.advonmedia\\.com|github\\.io|netlify\\.app)$/.test(h)){'
         'var m=document.createElement("meta");m.name="robots";m.content="noindex,nofollow";'
         'document.head.appendChild(m)}})(location.hostname)</script>')
HEADJS = ("document.documentElement.classList.add('js');try{if(!sessionStorage.getItem('zw-in')&&!document.hidden&&"
          "!matchMedia('(prefers-reduced-motion:reduce)').matches){document.documentElement.classList.add('zi');sessionStorage.setItem('zw-in','1')}}catch(e){}")

# ---------------------------------------------------------------- chrome
def mega(L, here):
    cols = []
    for g, gt in GROUPS.items():
        items = ''.join(f'<li><a href="{rel(here, spath(s, L))}">{icon(s["icon"])}<span>{e(s[L]["name"])}</span></a></li>' for s in S if s['group'] == g)
        cols.append(f'<div class="mg-c"><p class="mg-h">{e(gt[L])}</p><ul>{items}</ul></div>')
    return ''.join(cols)

def header(L, here, alt):
    t = T[L]; h = "" if here == homepath(L) else rel(here, homepath(L))
    other = T[L]['other']
    return f'''<a class="skip" href="#main">{e(t["skip"])}</a>
<div class="prog" aria-hidden="true"><i></i></div>
<header class="hd" id="hd"><div class="hd-in">
<a class="brand" href="{h}#top" title="{BRAND} — {e(t["home_lbl"])}"><svg class="lg" viewBox="0 0 100 100" aria-hidden="true"><use href="#zw"/></svg><span class="wm">Zen<i>Write</i></span></a>
<nav class="nav" aria-label="{e(t["menu"])}"><ul>
<li class="has-mg"><button class="nv-b" type="button" aria-expanded="false" aria-controls="mg">{e(t["nav_services"])}<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5"/></svg></button>
<div class="mg" id="mg">{mega(L, here)}</div></li>
<li><a href="{h}#diadikasia">{e(t["nav_how"])}</a></li>
<li><a href="{h}#faq">{e(t["nav_faq"])}</a></li></ul></nav>
<div class="hd-r"><a class="flag" href="{rel(here, alt)}" hreflang="{other}" lang="{other}" title="{e(t["switch"])}"><span class="fl" aria-hidden="true">{FLAG[other]}</span><span class="fl-t">{other.upper()}</span><span class="sr"> · {e(t["switch"])}</span></a>
<a class="btn btn-s" href="{h}#prosfora">{e(t["nav_quote"])}</a>
<button class="burger" type="button" aria-label="{e(t["menu"])}" aria-expanded="false" aria-controls="drawer"><i></i><i></i></button></div>
</div></header>
<div class="drawer" id="drawer" hidden><div class="dr-in">
<button class="dr-x" type="button" aria-label="{e(t["close"])}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"/></svg></button>
<p class="dr-h">{e(t["nav_services"])}</p><ul class="dr-s">{"".join(f'<li><a href="{rel(here, spath(s, L))}">{e(s[L]["name"])}</a></li>' for s in S)}</ul>
<ul class="dr-m"><li><a href="{h}#diadikasia">{e(t["nav_how"])}</a></li><li><a href="{h}#faq">{e(t["nav_faq"])}</a></li></ul>
<a class="btn" href="{h}#prosfora">{e(t["nav_quote"])}</a>
<a class="flag dr-f" href="{rel(here, alt)}" hreflang="{other}" lang="{other}"><span class="fl" aria-hidden="true">{FLAG[other]}</span>{e(t["switch"])}</a>
</div></div>'''

def footer(L, here):
    t = T[L]; h = "" if here == homepath(L) else rel(here, homepath(L))
    svc = ''.join(f'<li><a href="{rel(here, spath(s, L))}">{e(s[L]["name"])}</a></li>' for s in S)
    tel = f'<li><a href="tel:{PHONE}">{e(PHONE)}</a></li>' if PHONE else ''
    return f'''<footer class="ft"><div class="ft-in">
<div class="ft-b"><a class="brand" href="{h}#top"><svg class="lg" viewBox="0 0 100 100" aria-hidden="true"><use href="#zw"/></svg><span class="wm">Zen<i>Write</i></span></a>
<p>{e(t["ft_tag"])}</p><p class="ft-a">{e(t["ft_area"])}</p></div>
<div class="ft-c"><p class="ft-h">{e(t["nav_services"])}</p><ul class="ft-s">{svc}</ul></div>
<div class="ft-c"><p class="ft-h">{e(t["ct_k"])}</p><ul><li><a href="mailto:{EMAIL}">{EMAIL}</a></li>{tel}<li><a href="{h}#prosfora">{e(t["nav_quote"])}</a></li><li><a href="{h}#faq">{e(t["nav_faq"])}</a></li></ul></div>
</div>
<div class="ft-l"><span>© {TODAY[:4]} {BRAND}</span><span><a href="{rel(here, 'privacy.html')}">{e(t["privacy"])}</a> <span aria-hidden="true">·</span> <a class="adv-l" href="https://advonmedia.com" rel="noopener">Designed by <b class="adv">Advon Media</b></a></span></div>
</footer>
<nav class="mbar" aria-label="{e(t["ct_k"])}"><a href="{h}#prosfora"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19l2-6 9-9 4 4-9 9-6 2zM14 6l4 4"/></svg>{e(t["mb_quote"])}</a>
<a href="mailto:{EMAIL}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18v12H3z M3 7l9 6 9-6"/></svg>{e(t["mb_mail"])}</a></nav>
<a class="totop" href="#top" aria-label="{e(t["totop"])}"><svg viewBox="0 0 48 48" aria-hidden="true"><circle class="tt-r" cx="24" cy="24" r="21" pathLength="1"/><path d="M24 31V17M18 23l6-6 6 6"/></svg></a>'''

def intro(L):
    return f'''<div class="intro" aria-hidden="true"><div class="ia-l"></div><div class="ia-r"></div>
<div class="ia-c"><svg viewBox="0 0 100 100" class="ia-e"><defs><mask id="inm"><path d="{ENSO_G}" pathLength="1" class="ia-g"/></mask></defs><use href="#eo" mask="url(#inm)" class="ia-k"/><path d="{NIB}" class="ia-n"/></svg>
<span class="ia-w">Zen<i>Write</i></span><span class="ia-s">{"ZW"}</span></div></div>'''

def page(L, here, alt, title, desc, body, ld, extra_head=''):
    t = T[L]; pref = rel(here, '')
    pref = '' if pref == './' else pref
    other = t['other']
    fontcss = fonts(pref)
    pre = (f'<link rel="preload" href="{pref}assets/fonts/source-serif-4-el-300-normal.woff2" as="font" type="font/woff2" crossorigin>'
           f'<link rel="preload" href="{pref}assets/fonts/commissioner-el-400-normal.woff2" as="font" type="font/woff2" crossorigin>')
    hl = (f'<link rel="alternate" hreflang="{L}" href="{absu(here)}"><link rel="alternate" hreflang="{other}" href="{absu(alt)}">'
          f'<link rel="alternate" hreflang="x-default" href="{absu(here if L=="el" else alt)}">')
    return f'''<!doctype html>
<html lang="{L}" id="top"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large">{GUARD}
<link rel="canonical" href="{absu(here)}">{hl}
<meta name="theme-color" content="#F6F2EA"><meta name="color-scheme" content="light only">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}"><meta property="og:locale" content="{t["locale"]}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{absu(here)}">
<meta property="og:image" content="{DOMAIN}/assets/img/zenwrite-akadimaiki-ypostirixi-og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="ZenWrite — {e(t["eyebrow"])}">
<meta name="twitter:card" content="summary_large_image">{pre}
<style id="advon-fonts">{fontcss}</style><style>{CSS}</style>
<script>{HEADJS}</script>{extra_head}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',', ':'))}</script>
</head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{logo_symbol()}</svg>
{intro(L)}{header(L, here, alt)}
<main id="main">{body}</main>
{footer(L, here)}
<script>{JS}</script>
</body></html>'''

# ---------------------------------------------------------------- schema
def org(L):
    t = T[L]
    o = {'@type': 'ProfessionalService', '@id': DOMAIN + '/#org', 'name': BRAND, 'alternateName': ['Zen Write', 'zenwrite.gr'],
         'url': DOMAIN + '/', 'logo': DOMAIN + '/assets/icons/icon-512.png', 'image': DOMAIN + '/assets/img/zenwrite-akadimaiki-ypostirixi-og.jpg',
         'description': T['el']['about_p'], 'email': EMAIL,
         'areaServed': [{'@type': 'Country', 'name': 'Greece'}, {'@type': 'Country', 'name': 'Cyprus'}],
         'availableLanguage': ['el', 'en'], 'knowsAbout': [s['el']['name'] for s in S] + ['SPSS', 'R', 'AMOS', 'SmartPLS', 'APA 7'],
         'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': T['el']['nav_services'],
              'itemListElement': [{'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': s['el']['name'], 'url': absu(spath(s, 'el'))}} for s in S]}}
    if PHONE: o['telephone'] = PHONE
    return o

def faq_ld(items): return {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in items]}

def webpage(L, here, title, desc):
    return {'@type': 'WebPage', '@id': absu(here) + '#webpage', 'url': absu(here), 'name': title, 'description': desc, 'inLanguage': L,
            'isPartOf': {'@id': DOMAIN + '/#website'}, 'about': {'@id': DOMAIN + '/#org'}, 'dateModified': TODAY}

WEBSITE = {'@type': 'WebSite', '@id': DOMAIN + '/#website', 'url': DOMAIN + '/', 'name': BRAND, 'alternateName': ['Zen Write', 'zenwrite.gr'],
           'inLanguage': ['el', 'en'], 'publisher': {'@id': DOMAIN + '/#org'}}

# ---------------------------------------------------------------- home
def faq_html(items, cls='faq-l'):
    return f'<div class="{cls}">' + ''.join(
        f'<details class="fq" data-rv><summary><span>{e(q)}</span><i aria-hidden="true"></i></summary><div class="fq-a"><p>{e(a)}</p></div></details>' for q, a in items) + '</div>'

def chips(arr): return ''.join(f'<li>{e(x)}</li>' for x in arr)

def home(L):
    t = T[L]; here = homepath(L); alt = homepath(t['other'])
    rows = []
    n = 0
    for g, gt in GROUPS.items():
        rr = []
        for s in [s for s in S if s['group'] == g]:
            n += 1
            rr.append(f'<li data-rv><a class="sv" href="{rel(here, spath(s, L))}"><span class="sv-n">{n:02d}</span>{ricon(s["icon"], n, "ri sv-i")}'
                      f'<span class="sv-t"><span class="sv-h">{e(s[L]["name"])}</span><span class="sv-p">{e(s[L]["short"])}</span></span>'
                      f'<span class="sv-a" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M7 17 17 7M9 7h8v8"/></svg></span></a></li>')
        rows.append(f'<div class="sv-g"><p class="sv-gh" data-rv>{e(gt[L])}</p><ul class="sv-l">{"".join(rr)}</ul></div>')
    JI = ['compass', 'clip', 'table', 'chart', 'scatter', 'nib', 'screen']
    jr = ''.join(f'<li class="jr-s" data-rv><span class="jr-d" aria-hidden="true"></span><div class="jr-c sk">{ricon(JI[i], i, "ri jr-i")}<span class="jr-n">{i+1:02d}</span><h3>{e(a)}</h3><p>{e(b)}</p></div></li>' for i, (a, b) in enumerate(t['jr']))
    pr = ''.join(f'<li class="pr-c sk ch" data-rv style="--i:{i}"><span class="pr-n">{i+1}</span><h3>{e(a)}</h3><p>{e(b)}</p></li>' for i, (a, b) in enumerate(t['pr']))
    ph = ''.join(f'<li data-rv style="--i:{i}"><h3>{e(a)}</h3><p>{e(b)}</p></li>' for i, (a, b) in enumerate(t['ph']))
    facts = ''.join(f'<div><dt>{e(a)}</dt><dd>{(f"<a href=mailto:{EMAIL}>{EMAIL}</a>" if b == "email" else e(b))}</dd></div>' for a, b in t['facts'])
    fields = ''.join(f'<span>{e(f.strip())}</span><svg viewBox="0 0 100 100" aria-hidden="true"><use href="#zw"/></svg>' for f in t['fields'].split('·'))
    qtypes = ''.join(f'<label class="qc"><input type="radio" name="qt" value="{e(s[L]["name"])}" data-k="{s["q"]}"{" checked" if s["key"]=="statistiki" else ""}><span>{e(s[L]["name"])}</span></label>' for i, s in enumerate(S))
    opt = lambda arr: ''.join(f'<option>{e(x)}</option>' for x in arr)
    langs = ''.join(f'<label class="qc qc-s"><input type="radio" name="ql" value="{e(x)}"{" checked" if i==(0 if L=="el" else 1) else ""}><span>{e(x)}</span></label>' for i, x in enumerate(t['q_langs']))
    msg = 'data-l=\'' + e(json.dumps({k: t[k] for k in ('q_hello', 'q_intro', 'q_bye', 'q_level', 'q_field', 'q_len', 'q_words', 'q_pages', 'q_dead', 'q_langl', 'q_style', 'q_notes', 'q_copied', 'q_copy')}, ensure_ascii=False)) + '\''
    tl1 = ''.join(f'<li>{e(x)}</li>' for x in t['tools1']); tl2 = ''.join(f'<li>{e(x)}</li>' for x in t['tools2'])
    body = f'''
<section class="hero" id="hero"><div class="hero-bg" aria-hidden="true"><i class="w1"></i><i class="w2"></i><i class="w3"></i></div>
<div class="hero-in"><div class="hero-t">
<p class="eyebrow">{e(t["eyebrow"])}</p>
<h1 class="h1">{e(t["h1a"])} <em>{e(t["h1b"])}</em></h1>
<p class="hero-p">{e(t["hero_p"])}</p>
<div class="hero-cta"><a class="btn" href="#prosfora">{e(t["cta_quote"])}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a><a class="lnk" href="#analyseis">{e(t["cta_an"])}</a></div>
<ul class="pills">{chips(t["pills"])}</ul></div>
{chart(t)}
</div><a class="scue" href="#glance" aria-label="{e(t["about_k"])}"><span></span></a></section>

<section class="glance" id="glance">{dd("star","g1",1)}{dd("swirl","g2",2)}<div class="wrap gl-in"><svg class="gl-art draw" viewBox="0 0 640 560" aria-hidden="true">{HERO_SCENE}</svg><div><p class="kicker" data-rv>{e(t["about_k"])}</p><p class="gl-p" data-rv>{e(t["about_p"])}</p></div></div></section>

<div class="tick" aria-hidden="true"><div class="tick-t"><div class="tick-i">{fields}{fields}</div></div></div>

{analyses(L, here)}
<section class="svc" id="ypiresies"><div class="wrap svc-in"><div class="svc-h"><p class="kicker" data-rv>{e(t["svc_k"])}</p><h2 data-fx="mask">{e(t["svc_h"])}</h2><p class="lead" data-rv>{e(t["svc_p"])}</p>{dd("arrow","s1",3)}{dd("bell","s2",4)}</div>
<div class="svc-b">{"".join(rows)}</div></div></section>

<section class="jr" id="dromos">{dd("leaf","j1",5)}{dd("loop","j2",6)}<div class="wrap"><div class="sec-h c"><p class="kicker" data-rv>{e(t["jr_k"])}</p><h2 data-fx="cascade">{e(t["jr_h"])}</h2><p class="lead" data-rv>{e(t["jr_p"])}</p></div>
<div class="jr-w"><svg class="jr-svg" aria-hidden="true"><path class="jr-bg"/><path class="jr-p"/></svg><span class="jr-walk" aria-hidden="true"><svg viewBox="0 0 100 100"><use href="#zw"/></svg></span><ol class="jr-l">{jr}</ol></div></div></section>

<section class="pr dark" id="diadikasia">{dd("star","p1",7)}{dd("asterisk","p2",8)}<div class="wrap"><div class="sec-h"><p class="kicker" data-rv>{e(t["pr_k"])}</p><h2 data-fx="light">{e(t["pr_h"])}</h2></div><ol class="pr-l">{pr}</ol></div></section>

<section class="ph" id="filosofia">{dd("check","f1",9)}{dd("leaf","f2",10)}<div class="wrap"><p class="kicker" data-rv>{e(t["ph_k"])}</p><p class="ph-q" data-scrub>{e(t["ph_q"])}</p><ul class="ph-l">{ph}</ul></div></section>

<section class="tl" id="ergaleia">{dd("swirl","t1",11)}{dd("star","t2",12)}<div class="wrap sec-h c"><p class="kicker" data-rv>{e(t["tl_k"])}</p><h2 data-fx="brush">{e(t["tl_h"])}</h2></div>
<div class="mq" aria-label="{e(t["tl_k"])}"><ul class="mq-t">{tl1}{tl1}</ul><ul class="mq-t r">{tl2}{tl2}</ul></div></section>

<section class="qt" id="prosfora">{dd("asterisk","qa1",13)}<div class="wrap qt-in"><div class="qt-f"><p class="kicker" data-rv>{e(t["q_k"])}</p><h2 data-fx="mask">{e(t["q_h"])}</h2><p class="lead" data-rv>{e(t["q_p"])}</p>
<form class="qf" id="qf" novalidate>
<fieldset class="qg"><legend>{e(t["q_type"])}</legend><div class="qcs">{qtypes}</div></fieldset>
<div class="q2"><label class="qi"><span>{e(t["q_level"])}</span><select name="lv">{opt(t["q_levels"])}</select></label>
<label class="qi"><span>{e(t["q_field"])}</span><input name="fd" type="text" placeholder="{e(t["q_field_ph"])}" autocomplete="off"></label></div>
<label class="qi qr"><span>{e(t["q_len"])} <output id="qo">8.000 {e(t["q_words"])} · ≈ 27 {e(t["q_pages"])}</output></span><input name="ln" type="range" min="500" max="40000" step="500" value="8000"></label>
<div class="q2"><label class="qi"><span>{e(t["q_dead"])}</span><input name="dl" type="date"></label>
<label class="qi"><span>{e(t["q_style"])}</span><select name="st">{opt(t["q_styles"])}</select></label></div>
<fieldset class="qg"><legend>{e(t["q_langl"])}</legend><div class="qcs">{langs}</div></fieldset>
<label class="qi"><span>{e(t["q_notes"])}</span><textarea name="nt" rows="3" placeholder="{e(t["q_notes_ph"])}"></textarea></label>
<label class="qi"><span>{e(t["q_name"])}</span><input name="nm" type="text" placeholder="{e(t["q_name_ph"])}" autocomplete="name"></label>
</form></div>
<div class="qt-l">{dd("arrow","qa2",14)}<div class="letter sk" id="letter" {msg} data-to="{EMAIL}" data-sub="{e(t["q_k"])}"><p class="lt-k">{e(t["q_letter"])}</p><div class="lt-b" id="ltb" aria-live="polite"></div><span class="lt-seal" aria-hidden="true">ZW</span></div>
<div class="lt-a"><a class="btn" id="qsend" href="mailto:{EMAIL}">{e(t["q_send"])}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11l18-8-8 18-2-8z"/></svg></a><button class="lnk" type="button" id="qcopy">{e(t["q_copy"])}</button></div>
<p class="lt-n">{e(t["q_privacy"])}</p></div></div></section>

<section class="fqs" id="faq">{dd("loop","a1",15)}<div class="wrap fqs-in"><div class="fqs-h"><p class="kicker" data-rv>{e(t["faq_k"])}</p><h2 data-fx="cascade">{e(t["faq_h"])}</h2>
<dl class="facts" data-rv>{facts}</dl></div>{faq_html(t["faq"])}</div></section>

{cta(L, here, t["ct_k"], t["ct_h"], t["ct_p"])}'''
    ld = {'@context': 'https://schema.org', '@graph': [org(L), WEBSITE, webpage(L, here, t['title'], t['desc']), faq_ld(t['faq'])]}
    return here, alt, t['title'], t['desc'], body, ld

AN_LINK = {'bars': 'statistiki', 'bell': 'statistiki', 'box': 'spss', 'grid': 'spss', 'scatter': 'statistiki', 'reg': 'spss',
           'logit': 'spss', 'factor': 'erotimatologio', 'alpha': 'erotimatologio', 'sem': 'sem', 'med': 'sem', 'ts': 'rpy'}
def analyses(L, here):
    t = T[L]; byk = {s['key']: s for s in S}
    li = ''.join(f'<li data-rv style="--i:{i % 4}"><a class="an-c sk" href="{rel(here, spath(byk[AN_LINK[k]], L))}"><svg class="an-m draw" viewBox="0 0 120 80" aria-hidden="true">{SK.mini(k, 900 + i * 13).render()}</svg><h3>{e(n)}</h3><p>{e(dsc)}</p></a></li>' for i, (n, dsc, k) in enumerate(t['an']))
    return f'''<section class="an" id="analyseis">{dd("bell","n1",21)}{dd("asterisk","n2",22)}<div class="wrap"><div class="sec-h c"><p class="kicker" data-rv>{e(t["an_k"])}</p><h2 data-fx="light">{e(t["an_h"])}</h2><p class="lead" data-rv>{e(t["an_p"])}</p></div><ul class="an-l">{li}</ul></div></section>'''

def chart(t):
    import statistics as st
    P = CHART_PTS; n = len(P)
    xs = [p[0] for p in P]; ys = [p[1] for p in P]; mx_ = st.mean(xs); my_ = st.mean(ys)
    sxx = sum((x - mx_) ** 2 for x in xs); sxy = sum((x - mx_) * (y - my_) for x, y in P)
    bb = sxy / sxx; aa = my_ - bb * mx_
    line = f'M{SK.mx(.3):.0f} {SK.my(aa + bb * .3):.0f}L{SK.mx(9.7):.0f} {SK.my(aa + bb * 9.7):.0f}'
    dots = ''.join(f'<circle class="pt" cx="{SK.mx(x):.0f}" cy="{SK.my(y):.0f}" r="{5 + (i * 7 % 4) * .5:.1f}" style="--d:{.9 + i * .025:.2f}s"/>' for i, (x, y) in enumerate(P))
    labs = ''.join(f'<text class="ax" x="{SK.mx(k):.0f}" y="634">{k}</text><text class="ax" x="{SK.PX0 - 22:.0f}" y="{SK.my(k) + 5:.0f}">{k}</text>' for k in (2, 4, 6, 8, 10))
    data = json.dumps(P, separators=(',', ':'))
    return f'''<div class="chart" id="chart" data-pts="{data}" aria-hidden="true"><svg viewBox="0 0 800 700" class="ch-svg">
<path id="rgBand" class="rg-band" d=""/>{CHART_ART}{labs}<text class="axt" x="{SK.PX1 - 4}" y="668" text-anchor="end">{e(t["ax_x"])}</text><text class="axt" x="0" y="0" transform="translate(40 {SK.PY1 + 4}) rotate(-90)" text-anchor="end">{e(t["ax_y"])}</text>
{dots}<path id="rgLine" class="rg-line" d="{line}" pathLength="1"/>
<g id="rgNew" class="rg-new"><path class="rg-x" d=""/><circle r="8"/><circle class="rg-h" r="16"/><text x="14" y="-14">{e(t["ch_obs"])}</text></g>
<text id="rgNote" class="rg-note" x="640" y="170">r = 0,7</text></svg>
<div class="coef sk"><p class="cf-k">{e(t["ch_card"])}</p><table><tr><th></th><th>B</th><th>β</th><th>t</th><th>p</th></tr>
<tr><td>{"Σταθερά" if t["lang"] == "el" else "Constant"}</td><td id="cfA">–</td><td></td><td></td><td></td></tr>
<tr><td>X</td><td id="cfB">–</td><td id="cfR">–</td><td id="cfT">–</td><td id="cfP">–</td></tr></table><p class="cf-r">R² = <b id="cfR2">–</b> · n = <b id="cfN">{n}</b></p></div>
<p class="ch-tip">{e(t["ch_tip"])}</p></div>'''

def cta(L, here, k, h, p, q=''):
    t = T[L]; hp = rel(here, homepath(L))
    tgt = '#prosfora' if here == homepath(L) else f'{hp}?t={q}#prosfora'
    return f'''<section class="ct dark" id="epikoinonia"><div class="ct-e" aria-hidden="true"><svg viewBox="0 0 100 100"><defs><mask id="cm"><path d="{ENSO_G}" pathLength="1" class="ct-g"/></mask></defs><use href="#eo" mask="url(#cm)"/></svg></div><svg class="ct-pl draw" viewBox="0 0 900 240" aria-hidden="true">{CTA_PLANE}</svg>
<div class="wrap ct-in"><p class="kicker" data-rv>{e(k)}</p><h2 data-fx="mask">{e(h)}</h2><p class="lead" data-rv>{e(p)}</p>
<a class="ct-m" href="mailto:{EMAIL}" data-rv>{EMAIL}</a>
<div class="ct-b" data-rv><a class="btn btn-l" href="{tgt}">{e(t["nav_quote"])}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></div></div></section>'''

# ---------------------------------------------------------------- service page
def service(s, L):
    t = T[L]; c = s[L]; here = spath(s, L); alt = spath(s, t['other']); hp = rel(here, homepath(L))
    incl = ''.join(f'<li class="in-c sk" data-rv style="--i:{i}"><span class="in-n">{i+1:02d}</span><h3>{e(a)}</h3><p>{e(b)}</p></li>' for i, (a, b) in enumerate(c['incl']))
    same = [x for x in S if x['group'] == s['group'] and x is not s]
    others = [x for x in S if x['group'] != s['group']]
    relx = (same + others)[:3]
    rl = ''.join(f'<li data-rv style="--i:{i}"><a class="rl sk" href="{rel(here, spath(x, L))}">{ricon(x["icon"], i+20)}<span class="rl-h">{e(x[L]["name"])}</span><span class="rl-p">{e(x[L]["short"])}</span><span class="rl-a" aria-hidden="true">→</span></a></li>' for i, x in enumerate(relx))
    pr = ''.join(f'<li class="pr-c sk ch" data-rv style="--i:{i}"><span class="pr-n">{i+1}</span><h3>{e(a)}</h3><p>{e(b)}</p></li>' for i, (a, b) in enumerate(t['pr']))
    bc_name = t['nav_services']
    body = f'''
<section class="sh" id="hero"><div class="hero-bg" aria-hidden="true"><i class="w1"></i><i class="w2"></i></div><div class="wrap sh-in">
<div class="sh-t"><nav class="bc" aria-label="breadcrumb"><a href="{hp}">{e(t["home_lbl"])}</a><span aria-hidden="true">/</span><a href="{hp}#ypiresies">{e(bc_name)}</a><span aria-hidden="true">/</span><span aria-current="page">{e(c["name"])}</span></nav>
<p class="eyebrow">{e(c["kicker"])}</p><h1 class="h1 h1-s">{e(c["h1"])}</h1><p class="hero-p">{e(c["lead"])}</p>
<div class="hero-cta"><a class="btn" href="{hp}?t={s["q"]}#prosfora">{e(t["cta_quote"])}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a><a class="lnk" href="#periexei">{e(t["sp_incl"])}</a></div></div>
<div class="sh-v" aria-hidden="true"><svg viewBox="0 0 100 100" class="sh-e"><defs><mask id="sm"><path d="{ENSO_G}" pathLength="1" class="hv-g"/></mask></defs><use href="#eo" mask="url(#sm)" class="hv-ink"/></svg><svg viewBox="0 0 400 400" class="sh-art">{scaled(SK.service_art(ICONS[s["icon"]], 700 + S.index(s) * 10), .5, .5)}</svg></div>
</div></section>
<section class="inc" id="periexei"><div class="wrap"><div class="sec-h"><p class="kicker" data-rv>{e(t["sp_incl"])}</p><h2 data-fx="mask">{e(c["name"])}: {e(t["sp_incl"].lower())}</h2></div><ol class="in-l">{incl}</ol></div></section>
<section class="who"><div class="wrap who-in"><div><p class="kicker" data-rv>{e(t["sp_who"])}</p><p class="who-p" data-rv>{e(c["who"])}</p></div>
<div><p class="kicker" data-rv>{e(t["sp_tools"])}</p><ul class="tg" data-rv>{chips(s["tools"])}</ul></div></div></section>
<section class="pr dark" id="diadikasia">{dd("star","p1",7)}{dd("asterisk","p2",8)}<div class="wrap"><div class="sec-h"><p class="kicker" data-rv>{e(t["pr_k"])}</p><h2 data-fx="light">{e(t["pr_h"])}</h2></div><ol class="pr-l">{pr}</ol></div></section>
<section class="fqs" id="faq">{dd("loop","a1",15)}<div class="wrap fqs-in"><div class="fqs-h"><p class="kicker" data-rv>{e(t["sp_faq"])}</p><h2 data-fx="cascade">{e(c["name"])}: {e(t["sp_faq"].lower())}</h2></div>{faq_html(c["faq"] + [t["faq"][2]])}</div></section>
<section class="rel"><div class="wrap"><p class="kicker" data-rv>{e(t["sp_rel"])}</p><ul class="rl-l">{rl}</ul></div></section>
{cta(L, here, t["ct_k"], t["sp_cta_h"], t["sp_cta_p"], s["q"])}'''
    svc = {'@type': 'Service', '@id': absu(here) + '#service', 'name': c['name'], 'serviceType': c['name'], 'description': c['desc'],
           'url': absu(here), 'provider': {'@id': DOMAIN + '/#org'}, 'areaServed': [{'@type': 'Country', 'name': 'Greece'}, {'@type': 'Country', 'name': 'Cyprus'}],
           'availableLanguage': ['el', 'en'], 'audience': {'@type': 'Audience', 'audienceType': c['who']}}
    bc = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': t['home_lbl'], 'item': absu(homepath(L))},
        {'@type': 'ListItem', 'position': 2, 'name': c['name'], 'item': absu(here)}]}
    ld = {'@context': 'https://schema.org', '@graph': [org(L), WEBSITE, webpage(L, here, c['title'], c['desc']), svc, bc, faq_ld(c['faq'])]}
    return here, alt, c['title'], c['desc'], body, ld

# ---------------------------------------------------------------- write
def write(here, html_):
    p = os.path.join(OUT, here, 'index.html')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w').write(html_)

def main():
    keep = {'.git', 'privacy.html', 'assets', 'favicon.ico', 'site.webmanifest', 'llms.txt'}
    os.makedirs(OUT, exist_ok=True)
    pages = []
    for L in ('el', 'en'):
        here, alt, title, desc, body, ld = home(L)
        write(here, page(L, here, alt, title, desc, body, ld)); pages.append((here, alt, L))
        for s in S:
            here, alt, title, desc, body, ld = service(s, L)
            write(here, page(L, here, alt, title, desc, body, ld)); pages.append((here, alt, L))
    # sitemap + robots + nojekyll
    urls = []
    for here, alt, L in pages:
        other = 'en' if L == 'el' else 'el'
        urls.append(f'<url><loc>{absu(here)}</loc><lastmod>{TODAY}</lastmod>'
                    f'<xhtml:link rel="alternate" hreflang="{L}" href="{absu(here)}"/><xhtml:link rel="alternate" hreflang="{other}" href="{absu(alt)}"/></url>')
    open(f'{OUT}/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(urls) + '\n</urlset>\n')
    open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n')
    open(f'{OUT}/.nojekyll', 'w').write('')
    os.makedirs(f'{OUT}/assets/img', exist_ok=True)
    open(f'{OUT}/assets/img/zenwrite-logo.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="4 4 92 92"><path d="{ENSO_D}" fill="#1B1D21"/><path d="{NIB}" fill="#B0402C"/><path d="M50 49v16" stroke="#F6F2EA" stroke-width="1.6" stroke-linecap="round"/><circle cx="50" cy="47.5" r="2.2" fill="#F6F2EA"/></svg>')
    open(f'{HERE}/../og.html','w').write(f'''<!doctype html><html><head><meta charset="utf-8"><style>{fonts("site/")}body{{margin:0;width:1200px;height:630px;background:#F6F2EA;display:flex;align-items:center;gap:60px;padding:0 90px;box-sizing:border-box;font-family:'Commissioner';color:#1B1D21;overflow:hidden;position:relative}}
body::before{{content:"";position:absolute;width:900px;height:900px;right:-300px;top:-380px;border-radius:50%;background:radial-gradient(closest-side,rgba(184,67,47,.14),transparent)}}
svg{{width:400px;height:400px;flex:none}}h1{{font:300 76px/1 'Source Serif 4';margin:0;letter-spacing:-.02em}}h1 i{{color:#B0402C}}p{{font-size:27px;line-height:1.4;margin:26px 0 0;color:#46494F}}small{{display:block;margin-top:34px;font:600 18px/1 'Commissioner';letter-spacing:.16em;text-transform:uppercase;color:#B0402C}}</style></head>
<body><svg viewBox="4 4 92 92"><path d="{ENSO_D}" fill="#1B1D21"/><path d="{NIB}" fill="#B0402C"/><path d="M50 49v16" stroke="#F6F2EA" stroke-width="1.6" stroke-linecap="round"/><circle cx="50" cy="47.5" r="2.2" fill="#F6F2EA"/></svg>
<div><h1>Zen<i>Write</i></h1><p>Εργασίες, πτυχιακές, διπλωματικές<br>& στατιστική ανάλυση — με ηρεμία.</p><small>zenwrite.gr</small></div></body></html>''')
    print(len(pages), 'pages · css', len(CSS), 'B · js', len(JS), 'B')

if __name__ == '__main__':
    main()
