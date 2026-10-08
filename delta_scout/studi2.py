"""Delta Scout - studi 14-22 (Barcellona, Messi, finali, leggende prima dell'era dei dati) e pacchetti social.

Importato da studi.py: usa gli stessi CSV di output/ e gli stessi grafici SVG.
"""
from collections import Counter, defaultdict

from studi import FONT, e, fmt, hbars, legend, num, svg_open, table, watermark

MESSI = "5503"
PELE, CRUYFF, MARADONA, NEESKENS = "39712", "39713", "38641", "39721"

IT = {"Brazil": "Brasile", "Sweden": "Svezia", "Italy": "Italia", "Germany": "Germania Ovest", "Netherlands": "Olanda",
      "Argentina": "Argentina", "France": "Francia", "Croatia": "Croazia", "Inter Milan": "Inter", "AS Monaco": "Monaco",
      "FC Porto": "Porto", "AC Milan": "Milan", "Barcelona": "Barcellona", "Bayern Munich": "Bayern Monaco",
      "Tottenham Hotspur": "Tottenham", "Juventus W": "Juventus", "German DR": "Germania Est", "England": "Inghilterra",
      "Belgium": "Belgio", "Czechoslovakia": "Cecoslovacchia", "Romania": "Romania", "Peru": "Perù", "Uruguay": "Uruguay",
      "Mexico": "Messico", "Soviet Union U20": "URSS U20", "Argentina U20": "Argentina U20", "Las Palmas": "Las Palmas",
      "Real Madrid": "Real Madrid", "Athletic Club": "Athletic Bilbao", "VfB Stuttgart": "Stoccarda", "NY Cosmos": "New York Cosmos",
      "Seattle Sounders": "Seattle Sounders", "Boca Juniors": "Boca Juniors", "River Plate": "River Plate", "Napoli": "Napoli"}
it = lambda t: IT.get(t, t)
# finali vinte ai rigori (la serie finale non è negli eventi, quindi non entra negli xG)
SHOOTOUT = {"126": "Liverpool", "131": "Chelsea", "135": "Real Madrid", "778": "Argentina"}


def by_match(T):
    m = defaultdict(list)
    for r in T:
        m[r["n"]].append(r)
    return m


# ------------------------------------------------------------------------------------------- grafici nuovi
def season_chart(seasons, coaches, panels, w=680):
    """Più pannelli a linee impilati sulle stagioni, con le fasce degli allenatori.
    panels: [(titolo, [(nome serie, colore, valori)], decimali, unità)]."""
    pad_l, pad_r, top, ph, gap = 40, 26, 44, 112, 26
    h = top + len(panels) * (ph + gap) + 22
    n = len(seasons)
    X = lambda i: pad_l + (w - pad_l - pad_r) * (i + 0.5) / n
    cw = (w - pad_l - pad_r) / n
    s = [svg_open(w, h, "stagioni")]
    # fasce allenatori
    runs = []
    for i, c in enumerate(coaches):
        if runs and runs[-1][0] == c:
            runs[-1][2] = i
        else:
            runs.append([c, i, i])
    for k, (c, a, b) in enumerate(runs):
        x0, x1 = pad_l + cw * a, pad_l + cw * (b + 1)
        if k % 2 == 0:
            s.append(f'<rect x="{x0:.1f}" y="{top - 6}" width="{x1 - x0:.1f}" height="{h - top - 16}" fill="var(--grid)" opacity="0.6"/>')
        s.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{14 if k % 2 == 0 else 30}" font-size="11" font-weight="600" fill="var(--ink2)" '
                 f'text-anchor="middle">{e(c)}</text>'
                 f'<line x1="{(x0 + x1) / 2:.1f}" x2="{(x0 + x1) / 2:.1f}" y1="{18 if k % 2 == 0 else 34}" y2="{top - 6}" stroke="var(--axis)"/>')
    for p, (title, series, d, unit) in enumerate(panels):
        y0 = top + p * (ph + gap) + 18
        vals = [v for _, _, vs in series for v in vs if v is not None]
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1
        lo, hi = lo - span * 0.2, hi + span * 0.3
        Y = lambda v: y0 + (ph - 18) * (1 - (v - lo) / (hi - lo))
        s.append(f'<text x="{pad_l}" y="{y0 - 6}" font-size="12.5" font-weight="600" fill="var(--ink)">{e(title)}</text>')
        for t in (lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.75):
            s.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="var(--line)" stroke-width="1"/>'
                     f'<text x="{pad_l - 6}" y="{Y(t) + 3:.1f}" font-size="9.5" fill="var(--muted)" text-anchor="end">{fmt(t, d if d < 2 else 1)}</text>')
        for name, col, vs in series:
            pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vs) if v is not None)
            s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>')
            ok = [i for i, v in enumerate(vs) if v is not None]
            mark = {ok[0], ok[-1], max(ok, key=lambda i: vs[i]), min(ok, key=lambda i: vs[i])}
            for i in ok:
                s.append(f'<g><title>{e(seasons[i])} – {e(name)}: {fmt(vs[i], d)}{unit}</title>'
                         f'<circle cx="{X(i):.1f}" cy="{Y(vs[i]):.1f}" r="9" fill="transparent"/>'
                         f'<circle cx="{X(i):.1f}" cy="{Y(vs[i]):.1f}" r="3.5" fill="{col}" stroke="var(--surface)" stroke-width="1.5"/></g>')
                if i in mark:
                    s.append(f'<text x="{X(i):.1f}" y="{Y(vs[i]) - 8:.1f}" font-size="10.5" font-weight="600" fill="var(--ink)" '
                             f'text-anchor="middle">{fmt(vs[i], d)}{unit}</text>')
    for i, lab in enumerate(seasons):
        short = lab[2:4] + "/" + lab[7:9] if "/" in lab else lab
        s.append(f'<text x="{X(i):.1f}" y="{h - 8}" font-size="9.5" fill="var(--muted)" text-anchor="middle">{e(short)}</text>')
    s.append(watermark(w, h).replace(f'y="{h - 4}"', f'y="{h - 22}"') + "</svg>")
    return "".join(s)


def dumbbell(rows, w=680, row=30, label_w=250, score_w=92):
    """Finali: un punto per gli xG di chi ha vinto e uno per chi ha perso.
    rows: [(etichetta, xg vincitrice, xg sconfitta, testo risultato, nota)]."""
    h = row * len(rows) + 40
    hi = max(max(a, b) for _, a, b, _, _ in rows) * 1.08
    x0, x1 = label_w, w - score_w
    X = lambda v: x0 + (x1 - x0) * v / hi
    s = [svg_open(w, h, "xG nelle finali")]
    for k in range(0, int(hi) + 1):
        s.append(f'<line x1="{X(k):.1f}" x2="{X(k):.1f}" y1="8" y2="{h - 28}" stroke="var(--grid)"/>'
                 f'<text x="{X(k):.1f}" y="{h - 14}" font-size="10" fill="var(--muted)" text-anchor="middle">{k}</text>')
    s.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{h - 1}" font-size="10.5" fill="var(--muted)" text-anchor="middle">xG (rigori in partita compresi)</text>')
    for i, (lab, a, b, score, note) in enumerate(rows):
        y = 18 + i * row
        s.append(f'<g><title>{e(lab)} {e(score)}: xG vincitrice {fmt(a, 2)}, sconfitta {fmt(b, 2)}{" – " + e(note) if note else ""}</title>'
                 f'<line x1="{X(min(a, b)):.1f}" x2="{X(max(a, b)):.1f}" y1="{y}" y2="{y}" stroke="var(--axis)" stroke-width="3"/>'
                 f'<circle cx="{X(b):.1f}" cy="{y}" r="6.5" fill="var(--s2)" stroke="var(--surface)" stroke-width="2"/>'
                 f'<circle cx="{X(a):.1f}" cy="{y}" r="6.5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/></g>'
                 f'<text x="{label_w - 12}" y="{y + 4}" font-size="12" fill="var(--ink)" text-anchor="end">{e(lab)}</text>'
                 f'<text x="{x1 + 12}" y="{y + 4}" font-size="12" font-weight="600" fill="var(--ink)">{e(score)}</text>')
    s.append("</svg>")
    return "".join(s)


def bar_panel(title, items, d=1, unit="", w=330, row=24, label_w=120, ref=None):
    """Pannello di barre orizzontali con titolo, per piccoli multipli. items: [(etichetta, valore, colore)].
    ref: (valore, etichetta) per una linea di riferimento verticale."""
    h = 26 + row * len(items) + (16 if ref else 6)
    hi = max(v for _, v, _ in items + ([("", ref[0], "")] if ref else [])) * 1.22
    X = lambda v: label_w + (w - label_w - 10) * v / hi
    s = [svg_open(w, h, title), f'<text x="0" y="14" font-size="12.5" font-weight="600" fill="var(--ink)">{e(title)}</text>']
    for i, (lab, v, col) in enumerate(items):
        y = 26 + i * row
        bw = X(v) - label_w
        s.append(f'<g><title>{e(lab)}: {fmt(v, d)}{unit}</title><rect x="{label_w}" y="{y}" width="{max(bw, 1):.1f}" height="{row - 8}" rx="3" fill="{col}"/></g>'
                 f'<text x="{label_w - 8}" y="{y + row - 12}" font-size="11.5" fill="var(--ink)" text-anchor="end">{e(lab)}</text>'
                 f'<text x="{X(v) + 5:.1f}" y="{y + row - 12}" font-size="11" font-weight="600" fill="var(--ink)">{fmt(v, d)}{unit}</text>')
    if ref:
        s.append(f'<line x1="{X(ref[0]):.1f}" x2="{X(ref[0]):.1f}" y1="22" y2="{h - 14}" stroke="var(--ink2)" stroke-dasharray="3 3"/>'
                 f'<text x="{X(ref[0]):.1f}" y="{h - 3}" font-size="9.5" fill="var(--muted)" text-anchor="middle">{e(ref[1])}</text>')
    s.append("</svg>")
    return "".join(s)


def stacked_hbars(items, names, colors, d=2, w=680, row=26, label_w=170):
    """Barre orizzontali impilate. items: [(etichetta, [valori], nota)]."""
    h = row * len(items) + 30
    hi = max(sum(v) for _, v, _ in items)
    note_w = 7 * max(len(n) for _, _, n in items) + 60  # spazio a destra per valore e nota
    X = lambda v: label_w + (w - label_w - note_w) * v / hi
    s = [svg_open(w, h, "barre impilate")]
    for i, (lab, vals, note) in enumerate(items):
        y = 6 + i * row
        x = label_w
        for j, v in enumerate(vals):
            bw = X(v) - label_w
            s.append(f'<g><title>{e(lab)} – {e(names[j])}: {fmt(v, d)}</title><rect x="{x:.1f}" y="{y}" width="{max(bw - 1, 0):.1f}" '
                     f'height="{row - 9}" rx="2" fill="{colors[j]}"/></g>')
            x += bw
        s.append(f'<text x="{label_w - 10}" y="{y + row - 13}" font-size="12" fill="var(--ink)" text-anchor="end">{e(lab)}</text>'
                 f'<text x="{x + 6:.1f}" y="{y + row - 13}" font-size="11.5" font-weight="600" fill="var(--ink)">{fmt(sum(vals), d)}'
                 f'<tspan font-weight="400" fill="var(--muted)">{(" · " + e(note)) if note else ""}</tspan></text>')
    s.append(watermark(w, h) + "</svg>")
    return "".join(s)


def strips(rows, w=680, row=124, label_w=0):
    """Distribuzione di riferimento (punti grigi) e partite evidenziate (punti colorati con etichetta).
    rows: [(titolo, lo, hi, valori di riferimento, [(valore, etichetta)], nota asse)]."""
    h = row * len(rows) + 10
    s = [svg_open(w, h, "distribuzioni")]
    for i, (title, lo, hi, ref, marks, axis) in enumerate(rows):
        y0 = 10 + i * row
        X = lambda v: 14 + (w - 28) * (min(max(v, lo), hi) - lo) / (hi - lo)
        cy = y0 + 84
        s.append(f'<text x="0" y="{y0 + 4}" font-size="12.5" font-weight="600" fill="var(--ink)">{e(title)}</text>')
        for k, v in enumerate(sorted(ref)):
            jit = ((k * 7919) % 17 - 8) * 1.1
            s.append(f'<circle cx="{X(v):.1f}" cy="{cy + jit:.1f}" r="2.6" fill="var(--context)" opacity="0.8"/>')
        for k in range(5):
            t = lo + (hi - lo) * k / 4
            s.append(f'<text x="{X(t):.1f}" y="{cy + 30}" font-size="9.5" fill="var(--muted)" text-anchor="middle">{fmt(t, 0)}</text>')
        s.append(f'<text x="{w - 14}" y="{y0 + 4}" font-size="10" fill="var(--muted)" text-anchor="end">{e(axis)}</text>')
        placed = []
        for v, lab in sorted(marks):
            lx = X(v)
            lvl = 0
            tw = 5.6 * len(lab) + 8
            while any(abs(lx - p) < (tw + pw) / 2 and l == lvl for p, l, pw in placed):
                lvl += 1
            placed.append((lx, lvl, tw))
            ly = cy - 16 - lvl * 13
            s.append(f'<line x1="{lx:.1f}" x2="{lx:.1f}" y1="{ly + 3:.1f}" y2="{cy - 6}" stroke="var(--axis)" stroke-width="0.8"/>')
            s.append(f'<g><title>{e(lab)}: {fmt(v, 1)}</title><circle cx="{lx:.1f}" cy="{cy}" r="5.5" fill="var(--s1)" stroke="var(--surface)" stroke-width="1.5"/></g>'
                     f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9.5" fill="var(--ink)" text-anchor="middle">{e(lab)}</text>')
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------------------------------- studi
def barca_study(T):
    rows = [r for r in T if r["squadra"] == "Barcelona" and r["competizione"] == "La Liga" and r["stagione"] >= "2004/2005"]
    by = defaultdict(list)
    for r in rows:
        by[r["stagione"]].append(r)
    seasons = sorted(by)
    COACH = {"Frank Rijkaard": "Rijkaard", "Pep Guardiola": "Guardiola", "Tito Vilanova": "Vilanova", "Gerardo Martino": "Martino",
             "Luis Enrique": "Luis Enrique", "Ernesto Valverde": "Valverde", "Quique Setién": "Setién", "Ronald Koeman": "Koeman"}
    coaches = []
    for s_ in seasons:
        c = Counter(r["allenatore"] for r in by[s_] if r["allenatore"]).most_common()
        name = c[0][0] if c else ""
        if s_ == "2012/2013":
            name = "Tito Vilanova"  # nella fonte l'allenatore manca in 28 partite su 32: era Vilanova (Roura ad interim durante la malattia)
        coaches.append(COACH.get(name, name))
    pts = lambda r: 3 if r["esito"] == "V" else 1 if r["esito"] == "N" else 0
    avg = lambda rs, k: sum(num(r[k]) for r in rs) / len(rs)
    ppg = [sum(pts(r) for r in by[s_]) / len(by[s_]) for s_ in seasons]
    xg = [avg(by[s_], "xg") for s_ in seasons]
    xga = [avg(by[s_], "xg_subiti") for s_ in seasons]
    poss = [avg(by[s_], "possesso_pct") for s_ in seasons]
    ppda = [avg(by[s_], "ppda") for s_ in seasons]
    chart = season_chart(seasons, coaches, [
        ("Punti a partita", [("Punti", "var(--s1)", ppg)], 2, ""),
        ("xG a partita: creati e concessi", [("xG creati", "var(--s1)", xg), ("xG concessi", "var(--s2)", xga)], 2, ""),
        ("Possesso palla", [("Possesso", "var(--s1)", poss)], 0, "%"),
        ("PPDA: passaggi concessi per azione difensiva (più basso = pressing più alto)", [("PPDA", "var(--s1)", ppda)], 1, "")])
    # aggregati per allenatore (stagione in cui ha allenato la maggioranza delle partite)
    agg = defaultdict(list)
    for s_, c in zip(seasons, coaches):
        agg[c] += by[s_]
    order = list(dict.fromkeys(coaches))
    co = {c: dict(n=len(agg[c]), ppg=sum(pts(r) for r in agg[c]) / len(agg[c]), xg=avg(agg[c], "xg"), xga=avg(agg[c], "xg_subiti"),
                  poss=avg(agg[c], "possesso_pct"), ppda=avg(agg[c], "ppda"), tilt=avg(agg[c], "field_tilt_pct")) for c in order}
    g, k = co["Guardiola"], co["Koeman"]
    tab = table(["Stagione", "Allenatore", "Partite", "Punti/partita", "xG creati", "xG concessi", "Possesso", "PPDA", "Field tilt"],
                [[s_, c, len(by[s_]), fmt(p, 2), fmt(a, 2), fmt(b, 2), fmt(q, 0) + "%", fmt(d), fmt(avg(by[s_], "field_tilt_pct"), 0) + "%"]
                 for s_, c, p, a, b, q, d in zip(seasons, coaches, ppg, xg, xga, poss, ppda)] +
                [[f"Totale {c}", "", v["n"], fmt(v["ppg"], 2), fmt(v["xg"], 2), fmt(v["xga"], 2), fmt(v["poss"], 0) + "%", fmt(v["ppda"]),
                  fmt(v["tilt"], 0) + "%"] for c, v in co.items()])
    best = max(order, key=lambda c: co[c]["xg"] - co[c]["xga"] if co[c]["n"] >= 30 else -9)
    return dict(
        id="barcellona", kicker="Squadre", title="Il Barcellona in 17 stagioni: da Rijkaard a Koeman",
        headline=f"Con Guardiola il Barça teneva il {fmt(g['poss'], 0)}% della palla, pressava con un PPDA di {fmt(g['ppda'])} e concedeva "
                 f"{fmt(g['xga'], 2)} xG a partita; con Koeman il possesso scende al {fmt(k['poss'], 0)}%, il PPDA sale a {fmt(k['ppda'])} "
                 f"e gli xG concessi a {fmt(k['xga'], 2)}.",
        hook="Il Barcellona di Messi, una stagione alla volta: cosa è cambiato davvero?",
        chart=chart, legend=legend([("var(--s1)", "Valore della stagione (xG creati nel secondo pannello)"), ("var(--s2)", "xG concessi"),
                                    ("var(--grid)", "Fasce: allenatore della maggior parte delle partite")]),
        body=[f"Il pressing è la metrica che cambia di più: da circa {fmt(min(ppda[4:8]), 0)}–{fmt(max(ppda[4:8]), 0)} passaggi concessi per azione "
              f"difensiva negli anni di Guardiola a {fmt(ppda[-1])} nell'ultima stagione. Il Barça ha continuato ad avere la palla, ma l'ha "
              "riconquistata sempre più tardi e più in basso.",
              f"Per differenza tra xG creati e concessi l'allenatore migliore del periodo è {best} "
              f"({fmt(co[best]['xg'], 2)} contro {fmt(co[best]['xga'], 2)} a partita)."],
        method="Solo Liga, medie per partita in ogni stagione. Allenatore: quello indicato nella fonte per la maggior parte delle partite "
               "della stagione (nel 2012/13 manca in 28 partite: era Tito Vilanova). PPDA = passaggi dell'avversario nei suoi 60 metri "
               "diviso le azioni difensive del Barça nella stessa zona.",
        caveat="Fino al 2014/15 il dataset contiene quasi solo le partite in cui ha giocato Messi (7 nel 2004/05, 17 nel 2005/06): i punti a "
               "partita di quelle stagioni sono più alti di quelli reali. Dal 2015/16 le stagioni sono complete o quasi.",
        table=tab)


def messi_study(T, G):
    B = {r["n"] for r in T if r["squadra"] == "Barcelona" and r["competizione"] == "La Liga" and r["stagione"] >= "2005/2006"}
    s = defaultdict(lambda: defaultdict(float))
    for r in G:
        if r["n"] in B and r["squadra"] == "Barcelona":
            a = s[r["stagione"]]
            for k in ("npxg", "xa", "gol", "assist", "sca"):
                a["T" + k] += num(r[k])
                if r["player_id"] == MESSI:
                    a[k] += num(r[k])
            if r["player_id"] == MESSI:
                a["p"] += 1
                a["min"] += num(r["minuti"])
    seasons = sorted(s)
    share = lambda a, ks: 100 * sum(a[k] for k in ks) / sum(a["T" + k] for k in ks)
    xs = [share(s[x], ("npxg", "xa")) for x in seasons]
    gs = [share(s[x], ("gol", "assist")) for x in seasons]
    sc = [share(s[x], ("sca",)) for x in seasons]
    coaches = []
    for x in seasons:
        c = Counter(r["allenatore"] for r in T if r["n"] in B and r["stagione"] == x and r["squadra"] == "Barcelona" and r["allenatore"]).most_common(1)
        coaches.append((c[0][0].split()[-1] if c else "Vilanova").replace("Enrique", "L. Enrique"))
    chart = season_chart(seasons, coaches, [
        ("Quota di Messi su gol + assist del Barça", [("Gol + assist", "var(--s1)", gs)], 0, "%"),
        ("Quota di Messi su xG (senza rigori) + xA del Barça", [("xG + xA", "var(--s1)", xs)], 0, "%"),
        ("Quota di Messi sulle azioni che portano al tiro (SCA)", [("SCA", "var(--s1)", sc)], 0, "%")])
    tab = table(["Stagione", "Partite di Messi", "Minuti", "Gol", "Assist", "Quota gol+assist", "Quota xG+xA", "Quota SCA"],
                [[x, int(s[x]["p"]), int(s[x]["min"]), int(s[x]["gol"]), int(s[x]["assist"]), fmt(g_, 0) + "%", fmt(a_, 0) + "%", fmt(c_, 0) + "%"]
                 for x, g_, a_, c_ in zip(seasons, gs, xs, sc)])
    ig = max(range(len(seasons)), key=lambda i: gs[i])
    ix = max(range(len(seasons)), key=lambda i: xs[i])
    last = seasons[-1]
    return dict(
        id="messi", kicker="Giocatori", title="Messi-dipendenza: quanto del Barcellona passava da un solo giocatore",
        headline=f"Nel {seasons[ig]} Messi ha firmato il {fmt(gs[ig], 0)}% di gol e assist del Barça in Liga; per qualità delle occasioni "
                 f"(xG + xA) il picco è il {seasons[ix]}, con il {fmt(xs[ix], 0)}%. Uno su undici in campo, quasi un terzo della produzione.",
        hook="Un giocatore su undici. Quanto del Barcellona era Messi?",
        chart=chart, legend=legend([("var(--s1)", "Quota di Messi sul totale della squadra"), ("var(--grid)", "Fasce: allenatore")]),
        body=[f"La dipendenza cresce nel tempo invece di calare: nel {last}, a 33 anni, Messi valeva ancora il {fmt(gs[-1], 0)}% di gol e assist "
              f"e il {fmt(sc[-1], 0)}% delle azioni da tiro della squadra.",
              f"Il primo picco coincide con il passaggio da esterno a 'falso nove' (2009–2011): la quota di xG + xA passa dal {fmt(xs[3], 0)}% "
              f"del {seasons[3]} al {fmt(xs[5], 0)}% del {seasons[5]}."],
        method="Solo Liga, tutte le partite del Barcellona presenti nel dataset per stagione. Quota = valore di Messi diviso il totale di "
               "tutti i giocatori del Barça nelle stesse partite. xG senza rigori; xA = xG dei tiri nati da un suo passaggio; SCA = le due "
               "azioni offensive che precedono un tiro.",
        caveat="Fino al 2014/15 il dataset contiene quasi solo partite in cui Messi era in campo: la quota misura il suo peso quando gioca, "
               "non tiene conto delle partite saltate. Il 2004/05 (7 presenze, 91 minuti) è escluso.",
        table=tab)


def finals_rows(T, ns, label):
    M = by_match(T)
    rows, tab, n_more = [], [], 0
    for nn in ns:
        a, b = sorted(M[nn], key=lambda r: r["casa_trasferta"] != "casa")
        ga, gb = int(num(a["gol"])), int(num(b["gol"]))
        if ga == gb:
            w = a if SHOOTOUT[nn] == a["squadra"] else b
            note = "vinta ai rigori"
        else:
            w = a if ga > gb else b
            note = ""
        l_ = b if w is a else a
        xw, xl = num(w["xg"]), num(l_["xg"])
        n_more += xw > xl
        yr = a["data"][:4]
        rows.append((f"{yr} {it(w['squadra'])}–{it(l_['squadra'])}", xw, xl,
                     f"{int(num(w['gol']))}-{int(num(l_['gol']))}" + (" (rig.)" if note else ""), note))
        tab.append([nn, a["data"], label(a), it(w["squadra"]), f"{int(num(w['gol']))}-{int(num(l_['gol']))}" + (" d.c.r." if note else ""),
                    it(l_["squadra"]), fmt(xw, 2), fmt(xl, 2), int(num(w["tiri"])), int(num(l_["tiri"])), fmt(num(w["possesso_pct"]), 0) + "%"])
    return rows, tab, n_more


def wc_finals_study(T):
    ns = ["633", "640", "646", "649", "714", "778"]
    rows, tab, n_more = finals_rows(T, ns, lambda r: "Finale" + (" (indicata come semifinale nella fonte)" if r["n"] == "649" else ""))
    chart = dumbbell(rows)
    big = max(rows, key=lambda r: r[2] - r[1])
    return dict(
        id="finali-mondiali", kicker="Partite", title="Tutte le finali dei Mondiali nel dataset, misurate con gli xG",
        headline=f"In {n_more} finali su {len(rows)} ha vinto chi ha creato di più. {big[0][5:]} ({big[3]}, {big[0][:4]}) è la più "
                 f"'ingiusta': la squadra sconfitta aveva {fmt(big[2], 2)} xG contro {fmt(big[1], 2)}.",
        hook="Le finali dei Mondiali le vince sempre il più forte? I dati dicono di no.",
        chart=chart, legend=legend([("var(--s1)", "xG della squadra che ha vinto"), ("var(--s2)", "xG della squadra che ha perso")]),
        body=["Il Brasile del 1958 e del 1970 ha dominato anche nelle occasioni: oltre 2,7 xG in entrambe le finali.",
              "Olanda 1974, Germania Ovest 1986 e Croazia 2018 hanno perso creando più dei vincitori. Nel 2018 la Francia ha segnato 4 gol "
              "con 1,10 xG: un autogol e un rigore pesano molto più di quanto dicano le occasioni.",
              "La finale del 2022 è la più ricca di occasioni del gruppo: oltre 5 xG complessivi prima dei rigori."],
        method="Tutte le finali dei Mondiali presenti negli Open Data StatsBomb (6). xG di tutti i tiri dei 90 o 120 minuti, rigori in partita "
               "compresi; la serie finale dei rigori è esclusa. La finale del 1986 (Argentina–Germania Ovest, 29 giugno) nella fonte è "
               "etichettata come semifinale.",
        caveat="Le partite del 1958, 1970, 1974 e 1986 sono state ricostruite da StatsBomb a partire dai filmati: gli xG usano il modello "
               "moderno e non conoscono il contesto dell'epoca (palloni, campi, regole del fuorigioco). Gli autogol non hanno xG.",
        table=table(["Partita n.", "Data", "Fase", "Vincitrice", "Risultato", "Sconfitta", "xG vincitrice", "xG sconfitta", "Tiri V", "Tiri S",
                     "Possesso V"], tab))


def ucl_finals_study(T):
    ns = [str(i) for i in (121, 122, 123, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138)]
    rows, tab, n_more = finals_rows(T, ns, lambda r: "Finale")
    chart = dumbbell(rows, row=28)
    M = by_match(T)
    ch = M["131"]
    bay = [r for r in ch if r["squadra"] == "Bayern Munich"][0]
    che = [r for r in ch if r["squadra"] == "Chelsea"][0]
    lowest = min(rows, key=lambda r: r[1])
    return dict(
        id="finali-champions", kicker="Partite", title="17 finali di Champions League: chi meritava di vincere?",
        headline=f"Il caso limite è Monaco di Baviera 2012: il Bayern crea {fmt(num(bay['xg']), 2)} xG con {bay['tiri']} tiri, il Chelsea "
                 f"{fmt(num(che['xg']), 2)} con {che['tiri']}. Finisce 1-1 e la coppa va al Chelsea ai rigori. In tutto, chi ha creato di più "
                 f"ha vinto {n_more} finali su {len(rows)}.",
        hook="40 tiri contro 9, e la Champions la vince chi ne ha fatti 9.",
        chart=chart, legend=legend([("var(--s1)", "xG della squadra che ha vinto"), ("var(--s2)", "xG della squadra che ha perso")]),
        body=[f"Il trofeo vinto con meno occasioni: {lowest[0][5:]} {lowest[0][:4]} ({lowest[3]}) con {fmt(lowest[1], 2)} xG.",
              "L'Ajax di Cruyff vince tre finali di fila (1971–73) senza subire gol e creando sempre molto più degli avversari.",
              "Le vittorie più nette per occasioni: " + ", ".join(f"{r[0][5:]} {r[0][:4]} ({fmt(r[1], 2)} contro {fmt(r[2], 2)})" for r in
                                                                  sorted(rows, key=lambda r: r[2] - r[1])[:4]) + "."],
        method="Tutte le finali di Coppa dei Campioni / Champions League presenti negli Open Data StatsBomb (17: 1971–73 e 2004–2019, "
               "mancano 2006 e 2008). xG di tutti i tiri dei 90 o 120 minuti, rigori in partita compresi; serie finale esclusa.",
        caveat="Gli xG misurano le occasioni, non il merito: una squadra in vantaggio spesso concede tiri all'avversario. Le finali del "
               "1971–73 sono ricostruite da filmati e valutate con il modello moderno.",
        table=table(["Partita n.", "Data", "Fase", "Vincitrice", "Risultato", "Sconfitta", "xG vincitrice", "xG sconfitta", "Tiri V", "Tiri S",
                     "Possesso V"], tab))


def player_matches(G, pid):
    return sorted([r for r in G if r["player_id"] == pid], key=lambda r: r["data"])


def pele_study(G, T):
    P = [r for r in player_matches(G, PELE) if r["competizione"] == "FIFA World Cup"]
    cosmos = [r for r in player_matches(G, PELE) if r["competizione"] != "FIFA World Cup"]
    items = []
    for r in P:
        items.append((f"{r['data'][:4]} {it(r['avversario'])}", [num(r["xg"]), num(r["xa"])],
                      f"{r['gol']} gol, {r['assist']} assist"))
    chart = stacked_hbars(items, ["xG", "xA"], ["var(--s1)", "var(--s2)"], d=2, label_w=200)
    g = sum(int(num(r["gol"])) for r in P)
    a = sum(int(num(r["assist"])) for r in P)
    xg = sum(num(r["xg"]) for r in P)
    xa = sum(num(r["xa"]) for r in P)
    mins = sum(num(r["minuti"]) for r in P)
    kp = sum(num(r["passaggi_chiave"]) for r in P)
    tab = table(["Data", "Avversario", "Fase", "Minuti", "Gol", "Assist", "xG", "xA", "Tiri", "Passaggi chiave", "Dribbling (riusciti)"],
                [[r["data"], it(r["avversario"]), next((t["fase"] for t in T if t["n"] == r["n"]), ""), int(num(r["minuti"])), r["gol"], r["assist"],
                  fmt(num(r["xg"]), 2), fmt(num(r["xa"]), 2), r["tiri"], r["passaggi_chiave"], f"{r['dribbling']} ({r['dribbling_riusciti']})"]
                 for r in P + cosmos])
    f58 = P[0]
    return dict(
        id="pele", kicker="Prima dei dati", title="Pelé ai Mondiali: 9 partite ricostruite tiro per tiro",
        headline=f"Nelle 9 partite mondiali del dataset (1958, 1962, 1970) Pelé ha {g} gol e {a} assist: un gol o un assist ogni "
                 f"{fmt(mins / (g + a), 0)} minuti, da {fmt(xg, 1)} xG e {fmt(xa, 1)} xA.",
        hook="Pelé visto con i dati di oggi: cosa resta della leggenda?",
        chart=chart, legend=legend([("var(--s1)", "xG: qualità dei suoi tiri"), ("var(--s2)", "xA: qualità dei tiri nati da un suo passaggio")]),
        body=[f"A 17 anni, nella semifinale 1958 con la Francia, fa tripletta con {f58['tiri']} tiri, {f58['dribbling']} dribbling tentati e "
              f"{f58['passaggi_chiave']} passaggi chiave: è la sua partita più produttiva del dataset.",
              f"Nel 1970 cambia ruolo: meno gol (4 in 6 partite) e più rifinitura, con {kp:.0f} passaggi chiave in 9 partite e 3 assist "
              "tra semifinale e finale. Il dato racconta un 10 moderno prima che il termine esistesse."],
        method="Tutte le partite di Pelé ai Mondiali presenti negli Open Data StatsBomb: semifinale e finale 1958, Brasile–Messico 1962 e "
               "le 6 partite del 1970. In tabella anche New York Cosmos–Seattle 1977. xG e xA con il modello StatsBomb moderno.",
        caveat="Sono partite scelte (finali e partite storiche) e ricostruite da filmati: non sono un campione rappresentativo della carriera. "
               "Assist e xA dipendono anche da come i filmati permettono di attribuire i passaggi.",
        table=tab)


def brazil70_study(T, G, WC):
    ns = [str(i) for i in range(635, 641)]
    br = [r for r in T if r["n"] in ns and r["squadra"] == "Brazil"]
    P = defaultdict(lambda: defaultdict(float))
    for r in G:
        if r["n"] in ns and r["squadra"] == "Brazil":
            a = P[r["soprannome"] or r["giocatore"]]
            for k in ("xg", "xa", "gol", "assist", "minuti", "sca", "dribbling", "conduzioni_progressive"):
                a[k] += num(r[k])
            a["gol_partite"] += num(r["gol"]) > 0
    top = sorted(P.items(), key=lambda kv: -(kv[1]["xg"] + kv[1]["xa"]))[:8]
    items = [(k.strip(), [v["xg"], v["xa"]], f"{int(v['gol'])} gol, {int(v['assist'])} assist") for k, v in top]
    chart = stacked_hbars(items, ["xG", "xA"], ["var(--s1)", "var(--s2)"], d=2, label_w=160)
    avg = lambda rs, k: sum(num(r[k]) for r in rs) / len(rs)
    goals = sum(int(num(r["gol"])) for r in br)
    tot_xa = sum(v["xg"] + v["xa"] for v in P.values())
    jz = P["Jairzinho"]
    comp = [("xG a partita", "xg", 2), ("Tiri", "tiri", 1), ("Dribbling tentati", "dribbling", 1), ("Precisione passaggi", "precisione_passaggi_pct", 1),
            ("Possesso", "possesso_pct", 1), ("Conduzioni progressive", "conduzioni_progressive", 1)]
    tab = table(["Metrica (per partita)", "Brasile 1970", "Media squadre Mondiali 2018 e 2022"],
                [[lab, fmt(avg(br, k), d), fmt(avg(WC, k), d)] for lab, k, d in comp] +
                [["Giocatore", "xG + xA", "Gol / assist"]] + [[k.strip(), fmt(v["xg"] + v["xa"], 2), f"{int(v['gol'])} / {int(v['assist'])}"] for k, v in top])
    return dict(
        id="brasile-70", kicker="Prima dei dati", title="Brasile 1970: la squadra perfetta, partita per partita",
        headline=f"6 partite, 6 vittorie, {goals} gol. Jairzinho segna in tutte e sei ({int(jz['gol'])} gol) e tenta {int(jz['dribbling'])} "
                 f"dribbling: {fmt(jz['dribbling'] / jz['minuti'] * 90, 1)} ogni 90 minuti.",
        hook="Il Brasile del 1970 è davvero la squadra più bella di sempre? Abbiamo misurato tutte le sue partite.",
        chart=chart, legend=legend([("var(--s1)", "xG: qualità dei tiri del giocatore"), ("var(--s2)", "xA: qualità dei tiri nati da un suo passaggio")]),
        body=[f"Creava {fmt(avg(br, 'xg'), 2)} xG a partita, quasi il doppio di una squadra media dei Mondiali 2018 e 2022 "
              f"({fmt(avg(WC, 'xg'), 2)}), con il {fmt(avg(br, 'precisione_passaggi_pct'), 0)}% di passaggi riusciti e "
              f"{fmt(avg(br, 'dribbling'), 0)} dribbling tentati a partita (oggi {fmt(avg(WC, 'dribbling'), 0)}).",
              f"Le occasioni erano distribuite: {', '.join(k.strip() for k, v in top if v['xg'] + v['xa'] >= 2)} superano i 2 xG + xA nel "
              f"torneo, e nessuno vale più del {fmt(100 * (top[0][1]['xg'] + top[0][1]['xa']) / tot_xa, 0)}% della produzione della squadra "
              f"({top[0][0].strip()})."],
        method="Le 6 partite del Brasile al Mondiale 1970, tutte presenti negli Open Data StatsBomb (torneo completo). Confronto con la media "
               f"delle {len(WC)} prestazioni di squadra dei Mondiali 2018 e 2022.",
        caveat="Le partite del 1970 sono ricostruite dai filmati e valutate con modelli moderni. Gli avversari e il ritmo del gioco erano "
               "diversi: il confronto con il 2018–2022 descrive lo stile, non dice chi vincerebbe.",
        table=tab)


def holland74_study(T, G, WC):
    ns = ["641", "643", "644", "645", "646"]
    nl = sorted([r for r in T if r["n"] in ns and r["squadra"] == "Netherlands"], key=lambda r: r["data"])
    avg = lambda rs, k: sum(num(r[k]) for r in rs) / len(rs)
    ppda = avg(nl, "ppda")
    tilt = avg(nl, "field_tilt_pct")
    below = 100 * sum(num(r["ppda"]) <= ppda for r in WC) / len(WC)
    above = 100 * sum(num(r["field_tilt_pct"]) >= tilt for r in WC) / len(WC)
    chart = strips([
        ("PPDA: passaggi concessi per azione difensiva", 0, 45, [num(r["ppda"]) for r in WC],
         [(num(r["ppda"]), it(r["avversario"])) for r in nl], "← pressing più intenso"),
        ("Field tilt: quota dei passaggi nell'ultimo terzo", 10, 90, [num(r["field_tilt_pct"]) for r in WC],
         [(num(r["field_tilt_pct"]), it(r["avversario"])) for r in nl], "più dominio →")])
    pl = defaultdict(lambda: defaultdict(float))
    for r in G:
        if r["n"] in ns and r["squadra"] == "Netherlands":
            a = pl[r["player_id"]]
            a["name"] = r["soprannome"] or r["giocatore"]
            for k in ("minuti", "gol", "assist", "dribbling", "conduzioni_progressive", "pressioni", "pressioni_alte", "recuperi_alti", "sca", "xg", "xa"):
                a[k] += num(r[k])
    tot = lambda k: sum(a[k] for a in pl.values())
    c, n_ = pl[CRUYFF], pl[NEESKENS]
    top_rec = max(pl.values(), key=lambda a: a["recuperi_alti"])
    tab = table(["Avversario", "Data", "Risultato", "PPDA", "Field tilt", "Pressioni alte", "xG", "xG concessi"],
                [[it(r["avversario"]), r["data"], f"{r['gol']}-{r['gol_subiti']}", fmt(num(r["ppda"])), fmt(num(r["field_tilt_pct"]), 0) + "%",
                  r["pressioni_alte"], fmt(num(r["xg"]), 2), fmt(num(r["xg_subiti"]), 2)] for r in nl] +
                [["Media Olanda 1974", "", "", fmt(ppda), fmt(tilt, 0) + "%", fmt(avg(nl, "pressioni_alte"), 0), fmt(avg(nl, "xg"), 2), fmt(avg(nl, "xg_subiti"), 2)],
                 ["Media Mondiali 2018–2022", "", "", fmt(avg(WC, "ppda")), fmt(avg(WC, "field_tilt_pct"), 0) + "%", fmt(avg(WC, "pressioni_alte"), 0),
                  fmt(avg(WC, "xg"), 2), fmt(avg(WC, "xg_subiti"), 2)]])
    return dict(
        id="olanda-74", kicker="Prima dei dati", title="Olanda 1974: il calcio totale di Cruyff e Neeskens, misurato",
        headline=f"PPDA medio {fmt(ppda)}: ai Mondiali 2018 e 2022 solo il {fmt(below, 0)}% delle squadre ha pressato altrettanto in una "
                 f"partita. E teneva il {fmt(tilt, 0)}% dei passaggi nell'ultimo terzo: oggi ci arriva il {fmt(above, 0)}%.",
        hook="Nel 1974 l'Olanda pressava più delle squadre di oggi. I numeri.",
        chart=chart, legend=legend([("var(--context)", f"Squadre dei Mondiali 2018 e 2022 ({len(WC)} prestazioni)"),
                                    ("var(--s1)", "Olanda 1974 (etichetta = avversario)")]),
        body=[f"Cruyff era il motore offensivo: {int(c['dribbling'])} dribbling tentati ({fmt(100 * c['dribbling'] / tot('dribbling'), 0)}% della "
              f"squadra) e {int(c['conduzioni_progressive'])} conduzioni progressive ({fmt(100 * c['conduzioni_progressive'] / tot('conduzioni_progressive'), 0)}%), "
              f"più {int(c['gol'])} gol e {int(c['assist'])} assist in 5 partite. Ma pressava anche: {int(c['pressioni_alte'])} pressioni nell'ultimo "
              "terzo di campo.",
              f"Neeskens era l'altra metà del sistema: {int(n_['gol'])} gol da centrocampista (uno su rigore, al 2' della finale) "
              f"e {int(n_['recuperi_alti'])} palloni recuperati nell'ultimo terzo di campo"
              + (", più di chiunque altro nella squadra." if top_rec is n_ else ".")],
        method="5 partite dell'Olanda al Mondiale 1974 presenti negli Open Data StatsBomb (mancano Uruguay e Bulgaria nel primo girone). "
               "PPDA = passaggi dell'avversario nei suoi 60 metri diviso le azioni difensive nella stessa zona. Field tilt = quota dei "
               "passaggi nel terzo offensivo rispetto all'avversario.",
        caveat="Partite ricostruite dai filmati: le pressioni senza palla possono essere sottostimate quando l'inquadratura non le mostra. "
               "Il confronto con le squadre di oggi descrive l'intensità relativa, non le distanze percorse.",
        table=tab)


def maradona_study(T, G):
    ns = ["647", "648", "649"]
    ks = [("Gol", "gol"), ("xG", "xg"), ("Passaggi chiave", "passaggi_chiave"), ("Azioni che portano al tiro", "sca"), ("Falli subiti", "falli_subiti"),
          ("Tocchi in area avversaria", "tocchi_in_area"), ("Dribbling tentati", "dribbling"), ("Conduzioni progressive", "conduzioni_progressive")]
    me, team = defaultdict(float), defaultdict(float)
    for r in G:
        if r["n"] in ns and r["squadra"] == "Argentina":
            for _, k in ks:
                team[k] += num(r[k])
                if r["player_id"] == MARADONA:
                    me[k] += num(r[k])
    items = sorted([(lab, 100 * me[k] / team[k], "var(--s1)", f"{fmt(me[k], 1 if k == 'xg' else 0)} su {fmt(team[k], 1 if k == 'xg' else 0)}")
                    for lab, k in ks], key=lambda x: -x[1])
    chart = hbars(items, d=0, unit="%", label_w=220, value_w=60)
    M = [r for r in player_matches(G, MARADONA)]
    eng = [r for r in M if r["n"] == "647"][0]
    tab = table(["Data", "Partita", "Competizione", "Minuti", "Gol", "Assist", "xG", "Dribbling (riusciti)", "Passaggi chiave", "Falli subiti"],
                [[r["data"], f"{it(r['squadra'])}–{it(r['avversario'])}", r["competizione"].replace("UEFA Europa League", "Coppa UEFA"),
                  int(num(r["minuti"])), r["gol"], r["assist"], fmt(num(r["xg"]), 2), f"{r['dribbling']} ({r['dribbling_riusciti']})",
                  r["passaggi_chiave"], r["falli_subiti"]] for r in M])
    return dict(
        id="maradona", kicker="Prima dei dati", title="Maradona 1986: un giocatore che valeva mezza squadra",
        headline=f"Nei quarti, in semifinale e in finale Maradona ha segnato il {fmt(100 * me['gol'] / team['gol'], 0)}% "
                 f"dei gol dell'Argentina e prodotto il {fmt(100 * me['xg'] / team['xg'], 0)}% dei suoi xG. In campo erano in undici.",
        hook="Uno contro undici: quanto pesava Maradona sull'Argentina del 1986?",
        chart=chart, legend=legend([("var(--s1)", "Quota di Maradona sul totale dell'Argentina (3 partite)")]),
        body=[f"Contro l'Inghilterra tenta {eng['dribbling']} dribbling e ne riesce {eng['dribbling_riusciti']}, con 2 gol: quello di mano e "
              "quello dopo la corsa da centrocampo.",
              "Per confronto, un giocatore che contribuisse in parti uguali varrebbe il 10% circa dei numeri di squadra (portiere escluso). "
              f"Maradona subisce anche il {fmt(100 * me['falli_subiti'] / team['falli_subiti'], 0)}% dei falli: il modo per fermarlo era "
              "quello."],
        method="Le 3 partite dell'Argentina al Mondiale 1986 presenti negli Open Data StatsBomb (quarti con l'Inghilterra, semifinale con il "
               "Belgio, finale con la Germania Ovest). Quota = valore di Maradona diviso il totale di tutti i giocatori argentini. In tabella "
               "tutte le 12 partite di Maradona nel dataset (Argentina U20, Boca Juniors, Barcellona, Napoli, Argentina).",
        caveat="Tre partite sono un campione piccolo e scelto (le più importanti del torneo). Partite ricostruite da filmati, metriche "
               "calcolate con modelli moderni.",
        table=tab)


def legends_share_study(G):
    K = ["sca", "dribbling", "conduzioni_progressive", "npxg", "xa"]
    team = defaultdict(lambda: defaultdict(float))
    for r in G:
        t = team[(r["n"], r["squadra"])]
        for k in K:
            t[k] += num(r[k])
    pl = defaultdict(lambda: defaultdict(float))
    names = {}
    for r in G:
        if num(r["minuti"]) < 60:
            continue
        a = pl[r["player_id"]]
        t = team[(r["n"], r["squadra"])]
        a["m"] += 1
        for k in K:
            a[k] += num(r[k])
            a["T" + k] += t[k]
        a["mod"] += r["data"] >= "2015" and "(F)" not in r["competizione"]
        a["att"] += any(x in r["ruolo"] for x in ("Forward", "Wing", "Attacking"))
        names[r["player_id"]] = r["soprannome"] or r["giocatore"]

    def sh(a):
        return dict(sca=100 * a["sca"] / a["Tsca"], drib=100 * a["dribbling"] / a["Tdribbling"],
                    car=100 * a["conduzioni_progressive"] / a["Tconduzioni_progressive"],
                    xgxa=100 * (a["npxg"] + a["xa"]) / (a["Tnpxg"] + a["Txa"]))
    mod = [sh(a) for k, a in pl.items() if a["mod"] >= 10 and a["mod"] == a["m"] and a["att"] / a["m"] >= 0.5 and k != MESSI]
    pct = lambda k, q: sorted(x[k] for x in mod)[int(q * (len(mod) - 1))]
    who = [("Pelé", PELE, "var(--s1)"), ("Cruyff", CRUYFF, "var(--s1)"), ("Maradona", MARADONA, "var(--s1)"), ("Messi", MESSI, "var(--s2)")]
    S = {n: sh(pl[p]) for n, p, _ in who}
    mets = [("Azioni che portano al tiro", "sca"), ("Dribbling tentati", "drib"), ("Conduzioni progressive", "car"), ("xG + xA (senza rigori)", "xgxa")]
    panels = []
    for title, k in mets:
        items = [(n, S[n][k], c) for n, _, c in who] + [("Top 10% di oggi", pct(k, 0.9), "var(--neutral)")]
        panels.append(bar_panel(f"{title}: quota della squadra", items, d=0, unit="%", ref=(pct(k, 0.5), f"mediana attaccanti di oggi {fmt(pct(k, 0.5), 0)}%")))
    chart = '<div class="sm sm2">' + "".join(panels) + "</div>"
    tab = table(["Giocatore", "Partite (≥ 60')", "Quota SCA", "Quota dribbling", "Quota conduzioni progressive", "Quota xG + xA"],
                [[n, int(pl[p]["m"])] + [fmt(S[n][k], 1) + "%" for _, k in mets] for n, p, _ in who] +
                [["Attaccanti dal 2015: mediana", len(mod)] + [fmt(pct(k, 0.5), 1) + "%" for _, k in mets],
                 ["Attaccanti dal 2015: top 10%", len(mod)] + [fmt(pct(k, 0.9), 1) + "%" for _, k in mets]])
    m = S["Maradona"]
    # sopra la soglia del 10% migliore con almeno mezzo punto di margine (le quote si arrotondano all'unità nel grafico)
    over = {n: sum(S[n][k] >= pct(k, 0.9) + 0.5 for _, k in mets) for n, _, _ in who}
    top10 = "Voci (su 4) in cui superano il 10% migliore degli attaccanti di oggi: " + ", ".join(f"{n} {v}" for n, v in sorted(over.items(), key=lambda x: -x[1]))
    car_top = max(S, key=lambda n: S[n]["car"])
    return dict(
        id="leggende-dati", kicker="Prima dei dati", title="Pelé, Cruyff, Maradona e Messi: il peso sulla propria squadra",
        headline=f"Maradona generava il {fmt(m['sca'], 0)}% delle azioni da tiro delle sue squadre, Pelé il {fmt(S['Pelé']['xgxa'], 0)}% degli "
                 f"xG + xA. Un attaccante tipico di oggi è al {fmt(pct('sca', 0.5), 0)}% e al {fmt(pct('xgxa', 0.5), 0)}%. " + top10 + ".",
        hook="Confrontare epoche diverse è impossibile. A meno di guardare quanto contavano nella propria squadra.",
        chart=chart, legend=legend([("var(--s1)", "Leggende prima del 1991"), ("var(--s2)", "Messi (tutte le partite nel dataset)"),
                                    ("var(--neutral)", "Soglia del 10% migliore degli attaccanti dal 2015")]),
        body=["Contare dribbling o tiri per 90 minuti premierebbe le epoche più aperte (nel 1958–1990 si dribblava il doppio). La quota sul "
              "totale della squadra neutralizza lo stile dell'epoca: misura quanto del gioco offensivo passava da quel giocatore.",
              f"{car_top} è il più 'portatore di palla' dei quattro: {fmt(S[car_top]['car'], 0)}% delle conduzioni progressive. Messi, su "
              f"{int(pl[MESSI]['m'])} partite, tiene quote da leggenda per 17 anni."],
        method="Solo partite giocate per almeno 60 minuti. Quota = somma del giocatore diviso la somma di tutti i compagni nelle stesse "
               f"partite. Riferimento: {len(mod)} attaccanti, esterni e trequartisti con almeno 10 partite maschili dal 2015 (Messi escluso).",
        caveat=f"Pelé ({int(pl[PELE]['m'])} partite), Cruyff ({int(pl[CRUYFF]['m'])}) e Maradona ({int(pl[MARADONA]['m'])}) hanno campioni piccoli "
               "e scelti (finali, partite storiche): sono indicazioni, non medie di carriera. Le squadre di riferimento di oggi hanno "
               "livelli molto diversi tra loro.",
        table=tab)


# ------------------------------------------------------------------------------------------- pacchetti social
HOOKS = {
    "epoche": "Il calcio di oggi è più noioso? Abbiamo confrontato 60 anni di partite.",
    "mondiali": "Dal 1958 al 2022 i Mondiali sono diventati un altro sport. Due numeri lo dimostrano.",
    "stile": "Il calcio femminile non è il maschile 'più lento'. È un altro modo di giocare.",
    "portieri": "'Le portiere sono più scarse': lo abbiamo verificato su migliaia di tiri.",
    "olimpici": "Il gol direttamente da calcio d'angolo è un affare quasi tutto femminile.",
    "casa": "Giocare in casa conta. Ma molto meno nel calcio femminile.",
    "minuti": "Quando arrivano i gol? Più tardi di quanto pensi.",
    "possesso": "Avere la palla serve a vincere? Meno di quanto dica il tiki-taka.",
    "fortuna": "Quanti punti vale la fortuna in una stagione? Fino a 18.",
    "leicester": "Il Leicester 2015/16 visto dagli xG: un miracolo costruito in difesa.",
    "leggende": "Qual è la squadra più dominante del dataset? Non è maschile.",
    "finalizzatori": "Chi segna più di quanto dovrebbe? Classifica dei finalizzatori.",
    "colpi": "Vincere con 0,5 xG contro 3: le vittorie più improbabili.",
}
TAGS = {
    "epoche": "#storiadelcalcio #tattica", "mondiali": "#mondiali #worldcup #storiadelcalcio", "stile": "#calciofemminile #womensfootball",
    "portieri": "#calciofemminile #portieri", "olimpici": "#calciofemminile #golazo", "casa": "#calciofemminile #fattorecampo",
    "minuti": "#gol #statistiche", "possesso": "#tikitaka #possesso #tattica", "fortuna": "#xG #seriea #premierleague #laliga",
    "leicester": "#leicester #premierleague", "leggende": "#barcellona #arsenal #leverkusen", "finalizzatori": "#bomber #finalizzazione",
    "colpi": "#sorprese #ligue1", "barcellona": "#barcellona #fcbarcelona #guardiola #tattica", "messi": "#messi #barcellona #leomessi",
    "finali-mondiali": "#mondiali #finalimondiali #worldcup", "finali-champions": "#championsleague #ucl #finale",
    "pele": "#pele #brasile #mondiali #leggende", "brasile-70": "#brasile #mexico70 #mondiali #leggende",
    "olanda-74": "#cruyff #neeskens #calciototale #olanda", "maradona": "#maradona #mexico86 #argentina #leggende",
    "leggende-dati": "#pele #cruyff #maradona #messi #leggende",
}
BASE_TAGS = "#DeltaScout #football #calcio #dataanalysis #footballanalytics #StatsBomb"
# ordine di pubblicazione suggerito: alterna temi (leggende, finali, squadre, maschile/femminile) e apre con i contenuti più forti
CALENDAR = ["maradona", "finali-champions", "epoche", "olanda-74", "portieri", "messi", "finali-mondiali", "leicester", "brasile-70",
            "fortuna", "stile", "pele", "colpi", "barcellona", "olimpici", "leggende-dati", "possesso", "finalizzatori", "casa",
            "mondiali", "minuti", "leggende"]


def split_tweets(parts, limit=270):
    out = []
    for p in parts:
        cur = ""
        for sent in p.replace("; ", "; \n").replace(". ", ". \n").split("\n"):
            sent = sent.strip()
            if not sent or sent.startswith("In tabella"):  # rimanda alla tabella della pagina, non ha senso sui social
                continue
            if len(cur) + len(sent) + 1 > limit and cur:
                out.append(cur.strip())
                cur = sent
            else:
                cur = (cur + " " + sent).strip()
        if cur:
            out.append(cur)
    n = len(out)
    return [f"{i}/{n} {t}" for i, t in enumerate(out, 1)]


def pack_texts(st, week, nxt, serie="uno studio nuovo"):
    tags = f"{TAGS.get(st['id'], '')} {BASE_TAGS}".strip()
    src = "Dati: StatsBomb Open Data. Analisi e grafici: Delta Scout."
    body = " ".join(st["body"])
    li = (f"{st['hook']}\n\n{st['headline']}\n\n" + "\n".join(f"→ {b}" for b in st["body"]) +
          f"\n\nCome l'abbiamo calcolato: {st['method']}\n\nAttenzione: {st['caveat']}\n\n{src}\n"
          f"Ogni settimana {serie}: la prossima settimana, «{nxt}».\n\n{tags}")
    ig = (f"{st['hook']}\n\n{st['headline']}\n\nScorri il carosello: il grafico, le 3 cose da sapere e i limiti del dato. 👉\n\n"
          f"{src}\n\n{tags} #calcioitaliano #datavisualization #sportanalytics")
    x = split_tweets([st["hook"] + " 🧵", st["headline"], body, "Metodo: " + st["method"], "Limiti: " + st["caveat"] + " " + src])
    tt = (f"[0–3 s, testo a schermo] {st['hook']}\n[3–12 s] {st['headline']}\n[12–25 s] {st['body'][0]}\n"
          f"[25–30 s] Attenzione: {st['caveat'].split('. ')[0].rstrip('.')}. Dati StatsBomb Open Data. Segui Delta Scout per il prossimo contenuto.\n\n"
          f"Didascalia: {st['hook']} {TAGS.get(st['id'], '')} #DeltaScout #calcio #footballtiktok")
    alt = f"Grafico Delta Scout: {st['title']}. {st['headline']}"
    return (f"DELTA SCOUT · SETTIMANA {week} · {st['kicker'].upper()} · {st['title']}\n{'=' * 60}\n\n"
            f"LINKEDIN\n{'-' * 60}\n{li}\n\n"
            f"INSTAGRAM (carosello)\n{'-' * 60}\n{ig}\n\n"
            f"X / TWITTER (thread)\n{'-' * 60}\n" + "\n\n".join(x) + "\n\n"
            f"TIKTOK / REELS / SHORTS (copione 30 s, formato 9:16)\n{'-' * 60}\n{tt}\n\n"
            f"TESTO ALTERNATIVO (accessibilità, per ogni immagine del carosello)\n{'-' * 60}\n{alt}\n\n"
            f"HASHTAG\n{'-' * 60}\n{tags}\n\n"
            f"REGOLE DI PUBBLICAZIONE\n{'-' * 60}\nLascia sempre visibile il logo StatsBomb (è richiesto dalla licenza dei dati). "
            "Pubblica l'analisi, non i dati grezzi. Uso non commerciale.\n")
