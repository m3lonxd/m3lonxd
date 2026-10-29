"""Profil kartlarını (istatistik + diller) GitHub GraphQL verisinden SVG olarak üretir.

Kullanım: GITHUB_TOKEN=... python3 scripts/cards.py <kullanıcı> <çıktı-dizini>
Yalnızca herkese açık, çatal olmayan depolar sayılır.
"""
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

ACCENT = "#e5484d"
FONT = "Inter, -apple-system, 'Segoe UI', sans-serif"
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


def frame(width, height, title, inner):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d0f14"/><stop offset="1" stop-color="#140c0e"/>
    </linearGradient>
    <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity=".10"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" rx="18" fill="url(#bg)"/>
  <rect width="{width}" height="{height}" rx="18" fill="url(#sheen)"/>
  <rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="17.5" fill="none" stroke="#fff" stroke-opacity=".14"/>
  <text x="26" y="40" font-family="{FONT}" font-size="17" font-weight="700" fill="#f3f4f7">{escape(title)}</text>
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
        ("Public repositories", repos["totalCount"]),
        ("Commits across repositories", commits),
        ("Contributions (last year)", cc["contributionCalendar"]["totalContributions"]),
    ]
    lines = []
    for i, (label, value) in enumerate(rows):
        y = 78 + i * 30
        lines.append(
            f'  <circle cx="32" cy="{y - 5}" r="3.5" fill="{ACCENT}"/>'
            f'<text x="46" y="{y}" font-family="{FONT}" font-size="14" fill="#b8bec9">{label}</text>'
            f'<text x="374" y="{y}" text-anchor="end" font-family="{MONO}" font-size="15" font-weight="600" fill="#f3f4f7">{value:,}</text>'
        )
    return frame(400, 196, "Activity", "\n".join(lines))


def langs_card(user):
    totals = {}
    colors = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in SKIP_LANGS:
                continue
            totals[name] = totals.get(name, 0) + edge["size"]
            colors[name] = edge["node"]["color"] or "#8b8f98"
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    whole = sum(size for _, size in top)
    if not whole:
        return frame(400, 196, "Languages", f'  <text x="26" y="80" font-family="{FONT}" font-size="14" fill="#b8bec9">No public code yet.</text>')

    bar, x = [], 26.0
    for name, size in top:
        w = 348 * size / whole
        bar.append(f'<rect x="{x:.2f}" y="58" width="{w:.2f}" height="10" fill="{colors[name]}"/>')
        x += w
    legend = []
    for i, (name, size) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 26 + col * 180, 104 + row * 32
        legend.append(
            f'  <circle cx="{lx + 5}" cy="{ly - 5}" r="5" fill="{colors[name]}"/>'
            f'<text x="{lx + 18}" y="{ly}" font-family="{FONT}" font-size="14" fill="#e6e8ee">{escape(name)}</text>'
            f'<text x="{lx + 168}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="13" fill="#9097a3">{100 * size / whole:.1f}%</text>'
        )
    inner = (
        '  <clipPath id="bar"><rect x="26" y="58" width="348" height="10" rx="5"/></clipPath>\n'
        f'  <g clip-path="url(#bar)">{"".join(bar)}</g>\n' + "\n".join(legend)
    )
    return frame(400, 196, "Languages", inner)


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
