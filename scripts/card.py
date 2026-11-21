"""Profil başlık kartı: mavi-krem 1-bit baskı teması, katmanlı derinlik.

Katmanlar (arkadan öne):
  1. mavi zemin
  2. dev piksel "M3LON" yazısı (krem, alt satırlar dither)
  3. figür: assets/card-figure.png; saydam dış, mavi silüet içi, krem noktalar.
     Silüetin mavi içi arkadaki yazıyı örter; halkanın ortası saydam kalır.
  4. ön yazılar: kimlik, istatistikler ve figürün üzerinden geçen proje şeridi
  5. ince krem çerçeve

İçerik sabittir (odak: AI ajanları ve siber güvenlik); GitHub verisi ya da token gerekmez.
Kullanım: python3 scripts/card.py <kullanıcı> assets   (assets/card.svg üretir; içerik sabit, workflow gerekmez)
"""
import base64
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


def main():
    login, out = sys.argv[1], Path(sys.argv[2])
    assets = Path(__file__).resolve().parent.parent / "assets"
    svg = build(login, base64.b64encode((assets / "card-font.woff2").read_bytes()).decode(),
                (assets / "card-figure.png").read_bytes())
    out.mkdir(parents=True, exist_ok=True)
    (out / "card.svg").write_text(svg, encoding="utf-8")
    print(f"card.svg: {len(svg)} bayt")


if __name__ == "__main__":
    main()
