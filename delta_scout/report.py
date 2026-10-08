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
.lg{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12px;color:var(--mute);margin-top:10px;align-items:center}
.lg span{display:inline-flex;align-items:center;gap:6px}.lg svg{display:inline-block;width:auto;height:12px}
"""


ANAG, ELO = {}, {}


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
    return f'<svg viewBox="{x0 - 1} -1 {w + 2} 82" role="img">{lines}{inner}</svg>'


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
        tip = f'{s["minuto"]}\' {s["giocatore"]} – xG {f(s["xg"])} – {s["esito"]}'
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
    svg.append("</svg>")
    return "".join(svg)


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


def carry_map(C, team, color, names=None):
    cs = [c for c in C if c["squadra"] == team]
    if not cs:
        return '<p class="sub">Nessuna conduzione significativa.</p>'
    mx = max(max(num(c["xt"]) for c in cs), 0.01)
    out = []
    for c in sorted(cs, key=lambda c: num(c["xt"])):
        k = max(num(c["xt"]), 0) / mx
        w = 0.9 if c["in_area"] == "1" else 0.5
        out.append(f'<g><title>{e(c["minuto"])}\' {e(c["giocatore"])} – {c["metri"]} m, xT {f(c["xt"], 3)}</title>'
                   f'<line x1="{c["x"]}" y1="{c["y"]}" x2="{c["fine_x"]}" y2="{c["fine_y"]}" stroke="{color}" stroke-width="{w}" '
                   f'stroke-opacity="{0.35 + 0.6 * k:.2f}" stroke-dasharray="1.2 0.6"/>'
                   f'<circle cx="{c["fine_x"]}" cy="{c["fine_y"]}" r="{0.7 if c["in_area"] == "1" else 0.5}" fill="{color}"/></g>')
    tot = defaultdict(lambda: [0, 0.0, 0.0, ""])
    for c in cs:
        t = tot[c["player_id"]]
        t[0] += 1; t[1] += num(c["metri"]); t[2] += num(c["xt"]); t[3] = (names or {}).get(c["player_id"], c["giocatore"])
    best = sorted(tot.values(), key=lambda t: -t[1])[:5]
    lst = "".join(f"<li>{e(t[3])}: <b>{t[0]}</b> conduzioni, {t[1]:.0f} m, xT {t[2]:.2f}</li>" for t in best)
    return pitch("".join(out)) + f'<ul class="sub" style="margin-top:6px">{lst}</ul>'


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
    out.append("</svg>")
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
                    f'<td style="text-align:left">{e(s["parte_corpo"])}</td><td style="text-align:left">{e(situation(s))}</td>'
                    f'<td>{s["difensori_nel_triangolo"]}</td><td>{"sì" if s["sotto_pressione"] == "1" else ""}</td>'
                    f'<td>{"sì" if s["primo_tocco"] == "1" else ""}</td><td style="text-align:left">{e(s["assistman"])}</td></tr>')
    head = ("<tr><th>Min</th><th>Giocatore</th><th>xG</th><th>Esito</th><th>Dist. (yd)</th><th>Corpo</th><th>Situazione</th>"
            "<th>Difensori davanti</th><th>Pressato</th><th>Al volo</th><th>Assist da</th></tr>")
    return f'<div class="scroll"><table class="pl">{head}{"".join(rows)}</table></div>'


ICON = {"Gol": "⚽", "Gol su rigore": "⚽ (R)", "Autogol": "⚽ (AG)", "Giallo": "🟨", "Secondo giallo": "🟨🟥", "Rosso": "🟥",
        "Sostituzione": "🔁", "Cambio modulo": "📐"}


def timeline(K, teams):
    if not K:
        return '<p class="sub">Nessun evento.</p>'
    rows = []
    for k in K:
        c = COL[teams.index(k["squadra"])] if k["squadra"] in teams else "inherit"
        who = e(k["giocatore"])
        rows.append(f'<tr><td class="m">{k["minuto"]}\'</td><td>{ICON.get(k["tipo"], "")} <span class="dot" style="background:{c}"></span>'
                    f'<b>{e(k["tipo"])}</b> {who} <span class="sub">{e(k["dettaglio"])}</span></td></tr>')
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
    "Attacco": [("Min", lambda p: f(p["minuti"], 0)), ("Gol", lambda p: g(p, "gol")), ("Ass", lambda p: g(p, "assist")),
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
                ("Ruolo abituale", lambda p: e(ANAG.get(p["player_id"], {}).get("ruolo") or "–")),
                ("Link", lambda p: links(p))],
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
                        + (f'<td style="text-align:left">{e(p["ruolo"])}</td>' if i == 0 else "")
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
                badges.append(f'<text x="{x + 2.6:.1f}" y="{y - 2.2:.1f}" font-size="2.8">⚽{"" if gl == 1 else f"×{gl}"}</text>')
            if num(p.get("assist")):
                badges.append(f'<circle cx="{x - 3:.1f}" cy="{y - 2.6:.1f}" r="1.3" fill="var(--card)" stroke="{c}" stroke-width="0.3"/>'
                              f'<text x="{x - 3:.1f}" y="{y - 2.0:.1f}" font-size="1.7" text-anchor="middle" fill="{c}" font-weight="700">A</text>')
            cs = cards.get(r["giocatore"], [])
            if cs:
                col = "#d33" if any(t_ != "Giallo" for t_, _ in cs) else "#f2c200"
                badges.append(f'<rect x="{x + 2.4:.1f}" y="{y + 0.4:.1f}" width="1.5" height="2.1" rx="0.2" fill="{col}"/>')
            sub = subs.get(r["giocatore"])
            sigla = SIGLE.get(r["ruolo_iniziale"], "")
            name = e(pitch_name(r)) + (f', <tspan fill="var(--mute)" font-weight="600">{sigla}</tspan>' if sigla else "")
            sub_txt = (f'<text x="{x:.1f}" y="{y + 8.3:.1f}" font-size="2" fill="#d33" text-anchor="middle" '
                       f'stroke="var(--pitch)" stroke-width="0.5" paint-order="stroke">▼ {sub[0]}\'</text>') if sub else ""
            tip = f'{r["giocatore"]} – {r["ruolo_iniziale"]}' + (f' – xT {f(p.get("xt"))}, xG {f(p.get("xg"))}' if p else "")
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
        role = rows.get(on, {}).get("ruoli", "")
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
               + "".join(f'<li><span style="color:var(--ink)">{label(r["giocatore"])}</span>{tag(r["giocatore"])} · {e(r["ruoli"])}</li>' for r in xi)
               + "</ul>")
    if items:
        out.append(f'<p style="margin:0 0 4px"><b>Sostituzioni:</b></p><ul style="margin-bottom:8px">{"".join(items)}</ul>')
    if unused:
        out.append('<p style="margin:0 0 4px"><b>Riserve non utilizzate:</b></p><p class="sub" style="margin:0">'
                   + ", ".join(f'{e(r["maglia"])} {e(r.get("soprannome") or r["giocatore"])}' for r in unused) + "</p>")
    return "".join(out)


def initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper()


def report(T, P, S, E, K, teams, R=(), C=(), PS=None):
    nums = {r["player_id"]: r["maglia"] for r in R}
    for p in P:  # i numeri di rose.csv includono quelli recuperati quando la fonte riporta 0
        p["maglia"] = nums.get(p["player_id"], "" if p["maglia"] in ("0", "") else p["maglia"])
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
                   f'{pass_network(by_team[t], [x for x in E if x["squadra"] == t], COL[i])}</div>' for i, t in enumerate(teams))
    tables = "".join(f'<div class="card"><h2><span class="dot" style="background:{COL[i]}"></span>Giocatori – {e(t)}</h2>'
                     f'{player_tabs(by_team[t], COL[i])}{leg((sw_grad(COL[i]), "heatmap: da poche a molte azioni (attacca a destra)"), ("🟨🟥", "cartellini"), ("(25)", "età"))}'
                     f'<div class="legend">Righe in grigio = subentrati. Contrasti, dribbling, aerei e passaggi: riusciti/tentati.</div></div>' for i, t in enumerate(teams))
    heat = "".join(f'<div class="card"><h2><span class="dot" style="background:{COL[i]}"></span>Mappe di calore – {e(t)}</h2><div class="grid3">'
                   + "".join(f'<div><h3>{lab}</h3>{heat_pitch(T[t].get(f"heatmap_{k}_6x4"), COL[i])}</div>'
                             for k, lab in (("tocchi", "Azioni con palla"), ("pressioni", "Pressioni"), ("difesa", "Azioni difensive")))
                   + f'</div>{leg((sw_grad(COL[i]), "da poche a molte azioni"))}<div class="legend">La squadra attacca verso destra.</div></div>'
                   for i, t in enumerate(teams) if T[t].get("heatmap_tocchi_6x4"))
    combo = "".join(f"<div>{combos(E, by_team[t], t, COL[i])}</div>" for i, t in enumerate(teams))
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} – Delta Scout</title><style>{CSS}</style></head><body><main>
<p class="sub"><a href="index.html">← Tutte le partite</a></p>
<div class="card"><h1>#{meta["n"]} · {e(meta["competizione"])} {e(meta["stagione"])} · {e(meta["data"])}</h1>
<div class="score"><div class="t" style="color:{COL[0]}">{e(teams[0])}</div><div class="r">{h["gol"]} – {a["gol"]}</div>
<div class="t" style="color:{COL[1]}">{e(teams[1])}</div></div>
<div class="score sub"><div>xG {f(h["xg"])}{mod(h)}{coach(h)}</div><div></div><div>xG {f(a["xg"])}{mod(a)}{coach(a)}</div></div>
<div class="kv sub">{info_line(h)}</div></div>
<div class="card"><h2>Analisi</h2><p>{" ".join(text)}</p><h3>Giocatori chiave</h3><ul>{"".join(f"<li>{k}</li>" for k in keys)}</ul></div>
{f'<div class="card"><h2>Formazioni</h2>{lineups(T, P, R, K, teams)}</div>' if R else ""}
<div class="grid2"><div class="card"><h2>Statistiche di squadra</h2>{leg((sw_rect(COL[0]), e(teams[0])), (sw_rect(COL[1]), e(teams[1])))}
<table class="cmp" style="margin-top:8px">{"".join(rows)}</table><div class="legend">La barra mostra la quota di ogni squadra sul totale.</div></div>
<div><div class="card"><h2>Andamento xG</h2>{xg_timeline(S, teams)}{leg((sw_line(COL[0], 2.5), e(teams[0])), (sw_line(COL[1], 2.5), e(teams[1])), (sw_dot("var(--mute)"), "gol"))}
<div class="legend">xG cumulati minuto per minuto: ogni gradino è un tiro.</div></div>
<div class="card"><h2>Mappa dei tiri</h2>{shot_map(S, teams)}{leg((sw_dot(COL[0]), f"gol {e(teams[0])}"), (sw_dot(COL[0], False), "tiro"), (sw_dot(COL[1]), f"gol {e(teams[1])}"), (sw_dot(COL[1], False), "tiro"), (sw_dot("var(--mute)", False, 1.8), "xG basso"), (sw_dot("var(--mute)", False, 5), "xG alto"))}
<div class="legend">{e(teams[0])} attacca a destra, {e(teams[1])} a sinistra · passa il mouse per i dettagli</div></div></div></div>
<div class="grid2"><div class="card"><h2>Cronaca</h2>{timeline(K, teams)}</div>
<div><div class="card"><h2>Momentum</h2>{momentum_chart(T, teams)}{leg((sw_rect(COL[0]), f"{e(teams[0])} (sopra)"), (sw_rect(COL[1]), f"{e(teams[1])} (sotto)"))}
<div class="legend">Azioni nel terzo offensivo ogni 5 minuti: barra più alta = più pressione offensiva.</div></div>
<div class="card"><h2>Combinazioni più frequenti</h2><div class="grid2">{combo}</div></div></div></div>
<div class="card"><h2>Tiri per tipo</h2>{shot_breakdown(S, teams)}</div>
<div class="card"><h2>Tutti i tiri</h2>{shot_table(S, teams)}</div>
<div class="card"><h2>Carry map – conduzioni palla</h2><div class="grid2">{"".join(f'<div><h3><span class="dot" style="background:{COL[i]}"></span>{e(t)}</h3>{carry_map(C, t, COL[i], {p["player_id"]: short(p) for p in P})}</div>' for i, t in enumerate(teams))}</div>
{leg((sw_line("var(--mute)", 1.5, "3 2", 0.4, True), "conduzione, poco xT"), (sw_line("var(--mute)", 1.5, "3 2", 1, True), "conduzione, molto xT"), (sw_line("var(--mute)", 2.6, "3 2", 1, True), "entra in area"))}
<div class="legend">Conduzioni progressive, nel terzo finale o in area; il pallino è il punto di arrivo. Entrambe attaccano a destra.</div></div>
{f'<div class="card"><h2>Mappe individuali</h2>{individual_maps(P, PS, C, teams)}</div>' if PS is not None else ""}
<div class="card"><h2>Rete di passaggi</h2><div style="display:grid;gap:18px">{nets}</div>{leg((sw_dot("var(--mute)", True, 2.5), "poco coinvolto"), (sw_dot("var(--mute)", True, 5), "molto coinvolto"), (sw_line("var(--mute)", 0.8, "", 0.4), "pochi passaggi"), (sw_line("var(--mute)", 3), "molti passaggi"))}<div class="legend">Posizione media dei giocatori,
linee = almeno 3 passaggi riusciti (più spesse = più passaggi), cerchi più grandi = più coinvolti. Entrambe attaccano a destra.
Accanto: numero di maglia → giocatore, con i passaggi scambiati nella rete.</div></div>
{heat}
{tables}
<p class="sub">Dati: StatsBomb Open Data · Report generato da Delta Scout. Righe in grigio = subentrati.
Heatmap: azioni con palla, la squadra attacca verso destra.</p>
</main>{TAB_JS}</body></html>"""


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
    parts = [("Fase", t.get("fase")), ("Giornata", t.get("giornata")), ("Stadio", t.get("stadio")), ("Arbitro", t.get("arbitro"))]
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
    out.mkdir(parents=True, exist_ok=True)

    # i CSV sono ordinati per n: si leggono in parallelo, una partita alla volta (poca memoria)
    iters = {k: groups(src / f"{k}.csv", wanted) if (src / f"{k}.csv").exists() else iter(())
             for k in ("squadre", "giocatori", "tiri", "rete_passaggi", "eventi_chiave", "rose", "conduzioni")}
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
        pf = src / "passaggi" / f"{n}.json.gz"
        PS = json.loads(gzip.decompress(pf.read_bytes()).decode("utf-8"))["p"] if pf.exists() else None
        home = next((r for r in T_rows if r["casa_trasferta"] == "casa"), T_rows[0])
        teams = [home["squadra"], home["avversario"]]
        T = {r["squadra"]: r for r in T_rows}
        if len(T) != 2:
            continue
        (out / f"{n}.html").write_text(report(T, P, S, E, K, teams, R, C, PS), encoding="utf-8")
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
        f'<title>Delta Scout – Report partite</title><style>{CSS}</style></head><body><main>'
        f'<h2>Delta Scout – Report partite</h2><p class="sub">{len(done)} partite · dati StatsBomb Open Data</p>{body}</main></body></html>',
        encoding="utf-8")
    print(f"Fatto: {len(done)} report in {out}  →  apri {out / 'index.html'}")


if __name__ == "__main__":
    main()
