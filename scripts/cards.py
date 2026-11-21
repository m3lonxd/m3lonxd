"""Profil kartlarını (istatistik + diller) GitHub GraphQL verisinden SVG olarak üretir.

Kullanım: GITHUB_TOKEN=... python3 scripts/cards.py <kullanıcı> <çıktı-dizini>
Yalnızca herkese açık, çatal olmayan depolar sayılır.
"""
import base64
import json
import os
import sys
import urllib.request
from html import escape

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection { contributionCalendar { totalContributions } }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        defaultBranchRef { target { ... on Commit { history { totalCount } } } }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

MONO = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace"
# Depolarda dil olarak görünse de profilde anlamsız olanlar (üretilmiş/derleme dosyaları).
SKIP_LANGS = {"Makefile", "Shell", "Batchfile", "PowerShell", "Dockerfile", "NSIS", "M4", "Roff", "Fluent", "Jinja", "Procfile"}


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        raise SystemExit(f"GraphQL hatası: {data['errors']}")
    return data["data"]["user"]


BLUE = "#1b22cf"
CREAM = "#ece8cc"
P = 2  # dither pikseli
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
FONT_FILE = os.path.join(ASSETS, "card-font.woff2")
# Dil çubuğu ve lejant: renk yerine nokta yoğunluğu (sırayla)
FILLS = [CREAM, "url(#d75)", "url(#d50)", "url(#d25)", "url(#d12)", "none"]


def _font():
    with open(FONT_FILE, "rb") as f:
        return base64.b64encode(f.read()).decode()


def figure(name, x, y, w, h):
    """1-bit figür (assets/card-*.png), piksel başına bir nokta; ölçeklenince bulanıklaşmasın."""
    with open(os.path.join(ASSETS, name), "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return (f'  <image x="{x}" y="{y}" width="{w}" height="{h}" style="image-rendering:pixelated" '
            f'href="data:image/png;base64,{data}"/>')


def network(cx, cy, r=20.8, node=6.2):
    """Avuçtaki ağ sembolü: merkez ve altı düğüm, kart mavisiyle keskin vektör."""
    import math
    parts = []
    for k in range(6):
        a = math.radians(-90 + 60 * k)
        nx, ny = cx + r * math.cos(a), cy + r * math.sin(a)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{BLUE}" stroke-width="2.2"/>'
                     f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{node}" fill="{BLUE}"/>')
    parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.6" fill="{BLUE}"/>')
    return '  <g shape-rendering="geometricPrecision">' + "".join(parts) + "</g>"


def frame(width, height, title, inner):
    """Başlık kartıyla aynı dil: mavi zemin, krem çerçeve, ters renkli başlık, 1-bit dither."""
    t = title.upper()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" shape-rendering="crispEdges">
  <style>@font-face{{font-family:T;src:url(data:font/woff2;base64,{_font()}) format('woff2')}}text{{font-family:T,{MONO};white-space:pre}}</style>
  <defs>
    <pattern id="d12" width="{P * 4}" height="{P * 4}" patternUnits="userSpaceOnUse"><rect width="{P}" height="{P}" fill="{CREAM}"/></pattern>
    <pattern id="d25" width="{P * 4}" height="{P * 4}" patternUnits="userSpaceOnUse"><rect width="{P}" height="{P}" fill="{CREAM}"/><rect x="{P * 2}" y="{P * 2}" width="{P}" height="{P}" fill="{CREAM}"/></pattern>
    <pattern id="d50" width="{P * 2}" height="{P * 2}" patternUnits="userSpaceOnUse"><rect width="{P}" height="{P}" fill="{CREAM}"/><rect x="{P}" y="{P}" width="{P}" height="{P}" fill="{CREAM}"/></pattern>
    <pattern id="d75" width="{P * 4}" height="{P * 4}" patternUnits="userSpaceOnUse"><rect width="{P * 4}" height="{P * 4}" fill="{CREAM}"/><rect width="{P}" height="{P}" fill="{BLUE}"/><rect x="{P * 2}" y="{P * 2}" width="{P}" height="{P}" fill="{BLUE}"/></pattern>
  </defs>
  <rect width="{width}" height="{height}" fill="{BLUE}"/>
  <rect x="6" y="6" width="{width - 12}" height="{height - 12}" fill="none" stroke="{CREAM}" stroke-width="2"/>
  <rect x="10" y="10" width="{width - 20}" height="26" fill="url(#d25)"/>
  <rect x="18" y="14" width="{len(t) * 8.2 + 12:.1f}" height="18" fill="{CREAM}"/>
  <text x="24" y="27" font-size="12" letter-spacing="1" fill="{BLUE}">{escape(t)}</text>
  <rect x="10" y="36" width="{width - 20}" height="2" fill="{CREAM}"/>
{inner}
</svg>
"""


def stats_card(user):
    repos = user["repositories"]
    cc = user["contributionsCollection"]
    commits = sum(
        (n["defaultBranchRef"] or {}).get("target", {}).get("history", {}).get("totalCount", 0)
        for n in repos["nodes"]
    )
    rows = [
        ("PUBLIC REPOSITORIES", repos["totalCount"]),
        ("COMMITS ACROSS REPOS", commits),
        ("CONTRIBUTIONS, LAST YEAR", cc["contributionCalendar"]["totalContributions"]),
    ]
    lines = []
    for i, (label, value) in enumerate(rows):
        y = 60 + i * 22
        lines.append(
            f'  <rect x="24" y="{y - 9}" width="8" height="8" fill="{FILLS[i]}" stroke="{CREAM}" stroke-width="1"/>'
            f'<text x="42" y="{y}" font-size="11" letter-spacing="1.5" fill="{CREAM}">{label}</text>'
            f'<text x="374" y="{y + 1}" text-anchor="end" font-size="17" fill="{CREAM}">{value:,}</text>'
            f'<rect x="24" y="{y + 6}" width="350" height="2" fill="url(#d25)"/>'
        )
    # Göz şeridi: başlık bandıyla aynı genişlikte, kartın altında "izleyen" bakış
    lines.append(figure("card-eyes.png", 10, 118, 380, 68))
    return frame(400, 196, "Activity", "\n".join(lines))


def langs_card(user):
    totals = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in SKIP_LANGS:
                continue
            totals[name] = totals.get(name, 0) + edge["size"]
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    whole = sum(size for _, size in top)
    if not whole:
        return frame(400, 196, "Languages", f'  <text x="26" y="80" font-size="13" fill="{CREAM}">No public code yet.</text>')

    # Sol sütun: çubuk + tek sütun lejant; sağda dışarıdan uzanan el
    bar, x = [], 24.0
    for i, (name, size) in enumerate(top):
        w = 176 * size / whole
        fill = FILLS[i] if FILLS[i] != "none" else BLUE
        bar.append(f'<rect x="{x:.2f}" y="52" width="{w:.2f}" height="14" fill="{fill}"/>')
        x += w
    bar.append(f'<rect x="23" y="51" width="178" height="16" fill="none" stroke="{CREAM}" stroke-width="2"/>')
    legend = []
    for i, (name, size) in enumerate(top):
        ly = 92 + i * 17
        legend.append(
            f'  <rect x="24" y="{ly - 9}" width="10" height="10" fill="{FILLS[i]}" stroke="{CREAM}" stroke-width="1"/>'
            f'<text x="42" y="{ly}" font-size="12" fill="{CREAM}">{escape(name)}</text>'
            f'<text x="200" y="{ly}" text-anchor="end" font-size="12" fill="{CREAM}">{100 * size / whole:.1f}%</text>'
        )
    # El saydam zeminli: krem kol sağ çerçevenin önüne geçer, derinlik verir
    hx, hy = 224, 48
    hand = figure("card-hand.png", hx, hy, 176, 136) + "\n" + network(hx + 107.5, hy + 55.5)
    return frame(400, 196, "Languages", "\n".join(bar) + "\n" + "\n".join(legend) + "\n" + hand)


def main():
    login, out = sys.argv[1], sys.argv[2]
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN gerekli")
    user = fetch(login, token)
    os.makedirs(out, exist_ok=True)
    for name, svg in (("stats.svg", stats_card(user)), ("langs.svg", langs_card(user))):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(svg)
    print(f"{out}/stats.svg, {out}/langs.svg yazıldı")


if __name__ == "__main__":
    main()
