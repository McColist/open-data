"""Delta Scout - report HTML completi per partita, generati dai CSV di delta_scout/output.

Uso:
    python delta_scout/report.py                  # tutte le partite
    python delta_scout/report.py --n 778,831-894  # solo alcuni numeri
    python delta_scout/report.py --out C:\\DeltaScout\\report

Serve solo l'output di analizza.py (non i dati grezzi). Apri index.html nella cartella di output.
"""
import argparse
import csv
import gzip
import html
import json
import math
from collections import defaultdict
from itertools import groupby
from pathlib import Path

HERE = Path(__file__).resolve().parent
COL = ("#2a6fdb", "#e0533d")  # casa, trasferta

TEAM_ROWS = [
    ("Gol", "gol", 0), ("xG", "xg", 2), ("xT – minaccia creata con passaggi e conduzioni", "xt", 2), ("xG senza rigori", "npxg", 2), ("Tiri", "tiri", 0),
    ("Tiri in porta", "tiri_in_porta", 0), ("Tiri in area", "tiri_in_area", 0), ("xG per tiro", "xg_per_tiro", 3),
    ("Possesso %", "possesso_pct", 1), ("Field tilt %", "field_tilt_pct", 1), ("PPDA (basso = pressing intenso)", "ppda", 2),
    ("Passaggi", "passaggi", 0), ("Precisione passaggi %", "precisione_passaggi_pct", 1),
    ("Passaggi progressivi", "passaggi_progressivi", 0), ("Passaggi nel terzo finale", "passaggi_terzo_finale", 0),
    ("Passaggi in area", "passaggi_in_area", 0), ("Passaggi chiave", "passaggi_chiave", 0), ("Cross", "cross", 0),
    ("Cross riusciti", "cross_riusciti", 0), ("Conduzioni progressive", "conduzioni_progressive", 0),
    ("Dribbling riusciti", "dribbling_riusciti", 0), ("Pressioni", "pressioni", 0), ("Pressioni alte", "pressioni_alte", 0),
    ("Contropressioni", "contropressioni", 0), ("Recuperi", "recuperi", 0), ("Recuperi alti", "recuperi_alti", 0),
    ("Contrasti vinti", "contrasti_vinti", 0), ("Intercetti", "intercetti", 0), ("Duelli aerei vinti", "aerei_vinti", 0),
    ("Palle perse", "palle_perse", 0), ("Parate", "parate", 0), ("Corner", "corner", 0), ("Fuorigioco", "fuorigioco", 0),
    ("Falli", "falli", 0), ("Gialli", "gialli", 0), ("Rossi", "rossi", 0),
    ("Tiri subiti", "tiri_subiti", 0), ("Azioni che portano al tiro (SCA)", "azioni_tiro_sca", 0),
    ("Tiri da contropiede", "tiri_contropiede", 0), ("Possessi", "possessi", 0),
    ("Passaggi per possesso", "passaggi_per_possesso", 2), ("Sequenze da 10+ passaggi", "sequenze_10_passaggi", 0),
    ("Lunghezza media passaggi (m)", "lunghezza_media_passaggi_m", 1), ("Passaggi in avanti %", "passaggi_avanti_pct", 1),
    ("Lanci lunghi", "lanci_lunghi", 0), ("Passaggi sotto pressione", "passaggi_sotto_pressione", 0),
    ("Contese vinte (50/50)", "contese_vinte", 0),
    ("360: avversari entro 5 m dal portatore", "avversari_5m_medi_360", 2),
    ("360: azioni sotto pressione %", "azioni_pressate_360_pct", 1),
]

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b1f24;--mute:#66707a;--line:#e3e6ea;--pitch:#eef3ee;--pl:#b9c7b9}
@media (prefers-color-scheme:dark){:root{--bg:#14171a;--card:#1d2125;--ink:#e8eaed;--mute:#9aa3ad;--line:#30363d;--pitch:#1f2a22;--pl:#3f5244}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}a{color:inherit}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px}
h1{font-size:15px;font-weight:500;color:var(--mute);margin:0 0 6px}h2{font-size:17px;margin:0 0 12px}h3{font-size:15px;margin:12px 0 8px}
.score{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:center;text-align:center}
.score .t{font-size:20px;font-weight:600}.score .r{font-size:38px;font-weight:700;font-variant-numeric:tabular-nums}
.sub{color:var(--mute);font-size:13px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:760px){.grid2{grid-template-columns:1fr}.score .t{font-size:16px}.score .r{font-size:30px}}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
.cmp td{padding:3px 6px;border-bottom:1px solid var(--line)}.cmp td.v{width:64px;text-align:center;font-weight:600}
.cmp td.l{text-align:center;color:var(--mute);font-size:13px}.bar{display:flex;height:6px;border-radius:3px;overflow:hidden;background:var(--line);margin-top:3px}
.scroll{overflow-x:auto}.pl{font-size:12.5px;white-space:nowrap}.pl th{position:sticky;top:0;background:var(--card);font-weight:600;color:var(--mute);text-align:right;padding:4px 6px;border-bottom:1px solid var(--line)}
.pl td{text-align:right;padding:3px 6px;border-bottom:1px solid var(--line)}.pl td:first-child,.pl th:first-child{text-align:left;position:sticky;left:0;background:var(--card)}
.pl tr.sub td{color:var(--mute)}ul{margin:0;padding-left:18px}li{margin:3px 0}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
svg{display:block;width:100%;height:auto}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}.tabs button{font:inherit;font-size:13px;padding:4px 10px;border-radius:14px;
border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}.tabs button.on{background:var(--ink);color:var(--card)}
.hidden{display:none}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}@media (max-width:760px){.grid3{grid-template-columns:1fr}}
.tl td{padding:3px 6px;border-bottom:1px solid var(--line);vertical-align:top}.tl td.m{width:44px;text-align:right;color:var(--mute)}
.st td,.st th{padding:3px 6px;border-bottom:1px solid var(--line);text-align:right}.st th{color:var(--mute);font-weight:600}.st td:first-child,.st th:first-child{text-align:left}
.kv{display:flex;flex-wrap:wrap;gap:4px 18px;justify-content:center;margin-top:8px}.legend{font-size:12px;color:var(--mute);margin-top:6px}
.topnav{position:sticky;top:0;z-index:10;display:flex;gap:4px 14px;align-items:center;flex-wrap:nowrap;overflow-x:auto;
background:var(--bg);border-bottom:1px solid var(--line);padding:8px 16px;margin:0 -16px 14px;font-size:13px;white-space:nowrap}
.topnav a{color:var(--mute);text-decoration:none}.topnav a:hover{color:var(--ink)}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;color:var(--ink)!important;margin-right:8px}
.foot{border-top:1px solid var(--line);margin-top:24px;padding-top:12px;font-size:12px;color:var(--mute);display:grid;gap:8px}
.foot .sb{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.foot img{background:#fff;border-radius:4px;padding:2px 4px}
svg{-webkit-user-select:none;user-select:none}.card{scroll-margin-top:60px}
.flt{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;margin:0 0 10px;font-size:12.5px;color:var(--mute)}
.flt button{font:inherit;font-size:12.5px;padding:3px 9px;border-radius:12px;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}
.flt button.on{background:var(--ink);color:var(--card)}
.lg{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12px;color:var(--mute);margin-top:10px;align-items:center}
.lg span{display:inline-flex;align-items:center;gap:6px}.lg svg{display:inline-block;width:auto;height:12px}
"""


ANAG, ELO = {}, {}


ROLE_IT = {
    "Goalkeeper": "Portiere", "Right Back": "Terzino destro", "Right Center Back": "Difensore centrale destro",
    "Center Back": "Difensore centrale", "Left Center Back": "Difensore centrale sinistro", "Left Back": "Terzino sinistro",
    "Right Wing Back": "Esterno a tutta fascia destro", "Left Wing Back": "Esterno a tutta fascia sinistro",
    "Right Defensive Midfield": "Mediano destro", "Center Defensive Midfield": "Mediano", "Left Defensive Midfield": "Mediano sinistro",
    "Right Midfield": "Esterno destro di centrocampo", "Right Center Midfield": "Mezzala destra", "Center Midfield": "Centrocampista centrale",
    "Left Center Midfield": "Mezzala sinistra", "Left Midfield": "Esterno sinistro di centrocampo", "Right Wing": "Ala destra",
    "Right Attacking Midfield": "Trequartista destro", "Center Attacking Midfield": "Trequartista",
    "Left Attacking Midfield": "Trequartista sinistro", "Left Wing": "Ala sinistra", "Right Center Forward": "Attaccante destro",
    "Center Forward": "Centravanti", "Left Center Forward": "Attaccante sinistro", "Secondary Striker": "Seconda punta",
}
REEP_IT = {
    "goalkeeper": "Portiere", "centre-back": "Difensore centrale", "left-back": "Terzino sinistro", "right-back": "Terzino destro",
    "defensive midfield": "Mediano", "central midfield": "Centrocampista centrale", "attacking midfield": "Trequartista",
    "left midfield": "Esterno sinistro", "right midfield": "Esterno destro", "left winger": "Ala sinistra", "right winger": "Ala destra",
    "second striker": "Seconda punta", "centre-forward": "Centravanti", "forward": "Attaccante", "defender": "Difensore",
    "midfielder": "Centrocampista", "defensive midfielder": "Mediano", "winger": "Ala", "full-back": "Terzino",
    "wing-back": "Esterno a tutta fascia", "striker": "Attaccante", "attacking midfielder": "Trequartista",
}
FASI = {"Final": "Finale", "Group Stage": "Fase a gironi", "Round of 16": "Ottavi di finale", "Quarter-finals": "Quarti di finale",
        "Semi-finals": "Semifinali", "3rd Place Final": "Finale 3° posto", "Regular Season": "Campionato",
        "Round of 32": "Sedicesimi di finale", "Play-offs": "Play-off"}
CORPO = {"Right Foot": "Destro", "Left Foot": "Sinistro", "Head": "Testa", "Other": "Altro"}
MOTIVI = {"(Tactical)": "(scelta tecnica)", "(Injury)": "(infortunio)"}


def it_role(r):
    return ROLE_IT.get(r, r)


def it_roles(s):
    return " → ".join(it_role(x) for x in s.split(" → ")) if s else ""


LOGO_INNER = ('<g fill="none" stroke="#4a6a96" stroke-width="4"><rect x="251" y="375" width="698" height="494"/>'
              '<line x1="600" y1="483" x2="600" y2="869"/><circle cx="600" cy="622" r="54"/></g>'
              '<path d="M118 785 C300 770 380 690 470 525 C540 395 565 330 600 330 C635 330 660 395 730 525 C820 690 900 770 1082 785" '
              'fill="none" stroke="#7cc4f2" stroke-width="6" stroke-linecap="round"/><g stroke="#f4f4f4" stroke-width="20">'
              '<line x1="615" y1="462" x2="801" y2="777"/><line x1="410" y1="805" x2="786" y2="805"/><line x1="398" y1="778" x2="545" y2="530"/></g>'
              '<polygon points="512,520 576,477 567,552" fill="#f4f4f4"/>'
              '<circle cx="600" cy="435" r="30" fill="#111214" stroke="#7cc4f2" stroke-width="17"/>'
              '<circle cx="381" cy="805" r="30" fill="#111214" stroke="#f4f4f4" stroke-width="14"/>'
              '<circle cx="816" cy="805" r="30" fill="#111214" stroke="#f4f4f4" stroke-width="14"/>')
LOGO_SYMBOL = f'<svg style="display:none" aria-hidden="true"><symbol id="dslogo" viewBox="0 0 1200 1200">{LOGO_INNER}</symbol></svg>'
FAVICON = ("data:image/svg+xml," + __import__("urllib.parse").parse.quote(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="160 220 880 880"><rect x="160" y="220" width="880" height="880" rx="120" fill="#111214"/>{LOGO_INNER}</svg>'))
YEAR = "2026"
HEAD_EXTRA = (f'<link rel="icon" href="{FAVICON}"><meta name="copyright" content="© {YEAR} Delta Scout. Tutti i diritti riservati.">'
              '<meta name="robots" content="noai, noimageai">')
PROTECT_JS = ("<script>document.addEventListener('contextmenu',function(e){if(e.target.closest('svg'))e.preventDefault()});"
              "document.addEventListener('dragstart',function(e){if(e.target.closest('svg'))e.preventDefault()});</script>")


def brand_bar(nav=""):
    return (f'{LOGO_SYMBOL}<nav class="topnav"><a class="brand" href="index.html"><svg viewBox="0 0 1200 1200" width="30" height="30">'
            f'<rect width="1200" height="1200" rx="170" fill="#111214"/><use href="#dslogo" x="-330" y="-380" width="1860" height="1860"/></svg>'
            f'<span>Delta Scout</span></a>{nav}</nav>')


INDEX_NAV = '<a href="classifiche.html">Classifiche di tutti i tempi</a> <a href="studi.html">Studi</a> <a href="dati.html">Il dato spiegato</a>'


def footer():
    return (f'<footer class="foot"><div><b>© {YEAR} Delta Scout</b> – tutti i diritti riservati. Testi, grafici, indici (voto Delta Scout, '
            'classifiche) e impaginazione sono opera di Delta Scout: è vietata la riproduzione, anche parziale, senza autorizzazione scritta. '
            'Le condivisioni devono citare Delta Scout e linkare la pagina originale.</div>'
            '<div class="sb"><span>Dati evento:</span><img src="statsbomb_logo.png" alt="StatsBomb" height="22"> '
            '<span>StatsBomb Open Data · anagrafica: Reep (CC0)</span></div></footer>')


CAREER, ROLE_AVG, VOTI = {}, {}, {}
_js = HERE / "esporta_social.js"
EXPORT_JS = _js.read_text(encoding="utf-8") if _js.exists() else ""
_sb = HERE / "statsbomb_logo_small.png"
SB_B64 = "data:image/png;base64," + __import__("base64").b64encode(_sb.read_bytes()).decode() if _sb.exists() else ""
SOCIAL_STATS = [("Gol", "gol", 0), ("xG", "xg", 2), ("xT", "xt", 2), ("Tiri", "tiri", 0), ("Tiri in porta", "tiri_in_porta", 0),
                ("Possesso %", "possesso_pct", 0), ("Field tilt %", "field_tilt_pct", 0), ("PPDA (basso = più pressing)", "ppda", 1),
                ("Passaggi", "passaggi", 0), ("Precisione passaggi %", "precisione_passaggi_pct", 0),
                ("Passaggi progressivi", "passaggi_progressivi", 0), ("Pressioni alte", "pressioni_alte", 0),
                ("Recuperi alti", "recuperi_alti", 0), ("Contrasti vinti", "contrasti_vinti", 0)]


def plain(h):
    return html.unescape(__import__("re").sub(r"<[^>]+>", "", h)).strip()


def social_box(T, P, teams, text, keys):
    h, a = T[teams[0]], T[teams[1]]
    rated = sorted([p for p in P if p.get("voto")], key=lambda p: -float(p["voto"]))
    best = rated[0] if rated else None
    info = " · ".join(x for x in (FASI.get(h.get("fase"), h.get("fase")), h["data"], h.get("stadio")) if x)
    slug = __import__("re").sub(r"[^a-z0-9]+", "_", f'{h["n"]} {teams[0]} {teams[1]}'.lower()).strip("_")
    ds = {"title": f'{teams[0]} {h["gol"]}–{a["gol"]} {teams[1]}', "sub": f'{h["competizione"]} {h["stagione"]}', "slug": slug,
          "logo": FAVICON, "sb": SB_B64, "col": list(COL),
          "cover": {"home": teams[0], "away": teams[1], "gh": h["gol"], "ga": a["gol"], "xgh": f(h["xg"]), "xga": f(a["xg"]),
                    "comp": f'{h["competizione"]} {h["stagione"]}', "info": info,
                    "best": [short(best), best["squadra"], f'{float(best["voto"]):.1f}'] if best else None},
          "text": plain(" ".join(text)), "keys": [plain(k) for k in keys],
          "stats": [[lab, f(h.get(k), d), f(a.get(k), d)] for lab, k, d in SOCIAL_STATS if h.get(k) not in (None, "")],
          "top": [[short(p), p["squadra"], teams.index(p["squadra"]) if p["squadra"] in teams else 0, f'{float(p["voto"]):.1f}'] for p in rated[:14]]}
    js = json.dumps(ds, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    btns = "".join(f'<button data-f="{k}">{v}</button>' for k, v in (("4:5", "Instagram / LinkedIn 4:5"), ("1:1", "Quadrato 1:1"),
                                                                      ("9:16", "TikTok / Storie 9:16"), ("16:9", "X 16:9")))
    return (f'<div class="card" id="social"><h2>Pubblica sui social</h2><p class="sub" style="margin:0 0 10px">Crea il report come carosello di '
            f'slide (copertina, analisi, statistiche, pagelle, formazioni, tiri, conduzioni, pressing, reti di passaggi), con logo Delta Scout e '
            f'attribuzione StatsBomb. Scarichi uno zip con le immagini PNG e un PDF: il PDF si carica su LinkedIn come documento, le immagini su '
            f'Instagram, TikTok (modalità foto) e X (massimo 4 per post). Le immagini vengono create nel browser, non serve installare nulla.</p>'
            f'<div class="flt" id="exp-box">{btns}</div><p class="sub" id="exp-status"></p>'
            f'<script type="application/json" id="ds-export">{js}</script></div>')
CTX = [("xg", "xG"), ("xa", "xA"), ("xt", "xT"), ("sca", "SCA"), ("passaggi_progressivi", "Pass. progr."),
       ("conduzioni_progressive", "Cond. progr."), ("dribbling_riusciti", "Dribbling"), ("azioni_difensive", "Az. difensive"),
       ("pressioni", "Pressioni")]


def match_p90(p, k):
    m = num(p["minuti"])
    if m < 30:
        return None
    v = num(p["contrasti_vinti"]) + num(p["intercetti"]) + num(p["recuperi"]) if k == "azioni_difensive" else num(p.get(k))
    return v / m * 90


def ctx_cell(p, k):
    v = match_p90(p, k)
    c = CAREER.get(p["player_id"])
    if v is None or not c:
        return "–"
    car = num(c.get(f"{k}_p90"))
    d = 1 if max(v, car) >= 10 else 2
    if car > 0 and v >= 1.5 * car and v - car > 0.05:
        arrow = '<span style="color:#2f9e44">▲</span>'
    elif car > 0 and v <= 0.5 * car:
        arrow = '<span style="color:#e03131">▼</span>'
    else:
        arrow = ""
    return f'<b>{v:.{d}f}</b>{arrow}<span class="sub"> / {car:.{d}f}</span>'


def voto_badge(v, size="13px"):
    if v in (None, ""):
        return '<span class="sub">s.v.</span>'
    x = float(v)
    col = "#1c7ed6" if x >= 8 else "#2f9e44" if x >= 7 else "#94b51f" if x >= 6.5 else "#f08c00" if x >= 6 else "#e03131"
    return f'<span style="background:{col};color:#fff;border-radius:4px;padding:1px 5px;font-weight:700;font-size:{size}">{x:.1f}</span>'


def voto_col(v):
    x = float(v)
    return "#1c7ed6" if x >= 8 else "#2f9e44" if x >= 7 else "#94b51f" if x >= 6.5 else "#f08c00" if x >= 6 else "#e03131"


def age(p, data):
    dob = ANAG.get(p["player_id"], {}).get("data_nascita")
    if not dob:
        return ""
    y, m, d = map(int, data.split("-"))
    by, bm, bd = map(int, dob.split("-"))
    return str(y - by - ((m, d) < (bm, bd)))


def f(v, d=2):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "–"
    return f"{x:.{d}f}" if d else f"{x:.0f}"


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def e(s):
    return html.escape(str(s))


def short(p):
    return p.get("soprannome") or p["giocatore"]


def pitch(inner, half=False):
    w = 60 if half else 120
    x0 = 60 if half else 0
    lines = (f'<rect x="{x0}" y="0" width="{w}" height="80" fill="var(--pitch)"/>'
             '<g fill="none" stroke="var(--pl)" stroke-width="0.4">'
             '<rect x="0" y="0" width="120" height="80"/><line x1="60" y1="0" x2="60" y2="80"/>'
             '<circle cx="60" cy="40" r="10"/><rect x="0" y="18" width="18" height="44"/><rect x="102" y="18" width="18" height="44"/>'
             '<rect x="0" y="30" width="6" height="20"/><rect x="114" y="30" width="6" height="20"/></g>')
    mark = (f'<use href="#dslogo" x="{x0 + w / 2 - 9}" y="31" width="18" height="18" opacity="0.07"/>'
            f'<text x="{x0 + w - 1}" y="79" font-size="1.9" fill="var(--mute)" text-anchor="end" opacity="0.8">© Delta Scout</text>')
    return f'<svg viewBox="{x0 - 1} -1 {w + 2} 82" role="img">{lines}{mark}{inner}</svg>'


def shot_map(shots, teams):
    out = []
    for s in shots:
        home = s["squadra"] == teams[0]
        x, y = num(s["x"]), num(s["y"])
        if not home:  # la trasferta attacca verso sinistra
            x, y = 120 - x, 80 - y
        r = 0.8 + 4 * num(s["xg"]) ** 0.5
        c = COL[0 if home else 1]
        goal = s["gol"] == "1"
        tip = f'{s["minuto"]}\' {s["giocatore"]} – xG {f(s["xg"])} – {ESITI.get(s["esito"], s["esito"])}'
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{c if goal else "none"}" '
                   f'fill-opacity="{0.9 if goal else 0}" stroke="{c}" stroke-width="0.5"><title>{e(tip)}</title></circle>')
    return pitch("".join(out))


def xg_timeline(shots, teams):
    W, H, pad = 600, 260, 28
    end = max([90] + [int(s["minuto"]) + 1 for s in shots])
    tot = {t: 0.0 for t in teams}
    series = {t: [(0, 0.0)] for t in teams}
    goals = []
    for s in shots:
        t = s["squadra"]
        if t not in tot:
            continue
        m = int(s["minuto"]) + int(s["secondo"]) / 60
        series[t].append((m, tot[t]))
        tot[t] += num(s["xg"])
        series[t].append((m, tot[t]))
        if s["gol"] == "1":
            goals.append((t, m, tot[t], s["giocatore"]))
    ymax = max(1.0, *tot.values()) * 1.1
    X = lambda m: pad + (W - 2 * pad) * m / end
    Y = lambda v: H - pad - (H - 2 * pad) * v / ymax
    svg = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    for m in range(0, end + 1, 15):
        svg.append(f'<line x1="{X(m):.1f}" y1="{pad}" x2="{X(m):.1f}" y2="{H - pad}" stroke="var(--line)"/>'
                   f'<text x="{X(m):.1f}" y="{H - 10}" font-size="10" fill="var(--mute)" text-anchor="middle">{m}\'</text>')
    for v in (0, ymax / 2, ymax / 1.1):
        svg.append(f'<text x="{pad - 4}" y="{Y(v) + 3:.1f}" font-size="10" fill="var(--mute)" text-anchor="end">{v:.1f}</text>')
    for i, t in enumerate(teams):
        pts = series[t] + [(end, tot[t])]
        d = " ".join(f"{X(m):.1f},{Y(v):.1f}" for m, v in pts)
        svg.append(f'<polyline points="{d}" fill="none" stroke="{COL[i]}" stroke-width="2"/>')
    for t, m, v, who in goals:
        c = COL[teams.index(t)]
        svg.append(f'<circle cx="{X(m):.1f}" cy="{Y(v):.1f}" r="4.5" fill="{c}" stroke="var(--card)" stroke-width="1.5">'
                   f'<title>{e(who)} {int(m)}\'</title></circle>')
    svg.append(f'<text x="{W - 4}" y="{H - 2}" font-size="9" fill="var(--mute)" text-anchor="end" opacity="0.8">© Delta Scout</text></svg>')
    return "".join(svg)


def first_sub(K, team):
    m = [int(k["minuto"]) for k in K if k["squadra"] == team and k["tipo"] in ("Sostituzione", "Rosso", "Secondo giallo")]
    return min(m) if m else None


def network_window(PS, info, t0, t1, min_pass):
    pos = defaultdict(lambda: [0.0, 0.0, 0])
    cnt = defaultdict(int)
    for q in PS:
        if q[0] not in info or not (t0 <= q[7] < t1):
            continue
        a = pos[q[0]]
        a[0] += q[2]; a[1] += q[3]; a[2] += 1
        if q[6] and q[1] in info:
            b = pos[q[1]]
            b[0] += q[4]; b[1] += q[5]; b[2] += 1
            cnt[(q[0], q[1])] += 1
    pts = {pid: (v[0] / v[2], v[1] / v[2]) for pid, v in pos.items() if v[2] >= 3}
    es = [(x, y, c) for (x, y), c in cnt.items() if c >= min_pass and x in pts and y in pts]
    return pts, es


def network_windows(PS, players, team, K, color):
    """Rete di passaggi per ogni finestra tra un cambio e l'altro (o espulsione) + rete di tutta la partita."""
    info = {int(p["player_id"]): p for p in players if p["squadra"] == team}
    end = max([q[7] for q in PS] + [90]) + 1
    cuts = sorted({int(k["minuto"]) for k in K if k["squadra"] == team and k["tipo"] in ("Sostituzione", "Rosso", "Secondo giallo")})
    bounds = [0]
    for c in cuts:  # cambi a pochi minuti di distanza diventano un'unica finestra
        if c - bounds[-1] >= 5 and end - c >= 5:
            bounds.append(c)
    bounds.append(end)
    wins = [("tutta", "Tutta la partita", 0, end, 3,
             "Tutta la partita: titolari e subentrati insieme, quindi chi ha giocato nella stessa zona può sovrapporsi.")]
    for i in range(len(bounds) - 1):
        t0, t1 = bounds[i], bounds[i + 1]
        label = f"{t0}'–{t1 - 1}'" if i < len(bounds) - 2 else f"{t0}'–fine"
        note = ("Fino al primo cambio: gli 11 di partenza." if i == 0 and len(bounds) > 2 else
                "Nessun cambio: rete unica." if len(bounds) == 2 else f"Dal cambio del {t0}' al successivo.")
        wins.append((f"w{i}", label, t0, t1, 2, note))
    if len(bounds) == 2:
        wins = wins[:1]
    btns, panes = [], []
    for j, (wid, label, t0, t1, mp, note) in enumerate(wins):
        pts, es = network_window(PS, info, t0, t1, mp)
        body = render_network(pts, es, info, color, note) if es else f'<p class="sub">{e(note)} Pochi passaggi in questa finestra.</p>'
        btns.append(f'<button data-v="{wid}" class="{"on" if j == 0 else ""}">{e(label)}</button>')
        panes.append(f'<div data-w="{wid}"{"" if j == 0 else " hidden"}>{body}</div>')
    return f'<div class="nw"><div class="flt"><span>Periodo</span>{"".join(btns)}</div>{"".join(panes)}</div>'


NET_JS = """<script>document.querySelectorAll('.nw').forEach(function(n){n.querySelectorAll('.flt button').forEach(function(b){b.onclick=function(){
n.querySelectorAll('.flt button').forEach(function(x){x.classList.toggle('on',x===b)});
n.querySelectorAll('[data-w]').forEach(function(p){p.hidden=p.dataset.w!==b.dataset.v})}})})</script>"""


def render_network(pts, es, info, color, note):
    mx = max(c for _, _, c in es)
    vol = defaultdict(int)
    for a, b, c in es:
        vol[a] += c
        vol[b] += c
    vmax = max(vol.values())
    out = []
    for a, b, c in sorted(es, key=lambda x: x[2]):
        k = c / mx
        out.append(f'<line x1="{pts[a][0]:.1f}" y1="{pts[a][1]:.1f}" x2="{pts[b][0]:.1f}" y2="{pts[b][1]:.1f}" '
                   f'stroke="{color}" stroke-opacity="{0.15 + 0.6 * k:.2f}" stroke-width="{0.3 + 1.6 * k:.2f}">'
                   f'<title>{e(short(info[a]))} → {e(short(info[b]))}: {c}</title></line>')
    shown = []
    for pid in sorted(vol, key=lambda x: -vol[x]):
        p = info[pid]
        r = 2.3 + 1.9 * vol[pid] / vmax
        label = p["maglia"] or initials(pitch_name(p))
        shown.append((p, label, pid))
        x, y = pts[pid]
        out.append(f'<g><title>{e(short(p))}</title><circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{color}" '
                   f'stroke="var(--card)" stroke-width="0.4"/><text x="{x:.1f}" y="{y + 0.9:.1f}" font-size="{2.6 if p["maglia"] else 2}" '
                   f'fill="#fff" text-anchor="middle" font-weight="700">{e(label)}</text></g>')
    shown.sort(key=lambda x: (not x[0]["maglia"], int(x[0]["maglia"]) if x[0]["maglia"].isdigit() else 0, short(x[0])))
    legend = "".join(f'<li><b style="display:inline-block;min-width:22px;color:{color}">{e(lab)}</b>{e(short(p))}'
                     f'<span class="sub"> · {vol[pid]}</span></li>' for p, lab, pid in shown)
    return (f'<p class="sub" style="margin:0 0 6px">{e(note)}</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start"><div style="flex:3 1 420px">{pitch("".join(out))}</div>'
            f'<ul style="flex:1 1 200px;list-style:none;padding:0;margin:0;font-size:13px;line-height:1.75">{legend}</ul></div>')


def pass_network(players, edges, color):
    pos = {p["player_id"]: p for p in players if p["pos_media_x"]}
    es = [x for x in edges if x["passatore_id"] in pos and x["ricevente_id"] in pos and int(x["passaggi"]) >= 3]
    if not es:
        return '<p class="sub">Dati insufficienti.</p>'
    mx = max(int(x["passaggi"]) for x in es)
    vol = defaultdict(int)
    for x in es:
        vol[x["passatore_id"]] += int(x["passaggi"])
        vol[x["ricevente_id"]] += int(x["passaggi"])
    vmax = max(vol.values())
    out = []
    for x in sorted(es, key=lambda x: int(x["passaggi"])):
        a, b = pos[x["passatore_id"]], pos[x["ricevente_id"]]
        k = int(x["passaggi"]) / mx
        out.append(f'<line x1="{a["pos_media_x"]}" y1="{a["pos_media_y"]}" x2="{b["pos_media_x"]}" y2="{b["pos_media_y"]}" '
                   f'stroke="{color}" stroke-opacity="{0.15 + 0.6 * k:.2f}" stroke-width="{0.3 + 1.6 * k:.2f}">'
                   f'<title>{e(short(a))} → {e(short(b))}: {x["passaggi"]}</title></line>')
    shown = []
    for pid, p in sorted(pos.items(), key=lambda kv: -vol.get(kv[0], 0)):  # i cerchi piccoli sopra quelli grandi
        if pid not in vol:
            continue
        r = 2.3 + 1.9 * vol[pid] / vmax
        label = p["maglia"] or initials(pitch_name(p))
        shown.append((p, label))
        out.append(f'<g><title>{e(short(p))}</title><circle cx="{p["pos_media_x"]}" cy="{p["pos_media_y"]}" r="{r:.2f}" fill="{color}" '
                   f'stroke="var(--card)" stroke-width="0.4"/>'
                   f'<text x="{p["pos_media_x"]}" y="{num(p["pos_media_y"]) + 0.9:.1f}" font-size="{2.6 if p["maglia"] else 2}" fill="#fff" '
                   f'text-anchor="middle" font-weight="700">{e(label)}</text></g>')
    # legenda numero -> giocatore, in ordine crescente di numero di maglia
    shown.sort(key=lambda x: (not x[0]["maglia"], int(x[0]["maglia"]) if x[0]["maglia"].isdigit() else 0, short(x[0])))
    legend = "".join(f'<li><b style="display:inline-block;min-width:22px;color:{color}">{e(lab)}</b>{e(short(p))}'
                     f'<span class="sub"> · {vol[p["player_id"]]}</span></li>' for p, lab in shown)
    return (f'<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start"><div style="flex:3 1 420px">{pitch("".join(out))}</div>'
            f'<ul style="flex:1 1 200px;list-style:none;padding:0;margin:0;font-size:13px;line-height:1.75">{legend}</ul></div>')


CARRY_CLS = [("bassa", "#aab3bd", 0.5), ("media", "#f2a900", 0.75), ("alta", "#d6336c", 1.05)]


def carry_class(c):
    x = num(c["xt"])
    if x >= 0.03 or c["in_area"] == "1":
        return 2
    return 1 if x >= 0.01 else 0


ESITO_G = {"gol": "tiro", "tiro": "tiro", "palla persa": "persa", "fallo subito": "altro", "possesso mantenuto": "altro"}


def carry_map(C, team, color, players, ti):
    cs = [c for c in C if c["squadra"] == team]
    if not cs:
        return '<p class="sub">Nessuna conduzione significativa.</p>'
    info = {p["player_id"]: p for p in players}
    lab = lambda pid: (info.get(pid, {}).get("maglia") or initials(pitch_name(info[pid]))) if pid in info else "?"
    defs = "<defs>" + "".join(f'<marker id="ar{ti}{k}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="3.2" markerHeight="3.2" '
                              f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
                              for k, (_, col, _) in enumerate(CARRY_CLS)) + "</defs>"
    out = [defs]
    for c in sorted(cs, key=lambda c: (carry_class(c), num(c["xt"]))):
        k = carry_class(c)
        name, col, w = CARRY_CLS[k]
        who = short(info[c["player_id"]]) if c["player_id"] in info else c["giocatore"]
        es = c.get("esito", "")
        extra = " · entra in area" if c["in_area"] == "1" else ""
        end = ""
        fx, fy = num(c["fine_x"]), num(c["fine_y"])
        if es == "gol":
            end = f'<text x="{fx + 1.2:.1f}" y="{fy - 1:.1f}" font-size="2.6">⚽</text>'
        elif es == "tiro":
            end = f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="1.5" fill="none" stroke="var(--ink)" stroke-width="0.35"/>'
        elif es == "palla persa":
            end = (f'<path d="M{fx + 1:.1f},{fy - 2:.1f} l1.6,1.6 m0,-1.6 l-1.6,1.6" stroke="#e03131" stroke-width="0.45"/>')
        out.append(f'<g data-pid="{c["player_id"]}" data-k="{k}" data-p="{c["periodo"]}" data-o="{ESITO_G.get(es, "altro")}">'
                   f'<title>{c["minuto"]}\' {e(who)} – {c["metri"]} m, xT +{f(c["xt"], 3)} (pericolosità {name}){extra}'
                   f'{f" – esito: {es}" if es else ""}</title>'
                   f'<line x1="{c["x"]}" y1="{c["y"]}" x2="{c["fine_x"]}" y2="{c["fine_y"]}" stroke="{col}" stroke-width="{w}" '
                   f'stroke-linecap="round" marker-end="url(#ar{ti}{k})"/>'
                   f'<circle cx="{c["x"]}" cy="{c["y"]}" r="1.75" fill="{col}" stroke="{color}" stroke-width="0.35"/>'
                   f'<text x="{c["x"]}" y="{num(c["y"]) + 0.65:.2f}" font-size="1.8" font-weight="700" text-anchor="middle" '
                   f'fill="#fff">{e(lab(c["player_id"]))}</text>{end}</g>')
    tot = defaultdict(lambda: [0, 0.0, 0.0, 0, 0, 0])
    for c in cs:
        t = tot[c["player_id"]]
        t[0] += 1; t[1] += num(c["metri"]); t[2] += num(c["xt"]); t[3] += carry_class(c) == 2
        t[4] += c.get("esito") in ("tiro", "gol"); t[5] += c.get("esito") == "palla persa"
    rows = "".join(
        f'<li data-pid="{pid}" style="cursor:pointer"><b style="display:inline-block;min-width:22px;color:{color}">{e(lab(pid))}</b>'
        f'{e(short(info[pid]) if pid in info else pid)} <span class="sub">· {t[0]} cond. · {t[1]:.0f} m · xT {t[2]:.2f}'
        f'{f" · <b style=color:#d6336c>{t[3]} pericolose</b>" if t[3] else ""}'
        f'{f" · {t[4]} finite in tiro" if t[4] else ""}{f" · {t[5]} perse" if t[5] else ""}</span></li>'
        for pid, t in sorted(tot.items(), key=lambda kv: -kv[1][2]))
    btn = lambda grp, val, txt, on=False: f'<button data-f="{grp}" data-v="{val}" class="{"on" if on else ""}">{txt}</button>'
    periods = sorted({c["periodo"] for c in cs})
    flt = ('<div class="flt"><span>Pericolosità</span>' + btn("k", "1", "media e alta", True) + btn("k", "0", "tutte")
           + '<span>Tempo</span>' + btn("p", "all", "tutta la partita", True)
           + "".join(btn("p", pp, {"1": "1° tempo", "2": "2° tempo", "3": "1° suppl.", "4": "2° suppl."}[pp]) for pp in periods)
           + '<span>Esito</span>' + btn("o", "all", "tutti", True) + btn("o", "tiro", "finite in tiro") + btn("o", "persa", "palla persa")
           + "</div>")
    return (f'<div class="cm">{flt}<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start"><div style="flex:3 1 420px">'
            f'{pitch("".join(out))}</div>'
            f'<div style="flex:1 1 220px"><p class="sub" style="margin:0 0 4px">Ordinati per xT · clicca un giocatore per isolarlo</p>'
            f'<ul style="list-style:none;padding:0;margin:0;font-size:13px;line-height:1.75">{rows}</ul></div></div></div>')


CARRY_JS = """<script>document.querySelectorAll('.cm').forEach(function(m){var st={k:'1',p:'all',o:'all',pid:null};
function apply(){m.querySelectorAll('g[data-pid]').forEach(function(g){var ok=(+g.dataset.k>=+st.k)&&(st.p==='all'||g.dataset.p===st.p)&&
(st.o==='all'||g.dataset.o===st.o);g.style.display=ok?'':'none';g.style.opacity=!st.pid||g.dataset.pid===st.pid?1:0.07});
m.querySelectorAll('li[data-pid]').forEach(function(x){x.style.fontWeight=x.dataset.pid===st.pid?'700':'';x.style.opacity=!st.pid||x.dataset.pid===st.pid?1:0.5})}
m.querySelectorAll('.flt button').forEach(function(b){b.onclick=function(){st[b.dataset.f]=b.dataset.v;
m.querySelectorAll('.flt button[data-f="'+b.dataset.f+'"]').forEach(function(x){x.classList.toggle('on',x===b)});apply()}});
m.querySelectorAll('li[data-pid]').forEach(function(li){li.onclick=function(){st.pid=st.pid===li.dataset.pid?null:li.dataset.pid;apply()}});apply()})</script>"""


PRESS_COL = {"tiro": "#d6336c", "gol": "#d6336c", "palla persa": "#aab3bd"}


def pressing_map(RG, team, color, players):
    rs = [r for r in RG if r["squadra"] == team]
    if not rs:
        return '<p class="sub">Nessun dato.</p>'
    info = {p["player_id"]: p for p in players}
    out = []
    for r in sorted(rs, key=lambda r: r["esito"] in ("tiro", "gol")):
        es = r["esito"]
        col = PRESS_COL.get(es, color)
        big = es in ("tiro", "gol")
        who = short(info[r["player_id"]]) if r["player_id"] in info else ""
        out.append(f'<circle cx="{r["x"]}" cy="{r["y"]}" r="{1.4 if big else 0.9}" fill="{col}" fill-opacity="{1 if big else 0.75}" '
                   f'stroke="var(--card)" stroke-width="0.2"><title>{r["minuto"]}\' {e(who)} – {e(r["tipo"])} – poi: {e(es)}</title></circle>')
        if es == "gol":
            out.append(f'<text x="{num(r["x"]) + 1.3:.1f}" y="{num(r["y"]) - 1:.1f}" font-size="2.6">⚽</text>')
    n = len(rs)
    half = sum(num(r["x"]) >= 60 for r in rs)
    high = sum(num(r["x"]) >= 80 for r in rs)
    shot = sum(r["esito"] in ("tiro", "gol") for r in rs)
    goal = sum(r["esito"] == "gol" for r in rs)
    thirds = [sum(lo <= num(r["x"]) < hi for r in rs) for lo, hi in ((0, 40), (40, 80), (80, 121))]
    bar = "".join(f'<div style="flex:{max(v, 0.5)};background:{color};opacity:{0.35 + 0.3 * i};color:#fff;text-align:center;font-size:11px">{v}</div>'
                  for i, v in enumerate(thirds))
    best = defaultdict(int)
    for r in rs:
        best[r["player_id"]] += 1
    tops = ", ".join(f'{e(short(info[pid]))} {c}' for pid, c in sorted(best.items(), key=lambda kv: -kv[1])[:3] if pid in info)
    return (f'{pitch("".join(out))}<div style="display:flex;border-radius:4px;overflow:hidden;margin-top:6px">{bar}</div>'
            f'<div class="sub" style="display:flex;justify-content:space-between;font-size:11px"><span>terzo difensivo</span>'
            f'<span>centrocampo</span><span>terzo offensivo</span></div>'
            f'<p style="margin:6px 0 0;font-size:13px"><b>{n}</b> palloni recuperati · <b>{100 * half / n:.0f}%</b> nella metà avversaria · '
            f'<b>{high}</b> nel terzo offensivo · <b style="color:#d6336c">{shot}</b> portano a un tiro entro 10"{f" ({goal} gol)" if goal else ""}'
            f'<br><span class="sub">Più recuperi: {tops}</span></p>')


INDIV_JS = """<script>(function(){var D=JSON.parse(document.getElementById('indiv-data').textContent);
var sel=document.getElementById('indiv-p'),box=document.getElementById('indiv-map'),info=document.getElementById('indiv-info'),view='p';
D.players.forEach(function(pl,i){var o=document.createElement('option');o.value=i;o.textContent=pl[1]+' – '+pl[2];sel.appendChild(o)});
document.querySelectorAll('#indiv-tabs button').forEach(function(b){b.onclick=function(){view=b.dataset.v;
document.querySelectorAll('#indiv-tabs button').forEach(function(x){x.classList.toggle('on',x===b)});draw()}});
var best=0,bn=-1;D.players.forEach(function(pl,i){var k=D.passes.filter(function(p){return p[0]===pl[0]}).length;if(k>bn){bn=k;best=i}});
sel.value=best;sel.onchange=draw;
function L(x1,y1,x2,y2,c,w,o,d){return '<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'" stroke="'+c+'" stroke-width="'+w+'" stroke-opacity="'+o+'"'+(d?' stroke-dasharray="'+d+'"':'')+'/>'}
function C(x,y,r,c,o){return '<circle cx="'+x+'" cy="'+y+'" r="'+r+'" fill="'+c+'" fill-opacity="'+(o||1)+'"/>'}
function draw(){var pl=D.players[+sel.value],id=pl[0],col=D.col[pl[3]],g='',t;
if(view==='p'){var ps=D.passes.filter(function(p){return p[0]===id}),ok=0,kp=0,pr=0,ar=0;
ps.forEach(function(p){var key=p[8]&1,gold='#f2a900';if(p[6]){ok++;}if(key)kp++;if(p[8]&4)pr++;if(p[8]&16)ar++;
g+=p[6]?L(p[2],p[3],p[4],p[5],key?gold:col,key?0.7:0.4,key?1:0.75)+C(p[4],p[5],key?0.9:0.55,key?gold:col):
L(p[2],p[3],p[4],p[5],'#9aa3ad',0.35,0.6,'0.8 0.6')+C(p[4],p[5],0.45,'#9aa3ad',0.7)});
t='<b>'+ps.length+'</b> passaggi · <b>'+ok+'</b> riusciti ('+(ps.length?Math.round(100*ok/ps.length):0)+'%) · <b>'+pr+'</b> progressivi · <b>'+ar+'</b> in area · <span style="color:#f2a900"><b>'+kp+'</b> chiave</span> · <span style="color:#9aa3ad">grigio = sbagliati</span>'}
else if(view==='r'){var rs=D.passes.filter(function(p){return p[1]===id&&p[6]}),f3=0,ar2=0;
rs.forEach(function(p){if(p[4]>=80)f3++;if(p[4]>=102&&p[5]>=18&&p[5]<=62)ar2++;g+=L(p[2],p[3],p[4],p[5],col,0.25,0.18)+C(p[4],p[5],0.9,col,0.75)});
t='<b>'+rs.length+'</b> palloni ricevuti su passaggio · <b>'+f3+'</b> nel terzo finale · <b>'+ar2+'</b> in area · linee chiare = da dove arrivava il passaggio'}
else{var cs=D.carries.filter(function(c){return c[0]===id}),m=0,x=0;
cs.forEach(function(c){m+=c[5];x+=c[6];g+=L(c[1],c[2],c[3],c[4],col,c[7]?0.8:0.5,0.85,'1.2 0.6')+C(c[3],c[4],c[7]?0.8:0.55,col)});
t='<b>'+cs.length+'</b> conduzioni significative (progressive, nel terzo finale o in area) · <b>'+Math.round(m)+'</b> m · xT <b>'+x.toFixed(2)+'</b>'}
box.querySelector('.ind').innerHTML=g;info.innerHTML=t;document.getElementById('indiv-leg').innerHTML=D.legs[view].split('@C').join(col)}
draw()})()</script>"""


def individual_maps(P, PS, C, teams):
    players = [p for p in sorted(P, key=lambda p: (teams.index(p["squadra"]) if p["squadra"] in teams else 2,
                                                       p["titolare"] != "1", -num(p["minuti"])))]
    idx = {t: i for i, t in enumerate(teams)}
    legs = {"p": leg((sw_line("@C", 2, "", 1, True), "passaggio riuscito"), (sw_line("#9aa3ad", 1.5, "2 1.5", 0.8, True), "sbagliato"),
                     (sw_line("#f2a900", 2.5, "", 1, True), "passaggio chiave / assist")),
            "r": leg((sw_dot("@C"), "punto di ricezione"), (sw_line("@C", 1, "", 0.3), "da dove arrivava il passaggio")),
            "c": leg((sw_line("@C", 1.5, "3 2", 1, True), "conduzione"), (sw_line("@C", 2.6, "3 2", 1, True), "entra in area"))}
    data = {"col": list(COL), "legs": legs,
            "players": [[int(p["player_id"]), short(p), p["squadra"], idx.get(p["squadra"], 0)] for p in players],
            "passes": PS,
            "carries": [[int(c["player_id"]), num(c["x"]), num(c["y"]), num(c["fine_x"]), num(c["fine_y"]), num(c["metri"]),
                         num(c["xt"]), int(c["in_area"])] for c in C]}
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tabs = ('<div class="tabs" id="indiv-tabs"><button class="on" data-v="p">Passing map</button>'
            '<button data-v="r">Palloni ricevuti</button><button data-v="c">Conduzioni</button></div>')
    svg = pitch('<g class="ind"></g>')
    return (f'<div class="f" style="margin-bottom:10px"><label class="sub">Giocatore <select id="indiv-p" style="font:inherit;padding:4px 8px;'
            f'border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink)"></select></label></div>{tabs}'
            f'<div id="indiv-map">{svg}</div><div id="indiv-leg"></div><p class="sub" id="indiv-info" style="margin-top:6px"></p>'
            f'<div class="legend">Il giocatore attacca sempre verso destra. Passa da un giocatore all\'altro con il menu.</div>'
            f'<script type="application/json" id="indiv-data">{js}</script>{INDIV_JS}')


def mini_heat(spec, color):
    if not spec:
        return ""
    vals = [int(v) for v in spec.split(";")]
    mx = max(vals) or 1
    cells = "".join(f'<rect x="{(i % 6) * 8}" y="{(i // 6) * 8}" width="8" height="8" fill="{color}" fill-opacity="{0.05 + 0.9 * v / mx:.2f}"/>'
                    for i, v in enumerate(vals))
    return (f'<svg viewBox="0 0 48 32" width="48" height="32" style="display:inline-block;vertical-align:middle">'
            f'<rect width="48" height="32" fill="var(--pitch)"/>{cells}</svg>')


def sw(inner, w=22):
    return f'<svg viewBox="0 0 {w} 12" width="{w}" height="12">{inner}</svg>'


def sw_dot(c, filled=True, r=4.5):
    return sw(f'<circle cx="11" cy="6" r="{r}" fill="{c if filled else "none"}" stroke="{c}" stroke-width="1.3"/>')


def sw_line(c, w=2, dash="", op=1, end=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return sw(f'<line x1="1" y1="6" x2="{17 if end else 21}" y2="6" stroke="{c}" stroke-width="{w}" stroke-opacity="{op}"{d}/>'
              + (f'<circle cx="18.5" cy="6" r="2.4" fill="{c}"/>' if end else ""))


def sw_rect(c, op=1):
    return sw(f'<rect x="5" y="1" width="12" height="10" rx="1.5" fill="{c}" fill-opacity="{op}"/>')


def sw_grad(c):
    return sw("".join(f'<rect x="{i * 10}" y="1" width="10" height="10" fill="{c}" fill-opacity="{0.08 + 0.2 * i:.2f}"/>'
                      for i in range(5)), 50)


def leg(*items):
    return '<div class="lg">' + "".join(f"<span>{a}{b}</span>" for a, b in items) + "</div>"


def heat_pitch(spec, color):
    if not spec:
        return ""
    vals = [int(v) for v in spec.split(";")]
    mx = max(vals) or 1
    cells = "".join(f'<rect x="{(i % 6) * 20}" y="{(i // 6) * 20}" width="20" height="20" fill="{color}" '
                    f'fill-opacity="{0.85 * v / mx:.2f}"><title>{v}</title></rect>' for i, v in enumerate(vals))
    return pitch(cells)


def momentum_chart(T, teams):
    series = [[int(v) for v in (T[t].get("momentum_5min") or "").split(";") if v != ""] for t in teams]
    n = max(len(x) for x in series)
    if not n:
        return '<p class="sub">Dati non disponibili.</p>'
    W, H, pad = 600, 180, 24
    mx = max(max(x, default=0) for x in series) or 1
    bw = (W - 2 * pad) / n
    mid = H / 2
    out = [f'<svg viewBox="0 0 {W} {H}" role="img"><line x1="{pad}" y1="{mid}" x2="{W - pad}" y2="{mid}" stroke="var(--line)"/>']
    for i in range(n):
        a = series[0][i] if i < len(series[0]) else 0
        b = series[1][i] if i < len(series[1]) else 0
        x = pad + i * bw
        ha, hb = (mid - pad) * a / mx, (mid - pad) * b / mx
        out.append(f'<rect x="{x + 1:.1f}" y="{mid - ha:.1f}" width="{bw - 2:.1f}" height="{ha:.1f}" fill="{COL[0]}">'
                   f'<title>{i * 5}-{i * 5 + 5}\' {e(teams[0])}: {a}</title></rect>'
                   f'<rect x="{x + 1:.1f}" y="{mid:.1f}" width="{bw - 2:.1f}" height="{hb:.1f}" fill="{COL[1]}">'
                   f'<title>{i * 5}-{i * 5 + 5}\' {e(teams[1])}: {b}</title></rect>')
        if i % 3 == 0:
            out.append(f'<text x="{x:.1f}" y="{H - 4}" font-size="10" fill="var(--mute)">{i * 5}\'</text>')
    out.append(f'<text x="{W - 4}" y="{H - 2}" font-size="9" fill="var(--mute)" text-anchor="end" opacity="0.8">© Delta Scout</text></svg>')
    return "".join(out)


SET_PIECE = {"From Corner", "From Free Kick", "From Throw In"}


def situation(s):
    if s["tipo"] == "Penalty":
        return "Rigori"
    if s["tipo"] in ("Free Kick", "Corner") or s["azione"] in SET_PIECE:
        return "Palla inattiva"
    if s["azione"] == "From Counter":
        return "Contropiede"
    return "Azione manovrata"


def shot_breakdown(S, teams):
    groups_ = [("Situazione", situation, ["Azione manovrata", "Contropiede", "Palla inattiva", "Rigori"]),
               ("Parte del corpo", lambda s: {"Right Foot": "Destro", "Left Foot": "Sinistro", "Head": "Testa"}.get(s["parte_corpo"], "Altro"),
                ["Destro", "Sinistro", "Testa", "Altro"])]
    html_ = []
    for title, fn, cats in groups_:
        head = f"<tr><th>{title}</th>" + "".join(f'<th colspan="3" style="color:{COL[i]}">{e(t)}</th>' for i, t in enumerate(teams)) + "</tr>"
        head += "<tr><th></th>" + "<th>Tiri</th><th>Gol</th><th>xG</th>" * 2 + "</tr>"
        rows = []
        for c in cats:
            cells = []
            for t in teams:
                ss = [s for s in S if s["squadra"] == t and fn(s) == c]
                cells.append(f'<td>{len(ss)}</td><td>{sum(int(s["gol"]) for s in ss)}</td><td>{sum(num(s["xg"]) for s in ss):.2f}</td>')
            if any(s for s in S if fn(s) == c):
                rows.append(f"<tr><td>{c}</td>{''.join(cells)}</tr>")
        html_.append(f'<table class="st">{head}{"".join(rows)}</table>')
    return '<div class="grid2">' + "".join(html_) + "</div>"


ESITI = {"Goal": "Gol", "Saved": "Parato", "Saved To Post": "Parato (palo)", "Off T": "Fuori", "Post": "Palo",
         "Blocked": "Murato", "Wayward": "Fuori di molto", "Saved Off Target": "Parato fuori"}


def shot_table(S, teams):
    rows = []
    for s in S:
        c = COL[teams.index(s["squadra"])] if s["squadra"] in teams else "inherit"
        g = ' style="font-weight:600"' if s["gol"] == "1" else ""
        rows.append(f'<tr{g}><td><span class="dot" style="background:{c}"></span>{s["minuto"]}\'</td><td style="text-align:left">{e(s["giocatore"])}</td>'
                    f'<td>{f(s["xg"])}</td><td style="text-align:left">{ESITI.get(s["esito"], e(s["esito"]))}</td><td>{f(s["distanza_porta"], 1)}</td>'
                    f'<td style="text-align:left">{e(CORPO.get(s["parte_corpo"], s["parte_corpo"]))}</td><td style="text-align:left">{e(situation(s))}</td>'
                    f'<td>{s["difensori_nel_triangolo"]}</td><td>{"sì" if s["sotto_pressione"] == "1" else ""}</td>'
                    f'<td>{"sì" if s["primo_tocco"] == "1" else ""}</td><td style="text-align:left">{e(s["assistman"])}</td></tr>')
    head = ("<tr><th>Min</th><th>Giocatore</th><th>xG</th><th>Esito</th><th>Dist. (yd)</th><th>Corpo</th><th>Situazione</th>"
            "<th>Difensori davanti</th><th>Pressato</th><th>Al volo</th><th>Assist da</th></tr>")
    return f'<div class="scroll"><table class="pl">{head}{"".join(rows)}</table></div>'


ICON = {"Gol": "⚽", "Gol su rigore": "⚽ (R)", "Autogol": "⚽ (AG)", "Giallo": "🟨", "Secondo giallo": "🟨🟥", "Rosso": "🟥",
        "Sostituzione": "🔁", "Cambio modulo": "📐"}


def it_detail(d):
    for a, b in MOTIVI.items():
        d = d.replace(a, b)
    return d


def timeline(K, teams):
    if not K:
        return '<p class="sub">Nessun evento.</p>'
    rows = []
    for k in K:
        c = COL[teams.index(k["squadra"])] if k["squadra"] in teams else "inherit"
        who = e(k["giocatore"])
        rows.append(f'<tr><td class="m">{k["minuto"]}\'</td><td>{ICON.get(k["tipo"], "")} <span class="dot" style="background:{c}"></span>'
                    f'<b>{e(k["tipo"])}</b> {who} <span class="sub">{e(it_detail(k["dettaglio"]))}</span></td></tr>')
    return f'<table class="tl">{"".join(rows)}</table>'


def combos(E, players, t, color):
    names = {p["player_id"]: short(p) for p in players}
    es = sorted([x for x in E if x["squadra"] == t], key=lambda x: -int(x["passaggi"]))[:6]
    items = "".join(f'<li>{e(names.get(x["passatore_id"], x["passatore"]))} → {e(names.get(x["ricevente_id"], x["ricevente"]))}: '
                    f'<b>{x["passaggi"]}</b></li>' for x in es)
    return f'<h3><span class="dot" style="background:{color}"></span>{e(t)}</h3><ul>{items}</ul>'


def g(p, k, d=None):
    v = p.get(k, "")
    return f(v, d) if d is not None else (v if v not in (None, "") else "–")


def rv(p, a, b):
    return f'{g(p, a)}/{g(p, b)}'


PLAYER_TABS = {
    "Attacco": [("Voto", lambda p: voto_badge(p.get("voto"))), ("Min", lambda p: f(p["minuti"], 0)), ("Gol", lambda p: g(p, "gol")), ("Ass", lambda p: g(p, "assist")),
                ("xG", lambda p: g(p, "xg", 2)), ("npxG", lambda p: g(p, "npxg", 2)), ("xA", lambda p: g(p, "xa", 2)),
                ("xT", lambda p: g(p, "xt", 2)), ("xG chain", lambda p: g(p, "xg_chain", 2)), ("SCA", lambda p: g(p, "sca")), ("GCA", lambda p: g(p, "gca")),
                ("Tiri (porta)", lambda p: f'{g(p, "tiri")} ({g(p, "tiri_in_porta")})'), ("Tocchi area", lambda p: g(p, "tocchi_in_area")),
                ("Dribbling", lambda p: rv(p, "dribbling_riusciti", "dribbling")), ("P. chiave", lambda p: g(p, "passaggi_chiave"))],
    "Passaggi": [("Pass", lambda p: rv(p, "passaggi_riusciti", "passaggi")), ("%", lambda p: g(p, "precisione_passaggi_pct", 0)),
                 ("Lungh. media m", lambda p: g(p, "lunghezza_media_passaggi_m", 1)), ("Avanti", lambda p: g(p, "passaggi_avanti")),
                 ("Indietro", lambda p: g(p, "passaggi_indietro")), ("Progressivi", lambda p: g(p, "passaggi_progressivi")),
                 ("Terzo finale", lambda p: g(p, "passaggi_terzo_finale")), ("In area", lambda p: g(p, "passaggi_in_area")),
                 ("Chiave", lambda p: g(p, "passaggi_chiave")), ("Filtranti", lambda p: g(p, "filtranti")),
                 ("Cambi gioco", lambda p: g(p, "cambi_gioco")), ("Lanci lunghi", lambda p: rv(p, "lanci_lunghi_riusciti", "lanci_lunghi")),
                 ("Cross", lambda p: rv(p, "cross_riusciti", "cross")),
                 ("Sotto pressione", lambda p: rv(p, "passaggi_sotto_pressione_riusciti", "passaggi_sotto_pressione"))],
    "Possesso": [("xT passaggi", lambda p: g(p, "xt_passaggi", 2)), ("xT conduzioni", lambda p: g(p, "xt_conduzioni", 2)),
                 ("Azioni con palla", lambda p: g(p, "azioni_con_palla")), ("Ricezioni", lambda p: g(p, "ricezioni")),
                 ("Ric. terzo finale", lambda p: g(p, "ricezioni_terzo_finale")), ("Cond. progr.", lambda p: g(p, "conduzioni_progressive")),
                 ("Cond. terzo finale", lambda p: g(p, "conduzioni_terzo_finale")), ("Cond. in area", lambda p: g(p, "conduzioni_in_area")),
                 ("Metri progr.", lambda p: g(p, "metri_progressivi", 0)), ("Palle perse", lambda p: g(p, "palle_perse")),
                 ("Falli subiti", lambda p: g(p, "falli_subiti")), ("360 avv. 5m", lambda p: g(p, "avversari_5m_medi_360", 2)),
                 ("360 pressato %", lambda p: g(p, "azioni_pressate_360_pct", 0))],
    "Difesa": [("Pressioni", lambda p: g(p, "pressioni")), ("Pr. alte", lambda p: g(p, "pressioni_alte")),
               ("Contropr.", lambda p: g(p, "contropressioni")), ("Contrasti", lambda p: rv(p, "contrasti_vinti", "contrasti")),
               ("Intercetti", lambda p: g(p, "intercetti")), ("Recuperi", lambda p: g(p, "recuperi")),
               ("Rec. alti", lambda p: g(p, "recuperi_alti")), ("Respinte", lambda p: g(p, "respinte")), ("Blocchi", lambda p: g(p, "blocchi")),
               ("Aerei", lambda p: f'{g(p, "aerei_vinti")}/{num(p.get("aerei_vinti")) + num(p.get("aerei_persi")):.0f}'),
               ("Contese vinte", lambda p: g(p, "contese_vinte")), ("Saltato", lambda p: g(p, "saltato_da_avversario")),
               ("Falli", lambda p: g(p, "falli_commessi"))],
    "Profilo": [("Età", lambda p: age(p, p["data"]) or "–"), ("Nato il", lambda p: ANAG.get(p["player_id"], {}).get("data_nascita") or "–"),
                ("Altezza", lambda p: ANAG.get(p["player_id"], {}).get("altezza_cm") or "–"),
                ("Nazionalità", lambda p: e(p.get("nazionalita") or "–")),
                ("Ruolo abituale", lambda p: e(REEP_IT.get((ANAG.get(p["player_id"], {}).get("ruolo") or "").lower(), ANAG.get(p["player_id"], {}).get("ruolo")) or "–")),
                ("Link", lambda p: links(p))],
    "Rispetto alla carriera": [(lab, (lambda k: lambda p: ctx_cell(p, k))(k)) for k, lab in CTX],
    "Portiere": [("Min", lambda p: f(p["minuti"], 0)), ("Parate", lambda p: g(p, "parate")), ("Gol subiti", lambda p: g(p, "gol_subiti_portiere")),
                 ("Uscite", lambda p: g(p, "uscite")), ("Prese alte", lambda p: g(p, "prese_alte")), ("Pugni", lambda p: g(p, "respinte_di_pugno")),
                 ("Pass", lambda p: rv(p, "passaggi_riusciti", "passaggi")), ("%", lambda p: g(p, "precisione_passaggi_pct", 0)),
                 ("Lungh. media m", lambda p: g(p, "lunghezza_media_passaggi_m", 1)),
                 ("Lanci lunghi", lambda p: rv(p, "lanci_lunghi_riusciti", "lanci_lunghi"))],
}

def links(p):
    a = ANAG.get(p["player_id"], {})
    out = [f'<a href="{e(a[k])}" target="_blank" rel="noopener">{lab}</a>' for k, lab in
           (("transfermarkt", "Transfermarkt"), ("fbref", "FBref"), ("wikidata", "Wikidata")) if a.get(k)]
    return " · ".join(out) or "–"


TAB_JS = """<script>document.querySelectorAll('.tabs').forEach(function(t){t.addEventListener('click',function(ev){
var b=ev.target.closest('button');if(!b)return;var box=t.parentNode;t.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b)});
box.querySelectorAll('[data-tab]').forEach(function(p){p.classList.toggle('hidden',p.dataset.tab!==b.dataset.tab)})})})</script>"""


def player_tabs(players, color):
    btn = "".join(f'<button class="{"on" if i == 0 else ""}" data-tab="{k}">{k}</button>' for i, k in enumerate(PLAYER_TABS))
    panes = []
    for i, (k, cols) in enumerate(PLAYER_TABS.items()):
        ps = [p for p in players if p["ruolo"] == "Goalkeeper"] if k == "Portiere" else players
        head = "<tr><th>Giocatore</th>" + ("<th>Ruolo</th>" if i == 0 else "") + "".join(f"<th>{c}</th>" for c, _ in cols) \
            + ("<th>Heatmap</th>" if i == 0 else "") + "</tr>"
        rows = []
        for p in ps:
            card = " 🟥" if p["rossi"] != "0" else " 🟨" if p["gialli"] != "0" else ""
            cls = "" if p["titolare"] == "1" else ' class="sub"'
            ag = age(p, p["data"])
            rows.append(f'<tr{cls}><td>{e(p["maglia"] or "")} {e(short(p))}{card}{f" <span class=sub>({ag})</span>" if ag else ""}</td>'
                        + (f'<td style="text-align:left">{e(it_role(p["ruolo"]))}</td>' if i == 0 else "")
                        + "".join(f"<td>{fn(p)}</td>" for _, fn in cols)
                        + (f"<td>{mini_heat(p['heatmap_6x4'], color)}</td>" if i == 0 else "") + "</tr>")
        panes.append(f'<div data-tab="{k}" class="scroll{"" if i == 0 else " hidden"}"><table class="pl">{head}{"".join(rows)}</table></div>')
    return f'<div><div class="tabs">{btn}</div>{"".join(panes)}</div>'


def top(players, key, n=1, minimum=0.0):
    ps = sorted(players, key=key, reverse=True)
    return [p for p in ps[:n] if key(p) > minimum]


def summary(T, P, teams):
    h, a = T[teams[0]], T[teams[1]]
    gh, ga, xh, xa = int(h["gol"]), int(a["gol"]), num(h["xg"]), num(a["xg"])
    out = []
    if gh != ga:
        w, l = (h, a) if gh > ga else (a, h)
        dx = num(w["xg"]) - num(l["xg"])
        if dx >= 0.5:
            out.append(f'<b>{e(w["squadra"])}</b> ha vinto in modo meritato: {f(w["xg"])} xG contro {f(l["xg"])}.')
        elif dx <= -0.5:
            out.append(f'<b>{e(w["squadra"])}</b> ha vinto nonostante gli xG ({f(w["xg"])} contro {f(l["xg"])}): '
                       f'decisivi cinismo e/o portiere, {e(l["squadra"])} avrebbe meritato di più.')
        else:
            out.append(f'Partita equilibrata negli xG ({f(xh)}–{f(xa)}), decisa dagli episodi a favore di <b>{e(w["squadra"])}</b>.')
    else:
        if abs(xh - xa) >= 0.8:
            b = h if xh > xa else a
            out.append(f'Pareggio che sta stretto a <b>{e(b["squadra"])}</b>, superiore negli xG ({f(xh)}–{f(xa)}).')
        else:
            out.append(f'Pareggio coerente con le occasioni create ({f(xh)}–{f(xa)} xG).')
    eh, ea = ELO.get((h["n"], h["squadra"])), ELO.get((a["n"], a["squadra"]))
    if eh and ea and int(eh["partite_storia"]) >= 10 and int(ea["partite_storia"]) >= 10:
        ph = num(eh["prob_vittoria_attesa"])
        fav, pf, und = (h, ph, a) if ph >= 50 else (a, 100 - ph, h)
        if pf >= 60:
            res = "ha rispettato il pronostico" if int(fav["gol"]) > int(und["gol"]) else \
                  "è stata fermata sul pari" if gh == ga else "<b>è stata battuta a sorpresa</b>"
            out.append(f'Secondo il rating Elo {e(fav["squadra"])} partiva favorita ({f(fav is h and eh["elo_pre"] or ea["elo_pre"], 0)} '
                       f'contro {f(fav is h and ea["elo_pre"] or eh["elo_pre"], 0)}, aspettativa {pf:.0f}%) e {res}.')
        else:
            out.append(f'Alla vigilia le due squadre erano vicine nel rating Elo ({f(eh["elo_pre"], 0)} contro {f(ea["elo_pre"], 0)}).')
    ctrl = h if num(h["field_tilt_pct"]) >= num(a["field_tilt_pct"]) else a
    pos = h if num(h["possesso_pct"]) >= num(a["possesso_pct"]) else a
    if ctrl is pos:
        out.append(f'{e(ctrl["squadra"])} ha controllato il gioco: {f(pos["possesso_pct"], 0)}% di possesso e '
                   f'{f(ctrl["field_tilt_pct"], 0)}% di field tilt (passaggi nel terzo offensivo).')
    else:
        out.append(f'{e(pos["squadra"])} ha avuto più palla ({f(pos["possesso_pct"], 0)}%), ma {e(ctrl["squadra"])} ha giocato '
                   f'di più nella trequarti avversaria (field tilt {f(ctrl["field_tilt_pct"], 0)}%).')
    pp = [(t, num(T[t]["ppda"])) for t in teams if T[t]["ppda"] not in ("", None)]
    if len(pp) == 2:
        (t1, v1), (t2, v2) = sorted(pp, key=lambda x: x[1])
        style = lambda v: "pressing alto e aggressivo" if v < 9 else "pressing medio" if v < 14 else "atteggiamento attendista"
        out.append(f'Pressing: {e(t1)} PPDA {f(v1, 1)} ({style(v1)}), {e(t2)} PPDA {f(v2, 1)} ({style(v2)}). '
                   f'Recuperi alti: {T[t1]["recuperi_alti"]} contro {T[t2]["recuperi_alti"]}.')
    q = [(t, num(T[t]["xg_per_tiro"]), int(T[t]["tiri"])) for t in teams]
    (tq, vq, nq), (to, vo, no) = sorted(q, key=lambda x: -x[1])
    if vq - vo >= 0.05:
        out.append(f'Qualità delle occasioni migliore per {e(tq)} ({f(vq)} xG a tiro su {nq} tiri) rispetto a {e(to)} '
                   f'({f(vo)} su {no}).')
    keys = []
    rated = [p for p in P if p.get("voto")]
    if rated:
        p = max(rated, key=lambda p: float(p["voto"]))
        keys.append(f'<b>Migliore in campo: {e(short(p))}</b> ({e(p["squadra"])}) con voto Delta Scout {voto_badge(p["voto"], "12px")}.')
    best_ctx = None
    for p in P:
        c = CAREER.get(p["player_id"])
        if not c or num(c["minuti"]) < 900:
            continue
        ups = [(lab, match_p90(p, k), num(c.get(f"{k}_p90"))) for k, lab in CTX]
        ups = [(lab, v, car) for lab, v, car in ups if v is not None and car > 0 and v >= 1.5 * car and v - car > 0.05]
        if len(ups) >= 3 and (best_ctx is None or len(ups) > len(best_ctx[1])):
            best_ctx = (p, ups)
    if best_ctx:
        p, ups = best_ctx
        det = ", ".join(f"{lab} {v:.2f} contro {car:.2f}" for lab, v, car in ups[:3])
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) molto sopra la sua media in carriera in {len(ups)} statistiche '
                    f'(per 90\': {det}).')
    att = top(P, lambda p: num(p["xg"]) + num(p["xa"]))
    if att:
        p = att[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) il più pericoloso: {f(p["xg"])} xG + {f(p["xa"])} xA'
                    + (f', {p["gol"]} gol' if p["gol"] != "0" else "") + (f', {p["assist"]} assist' if p["assist"] != "0" else "") + ".")
    prog = top(P, lambda p: num(p["metri_progressivi"]))
    if prog:
        p = prog[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) il motore della manovra: {f(p["metri_progressivi"], 0)} metri '
                    f'progressivi, {p["passaggi_progressivi"]} passaggi e {p["conduzioni_progressive"]} conduzioni progressive.')
    xtp = top(P, lambda p: num(p.get("xt")), minimum=0.05)
    if xtp:
        p = xtp[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) il più bravo a far avanzare la minaccia: {f(p["xt"])} xT '
                    f'({f(p.get("xt_passaggi"))} con i passaggi, {f(p.get("xt_conduzioni"))} con le conduzioni).')
    cre = top(P, lambda p: num(p["passaggi_chiave"]), minimum=1)
    if cre:
        p = cre[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) il più creativo: {p["passaggi_chiave"]} passaggi chiave.')
    dif = top(P, lambda p: num(p["contrasti_vinti"]) + num(p["intercetti"]) + num(p["recuperi"]))
    if dif:
        p = dif[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) il migliore in fase difensiva: {p["contrasti_vinti"]} contrasti vinti, '
                    f'{p["intercetti"]} intercetti, {p["recuperi"]} recuperi.')
    prs = top(P, lambda p: num(p["pressioni"]))
    if prs:
        p = prs[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) il più attivo nel pressing: {p["pressioni"]} pressioni '
                    f'({p["pressioni_alte"]} nella trequarti avversaria).')
    drb = top(P, lambda p: num(p["dribbling_riusciti"]), minimum=2)
    if drb:
        p = drb[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) il miglior dribblatore: {p["dribbling_riusciti"]}/{p["dribbling"]} riusciti.')
    gk = top(P, lambda p: num(p["parate"]), minimum=3)
    if gk:
        p = gk[0]
        keys.append(f'<b>{e(short(p))}</b> ({e(p["squadra"])}) decisivo tra i pali: {p["parate"]} parate.')
    return out, keys


ROLE_XY = {
    "Goalkeeper": (5, 40), "Right Back": (32, 70), "Right Center Back": (24, 55), "Center Back": (24, 40),
    "Left Center Back": (24, 25), "Left Back": (32, 10), "Right Wing Back": (48, 72), "Left Wing Back": (48, 8),
    "Right Defensive Midfield": (42, 52), "Center Defensive Midfield": (42, 40), "Left Defensive Midfield": (42, 28),
    "Right Midfield": (62, 72), "Right Center Midfield": (58, 54), "Center Midfield": (58, 40), "Left Center Midfield": (58, 26),
    "Left Midfield": (62, 8), "Right Wing": (84, 70), "Right Attacking Midfield": (78, 55), "Center Attacking Midfield": (78, 40),
    "Left Attacking Midfield": (78, 25), "Left Wing": (84, 10), "Right Center Forward": (98, 52), "Center Forward": (100, 40),
    "Left Center Forward": (98, 28), "Secondary Striker": (90, 40),
}


REPARTI = {"Portiere": "#c99a06", "Difensore": "#2f8f5b", "Centrocampista": "#7b5cd6", "Attaccante": "#e8590c"}


SIGLE = {
    "Goalkeeper": "GK", "Right Back": "RB", "Right Center Back": "RCB", "Center Back": "CB", "Left Center Back": "LCB",
    "Left Back": "LB", "Right Wing Back": "RWB", "Left Wing Back": "LWB", "Right Defensive Midfield": "RDM",
    "Center Defensive Midfield": "CDM", "Left Defensive Midfield": "LDM", "Right Midfield": "RM", "Right Center Midfield": "RCM",
    "Center Midfield": "CM", "Left Center Midfield": "LCM", "Left Midfield": "LM", "Right Wing": "RW",
    "Right Attacking Midfield": "RAM", "Center Attacking Midfield": "CAM", "Left Attacking Midfield": "LAM", "Left Wing": "LW",
    "Right Center Forward": "RCF", "Center Forward": "CF", "Left Center Forward": "LCF", "Secondary Striker": "SS",
}


def reparto(role):
    if role == "Goalkeeper":
        return "Portiere"
    if "Back" in role:
        return "Difensore"
    if "Midfield" in role:
        return "Centrocampista"
    return "Attaccante" if role else "Centrocampista"


def pitch_name(r):
    nick = r.get("soprannome")
    toks = (nick or r["giocatore"]).split()
    if nick and len(toks) > 1:
        return " ".join(toks[1:])
    return toks[-1] if toks else ""


def sub_events(K, team):
    """{nome uscito: (minuto, nome entrato, motivo)} dalla cronaca."""
    out = {}
    for k in K:
        if k["squadra"] == team and k["tipo"] == "Sostituzione":
            d = k["dettaglio"].removeprefix("entra ")
            motivo = ""
            if d.endswith(")") and " (" in d:
                d, motivo = d[:-1].rsplit(" (", 1)
            out[k["giocatore"]] = (k["minuto"], d, motivo)
    return out


def card_minutes(K, team):
    out = defaultdict(list)
    for k in K:
        if k["squadra"] == team and k["tipo"] in ("Giallo", "Secondo giallo", "Rosso"):
            out[k["giocatore"]].append((k["tipo"], k["minuto"]))
    return out


def goal_minutes(K, team):
    out = defaultdict(list)
    for k in K:
        if k["squadra"] == team and k["tipo"] in ("Gol", "Gol su rigore"):
            out[k["giocatore"]].append(k["minuto"] + ("' (R)" if k["tipo"] == "Gol su rigore" else "'"))
    return out


def spread(pts):
    """Porta le posizioni medie nella propria metà (10-49 x 11-69), mantenendo l'ordine, e separa i giocatori sovrapposti."""
    if not pts:
        return
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for p in pts:
        p[0] = 10 + 39 * (p[0] - x0) / (x1 - x0 or 1)
        p[1] = 11 + 58 * (p[1] - y0) / (y1 - y0 or 1)
    for _ in range(200):
        moved = False
        for a in range(len(pts)):
            for b in range(a + 1, len(pts)):
                dx, dy = pts[b][0] - pts[a][0], pts[b][1] - pts[a][1]
                d = math.hypot(dx / 2.1, dy)  # le etichette "Cognome, RUOLO" sono larghe
                if d < 11.5:
                    if d == 0:
                        dx, dy, d = 0.0, 1.0, 1.0
                    k = (11.5 - d) / 2 / d
                    pts[a][0] -= dx * k * 0.7; pts[a][1] -= dy * k
                    pts[b][0] += dx * k * 0.7; pts[b][1] += dy * k
                    moved = True
        for p in pts:
            p[0] = min(max(p[0], 9), 51)
            p[1] = min(max(p[1], 11), 69)  # simmetrico (la trasferta è ruotata) e con spazio sotto per nome e uscita
        if not moved:
            break


def lineups(T, P, R, K, teams):
    by_id = {p["player_id"]: p for p in P}
    marks = []
    for i, t in enumerate(teams):
        c = COL[i]
        subs = sub_events(K, t)
        cards = card_minutes(K, t)
        xi = [r for r in R if r["squadra"] == t and r["stato"] == "titolare"]
        pts = []
        for r in xi:
            p = by_id.get(r["player_id"], {})
            if p.get("pos_media_x"):
                pts.append([num(p["pos_media_x"]), num(p["pos_media_y"])])
            else:
                pts.append(list(ROLE_XY.get(r["ruolo_iniziale"], (60, 40))))
        spread(pts)
        for r, (x, y) in zip(xi, pts):
            p = by_id.get(r["player_id"], {})
            if i == 1:  # la trasferta occupa l'altra metà, ruotata di 180°
                x, y = 120 - x, 80 - y
            badges = []
            gl = int(num(p.get("gol")))
            if gl:
                badges.append(f'<text x="{x - 3.2:.1f}" y="{y - 2.0:.1f}" font-size="2.6" text-anchor="end">⚽{"" if gl == 1 else f"×{gl}"}</text>')
            if num(p.get("assist")):
                badges.append(f'<circle cx="{x - 3.6:.1f}" cy="{y + 1.0:.1f}" r="1.3" fill="var(--card)" stroke="{c}" stroke-width="0.3"/>'
                              f'<text x="{x - 3.6:.1f}" y="{y + 1.6:.1f}" font-size="1.7" text-anchor="middle" fill="{c}" font-weight="700">A</text>')
            if p.get("voto"):
                badges.append(f'<rect x="{x + 1.6:.1f}" y="{y - 4.6:.1f}" width="5" height="2.8" rx="0.6" fill="{voto_col(p["voto"])}"/>'
                              f'<text x="{x + 4.1:.1f}" y="{y - 2.55:.1f}" font-size="2" fill="#fff" font-weight="700" text-anchor="middle">'
                              f'{float(p["voto"]):.1f}</text>')
            cs = cards.get(r["giocatore"], [])
            if cs:
                col = "#d33" if any(t_ != "Giallo" for t_, _ in cs) else "#f2c200"
                badges.append(f'<rect x="{x + 2.4:.1f}" y="{y + 0.4:.1f}" width="1.5" height="2.1" rx="0.2" fill="{col}"/>')
            sub = subs.get(r["giocatore"])
            sigla = SIGLE.get(r["ruolo_iniziale"], "")
            name = e(pitch_name(r)) + (f', <tspan fill="var(--mute)" font-weight="600">{sigla}</tspan>' if sigla else "")
            sub_txt = (f'<text x="{x:.1f}" y="{y + 8.3:.1f}" font-size="2" fill="#d33" text-anchor="middle" '
                       f'stroke="var(--pitch)" stroke-width="0.5" paint-order="stroke">▼ {sub[0]}\'</text>') if sub else ""
            tip = f'{r["giocatore"]} – {it_role(r["ruolo_iniziale"])}' + (f' – xT {f(p.get("xt"))}, xG {f(p.get("xg"))}' if p else "")
            marks.append(
                f'<g><title>{e(tip)}</title><circle cx="{x:.1f}" cy="{y:.1f}" r="3.1" fill="{REPARTI[reparto(r["ruolo_iniziale"])]}" stroke="{c}" stroke-width="0.9"/>'
                f'<text x="{x:.1f}" y="{y + 1.1:.1f}" font-size="{2.9 if r["maglia"] else 2.2}" fill="#fff" text-anchor="middle" '
                f'font-weight="700">{e(r["maglia"] or initials(pitch_name(r)))}</text>'
                f'<text x="{x:.1f}" y="{y + 5.6:.1f}" font-size="2.2" fill="var(--ink)" text-anchor="middle" '
                f'stroke="var(--pitch)" stroke-width="0.6" paint-order="stroke">{name}</text>{sub_txt}{"".join(badges)}</g>')
    head = "".join(f'<div style="text-align:{"left" if i == 0 else "right"}"><span class="dot" style="background:{COL[i]}"></span>'
                   f'<b>{e(t)}</b> <span class="sub">{e(T[t].get("modulo") or "")}</span></div>' for i, t in enumerate(teams))
    lists = "".join(f"<div>{bench(T[t], R, K, t, COL[i])}</div>" for i, t in enumerate(teams))
    return (f'<div class="grid2" style="margin-bottom:8px">{head}</div>{pitch("".join(marks))}'
            + leg(*[(sw_dot(v), k) for k, v in REPARTI.items()])
            + leg((sw_dot(COL[0], False), f"bordo {e(teams[0])}"), (sw_dot(COL[1], False), f"bordo {e(teams[1])}"), ("⚽", "gol"),
                  (sw(f'<circle cx="11" cy="6" r="4.5" fill="none" stroke="var(--mute)" stroke-width="1"/><text x="11" y="8.6" font-size="7" text-anchor="middle" fill="var(--mute)" font-weight="700">A</text>'), "assist"),
                  (sw_rect("#f2c200"), "giallo"), (sw_rect("#d33"), "rosso"), ('<span style="color:#d33">▼ 63\'</span>', "minuto di uscita"))
            + f'<div class="legend">Posizione media reale dei titolari (tutte le azioni con palla), ogni squadra nella propria metà · '
            f'accanto al nome il ruolo di partenza (GK portiere, CB/RCB/LCB centrali, RB/LB terzini, RWB/LWB esterni, CDM/RDM/LDM mediani, '
            f'CM/RCM/LCM centrocampisti, RM/LM esterni di centrocampo, CAM/RAM/LAM trequartisti, RW/LW ali, CF/RCF/LCF/SS attaccanti) · '
            f'passa il mouse per ruolo, xT e xG</div>'
            f'<div class="grid2" style="margin-top:12px">{lists}</div>')


def bench(t, R, K, team, color):
    subs = sub_events(K, team)
    cards = card_minutes(K, team)
    goals = goal_minutes(K, team)
    rows = {r["giocatore"]: r for r in R if r["squadra"] == team}
    def tag(name):
        out = "".join(f' ⚽{m}' for m in goals.get(name, []))
        out += "".join(f' {"🟨" if c == "Giallo" else "🟥"}{m}\'' for c, m in cards.get(name, []))
        return out
    def label(name):
        r = rows.get(name)
        return f'{e(r["maglia"])} {e(r.get("soprannome") or r["giocatore"])}' if r else e(name)
    items = []
    for off, (minute, on, motivo) in sorted(subs.items(), key=lambda x: int(x[1][0])):
        why = {"Tactical": "", "Injury": " – infortunio"}.get(motivo, f" – {motivo}" if motivo else "")
        role = it_roles(rows.get(on, {}).get("ruoli", ""))
        items.append(f'<li><span class="sub">{minute}\'</span> <span style="color:#2a9d4a">▲</span> <b>{label(on)}</b>{tag(on)} '
                     f'<span style="color:#d33">▼</span> {label(off)}<span class="sub">{why}{f" · {e(role)}" if role else ""}</span></li>')
    unused = [r for r in R if r["squadra"] == team and r["stato"] == "non entrato"]
    xi = [r for r in R if r["squadra"] == team and r["stato"] == "titolare"]
    shifts = [k for k in K if k["squadra"] == team and k["tipo"] == "Cambio modulo"]
    out = [f'<h3><span class="dot" style="background:{color}"></span>{e(team)}</h3>']
    if t.get("allenatore"):
        out.append(f'<p style="margin:0 0 6px"><b>Allenatore:</b> {e(t["allenatore"])}</p>')
    if t.get("modulo"):
        ch = "".join(f'; {k["minuto"]}\' {e(k["dettaglio"])}' for k in shifts)
        out.append(f'<p style="margin:0 0 6px"><b>Modulo:</b> {e(t["modulo"])}<span class="sub">{ch}</span></p>')
    out.append('<p style="margin:0 0 4px"><b>Titolari:</b></p><ul class="sub" style="margin-bottom:8px">'
               + "".join(f'<li><span style="color:var(--ink)">{label(r["giocatore"])}</span>{tag(r["giocatore"])} · {e(it_roles(r["ruoli"]))}</li>' for r in xi)
               + "</ul>")
    if items:
        out.append(f'<p style="margin:0 0 4px"><b>Sostituzioni:</b></p><ul style="margin-bottom:8px">{"".join(items)}</ul>')
    if unused:
        out.append('<p style="margin:0 0 4px"><b>Riserve non utilizzate:</b></p><p class="sub" style="margin:0">'
                   + ", ".join(f'{e(r["maglia"])} {e(r.get("soprannome") or r["giocatore"])}' for r in unused) + "</p>")
    return "".join(out)


def initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper()


def report(T, P, S, E, K, teams, R=(), C=(), PS=None, RG=()):
    nums = {r["player_id"]: r["maglia"] for r in R}
    for p in P:  # i numeri di rose.csv includono quelli recuperati quando la fonte riporta 0
        p["maglia"] = nums.get(p["player_id"], "" if p["maglia"] in ("0", "") else p["maglia"])
        p["voto"] = VOTI.get((p["n"], p["player_id"]), "")
    h, a = T[teams[0]], T[teams[1]]
    has360 = h.get("dati_360") == "1"
    text, keys = summary(T, P, teams)
    rows = []
    for label, k, d in TEAM_ROWS:
        if k.endswith("_360") and not has360:
            continue
        vh, va = num(h.get(k)), num(a.get(k))
        tot = vh + va
        ph = 50 if tot == 0 else 100 * vh / tot
        rows.append(f'<tr><td class="v">{f(h.get(k), d)}</td><td class="l">{label}'
                    f'<div class="bar"><span style="width:{ph:.1f}%;background:{COL[0]}"></span>'
                    f'<span style="width:{100 - ph:.1f}%;background:{COL[1]}"></span></div></td><td class="v">{f(a.get(k), d)}</td></tr>')
    by_team = {t: sorted([p for p in P if p["squadra"] == t], key=lambda p: (p["titolare"] != "1", -num(p["minuti"])))
               for t in teams}
    meta = h
    title = f'{teams[0]} {h["gol"]}-{a["gol"]} {teams[1]}'
    legend = "".join(f'<span class="dot" style="background:{COL[i]}"></span>{e(t)} &nbsp; ' for i, t in enumerate(teams))
    nets = "".join(f'<div><h3><span class="dot" style="background:{COL[i]}"></span>{e(t)}</h3>'
                   + (network_windows(PS, P, t, K, COL[i]) if PS is not None else
                      pass_network(by_team[t], [x for x in E if x["squadra"] == t], COL[i])) + '</div>' for i, t in enumerate(teams))
    press = "".join(f'<div><h3><span class="dot" style="background:{COL[i]}"></span>{e(t)}</h3>{pressing_map(RG, t, COL[i], P)}</div>'
                    for i, t in enumerate(teams))
    nav = "".join(f'<a href="#{i}">{l}</a>' for i, l in (("analisi", "Analisi"), ("formazioni", "Formazioni"), ("statistiche", "Statistiche"),
                  ("cronaca", "Cronaca"), ("tiri", "Tiri"), ("conduzioni", "Conduzioni"), ("pressing", "Pressing"),
                  ("individuali", "Mappe individuali"), ("rete", "Rete passaggi"), ("calore", "Mappe di calore"), ("giocatori", "Giocatori")))
    tables = "".join(f'<div class="card" id="giocatori"><h2><span class="dot" style="background:{COL[i]}"></span>Giocatori – {e(t)}</h2>'
                     f'{player_tabs(by_team[t], COL[i])}{leg((sw_grad(COL[i]), "heatmap: da poche a molte azioni (attacca a destra)"), ("🟨🟥", "cartellini"), ("(25)", "età"))}'
                     f'<div class="legend">Righe in grigio = subentrati. Contrasti, dribbling, aerei e passaggi: riusciti/tentati. '
                     f'Voto Delta Scout 0–10 (s.v. sotto 20 minuti): indice calcolato da Delta Scout confrontando ogni statistica con tutte le '
                     f'prestazioni dello stesso reparto. "Rispetto alla carriera": valore per 90\' nella partita / media per 90\' in carriera '
                     f'(▲ almeno 1,5 volte la media, ▼ meno della metà; servono 30 minuti).</div></div>' for i, t in enumerate(teams))
    heat = "".join(f'<div class="card" id="calore"><h2><span class="dot" style="background:{COL[i]}"></span>Mappe di calore – {e(t)}</h2><div class="grid3">'
                   + "".join(f'<div><h3>{lab}</h3>{heat_pitch(T[t].get(f"heatmap_{k}_6x4"), COL[i])}</div>'
                             for k, lab in (("tocchi", "Azioni con palla"), ("pressioni", "Pressioni"), ("difesa", "Azioni difensive")))
                   + f'</div>{leg((sw_grad(COL[i]), "da poche a molte azioni"))}<div class="legend">La squadra attacca verso destra.</div></div>'
                   for i, t in enumerate(teams) if T[t].get("heatmap_tocchi_6x4"))
    combo = "".join(f"<div>{combos(E, by_team[t], t, COL[i])}</div>" for i, t in enumerate(teams))
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} – Delta Scout</title>{HEAD_EXTRA}<style>{CSS}</style></head><body><main>
{brand_bar(nav)}
<p class="sub"><a href="index.html">← Tutte le partite</a> · <a href="classifiche.html">Classifiche</a></p>
<div class="card"><h1>#{meta["n"]} · {e(meta["competizione"])} {e(meta["stagione"])} · {e(meta["data"])}</h1>
<div class="score"><div class="t" style="color:{COL[0]}">{e(teams[0])}</div><div class="r">{h["gol"]} – {a["gol"]}</div>
<div class="t" style="color:{COL[1]}">{e(teams[1])}</div></div>
<div class="score sub"><div>xG {f(h["xg"])}{mod(h)}{coach(h)}</div><div></div><div>xG {f(a["xg"])}{mod(a)}{coach(a)}</div></div>
<div class="kv sub">{info_line(h)}</div></div>
{social_box(T, P, teams, text, keys) if EXPORT_JS else ""}
<div class="card" id="analisi"><h2>Analisi</h2><p>{" ".join(text)}</p><h3>Giocatori chiave</h3><ul>{"".join(f"<li>{k}</li>" for k in keys)}</ul></div>
{f'<div class="card" id="formazioni"><h2>Formazioni</h2>{lineups(T, P, R, K, teams)}</div>' if R else ""}
<div class="grid2" id="statistiche"><div class="card"><h2>Statistiche di squadra</h2>{leg((sw_rect(COL[0]), e(teams[0])), (sw_rect(COL[1]), e(teams[1])))}
<table class="cmp" style="margin-top:8px">{"".join(rows)}</table><div class="legend">La barra mostra la quota di ogni squadra sul totale.</div></div>
<div><div class="card"><h2>Andamento xG</h2>{xg_timeline(S, teams)}{leg((sw_line(COL[0], 2.5), e(teams[0])), (sw_line(COL[1], 2.5), e(teams[1])), (sw_dot("var(--mute)"), "gol"))}
<div class="legend">xG cumulati minuto per minuto: ogni gradino è un tiro.</div></div>
<div class="card"><h2>Mappa dei tiri</h2>{shot_map(S, teams)}{leg((sw_dot(COL[0]), f"gol {e(teams[0])}"), (sw_dot(COL[0], False), "tiro"), (sw_dot(COL[1]), f"gol {e(teams[1])}"), (sw_dot(COL[1], False), "tiro"), (sw_dot("var(--mute)", False, 1.8), "xG basso"), (sw_dot("var(--mute)", False, 5), "xG alto"))}
<div class="legend">{e(teams[0])} attacca a destra, {e(teams[1])} a sinistra · passa il mouse per i dettagli</div></div></div></div>
<div class="grid2" id="cronaca"><div class="card"><h2>Cronaca</h2>{timeline(K, teams)}</div>
<div><div class="card"><h2>Momentum</h2>{momentum_chart(T, teams)}{leg((sw_rect(COL[0]), f"{e(teams[0])} (sopra)"), (sw_rect(COL[1]), f"{e(teams[1])} (sotto)"))}
<div class="legend">Azioni nel terzo offensivo ogni 5 minuti: barra più alta = più pressione offensiva.</div></div>
<div class="card"><h2>Combinazioni più frequenti</h2><div class="grid2">{combo}</div></div></div></div>
<div class="card" id="tiri"><h2>Tiri per tipo</h2>{shot_breakdown(S, teams)}</div>
<div class="card"><h2>Tutti i tiri</h2>{shot_table(S, teams)}</div>
<div class="card" id="conduzioni"><h2>Carry map – conduzioni palla</h2><div style="display:grid;gap:22px">{"".join(f'<div><h3><span class="dot" style="background:{COL[i]}"></span>{e(t)}</h3>{carry_map(C, t, COL[i], P, i)}</div>' for i, t in enumerate(teams))}</div>
{leg(*[(sw_line(col, 2.2, "", 1, True), f"pericolosità {name}") for name, col, _ in CARRY_CLS])}
{leg((sw(f'<circle cx="11" cy="6" r="5" fill="#7b8794"/><text x="11" y="8.4" font-size="7" text-anchor="middle" fill="#fff" font-weight="700">10</text>'), "chi parte palla al piede (numero di maglia)"),
     (sw('<circle cx="11" cy="6" r="4.3" fill="none" stroke="var(--ink)" stroke-width="1.2"/>'), "finisce in un tiro entro 10\""), ("⚽", "finisce in gol"),
     (sw('<path d="M7,2 l8,8 m0,-8 l-8,8" stroke="#e03131" stroke-width="1.6"/>'), "palla persa entro 10\""))}
<div class="legend">Conduzioni progressive, nel terzo finale o in area. Il cerchio con il numero è il punto di partenza, la freccia indica dove è arrivato il giocatore.
Pericolosità = xT guadagnato: bassa sotto 0,01, media 0,01–0,03, alta oltre 0,03 o se entra in area. Di base sono mostrate solo quelle medie e alte.
Entrambe le squadre attaccano verso destra · passa il mouse su una conduzione per i dettagli.</div></div>{CARRY_JS}
<div class="card" id="pressing"><h2>Pressing – dove si recupera palla</h2><div class="grid2">{press}</div>
{leg((sw_dot("var(--mute)", True, 2.5), "recupero (colore della squadra)"), (sw_dot("#d6336c", True, 4), "porta a un tiro entro 10\""), ("⚽", "porta a un gol"), (sw_dot("#aab3bd", True, 2.5), "palla persa subito dopo"))}
<div class="legend">Recuperi palla, intercetti vinti e contrasti vinti. Entrambe le squadre attaccano verso destra: più punti a destra = pressing più alto.
La barra sotto il campo conta i recuperi per terzo di campo.</div></div>
{f'<div class="card" id="individuali"><h2>Mappe individuali</h2>{individual_maps(P, PS, C, teams)}</div>' if PS is not None else ""}
<div class="card" id="rete"><h2>Rete di passaggi</h2><div style="display:grid;gap:18px">{nets}</div>{leg((sw_dot("var(--mute)", True, 2.5), "poco coinvolto"), (sw_dot("var(--mute)", True, 5), "molto coinvolto"), (sw_line("var(--mute)", 0.8, "", 0.4), "pochi passaggi"), (sw_line("var(--mute)", 3), "molti passaggi"))}<div class="legend">Scegli il periodo: tutta la partita (titolari e subentrati insieme, possibili sovrapposizioni) oppure ogni finestra
tra un cambio e l'altro, dove ogni cerchio è un giocatore realmente in campo in quel momento (cambi a meno di 5 minuti di distanza sono uniti).
Posizione media di passaggi e ricezioni; linee = passaggi riusciti tra due giocatori (almeno 3 nella partita intera, 2 nelle finestre),
più spesse = più passaggi; cerchi più grandi = più coinvolti. Entrambe attaccano a destra.
Accanto: numero di maglia → giocatore, con i passaggi scambiati nella rete.</div></div>
{heat}
{tables}
{footer()}
</main>{TAB_JS}{NET_JS}{PROTECT_JS}{EXPORT_JS}</body></html>"""


def mod(t):
    return f' · {e(t["modulo"])}' if t.get("modulo") else ""


def coach(t):
    s = f'<br>All. {e(t["allenatore"])}' if t.get("allenatore") else ""
    el = ELO.get((t["n"], t["squadra"]))
    if el:
        note = "" if int(el["partite_storia"]) >= 10 else " (stima poco affidabile)"
        s += f'<br>Elo {el["elo_pre"]} → {el["elo_post"]}{note}'
    return s


def info_line(t):
    parts = [("Fase", FASI.get(t.get("fase"), t.get("fase"))), ("Giornata", t.get("giornata")), ("Stadio", t.get("stadio")), ("Arbitro", t.get("arbitro"))]
    return "".join(f"<span>{k}: {e(v)}</span>" for k, v in parts if v)


def groups(path, wanted):
    with open(path, encoding="utf-8") as fh:
        for n, rows in groupby(csv.DictReader(fh), key=lambda r: int(r["n"])):
            if wanted is None or n in wanted:
                yield n, list(rows)


def parse_n(spec):
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", help="numeri di partita da partite.csv, es. 778,831-894")
    ap.add_argument("--data", default=str(HERE / "output"), help="cartella con i CSV di analizza.py")
    ap.add_argument("--out", default=str(HERE / "report"))
    args = ap.parse_args()
    wanted = parse_n(args.n) if args.n else None
    src, out = Path(args.data), Path(args.out)
    if (src / "anagrafica_giocatori.csv").exists():
        with open(src / "anagrafica_giocatori.csv", encoding="utf-8") as fh:
            ANAG.update({r["player_id"]: r for r in csv.DictReader(fh) if r["reep_id"]})
    if (src / "elo.csv").exists():
        with open(src / "elo.csv", encoding="utf-8") as fh:
            ELO.update({(r["n"], r["squadra"]): r for r in csv.DictReader(fh)})
    if (src / "voti.csv").exists():
        with open(src / "voti.csv", encoding="utf-8") as fh:
            VOTI.update({(r["n"], r["player_id"]): r["voto"] for r in csv.DictReader(fh) if r["voto"]})
    if (src / "carriere_giocatori.csv").exists():
        with open(src / "carriere_giocatori.csv", encoding="utf-8") as fh:
            CAREER.update({r["player_id"]: r for r in csv.DictReader(fh)})
        for r in CAREER.values():
            r["azioni_difensive_p90"] = r.get("azioni_difensive_p90") or str(
                num(r["contrasti_vinti_p90"]) + num(r["intercetti_p90"]) + num(r["recuperi_p90"]))
    out.mkdir(parents=True, exist_ok=True)
    logo_png = HERE / "statsbomb_logo.png"
    if logo_png.exists():
        (out / "statsbomb_logo.png").write_bytes(logo_png.read_bytes())
    (out / "vendor").mkdir(exist_ok=True)
    for v in (HERE / "vendor").glob("*"):
        (out / "vendor" / v.name).write_bytes(v.read_bytes())
    for page in ("classifiche.html", "studi.html", "dati.html"):
        if (HERE / page).exists():
            (out / page).write_bytes((HERE / page).read_bytes())

    # i CSV sono ordinati per n: si leggono in parallelo, una partita alla volta (poca memoria)
    iters = {k: groups(src / f"{k}.csv", wanted) if (src / f"{k}.csv").exists() else iter(())
             for k in ("squadre", "giocatori", "tiri", "rete_passaggi", "eventi_chiave", "rose", "conduzioni", "recuperi")}
    pending = {k: next(it, None) for k, it in iters.items()}

    def take(k, n):
        rows = []
        while pending[k] and pending[k][0] <= n:
            if pending[k][0] == n:
                rows = pending[k][1]
            pending[k] = next(iters[k], None)
        return rows

    done = []
    while pending["squadre"]:
        n, T_rows = pending["squadre"]
        pending["squadre"] = next(iters["squadre"], None)
        P, S, E, K = take("giocatori", n), take("tiri", n), take("rete_passaggi", n), take("eventi_chiave", n)
        R = take("rose", n)
        C = take("conduzioni", n)
        RG = take("recuperi", n)
        pf = src / "passaggi" / f"{n}.json.gz"
        PS = json.loads(gzip.decompress(pf.read_bytes()).decode("utf-8"))["p"] if pf.exists() else None
        home = next((r for r in T_rows if r["casa_trasferta"] == "casa"), T_rows[0])
        teams = [home["squadra"], home["avversario"]]
        T = {r["squadra"]: r for r in T_rows}
        if len(T) != 2:
            continue
        (out / f"{n}.html").write_text(report(T, P, S, E, K, teams, R, C, PS, RG), encoding="utf-8")
        done.append((n, home, T[teams[1]]))
        if len(done) % 200 == 0:
            print(f"{len(done)} report…", flush=True)

    sections = defaultdict(list)
    for n, h, a in done:
        sections[(h["competizione"], h["stagione"])].append(
            f'<li><a href="{n}.html">{e(h["data"])} · {e(h["squadra"])} <b>{h["gol"]}-{a["gol"]}</b> {e(a["squadra"])}</a>'
            f' <span class="sub">#{n} · xG {f(h["xg"])}–{f(a["xg"])}</span></li>')
    body = "".join(f'<details class="card"><summary><b>{e(c)} – {e(s)}</b> <span class="sub">({len(v)})</span></summary>'
                   f'<ul>{"".join(v)}</ul></details>' for (c, s), v in sections.items())
    (out / "index.html").write_text(
        f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Delta Scout – Report partite</title>{HEAD_EXTRA}<style>{CSS}</style></head><body><main>'
        f'{brand_bar(INDEX_NAV)}'
        f'<h2>Report partite</h2><p class="sub">{len(done)} partite · dati StatsBomb Open Data</p>{body}{footer()}</main>{PROTECT_JS}</body></html>',
        encoding="utf-8")
    print(f"Fatto: {len(done)} report in {out}  →  apri {out / 'index.html'}")


if __name__ == "__main__":
    main()
