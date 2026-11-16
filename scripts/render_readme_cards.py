#!/usr/bin/env python3
"""Render every README card as an animated SVG into cards/.

Reads data/contributions.json (refreshed daily by the GitHub Action) and draws:
hero, contribution graph, monthly chart, three world tiles, stack, two repo cards.

STATIC=1 python scripts/render_readme_cards.py   -> final frame, no animation
"""
import base64
import datetime as dt
import html
import json
import math
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

# ---------------------------------------------------------------- config ----
PAPER, INK, MUTED = "#F6F1E7", "#14110F", "#6B655C"
BLUE, RED, YELLOW = "#2447F5", "#E5392B", "#F4B400"
RAMP = ["#E8E1D2", "#BCC8FB", "#869BF9", "#4F6BF6", BLUE]  # blue contribution levels

PROFILE = "https://github.com/Raghavkhedar"
FIRST, LAST = "Raghav", "Khedar"
TAGLINE = ["Computer engineering student at Thapar.", "I build field-ops apps, internal tools and reports."]
STATUS = "Data analyst intern  ·  Gurgaon"

# Edit these freely. `n` is the number that counts up on each tile.
TILES = [
    dict(file="build", color=BLUE, ink="#FFFFFF", label="BUILD", n=36, unit="repositories",
         lines=["Android apps, admin portals,", "internal ERP and CRM tools."]),
    dict(file="data", color=RED, ink="#FFFFFF", label="DATA", n=24, unit="linked reports",
         lines=["Sheets, Apps Script and", "finance automation."]),
    dict(file="learn", color=YELLOW, ink=INK, label="LEARN", n=4, unit="years of B.E.",
         lines=["Computer vision, systems", "and whatever is next."]),
]
STACK = ["Python", "Django", "JavaScript", "TypeScript", "React", "Next.js", "Tailwind CSS", "HTML5", "CSS3",
         "Kotlin", "Firebase", "PostgreSQL", "Docker", "htmx", "Apps Script", "Git", "C++", "C", "Bootstrap"]
REPOS = [
    dict(file="repo1", name="whitecoffee", lang="HTML", color=YELLOW,
         desc=["Field-ops monorepo: Android app,", "Next.js admin portal, Firebase."],
         url="https://github.com/Raghavkhedar/whitecoffee"),
    dict(file="repo2", name="ERP", lang="Python", color=RED,
         desc=["Django and PostgreSQL ERP for", "hiring and onboarding."],
         url="https://github.com/Raghavkhedar/ERP"),
]
CUP = [
    "      )   (     )",
    "     (     )   (",
    "      )   (     )",
    "",
    "   .-------------------.",
    "   |:::::::::::::::::::|___",
    "   |:::::::::::::::::::|   \\",
    "   |:::::::::::::::::::|    |",
    "   |:::::::::::::::::::|   /",
    "    \\:::::::::::::::::/---'",
    "     \\:::::::::::::::/",
    "      '-------------'",
    "  ___________________________",
    " (___________________________)",
]

# ------------------------------------------------------------- plumbing -----
FONTS = {
    "serif": ("Instrument Serif", "serif-400.woff", "normal", 400),
    "serifi": ("Instrument Serif", "serif-400i.woff", "italic", 400),
    "sans4": ("Geist", "sans-400.woff", "normal", 400),
    "sans6": ("Geist", "sans-600.woff", "normal", 600),
    "mono": ("Geist Mono", "mono-400.woff", "normal", 400),
}


def font_css(keys):
    out = []
    for k in keys:
        fam, fn, style, weight = FONTS[k]
        b64 = base64.b64encode((ROOT / "fonts" / fn).read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(out)


# Animations use backwards fill, so with animation disabled (reduced motion,
# STATIC=1) every element simply shows its final state.
BASE_CSS = """
text{white-space:pre}
.serif{font-family:'Instrument Serif',Georgia,serif}
.sans{font-family:Geist,'Segoe UI',Helvetica,Arial,sans-serif}
.mono{font-family:'Geist Mono',ui-monospace,Menlo,Consolas,monospace}
.fb{transform-box:fill-box}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes pop{0%{opacity:0;transform:scale(.2)}70%{opacity:1;transform:scale(1.18)}100%{transform:scale(1)}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes swing{0%{opacity:0;transform:translateY(46px) rotate(-7deg)}55%{opacity:1;transform:translateY(-8px) rotate(2deg)}78%{transform:translateY(3px) rotate(-.6deg)}100%{transform:none}}
@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}
@keyframes beat{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.7);opacity:.45}}
@keyframes ring{0%{transform:scale(.4);opacity:.7}100%{transform:scale(2.4);opacity:0}}
@keyframes shine{0%,62%{transform:translateX(0) skewX(-20deg)}100%{transform:translateX(620%) skewX(-20deg)}}
@keyframes steam{0%,100%{opacity:.3}50%{opacity:1}}
@keyframes draw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes show{from,to{opacity:1}}
.rise{animation:rise .7s cubic-bezier(.2,.8,.2,1) backwards}
.fade{animation:fade .5s ease-out backwards}
.pop{animation:pop .5s cubic-bezier(.2,.9,.3,1.2) backwards;transform-box:fill-box;transform-origin:center}
.grow{animation:grow .8s cubic-bezier(.2,.8,.2,1) backwards;transform-box:fill-box;transform-origin:bottom}
.swing{animation:swing 1s cubic-bezier(.2,.8,.2,1) backwards;transform-box:fill-box;transform-origin:50% 100%}
.nudge{animation:nudge 1.8s ease-in-out infinite}
.beat{animation:beat 1.8s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.ring{animation:ring 3s ease-out infinite;transform-box:fill-box;transform-origin:center;opacity:.25}
.shine{animation:shine 5.5s ease-in-out infinite;transform-box:fill-box;opacity:.22}
.steam{animation:steam 3s ease-in-out infinite}
.draw{stroke-dasharray:var(--len);animation:draw 1s ease-out backwards}
.blink{animation:blink 1.1s steps(1) infinite}
.f{opacity:0;animation:show .07s steps(1,end)}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def D(t):
    return f'style="animation-delay:{t:.2f}s"'


def svg(w, h, title, body, fonts):
    css = font_css(fonts) + BASE_CSS + ("*{animation:none!important}" if STATIC else "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title><style>{css}</style>{body}</svg>'
    )


def card(x, y, w, h, fill=PAPER, off=8, r=20, cid=None):
    """Paper card with ink border and a hard offset shadow."""
    return (
        f'<rect x="{x + off}" y="{y + off}" width="{w}" height="{h}" rx="{r}" fill="{INK}"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>'
    )


def clip(cid, x, y, w, h, r):
    return f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>'


def write(name, content):
    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}.svg").write_text(content, encoding="utf-8")
    print(f"  cards/{name}.svg  {len(content) / 1024:.0f} KB")


# ----------------------------------------------------------------- data -----
def load():
    raw = json.loads((ROOT / "data" / "contributions.json").read_text())
    days = {d["date"]: int(d["count"]) for d in raw["days"]}
    today = dt.date.fromisoformat(max(days))
    return days, today


def stats(days, today):
    get = lambda d: days.get(d.isoformat(), 0)
    start = today - dt.timedelta(days=364)
    window = [start + dt.timedelta(days=i) for i in range(365)]
    total = sum(get(d) for d in window)
    active = sum(1 for d in window if get(d) > 0)
    cur, d = 0, today
    if get(d) == 0:
        d -= dt.timedelta(days=1)
    while get(d) > 0:
        cur += 1
        d -= dt.timedelta(days=1)
    best_run = run = 0
    for d in window:
        run = run + 1 if get(d) > 0 else 0
        best_run = max(best_run, run)
    busiest = max(window, key=get)
    # last 12 calendar months
    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    per_month = []
    for (y, m) in months:
        s = sum(c for k, c in days.items() if k.startswith(f"{y:04d}-{m:02d}-"))
        per_month.append((dt.date(y, m, 1).strftime("%b"), s))
    return dict(total=total, active=active, streak=cur, longest=best_run,
                busiest=(get(busiest), busiest.strftime("%-d %b")), months=per_month)


# ---------------------------------------------------------------- cards -----
def hero():
    W, H = 1000, 424
    b = [card(4, 4, 980, 408, r=24)]
    b.append(f'<text x="48" y="62" class="mono fade" font-size="13" letter-spacing="3" fill="{MUTED}" {D(.1)}>HELLO, I\'M</text>')
    b.append(f'<text x="44" y="172" class="serif rise" font-size="112" fill="{INK}" {D(.25)}>{FIRST}</text>')
    b.append(f'<text x="44" y="268" class="serif rise" font-size="112" font-style="italic" fill="{BLUE}" {D(.55)}>{LAST}</text>')
    # marker underline that draws in under the surname
    ln = 330
    b.append(f'<path d="M50 286 C 130 278, 230 292, 370 281" fill="none" stroke="{YELLOW}" stroke-width="7" '
             f'stroke-linecap="round" class="draw" style="--len:{ln};animation-delay:1.1s"/>')
    for i, t in enumerate(TAGLINE):
        b.append(f'<text x="48" y="{322 + i * 28}" class="sans rise" font-size="19" fill="{INK}" {D(.9 + i * .15)}>{esc(t)}</text>')
    b.append(f'<circle cx="55" cy="381" r="6" fill="{RED}" class="beat" style="animation-delay:1.5s"/>')
    b.append(f'<text x="72" y="386" class="mono fade" font-size="14" fill="{MUTED}" {D(1.3)}>{esc(STATUS)}</text>')
    b.append(f'<rect x="{72 + 8.4 * len(STATUS) + 6:.0f}" y="372" width="8" height="16" fill="{INK}" class="blink"/>')
    # ASCII coffee cup prints in row by row
    for i, row in enumerate(CUP):
        if not row:
            continue
        cls = "mono steam" if i < 3 else "mono fade"
        delay = f"animation-delay:{(i * .5 if i < 3 else .5 + i * .09):.2f}s"
        col = MUTED if i < 3 else INK
        b.append(f'<text x="640" y="{128 + i * 21}" class="{cls}" font-size="16" fill="{col}" style="{delay}" xml:space="preserve">{esc(row)}</text>')
    b.append(f'<text x="640" y="{128 + len(CUP) * 21 + 14}" class="mono fade" font-size="12" fill="{MUTED}" letter-spacing="2" {D(2.0)}>WHITECOFFEE, BUT MAKE IT ASCII</text>')
    return svg(W, H, f"{FIRST} {LAST}: computer engineering student and data analyst intern", "".join(b),
               ["serif", "serifi", "sans4", "mono"])


def graph(days, today, s):
    W, H = 1000, 280
    cell, pitch, x0, y0 = 14, 17, 48, 116
    start = today - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # back up to Sunday
    nz = sorted(c for c in days.values() if c > 0) or [1]
    q = [nz[int(len(nz) * p)] for p in (.25, .5, .75)]
    lvl = lambda c: 0 if c == 0 else 1 + sum(c > t for t in q)
    b = [card(4, 4, 980, 256, r=24)]
    b.append(f'<text x="48" y="60" class="serif rise" font-size="34" fill="{INK}" {D(1.6)}>Contribution graph</text>')
    b.append(f'<text x="48" y="82" class="mono fade" font-size="12" fill="{MUTED}" {D(1.7)}>{s["total"]:,} contributions in the last year</text>')
    # legend
    lx = 984 - 48 - (5 * 17 + 60)
    b.append(f'<text x="{lx}" y="66" class="mono" font-size="11" fill="{MUTED}">Less</text>')
    for i, c in enumerate(RAMP):
        b.append(f'<rect x="{lx + 34 + i * 17}" y="55" width="{cell}" height="{cell}" rx="3" fill="{c}"/>')
    b.append(f'<text x="{lx + 34 + 5 * 17 + 4}" y="66" class="mono" font-size="11" fill="{MUTED}">More</text>')
    last_m = None
    d = start
    col = 0
    while d <= today:
        row = (d.weekday() + 1) % 7
        if row == 0 and d != start:
            col += 1
        if d.day <= 7 and row == 0 and d.month != last_m:
            last_m = d.month
            b.append(f'<text x="{x0 + col * pitch}" y="{y0 - 8}" class="mono" font-size="11" fill="{MUTED}">{d.strftime("%b")}</text>')
        c = days.get(d.isoformat(), 0)
        delay = 1.8 + col * 0.022 + row * 0.01
        b.append(f'<rect x="{x0 + col * pitch}" y="{y0 + row * pitch}" width="{cell}" height="{cell}" rx="3" '
                 f'fill="{RAMP[lvl(c)]}" class="pop" {D(delay)}><title>{c} on {d.isoformat()}</title></rect>')
        d += dt.timedelta(days=1)
    return svg(W, H, f"Contribution graph, {s['total']} contributions in the last year", "".join(b), ["serif", "mono"])


def months(s):
    W, H = 1000, 344
    b = [card(4, 4, 980, 328, r=24)]
    b.append(f'<text x="48" y="64" class="serif rise" font-size="34" fill="{INK}" {D(3.2)}>Contributions per month</text>')
    b.append(f'<text x="48" y="86" class="mono fade" font-size="12" fill="{MUTED}" {D(3.3)}>last 12 months</text>')
    vals = [v for _, v in s["months"]]
    top = max(vals) or 1
    best = vals.index(max(vals))
    base, maxh, bw, pitch, x0 = 280, 150, 36, 50, 52
    b.append(f'<line x1="48" y1="{base}" x2="656" y2="{base}" stroke="{INK}" stroke-width="2"/>')
    for i, (lab, v) in enumerate(s["months"]):
        h = max(4, v / top * maxh)
        x = x0 + i * pitch
        fill = BLUE if i == best else INK
        b.append(f'<rect x="{x}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" rx="5" fill="{fill}" class="grow" {D(3.4 + i * .06)}><title>{lab}: {v}</title></rect>')
        b.append(f'<text x="{x + bw / 2}" y="{base + 22}" text-anchor="middle" class="mono fade" font-size="11" fill="{MUTED}" {D(3.4 + i * .06)}>{lab.upper()}</text>')
        if i == best:
            b.append(f'<text x="{x + bw / 2}" y="{base - h - 10:.1f}" text-anchor="middle" class="serif pop" font-size="26" fill="{BLUE}" {D(4.3)}>{v}</text>')
    stat = [
        ("Current streak", f'{s["streak"]}', "days"),
        ("Longest streak", f'{s["longest"]}', "days"),
        ("Active days", f'{s["active"]}', "of 365"),
        ("Busiest day", f'{s["busiest"][0]}', s["busiest"][1]),
    ]
    for i, (lab, big, small) in enumerate(stat):
        cx, cy = 712 + (i % 2) * 140, 120 + (i // 2) * 100
        d = 3.6 + i * .15
        b.append(f'<text x="{cx}" y="{cy}" class="mono fade" font-size="11" letter-spacing="1.5" fill="{MUTED}" {D(d)}>{lab.upper()}</text>')
        b.append(f'<text x="{cx - 2}" y="{cy + 48}" class="serif rise" font-size="56" fill="{INK}" {D(d)}>{big}</text>')
        b.append(f'<text x="{cx}" y="{cy + 68}" class="sans fade" font-size="13" fill="{MUTED}" {D(d + .1)}>{esc(small)}</text>')
    return svg(W, H, "Contributions per month with streak stats", "".join(b), ["serif", "sans4", "mono"])


def arrow(x, y, color, cls="nudge", delay=0):
    return (f'<g class="{cls}" style="animation-delay:{delay}s"><path d="M{x} {y} h26 m-9 -9 l9 9 l-9 9" fill="none" '
            f'stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></g>')


def tile(t, i):
    W, H = 320, 262
    cid = f"c{t['file']}"
    ink = t["ink"]
    t0 = 4.6 + i * .3
    b = [f'<defs>{clip(cid, 3, 3, 304, 244, 22)}</defs>']
    b.append(f'<g class="swing" {D(t0)}>')
    b.append(card(3, 3, 304, 244, fill=t["color"], off=7, r=22))
    b.append(f'<g clip-path="url(#{cid})">')
    b.append(f'<circle cx="306" cy="6" r="26" fill="none" stroke="{ink}" stroke-width="3" class="ring" style="animation-delay:{t0 + 1.2}s"/>')
    b.append(f'<rect x="-70" y="-10" width="46" height="280" fill="#fff" class="shine" style="animation-delay:{t0 + 2}s"/>')
    b.append('</g>')
    b.append(f'<text x="26" y="48" class="mono" font-size="13" letter-spacing="3" fill="{ink}">{t["label"]}</text>')
    b.append(arrow(254, 40, ink, delay=t0 + 1))
    # count-up from CSS-only frames (no SMIL), final value stays
    n, fr = t["n"], 18
    base = t0 + .5
    for k in range(fr):
        v = round(n * (k / (fr - 1)) ** 2)
        b.append(f'<text x="24" y="146" class="serif f" font-size="96" fill="{ink}" style="animation-delay:{base + k * .06:.2f}s">{v}</text>')
    b.append(f'<text x="24" y="146" class="serif fade" font-size="96" fill="{ink}" style="animation-delay:{base + fr * .06:.2f}s">{n}</text>')
    b.append(f'<text x="28" y="176" class="sans" font-size="18" font-weight="600" fill="{ink}">{esc(t["unit"])}</text>')
    for j, ln in enumerate(t["lines"]):
        b.append(f'<text x="28" y="{206 + j * 19}" class="sans" font-size="14" fill="{ink}" fill-opacity=".85">{esc(ln)}</text>')
    b.append('</g>')
    return svg(W, H, f"{t['label']}: {n} {t['unit']}", "".join(b), ["serif", "sans6", "sans4", "mono"])


def stack():
    W = 1000
    chips, x, y = [], 48, 74
    for i, name in enumerate(STACK):
        w = len(name) * 10.2 + 52
        if x + w > W - 48:
            x, y = 48, y + 52
        fill = [BLUE, RED, YELLOW][i % 3]
        chips.append(
            f'<g class="pop" {D(6.3 + i * .07)}><rect x="{x}" y="{y}" width="{w:.0f}" height="38" rx="19" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="{x + 18}" cy="{y + 19}" r="5" fill="{fill}"/>'
            f'<text x="{x + 32}" y="{y + 24.5}" class="sans" font-size="15" font-weight="600" fill="{INK}">{esc(name)}</text></g>'
        )
        x += w + 10
    H = y + 38 + 44
    b = [card(4, 4, 980, H - 24, r=24)]
    b.append(f'<text x="48" y="50" class="mono fade" font-size="13" letter-spacing="3" fill="{MUTED}" {D(6.2)}>STACK</text>')
    b += chips
    return svg(W, H, "Tech stack", "".join(b), ["sans6", "mono"])


def repo(r, i):
    W, H = 492, 178
    cid = f"c{r['file']}"
    t0 = 6.9 + i * .25
    b = [f'<defs>{clip(cid, 3, 3, 478, 160, 20)}</defs><g class="swing" {D(t0)}>']
    b.append(card(3, 3, 478, 160, off=7, r=20))
    b.append(f'<g clip-path="url(#{cid})"><rect x="-70" y="-10" width="40" height="190" fill="{r["color"]}" class="shine" style="animation-delay:{t0 + 2}s"/></g>')
    b.append(f'<text x="28" y="48" class="mono" font-size="12" letter-spacing="3" fill="{MUTED}">PINNED</text>')
    b.append(f'<text x="26" y="92" class="serif" font-size="42" fill="{INK}">{esc(r["name"])}</text>')
    for j, ln in enumerate(r["desc"]):
        b.append(f'<text x="28" y="{118 + j * 19}" class="sans" font-size="14" fill="{INK}" fill-opacity=".8">{esc(ln)}</text>')
    b.append(f'<circle cx="372" cy="44" r="6" fill="{r["color"]}" stroke="{INK}" stroke-width="1.5"/>')
    b.append(f'<text x="386" y="48.5" class="mono" font-size="12" fill="{INK}">{esc(r["lang"])}</text>')
    b.append(arrow(420, 124, INK, delay=t0 + 1))
    b.append('</g>')
    return svg(W, H, f"Repository {r['name']}", "".join(b), ["serif", "sans4", "mono"])


def main():
    days, today = load()
    s = stats(days, today)
    print(f"Rendering cards (STATIC={int(STATIC)}), data through {today}")
    write("hero", hero())
    write("graph", graph(days, today, s))
    write("months", months(s))
    for i, t in enumerate(TILES):
        write(t["file"], tile(t, i))
    write("stack", stack())
    for i, r in enumerate(REPOS):
        write(r["file"], repo(r, i))


if __name__ == "__main__":
    main()
