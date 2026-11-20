"""Profil başlığı için animasyonlu terminal kartı (SVG).

Kartta `whoami` ve `fastfetch` yazılır; solda piksel karpuz dilimi, sağda GitHub'dan
gelen güncel bilgiler çıkar. Çalışma süresi (uptime) bilerek gösterilmez.

Kullanım: GITHUB_TOKEN=... python3 scripts/terminal.py <kullanıcı> <çıktı-dizini>

Yazı tipi (JetBrains Mono, SIL OFL 1.1) küçük bir alt küme olarak SVG'nin içine
gömülür; README görselleri <img> ile açıldığı için dış yazı tipi yüklenemez.
Animasyon yalnız CSS'tir; hareket azaltma tercihinde her şey doğrudan görünür.
"""
import base64
import json
import math
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    bio
    followers { totalCount }
    pullRequests { totalCount }
    contributionsCollection { contributionCalendar { totalContributions } }
    pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { name } } }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        stargazerCount
        defaultBranchRef { target { ... on Commit { history { totalCount } } } }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

# Makinenin kendisi: Action'da okunamaz, burada sabit tutulur.
SYSTEM = {"OS": "Debian GNU/Linux 13", "Shell": "fish", "Stack": "Python · JS · TS · C++ · Rust"}
SKIP_LANGS = {"Makefile", "Shell", "Batchfile", "PowerShell", "Dockerfile", "NSIS", "M4", "Roff", "Fluent", "Jinja", "Procfile"}
SHORT = {"Python": "Py", "JavaScript": "JS", "TypeScript": "TS", "C++": "C++", "Rust": "Rust", "HTML": "HTML", "CSS": "CSS", "Go": "Go"}

BG = "#0d0f14"
BAR = "#12151c"
FG = "#d7dae0"
MUTED = "#7c8290"
ACCENT = "#e5484d"
GREEN = "#46a758"
LABEL = "#e5a84d"

FS = 14            # yazı boyu
CW = FS * 0.6      # JetBrains Mono karakter genişliği
LH = 22            # satır yüksekliği
PAD = 24
WIDTH = 880


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        raise SystemExit(f"GraphQL hatası: {data['errors']}")
    return data["data"]["user"]


def facts(u):
    """Kartta görünecek etiket/değer satırları; sıfır olan sosyal sayılar gösterilmez."""
    repos = u["repositories"]["nodes"]
    commits = sum(((r.get("defaultBranchRef") or {}).get("target") or {}).get("history", {}).get("totalCount", 0)
                  for r in repos)
    stars = sum(r["stargazerCount"] for r in repos)
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            if name not in SKIP_LANGS:
                langs[name] = langs.get(name, 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    pinned = [n["name"] for n in u["pinnedItems"]["nodes"] if n]
    projects = pinned or [r["name"] for r in repos if r["name"] != u["login"]][:3]

    rows = [("OS", SYSTEM["OS"]), ("Shell", SYSTEM["Shell"]), ("Stack", SYSTEM["Stack"]),
            ("Repos", f"{u['repositories']['totalCount']} public")]
    if commits:
        rows.append(("Commits", f"{commits:,}".replace(",", ".")))
    rows.append(("Activity", f"{u['contributionsCollection']['contributionCalendar']['totalContributions']:,}".replace(",", ".")
                 + " contributions this year"))
    if u["pullRequests"]["totalCount"]:
        rows.append(("PRs", str(u["pullRequests"]["totalCount"])))
    if stars:
        rows.append(("Stars", str(stars)))
    if u["followers"]["totalCount"] >= 10:
        rows.append(("Followers", str(u["followers"]["totalCount"])))
    if top:
        rows.append(("Langs", " · ".join(f"{SHORT.get(n, n)} {round(100 * s / total)}%" for n, s in top)))
    rows.append(("Projects", " · ".join(projects[:3])))
    return rows


def melon(x0, y0, cell=8):
    """Piksel karpuz dilimi: kırmızı iç, çekirdekler, açık ve koyu yeşil kabuk."""
    out = []
    w, h = 26, 13
    cx, r = w / 2, 13.0
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + 0.5 - cx, y + 0.5)
            if d > r:
                continue
            if d > 11.8:
                color = GREEN
            elif d > 10.7:
                color = "#cfe8b8"
            elif y >= 2 and d < 9.4 and (x * 5 + y * 7) % 13 == 0:
                color = "#22181a"
            else:
                color = ACCENT
            out.append(f'<rect x="{x0 + x * cell}" y="{y0 + y * cell}" width="{cell}" height="{cell}" fill="{color}"/>')
    return "".join(out), w * cell, h * cell


def build(u, font_b64):
    login = u["login"]
    host = "github"
    bio = (u.get("bio") or "").strip()
    rows = facts(u)

    css = []
    body = []
    t = 0.35
    step_char = 0.065

    def appear(cls, at):
        css.append(f".{cls}{{animation:on .01s linear {at:.2f}s forwards}}")

    def prompt(y, cmd, at, cls):
        """İstem satırı; komut, imleç örtüsüyle harf harf açılır."""
        p_user = f'<tspan fill="{ACCENT}">{escape(login)}</tspan><tspan fill="{MUTED}">@</tspan><tspan fill="{FG}">{host}</tspan>'
        p_rest = f'<tspan fill="{MUTED}"> ~ </tspan><tspan fill="{GREEN}">❯</tspan>'
        plen = len(login) + 1 + len(host) + 3 + 1 + 1
        x_cmd = PAD + plen * CW
        body.append(f'<g class="{cls}"><text x="{PAD}" y="{y}">{p_user}{p_rest}</text>')
        if cmd:
            w = len(cmd) * CW
            body.append(f'<text x="{x_cmd:.1f}" y="{y}" fill="{FG}">{escape(cmd)}</text>'
                        f'<rect class="{cls}c" x="{x_cmd - 1:.1f}" y="{y - FS}" width="{w + CW + 2:.1f}" height="{FS + 6}" fill="{BG}"/>')
            css.append(f".{cls}c{{animation:type {len(cmd) * step_char:.2f}s steps({len(cmd)}) {at + 0.25:.2f}s forwards}}"
                       f".{cls}c{{--w:{w:.1f}px}}")
        body.append("</g>")
        appear(cls, at)
        return at + 0.25 + len(cmd) * step_char + 0.3

    y = 34 + PAD + 8
    t = prompt(y, "whoami", t, "p1")
    y += LH
    who = f"{login}" + (f" — {bio}" if bio else "")
    body.append(f'<text class="o1" x="{PAD}" y="{y}" fill="{FG}">{escape(who[:96])}</text>')
    appear("o1", t)
    t += 0.35
    y += LH + 8
    t = prompt(y, "fastfetch", t, "p2")
    y += 16

    art, aw, ah = melon(PAD, y)
    body.append(f'<g class="art">{art}</g>')
    appear("art", t)
    t += 0.15

    ix = PAD + aw + 36
    iy = y + 12
    head = f'<tspan fill="{ACCENT}">{escape(login)}</tspan><tspan fill="{MUTED}">@</tspan><tspan fill="{FG}">{host}</tspan>'
    body.append(f'<text class="i0" x="{ix}" y="{iy}">{head}</text>')
    appear("i0", t)
    body.append(f'<text class="i0" x="{ix}" y="{iy + LH}" fill="{MUTED}">{"─" * (len(login) + 1 + len(host))}</text>')
    label_w = max(len(k) for k, _ in rows) + 2
    for n, (k, v) in enumerate(rows, start=1):
        yy = iy + LH * (n + 1)
        t += 0.07
        body.append(f'<text class="i{n}" x="{ix}" y="{yy}"><tspan fill="{LABEL}">{escape(k)}</tspan>'
                    f'<tspan x="{ix + label_w * CW:.1f}" fill="{FG}">{escape(v)}</tspan></text>')
        appear(f"i{n}", t)
    yy = iy + LH * (len(rows) + 2) - 4
    t += 0.1
    sw = 22
    palette = ["#2a2f3a", ACCENT, GREEN, LABEL, "#5b8def", "#b072d6", "#3fb7c4", FG]
    body.append('<g class="pal">' + "".join(
        f'<rect x="{ix + i * sw}" y="{yy}" width="{sw}" height="12" fill="{c}"/>' for i, c in enumerate(palette)) + "</g>")
    appear("pal", t)

    y = max(y + ah, yy + 12) + LH + 10
    t += 0.3
    prompt(y, "", t, "p3")
    plen = len(login) + 1 + len(host) + 3 + 1 + 1
    body.append(f'<rect class="cur" x="{PAD + plen * CW:.1f}" y="{y - FS + 1}" width="{CW:.1f}" height="{FS + 3}" fill="{FG}"/>')
    css.append(f".cur{{opacity:0;animation:on .01s linear {t:.2f}s forwards, blink 1.1s steps(1) {t:.2f}s infinite}}")
    height = y + PAD

    label = (f"Terminal: {login}@{host} — whoami: {who}. fastfetch: "
             + "; ".join(f"{k}: {v}" for k, v in rows) + ".")
    style = (
        f"@font-face{{font-family:T;src:url(data:font/woff2;base64,{font_b64}) format('woff2')}}"
        f"text{{font-family:T,'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-size:{FS}px;white-space:pre}}"
        ".p1,.p2,.p3,.o1,.art,.pal,[class^=i]{opacity:0}"
        "@keyframes on{to{opacity:1}}"
        "@keyframes type{to{transform:translateX(var(--w))}}"
        "@keyframes blink{50%{opacity:0}}"
        + "".join(css)
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}"
        ".p1,.p2,.p3,.o1,.art,.pal,[class^=i],.cur{opacity:1}[class$=c]{display:none}}"
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(label)}">
<style>{style}</style>
<rect width="{WIDTH}" height="{height}" rx="10" fill="{BG}"/>
<rect width="{WIDTH}" height="34" rx="10" fill="{BAR}"/><rect y="24" width="{WIDTH}" height="10" fill="{BAR}"/>
<rect y="34" width="{WIDTH}" height="1" fill="#1e222b"/>
<circle cx="20" cy="17" r="5" fill="#2a2f3a"/><circle cx="38" cy="17" r="5" fill="#2a2f3a"/><circle cx="56" cy="17" r="5" fill="#2a2f3a"/>
<text x="{WIDTH / 2}" y="22" fill="{MUTED}" text-anchor="middle" style="font-size:12px">{escape(login)}@{host}: ~ — fish</text>
{"".join(body)}
</svg>
"""


def main():
    if len(sys.argv) != 3:
        raise SystemExit("kullanım: terminal.py <kullanıcı> <çıktı-dizini>")
    login, out = sys.argv[1], Path(sys.argv[2])
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN gerekli")
    font = Path(__file__).resolve().parent.parent / "assets" / "terminal-font.woff2"
    svg = build(fetch(login, token), base64.b64encode(font.read_bytes()).decode())
    out.mkdir(parents=True, exist_ok=True)
    (out / "terminal.svg").write_text(svg, encoding="utf-8")
    print(f"terminal.svg: {len(svg)} bayt")


if __name__ == "__main__":
    main()
