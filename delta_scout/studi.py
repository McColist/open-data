"""Delta Scout - studi sul dataset: epoche, maschile/femminile, squadre, fortuna, finalizzazione, anomalie.

Ogni studio calcola i numeri dai CSV di output/, li disegna (SVG) e riporta campione, metodo e limiti.
Uso:
    python delta_scout/studi.py
Scrive delta_scout/studi.html (esportabile per i social come i report).
"""
import csv
import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def e(s):
    return html.escape(str(s))


def load(name):
    with open(OUT / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def is_f(comp):
    return "(F)" in comp


def wilson(k, n, z=1.96):
    """Intervallo di confidenza al 95% di una proporzione (Wilson)."""
    if not n:
        return 0, 0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def fmt(v, d=1):
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


# ------------------------------------------------------------------------------------------- grafici (SVG)
FONT = 'font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif"'


def svg_open(w, h, label):
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}" {FONT}>'


def watermark(w, h):
    return f'<text x="{w - 4}" y="{h - 4}" font-size="10" fill="var(--muted)" text-anchor="end">© Delta Scout</text>'


def line_panel(title, labels, values, ns, d=1, unit="", w=300, h=190):
    """Piccolo multiplo: una serie su categorie ordinate (epoche)."""
    pad_l, pad_r, pad_t, pad_b = 22, 22, 30, 40
    lo, hi = min(values), max(values)
    span = hi - lo or 1
    lo, hi = lo - span * 0.25, hi + span * 0.25
    X = lambda i: pad_l + (w - pad_l - pad_r) * i / (len(values) - 1)
    Y = lambda v: pad_t + (h - pad_t - pad_b) * (1 - (v - lo) / (hi - lo))
    s = [svg_open(w, h, title), f'<text x="0" y="16" font-size="13" font-weight="600" fill="var(--ink)">{e(title)}</text>']
    for t in (lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.75):
        s.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="var(--grid)" stroke-width="1"/>')
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(values))
    s.append(f'<polyline points="{pts}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, (lab, v, n) in enumerate(zip(labels, values, ns)):
        s.append(f'<g><title>{e(lab)}: {fmt(v, d)}{unit} ({n} partite)</title>'
                 f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="12" fill="transparent"/>'
                 f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4.5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/></g>'
                 f'<text x="{X(i):.1f}" y="{h - 22}" font-size="10" fill="var(--muted)" text-anchor="middle">{e(lab)}</text>'
                 f'<text x="{X(i):.1f}" y="{h - 9}" font-size="9" fill="var(--muted)" text-anchor="middle">n={n}</text>')
        if i in (0, len(values) - 1):
            s.append(f'<text x="{X(i):.1f}" y="{Y(v) - 10:.1f}" font-size="12" font-weight="600" fill="var(--ink)" text-anchor="middle">'
                     f'{fmt(v, d)}{unit}</text>')
    s.append("</svg>")
    return "".join(s)


def columns(cats, series, d=1, unit="", w=640, h=300, ci=False, ymax=None, label_all=True):
    """Colonne raggruppate. series: [(nome, var colore, valori, [ (lo,hi) ])]."""
    pad_l, pad_r, pad_t, pad_b = 40, 10, 16, 44
    top = ymax or max(max(s[2]) for s in series) * 1.18
    gw = (w - pad_l - pad_r) / len(cats)
    bw = min(24, (gw * 0.7) / len(series))
    Y = lambda v: pad_t + (h - pad_t - pad_b) * (1 - v / top)
    s = [svg_open(w, h, " / ".join(c for c in cats))]
    for k in range(1, 5):
        t = top * k / 5
        s.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="var(--grid)" stroke-width="1"/>'
                 f'<text x="{pad_l - 6}" y="{Y(t) + 3:.1f}" font-size="10" fill="var(--muted)" text-anchor="end">{fmt(t, 0 if top >= 10 else 1)}</text>')
    s.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--axis)" stroke-width="1"/>')
    for i, c in enumerate(cats):
        x0 = pad_l + gw * i + (gw - bw * len(series) - 2 * (len(series) - 1)) / 2
        for j, ser in enumerate(series):
            v = ser[2][i]
            x = x0 + j * (bw + 2)
            y = Y(v)
            hgt = Y(0) - y
            r = min(4, hgt / 2, bw / 2)
            path = (f"M{x:.1f},{Y(0):.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} H{x + bw - r:.1f} "
                    f"Q{x + bw:.1f},{y:.1f} {x + bw:.1f},{y + r:.1f} V{Y(0):.1f} Z")
            tip = f"{c} – {ser[0]}: {fmt(v, d)}{unit}"
            if ci and len(ser) > 3:
                lo_, hi_ = ser[3][i]
                tip += f" (IC 95%: {fmt(lo_, d)}–{fmt(hi_, d)})"
            s.append(f'<g><title>{e(tip)}</title><path d="{path}" fill="{ser[1]}"/>')
            if ci and len(ser) > 3:
                lo_, hi_ = ser[3][i]
                cx = x + bw / 2
                s.append(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{Y(hi_):.1f}" y2="{Y(lo_):.1f}" stroke="var(--ink)" stroke-width="1.2"/>'
                         f'<line x1="{cx - 4:.1f}" x2="{cx + 4:.1f}" y1="{Y(hi_):.1f}" y2="{Y(hi_):.1f}" stroke="var(--ink)" stroke-width="1.2"/>'
                         f'<line x1="{cx - 4:.1f}" x2="{cx + 4:.1f}" y1="{Y(lo_):.1f}" y2="{Y(lo_):.1f}" stroke="var(--ink)" stroke-width="1.2"/>')
            s.append("</g>")
            if label_all:
                ly = (Y(ser[3][i][1]) if ci and len(ser) > 3 else y) - 6
                s.append(f'<text x="{x + bw / 2:.1f}" y="{ly:.1f}" font-size="11" font-weight="600" fill="var(--ink)" '
                         f'text-anchor="middle">{fmt(v, d)}</text>')
        s.append(f'<text x="{pad_l + gw * i + gw / 2:.1f}" y="{h - 26}" font-size="11" fill="var(--muted)" text-anchor="middle">{e(c)}</text>')
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def hbars(items, d=1, unit="", w=640, row=26, diverging=False, label_w=210, value_w=60):
    """Barre orizzontali. items: [(etichetta, valore, colore, nota)]."""
    h = row * len(items) + 30
    vals = [v for _, v, _, _ in items]
    mpos = max([v for v in vals if v > 0] + [0])
    mneg = max([-v for v in vals if v < 0] + [0])
    if diverging:
        scale = (w - label_w - 2 * value_w) / ((mpos + mneg) or 1)
        x0 = label_w + value_w + mneg * scale
    else:
        scale = (w - label_w - value_w) / (mpos or 1)
        x0 = label_w
    s = [svg_open(w, h, "barre")]
    if diverging:
        s.append(f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="4" y2="{h - 22}" stroke="var(--axis)" stroke-width="1"/>')
    for i, (lab, v, col, note) in enumerate(items):
        y = 6 + i * row
        bh = min(16, row - 8)
        bw = abs(v) * scale
        x = x0 if v >= 0 else x0 - bw
        r = min(4, bw / 2)
        if v >= 0:
            path = f"M{x:.1f},{y:.1f} H{x + bw - r:.1f} Q{x + bw:.1f},{y:.1f} {x + bw:.1f},{y + r:.1f} V{y + bh - r:.1f} Q{x + bw:.1f},{y + bh:.1f} {x + bw - r:.1f},{y + bh:.1f} H{x:.1f} Z"
            tx, anchor = x + bw + 6, "start"
        else:
            path = f"M{x0:.1f},{y:.1f} H{x + r:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y + r:.1f} V{y + bh - r:.1f} Q{x:.1f},{y + bh:.1f} {x + r:.1f},{y + bh:.1f} H{x0:.1f} Z"
            tx, anchor = x - 6, "end"
        sign = "+" if diverging and v > 0 else ""
        s.append(f'<g><title>{e(lab)}: {sign}{fmt(v, d)}{unit}{" – " + e(note) if note else ""}</title><path d="{path}" fill="{col}"/></g>'
                 f'<text x="{label_w - 10}" y="{y + bh - 3}" font-size="12" fill="var(--ink)" text-anchor="end">{e(lab)}</text>'
                 f'<text x="{tx:.1f}" y="{y + bh - 3}" font-size="12" font-weight="600" fill="var(--ink)" text-anchor="{anchor}">{sign}{fmt(v, d)}{unit}</text>')
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def stacked100(rows, cats, colors, w=640, row=46, label_w=230):
    """Barre 100% impilate. rows: [(etichetta, [valori in %], n)]."""
    h = row * len(rows) + 20
    s = [svg_open(w, h, "barre impilate")]
    span = w - label_w - 10
    for i, (lab, vals, n) in enumerate(rows):
        y = 8 + i * row
        x = label_w
        s.append(f'<text x="{label_w - 10}" y="{y + 14}" font-size="12" fill="var(--ink)" text-anchor="end">{e(lab)}</text>'
                 f'<text x="{label_w - 10}" y="{y + 28}" font-size="10" fill="var(--muted)" text-anchor="end">{n if isinstance(n, str) else f"{n} partite"}</text>')
        for j, v in enumerate(vals):
            bw = span * v / 100
            s.append(f'<g><title>{e(lab)} – {e(cats[j])}: {fmt(v)}%</title><rect x="{x:.1f}" y="{y}" width="{max(bw - 2, 0):.1f}" height="24" '
                     f'rx="{3 if j in (0, len(vals) - 1) else 0}" fill="{colors[j]}"/></g>')
            if bw > 44:
                s.append(f'<text x="{x + bw / 2 - 1:.1f}" y="{y + 16}" font-size="12" font-weight="600" fill="#fff" text-anchor="middle">{fmt(v, 0)}%</text>')
            x += bw
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def scatter(points, xlab, ylab, w=640, h=420, invert_y=False):
    """points: [(x, y, etichetta, evidenziato, tooltip)]."""
    pad_l, pad_r, pad_t, pad_b = 46, 16, 14, 40
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_lo, x_hi = 0, max(xs) * 1.08
    y_lo, y_hi = 0, max(ys) * 1.08
    X = lambda v: pad_l + (w - pad_l - pad_r) * (v - x_lo) / (x_hi - x_lo)
    Y = (lambda v: pad_t + (h - pad_t - pad_b) * (v - y_lo) / (y_hi - y_lo)) if invert_y else \
        (lambda v: pad_t + (h - pad_t - pad_b) * (1 - (v - y_lo) / (y_hi - y_lo)))
    s = [svg_open(w, h, f"{xlab} / {ylab}")]
    for k in range(0, 5):
        tx = x_hi * k / 4
        ty = y_hi * k / 4
        s.append(f'<line x1="{X(tx):.1f}" x2="{X(tx):.1f}" y1="{pad_t}" y2="{h - pad_b}" stroke="var(--grid)" stroke-width="1"/>'
                 f'<text x="{X(tx):.1f}" y="{h - pad_b + 14}" font-size="10" fill="var(--muted)" text-anchor="middle">{fmt(tx)}</text>'
                 f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(ty):.1f}" y2="{Y(ty):.1f}" stroke="var(--grid)" stroke-width="1"/>'
                 f'<text x="{pad_l - 6}" y="{Y(ty) + 3:.1f}" font-size="10" fill="var(--muted)" text-anchor="end">{fmt(ty)}</text>')
    s.append(f'<text x="{(pad_l + w - pad_r) / 2:.1f}" y="{h - 6}" font-size="11" fill="var(--muted)" text-anchor="middle">{e(xlab)}</text>'
             f'<text transform="translate(12,{(pad_t + h - pad_b) / 2:.1f}) rotate(-90)" font-size="11" fill="var(--muted)" text-anchor="middle">{e(ylab)}</text>')
    for x, y, lab, hi, tip in sorted(points, key=lambda p: p[3]):
        col = "var(--s1)" if hi else "var(--context)"
        s.append(f'<g><title>{e(tip)}</title><circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="10" fill="transparent"/>'
                 f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{5 if hi else 4}" fill="{col}" stroke="var(--surface)" stroke-width="2"/></g>')
    # etichette delle squadre evidenziate: colonna nella zona vuota in alto a sinistra, con linea guida fino al punto
    hls = sorted([p for p in points if p[3]], key=lambda p: Y(p[1]))
    lx = pad_l + 8
    placed = []
    for x, y, lab, hi, tip in hls:
        ly = max(Y(y), (placed[-1] + 17) if placed else pad_t + 10)
        placed.append(ly)
        tw = 6.4 * len(lab)
        s.append(f'<line x1="{lx + tw + 4:.1f}" y1="{ly:.1f}" x2="{X(x) - 6:.1f}" y2="{Y(y):.1f}" stroke="var(--axis)" stroke-width="1"/>'
                 f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-size="11.5" fill="var(--ink)">{e(lab)}</text>')
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def slope(left, right, names, title_l, title_r, hl, w=640, row=26):
    """Slope chart tra due classifiche. left/right: {squadra: posizione}."""
    n = len(names)
    h = row * n + 50
    xl, xr = 230, w - 230
    Y = lambda p: 34 + (p - 1) * row
    s = [svg_open(w, h, f"{title_l} / {title_r}"),
         f'<text x="{xl}" y="16" font-size="12" font-weight="600" fill="var(--muted)" text-anchor="middle">{e(title_l)}</text>'
         f'<text x="{xr}" y="16" font-size="12" font-weight="600" fill="var(--muted)" text-anchor="middle">{e(title_r)}</text>']
    for t in names:
        a, b = left[t], right[t]
        col = "var(--s1)" if t in hl else "var(--context)"
        sw = 2.5 if t in hl else 1.5
        fw = ' font-weight="700"' if t in hl else ""
        s.append(f'<g><title>{e(t)}: {a}° reale, {b}° per punti attesi</title>'
                 f'<line x1="{xl}" y1="{Y(a)}" x2="{xr}" y2="{Y(b)}" stroke="{col}" stroke-width="{sw}"/>'
                 f'<circle cx="{xl}" cy="{Y(a)}" r="4.5" fill="{col}" stroke="var(--surface)" stroke-width="2"/>'
                 f'<circle cx="{xr}" cy="{Y(b)}" r="4.5" fill="{col}" stroke="var(--surface)" stroke-width="2"/></g>'
                 f'<text x="{xl - 12}" y="{Y(a) + 4}" font-size="12" fill="var(--ink)" text-anchor="end"{fw}>{a}. {e(t)}</text>'
                 f'<text x="{xr + 12}" y="{Y(b) + 4}" font-size="12" fill="var(--ink)"{fw}>{b}. {e(t)}</text>')
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def svg_tiles(tiles, w=640, h=130):
    tw = (w - 16 * (len(tiles) - 1)) / len(tiles)
    s = [svg_open(w, h, "riquadri")]
    for i, (lab, val, sub1, sub2) in enumerate(tiles):
        x = i * (tw + 16)
        s.append(f'<rect x="{x:.1f}" y="1" width="{tw:.1f}" height="{h - 2}" rx="10" fill="none" stroke="var(--line)"/>'
                 f'<text x="{x + 16:.1f}" y="24" font-size="13" fill="var(--muted)">{e(lab)}</text>'
                 f'<text x="{x + 16:.1f}" y="72" font-size="44" font-weight="650" fill="var(--ink)">{e(val)}</text>'
                 f'<text x="{x + 16:.1f}" y="96" font-size="13" fill="var(--ink2)">{e(sub1)}</text>'
                 f'<text x="{x + 16:.1f}" y="116" font-size="13" font-weight="600" fill="var(--ink2)">{e(sub2)}</text>')
    s.append("</svg>")
    return "".join(s)


def legend(items):
    return '<div class="lg">' + "".join(
        f'<span><svg viewBox="0 0 14 14" width="14" height="14"><rect x="1" y="1" width="12" height="12" rx="3" fill="{c}"/></svg>{e(t)}</span>'
        for c, t in items) + "</div>"


def table(head, rows):
    th = "".join(f"<th>{e(x)}</th>" for x in head)
    tr = "".join("<tr>" + "".join(f"<td>{e(x)}</td>" for x in r) + "</tr>" for r in rows)
    return f'<details class="tview"><summary>Tabella dei dati</summary><div class="scroll"><table>{th and "<tr>" + th + "</tr>"}{tr}</table></div></details>'


# ------------------------------------------------------------------------------------------- studi
def eras_study(T, SH):
    def era(d):
        y = int(d[:4])
        return 0 if y < 1991 else 1 if y < 2010 else 2 if y < 2020 else 3
    labels = ["1958–90", "1991–2009", "2010–19", "2020–25"]
    rows = [[] for _ in labels]
    for r in T:
        if not is_f(r["competizione"]):
            rows[era(r["data"])].append(r)
    shots = [[] for _ in labels]
    for s_ in SH:
        if not is_f(s_["competizione"]) and s_["tipo"] != "Penalty":
            shots[era(s_["data"])].append(s_)
    ns = [len(r) // 2 for r in rows]
    mean = lambda rs, k: sum(num(r[k]) for r in rs) / len(rs)
    outside = lambda ss: 100 * sum(num(x["x"]) < 102 or not (18 <= num(x["y"]) <= 62) for x in ss) / len(ss)
    panels = [
        ("Dribbling tentati (per squadra)", [mean(r, "dribbling") for r in rows], 1, ""),
        ("Passaggi per azione", [mean(r, "passaggi_per_possesso") for r in rows], 2, ""),
        ("Azioni da 10+ passaggi", [mean(r, "sequenze_10_passaggi") for r in rows], 1, ""),
        ("Passaggi in avanti", [mean(r, "passaggi_avanti_pct") for r in rows], 1, "%"),
        ("Tiri da fuori area", [outside(s_) for s_ in shots], 1, "%"),
        ("Falli commessi (per squadra)", [mean(r, "falli") for r in rows], 1, ""),
    ]
    chart = '<div class="sm">' + "".join(line_panel(t, labels, v, ns, d, u) for t, v, d, u in panels) + "</div>"
    tab = table(["Metrica"] + labels, [[t] + [fmt(x, d) + u for x in v] for t, v, d, u in panels] +
                [["Partite"] + [str(n) for n in ns], ["Tiri (senza rigori)"] + [str(len(s_)) for s_ in shots]])
    v = dict((t, vals) for t, vals, _, _ in panels)
    return dict(
        id="epoche", kicker="Come è cambiato il calcio", title="Meno dribbling, più pazienza: 60 anni di calcio maschile",
        headline=f"I dribbling tentati sono scesi da {fmt(v['Dribbling tentati (per squadra)'][0])} a {fmt(v['Dribbling tentati (per squadra)'][3])} "
                 f"a squadra, le azioni da 10+ passaggi sono passate da {fmt(v['Azioni da 10+ passaggi'][0])} a {fmt(v['Azioni da 10+ passaggi'][3])} e solo il {fmt(v['Passaggi in avanti'][3], 0)}% dei passaggi oggi va in avanti.",
        chart=chart, legend="",
        body=["La palla oggi si sposta passando, non portandola: meno dribbling, azioni più lunghe, passaggi meno verticali.",
              "Si tira meno da lontano (dal " + fmt(v["Tiri da fuori area"][0], 0) + "% al " + fmt(v["Tiri da fuori area"][3], 0) +
              "% dei tiri da fuori area) e si fanno meno falli."],
        method="Medie per squadra a partita, solo calcio maschile. Dribbling = tentativi di saltare l'avversario. Passaggi per azione = "
               "passaggi diviso possessi. Passaggio in avanti = guadagna più di 2 yard verso la porta. Tiri da fuori area esclusi i rigori.",
        caveat=f"Prima del 1991 ci sono solo {ns[0]} partite (soprattutto finali e partite storiche dei Mondiali ricostruite da video) e il mix "
               f"di competizioni cambia tra le epoche (molta Liga 2004–2021, i 4 grandi campionati 2015/16, tornei per nazionali dal 2018). "
               f"Il trend è coerente in tutte le metriche, ma i valori del primo periodo sono indicativi.",
        table=tab)


def worldcup_study(T):
    ed = defaultdict(list)
    for r in T:
        if r["competizione"] == "FIFA World Cup":
            ed[r["stagione"]].append(r)
    years = sorted(ed)
    drib = [sum(num(r["dribbling"]) for r in ed[y]) / len(ed[y]) for y in years]
    seq = [sum(num(r["sequenze_10_passaggi"]) for r in ed[y]) / len(ed[y]) for y in years]
    ns = [len(ed[y]) // 2 for y in years]
    chart = columns(years, [("Dribbling tentati", "var(--s1)", drib), ("Azioni da 10+ passaggi", "var(--s2)", seq)], d=1, w=640, h=300)
    tab = table(["Edizione", "Partite nel dataset", "Dribbling tentati", "Azioni 10+ passaggi"],
                [[y, n, fmt(a), fmt(b)] for y, n, a, b in zip(years, ns, drib, seq)])
    return dict(
        id="mondiali", kicker="Come è cambiato il calcio", title="Mondiali 1958–2022: le due curve che si incrociano",
        headline=f"Nel 1958 una squadra tentava {fmt(drib[0], 0)} dribbling e faceva {fmt(seq[0])} azioni da 10+ passaggi a partita; "
                 f"nel 2022 i dribbling sono {fmt(drib[-1], 0)}, le azioni lunghe {fmt(seq[-1])}.",
        chart=chart, legend=legend([("var(--s1)", "Dribbling tentati (per squadra)"), ("var(--s2)", "Azioni da 10+ passaggi (per squadra)")]),
        body=["Lo stesso torneo, a distanza di 64 anni: la conduzione individuale lascia il posto al possesso costruito."],
        method="Medie per squadra a partita in ogni edizione dei Mondiali presente nel dataset.",
        caveat="Dal 1958 al 1990 il dataset ha da 1 a 6 partite per edizione (vedi tabella): sono tendenze, non medie di torneo. "
               "2018 e 2022 sono completi (64 partite ciascuno).",
        table=tab)


def gender_style_study(T):
    m = [r for r in T if not is_f(r["competizione"]) and int(r["data"][:4]) >= 2018]
    f = [r for r in T if is_f(r["competizione"])]
    keys = [("Pressioni", "pressioni"), ("Possessi", "possessi"), ("Dribbling tentati", "dribbling"), ("Cross", "cross"),
            ("Tiri", "tiri"), ("xG per tiro", "xg_per_tiro"), ("Passaggi", "passaggi"), ("Precisione passaggi", "precisione_passaggi_pct"),
            ("Passaggi per azione", "passaggi_per_possesso"), ("Falli", "falli"), ("Ammonizioni", "gialli")]
    rows = []
    for lab, k in keys:
        a = sum(num(r[k]) for r in m) / len(m)
        b = sum(num(r[k]) for r in f) / len(f)
        rows.append((lab, 100 * (b - a) / a, a, b))
    rows.sort(key=lambda x: -x[1])
    dd = {lab: d for lab, d, _, _ in rows}
    items = [(lab, d, "var(--s2)" if d >= 0 else "var(--s1)", f"maschile {fmt(a, 2)}, femminile {fmt(b, 2)}") for lab, d, a, b in rows]
    chart = hbars(items, d=1, unit="%", diverging=True, label_w=180)
    tab = table(["Metrica (per squadra a partita)", "Maschile", "Femminile", "Differenza"],
                [[lab, fmt(a, 2), fmt(b, 2), ("+" if d > 0 else "") + fmt(d) + "%"] for lab, d, a, b in rows])
    return dict(
        id="stile", kicker="Maschile e femminile", title="Più pressing, meno falli: due modi di giocare",
        headline=f"Il calcio femminile ha il {fmt(dd['Pressioni'], 0)}% di pressioni e il {fmt(dd['Possessi'], 0)}% di possessi in più, "
                 f"azioni più corte ({fmt(dd['Passaggi per azione'], 0)}% di passaggi per azione) e il {fmt(-dd['Falli'], 0)}% di falli in meno. "
                 f"La qualità media dei tiri è quasi identica ({'+' if dd['xG per tiro'] > 0 else ''}{fmt(dd['xG per tiro'])}% di xG per tiro).",
        chart=chart, legend=legend([("var(--s2)", "Più alto nel femminile"), ("var(--s1)", "Più alto nel maschile")]),
        body=["Partite più spezzate e di transizione: più cambi di possesso, più pressione sulla palla, meno passaggi per azione.",
              f"Meno contatti puniti: falli {fmt(dd['Falli'], 0)}%, ammonizioni {fmt(dd['Ammonizioni'], 0)}%."],
        method=f"Confronto sullo stesso periodo: {len(m) // 2} partite maschili dal 2018 e {len(f) // 2} femminili (2018–2025). "
               "Differenza percentuale del valore femminile rispetto al maschile.",
        caveat="Le competizioni non sono le stesse (maschile: tornei per nazionali, MLS, Bundesliga, Ligue 1 2021–23, India; femminile: "
               "campionati inglese, spagnolo, tedesco, italiano, NWSL e tornei). Lo stile dipende anche dal livello delle squadre.",
        table=tab)


def gender_skill_study(SH):
    def grp(c):
        return [s_ for s_ in SH if c(s_)]
    M = grp(lambda s_: not is_f(s_["competizione"]) and int(s_["data"][:4]) >= 2018)
    F = grp(lambda s_: is_f(s_["competizione"]))
    def stats(ss):
        on = [x for x in ss if x["tipo"] != "Penalty" and x["esito"] in ("Goal", "Saved", "Saved To Post")]
        sv = sum(x["esito"] != "Goal" for x in on)
        np_ = [x for x in ss if x["tipo"] != "Penalty"]
        g = sum(x["gol"] == "1" for x in np_)
        pen = [x for x in ss if x["tipo"] == "Penalty"]
        pg = sum(x["gol"] == "1" for x in pen)
        return [(100 * sv / len(on), wilson(sv, len(on)), len(on)), (100 * g / len(np_), wilson(g, len(np_)), len(np_)),
                (100 * pg / len(pen), wilson(pg, len(pen)), len(pen))]
    a, b = stats(M), stats(F)
    cats = ["Parate sui tiri in porta", "Tiri trasformati in gol", "Rigori segnati"]
    chart = columns(cats, [("Maschile", "var(--s1)", [x[0] for x in a], [x[1] for x in a]),
                           ("Femminile", "var(--s2)", [x[0] for x in b], [x[1] for x in b])], d=1, unit="%", ci=True, ymax=100)
    tab = table(["Misura", "Maschile", "IC 95%", "Tentativi", "Femminile", "IC 95%", "Tentativi"],
                [[c, fmt(x[0]) + "%", f"{fmt(x[1][0])}–{fmt(x[1][1])}%", x[2], fmt(y[0]) + "%", f"{fmt(y[1][0])}–{fmt(y[1][1])}%", y[2]]
                 for c, x, y in zip(cats, a, b)])
    return dict(
        id="portieri", kicker="Maschile e femminile", title="Le portiere parano come i portieri",
        headline=f"Parate sui tiri in porta: {fmt(a[0][0])}% nel maschile, {fmt(b[0][0])}% nel femminile. Anche gol per tiro e rigori sono "
                 f"praticamente identici.",
        chart=chart, legend=legend([("var(--s1)", "Maschile (dal 2018)"), ("var(--s2)", "Femminile")]),
        body=["Uno dei luoghi comuni più ripetuti non regge ai numeri: su migliaia di tiri, la percentuale di parate è la stessa.",
              "Le barre nere sono l'intervallo di confidenza al 95%: dove si sovrappongono, la differenza non è distinguibile dal caso."],
        method="Tiri in porta = gol + parati (anche sul palo), rigori esclusi. Gol per tiro su tutti i tiri non su rigore. Rigori in partita "
               "(esclusi quelli delle serie finali). Intervalli di Wilson al 95%.",
        caveat="Il dato non misura la difficoltà dei tiri in porta (serve un modello post-tiro, non disponibile negli Open Data). "
               "Gli xG medi dei gol sono comunque quasi uguali (0,246 contro 0,249).",
        table=tab)


def olympic_study(SH, T):
    valid = {r["n"] for r in T}
    goals = [s_ for s_ in SH if s_["gol"] == "1" and s_["tipo"] == "Corner" and s_["n"] in valid]
    mm = sum(1 for r in T if not is_f(r["competizione"])) // 2
    ff = sum(1 for r in T if is_f(r["competizione"])) // 2
    gm = [x for x in goals if not is_f(x["competizione"])]
    gf = [x for x in goals if is_f(x["competizione"])]
    rm, rf = 100 * len(gm) / mm, 100 * len(gf) / ff
    tiles = svg_tiles([("Femminile", str(len(gf)), f"gol olimpici in {ff} partite", f"{fmt(rf, 2)} ogni 100 partite"),
                       ("Maschile", str(len(gm)), f"gol olimpici in {mm} partite", f"{fmt(rm, 2)} ogni 100 partite")])
    chart = columns(["Gol olimpici ogni 100 partite"], [("Maschile", "var(--s1)", [rm]), ("Femminile", "var(--s2)", [rf])], d=2, w=640, h=230)
    tab = table(["Data", "Giocatrice / giocatore", "Squadra", "Competizione", "Partita n."],
                [[x["data"], x["giocatore"], x["squadra"], x["competizione"], x["n"]] for x in sorted(goals, key=lambda x: x["data"])])
    return dict(
        id="olimpici", kicker="Maschile e femminile", title="Il gol olimpico è (quasi) femminile",
        headline=f"{len(gf)} gol direttamente da calcio d'angolo nel femminile contro {len(gm)} nel maschile, con metà delle partite: "
                 f"circa {fmt(rf / rm, 0)} volte più frequente.",
        chart=tiles + chart, legend=legend([("var(--s1)", "Maschile"), ("var(--s2)", "Femminile")]),
        body=["Chloe Kelly ne ha segnati due (2020 e 2024). Quattro sono arrivati in Frauen Bundesliga tra il 17 marzo e il 20 aprile 2024."],
        method="Gol su tiro classificato da StatsBomb come calcio d'angolo diretto, rapportati al numero di partite del dataset.",
        caveat="Sono pochi eventi (18 in tutto): il rapporto è indicativo e ha un margine d'errore ampio. Possibili spiegazioni (porte "
               "della stessa misura con portiere mediamente più basse, traiettorie a rientrare) vanno verificate, non sono nei dati.",
        table=tab)


def timing_study(K):
    bands = ["0–15'", "15–30'", "30–45'", "Recupero 1° t.", "45–60'", "60–75'", "75–90'", "Recupero 2° t.", "Suppl."]
    def band(r):
        m, p = int(r["minuto"]), int(r["periodo"])
        if p == 1:
            return 3 if m >= 45 else min(m // 15, 2)
        if p == 2:
            return 7 if m >= 90 else 4 + min((m - 45) // 15, 2)
        return 8
    G = [r for r in K if r["tipo"] in ("Gol", "Gol su rigore", "Autogol")]
    res = {}
    for g in ("M", "F"):
        c = Counter(band(r) for r in G if ("F" if is_f(r["competizione"]) else "M") == g)
        tot = sum(c.values())
        res[g] = ([100 * c[i] / tot for i in range(9)], tot)
    chart = columns(bands, [("Maschile", "var(--s1)", res["M"][0]), ("Femminile", "var(--s2)", res["F"][0])], d=1, unit="%", w=720, h=300,
                    label_all=False)
    last = lambda g: res[g][0][6] + res[g][0][7]
    tab = table(["Fascia", "Maschile %", "Femminile %"], [[b, fmt(x), fmt(y)] for b, x, y in zip(bands, res["M"][0], res["F"][0])] +
                [["Gol totali", res["M"][1], res["F"][1]]])
    return dict(
        id="minuti", kicker="Partite", title="Quando si segna: il gol arriva nel finale",
        headline=f"Dal 75' alla fine (recupero compreso) arriva il {fmt(last('M'))}% dei gol nel maschile e il {fmt(last('F'))}% nel femminile; "
                 f"il recupero del secondo tempo da solo vale il {fmt(res['M'][0][7])}% e il {fmt(res['F'][0][7])}%.",
        chart=chart, legend=legend([("var(--s1)", "Maschile"), ("var(--s2)", "Femminile")]),
        body=[f"Il secondo tempo produce più gol del primo in entrambi i calci ({fmt(sum(res['M'][0][4:8]), 0)}% contro "
              f"{fmt(sum(res['M'][0][0:4]), 0)}% nel maschile, {fmt(sum(res['F'][0][4:8]), 0)}% contro {fmt(sum(res['F'][0][0:4]), 0)}% nel femminile). "
              f"Nel maschile i primi 15 minuti sono la fascia regolare meno prolifica ({fmt(res['M'][0][0])}%)."],
        method=f"Tutti i gol del dataset (compresi rigori e autogol, esclusi i rigori delle serie finali): {res['M'][1]} maschili e {res['F'][1]} "
               "femminili. Le fasce di recupero sono separate: non durano 15 minuti, vanno lette come blocchi a sé.",
        caveat="Le fasce del recupero hanno durata variabile e il dato del recupero non è normalizzato per minuto.",
        table=tab)


FULL = {("La Liga", "2015/2016"), ("Ligue 1", "2015/2016"), ("Premier League", "2015/2016"), ("Serie A", "2015/2016")}
# per i punti attesi servono stagioni complete E con gli eventi di tutte le partite (in Ligue 1 2015/16 mancano quelli di Marsiglia e Caen)
FULL_EVENTS = {("La Liga", "2015/2016"), ("Premier League", "2015/2016"), ("Serie A", "2015/2016")}


def bad_matches(T, K):
    """Partite in cui a una squadra mancano gli eventi nella fonte: 0 passaggi oppure gol degli eventi diversi dal risultato."""
    opp = {(r["n"], r["squadra"]): r["avversario"] for r in T}
    g = Counter()
    for k in K:
        if k["tipo"] in ("Gol", "Gol su rigore"):
            g[(k["n"], k["squadra"])] += 1
        elif k["tipo"] == "Autogol":
            g[(k["n"], opp.get((k["n"], k["squadra"])))] += 1
    return {r["n"] for r in T if g[(r["n"], r["squadra"])] != int(num(r["gol"])) or num(r["passaggi"]) == 0}
FULL_F = {("FA Women's Super League (F)", "2018/2019"), ("FA Women's Super League (F)", "2019/2020"), ("FA Women's Super League (F)", "2020/2021"),
          ("FA Women's Super League (F)", "2023/2024"), ("Frauen Bundesliga (F)", "2023/2024"), ("Liga F (F)", "2023/2024"),
          ("NWSL (F)", "2023"), ("Serie A Women (F)", "2023/2024")}


def home_study(T):
    def shares(rows):
        n = len(rows)
        v = sum(r["esito"] == "V" for r in rows)
        p = sum(r["esito"] == "P" for r in rows)
        return [100 * v / n, 100 * (n - v - p) / n, 100 * p / n], n, wilson(v, n), wilson(p, n)
    home = [r for r in T if r["casa_trasferta"] == "casa"]
    m = [r for r in home if (r["competizione"], r["stagione"]) in FULL]
    f = [r for r in home if (r["competizione"], r["stagione"]) in FULL_F]
    sm, nm, cm_v, cm_p = shares(m)
    sf, nf, cf_v, cf_p = shares(f)
    gm = (sum(num(r["gol"]) for r in m) / nm, sum(num(r["gol_subiti"]) for r in m) / nm)
    gf = (sum(num(r["gol"]) for r in f) / nf, sum(num(r["gol_subiti"]) for r in f) / nf)
    chart = stacked100([("Maschile – 4 campionati 2015/16", sm, nm), ("Femminile – 8 campionati completi", sf, nf)],
                       ["Vittoria in casa", "Pareggio", "Vittoria in trasferta"], ["var(--s1)", "var(--neutral)", "var(--s2)"])
    tab = table(["Campione", "Partite", "Vittoria in casa", "Pareggio", "Vittoria in trasferta", "Gol casa", "Gol ospiti"],
                [["Maschile (Liga, Premier, Serie A, Ligue 1 2015/16)", nm] + [fmt(x) + "%" for x in sm] + [fmt(gm[0], 2), fmt(gm[1], 2)],
                 ["Femminile (WSL, Liga F, Frauen BL, Serie A, NWSL)", nf] + [fmt(x) + "%" for x in sf] + [fmt(gf[0], 2), fmt(gf[1], 2)]])
    return dict(
        id="casa", kicker="Maschile e femminile", title="Il fattore campo pesa molto meno nel femminile",
        headline=f"Nel maschile chi gioca in casa vince il {fmt(sm[0])}% delle volte e perde il {fmt(sm[2])}% (+{fmt(sm[0] - sm[2])} punti); "
                 f"nel femminile il distacco è di appena +{fmt(sf[0] - sf[2])} punti ({fmt(sf[0])}% contro {fmt(sf[2])}%).",
        chart=chart, legend=legend([("var(--s1)", "Vittoria in casa"), ("var(--neutral)", "Pareggio"), ("var(--s2)", "Vittoria in trasferta")]),
        body=[f"Nel femminile ci sono anche molti meno pareggi ({fmt(sf[1])}% contro {fmt(sm[1])}%): partite più spesso decise, "
              "spesso per il maggiore divario tra le squadre di uno stesso campionato."],
        method="Solo campionati completi (tutte le partite della stagione), così il confronto non dipende da quali partite sono state scelte. "
               f"Intervalli al 95% della vittoria in casa: maschile {fmt(cm_v[0])}–{fmt(cm_v[1])}%, femminile {fmt(cf_v[0])}–{fmt(cf_v[1])}%.",
        caveat="Pubblico, distanze e strutture sono molto diversi tra i due calci: il dato descrive la differenza, non ne spiega la causa. "
               "Nella WSL 2020/21 a porte chiuse il distacco era zero, ma lo era anche nelle stagioni con pubblico del nostro campione.",
        table=tab)


def possession_study(T, n_anom=0):
    b = defaultdict(lambda: [0, 0, 0, 0.0])
    for r in T:
        if is_f(r["competizione"]):
            continue
        p = num(r["possesso_pct"])
        k = max(30, min(int(p // 10) * 10, 70))
        x = b[k]
        x[0] += 1; x[1] += r["esito"] == "V"; x[2] += r["esito"] == "P"; x[3] += num(r["xg"])
    keys = sorted(b)
    labs = [f"{k}–{k + 10}%" if k not in (30, 70) else ("< 40%" if k == 30 else "≥ 70%") for k in keys]
    win = [100 * b[k][1] / b[k][0] for k in keys]
    cis = [wilson(b[k][1], b[k][0]) for k in keys]
    chart = columns(labs, [("Vittorie", "var(--s1)", win, cis)], d=0, unit="%", ci=True, ymax=70, h=280)
    tab = table(["Possesso", "Partite", "Vittorie", "IC 95%", "Sconfitte", "xG medi"],
                [[l, b[k][0], fmt(w) + "%", f"{fmt(c[0])}–{fmt(c[1])}%", fmt(100 * b[k][2] / b[k][0]) + "%", fmt(b[k][3] / b[k][0], 2)]
                 for l, k, w, c in zip(labs, keys, win, cis)])
    return dict(
        id="possesso", kicker="Partite", title="Il possesso aiuta, ma meno di quanto si pensi",
        headline=f"Chi tiene la palla per oltre il 70% del tempo vince il {fmt(win[-1], 0)}% delle partite: in {fmt(100 - win[-1], 0)} casi su 100 "
                 f"non vince. Sotto il 40% si vince comunque il {fmt(win[0], 0)}% delle volte.",
        chart=chart, legend="",
        body=["La relazione esiste ed è chiara (più possesso, più xG, più vittorie), ma è molto meno netta di quanto suggerisca il dibattito "
              "sul 'tiki-taka'."],
        method="Tutte le partite maschili, per squadra; possesso = quota del tempo di possesso. Barre: percentuale di vittorie; linee: "
               f"intervallo di confidenza al 95%. Escluse {n_anom} partite con possesso anomalo nella fonte.",
        caveat="Il possesso dipende anche dal risultato: chi è in vantaggio spesso lascia la palla all'avversario. Il dataset contiene "
               "moltissime partite del Barcellona, che alza la quota di vittorie nelle fasce di possesso alte.",
        table=tab)


def poisson(l, k):
    return math.exp(-l) * l ** k / math.factorial(k)


def xpts(a, b):
    pw = pd = 0.0
    for i in range(12):
        for j in range(12):
            p = poisson(a, i) * poisson(b, j)
            if i > j:
                pw += p
            elif i == j:
                pd += p
    return 3 * pw + pd


def season_tables(T):
    tabs = defaultdict(lambda: defaultdict(lambda: [0, 0.0, 0, 0.0, 0.0, 0, 0]))
    for r in T:
        k = (r["competizione"], r["stagione"])
        if k not in FULL_EVENTS:
            continue
        a = tabs[k][r["squadra"]]
        a[0] += 3 if r["esito"] == "V" else 1 if r["esito"] == "N" else 0
        a[1] += xpts(num(r["xg"]), num(r["xg_subiti"]))
        a[2] += 1
        a[3] += num(r["xg"]); a[4] += num(r["xg_subiti"]); a[5] += int(num(r["gol"])); a[6] += int(num(r["gol_subiti"]))
    return tabs


def luck_study(tabs):
    allr = [(a[0] - a[1], t, k, a) for k, tb in tabs.items() for t, a in tb.items()]
    allr.sort(key=lambda x: -x[0])
    sel = allr[:7] + allr[-7:]
    short = {"Premier League": "Premier", "Serie A": "Serie A", "La Liga": "Liga", "Ligue 1": "Ligue 1"}
    items = [(f"{t} ({short[k[0]]})", d, "var(--s1)" if d >= 0 else "var(--neg)", f"punti {a[0]}, attesi {fmt(a[1])}") for d, t, k, a in sel]
    chart = hbars(items, d=1, unit=" pt", diverging=True, label_w=230)
    tab = table(["Squadra", "Campionato", "Punti", "Punti attesi", "Differenza", "Gol fatti-subiti", "xG fatti-subiti"],
                [[t, k[0], a[0], fmt(a[1]), ("+" if d > 0 else "") + fmt(d), f"{a[5]}-{a[6]}", f"{fmt(a[3])}-{fmt(a[4])}"] for d, t, k, a in allr])
    top, bot = allr[0], allr[-1]
    return dict(
        id="fortuna", kicker="Squadre", title="La stagione della fortuna: Liga, Premier e Serie A 2015/16",
        headline=f"{top[1]} ha fatto {fmt(top[0], 0)} punti più di quanto valessero le sue occasioni, {bot[1]} {fmt(-bot[0], 0)} in meno. "
                 f"Nell'elenco dei più fortunati ci sono anche Leicester (campione) e Roma.",
        chart=chart, legend=legend([("var(--s1)", "Più punti del previsto"), ("var(--neg)", "Meno punti del previsto")]),
        body=["I punti attesi stimano quanti punti 'valeva' ogni partita in base alle occasioni create e concesse (xG). La differenza misura "
              "efficacia sotto porta, parate decisive e fortuna: in una stagione possono valere 15–20 punti."],
        method="Per ogni partita: probabilità di vittoria, pareggio e sconfitta da due distribuzioni di Poisson con media pari agli xG delle "
               "due squadre; punti attesi = 3 × P(vittoria) + P(pareggio), sommati sulla stagione. Le 3 stagioni sono complete e con tutti gli "
               "eventi (1.140 partite). La Ligue 1 2015/16 è esclusa: nella fonte mancano gli eventi di Marsiglia e Caen in 15 partite.",
        caveat="È il metodo standard ma semplificato: tratta i gol delle due squadre come indipendenti e usa gli xG senza distinguere rigori "
               "e situazioni di punteggio. Le squadre forti tendono a superare un po' gli xG per qualità dei loro attaccanti.",
        table=tab)


def leicester_study(tabs, T):
    tb = tabs[("Premier League", "2015/2016")]
    real = sorted(tb, key=lambda t: (-tb[t][0], -(tb[t][5] - tb[t][6])))
    exp = sorted(tb, key=lambda t: -tb[t][1])
    names = real[:8]
    left = {t: i + 1 for i, t in enumerate(real)}
    right = {t: i + 1 for i, t in enumerate(exp)}
    chart = slope(left, right, names, "Classifica reale", "Classifica per punti attesi", {"Leicester City"})
    a = tb["Leicester City"]
    ars = tb["Arsenal"]
    lr = [r for r in T if r["squadra"] == "Leicester City" and r["stagione"] == "2015/2016"]
    lei_poss = sum(num(r["possesso_pct"]) for r in lr) / len(lr)
    tab = table(["Squadra", "Pos. reale", "Punti", "Pos. punti attesi", "Punti attesi", "xG fatti", "xG subiti"],
                [[t, left[t], tb[t][0], right[t], fmt(tb[t][1]), fmt(tb[t][3]), fmt(tb[t][4])] for t in real])
    return dict(
        id="leicester", kicker="Squadre", title="Leicester 2015/16, il miracolo che gli xG non vedevano",
        headline=f"Campione con {a[0]} punti, ma per le occasioni create e concesse valeva {fmt(a[1], 0)} punti: sarebbe arrivato "
                 f"{right['Leicester City']}°. La squadra migliore per punti attesi era l'Arsenal ({fmt(ars[1], 0)}).",
        chart=chart, legend=legend([("var(--s1)", "Leicester City"), ("var(--context)", "Altre squadre (prime 8 reali)")]),
        body=[f"In attacco il Leicester è in linea con le attese ({a[5]} gol da {fmt(a[3])} xG). La differenza è in difesa: {a[6]} gol "
              f"subiti contro {fmt(a[4])} xG concessi, cioè {fmt(a[4] - a[6], 0)} gol in meno del previsto, con il {fmt(lei_poss, 0)}% di possesso medio."],
        method="Punti attesi calcolati partita per partita dagli xG (modello di Poisson, vedi studio 'La stagione della fortuna'). "
               "Stagione completa: 380 partite.",
        caveat="Gli xG non misurano tutto: la qualità di portiere e difensori nel ridurre la pericolosità dei tiri subiti non è nel modello. "
               "Il dato dice quanto il titolo sia stato eccezionale, non che sia stato immeritato.",
        table=tab)


def legends_study(T):
    ts = defaultdict(lambda: defaultdict(float))
    for r in T:
        k = (r["squadra"], r["competizione"], r["stagione"])
        a = ts[k]
        a["g"] += 1
        a["pts"] += 3 if r["esito"] == "V" else 1 if r["esito"] == "N" else 0
        for x in ("xg", "xg_subiti", "possesso_pct", "field_tilt_pct", "gol", "gol_subiti"):
            a[x] += num(r[x])
    hl = {("Barcelona WFC", "Liga F (F)", "2023/2024"): "Barcellona F 2023/24",
          ("Bayer Leverkusen", "1. Bundesliga", "2023/2024"): "Leverkusen 2023/24",
          ("Barcelona", "La Liga", "2008/2009"): "Barcellona 2008/09",
          ("Arsenal", "Premier League", "2003/2004"): "Arsenal 2003/04",
          ("Leicester City", "Premier League", "2015/2016"): "Leicester 2015/16",
          ("Paris Saint-Germain", "Ligue 1", "2015/2016"): "PSG 2015/16",
          ("Juventus", "Serie A", "2015/2016"): "Juventus 2015/16",
          ("Chelsea FCW", "FA Women's Super League (F)", "2023/2024"): "Chelsea F 2023/24"}
    pts = []
    for k, a in ts.items():
        if a["g"] < 20:
            continue
        g = a["g"]
        lab = hl.get(k, f"{k[0]} {k[2]}")
        pts.append((a["xg"] / g, a["xg_subiti"] / g, lab, k in hl,
                    f"{k[0]} – {k[1]} {k[2]}: {int(g)} partite, xG {fmt(a['xg'] / g, 2)} fatti e {fmt(a['xg_subiti'] / g, 2)} subiti a partita, "
                    f"{fmt(a['pts'] / g, 2)} punti a partita, field tilt {fmt(a['field_tilt_pct'] / g, 0)}%"))
    chart = scatter(pts, "xG creati a partita", "xG concessi a partita (in alto = meno)", invert_y=True)
    rows = sorted([(k, a) for k, a in ts.items() if k in hl], key=lambda kv: -(kv[1]["xg"] - kv[1]["xg_subiti"]) / kv[1]["g"])
    tab = table(["Squadra", "Partite", "Punti/partita", "xG fatti", "xG subiti", "Possesso", "Field tilt"],
                [[hl[k], int(a["g"]), fmt(a["pts"] / a["g"], 2), fmt(a["xg"] / a["g"], 2), fmt(a["xg_subiti"] / a["g"], 2),
                  fmt(a["possesso_pct"] / a["g"], 0) + "%", fmt(a["field_tilt_pct"] / a["g"], 0) + "%"] for k, a in rows])
    bw = ts[("Barcelona WFC", "Liga F (F)", "2023/2024")]
    ar = ts[("Arsenal", "Premier League", "2003/2004")]
    return dict(
        id="leggende", kicker="Squadre", title="Le squadre più dominanti del dataset",
        headline=f"Il Barcellona femminile 2023/24 è un caso a parte: {fmt(bw['xg'] / bw['g'], 2)} xG creati e {fmt(bw['xg_subiti'] / bw['g'], 2)} "
                 f"concessi a partita, con l'{fmt(bw['field_tilt_pct'] / bw['g'], 0)}% dei passaggi nell'ultimo terzo di campo.",
        chart=chart, legend=legend([("var(--s1)", "Squadre citate"), ("var(--context)", "Altre stagioni con almeno 20 partite")]),
        body=[f"Gli Invincibili dell'Arsenal 2003/04 non dominavano il territorio: field tilt medio del {fmt(ar['field_tilt_pct'] / ar['g'], 0)}% "
              "(meno della metà del gioco offensivo) e 1,60 xG a partita. Erano una squadra di efficacia e ripartenze, non di dominio."],
        method="Ogni punto è una squadra in una stagione con almeno 20 partite nel dataset. Field tilt = quota dei passaggi nel terzo "
               "offensivo rispetto all'avversario.",
        caveat="Le stagioni del Barcellona maschile e di poche altre squadre sono presenti quasi solo per quella squadra: avversari diversi "
               "per livello, maschile e femminile insieme. Il grafico confronta il dominio relativo al proprio campionato.",
        table=tab)


def finishing_study(C):
    pool = [r for r in C if num(r["tiri"]) >= 40]
    s = sorted(pool, key=lambda r: -num(r["finalizzazione"]))
    sel = s[:8] + s[-8:]
    name = lambda r: (r["soprannome"] or r["giocatore"]) + (" (F)" if r["sesso"] == "F" else "")
    items = [(name(r), num(r["finalizzazione"]), "var(--s1)" if num(r["finalizzazione"]) >= 0 else "var(--neg)",
              f"{int(num(r['gol_np']))} gol senza rigori da {fmt(num(r['npxg']))} xG, {int(num(r['tiri']))} tiri") for r in sel]
    chart = hbars(items, d=1, unit="", diverging=True, label_w=190)
    tab = table(["Giocatore", "Sesso", "Squadre", "Tiri", "Gol senza rigori", "xG senza rigori", "Differenza"],
                [[r["soprannome"] or r["giocatore"], r["sesso"], r["squadre"], int(num(r["tiri"])), int(num(r["gol_np"])),
                  fmt(num(r["npxg"])), fmt(num(r["finalizzazione"]))] for r in sel])
    top = s[0]
    return dict(
        id="finalizzatori", kicker="Giocatori", title="Chi segna più (e meno) di quanto dovrebbe",
        headline=f"{top['soprannome'] or top['giocatore']} ha segnato {fmt(num(top['finalizzazione']), 0)} gol in più di quanto valessero i suoi tiri; "
                 f"in fondo alla classifica {s[-1]['soprannome'] or s[-1]['giocatore']}, {fmt(num(s[-1]['finalizzazione']), 1)}.",
        chart=chart, legend=legend([("var(--s1)", "Segna più del previsto"), ("var(--neg)", "Segna meno del previsto")]),
        body=["Messi è un caso fuori scala (+144 in 602 partite): lo indichiamo a parte per non schiacciare il grafico.",
              "Il dato premia chi tira tanto: con molte partite anche un piccolo vantaggio per tiro diventa grande."],
        method="Gol senza rigori meno xG senza rigori, su tutte le partite del giocatore nel dataset; almeno 40 tiri.",
        caveat="Un solo campione per giocatore: per chi ha poche partite (molte giocatrici e i giocatori di una sola stagione) il dato è "
               "più rumoroso. Gli xG sono quelli StatsBomb, che non vedono la posizione del portiere al momento del tiro.",
        table=tab), s


def upsets_study(T, K, SH):
    # partite con eventi mancanti: i gol registrati devono corrispondere al risultato
    goals = Counter()
    for k in K:
        if k["tipo"] in ("Gol", "Gol su rigore"):
            goals[(k["n"], k["squadra"])] += 1
        elif k["tipo"] == "Autogol":
            other = [r["avversario"] for r in T if r["n"] == k["n"] and r["squadra"] == k["squadra"]]
            if other:
                goals[(k["n"], other[0])] += 1
    ok = lambda r: goals[(r["n"], r["squadra"])] == int(num(r["gol"])) and num(r["passaggi"]) > 0
    bad = sorted({r["n"] for r in T if not ok(r)})
    wins = [r for r in T if r["esito"] == "V" and ok(r) and all(ok(x) for x in T if x["n"] == r["n"])]
    wins.sort(key=lambda r: num(r["xg"]) - num(r["xg_subiti"]))
    top = wins[:10]
    items = [(f"{r['squadra']} {r['gol']}-{r['gol_subiti']} {r['avversario']}", num(r["xg_subiti"]) - num(r["xg"]), "var(--neg)",
              f"{r['competizione']} {r['data']}, xG {fmt(num(r['xg']), 2)} contro {fmt(num(r['xg_subiti']), 2)}") for r in top]
    chart = hbars(items, d=2, unit=" xG", diverging=False, label_w=340, value_w=80)
    tab = table(["Partita n.", "Data", "Competizione", "Vincente", "Risultato", "Sconfitta", "xG vincente", "xG sconfitta"],
                [[r["n"], r["data"], r["competizione"], r["squadra"], f"{r['gol']}-{r['gol_subiti']}", r["avversario"],
                  fmt(num(r["xg"]), 2), fmt(num(r["xg_subiti"]), 2)] for r in top])
    t0 = top[0]
    return dict(
        id="colpi", kicker="Partite", title="Le vittorie più improbabili",
        headline=f"{t0['squadra']}–{t0['avversario']} {t0['gol']}-{t0['gol_subiti']} ({t0['competizione']}, {t0['data'][:4]}): "
                 f"vinta con {fmt(num(t0['xg']), 2)} xG contro {fmt(num(t0['xg_subiti']), 2)}.",
        chart=chart.replace("−", "−"), legend="",
        body=["Le barre indicano lo svantaggio in xG di chi ha vinto (xG dello sconfitto meno xG del vincitore): più lunga la barra, "
              "più improbabile la vittoria."],
        method="Vittorie ordinate per differenza di xG (xG del vincitore meno xG dello sconfitto). Ogni partita è controllata: i gol "
               f"registrati negli eventi devono coincidere con il risultato. Partite escluse per eventi mancanti nella fonte: {len(bad)} "
               f"(n. {', '.join(bad[:8])}{'…' if len(bad) > 8 else ''}).",
        caveat="Gli xG non includono gli autogol e valutano ogni tiro in modo isolato: in partite con tanti tiri ribattuti la somma degli xG "
               "può sovrastimare il dominio reale.",
        table=tab)


# ------------------------------------------------------------------------------------------- pagina
CSS = """
:root{--bg:#f6f7f9;--surface:#fcfcfb;--card:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--muted:#6b6a66;--line:#e3e6ea;--grid:#ecebe7;--axis:#c9c8c2;
--s1:#2a78d6;--s2:#eb6834;--neg:#e34948;--neutral:#b9b8b2;--context:#c7c6c0}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){--bg:#121314;--surface:#1a1a19;--card:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;
--muted:#9c9b93;--line:#30302d;--grid:#2a2a28;--axis:#4a4a46;--s1:#3987e5;--s2:#d95926;--neg:#e66767;--neutral:#5c5c57;--context:#4b4b47}}
:root[data-theme="dark"]{--bg:#121314;--surface:#1a1a19;--card:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;--muted:#9c9b93;--line:#30302d;--grid:#2a2a28;
--axis:#4a4a46;--s1:#3987e5;--s2:#d95926;--neg:#e66767;--neutral:#5c5c57;--context:#4b4b47}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1000px;margin:0 auto;padding:16px}a{color:var(--s1)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;margin:0 0 18px;scroll-margin-top:64px}
.kicker{font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
h1{font-size:26px;margin:4px 0 8px;color:var(--ink)}h2{font-size:21px;margin:4px 0 10px;line-height:1.25}.head{font-size:16.5px;font-weight:500;margin:0 0 14px}
p{margin:0 0 10px;color:var(--ink2)}svg{display:block;width:100%;height:auto;overflow:visible}
.sm.sm2{grid-template-columns:1fr 1fr}@media (max-width:480px){.sm.sm2{grid-template-columns:1fr}}.sm{display:grid;grid-template-columns:repeat(3,1fr);gap:18px 22px}@media (max-width:760px){.sm{grid-template-columns:1fr 1fr}}
@media (max-width:480px){.sm{grid-template-columns:1fr}}
.lg{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--ink2);margin:10px 0 4px}.lg span{display:inline-flex;align-items:center;gap:6px}
.lg svg{display:inline-block;width:14px;height:14px}
.meta{font-size:13px;color:var(--muted);border-top:1px solid var(--line);margin-top:12px;padding-top:10px}.meta b{color:var(--ink2)}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:0 0 14px}.tile{border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.tl{font-size:13px;color:var(--muted)}.tv{font-size:44px;font-weight:650;line-height:1.1}.ts{font-size:13px;color:var(--ink2)}
details.tview{margin-top:10px;font-size:13px}details.tview summary{cursor:pointer;color:var(--ink2)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;margin-top:8px;font-variant-numeric:tabular-nums}
th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;white-space:nowrap}th{color:var(--muted);font-weight:600}
.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13.5px}.toc a{text-decoration:none}
.exp{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:12px;font-size:12.5px;color:var(--muted)}
.wk{color:var(--s1)}details.txt pre{white-space:pre-wrap;font:12.5px/1.5 ui-monospace,Menlo,Consolas,monospace;background:var(--bg);
border:1px solid var(--line);border-radius:8px;padding:10px;max-height:340px;overflow:auto;color:var(--ink2)}
details.txt .copy,.exp button{font:inherit;font-size:12.5px;padding:3px 9px;border-radius:12px;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}
"""


def card(i, st):
    body = "".join(f"<p>{e(p)}</p>" for p in st["body"])
    fm = ("4:5", "1:1", "9:16", "16:9")
    btn = "".join(f'<button data-f="{k}">{k}</button>' for k in fm)
    pk = "".join(f'<button data-f="{k}">{k}</button>' for k in fm)
    return (f'<section class="card study" id="{st["id"]}"><div class="kicker">{i}. {e(st["kicker"])} · <span class="wk">Settimana {st["week"]}</span></div>'
            f'<h2>{e(st["title"])}</h2>'
            f'<p class="head">{e(st["headline"])}</p><div class="chart">{st["chart"]}</div>{st["legend"]}{body}'
            f'<div class="meta"><p><b>Come è calcolato.</b> {e(st["method"])}</p><p><b>Attenzione.</b> {e(st["caveat"])}</p></div>'
            f'{st["table"]}<details class="tview txt"><summary>Testi per i social (LinkedIn, Instagram, X, TikTok, alt text)</summary>'
            f'<button class="copy">Copia i testi</button><pre>{e(st["texts"])}</pre></details>'
            f'<div class="exp pack"><span>📦 Pack completo (5 slide PNG + PDF + testi):</span>{pk}<span class="pst"></span></div>'
            f'<div class="exp one"><span>📷 Solo il grafico:</span>{btn}</div></section>')


def poss_anomalies(T):
    """Partite con possesso non affidabile: fuori scala o lontano oltre 15 punti dalla quota dei passaggi (durate di eventi anomale)."""
    M = defaultdict(list)
    for r in T:
        M[r["n"]].append(r)
    out = set()
    for n, rs in M.items():
        if len(rs) != 2:
            continue
        a, b = rs
        tp = num(a["passaggi"]) + num(b["passaggi"])
        p = num(a["possesso_pct"])
        if not 0 <= p <= 100 or (tp and abs(p - 100 * num(a["passaggi"]) / tp) > 15):
            out.add(n)
    return out


def write_page(items, fname, title, h1, intro, cal, cta, nav, all_label):
    import report  # logo, copyright, esportazione condivisi con i report
    toc = "".join(f'<a href="#{s["id"]}">{i}. {e(s["title"])}</a>' for i, s in enumerate(items, 1))
    cards = "".join(card(i, s) for i, s in enumerate(items, 1))
    data = {"logo": report.FAVICON, "sb": report.SB_B64, "cta": cta,
            "studies": [{"id": s["id"], "num": i, "tag": s["tag"], "kicker": s["kicker"], "title": s["title"], "headline": s["headline"],
                         "hook": s["hook"], "body": s["body"], "method": s["method"], "caveat": s["caveat"], "week": s["week"],
                         "next": s["next"], "texts": s["texts"],
                         "foot": "Campione e metodo: " + s["method"][:220] + ("…" if len(s["method"]) > 220 else "")}
                        for i, s in enumerate(items, 1)]}
    js = (HERE / "studi_export.js").read_text(encoding="utf-8")
    data_js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    exp_btns = "".join(f'<button data-f="{k}">{k}</button>' for k in ("4:5", "1:1", "9:16", "16:9"))
    page = (f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title>{report.HEAD_EXTRA}<style>{report.CSS}{CSS}</style></head><body><main>'
            f'{report.brand_bar(nav)}'
            f'<div class="card"><div class="kicker">{e(title)}</div><h1>{e(h1)}</h1><p>{intro}</p><div class="toc">{toc}</div>{cal}'
            f'<div class="exp" id="exp-all"><span>📷 {e(all_label)} (zip + PDF):</span>{exp_btns}</div><p class="sub" id="exp-status"></p></div>'
            f'{cards}{report.footer()}</main>'
            f'<script type="application/json" id="studi-data">{data_js}</script>'
            f'{report.PROTECT_JS}<script>{js}</script></body></html>')
    (HERE / fname).write_text(page, encoding="utf-8")


def main():
    T = load("squadre.csv")
    SH = load("tiri.csv")
    K = load("eventi_chiave.csv")
    C = load("carriere_giocatori.csv")
    bad = bad_matches(T, K)
    anom = poss_anomalies(T)
    Tv = [r for r in T if r["n"] not in bad]  # studi basati sugli eventi: solo partite con i dati di entrambe le squadre
    tabs = season_tables(T)
    fin, ranked = finishing_study([r for r in C if r["player_id"] != "5503"])
    studies = [eras_study(Tv, SH), worldcup_study(Tv), gender_style_study(Tv), gender_skill_study(SH), olympic_study(SH, Tv),
               home_study(T), timing_study(K), possession_study([r for r in Tv if r["n"] not in anom], len(anom)), luck_study(tabs),
               leicester_study(tabs, T), legends_study(Tv), fin, upsets_study(T, K, SH)]
    import studi2 as s2
    import spiegati as sp
    G = load("giocatori.csv")
    WC = [r for r in Tv if r["competizione"] == "FIFA World Cup" and r["stagione"] in ("2018", "2022")]
    studies += [s2.barca_study(Tv), s2.messi_study(Tv, G), s2.wc_finals_study(T), s2.ucl_finals_study(T), s2.pele_study(G, T),
                s2.brazil70_study(Tv, G, WC), s2.holland74_study(Tv, G, WC), s2.maradona_study(T, G), s2.legends_share_study(G)]
    for st in studies:
        if st["id"] in ("epoche", "mondiali", "stile", "olimpici", "possesso", "leggende", "barcellona", "messi"):
            st["method"] += f" Escluse {len(bad)} partite in cui la fonte non contiene gli eventi di una delle due squadre."
        st.setdefault("hook", s2.HOOKS.get(st["id"], st["title"]))
    dati = sp.build(T, Tv, G, SH, C, load("voti.csv"), load("elo.csv"), load("rete_passaggi.csv"), bad, anom)
    s2.TAGS.update(sp.TAGS)
    pages = [(studies, s2.CALENDAR, "Studio", "uno studio nuovo"), (dati, sp.CALENDAR_DATI, "Il dato spiegato", "spieghiamo un dato")]
    weeks = {}
    for items, calendar, label, serie in pages:
        week = {sid: i for i, sid in enumerate(calendar, 1)}
        assert sorted(week) == sorted(s["id"] for s in items), f"calendario e contenuti non coincidono ({label})"
        by_week = {week[s["id"]]: s for s in items}
        for i, st in enumerate(items, 1):
            st["week"] = week[st["id"]]
            st["tag"] = f"Studio {i} · {st['kicker']}" if label == "Studio" else "Il dato spiegato"
            nxt = by_week.get(st["week"] + 1)
            st["next"] = nxt["title"] if nxt else ""
            st["texts"] = s2.pack_texts(st, st["week"], st["next"] or "a presto", serie)
        weeks[label] = by_week
    num_of = {s["id"]: i for items, *_ in pages for i, s in enumerate(items, 1)}
    cal_rows = [[f"Settimana {w}", f'<a href="studi.html#{weeks["Studio"][w]["id"]}">{num_of[weeks["Studio"][w]["id"]]}. {e(weeks["Studio"][w]["title"])}</a>',
                 f'<a href="dati.html#{weeks["Il dato spiegato"][w]["id"]}">{e(weeks["Il dato spiegato"][w]["title"])}</a>'] for w in sorted(weeks["Studio"])]
    cal = ('<details class="tview" open><summary>Piano editoriale: ogni settimana uno studio e un dato spiegato</summary><div class="scroll"><table>'
           '<tr><th>Settimana</th><th>Studio</th><th>Il dato spiegato</th></tr>' +
           "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in cal_rows) + "</table></div></details>")
    nav = ('<a href="index.html">Report partite</a> <a href="classifiche.html">Classifiche di tutti i tempi</a> '
           '<a href="studi.html">Studi</a> <a href="dati.html">Il dato spiegato</a>')
    pack = "Ogni contenuto ha il suo pack social: carosello di 5 slide (PNG e PDF) e testi pronti per LinkedIn, Instagram, X e TikTok."
    write_page(studies, "studi.html", "Delta Scout · Studi", f"Cosa dicono 3.961 partite: {len(studies)} studi",
               "Studi sul dataset StatsBomb Open Data: come è cambiato il calcio, le differenze tra maschile e femminile, squadre, fortuna, "
               "finalizzazione, partite anomale, finali e leggende prima dell’era dei dati. Ogni studio riporta campione, metodo e limiti; i "
               "numeri sono ricalcolati dai dati a ogni esecuzione di <code>studi.py</code>. " + pack,
               cal, "Uno studio sui dati del calcio ogni settimana", nav, "Esporta tutti gli studi")
    write_page(dati, "dati.html", "Delta Scout · Il dato spiegato", f"Il dato spiegato: {len(dati)} metriche con esempi veri",
               "Cosa vogliono dire xG, PPDA, field tilt, xT e tutti gli altri numeri dei report Delta Scout. Per ogni metrica: definizione "
               "in parole semplici, come si legge, valori tipici e record presi dalle 3.961 partite del database, come è calcolata e i suoi "
               "limiti. " + pack, cal, "Ogni settimana spieghiamo un dato del calcio", nav, "Esporta tutte le schede")
    print(f"{len(studies)} studi in studi.html, {len(dati)} schede in dati.html")
    for s in studies + dati:
        print(f"- {s['title']}: {s['headline']}")


if __name__ == "__main__":
    main()
