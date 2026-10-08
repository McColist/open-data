"""Delta Scout - report HTML completi per partita, generati dai CSV di delta_scout/output.

Uso:
    python delta_scout/report.py                  # tutte le partite
    python delta_scout/report.py --n 778,831-894  # solo alcuni numeri
    python delta_scout/report.py --out C:\\DeltaScout\\report

Serve solo l'output di analizza.py (non i dati grezzi). Apri index.html nella cartella di output.
"""
import argparse
import csv
import html
from collections import defaultdict
from itertools import groupby
from pathlib import Path

HERE = Path(__file__).resolve().parent
COL = ("#2a6fdb", "#e0533d")  # casa, trasferta

TEAM_ROWS = [
    ("Gol", "gol", 0), ("xG", "xg", 2), ("xG senza rigori", "npxg", 2), ("Tiri", "tiri", 0),
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
svg{display:block;width:100%;height:auto}.legend{font-size:12px;color:var(--mute);margin-top:6px}
"""


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
    for pid, p in pos.items():
        if pid not in vol:
            continue
        r = 1.6 + 2.2 * vol[pid] / vmax
        label = p["maglia"] or short(p).split()[-1][:3]
        out.append(f'<circle cx="{p["pos_media_x"]}" cy="{p["pos_media_y"]}" r="{r:.2f}" fill="{color}" stroke="var(--card)" stroke-width="0.4">'
                   f'<title>{e(short(p))}</title></circle>'
                   f'<text x="{p["pos_media_x"]}" y="{num(p["pos_media_y"]) + 1:.1f}" font-size="2.6" fill="#fff" text-anchor="middle" '
                   f'font-weight="600">{e(label)}</text>')
    return pitch("".join(out))


def mini_heat(spec, color):
    if not spec:
        return ""
    vals = [int(v) for v in spec.split(";")]
    mx = max(vals) or 1
    cells = "".join(f'<rect x="{(i % 6) * 8}" y="{(i // 6) * 8}" width="8" height="8" fill="{color}" fill-opacity="{0.05 + 0.9 * v / mx:.2f}"/>'
                    for i, v in enumerate(vals))
    return (f'<svg viewBox="0 0 48 32" width="48" height="32" style="display:inline-block;vertical-align:middle">'
            f'<rect width="48" height="32" fill="var(--pitch)"/>{cells}</svg>')


PLAYER_COLS = [
    ("Min", lambda p: f(p["minuti"], 0)), ("Gol", lambda p: p["gol"]), ("Ass", lambda p: p["assist"]),
    ("xG", lambda p: f(p["xg"])), ("xA", lambda p: f(p["xa"])), ("xG chain", lambda p: f(p["xg_chain"])),
    ("Tiri", lambda p: f'{p["tiri"]} ({p["tiri_in_porta"]})'), ("Pass", lambda p: f'{p["passaggi_riusciti"]}/{p["passaggi"]}'),
    ("Pass %", lambda p: f(p["precisione_passaggi_pct"], 0)), ("P. chiave", lambda p: p["passaggi_chiave"]),
    ("P. progr.", lambda p: p["passaggi_progressivi"]), ("In area", lambda p: p["passaggi_in_area"]),
    ("Cond. progr.", lambda p: p["conduzioni_progressive"]), ("Metri progr.", lambda p: f(p["metri_progressivi"], 0)),
    ("Dribbling", lambda p: f'{p["dribbling_riusciti"]}/{p["dribbling"]}'), ("Tocchi area", lambda p: p["tocchi_in_area"]),
    ("Pressioni", lambda p: p["pressioni"]), ("Contrasti", lambda p: f'{p["contrasti_vinti"]}/{p["contrasti"]}'),
    ("Intercetti", lambda p: p["intercetti"]), ("Recuperi", lambda p: p["recuperi"]),
    ("Aerei", lambda p: f'{p["aerei_vinti"]}/{num(p["aerei_vinti"]) + num(p["aerei_persi"]):.0f}'),
    ("Palle perse", lambda p: p["palle_perse"]), ("Falli", lambda p: p["falli_commessi"]),
    ("Parate", lambda p: p["parate"]),
]


def player_table(players, color, has360):
    cols = PLAYER_COLS + ([("Avv. 5m (360)", lambda p: f(p["avversari_5m_medi_360"]))] if has360 else [])
    head = "<tr><th>Giocatore</th><th>Ruolo</th>" + "".join(f"<th>{c}</th>" for c, _ in cols) + "<th>Heatmap</th></tr>"
    rows = []
    for p in players:
        card = " 🟥" if p["rossi"] != "0" else " 🟨" if p["gialli"] != "0" else ""
        cls = "" if p["titolare"] == "1" else ' class="sub"'
        rows.append(f'<tr{cls}><td>{e(p["maglia"] or "")} {e(short(p))}{card}</td><td style="text-align:left">{e(p["ruolo"])}</td>'
                    + "".join(f"<td>{fn(p)}</td>" for _, fn in cols) + f"<td>{mini_heat(p['heatmap_6x4'], color)}</td></tr>")
    return f'<div class="scroll"><table class="pl">{head}{"".join(rows)}</table></div>'


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


def report(T, P, S, E, teams):
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
                     f'{player_table(by_team[t], COL[i], has360)}</div>' for i, t in enumerate(teams))
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} – Delta Scout</title><style>{CSS}</style></head><body><main>
<p class="sub"><a href="index.html">← Tutte le partite</a></p>
<div class="card"><h1>#{meta["n"]} · {e(meta["competizione"])} {e(meta["stagione"])} · {e(meta["data"])}</h1>
<div class="score"><div class="t" style="color:{COL[0]}">{e(teams[0])}</div><div class="r">{h["gol"]} – {a["gol"]}</div>
<div class="t" style="color:{COL[1]}">{e(teams[1])}</div></div>
<div class="score sub"><div>xG {f(h["xg"])}</div><div></div><div>xG {f(a["xg"])}</div></div></div>
<div class="card"><h2>Analisi</h2><p>{" ".join(text)}</p><h3>Giocatori chiave</h3><ul>{"".join(f"<li>{k}</li>" for k in keys)}</ul></div>
<div class="grid2"><div class="card"><h2>Statistiche di squadra</h2><table class="cmp">{"".join(rows)}</table></div>
<div><div class="card"><h2>Andamento xG</h2>{xg_timeline(S, teams)}<div class="legend">{legend} · pallini = gol</div></div>
<div class="card"><h2>Mappa dei tiri</h2>{shot_map(S, teams)}<div class="legend">{e(teams[0])} attacca a destra, {e(teams[1])} a sinistra ·
dimensione = xG · pieno = gol · passa il mouse per i dettagli</div></div></div></div>
<div class="card"><h2>Rete di passaggi</h2><div class="grid2">{nets}</div><div class="legend">Posizione media dei giocatori,
linee = almeno 3 passaggi riusciti (più spesse = più passaggi), cerchi più grandi = più coinvolti. Entrambe attaccano a destra.</div></div>
{tables}
<p class="sub">Dati: StatsBomb Open Data · Report generato da Delta Scout. Righe in grigio = subentrati.
Heatmap: azioni con palla, la squadra attacca verso destra.</p>
</main></body></html>"""


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
    out.mkdir(parents=True, exist_ok=True)

    # i CSV sono ordinati per n: si leggono in parallelo, una partita alla volta (poca memoria)
    iters = {k: groups(src / f"{k}.csv", wanted) for k in ("squadre", "giocatori", "tiri", "rete_passaggi")}
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
        P, S, E = take("giocatori", n), take("tiri", n), take("rete_passaggi", n)
        home = next((r for r in T_rows if r["casa_trasferta"] == "casa"), T_rows[0])
        teams = [home["squadra"], home["avversario"]]
        T = {r["squadra"]: r for r in T_rows}
        if len(T) != 2:
            continue
        (out / f"{n}.html").write_text(report(T, P, S, E, teams), encoding="utf-8")
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
