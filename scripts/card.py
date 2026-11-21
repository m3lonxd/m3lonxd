"""Profil başlık kartı: mavi-krem 1-bit baskı teması, katmanlı derinlik.

Katmanlar (arkadan öne):
  1. mavi zemin
  2. dev piksel "M3LON" yazısı (krem, alt satırlar dither)
  3. figür: assets/card-figure.png; saydam dış, mavi silüet içi, krem noktalar.
     Silüetin mavi içi arkadaki yazıyı örter; halkanın ortası saydam kalır.
  4. ön yazılar: kimlik, istatistikler ve figürün üzerinden geçen proje şeridi
  5. ince krem çerçeve

İçerik sabittir (odak: AI ajanları ve siber güvenlik); GitHub verisi ya da token gerekmez.
Kullanım: python3 scripts/card.py <kullanıcı> assets   (assets/card.svg ve assets/stack.svg üretir; içerik sabit, workflow gerekmez)
"""
import base64
import math
import sys
from html import escape
from pathlib import Path

BLUE = "#1b22cf"
CREAM = "#ece8cc"
W, H = 880, 560
P = 2
FS, CW = 14, 14 * 0.6

# Kartın içeriği bilerek sabit: sayı ve sürekli değişen bilgi yok.
FOCUS = "AI agents and cyber security."
INTRO = ["Tools that let agents act on real machines,", "and tools that keep those machines safe."]
ROWS = [
    ("Agents", "desktop and terminal control for AI"),
    ("Security", "honeypots · attack maps · hardening"),
    ("Stack", "Python · TypeScript · C++ · Rust"),
    ("OS", "Linux"),
]
PROJECTS = "computer-use-linux · nexguard"

GLYPHS = {
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
}


def patterns():
    return (f'<pattern id="d25" width="{P * 4}" height="{P * 4}" patternUnits="userSpaceOnUse">'
            f'<rect width="{P}" height="{P}" fill="{CREAM}"/><rect x="{P * 2}" y="{P * 2}" width="{P}" height="{P}" fill="{CREAM}"/></pattern>'
            f'<pattern id="d50" width="{P * 2}" height="{P * 2}" patternUnits="userSpaceOnUse">'
            f'<rect width="{P}" height="{P}" fill="{CREAM}"/><rect x="{P}" y="{P}" width="{P}" height="{P}" fill="{CREAM}"/></pattern>'
            f'<pattern id="d75" width="{P * 4}" height="{P * 4}" patternUnits="userSpaceOnUse">'
            f'<rect width="{P * 4}" height="{P * 4}" fill="{CREAM}"/><rect width="{P}" height="{P}" fill="{BLUE}"/>'
            f'<rect x="{P * 2}" y="{P * 2}" width="{P}" height="{P}" fill="{BLUE}"/></pattern>')


def giant(text, x0, y0, cell):
    """Piksel harfler; üst beş satır dolu krem, alt iki satır dither."""
    out = []
    for k, ch in enumerate(text):
        gx = x0 + k * (5 * cell + cell)
        for y, row in enumerate(GLYPHS[ch]):
            fill = CREAM if y < 5 else "url(#d50)"
            for x, c in enumerate(row):
                if c == "#":
                    out.append(f'<rect x="{gx + x * cell}" y="{y0 + y * cell}" width="{cell}" height="{cell}" fill="{fill}"/>')
    return "".join(out)


def build(login, font_b64, fig_png):
    css = []

    def appear(cls, at):
        css.append(f".{cls}{{animation:on .5s ease-out {at:.2f}s forwards}}")

    # figür
    fw, fh = int.from_bytes(fig_png[16:20], "big"), int.from_bytes(fig_png[20:24], "big")
    fx, fy = W - fw, 0
    fig = (f'<svg x="{fx}" y="{fy}" width="{fw}" height="{fh}" overflow="hidden">'
           f'<image href="data:image/png;base64,{base64.b64encode(fig_png).decode()}" width="{fw}" height="{fh}" style="image-rendering:pixelated"/>'
           f'<rect class="scan" width="{fw}" height="{fh}" fill="{BLUE}"/></svg>')
    css.append(f".scan{{--h:{fh}px;animation:drop 1.1s steps({fh // 8}) .5s forwards}}")

    # arka: dev yazı (N dedenin başının, O kolunun arkasına düşer)
    back = giant("M3LON", 90, 34, 22)
    css.append(".back{animation:on .6s steps(4) .1s forwards}")

    # ön: kimlik, odak cümlesi ve alanlar (sabit; sayı yok, eskimez)
    front = []
    x, y = 40, 236
    tag = f"{login.upper()} / GITHUB"
    front.append(f'<g class="f1"><rect x="{x - 4}" y="{y - 14}" width="{len(tag) * 8.2 + 8:.1f}" height="19" fill="{CREAM}"/>'
                 f'<text x="{x}" y="{y}" fill="{BLUE}" style="font-size:12px;letter-spacing:1px">{escape(tag)}</text></g>')
    appear("f1", 1.2)
    front.append(f'<text class="f2" x="{x}" y="{y + 36}" fill="{CREAM}" style="font-size:21px">{escape(FOCUS)}</text>')
    for i, line in enumerate(INTRO):
        front.append(f'<text class="f2" x="{x}" y="{y + 62 + i * 20}" fill="{CREAM}">{escape(line)}</text>')
    appear("f2", 1.35)
    ry = y + 62 + len(INTRO) * 20 + 22
    for n, (k, v) in enumerate(ROWS):
        yy = ry + n * 22
        front.append(f'<text class="r{n}" x="{x}" y="{yy}" fill="{CREAM}"><tspan style="font-size:11px;letter-spacing:1.5px">{escape(k.upper())}</tspan>'
                     f'<tspan x="{x + 11 * CW:.1f}">{escape(v)}</tspan></text>')
        appear(f"r{n}", 1.5 + n * 0.08)

    # ön: proje şeridi figürün halkasının önünden geçer
    py = H - 58
    proj = PROJECTS
    pt = f"PROJECTS  {proj}"
    pw = max(len(pt) * CW + 24, 700)  # şerit her durumda halkanın önünden geçer
    front.append(f'<g class="pj"><rect x="{x - 12}" y="{py - 18}" width="{pw:.1f}" height="28" fill="{BLUE}"/>'
                 f'<rect x="{x - 12}" y="{py - 18}" width="{pw:.1f}" height="28" fill="none" stroke="{CREAM}" stroke-width="2"/>'
                 f'<text x="{x}" y="{py + 1}" fill="{CREAM}"><tspan style="font-size:11px;letter-spacing:1.5px">PROJECTS</tspan>'
                 f'<tspan x="{x + 11 * CW:.1f}">{escape(proj)}</tspan></text></g>')
    appear("pj", 2.1)
    # dither rampası, sağ üst köşe işareti
    ramp = [CREAM, "url(#d75)", "url(#d50)", "url(#d25)"]
    front.append('<g class="rp">' + "".join(
        f'<rect x="{x + i * 22}" y="{py - 46}" width="22" height="10" fill="{c}"/>' for i, c in enumerate(ramp)) + "</g>")
    appear("rp", 2.0)

    label = (f"{login}: {FOCUS} {' '.join(INTRO)} " + "; ".join(f"{k}: {v}" for k, v in ROWS) + f"; Projects: {proj}.")
    style = (
        f"@font-face{{font-family:T;src:url(data:font/woff2;base64,{font_b64}) format('woff2')}}"
        f"text{{font-family:T,'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-size:{FS}px;white-space:pre}}"
        ".back,.f1,.f2,.pj,.rp,[class^=r]{opacity:0}"
        "@keyframes on{to{opacity:1}}"
        "@keyframes drop{to{transform:translateY(var(--h))}}"
        + "".join(css)
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}"
        ".back,.f1,.f2,.pj,.rp,[class^=r]{opacity:1}.scan{display:none}}"
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" shape-rendering="crispEdges">
<style>{style}</style>
<defs>{patterns()}</defs>
<rect width="{W}" height="{H}" fill="{BLUE}"/>
<g class="back">{back}</g>
{fig}
{"".join(front)}
<rect x="7" y="7" width="{W - 14}" height="{H - 14}" fill="none" stroke="{CREAM}" stroke-width="2"/>
</svg>
"""


# 28x28 1-bit logolar: Simple Icons (CC0) yollarından 1px ızgarada eşiklenmiş.
# Her satır 28 bitlik bir hex sayı; 1 = dolu piksel. İnce hatlı logolarda eşik düşük tutuldu.
ICONS = {
    "PYTHON": "003f800 00ffe00 019ff00 018ff80 019ff80 01fff80 0003f80 0003fb8 3ffffbc 7ffffbe 7ffff3e fffff3f ffffe7f ff8007f fe001ff fe7ffff fcfffff 7cffffe 7dffffe 3dffffc 1dfc000 01fc000 01fff80 01ff980 01ff180 00ff980 007ff00 001fc00",
    "JAVASCRIPT": "fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fff9e0f fff9c07 fff9cef fff98ff fff9c7f fff9c1f fff9f07 fff9fc7 fff9fe3 ffb9de3 ff11807 ff03c07 ffc7f1f fffffff fffffff",
    "TYPESCRIPT": "fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffffff fffff1f f001c07 f001807 ff1f0ff ff1f1ff ff1f0ff ff1f83f ff1fc0f ff1ff07 ff1ffc7 ff1ffc7 ff1f7c7 ff1f007 ff1f00f fffffff fffffff fffffff",
    "C++": "000f000 001f800 007fe00 01fff80 07fffe0 0fffff0 3fe07fc 3f801fc 3f000fc 3e0007c 3e0f0fc 3c1fbfc 3c3fffc 3c3ff34 3c3ff34 3c3fffc 3c1fbfc 3e0f0fc 3e0007c 3f000fc 3f801fc 3fe07fc 0fffff0 07fffe0 01fff80 007fe00 001f800 000f000",
    "RUST": "0016800 00dfb00 02fff40 03f9fc0 0fc63f0 0f000f0 3e0007c 1fffe38 7ffff1e 7ffff9e 25f0fa4 fdf0faf 71fff1e f1ffe0f f1fff0f 71f1f1e f1f0f9f 3ffcffc 7ffcffe 7ffc7fe 1c00038 3f801fc 0e40270 0fc03f0 03fffc0 02fff40 00dfb00 0016800",
    "LINUX": "000f800 001fc00 003fc00 003fe00 002ee00 003fe00 003be00 0020e00 0031e00 003f700 0060700 00e0780 00c03c0 01c03e0 03c01e0 03801e0 03801f0 07800f0 07001f0 05803f0 08c02c0 1060008 2070408 2020404 2011c08 301fc30 1f19c40 01e0780",
    "GIT": "0006000 000f000 001f800 001fc00 000fe00 00c7f00 01e1f80 03f0fc0 07f0fe0 0ff07f0 1ff83f8 3ff91fc 7ff987e fff9c3f fff9c3f 7ff9c7e 3ff9ffc 1ff9ff8 0ff8ff0 07f0fe0 03f0fc0 01f9f80 00fff00 007fe00 003fc00 001f800 000f000 0006000",
}
STACK = ["PYTHON", "JAVASCRIPT", "TYPESCRIPT", "C++", "RUST", "LINUX", "GIT"]
ICON = 28


def icon(rows, x, y, color):
    """Hex bitmap'i tek bir path'e çevirir: her yatay koşu 1px yüksekliğinde bir dikdörtgen."""
    d = []
    for r, word in enumerate(rows.split()):
        bits = f"{int(word, 16):0{ICON}b}"
        c = 0
        while c < ICON:
            if bits[c] != "1":
                c += 1
                continue
            run = c
            while run < ICON and bits[run] == "1":
                run += 1
            d.append(f"M{x + c} {y + r}h{run - c}v1h{c - run}z")
            c = run
    return f'<path fill="{color}" d="{"".join(d)}"/>'


def stack_svg(font_b64):
    """Stack şeridi: hepsi aynı mavi zeminli, krem çerçeveli, piksel logolu kutular."""
    cw, pad, h, gap, ig = 7.8 + 1, 9, 40, 6, 8  # 13px mono ilerleme + 1px harf aralığı; ig: logo-yazı arası
    x, tiles = 4, []
    for name in STACK:
        w = math.ceil(pad + ICON + ig + len(name) * cw - 1 + pad)  # tam sayı: logo pikselleri ızgaraya otursun
        tiles.append(f'<rect x="{x}" y="4" width="{w}" height="{h}" fill="{BLUE}" stroke="{CREAM}" stroke-width="2"/>'
                     + icon(ICONS[name], x + pad, 4 + (h - ICON) // 2, CREAM)
                     + f'<text x="{x + pad + ICON + ig}" y="29" fill="{CREAM}" style="font-size:13px;letter-spacing:1px">{name}</text>')
        x += w + gap
    width, height = x - gap + 4, h + 8
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="Stack: {", ".join(n.title() if n not in ("C++",) else n for n in STACK)}" shape-rendering="crispEdges">'
            f'<style>@font-face{{font-family:T;src:url(data:font/woff2;base64,{font_b64}) format(\'woff2\')}}'
            f"text{{font-family:T,'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;white-space:pre}}</style>"
            f'{"".join(tiles)}</svg>\n')


def main():
    login, out = sys.argv[1], Path(sys.argv[2])
    assets = Path(__file__).resolve().parent.parent / "assets"
    svg = build(login, base64.b64encode((assets / "card-font.woff2").read_bytes()).decode(),
                (assets / "card-figure.png").read_bytes())
    out.mkdir(parents=True, exist_ok=True)
    (out / "card.svg").write_text(svg, encoding="utf-8")
    stack = stack_svg(base64.b64encode((assets / "card-font.woff2").read_bytes()).decode())
    (out / "stack.svg").write_text(stack, encoding="utf-8")
    print(f"card.svg: {len(svg)} bayt, stack.svg: {len(stack)} bayt")


if __name__ == "__main__":
    main()
