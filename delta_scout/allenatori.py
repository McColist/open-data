"""Delta Scout - serie «Allenatori»: lo stile degli allenatori e la sua evoluzione tra stagioni e squadre.

Un «periodo» è un allenatore in una squadra in una stagione (almeno 15 partite) oppure con una nazionale
(tutti i tornei insieme, almeno 5 partite). Escluse le partite senza eventi di una squadra e con possesso anomalo.
Importato da studi.py; stessa struttura degli studi (grafico, metodo, limiti, tabella, pack social).
"""
import random
import statistics
from collections import Counter, defaultdict

from studi import FONT, columns, e, fmt, is_f, legend, num, scatter, svg_open, table, watermark
from studi2 import bar_panel, it, season_chart

K_ = "Allenatori"
NAT = {"FIFA World Cup", "UEFA Euro", "Copa America", "African Cup of Nations"}
NAMES = {"Spain": "Spagna", "Belgium": "Belgio", "Portugal": "Portogallo", "Juventus W": "Juventus F", "Arsenal WFC": "Arsenal F",
         "Chelsea FCW": "Chelsea F", "Athletic Club": "Athletic", "Paris Saint-Germain": "PSG", "Tottenham Hotspur": "Tottenham",
         "Birmingham City WFC": "Birmingham F", "Aston Villa W": "Aston Villa F", "Las Palmas": "Las Palmas", "Saint-Étienne": "Saint-Étienne",
         "Manchester United": "Manchester United", "Inter Milan": "Inter"}
METRICS = [("possesso_pct", "Possesso", 0, "%"), ("field_tilt_pct", "Field tilt", 0, "%"), ("ppda", "PPDA (più basso = più pressing)", 1, ""),
           ("passaggi_per_possesso", "Passaggi per azione", 1, ""), ("lanci_pct", "Lanci lunghi sul totale dei passaggi", 0, "%"),
           ("pressioni_alte", "Pressioni nell'ultimo terzo", 0, "")]
SIG = [("ppda", "PPDA (intensità del pressing)"), ("xg_subiti", "xG concessi"), ("xg", "xG creati"), ("possesso_pct", "Possesso"),
       ("field_tilt_pct", "Field tilt"), ("passaggi_per_possesso", "Passaggi per azione"), ("passaggi_avanti_pct", "Passaggi in avanti"),
       ("lanci_pct", "Lanci lunghi"), ("pressioni_alte", "Pressioni nell'ultimo terzo")]


def nm(team):
    return NAMES.get(team, it(team))


def spells(Tv):
    sp = defaultdict(list)
    for r in Tv:
        if r["allenatore"]:
            nat = r["competizione"] in NAT
            sp[(r["allenatore"], r["squadra"], "naz" if nat else r["stagione"])].append(r)
    out = {}
    for k, rs in sp.items():
        if len(rs) >= 15 or (k[2] == "naz" and len(rs) >= 5):
            v = {m: sum(num(r[m]) for r in rs) / len(rs) for m in ("possesso_pct", "field_tilt_pct", "ppda", "passaggi_per_possesso",
                                                                   "pressioni_alte", "xg", "xg_subiti", "passaggi_avanti_pct")}
            v["lanci_pct"] = 100 * sum(num(r["lanci_lunghi"]) for r in rs) / max(1, sum(num(r["passaggi"]) for r in rs))
            v["ppg"] = sum(3 if r["esito"] == "V" else 1 if r["esito"] == "N" else 0 for r in rs) / len(rs)
            v["n"] = len(rs)
            v["f"] = any(is_f(r["competizione"]) for r in rs)
            v["start"] = min(r["data"] for r in rs)
            yrs = sorted({r["data"][:4] for r in rs})
            v["label"] = (f"{nm(k[1])} {k[2][2:4]}/{k[2][7:9]}" if k[2] != "naz" else
                          f"{nm(k[1])} {yrs[0]}" + (f"–{yrs[-1][2:]}" if len(yrs) > 1 else ""))
            out[k] = v
    return out


def medians(S):
    return {(g, m): statistics.median(v[m] for v in S.values() if v["f"] == g) for g in (True, False) for m, *_ in METRICS + [("xg", 0, 0, 0)]}


def coach_chart(S, keys, med):
    g = S[keys[0]]["f"]
    panels = []
    for m, title, d, u in METRICS:
        items = [(S[k]["label"], S[k][m], "var(--s1)" if i == len(keys) - 1 else "var(--s2)" if i == 0 else "var(--context)")
                 for i, k in enumerate(keys)]
        panels.append(bar_panel(title, items, d=d, unit=u, label_w=128, ref=(med[(g, m)], f"mediana {fmt(med[(g, m)], d)}{u}")))
    return '<div class="sm">' + "".join(panels) + "</div>"


def coach_table(S, keys):
    return table(["Periodo", "Partite", "Punti/partita", "Possesso", "Field tilt", "PPDA", "Passaggi per azione", "Lanci lunghi",
                  "Pressioni ultimo terzo", "xG creati", "xG concessi"],
                 [[S[k]["label"], S[k]["n"], fmt(S[k]["ppg"], 2), fmt(S[k]["possesso_pct"], 0) + "%", fmt(S[k]["field_tilt_pct"], 0) + "%",
                   fmt(S[k]["ppda"]), fmt(S[k]["passaggi_per_possesso"]), fmt(S[k]["lanci_pct"], 1) + "%", fmt(S[k]["pressioni_alte"], 0),
                   fmt(S[k]["xg"], 2), fmt(S[k]["xg_subiti"], 2)] for k in keys])


def card(id_, title, hook, headline, chart, leg, body, method, caveat, tab):
    return dict(id=id_, kicker=K_, title=title, hook=hook, headline=headline, chart=chart, legend=leg, body=body, method=method,
                caveat=caveat, table=tab)


COACH_LEG = legend([("var(--s2)", "Primo periodo"), ("var(--context)", "Periodi intermedi"), ("var(--s1)", "Ultimo periodo"),
                    ("var(--ink2)", "Linea tratteggiata: mediana di tutte le squadre-stagione")])
METHOD = ("Medie per partita di ogni periodo: un allenatore in una squadra e in una stagione (almeno 15 partite nel database) o con una "
          "nazionale (tutti i tornei insieme, almeno 5 partite). Mediane calcolate su tutti i periodi dello stesso calcio (maschile o "
          "femminile). Lanci lunghi = passaggi di almeno 32 metri sul totale dei passaggi.")


def keys_of(S, coach, teams=None):
    ks = [k for k in S if k[0] == coach and (teams is None or k[1] in teams)]
    return sorted(ks, key=lambda k: S[k]["start"])


def pick(S, coach, team, season):
    return next(k for k in S if k[0] == coach and k[1] == team and k[2] == season)


# ------------------------------------------------------------------------------------------- studi
def signature_study(S):
    pct = {}
    for g in (True, False):
        ks = [k for k in S if S[k]["f"] == g]
        for m, _ in SIG:
            vs = sorted(S[k][m] for k in ks)
            for k in ks:
                pct[(k, m)] = 100 * sum(v < S[k][m] for v in vs) / (len(vs) - 1)
    coaches = Counter(k[0] for k in S)
    per_coach = defaultdict(list)
    same = []
    for c, n in coaches.items():
        if n < 2:
            continue
        ks = keys_of(S, c)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                if ks[i][1] != ks[j][1] and S[ks[i]]["f"] == S[ks[j]]["f"]:
                    per_coach[c].append((ks[i], ks[j]))
        same += [(ks[i], ks[i + 1]) for i in range(len(ks) - 1) if ks[i][1] == ks[i + 1][1]]
    rnd_pairs = []
    random.seed(7)
    allk = list(S)
    while len(rnd_pairs) < 20000:
        a, b = random.sample(allk, 2)
        if a[0] != b[0] and S[a]["f"] == S[b]["f"]:
            rnd_pairs.append((a, b))
    dist = lambda pairs, m: statistics.mean(abs(pct[(a, m)] - pct[(b, m)]) for a, b in pairs)
    res = []
    for m, lab in SIG:
        club = statistics.mean(dist(p, m) for p in per_coach.values())  # ogni allenatore pesa uguale
        res.append((lab, club, dist(same, m), dist(rnd_pairs, m)))
    res.sort(key=lambda x: x[1])
    short = {"PPDA (intensità del pressing)": "PPDA", "Passaggi per azione": "Passaggi/azione", "Pressioni nell'ultimo terzo": "Press. alte",
             "Passaggi in avanti": "Pass. avanti"}
    chart = columns([short.get(r[0], r[0]) for r in res], [("Stesso allenatore, squadra diversa", "var(--s1)", [r[1] for r in res]),
                                          ("Stesso allenatore, stagione dopo (stessa squadra)", "var(--neutral)", [r[2] for r in res]),
                                          ("Due allenatori a caso", "var(--s2)", [r[3] for r in res])], d=0, w=760, h=300, ymax=45)
    best, worst = res[0], res[-1]
    pres = [r for r in res if r[0].startswith("Lanci")][0]
    names = ", ".join(sorted(per_coach))
    return card(
        "a-firma", "La firma dell'allenatore: cosa si porta dietro quando cambia squadra",
        "Un allenatore cambia squadra. Cosa resta uguale? Il pressing sì, i passaggi no.",
        f"Quando un allenatore cambia squadra, il dato che resta più simile è {best[0].split(' (')[0]}: in media si sposta di {fmt(best[1], 0)} "
        f"posizioni percentili, contro le {fmt(best[3], 0)} di due allenatori presi a caso. I lanci lunghi invece cambiano come tra due "
        f"allenatori qualsiasi ({fmt(pres[1], 0)} contro {fmt(pres[3], 0)}).",
        chart, legend([("var(--s1)", "Stesso allenatore, squadra diversa"), ("var(--neutral)", "Stesso allenatore e squadra, stagione successiva"),
                       ("var(--s2)", "Due allenatori diversi presi a caso")]),
        ["Più bassa la colonna, più il dato è 'dell'allenatore': resta simile anche cambiando giocatori, campionato o paese.",
         f"Il pressing è l'unico dato che resta simile quasi come tra due stagioni nella stessa squadra ({fmt(best[1], 1)} contro "
         f"{fmt(best[2], 1)}). Possesso, xG e field tilt stanno a metà strada: dipendono anche dalla forza della rosa. Il modo di passare la "
         "palla (lanci, passaggi in avanti, lunghezza delle azioni) e le pressioni nell'ultimo terzo cambiano come tra due allenatori "
         "presi a caso: dipendono dai giocatori e da quanto la squadra sta nella metà avversaria.",
         f"Allenatori con almeno due squadre diverse nel database: {names}."],
        "Per ogni metrica, ogni periodo (allenatore + squadra + stagione, almeno 15 partite; nazionali con almeno 5) riceve un percentile "
        "tra tutti i periodi dello stesso calcio. Si misura la distanza media in percentili tra due periodi dello stesso allenatore in "
        "squadre diverse (ogni allenatore pesa uguale), tra due stagioni consecutive nella stessa squadra e tra 20.000 coppie casuali.",
        f"Sono {len(per_coach)} allenatori: un campione piccolo, utile per indicare una tendenza. Chi passa a una squadra molto più forte "
        "(da Southampton al Barcellona) cambia per forza possesso e passaggi: il confronto mescola stile e qualità della rosa.",
        table(["Metrica", "Stesso allenatore, squadra diversa", "Stessa squadra, stagione dopo", "Coppie casuali"],
              [[r[0], fmt(r[1], 1), fmt(r[2], 1), fmt(r[3], 1)] for r in res]))


def big_club_study(S):
    moves = [("Ernesto Valverde", ("Athletic Club", "2015/2016"), ("Barcelona", "2017/2018")),
             ("Quique Setién", ("Las Palmas", "2015/2016"), ("Barcelona", "2019/2020")),
             ("Ronald Koeman", ("Southampton", "2015/2016"), ("Barcelona", "2020/2021")),
             ("Christophe Galtier", ("Saint-Étienne", "2015/2016"), ("Paris Saint-Germain", "2022/2023")),
             ("Mauricio Pochettino", ("Tottenham Hotspur", "2015/2016"), ("Paris Saint-Germain", "2021/2022")),
             ("Carla Ward", ("Birmingham City WFC", "2020/2021"), ("Aston Villa W", "2023/2024"))]
    rows = []
    for c, a, b in moves:
        ka, kb = pick(S, c, *a), pick(S, c, *b)
        rows.append((c, S[ka], S[kb]))
    def shift(metric, title, lo, hi, step, d, unit):
        w, row, lw = 680, 30, 300
        h = row * len(rows) + 44
        X = lambda v: lw + (w - lw - 70) * (v - lo) / (hi - lo)
        s = [svg_open(w, h, title), f'<text x="0" y="12" font-size="12.5" font-weight="600" fill="var(--ink)">{e(title)}</text>']
        t = lo
        while t <= hi + 1e-9:
            s.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="20" y2="{h - 22}" stroke="var(--grid)"/>'
                     f'<text x="{X(t):.1f}" y="{h - 8}" font-size="10" fill="var(--muted)" text-anchor="middle">{fmt(t, 0)}{unit}</text>')
            t += step
        for i, (c, A, B) in enumerate(rows):
            y = 34 + i * row
            a, b = A[metric], B[metric]
            s.append(f'<g><title>{e(c)}: {e(A["label"])} {fmt(a, d)}{unit} → {e(B["label"])} {fmt(b, d)}{unit}</title>'
                     f'<line x1="{X(a):.1f}" x2="{X(b):.1f}" y1="{y}" y2="{y}" stroke="var(--axis)" stroke-width="3"/>'
                     f'<circle cx="{X(a):.1f}" cy="{y}" r="6" fill="var(--s2)" stroke="var(--surface)" stroke-width="2"/>'
                     f'<circle cx="{X(b):.1f}" cy="{y}" r="6" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/></g>'
                     f'<text x="{lw - 12}" y="{y + 4}" font-size="11.5" fill="var(--ink)" text-anchor="end">{e(c.split()[-1])}: '
                     f'{e(A["label"])} → {e(B["label"])}</text>'
                     f'<text x="{w - 60}" y="{y + 4}" font-size="11.5" font-weight="600" fill="var(--ink)">{"+" if b > a else ""}{fmt(b - a, d)}</text>')
        s.append("</svg>")
        return "".join(s)
    chart = shift("possesso_pct", "Possesso", 30, 80, 10, 0, "%") + shift("ppda", "PPDA (più basso = più pressing)", 10, 32, 4, 1, "")
    dp = [B["possesso_pct"] - A["possesso_pct"] for _, A, B in rows]
    dd = [abs(B["ppda"] - A["ppda"]) for _, A, B in rows]
    dl = [B["lanci_pct"] - A["lanci_pct"] for _, A, B in rows]
    men = rows[:5]
    return card(
        "a-big", "Quando l'allenatore arriva in una grande squadra",
        "Da Southampton al Barcellona: è l'allenatore che cambia la squadra o la squadra che cambia l'allenatore?",
        f"Sei allenatori passati da una squadra media a una grande: il possesso sale in tutti i casi (da +{fmt(min(dp), 0)} a "
        f"+{fmt(max(dp), 0)} punti), i lanci lunghi calano. L'intensità del pressing cambia molto meno: in media {fmt(statistics.mean(dd), 1)} "
        "passaggi concessi per azione difensiva.",
        chart, legend([("var(--s2)", "Squadra di partenza"), ("var(--s1)", "Grande squadra")]),
        [f"Valverde, Setién, Koeman, Galtier e Pochettino: con giocatori migliori tengono più palla e lanciano meno (i lanci lunghi "
         f"calano in media di {fmt(-statistics.mean(dl[:5]), 1)} punti percentuali sul totale dei passaggi). È la rosa a decidere quanto "
         "si può tenere la palla.",
         f"Il pressing invece resta simile: Pochettino pressa più della mediana sia al Tottenham (PPDA {fmt(rows[4][1]['ppda'])}) sia al PSG "
         f"({fmt(rows[4][2]['ppda'])}); Koeman resta vicino alla mediana ({fmt(rows[2][1]['ppda'])} e {fmt(rows[2][2]['ppda'])}).",
         f"Carla Ward è l'esempio femminile: dal {fmt(rows[5][1]['possesso_pct'], 0)}% di possesso con il Birmingham al "
         f"{fmt(rows[5][2]['possesso_pct'], 0)}% con l'Aston Villa, e i lanci lunghi quasi dimezzati."],
        METHOD,
        "Squadre diverse in campionati diversi: il cambiamento mescola l'idea dell'allenatore, la qualità della rosa e il livello degli "
        "avversari. Il Barcellona di Setién è di 19 partite, quello di Valverde di 35.",
        table(["Allenatore", "Da", "A", "Possesso prima", "Possesso dopo", "PPDA prima", "PPDA dopo", "Lanci lunghi prima", "Lanci lunghi dopo"],
              [[c, A["label"], B["label"], fmt(A["possesso_pct"], 0) + "%", fmt(B["possesso_pct"], 0) + "%", fmt(A["ppda"]), fmt(B["ppda"]),
                fmt(A["lanci_pct"], 1) + "%", fmt(B["lanci_pct"], 1) + "%"] for c, A, B in rows]))


def guardiola_study(S):
    ks = keys_of(S, "Pep Guardiola", {"Barcelona"})
    seasons = [k[2] for k in ks]
    v = lambda m: [S[k][m] for k in ks]
    chart = season_chart(seasons, ["Guardiola"] * len(ks), [
        ("Passaggi per azione", [("Passaggi per azione", "var(--s1)", v("passaggi_per_possesso"))], 2, ""),
        ("Lanci lunghi sul totale dei passaggi", [("Lanci lunghi", "var(--s1)", v("lanci_pct"))], 1, "%"),
        ("Possesso", [("Possesso", "var(--s1)", v("possesso_pct"))], 0, "%"),
        ("xG a partita: creati e concessi", [("xG creati", "var(--s1)", v("xg")), ("xG concessi", "var(--s2)", v("xg_subiti"))], 2, "")])
    a, b = S[ks[0]], max((S[k] for k in ks), key=lambda x: x["passaggi_per_possesso"])
    bk = next(k for k in ks if S[k] is b)
    return card(
        "a-guardiola", "Guardiola al Barcellona: il tiki-taka nasce stagione dopo stagione",
        "Il tiki-taka di Guardiola non è nato in un giorno. Ecco come cambia in quattro stagioni.",
        f"Nella prima stagione il Barça di Guardiola faceva {fmt(a['passaggi_per_possesso'])} passaggi per azione; nel {bk[2]} arriva a "
        f"{fmt(b['passaggi_per_possesso'])}. I lanci lunghi scendono dal {fmt(a['lanci_pct'], 1)}% all'{fmt(b['lanci_pct'], 1)}% dei passaggi.",
        chart, legend([("var(--s1)", "Valore della stagione (xG creati nell'ultimo pannello)"), ("var(--s2)", "xG concessi")]),
        [f"La prima stagione (2008/09, triplete) è la più verticale e la più prolifica: {fmt(a['xg'], 2)} xG a partita. Le stagioni "
         "successive tengono di più la palla e la fanno girare più a lungo prima di attaccare.",
         f"Il pressing resta costante per tutti e quattro gli anni (PPDA tra {fmt(min(v('ppda')))} e {fmt(max(v('ppda')))}): l'idea "
         "di riconquista è la stessa dal primo giorno, cambia il modo di tenere la palla."],
        METHOD + " Solo Liga.",
        "Nel database ci sono quasi solo le partite giocate da Messi in quegli anni (30–37 per stagione su 38). Le 2 partite del Bayern "
        "2015/16 non bastano per un confronto.",
        coach_table(S, ks))


def generic(S, med, id_, coach, ks, title, hook, headline, body, caveat):
    return card(id_, title, hook, headline, coach_chart(S, ks, med), COACH_LEG, body, METHOD, caveat, coach_table(S, ks))


def wenger_study(S, med):
    ks = keys_of(S, "Arsène Wenger")
    a, b = S[ks[0]], S[ks[1]]
    return generic(
        S, med, "a-wenger", "Arsène Wenger", ks, "Wenger 2004 e 2016: lo stesso allenatore, dodici anni dopo",
        "Stesso allenatore, stessa squadra, 12 anni di distanza: com'è cambiato l'Arsenal di Wenger?",
        f"Il possesso è quasi identico ({fmt(a['possesso_pct'], 0)}% e {fmt(b['possesso_pct'], 0)}%), ma l'Arsenal 2015/16 gioca molto più "
        f"vicino alla porta avversaria: field tilt dal {fmt(a['field_tilt_pct'], 0)}% al {fmt(b['field_tilt_pct'], 0)}%, pressioni nell'ultimo "
        f"terzo da {fmt(a['pressioni_alte'], 0)} a {fmt(b['pressioni_alte'], 0)} a partita.",
        [f"Gli Invincibili del 2003/04 attaccavano in velocità: {fmt(a['passaggi_per_possesso'])} passaggi per azione, {fmt(a['lanci_pct'], 1)}% di "
         f"lanci lunghi. Nel 2015/16 le azioni sono più lunghe ({fmt(b['passaggi_per_possesso'])} passaggi) e i lanci scendono al "
         f"{fmt(b['lanci_pct'], 1)}%.",
         f"Il risultato non segue lo stile: il 2003/04 (imbattuto, {fmt(a['ppg'], 2)} punti a partita nel database) concedeva meno "
         f"({fmt(a['xg_subiti'], 2)} xG contro {fmt(b['xg_subiti'], 2)}). Wenger si è adattato al calcio del suo tempo, che nel frattempo "
         "era diventato più di possesso e pressione."],
        "Nei dodici anni cambia anche il calcio: parte della differenza è l'epoca (vedi lo studio sulle epoche). Della Premier 2003/04 il "
        "database contiene solo le partite dell'Arsenal, quindi non si può confrontare con la media di quel campionato.")


def montemurro_study(S, med):
    ks = keys_of(S, "Joseph Montemurro")
    ars = [S[k] for k in ks if k[1] == "Arsenal WFC"]
    juv = S[ks[-1]]
    pa = statistics.mean(x["possesso_pct"] for x in ars)
    pp = statistics.mean(x["ppda"] for x in ars)
    return generic(
        S, med, "a-montemurro", "Joseph Montemurro", ks, "Montemurro: dall'Arsenal alla Juventus, la stessa squadra in un altro paese",
        "Si può riconoscere un allenatore dai numeri? Montemurro sì, anche in un altro campionato.",
        f"Con l'Arsenal (tre stagioni) teneva in media il {fmt(pa, 0)}% di possesso con un PPDA di {fmt(pp)}; alla Juventus, in Serie A, "
        f"{fmt(juv['possesso_pct'], 0)}% e {fmt(juv['ppda'])}. Tra gli allenatori con almeno due squadre nel database è quello il cui stile cambia meno.",
        ["Squadra di possesso, pressing medio-alto, azioni di circa 5 passaggi: il profilo resta lo stesso in Inghilterra e in Italia.",
         f"Cambia la produzione offensiva: {fmt(statistics.mean(x['xg'] for x in ars), 2)} xG a partita con l'Arsenal, {fmt(juv['xg'], 2)} con la "
         "Juventus, coerente con una rosa e un campionato diversi."],
        "Calcio femminile: le mediane sono quelle delle squadre femminili. Arsenal e Juventus erano entrambe squadre di vertice nei loro "
        "campionati, quindi il confronto è più pulito di un passaggio da piccola a grande.")


def luis_enrique_study(S, med):
    ks = keys_of(S, "Luis Enrique")
    sp = S[ks[-1]]
    bar = [S[k] for k in ks[:-1]]
    return generic(
        S, med, "a-luisenrique", "Luis Enrique", ks, "Luis Enrique: dal Barcellona della MSN alla Spagna del possesso",
        "Il Barça della MSN e la Spagna di Pedri: due squadre opposte, stesso allenatore.",
        f"Con la Spagna (Euro 2020 e Mondiale 2022) Luis Enrique tiene il {fmt(sp['possesso_pct'], 0)}% di possesso e fa {fmt(sp['passaggi_per_possesso'])} "
        f"passaggi per azione, molto più del suo Barcellona ({fmt(min(x['passaggi_per_possesso'] for x in bar))}–{fmt(max(x['passaggi_per_possesso'] for x in bar))}).",
        [f"Il Barcellona 2014–2017 con Messi, Suárez e Neymar era più diretto: lanci lunghi tra il {fmt(min(x['lanci_pct'] for x in bar), 1)}% e il "
         f"{fmt(max(x['lanci_pct'] for x in bar), 1)}%, {fmt(max(x['xg'] for x in bar), 2)} xG a partita nella stagione migliore.",
         f"Il pressing è la costante: PPDA tra {fmt(min(x['ppda'] for x in bar + [sp]))} e {fmt(max(x['ppda'] for x in bar + [sp]))} in tutti i periodi. "
         f"Con la Spagna le pressioni nell'ultimo terzo salgono a {fmt(sp['pressioni_alte'], 0)} a partita."],
        "Le partite della Spagna sono 10, contro avversari di tornei internazionali; quelle del Barcellona sono di Liga. Contesti molto "
        "diversi: il confronto descrive due squadre, non 'il vero' Luis Enrique.")


def hayes_study(S, med):
    ks = keys_of(S, "Emma Hayes")
    a, b = S[ks[0]], S[ks[-1]]
    best = max((S[k] for k in ks), key=lambda x: x["xg"] - x["xg_subiti"])
    bk = next(k for k in ks if S[k] is best)
    return generic(
        S, med, "a-hayes", "Emma Hayes", ks, "Emma Hayes e il Chelsea: sei anni di evoluzione",
        "La tecnica che ha costruito il Chelsea più vincente d'Inghilterra: come è cambiato il suo calcio.",
        f"Dal 2018/19 al 2023/24 il Chelsea di Emma Hayes riduce i lanci lunghi dal {fmt(a['lanci_pct'], 1)}% al {fmt(b['lanci_pct'], 1)}% "
        f"dei passaggi e alza le pressioni nell'ultimo terzo da {fmt(a['pressioni_alte'], 0)} a {fmt(b['pressioni_alte'], 0)} a partita.",
        [f"La stagione più dominante è il {bk[2]}: {fmt(best['xg'], 2)} xG creati e {fmt(best['xg_subiti'], 2)} concessi a partita.",
         "Il Chelsea resta sempre sopra la mediana del campionato per possesso e field tilt, ma il modo di arrivarci cambia: più "
         "costruzione palla a terra, più pressione alta."],
        "Stagioni presenti: " + ", ".join(S[k]["label"] for k in ks) + ". Le altre non sono negli Open Data o hanno meno di 15 partite "
        "valide nel database.")


def mourinho_study(T):
    rs = [r for r in T if "Mourinho" in r["allenatore"]]
    pts = []
    for r in rs:
        hl = r["squadra"] != "Chelsea"
        lab = f"{nm(r['squadra'])} {r['gol']}-{r['gol_subiti']} {nm(r['avversario'])} ({r['data'][:4]})"
        pts.append((num(r["possesso_pct"]), num(r["ppda"]), lab, hl, f"{lab}: possesso {fmt(num(r['possesso_pct']), 0)}%, PPDA {fmt(num(r['ppda']))}"))
    chart = scatter(pts, "Possesso (%)", "PPDA (più basso = più pressing)")
    ch = [r for r in rs if r["squadra"] == "Chelsea"]
    big = [r for r in rs if r["squadra"] != "Chelsea"]
    avg = lambda xs, k: sum(num(r[k]) for r in xs) / len(xs)
    wins = sum(r["esito"] == "V" for r in big)
    inter = next(r for r in big if r["squadra"] == "Inter Milan")
    cl = [r for r in big if r["squadra"] == "Real Madrid"]
    return card(
        "a-mourinho", "Mourinho, il camaleonte: possesso solo quando serve",
        "Mourinho 'non sa giocare a calcio'? I dati raccontano un allenatore che cambia pelle a seconda dell'avversario.",
        f"Nelle {len(ch)} partite del Chelsea 2015/16 Mourinho tiene il {fmt(avg(ch, 'possesso_pct'), 0)}% di possesso. Nelle {len(big)} partite "
        f"contro grandi avversari (finali di Champions e Clásici) scende al {fmt(avg(big, 'possesso_pct'), 0)}%: ne vince {wins}.",
        chart, legend([("var(--s1)", "Finali e Clásici (Porto, Inter, Real Madrid)"), ("var(--context)", "Chelsea 2015/16, Premier League")]),
        ["Il possesso non è un'identità ma uno strumento: contro il Barcellona e nelle finali Mourinho lascia la palla e difende basso.",
         f"La finale di Champions 2010 (Bayern–Inter 0-2) è l'esempio più netto: {fmt(num(inter['possesso_pct']), 0)}% di possesso, coppa "
         f"vinta. Nei {len(cl)} Clásici con il Real Madrid il possesso sta tra il {fmt(min(num(r['possesso_pct']) for r in cl), 0)}% e il "
         f"{fmt(max(num(r['possesso_pct']) for r in cl), 0)}%."],
        f"Tutte le {len(rs)} partite di squadre allenate da Mourinho nel database: {len(ch)} del Chelsea 2015/16 (fino all'esonero di dicembre), la "
        "finale di Champions 2004 (Porto) e 2010 (Inter), 4 Clásici con il Real Madrid (2010–2012).",
        "Campione molto sbilanciato: mancano le stagioni migliori in campionato (Porto, primo Chelsea, Inter, Real). Le partite contro il "
        "Barcellona sono quelle in cui il database contiene Messi, quindi sono tutte contro la squadra più forte del periodo.",
        table(["Partita", "Possesso", "PPDA", "xG", "xG concessi"],
              [[f"{nm(r['squadra'])} {r['gol']}-{r['gol_subiti']} {nm(r['avversario'])} ({r['data']})", fmt(num(r["possesso_pct"]), 0) + "%",
                fmt(num(r["ppda"])), fmt(num(r["xg"]), 2), fmt(num(r["xg_subiti"]), 2)] for r in sorted(rs, key=lambda r: r["data"])]))


def martinez_study(S, med):
    ks = keys_of(S, "Roberto Martínez")
    ev, be, po = (S[k] for k in ks)
    return generic(
        S, med, "a-martinez", "Roberto Martínez", ks, "Roberto Martínez: Everton, Belgio, Portogallo",
        "Tre squadre, tre rose diversissime: cosa resta dello stile di Roberto Martínez?",
        f"Il possesso segue i giocatori: {fmt(ev['possesso_pct'], 0)}% con l'Everton, {fmt(be['possesso_pct'], 0)}% con il Belgio, "
        f"{fmt(po['possesso_pct'], 0)}% con il Portogallo. Il pressing cambia meno: PPDA {fmt(ev['ppda'])}, {fmt(be['ppda'])} e {fmt(po['ppda'])}.",
        [f"Con il Belgio della generazione d'oro (Mondiali 2018 e 2022, Euro 2020) le azioni si allungano: {fmt(be['passaggi_per_possesso'])} "
         f"passaggi per azione contro {fmt(ev['passaggi_per_possesso'])} all'Everton.",
         f"Con il Portogallo a Euro 2024 la squadra domina il territorio (field tilt {fmt(po['field_tilt_pct'], 0)}%) ma crea "
         f"{fmt(po['xg'], 2)} xG a partita."],
        "Le partite delle nazionali sono poche (Belgio 15, Portogallo 5) e contro avversari di tornei internazionali.")


def mancini_study(S, med):
    ks = keys_of(S, "Roberto Mancini")
    a, b = S[ks[0]], S[ks[-1]]
    return generic(
        S, med, "a-mancini", "Roberto Mancini", ks, "Mancini dall'Inter all'Italia campione d'Europa",
        "Dall'Inter 2015/16 all'Italia di Wembley: come è cambiato il calcio di Mancini?",
        f"L'Italia di Euro 2020 concede {fmt(b['xg_subiti'], 2)} xG a partita contro gli {fmt(a['xg_subiti'], 2)} dell'Inter 2015/16, gioca di più "
        f"nell'ultimo terzo (field tilt {fmt(b['field_tilt_pct'], 0)}% contro {fmt(a['field_tilt_pct'], 0)}%) e fa azioni più lunghe "
        f"({fmt(b['passaggi_per_possesso'])} passaggi contro {fmt(a['passaggi_per_possesso'])}).",
        [f"Il pressing resta simile (PPDA {fmt(a['ppda'])} e {fmt(b['ppda'])}), ma le pressioni nell'ultimo terzo salgono da "
         f"{fmt(a['pressioni_alte'], 0)} a {fmt(b['pressioni_alte'], 0)}: l'Italia aggrediva più in alto.",
         "Con meno lanci lunghi e più passaggi corti, l'Italia di Mancini è più 'spagnola' della sua Inter."],
        "L'Italia ha 7 partite (tutto l'Europeo, compresi supplementari e rigori) contro le 38 della Serie A: il campione è piccolo e gli "
        "avversari sono diversi.")


def valverde_study(S, med):
    ks = keys_of(S, "Ernesto Valverde")
    a = S[ks[0]]
    bs = [S[k] for k in ks[1:]]
    return generic(
        S, med, "a-valverde", "Ernesto Valverde", ks, "Valverde: dall'Athletic al Barcellona di Messi",
        "Lo stesso allenatore con la squadra più 'inglese' della Liga e con il Barcellona di Messi.",
        f"All'Athletic 2015/16 Valverde teneva il {fmt(a['possesso_pct'], 0)}% di possesso con il {fmt(a['lanci_pct'], 1)}% di lanci lunghi; "
        f"al Barcellona sale al {fmt(min(x['possesso_pct'] for x in bs), 0)}–{fmt(max(x['possesso_pct'] for x in bs), 0)}% e i lanci scendono "
        f"sotto il {fmt(max(x['lanci_pct'] for x in bs) + 0.5, 0)}%.",
        [f"Il pressing è quasi identico: PPDA {fmt(a['ppda'])} a Bilbao, {', '.join(fmt(x['ppda']) for x in bs)} a Barcellona.",
         f"Con Messi gli xG creati passano da {fmt(a['xg'], 2)} a {fmt(max(x['xg'] for x in bs), 2)} a partita, ma gli xG concessi restano "
         f"simili ({fmt(a['xg_subiti'], 2)} e {fmt(statistics.mean(x['xg_subiti'] for x in bs), 2)})."],
        "Nella stagione 2019/20, esonerato a gennaio, Valverde ha meno di 15 partite nel database e non è incluso.")


CALENDAR_ALL = {1: "a-firma", 3: "a-big", 5: "a-guardiola", 7: "a-mourinho", 9: "a-montemurro", 11: "a-wenger", 13: "a-luisenrique",
                15: "a-hayes", 17: "a-valverde", 19: "a-mancini", 21: "a-martinez"}
TAGS = {"a-firma": "#allenatori #tattica", "a-big": "#allenatori #barcellona #psg", "a-guardiola": "#guardiola #tikitaka #barcellona",
        "a-mourinho": "#mourinho #specialone", "a-montemurro": "#montemurro #juventuswomen #arsenalwomen", "a-wenger": "#wenger #arsenal #invincibili",
        "a-luisenrique": "#luisenrique #spagna #barcellona", "a-hayes": "#emmahayes #chelseawomen #WSL", "a-valverde": "#valverde #athletic #barcellona",
        "a-mancini": "#mancini #italia #euro2020", "a-martinez": "#robertomartinez #belgio #portogallo"}


def build(Tv, T_all):
    S = spells(Tv)
    med = medians(S)
    return [signature_study(S), big_club_study(S), guardiola_study(S), mourinho_study(T_all), montemurro_study(S, med), wenger_study(S, med),
            luis_enrique_study(S, med), hayes_study(S, med), valverde_study(S, med), mancini_study(S, med), martinez_study(S, med)]
