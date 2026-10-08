"""Delta Scout - «Il dato spiegato»: una scheda per ogni metrica dei report, con esempi presi dal database.

Ogni scheda ha la stessa struttura degli studi (grafico, metodo, limiti, tabella, pack social) e viene pubblicata
nella stessa settimana di uno studio (CALENDAR_DATI, abbinato a studi2.CALENDAR). Importato da studi.py.
"""
import json
import math
from collections import defaultdict

from studi import (FONT, HERE, columns, e, fmt, hbars, is_f, legend, num, stacked100, svg_open, table, watermark, xpts, poisson)
from studi2 import IT, MESSI, MARADONA, it

K_ = "Il dato spiegato"


def q(vals, p):
    v = sorted(vals)
    return v[int(p * (len(v) - 1))]


def name(r):
    return (r.get("soprannome") or r["giocatore"]).strip()


SCORE = {}  # (n, squadra) -> (gol fatti, gol subiti), riempito da build()


def match_lab(r):
    g = SCORE.get((r["n"], r["squadra"]), ("?", "?"))
    return f"{it(r['squadra'])}–{it(r['avversario'])} {g[0]}-{g[1]} ({r['data'][:4]})"


# ------------------------------------------------------------------------------------------- grafici
def histogram(values, lo, hi, nb, markers, unit="", d=0, w=680, h=270, xlab="", ticks=5):
    """Distribuzione (quota di partite per fascia) con marcatori verticali etichettati: [(valore, etichetta)]."""
    pad_l, pad_r, pad_t, pad_b = 40, 14, 74, 40
    step = (hi - lo) / nb
    cnt = [0] * nb
    for v in values:
        cnt[min(max(int((v - lo) / step), 0), nb - 1)] += 1
    sh = [100 * c / len(values) for c in cnt]
    top = max(sh) * 1.12
    X = lambda v: pad_l + (w - pad_l - pad_r) * (min(max(v, lo), hi) - lo) / (hi - lo)
    Y = lambda v: pad_t + (h - pad_t - pad_b) * (1 - v / top)
    s = [svg_open(w, h, "distribuzione")]
    for k in (1, 2):
        t = top * k / 2.4
        s.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="var(--grid)"/>'
                 f'<text x="{pad_l - 6}" y="{Y(t) + 3:.1f}" font-size="10" fill="var(--muted)" text-anchor="end">{fmt(t, 0)}%</text>')
    bw = (w - pad_l - pad_r) / nb
    for i, v in enumerate(sh):
        x = pad_l + i * bw
        a, b = lo + i * step, lo + (i + 1) * step
        s.append(f'<g><title>{fmt(a, d)}–{fmt(b, d)}{unit}: {fmt(v, 1)}% delle partite</title>'
                 f'<rect x="{x + 1:.1f}" y="{Y(v):.1f}" width="{bw - 2:.1f}" height="{Y(0) - Y(v):.1f}" rx="2" fill="var(--context)"/></g>')
    for k in range(ticks + 1):
        t = lo + (hi - lo) * k / ticks
        s.append(f'<text x="{X(t):.1f}" y="{h - 24}" font-size="10" fill="var(--muted)" text-anchor="middle">{fmt(t, d)}{unit}</text>')
    s.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--axis)"/>'
             f'<text x="{(pad_l + w - pad_r) / 2:.1f}" y="{h - 6}" font-size="10.5" fill="var(--muted)" text-anchor="middle">{e(xlab)}</text>')
    placed = []
    for v, lab, col in sorted(markers):
        x = X(v)
        tw = 5.8 * len(lab) + 10
        lvl = 0
        while any(abs(x - p) < (tw + pw) / 2 and l == lvl for p, l, pw in placed):
            lvl += 1
        placed.append((x, lvl, tw))
        ly = 14 + lvl * 15
        anchor = "start" if x < pad_l + 60 else "end" if x > w - pad_r - 60 else "middle"
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{ly + 4}" y2="{Y(0):.1f}" stroke="{col}" stroke-width="2" stroke-dasharray="4 3"/>'
                 f'<text x="{x:.1f}" y="{ly}" font-size="10.5" font-weight="600" fill="var(--ink)" text-anchor="{anchor}">{e(lab)}</text>')
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def pitch_open(w=680, label="campo"):
    h = w * 80 / 120
    return (f'<svg viewBox="-2 -2 124 84" width="{w}" height="{h:.0f}" role="img" aria-label="{e(label)}" {FONT}>'
            '<rect x="-2" y="-2" width="124" height="84" fill="var(--surface)"/>')


def pitch_lines():
    return ('<g fill="none" stroke="var(--axis)" stroke-width="0.35">'
            '<rect x="0" y="0" width="120" height="80"/><line x1="60" y1="0" x2="60" y2="80"/><circle cx="60" cy="40" r="10"/>'
            '<rect x="0" y="18" width="18" height="44"/><rect x="102" y="18" width="18" height="44"/>'
            '<rect x="0" y="30" width="6" height="20"/><rect x="114" y="30" width="6" height="20"/></g>'
            '<text x="119" y="79" font-size="2.2" fill="var(--muted)" text-anchor="end">© Delta Scout</text>')


def grid_heat(grid, nx, ny, label, fmt_cell=None, title=""):
    """Griglia ny x nx sul campo (attacco verso destra), colore = intensità di --s1."""
    mx = max(max(r) for r in grid) or 1
    cw, ch = 120 / nx, 80 / ny
    s = [pitch_open(label=label)]
    for j in range(ny):
        for i in range(nx):
            v = grid[j][i]
            op = 0.06 + 0.9 * (v / mx)
            s.append(f'<g><title>{e(title)}: {fmt_cell(v) if fmt_cell else v}</title>'
                     f'<rect x="{i * cw:.2f}" y="{j * ch:.2f}" width="{cw:.2f}" height="{ch:.2f}" fill="var(--s1)" opacity="{op:.2f}"/></g>')
            if fmt_cell and (nx <= 8 or (j % 2 == 0 and i % 2 == 1)):
                s.append(f'<text x="{i * cw + cw / 2:.2f}" y="{j * ch + ch / 2 + 1:.2f}" font-size="{2.6 if nx > 8 else 3.4}" '
                         f'fill="{"#fff" if v / mx > 0.5 else "var(--ink)"}" text-anchor="middle">{fmt_cell(v)}</text>')
    s.append(pitch_lines())
    s.append('<text x="60" y="-0.3" font-size="2.6" fill="var(--muted)" text-anchor="middle">attacco →</text></svg>')
    return "".join(s)


def lines_chart(series, n, xlab, w=680, h=300, d=0):
    """Più linee su un indice (giornate). series: [(nome, colore, valori, evidenziata)]."""
    pad_l, pad_r, pad_t, pad_b = 44, 130, 14, 34
    vals = [v for _, _, vs, _ in series for v in vs]
    lo, hi = min(vals), max(vals)
    sp = hi - lo or 1
    lo, hi = lo - sp * 0.05, hi + sp * 0.05
    X = lambda i: pad_l + (w - pad_l - pad_r) * i / (n - 1)
    Y = lambda v: pad_t + (h - pad_t - pad_b) * (1 - (v - lo) / (hi - lo))
    s = [svg_open(w, h, xlab)]
    for k in range(5):
        t = lo + (hi - lo) * k / 4
        s.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="var(--grid)"/>'
                 f'<text x="{pad_l - 6}" y="{Y(t) + 3:.1f}" font-size="10" fill="var(--muted)" text-anchor="end">{fmt(t, d)}</text>')
    for i in range(0, n, 5):
        s.append(f'<text x="{X(i):.1f}" y="{h - 18}" font-size="10" fill="var(--muted)" text-anchor="middle">{i + 1}</text>')
    s.append(f'<text x="{(pad_l + w - pad_r) / 2:.1f}" y="{h - 3}" font-size="10.5" fill="var(--muted)" text-anchor="middle">{e(xlab)}</text>')
    ends = []
    for nm_, col, vs, hl in sorted(series, key=lambda x: x[3]):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vs))
        s.append(f'<g><title>{e(nm_)}: {fmt(vs[-1], d)} a fine stagione</title><polyline points="{pts}" fill="none" stroke="{col}" '
                 f'stroke-width="{2.6 if hl else 1.5}" stroke-linejoin="round"/></g>')
        ends.append([Y(vs[-1]), nm_, vs[-1], hl])
    ends.sort()
    for k in range(1, len(ends)):
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 13)
    for y, nm_, v, hl in ends:
        s.append(f'<text x="{w - pad_r + 8}" y="{y + 4:.1f}" font-size="11" fill="var(--ink)"{" font-weight=\"700\"" if hl else ""}>'
                 f'{e(nm_)} {fmt(v, d)}</text>')
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def momentum_bars(a, b, na, nb, w=680, h=220):
    n = max(len(a), len(b))
    pad = 30
    mx = max(a + b) or 1
    mid = h / 2 - 6
    bw = (w - 2 * pad) / n
    s = [svg_open(w, h, "momentum"), f'<line x1="{pad}" x2="{w - pad}" y1="{mid}" y2="{mid}" stroke="var(--axis)"/>']
    for i in range(n):
        va = a[i] if i < len(a) else 0
        vb = b[i] if i < len(b) else 0
        x = pad + i * bw
        ha, hb = (mid - 16) * va / mx, (mid - 16) * vb / mx
        s.append(f'<g><title>{i * 5}–{i * 5 + 5}\' {e(na)}: {va} tocchi nell\'ultimo terzo</title><rect x="{x + 1:.1f}" y="{mid - ha:.1f}" '
                 f'width="{bw - 2:.1f}" height="{ha:.1f}" fill="var(--s1)"/></g>'
                 f'<g><title>{i * 5}–{i * 5 + 5}\' {e(nb)}: {vb} tocchi nell\'ultimo terzo</title><rect x="{x + 1:.1f}" y="{mid:.1f}" '
                 f'width="{bw - 2:.1f}" height="{hb:.1f}" fill="var(--s2)"/></g>')
        if i % 3 == 0:
            s.append(f'<text x="{x:.1f}" y="{h - 4}" font-size="10" fill="var(--muted)">{i * 5}\'</text>')
    s.append(f'<text x="{pad}" y="12" font-size="11" fill="var(--ink2)">{e(na)} ↑</text>'
             f'<text x="{pad}" y="{h - 18}" font-size="11" fill="var(--ink2)">{e(nb)} ↓</text>')
    s.append(watermark(w, h).replace(f'y="{h - 4}"', 'y="12"') + "</svg>")
    return "".join(s)


def network(nodes, edges, color="var(--s1)"):
    """nodes: {id: (x, y, passaggi, maglia, nome)}; edges: [(a, b, n)]."""
    mx_e = max(n for _, _, n in edges)
    mx_n = max(v[2] for v in nodes.values())
    s = [pitch_open(label="rete di passaggi"), pitch_lines()]
    for a, b, n in sorted(edges, key=lambda x: x[2]):
        (x1, y1), (x2, y2) = nodes[a][:2], nodes[b][:2]
        s.append(f'<g><title>{e(nodes[a][4])} ↔ {e(nodes[b][4])}: {n} passaggi</title><line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                 f'y2="{y2:.1f}" stroke="{color}" stroke-width="{0.3 + 1.6 * n / mx_e:.2f}" opacity="{0.25 + 0.6 * n / mx_e:.2f}"/></g>')
    for k, (x, y, n, mg, nm_) in nodes.items():
        r = 1.8 + 2.4 * math.sqrt(n / mx_n)
        s.append(f'<g><title>{e(nm_)}: {int(n)} passaggi riusciti</title><circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{color}" '
                 f'stroke="var(--surface)" stroke-width="0.5"/><text x="{x:.1f}" y="{y + 1.1:.1f}" font-size="2.9" font-weight="700" '
                 f'fill="#fff" text-anchor="middle">{e(mg)}</text></g>')
    s.append("</svg>")
    return "".join(s)


def card(id_, title, hook, headline, chart, leg, body, method, caveat, tab):
    return dict(id=id_, kicker=K_, title=title, hook=hook, headline=headline, chart=chart, legend=leg, body=body, method=method,
                caveat=caveat, table=tab)


def career(C, k, min_min=1800, n=10, label_f=True):
    pool = [r for r in C if num(r["minuti"]) >= min_min]
    top = sorted(pool, key=lambda r: -num(r[k]))[:n]
    lab = lambda r: name(r) + (" (F)" if label_f and r["sesso"] == "F" else "")
    return pool, top, lab


# ------------------------------------------------------------------------------------------- schede
def xg_card(SH, bad):
    ss = [s for s in SH if s["tipo"] != "Penalty" and s["n"] not in bad]
    bins = [(0, .05), (.05, .1), (.1, .2), (.2, .3), (.3, .5), (.5, 1.01)]
    labs, pred, real, ns = [], [], [], []
    for a, b in bins:
        x = [s for s in ss if a <= num(s["xg"]) < b]
        labs.append(f"{fmt(a, 2)}–{fmt(min(b, 1), 2)}")
        pred.append(100 * sum(num(s["xg"]) for s in x) / len(x))
        real.append(100 * sum(s["gol"] == "1" for s in x) / len(x))
        ns.append(len(x))
    chart = columns(labs, [("Gol attesi (media degli xG)", "var(--s2)", pred), ("Gol segnati davvero", "var(--s1)", real)], d=1, unit="%")
    pen = num(next(s["xg"] for s in SH if s["tipo"] == "Penalty"))
    miss = max([s for s in ss if s["gol"] != "1"], key=lambda s: num(s["xg"]))
    op = [s for s in ss if s["tipo"] == "Open Play" and s["gol"] == "1" and s["n"] not in bad]
    lucky = min(op, key=lambda s: num(s["xg"]))
    mar = sorted([s for s in SH if s["n"] == "647" and s["player_id"] == MARADONA and s["gol"] == "1"], key=lambda s: int(s["minuto"]))
    med = q([num(s["xg"]) for s in ss], .5)
    return card(
        "d-xg", "xG: quanto valeva quell'occasione",
        "Cosa vuol dire '2,3 xG'? Il dato più usato del calcio, spiegato con 98.000 tiri.",
        f"Gli xG (expected goals) danno a ogni tiro la probabilità di diventare gol, da 0 a 1. Un rigore vale {fmt(pen, 2)}; "
        f"il tiro tipico del database vale appena {fmt(med, 2)}, cioè segna circa una volta su {fmt(1 / med, 0)}.",
        chart, legend([("var(--s2)", "Gol attesi: media degli xG dei tiri della fascia"), ("var(--s1)", "Gol segnati davvero")]),
        ["Come si legge: la somma degli xG di una squadra è il numero di gol che 'meritava' con le occasioni create. Il grafico mostra "
         "che il modello funziona: in ogni fascia la percentuale di gol reali è vicina a quella prevista.",
         f"Esempio: il gol di mano di Maradona all'Inghilterra (1986) vale {fmt(num(mar[0]['xg']), 2)} xG, quello dopo la corsa da metà campo "
         f"{fmt(num(mar[1]['xg']), 2)}: l'ultimo tiro era facile, il difficile era arrivarci. Gli xG non misurano il dribbling che lo precede.",
         f"Gli estremi: {miss['giocatore']} ({it(miss['squadra'])}–{it(miss['avversario'])}, {miss['data'][:4]}) sbaglia un tiro da "
         f"{fmt(num(miss['xg']), 2)} xG; {lucky['giocatore']} ({lucky['data'][:4]}) segna su azione con un tiro da "
         f"{fmt(num(lucky['xg']), 3)} xG da {fmt(num(lucky['distanza_porta']), 0)} metri."],
        "xG del modello StatsBomb, che considera posizione, angolo, parte del corpo, tipo di azione, posizione di portiere e difensori. "
        f"Grafico: {len(ss):,} tiri senza rigori, divisi per fascia di xG.".replace(",", "."),
        "Gli xG valutano l'occasione, non il tiratore: un campione e un difensore che tirano dallo stesso punto hanno lo stesso xG. "
        "Il modello non vede se il tiro è stato poi ben calciato (per quello servono i 'post-shot xG').",
        table(["Fascia di xG", "Tiri", "Gol attesi", "Gol reali"], [[l, f"{n:,}".replace(",", "."), fmt(p) + "%", fmt(r) + "%"]
                                                                     for l, n, p, r in zip(labs, ns, pred, real)]))


def xa_card(C, G, bad):
    pool, top, lab = career(C, "xa_p90")
    items = [(lab(r), num(r["xa_p90"]), "var(--s1)", f"{int(num(r['assist']))} assist, {int(num(r['passaggi_chiave']))} passaggi chiave in "
              f"{int(num(r['minuti']))} minuti") for r in top]
    chart = hbars(items, d=2, label_w=230)
    best = max([r for r in G if r["n"] not in bad and not is_f(r["competizione"])], key=lambda r: num(r["xa"]))
    me = next(r for r in C if r["player_id"] == MESSI)
    return card(
        "d-xa", "xA e passaggi chiave: il valore dell'ultimo passaggio",
        "Un assist dipende anche da chi tira. Gli xA no: ecco come misurare chi crea davvero.",
        "Gli xA (expected assists) sono gli xG dei tiri nati da un passaggio: un passaggio chiave che mette un compagno davanti alla porta "
        "vale molto anche se il compagno sbaglia. Il passaggio chiave è l'ultimo passaggio prima di un tiro.",
        chart, legend([("var(--s1)", "xA ogni 90 minuti (carriera nel database, almeno 1.800 minuti)")]),
        [f"Come si legge: il giocatore tipico del database ha {fmt(q([num(r['xa_p90']) for r in pool], .5), 2)} xA ogni 90 minuti, il 10% "
         f"migliore supera {fmt(q([num(r['xa_p90']) for r in pool], .9), 2)}. Gli assist veri oscillano di più, perché dipendono dalla "
         "precisione di chi tira.",
         f"Esempio: {name(best)} in {match_lab(best)} crea {fmt(num(best['xa']), 2)} xA con {best['passaggi_chiave']} passaggi chiave "
         f"e chiude con {best['assist']} assist: la partita con più xA del calcio maschile nel database.",
         f"Messi: {fmt(num(me['xa_p90']), 2)} xA e {fmt(num(me['passaggi_chiave_p90']), 1)} passaggi chiave ogni 90 minuti in "
         f"{int(num(me['partite']))} partite, numeri da rifinitore puro per uno che è anche il miglior marcatore del database."],
        f"xA = somma degli xG dei tiri che seguono un passaggio del giocatore. Classifica: {len(pool)} giocatori e giocatrici con almeno "
        "1.800 minuti nel database.",
        "Gli xA dipendono anche dalla squadra: in una squadra che tira molto è più facile accumularli. Il passaggio chiave conta anche se "
        "il tiro è debolissimo.",
        table(["Giocatore", "Squadre", "Minuti", "xA/90", "Assist", "Passaggi chiave/90"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), fmt(num(r["xa_p90"]), 2), int(num(r["assist"])),
                fmt(num(r["passaggi_chiave_p90"]), 1)] for r in top]))


def dribbling_card(C, G, bad, T):
    pool, top, lab = career(C, "dribbling_riusciti_p90")
    items = [(lab(r), num(r["dribbling_riusciti_p90"]), "var(--s1)", f"riuscita {fmt(num(r['dribbling_pct']), 0)}%") for r in top]
    chart = hbars(items, d=1, label_w=230)
    best = max([r for r in G if r["n"] not in bad], key=lambda r: num(r["dribbling_riusciti"]))
    allp = [r for r in pool if num(r["dribbling_p90"]) >= 1]
    pct = q([num(r["dribbling_pct"]) for r in allp], .5)
    return card(
        "d-dribbling", "Dribbling: tentati, riusciti e percentuale",
        "Chi salta più avversari nella storia del database? Spoiler: lo sai già.",
        f"Un dribbling è il tentativo di superare un avversario palla al piede. Conta sia quanti se ne tentano sia quanti riescono: "
        f"il giocatore tipico ne completa il {fmt(pct, 0)}%.",
        chart, legend([("var(--s1)", "Dribbling riusciti ogni 90 minuti (almeno 1.800 minuti nel database)")]),
        [f"Come si legge: chi dribbla molto rischia anche di perdere palla, quindi il numero va letto insieme alla percentuale. Il 10% "
         f"migliore del database completa più di {fmt(q([num(r['dribbling_riusciti_p90']) for r in pool], .9), 1)} dribbling ogni 90 minuti.",
         f"Esempio: {name(best)} completa {best['dribbling_riusciti']} dribbling su {best['dribbling']} in {match_lab(best)}, il record del "
         "database in una singola partita.",
         "Il dribbling è il dato più cambiato con le epoche: nelle partite prima del 1991 le squadre ne tentavano quasi il doppio di oggi "
         "(vedi lo studio 'Meno dribbling, più pazienza')."],
        "Dribbling = evento 'Dribble' di StatsBomb (tentativo di superare l'avversario); riuscito = esito 'Complete'.",
        "Non distingue il dribbling che porta verso la porta da quello in zona innocua. Per questo vanno guardate anche le conduzioni "
        "progressive.",
        table(["Giocatore", "Squadre", "Minuti", "Riusciti/90", "Tentati/90", "% riuscita"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), fmt(num(r["dribbling_riusciti_p90"]), 1), fmt(num(r["dribbling_p90"]), 1),
                fmt(num(r["dribbling_pct"]), 0) + "%"] for r in top]))


def ppda_card(T, Tv):
    v = [num(r["ppda"]) for r in Tv]
    med = q(v, .5)
    nl = [r for r in Tv if r["squadra"] == "Netherlands" and r["data"].startswith("1974")]
    nl_avg = sum(num(r["ppda"]) for r in nl) / len(nl)
    che = next(r for r in Tv if r["n"] == "2868" and r["squadra"] == "Chelsea")
    atl = [r for r in Tv if r["squadra"] == "Atlético Madrid" and r["competizione"] == "La Liga" and r["stagione"] == "2015/2016"]
    atl_avg = sum(num(r["ppda"]) for r in atl) / len(atl)
    ita = next((r for r in Tv if r["n"] == "640" and r["squadra"] == "Italy"), None)
    mk = [(med, f"mediana {fmt(med)}", "var(--ink2)"), (nl_avg, f"Olanda 1974: {fmt(nl_avg)}", "var(--s1)"),
          (num(che["ppda"]), f"Chelsea di Mourinho–Villa: {fmt(num(che['ppda']))}", "var(--s1)"),
          (atl_avg, f"Atlético 2015/16: {fmt(atl_avg)}", "var(--ink2)")]
    if ita:
        mk.append((num(ita["ppda"]), f"Italia, finale 1970: {fmt(num(ita['ppda']))}", "var(--s2)"))
    chart = histogram(v, 0, 40, 40, mk, d=0, xlab="PPDA (passaggi concessi per azione difensiva) – a sinistra si pressa di più")
    return card(
        "d-ppda", "PPDA: come si misura il pressing",
        "Quanto pressa una squadra? C'è un numero che lo dice: il PPDA.",
        f"Il PPDA conta quanti passaggi una squadra lascia fare all'avversario nei suoi primi 60 metri prima di intervenire. Più è basso, "
        f"più il pressing è alto e aggressivo: la partita tipica del database è a {fmt(med)}.",
        chart, legend([("var(--context)", "Tutte le partite del database (per squadra)"), ("var(--s1)", "Esempi di pressing alto"),
                       ("var(--s2)", "Esempio di blocco basso"),
                       ("var(--ink2)", "Riferimenti")]),
        [f"Come si legge: sotto {fmt(q(v, .1), 0)} è pressing intenso (10% delle prestazioni), sopra {fmt(q(v, .9), 0)} la squadra aspetta "
         "nella propria metà campo. Non è 'meglio' o 'peggio': è una scelta di stile.",
         f"Esempio: l'Olanda di Cruyff nel 1974 ha una media di {fmt(nl_avg)}, come le squadre più aggressive di oggi. L'Atlético di "
         f"Simeone 2015/16, la difesa migliore della Liga, sta a {fmt(atl_avg)}, " +
         ("vicino alla mediana: difendere bene non vuol dire per forza aspettare basso." if abs(atl_avg - med) < 2 else
          ("sopra la mediana: aspetta e chiude gli spazi." if atl_avg > med else "sotto la mediana: difende anche pressando.")),
         f"Il PPDA più basso di una squadra di Mourinho nel database è {fmt(num(che['ppda']))}, in {match_lab(che)}."],
        "PPDA = passaggi dell'avversario nei suoi primi 60 metri (dalla propria porta) diviso le azioni difensive della squadra nella "
        f"stessa zona (contrasti, intercetti e falli). Grafico: {len(v)} prestazioni, valori sopra 40 raggruppati nell'ultima colonna.",
        "Con un avversario che non passa quasi mai la palla (lanci lunghi) il PPDA può essere basso senza un vero pressing; con pochissime "
        "azioni difensive può diventare altissimo (oltre 100).",
        table(["Esempio", "PPDA"], [[lab_, fmt(val)] for val, lab_, _ in mk]))


def tilt_card(Tv):
    v = [num(r["field_tilt_pct"]) for r in Tv]
    def avg(f):
        rs = [r for r in Tv if f(r)]
        return sum(num(r["field_tilt_pct"]) for r in rs) / len(rs), len(rs)
    bw, _ = avg(lambda r: r["squadra"] == "Barcelona WFC" and r["stagione"] == "2023/2024")
    lei, _ = avg(lambda r: r["squadra"] == "Leicester City" and r["stagione"] == "2015/2016")
    pep, _ = avg(lambda r: r["squadra"] == "Barcelona" and r["allenatore"] == "Pep Guardiola")
    rec = max(Tv, key=lambda r: num(r["field_tilt_pct"]))
    mk = [(50, "equilibrio 50%", "var(--ink2)"), (bw, f"Barcellona F 2023/24: {fmt(bw, 0)}%", "var(--s1)"),
          (pep, f"Barça di Guardiola: {fmt(pep, 0)}%", "var(--s1)"), (lei, f"Leicester 2015/16: {fmt(lei, 0)}%", "var(--s2)")]
    chart = histogram(v, 0, 100, 25, mk, unit="%", xlab="Field tilt: quota dei passaggi nell'ultimo terzo di campo")
    return card(
        "d-tilt", "Field tilt: chi gioca nella metà campo dell'altro",
        "Il possesso dice chi ha la palla. Il field tilt dice dove la usa.",
        "Il field tilt è la quota dei passaggi giocati nell'ultimo terzo di campo: se una squadra ne fa 70 e l'avversaria 30, il tilt è "
        "70%. Misura il dominio territoriale meglio del possesso.",
        chart, legend([("var(--context)", "Tutte le partite del database (per squadra)"), ("var(--s1)", "Squadre di dominio"),
                       ("var(--s2)", "Squadra di ripartenza")]),
        ["Come si legge: 50% è equilibrio; oltre 65% una squadra gioca stabilmente nella metà avversaria, sotto 35% difende basso.",
         f"Esempio: il Leicester campione 2015/16 aveva un tilt medio del {fmt(lei, 0)}%: vinceva lasciando il campo agli altri. Il "
         f"Barcellona femminile 2023/24 arriva all'{fmt(bw, 0)}% di media.",
         f"Record del database: {match_lab(rec)}, {fmt(num(rec['field_tilt_pct']), 1)}% dei passaggi nell'ultimo terzo."],
        "Field tilt = passaggi della squadra che partono o arrivano nell'ultimo terzo diviso la somma dello stesso dato per le due squadre.",
        "Una squadra in vantaggio può abbassarsi volontariamente: il tilt descrive il tipo di partita, non chi l'ha giocata meglio.",
        table(["Esempio", "Field tilt"], [[lab_, fmt(val, 1) + "%"] for val, lab_, _ in mk] +
              [[match_lab(rec), fmt(num(rec["field_tilt_pct"]), 1) + "%"]]))


def possession_card(Tv, anom):
    rows = [r for r in Tv if r["n"] not in anom]
    v = [num(r["possesso_pct"]) for r in rows]
    tilt_gap = sorted(rows, key=lambda r: num(r["field_tilt_pct"]) - num(r["possesso_pct"]))
    low = [r for r in rows if num(r["possesso_pct"]) < 35 and r["esito"] == "V" and not is_f(r["competizione"])]
    inter = next((r for r in rows if r["n"] == "129" and r["squadra"] == "Inter Milan"), None)
    mk = [(50, "50%", "var(--ink2)")]
    if inter:
        mk.append((num(inter["possesso_pct"]), f"Inter, finale 2010: {fmt(num(inter['possesso_pct']), 0)}%", "var(--s2)"))
    lfc = next((r for r in rows if r["n"] == "138" and r["squadra"] == "Liverpool"), None)
    if lfc:
        mk.append((num(lfc["possesso_pct"]), f"Liverpool, finale 2019: {fmt(num(lfc['possesso_pct']), 0)}%", "var(--s2)"))
    chart = histogram(v, 0, 100, 25, mk, unit="%", xlab="Possesso palla (quota del tempo)")
    return card(
        "d-possesso", "Possesso palla: cosa misura (e cosa no)",
        "Avere la palla il 70% del tempo non vuol dire dominare. Ecco perché.",
        "Il possesso è la quota del tempo in cui una squadra ha il controllo della palla. È il dato più citato in TV e uno dei meno "
        "utili da solo: non dice dove si gioca né quanto si crea.",
        chart, legend([("var(--context)", "Tutte le partite del database (per squadra)"), ("var(--s2)", "Finali vinte con poco possesso")]),
        [f"Come si legge: va affiancato a field tilt e xG. Nel database ci sono {len(low)} vittorie maschili con meno del 35% di possesso.",
         (f"Esempio: l'Inter di Mourinho vince la finale di Champions 2010 con il {fmt(num(inter['possesso_pct']), 0)}% di possesso e il Liverpool "
          f"quella del 2019 con il {fmt(num(lfc['possesso_pct']), 0)}%." if inter and lfc else ""),
         "Lo studio 'Il possesso aiuta, ma meno di quanto si pensi' mostra che oltre il 70% di possesso si vince il 58% delle volte."],
        "Possesso = somma della durata degli eventi in cui la squadra è in possesso (dati StatsBomb), diviso il totale delle due squadre. "
        f"Escluse {len(anom)} partite in cui la durata di alcuni eventi nella fonte è anomala (possesso fuori scala o lontano oltre 15 punti "
        "dalla quota dei passaggi).",
        "Il possesso dipende dal punteggio: chi vince spesso lascia la palla all'avversario. E una squadra può tenere palla a lungo nella "
        "propria metà campo senza creare nulla.",
        table(["Esempio", "Possesso"], [[lab_, fmt(val, 1) + "%"] for val, lab_, _ in mk]))


def sca_card(C, G, bad):
    pool, top, lab = career(C, "sca_p90")
    items = [(lab(r), num(r["sca_p90"]), "var(--s1)", f"{fmt(num(r['gca_p90']), 2)} GCA/90") for r in top]
    chart = hbars(items, d=1, label_w=230)
    rob = next(r for r in G if r["n"] == "131" and name(r) == "Arjen Robben")
    best = max([r for r in G if r["n"] not in bad], key=lambda r: num(r["sca"]))
    return card(
        "d-sca", "SCA e GCA: le azioni che portano al tiro",
        "Non solo chi segna e chi fa assist: chi c'è nelle due azioni prima del tiro?",
        "Le SCA (shot-creating actions) sono le due azioni offensive che precedono un tiro: un passaggio, un dribbling riuscito, un fallo "
        "subito. Le GCA sono le stesse azioni quando il tiro diventa gol.",
        chart, legend([("var(--s1)", "Azioni che portano al tiro ogni 90 minuti (almeno 1.800 minuti nel database)")]),
        [f"Come si legge: misura quanto un giocatore è coinvolto nella creazione, anche quando non fa l'ultimo passaggio. Il giocatore "
         f"tipico ne ha {fmt(q([num(r['sca_p90']) for r in pool], .5), 1)} ogni 90 minuti, il 10% migliore oltre "
         f"{fmt(q([num(r['sca_p90']) for r in pool], .9), 1)}.",
         f"Esempio: nella finale di Champions 2012 Robben partecipa a {rob['sca']} azioni da tiro in {int(num(rob['minuti']))} minuti: "
         "il Bayern passava quasi sempre da lui, e il Chelsea vinse lo stesso.",
         f"Record del database: {name(best)}, {best['sca']} SCA in {match_lab(best)}."],
        "Per ogni tiro si prendono le ultime due azioni offensive riuscite della stessa azione (passaggio riuscito, dribbling riuscito, "
        f"fallo subito, tiro ribattuto) e si attribuisce una SCA a chi le ha fatte. Classifica: {len(pool)} giocatori con almeno 1.800 minuti.",
        "Conta allo stesso modo un passaggio decisivo e uno banale, purché arrivi nelle due azioni prima del tiro. È una misura di "
        "coinvolgimento, non di qualità.",
        table(["Giocatore", "Squadre", "Minuti", "SCA/90", "GCA/90"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), fmt(num(r["sca_p90"]), 2), fmt(num(r["gca_p90"]), 2)] for r in top]))


def xpts_card(T):
    M = defaultdict(list)
    for r in T:
        M[r["n"]].append(r)
    picks = [("131", "Bayern Munich"), ("778", "Argentina"), ("646", "Netherlands"), ("2868", "Chelsea")]
    rows, tab = [], []
    for n_, team in picks:
        a = next(r for r in M[n_] if r["squadra"] == team)
        xa, xb = num(a["xg"]), num(a["xg_subiti"])
        pw = pd = 0.0
        for i in range(12):
            for j in range(12):
                p = poisson(xa, i) * poisson(xb, j)
                if i > j:
                    pw += p
                elif i == j:
                    pd += p
        pl = 1 - pw - pd
        rows.append((f"{it(team)} ({fmt(xa, 2)} xG) – {it(a['avversario'])} ({fmt(xb, 2)})", [100 * pw, 100 * pd, 100 * pl],
                     f"{a['data'][:4]}, finì {a['gol']}-{a['gol_subiti']}"))
        tab.append([match_lab(a), fmt(xa, 2), fmt(xb, 2), fmt(100 * pw) + "%", fmt(100 * pd) + "%", fmt(100 * pl) + "%", fmt(3 * pw + pd, 2),
                    {"V": 3, "N": 1, "P": 0}[a["esito"]]])
    chart = stacked100([(l, v, y) for l, v, y in rows], ["Vittoria", "Pareggio", "Sconfitta"],
                       ["var(--s1)", "var(--neutral)", "var(--s2)"], label_w=330)
    b = tab[0]
    return card(
        "d-xpts", "Punti attesi: quanti punti valeva una partita",
        "Dagli xG a una classifica 'giusta': come si calcolano i punti attesi.",
        f"I punti attesi trasformano gli xG delle due squadre in probabilità di vittoria, pareggio e sconfitta. Esempio: con 3,49 xG contro "
        f"0,29 il Bayern della finale 2012 aveva il {b[3]} di probabilità di vincere: valeva {b[6]} punti, ne ha avuto {b[7]} (finì 1-1).",
        chart, legend([("var(--s1)", "Probabilità di vittoria"), ("var(--neutral)", "Pareggio"), ("var(--s2)", "Sconfitta")]),
        ["Come si legge: punti attesi = 3 × probabilità di vittoria + 1 × probabilità di pareggio. Sommati su una stagione danno la "
         "classifica che le squadre avrebbero meritato con le loro occasioni.",
         "Esempio: il Leicester 2015/16 ha vinto il titolo con 81 punti ma ne valeva 64 (studio 'Leicester 2015/16').",
         f"Con xG vicini il risultato è aperto: nella finale 2022 ({tab[1][1]} contro {tab[1][2]} xG) l'Argentina aveva il {tab[1][3]} di "
         f"probabilità di vincere nei 120 minuti, il {tab[1][4]} di pareggiare. Finì 3-3 e decisero i rigori."],
        "Due distribuzioni di Poisson con media pari agli xG delle squadre; si sommano le probabilità di tutti i risultati (fino a 11 gol). "
        "Gli xG comprendono i rigori in partita e i supplementari, non la serie finale dei rigori.",
        "Il modello tratta i gol delle due squadre come indipendenti e non tiene conto del punteggio (chi è avanti cambia gioco).",
        table(["Partita", "xG", "xG concessi", "P(vittoria)", "P(pareggio)", "P(sconfitta)", "Punti attesi", "Punti reali"], tab))


def carries_card(C, G, bad):
    pool, top, lab = career(C, "conduzioni_progressive_p90")
    items = [(lab(r), num(r["conduzioni_progressive_p90"]), "var(--s1)", f"{fmt(num(r['metri_progressivi_p90']), 0)} m progressivi/90")
             for r in top]
    chart = hbars(items, d=1, label_w=230)
    best = max([r for r in G if r["n"] not in bad], key=lambda r: num(r["conduzioni_progressive"]))
    mod = max([r for r in G if r["n"] not in bad and r["data"] >= "2015"], key=lambda r: num(r["conduzioni_progressive"]))
    return card(
        "d-conduzioni", "Conduzioni progressive: portare palla verso la porta",
        "Garrincha, Neymar, Robben: chi porta palla meglio di tutti?",
        "Una conduzione è quando un giocatore si muove con la palla al piede. È progressiva se avvicina la palla alla porta avversaria "
        "di almeno un quarto della distanza: è il modo di avanzare senza passare la palla.",
        chart, legend([("var(--s1)", "Conduzioni progressive ogni 90 minuti (almeno 1.800 minuti nel database)")]),
        [f"Come si legge: il giocatore tipico ne fa {fmt(q([num(r['conduzioni_progressive_p90']) for r in pool], .5), 1)} ogni 90 minuti, "
         f"il 10% migliore oltre {fmt(q([num(r['conduzioni_progressive_p90']) for r in pool], .9), 1)}. Insieme ai passaggi progressivi "
         "dice chi fa avanzare la squadra.",
         f"Esempio: il record del database è di {name(best)}, {best['conduzioni_progressive']} conduzioni progressive in {match_lab(best)}.",
         f"Dal 2015 in poi il record è di {name(mod)}: {mod['conduzioni_progressive']} in {match_lab(mod)}."],
        "Conduzione = evento 'Carry' di StatsBomb. Progressiva = la distanza dalla porta alla fine è al massimo il 75% di quella "
        f"all'inizio. Classifica: {len(pool)} giocatori con almeno 1.800 minuti.",
        "Non distingue tra conduzioni contro un avversario schierato e in campo aperto. Le partite storiche (ricostruite da filmati) "
        "possono avere conduzioni registrate in modo diverso.",
        table(["Giocatore", "Squadre", "Minuti", "Conduzioni progr./90", "Metri progressivi/90"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), fmt(num(r["conduzioni_progressive_p90"]), 2),
                fmt(num(r["metri_progressivi_p90"]), 0)] for r in top]))


def pressing_card(Tv, G, bad):
    v = [num(r["pressioni"]) for r in Tv]
    med = q(v, .5)
    def avg(f, k):
        rs = [r for r in Tv if f(r)]
        return sum(num(r[k]) for r in rs) / len(rs)
    lei_cp = avg(lambda r: r["squadra"] == "Leicester City" and r["stagione"] == "2015/2016", "contropressioni")
    best = max([r for r in G if r["n"] not in bad], key=lambda r: num(r["pressioni"]))
    lev = avg(lambda r: r["squadra"] == "Bayer Leverkusen" and r["stagione"] == "2023/2024", "pressioni")
    mk = [(med, f"mediana {fmt(med, 0)}", "var(--ink2)"), (lev, f"Leverkusen 2023/24: {fmt(lev, 0)}", "var(--s1)")]
    chart = histogram(v, 50, 300, 25, mk, d=0, xlab="Pressioni della squadra in una partita")
    return card(
        "d-pressioni", "Pressioni, pressioni alte e contropressioni",
        "Il pressing non è solo correre: tre numeri per capirlo.",
        f"Una pressione è un giocatore che va addosso a chi ha la palla entro pochi metri. Una squadra ne fa di solito circa {fmt(med, 0)} a partita. "
        "Le pressioni alte avvengono nell'ultimo terzo di campo; le contropressioni nei 5 secondi dopo aver perso palla.",
        chart, legend([("var(--context)", "Tutte le partite del database (per squadra)"), ("var(--s1)", "Esempio")]),
        ["Come si legge: tante pressioni possono voler dire pressing organizzato oppure una squadra costretta a rincorrere. Le pressioni "
         "alte e il PPDA dicono quale delle due.",
         f"Esempio: il record individuale è di {name(best)}, {best['pressioni']} pressioni in {match_lab(best)}.",
         f"La contropressione è il 'gegenpressing'. Il Leicester 2015/16, squadra di ripartenza, ne faceva {fmt(lei_cp, 0)} a partita, "
         f"in linea con la mediana del database ({fmt(q([num(r['contropressioni']) for r in Tv], .5), 0)}): si può ripartire e contropressare."],
        "Pressione = evento 'Pressure' di StatsBomb. Alta = nell'ultimo terzo di campo (x ≥ 80 su 120). Contropressione = pressione segnata da StatsBomb "
        f"come 'counterpress' (entro 5 secondi dalla perdita del possesso). Grafico: {len(v)} prestazioni di squadra.",
        "Nei dati sono registrate solo le pressioni sul portatore di palla: chi chiude una linea di passaggio senza avvicinarsi non viene "
        "contato. Calcio maschile e femminile insieme.",
        table(["Esempio", "Valore"], [[l, fmt(x, 0)] for x, l, _ in mk] + [[f"Record individuale: {name(best)}", best["pressioni"]]]))


def xt_card(G, bad):
    g = json.loads((HERE / "xt_griglia.json").read_text(encoding="utf-8"))
    grid = g["griglia"]
    chart = grid_heat(grid, 16, 12, "xT", fmt_cell=lambda v: fmt(v, 2), title="valore della zona")
    edge = grid[5][14]
    mid = grid[5][8]
    own = grid[5][2]
    mod = max([r for r in G if r["n"] not in bad and not is_f(r["competizione"])], key=lambda r: num(r["xt"]))
    fem = max([r for r in G if r["n"] not in bad and is_f(r["competizione"])], key=lambda r: num(r["xt"]))
    return card(
        "d-xt", "xT: quanto vale ogni zona del campo",
        "Un passaggio da centrocampo vale meno di uno al limite dell'area. Quanto meno? Ecco la mappa.",
        f"L'xT (expected threat) assegna a ogni zona del campo la probabilità che da lì l'azione finisca in gol. Al limite dell'area una "
        f"palla vale {fmt(edge, 3)}, a centrocampo {fmt(mid, 3)}, nella propria trequarti {fmt(own, 3)}.",
        chart, legend([("var(--s1)", "Valore di minaccia della zona (più scuro = più pericoloso)")]),
        ["Come si legge: ogni passaggio o conduzione vale la differenza tra la zona di arrivo e quella di partenza. È il modo di dare un "
         "valore anche alle azioni che non finiscono con un tiro.",
         f"Esempio: {name(mod)} in {match_lab(mod)} produce {fmt(num(mod['xt']), 2)} xT, il valore più alto nel calcio maschile del database.",
         f"Nel femminile il record è di {name(fem)}, {fmt(num(fem['xt']), 2)} xT in {match_lab(fem)}."],
        f"Griglia 16 × 12 calcolata da Delta Scout su tutte le {g['partite']:,} partite con il metodo di Karun Singh (2018): per ogni zona, "
        "probabilità di tirare e segnare subito più valore atteso dei movimenti successivi, ricalcolati fino a convergenza.".replace(",", "."),
        "L'xT non sa dove sono gli avversari: un passaggio nella zona giusta ma verso un compagno marcato vale come uno libero.",
        table(["Esempio", "xT"], [[f"{name(mod)} – {match_lab(mod)}", fmt(num(mod["xt"]), 2)], [f"{name(fem)} – {match_lab(fem)}", fmt(num(fem["xt"]), 2)]]))


def progressive_card(C, G, bad):
    pool, top, lab = career(C, "passaggi_progressivi_p90")
    items = [(lab(r), num(r["passaggi_progressivi_p90"]), "var(--s1)", f"precisione {fmt(num(r['precisione_passaggi_pct']), 0)}%") for r in top]
    chart = hbars(items, d=1, label_w=230)
    vie = next((r for r in G if r["n"] == "2787" and "Vieira" in r["giocatore"]), None)
    best = max([r for r in G if r["n"] not in bad], key=lambda r: num(r["passaggi_progressivi"]))
    return card(
        "d-progressivi", "Passaggi progressivi: far avanzare la squadra",
        "Il passaggio più utile non è sempre l'assist. È quello che rompe le linee.",
        "Un passaggio è progressivo se avvicina la palla alla porta avversaria di almeno un quarto della distanza. Sono i passaggi che "
        "rompono le linee e fanno avanzare la squadra.",
        chart, legend([("var(--s1)", "Passaggi progressivi ogni 90 minuti (almeno 1.800 minuti nel database)")]),
        ["Come si legge: registi e difensori costruttori sono in cima. Va letto con la precisione: chi tenta molti passaggi verticali "
         "ne sbaglia anche di più.",
         (f"Esempio: nell'ultima partita degli Invincibili dell'Arsenal (2004, contro il Leicester) {vie['giocatore']} fa {vie['passaggi_progressivi']} "
          "passaggi progressivi." if vie else ""),
         f"Record del database: {name(best)}, {best['passaggi_progressivi']} in {match_lab(best)}."],
        "Progressivo = passaggio riuscito la cui distanza dalla porta all'arrivo è al massimo il 75% di quella alla partenza. "
        f"Classifica: {len(pool)} giocatori con almeno 1.800 minuti.",
        "Una squadra che attacca molto ha più occasioni di farne. I lanci lunghi dalla difesa contano come progressivi anche se finiscono "
        "a un compagno marcato.",
        table(["Giocatore", "Squadre", "Minuti", "Progressivi/90", "Precisione passaggi"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), fmt(num(r["passaggi_progressivi_p90"]), 1),
                fmt(num(r["precisione_passaggi_pct"]), 0) + "%"] for r in top]))


def elo_card(E, T):
    pl = {r["n"] for r in T if r["competizione"] == "Premier League" and r["stagione"] == "2015/2016"}
    traj = defaultdict(list)
    for r in sorted(E, key=lambda r: r["data"]):
        if r["n"] in pl:
            traj[r["squadra"]].append(num(r["elo_post"]))
    teams = [("Leicester City", "var(--s1)", True), ("Arsenal", "var(--context)", False), ("Tottenham Hotspur", "var(--context)", False),
             ("Manchester City", "var(--context)", False), ("Chelsea", "var(--s2)", True), ("Aston Villa", "var(--context)", False)]
    series = [(it(t).replace(" Hotspur", ""), c, [1500] + traj[t], h) for t, c, h in teams]
    chart = lines_chart(series, 39, "Giornata di Premier League 2015/16 (0 = inizio, tutti a 1500)")
    lei = traj["Leicester City"]
    # dopo le prime 10 giornate, quando l'Elo ha avuto il tempo di separare le squadre
    later = sorted([r for r in E if r["n"] in pl and r["squadra"] == "Leicester City"], key=lambda r: r["data"])[10:]
    low = min(later, key=lambda r: num(r["prob_vittoria_attesa"]))
    res = next(t for t in T if t["n"] == low["n"] and t["squadra"] == "Leicester City")
    home = res["casa_trasferta"] == "casa"
    ml = (f"{it(res['squadra'])}–{it(res['avversario'])} {res['gol']}-{res['gol_subiti']}" if home else
          f"{it(res['avversario'])}–{it(res['squadra'])} {res['gol_subiti']}-{res['gol']}")
    ch = traj["Chelsea"]
    ch_min = min(range(len(ch)), key=lambda i: ch[i])
    return card(
        "d-elo", "Elo: la forza di una squadra in un numero",
        "Come si misura la forza di una squadra partita dopo partita? Con lo stesso sistema degli scacchi.",
        f"L'Elo dà a ogni squadra un punteggio che sale quando vince e scende quando perde, di più se il risultato è inatteso. Nella "
        f"Premier 2015/16 il Leicester parte da 1500 come tutti e chiude a {fmt(lei[-1], 0)}, il valore più alto del campionato.",
        chart, legend([("var(--s1)", "Leicester City"), ("var(--s2)", "Chelsea (campione in carica)"), ("var(--context)", "Altre squadre")]),
        ["Come si legge: la differenza di Elo diventa un risultato atteso. Con 100 punti di vantaggio ci si aspetta circa il 64% dei "
         "punti in palio (il campo di casa aggiunge 60 punti di Elo).",
         f"Esempio: dalla 11ª giornata in poi la partita in cui il Leicester partiva meno favorito è {ml} ({res['data']}): risultato "
         f"atteso {fmt(num(low['prob_vittoria_attesa']), 0)}%.",
         f"Il Chelsea campione in carica scende fino a {fmt(ch[ch_min], 0)} alla {ch_min + 1}ª giornata e risale nella seconda metà: "
         "l'Elo racconta l'esonero di Mourinho (dicembre 2015) senza bisogno di leggere la classifica."],
        "Elo di Delta Scout: tutte le squadre partono da 1500 alla loro prima partita nel database, K = 30, +60 punti per il campo di casa "
        "(0 nei tornei su campo neutro). Grafico: Premier League 2015/16, stagione completa.",
        "L'Elo ha bisogno di molte partite: nelle competizioni con poche partite per squadra nel database (tornei, partite storiche) è "
        "poco informativo. Il Barcellona domina la classifica Elo perché è la squadra con più partite.",
        table(["Squadra", "Elo a fine stagione"], [[n_, fmt(v[-1], 0)] for n_, _, v, _ in sorted(series, key=lambda s: -s[2][-1])]))


def momentum_card(T):
    rs = {r["squadra"]: r for r in T if r["n"] == "778"}
    a = [int(x) for x in rs["Argentina"]["momentum_5min"].split(";") if x]
    b = [int(x) for x in rs["France"]["momentum_5min"].split(";") if x]
    chart = momentum_bars(a, b, "Argentina", "Francia")
    fa = sum(a[:16]); fb = sum(b[:16])
    pk = max(range(9, 18), key=lambda i: b[i])  # picco della Francia nel secondo tempo
    return card(
        "d-momentum", "Momentum: chi sta spingendo, minuto per minuto",
        "La finale del 2022 in un solo grafico: chi spingeva e quando.",
        f"Il momentum di Delta Scout conta i palloni toccati nell'ultimo terzo di campo ogni 5 minuti. Nella finale 2022 l'Argentina "
        f"ne tocca {fa} nei primi 80 minuti, la Francia {fb}. Eppure al 90' è 2-2: il momentum dice chi spinge, non chi segna.",
        chart, legend([("var(--s1)", "Argentina: tocchi nell'ultimo terzo ogni 5 minuti"), ("var(--s2)", "Francia")]),
        ["Come si legge: una barra lunga è una squadra che vive nell'ultimo terzo di campo. Non sono occasioni: è pressione territoriale.",
         f"Esempio: il momento migliore della Francia nel secondo tempo è tra il {pk * 5}' e il {pk * 5 + 5}' ({b[pk]} tocchi contro {a[pk]}); "
         "i due gol di Mbappé arrivano all'80' e all'81', da un rigore e da un'azione rapida, non da una lunga pressione.",
         "Per questo nei report il momentum sta accanto alla timeline degli xG: uno mostra il territorio, l'altra le occasioni."],
        "Tocchi = passaggi, ricezioni, conduzioni, dribbling, tiri e altre azioni con palla con x ≥ 80 su un campo di 120 (ultimo terzo), "
        "contati a blocchi di 5 minuti di gioco.",
        "È una misura di territorio, non di pericolosità: 10 passaggi laterali al limite dell'area pesano come 10 tocchi in area.",
        table(["Minuti", "Argentina", "Francia"], [[f"{i * 5}–{i * 5 + 5}'", x, y] for i, (x, y) in enumerate(zip(a, b))]))


def chain_card(C, G, bad):
    pool, top, lab = career(C, "xg_chain_p90")
    items = [(lab(r), num(r["xg_chain_p90"]), "var(--s1)", f"xG + xA {fmt(num(r['xg_xa_p90']), 2)}/90") for r in top]
    chart = hbars(items, d=2, label_w=230)
    best = max([r for r in G if r["n"] not in bad], key=lambda r: num(r["xg_chain"]))
    bus = next((r for r in C if "Busquets" in r["giocatore"]), None)
    return card(
        "d-chain", "xG chain: essere dentro le azioni pericolose",
        "Busquets non segna e non fa assist. Eppure c'era in quasi tutte le azioni del Barça.",
        "L'xG chain somma gli xG di tutte le azioni d'attacco a cui un giocatore ha partecipato, in qualsiasi momento: non solo tiro e "
        "assist, anche il primo passaggio dalla difesa.",
        chart, legend([("var(--s1)", "xG chain ogni 90 minuti (almeno 1.800 minuti nel database)")]),
        ["Come si legge: confrontato con xG + xA dice quanto un giocatore costruisce lontano dalla porta. Chi ha xG chain alto ma xG + xA "
         "basso è un regista.",
         (f"Esempio: Sergio Busquets ha {fmt(num(bus['xg_chain_p90']), 2)} xG chain ogni 90 minuti ma solo {fmt(num(bus['xg_xa_p90']), 2)} "
          "di xG + xA: partecipa alla costruzione, lascia ad altri la conclusione." if bus else ""),
         f"Record del database: {name(best)}, {fmt(num(best['xg_chain']), 2)} in {match_lab(best)}."],
        "Per ogni azione (possesso) che finisce con un tiro, l'xG del tiro viene assegnato a tutti i giocatori della squadra che hanno "
        f"toccato palla in quell'azione. Classifica: {len(pool)} giocatori con almeno 1.800 minuti.",
        "Premia chi gioca in squadre che tirano molto (il Barcellona domina la classifica): va confrontato con i compagni di squadra.",
        table(["Giocatore", "Squadre", "Minuti", "xG chain/90", "xG + xA/90"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), fmt(num(r["xg_chain_p90"]), 2), fmt(num(r["xg_xa_p90"]), 2)] for r in top]))


def network_card(RP, G):
    pos = {r["player_id"]: r for r in G if r["n"] == "778" and r["squadra"] == "Argentina"}
    starters = {k for k, r in pos.items() if r["titolare"] == "1"}
    cnt = defaultdict(int)
    tot = defaultdict(int)
    for r in RP:
        if r["n"] == "778" and r["squadra"] == "Argentina":
            a, b, n_ = r["passatore_id"], r["ricevente_id"], int(num(r["passaggi"]))
            tot[a] += n_
            if a in starters and b in starters:
                cnt[tuple(sorted((a, b)))] += n_
    nodes = {k: (num(pos[k]["pos_media_x"]), num(pos[k]["pos_media_y"]), tot[k], pos[k]["maglia"], name(pos[k])) for k in starters}
    edges = [(a, b, n_) for (a, b), n_ in cnt.items() if n_ >= 4]
    chart = network(nodes, edges)
    top_pair = max(cnt.items(), key=lambda kv: kv[1])
    hub = max(starters, key=lambda k: tot[k])
    names = sorted(((int(pos[k]["maglia"] or 0), name(pos[k])) for k in starters))
    return card(
        "d-rete", "La rete di passaggi: la squadra come una mappa",
        "Cerchi, linee e numeri: come si legge una rete di passaggi.",
        f"La rete di passaggi mette ogni giocatore nella sua posizione media e collega chi si è passato la palla: più spessa la linea, "
        f"più passaggi. Nella finale 2022 la coppia più cercata dell'Argentina è {name(pos[top_pair[0][0]])}–{name(pos[top_pair[0][1]])} "
        f"({top_pair[1]} passaggi).",
        chart, legend([("var(--s1)", "Argentina, finale Mondiale 2022: titolari (numero di maglia), linee da 4 passaggi in su")]),
        ["Come si legge: il cerchio più grande è chi tocca più palloni; la forma della rete mostra il modulo reale, non quello sulla "
         "carta; i buchi sono le zone dove la squadra non passa.",
         f"Esempio: {name(pos[hub])} è il giocatore con più passaggi ({tot[hub]}). Messi (10) è il "
         f"{sorted(starters, key=lambda k: -nodes[k][0]).index(next(k for k in starters if name(pos[k]) == 'Lionel Messi')) + 1}° titolare "
         "più avanzato per posizione media.",
         "Numeri di maglia: " + ", ".join(f"{m} {n_}" for m, n_ in names) + "."],
        "Passaggi riusciti tra titolari in tutta la partita (dati StatsBomb), posizioni medie dei tocchi di palla di ciascun giocatore; "
        "attacco verso destra. Nei report Delta Scout la rete è divisa anche per finestre tra un cambio e l'altro.",
        "Le posizioni medie schiacciano tutta la partita in un punto: un terzino che sale e scende risulta a metà campo. Le sostituzioni "
        "cambiano la rete, per questo i report la dividono per finestre.",
        table(["Passatore ↔ ricevente", "Passaggi"], [[f"{name(pos[a])} ↔ {name(pos[b])}", n_]
                                                     for (a, b), n_ in sorted(cnt.items(), key=lambda kv: -kv[1])[:10]]))


def recoveries_card(Tv, G, bad):
    v = [num(r["recuperi_alti"]) for r in Tv]
    med = q(v, .5)
    def avg(f):
        rs = [r for r in Tv if f(r)]
        return sum(num(r["recuperi_alti"]) for r in rs) / len(rs)
    lev = avg(lambda r: r["squadra"] == "Bayer Leverkusen" and r["stagione"] == "2023/2024")
    pep = avg(lambda r: r["squadra"] == "Barcelona" and r["allenatore"] == "Pep Guardiola")
    lei = avg(lambda r: r["squadra"] == "Leicester City" and r["stagione"] == "2015/2016")
    rec = max(Tv, key=lambda r: num(r["recuperi_alti"]))
    best = max([r for r in G if r["n"] not in bad and not is_f(r["competizione"])], key=lambda r: num(r["recuperi_alti"]))
    mk = [(med, f"mediana {fmt(med, 0)}", "var(--ink2)"), (pep, f"Barça di Guardiola: {fmt(pep, 1)}", "var(--s1)"),
          (lev, f"Leverkusen 2023/24: {fmt(lev, 1)}", "var(--s1)"), (lei, f"Leicester 2015/16: {fmt(lei, 1)}", "var(--s2)")]
    chart = histogram(v, 0, 40, 40, mk, d=0, xlab="Palloni recuperati nell'ultimo terzo di campo in una partita")
    return card(
        "d-recuperi", "Recuperi alti: rubare palla vicino alla porta",
        "Il pallone più pericoloso è quello che rubi all'avversario vicino alla sua porta.",
        f"Un recupero alto è un pallone riconquistato nell'ultimo terzo di campo, vicino alla porta avversaria. Una squadra ne fa in media {fmt(med, 0)} a partita: ogni "
        "recupero alto è un'azione che parte già vicino alla porta.",
        chart, legend([("var(--context)", "Tutte le partite del database (per squadra)"), ("var(--s1)", "Squadre di pressing"),
                       ("var(--s2)", "Squadra di blocco basso")]),
        ["Come si legge: è il risultato del pressing (il PPDA ne misura l'intensità, i recuperi alti l'efficacia).",
         f"Esempio: il Barça di Guardiola ({fmt(pep, 1)} a partita) e il Leicester 2015/16 ({fmt(lei, 1)}) hanno valori " +
         ("quasi identici con stili opposti: da solo il dato non basta a descrivere il pressing." if abs(pep - lei) < 1.5 else
          "diversi, coerenti con i due stili opposti."),
         f"Record di squadra: {match_lab(rec)}, {rec['recuperi_alti']}. Nel maschile il record individuale è di {name(best)}: "
         f"{best['recuperi_alti']} in {match_lab(best)}."],
        "Recupero = evento 'Ball Recovery' riuscito di StatsBomb (pallone vagante conquistato); alto = con x ≥ 80 su un campo di 120. "
        f"Grafico: {len(v)} prestazioni di squadra.",
        "Dipende anche dall'avversario: contro squadre che giocano molto palla a terra dalla difesa è più facile recuperare in alto.",
        table(["Esempio", "Recuperi alti"], [[l, fmt(x, 1)] for x, l, _ in mk] + [[match_lab(rec), rec["recuperi_alti"]]]))


def voto_card(V, G):
    vals = [num(v["voto"]) for v in V if v["voto"]]
    vv = {(v["n"], v["player_id"]): num(v["voto"]) for v in V if v["voto"]}
    f778 = {name(r): (vv.get(("778", r["player_id"])), r) for r in G if r["n"] == "778"}
    mes = f778.get("Lionel Messi")
    mba = f778.get("Kylian Mbappé")
    tens = sorted([(v, r) for r in G for v in [vv.get((r["n"], r["player_id"]))] if v is not None and v >= 10],
                  key=lambda x: x[1]["data"])
    mk = [(6.6, "centro della scala 6,6", "var(--ink2)")]
    if mes:
        mk.append((mes[0], f"Messi, finale 2022: {fmt(mes[0])}", "var(--s1)"))
    if mba:
        mk.append((mba[0], f"Mbappé, finale 2022: {fmt(mba[0])}", "var(--s2)"))
    chart = histogram(vals, 3, 10, 35, mk, d=0, xlab="Voto Delta Scout", ticks=7)
    over8 = 100 * sum(v >= 8 for v in vals) / len(vals)
    return card(
        "d-voto", "Il voto Delta Scout: come nasce un 7,5",
        "Il voto in pagella, ma calcolato dai dati: come funziona il voto Delta Scout.",
        f"Il voto Delta Scout confronta ogni prestazione con tutte quelle dello stesso ruolo nel database e la traduce in un voto da 3 "
        f"a 10 centrato su 6,6. Solo il {fmt(over8, 1)}% delle prestazioni arriva a 8.",
        chart, legend([("var(--context)", f"Tutti i voti del database ({len(vals):,} prestazioni)".replace(",", ".")),
                       ("var(--s1)", "Messi, finale 2022"), ("var(--s2)", "Mbappé, finale 2022")]),
        ["Come si legge: ogni statistica (gol, xG, passaggi progressivi, azioni difensive…) diventa uno scarto dalla media del ruolo; "
         "gli scarti, pesati in modo diverso per portieri, difensori, centrocampisti e attaccanti, danno il voto. ±0,2 per vittoria o "
         "sconfitta; sotto i 20 minuti 's.v.'.",
         (f"Esempio: nella finale 2022 Mbappé (tripletta) prende {fmt(mba[0])} pur avendo perso, Messi (doppietta) {fmt(mes[0])}." if mes and mba else ""),
         "Il 10 è quasi irraggiungibile: nel database ci sono solo " + str(len(tens)) + " prestazioni da 10: " +
         ", ".join(f"{name(r)} ({r['gol']} gol, {r['assist']} assist, {r['data'][:4]})" for _, r in tens[:3]) + "."],
        "Z-score di ogni statistica rispetto a tutte le prestazioni dello stesso reparto e dello stesso sesso; somma pesata (pesi pubblici "
        "in voti.py), riportata su una scala compressa agli estremi (tanh). Calcio maschile e femminile hanno medie separate.",
        "È una formula di Delta Scout, trasparente ma non una verità: i pesi sono scelte. Non vede ciò che non è nei dati (posizionamento "
        "senza palla, leadership).",
        table(["Prestazione da 10", "Partita", "Gol", "Assist"], [[name(r), match_lab(r), r["gol"], r["assist"]] for _, r in tens]))


def data360_card(G):
    rows = [r for r in G if r["n"] == "778" and num(r["eventi_360"]) >= 50]
    rows.sort(key=lambda r: -num(r["azioni_pressate_360_pct"]))
    items = [(f"{name(r)} ({'ARG' if r['squadra'] == 'Argentina' else 'FRA'})", num(r["azioni_pressate_360_pct"]),
              "var(--s1)" if r["squadra"] == "Argentina" else "var(--s2)",
              f"{fmt(num(r['avversari_5m_medi_360']), 2)} avversari entro 5 m in media") for r in rows[:12]]
    chart = hbars(items, d=0, unit="%", label_w=230)
    mes = next(r for r in rows if name(r) == "Lionel Messi")
    return card(
        "d-360", "Dati 360: cosa vede la telecamera intorno alla palla",
        "Per ogni passaggio sappiamo dove erano tutti gli altri giocatori. Ecco cosa ci si fa.",
        "I dati 360 aggiungono a ogni evento la posizione di tutti i giocatori visibili nell'inquadratura. Così si può misurare quanti "
        f"avversari aveva intorno chi toccava palla: Messi, nella finale 2022, ne aveva {fmt(num(mes['avversari_5m_medi_360']), 2)} entro "
        f"5 metri in media.",
        chart, legend([("var(--s1)", "Argentina"), ("var(--s2)", "Francia"),
                       ("var(--context)", "Barre: % delle azioni con almeno 2 avversari entro 5 metri")]),
        ["Come si legge: chi gioca con molti avversari vicino lavora in spazi stretti (trequartisti, attaccanti); i difensori centrali "
         "hanno quasi sempre spazio.",
         f"Esempio: {fmt(num(mes['azioni_pressate_360_pct']), 0)}% delle azioni di Messi nella finale avviene con almeno due avversari "
         "entro 5 metri: è il prezzo di ricevere tra le linee.",
         "Nel database i dati 360 coprono solo alcune competizioni recenti (Euro 2020 e 2024, Mondiali 2022 e femminili 2023, Bundesliga "
         "2023/24 e altre): per questo non compaiono in tutti i report."],
        "Per ogni evento con 'freeze frame' 360 si contano gli avversari entro 5 metri dal giocatore in azione. Solo giocatori con "
        "almeno 50 eventi 360 nella partita.",
        "La telecamera non inquadra sempre tutto il campo: gli avversari fuori dall'inquadratura non vengono contati.",
        table(["Giocatore", "Squadra", "Eventi 360", "Avversari entro 5 m", "% azioni con ≥ 2 avversari"],
              [[name(r), it(r["squadra"]), r["eventi_360"], fmt(num(r["avversari_5m_medi_360"]), 2), fmt(num(r["azioni_pressate_360_pct"]), 0) + "%"]
               for r in rows]))


def heatmap_card(G):
    def agg(f):
        g = [0.0] * 24
        n_ = 0
        for r in G:
            if r["player_id"] == MESSI and f(r) and r["heatmap_6x4"]:
                for i, v in enumerate(r["heatmap_6x4"].split(";")):
                    g[i] += num(v)
                n_ += 1
        tot = sum(g) or 1
        return [[100 * g[j * 6 + i] / tot for i in range(6)] for j in range(4)], n_
    early, ne = agg(lambda r: r["data"] < "2009-01-01")
    late, nl = agg(lambda r: r["data"] >= "2018-07-01" and r["squadra"] == "Barcelona")
    f = lambda v: fmt(v, 0) + "%"
    chart = ('<div class="sm sm2">' + f'<div><p class="head">Messi 2004–2008 ({ne} partite)</p>{grid_heat(early, 6, 4, "heatmap", f, "quota dei tocchi")}</div>'
             f'<div><p class="head">Messi 2018–2021 ({nl} partite)</p>{grid_heat(late, 6, 4, "heatmap", f, "quota dei tocchi")}</div></div>')
    last_e = sum(early[j][5] + early[j][4] for j in range(4))
    last_l = sum(late[j][5] + late[j][4] for j in range(4))
    right_e = sum(early[3]) + sum(early[2])
    right_l = sum(late[3]) + sum(late[2])
    return card(
        "d-heatmap", "La heatmap: dove gioca davvero un giocatore",
        "Lo stesso giocatore, 10 anni dopo: la heatmap racconta la carriera di Messi.",
        f"La heatmap divide il campo in zone e mostra in quale percentuale un giocatore tocca palla in ciascuna. Il Messi degli inizi "
        f"toccava il {fmt(right_e, 0)}% dei palloni nella metà destra del campo, quello del 2018–2021 il {fmt(right_l, 0)}%.",
        chart, legend([("var(--s1)", "Quota dei tocchi di palla in ogni zona (attacco verso destra, fascia destra in basso)")]),
        ["Come si legge: zone scure = dove il giocatore vive. Il campo è orientato con l'attacco verso destra; in basso la fascia destra.",
         f"Esempio: la quota di palloni toccati nell'ultimo terzo resta quasi la stessa ({fmt(last_e, 0)}% e {fmt(last_l, 0)}%): Messi "
         "non arretra, si sposta verso il centro. Da ala destra a giocatore che parte da destra e taglia dentro.",
         "Nei report Delta Scout ci sono le heatmap di ogni giocatore e di ogni squadra, insieme alle mappe di passaggi e ricezioni."],
        "Tocchi di palla (passaggi, ricezioni, conduzioni, dribbling, tiri, duelli) contati in una griglia 6 × 4 e divisi per il totale. "
        "Tutte le partite di Messi nel database nei due periodi.",
        "La griglia 6 × 4 è grossolana per scelta: con zone più piccole servirebbero molte più partite per avere dati stabili.",
        table(["Periodo", "Partite", "Tocchi nell'ultimo terzo", "Tocchi nella metà destra"],
              [["2004–2008", ne, fmt(last_e, 0) + "%", fmt(right_e, 0) + "%"], ["2018–2021", nl, fmt(last_l, 0) + "%", fmt(right_l, 0) + "%"]]))


def defence_card(C):
    pool = [r for r in C if num(r["minuti"]) >= 1800]
    key = lambda r: num(r["contrasti_vinti_p90"]) + num(r["intercetti_p90"]) + num(r["recuperi_p90"])
    top = sorted(pool, key=lambda r: -key(r))[:10]
    lab = lambda r: name(r) + (" (F)" if r["sesso"] == "F" else "")
    from studi2 import stacked_hbars
    items = [(lab(r), [num(r["contrasti_vinti_p90"]), num(r["intercetti_p90"]), num(r["recuperi_p90"])], f"aerei vinti {fmt(num(r['aerei_pct']), 0)}%")
             for r in top]
    chart = stacked_hbars(items, ["Contrasti vinti", "Intercetti", "Recuperi"], ["var(--s1)", "var(--s2)", "var(--neutral)"], d=1, label_w=210)
    kante = next((r for r in pool if "Kanté" in r["giocatore"]), None)
    return card(
        "d-difesa", "Contrasti, intercetti, recuperi: i numeri di chi difende",
        "Come si misura un difensore se non segna e non fa assist?",
        "Le azioni difensive con palla sono tre: il contrasto vinto (togliere palla all'avversario), l'intercetto (rubare un passaggio) e "
        "il recupero (prendere un pallone vagante). Sommate, dicono quanti palloni un giocatore restituisce alla squadra.",
        chart, legend([("var(--s1)", "Contrasti vinti ogni 90 minuti"), ("var(--s2)", "Intercetti"), ("var(--neutral)", "Recuperi")]),
        ["Come si legge: chi gioca in squadre che difendono molto ha più occasioni di farne. Il dato va letto insieme al possesso della "
         "squadra e alla percentuale di duelli aerei vinti.",
         (f"Esempio: N'Golo Kanté (Leicester 2015/16 e Francia): {fmt(key(kante), 1)} azioni difensive ogni 90 minuti, "
          f"di cui {fmt(num(kante['intercetti_p90']), 1)} intercetti." if kante else ""),
         "Il miglior difensore spesso non deve intervenire: un buon posizionamento evita il contrasto, e i dati non lo vedono."],
        f"Somma ogni 90 minuti di contrasti vinti, intercetti e recuperi (eventi StatsBomb). Classifica: {len(pool)} giocatori con almeno "
        "1.800 minuti.",
        "Non misura la qualità del posizionamento né i duelli evitati; nelle squadre con poco possesso i numeri sono gonfiati.",
        table(["Giocatore", "Squadre", "Minuti", "Contrasti vinti/90", "Intercetti/90", "Recuperi/90", "Aerei vinti"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), fmt(num(r["contrasti_vinti_p90"]), 1), fmt(num(r["intercetti_p90"]), 1),
                fmt(num(r["recuperi_p90"]), 1), fmt(num(r["aerei_pct"]), 0) + "%"] for r in top]))


def saves_card(C, G, bad):
    pool = [r for r in C if num(r["minuti"]) >= 2700 and r["ruolo"] == "Portiere"]
    top = sorted(pool, key=lambda r: -num(r["parate_pct"]))[:10]
    lab = lambda r: name(r) + (" (F)" if r["sesso"] == "F" else "")
    items = [(lab(r), num(r["parate_pct"]), "var(--s1)", f"{int(num(r['parate']))} parate, {int(num(r['gol_subiti_portiere']))} gol subiti") for r in top]
    chart = hbars(items, d=1, unit="%", label_w=230)
    med = q([num(r["parate_pct"]) for r in pool], .5)
    best = max([r for r in G if r["n"] not in bad], key=lambda r: num(r["parate"]))
    return card(
        "d-parate", "Percentuale di parate: il numero dei portieri",
        "Quanti tiri in porta para un buon portiere? Meno di quanto pensi.",
        f"La percentuale di parate è la quota di tiri in porta che il portiere non lascia entrare. Il portiere tipico del database "
        f"ne para il {fmt(med, 0)}%; anche il migliore, {lab(top[0])}, lascia passare il {fmt(100 - num(top[0]['parate_pct']), 0)}% dei tiri in porta.",
        chart, legend([("var(--s1)", "Percentuale di parate (portieri con almeno 2.700 minuti nel database)")]),
        ["Come si legge: va letta con la qualità dei tiri subiti. Un portiere di una squadra forte riceve pochi tiri ma spesso difficili.",
         f"Esempio: il record di parate in una partita è di {name(best)}, {best['parate']} in {match_lab(best)}.",
         "Lo studio 'Le portiere parano come i portieri' mostra che la percentuale è la stessa nel calcio maschile e femminile."],
        "Parate / (parate + gol subiti), cioè sui tiri in porta subiti dal portiere, rigori compresi. "
        f"Classifica: {len(pool)} portieri con almeno 2.700 minuti.",
        "Senza un modello 'post-tiro' (che valuta la traiettoria) non si sa quanto fossero difficili le parate: i dati Open non lo "
        "includono.",
        table(["Portiere", "Squadre", "Minuti", "Parate", "Gol subiti", "% parate"],
              [[lab(r), r["squadre"][:40], int(num(r["minuti"])), int(num(r["parate"])), int(num(r["gol_subiti_portiere"])),
                fmt(num(r["parate_pct"]), 1) + "%"] for r in top]))


# abbinamento settimana per settimana con studi2.CALENDAR (stessa lunghezza)
CALENDAR_DATI = ["d-xg", "d-xa", "d-dribbling", "d-ppda", "d-parate", "d-sca", "d-possesso", "d-xpts", "d-conduzioni", "d-tilt",
                 "d-pressioni", "d-xt", "d-progressivi", "d-elo", "d-momentum", "d-chain", "d-rete", "d-recuperi", "d-voto", "d-360",
                 "d-heatmap", "d-difesa"]
TAGS = {"d-xg": "#xG #expectedgoals", "d-xa": "#xA #assist", "d-dribbling": "#dribbling", "d-ppda": "#pressing #PPDA", "d-parate": "#portieri",
        "d-sca": "#SCA", "d-possesso": "#possesso", "d-xpts": "#xPts #puntiattesi", "d-conduzioni": "#conduzioni", "d-tilt": "#fieldtilt",
        "d-pressioni": "#pressing #gegenpressing", "d-xt": "#xT #expectedthreat", "d-progressivi": "#passaggiprogressivi", "d-elo": "#elo",
        "d-momentum": "#momentum #finalemondiale", "d-chain": "#xGchain #busquets", "d-rete": "#passingnetwork #retedipassaggi",
        "d-recuperi": "#pressing #recuperi", "d-voto": "#pagelle #voto", "d-360": "#dati360 #statsbomb360", "d-heatmap": "#heatmap #messi",
        "d-difesa": "#difesa #kante"}


def build(T, Tv, G, SH, C, V, E, RP, bad, anom):
    SCORE.update({(r["n"], r["squadra"]): (r["gol"], r["gol_subiti"]) for r in T})
    cards = [xg_card(SH, bad), xa_card(C, G, bad), dribbling_card(C, G, bad, T), ppda_card(T, Tv), saves_card(C, G, bad), sca_card(C, G, bad),
             possession_card(Tv, anom), xpts_card(T), carries_card(C, G, bad), tilt_card(Tv), pressing_card(Tv, G, bad), xt_card(G, bad),
             progressive_card(C, G, bad), elo_card(E, T), momentum_card(T), chain_card(C, G, bad), network_card(RP, G),
             recoveries_card(Tv, G, bad), voto_card(V, G), data360_card(G), heatmap_card(G), defence_card(C)]
    for c in cards:
        c["body"] = [b for b in c["body"] if b]
    return cards
