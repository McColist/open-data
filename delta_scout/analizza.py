"""Delta Scout - analisi di tutte le partite StatsBomb Open Data.

Uso:
    python delta_scout/analizza.py                 # tutte le partite di partite.csv
    python delta_scout/analizza.py --n 831-894,3960 # solo alcuni numeri
    python delta_scout/analizza.py --workers 8

Output in delta_scout/output/ (vedi delta_scout/README.md per il significato delle colonne):
    squadre.csv, giocatori.csv, tiri.csv, rete_passaggi.csv
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HERE = Path(__file__).resolve().parent

GOAL = (120.0, 40.0)
SET_PIECE_PASSES = {"Corner", "Free Kick", "Throw-in", "Goal Kick", "Kick Off"}
TACKLE_WON = {"Won", "Success", "Success In Play", "Success Out"}
TOUCH_TYPES = {"Pass", "Ball Receipt*", "Carry", "Shot", "Dribble", "Ball Recovery", "Clearance",
               "Interception", "Miscontrol", "Dispossessed", "Duel", "Goal Keeper", "50/50", "Block"}


def load_xt():
    f = Path(__file__).resolve().parent / "xt_griglia.json"
    return json.loads(f.read_text(encoding="utf-8"))["griglia"] if f.exists() else None


XT = load_xt()


def xt_at(p):
    x = min(int(p[0] / 120 * 16), 15)
    y = min(int(p[1] / 80 * 12), 11)
    return XT[y][x]


def xt_gain(start, end):
    return xt_at(end) - xt_at(start) if XT and start and end else 0.0


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_progressive(start, end, min_gain=0.0):
    d0, d1 = dist(start, GOAL), dist(end, GOAL)
    return d1 <= 0.75 * d0 and d0 - d1 >= min_gain


def in_box(p):
    return p[0] >= 102 and 18 <= p[1] <= 62


def zone(p):
    """Griglia 6x4 (colonne lungo il campo, righe in larghezza) -> indice 0..23."""
    c = min(int(p[0] / 20), 5)
    r = min(int(p[1] / 20), 3)
    return r * 6 + c


def in_triangle(p, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def ts(t):
    """'HH:MM:SS.mmm' -> secondi."""
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def kev(base, e, tipo, giocatore, dettaglio):
    return {**base, "periodo": e["period"], "minuto": e["minute"], "secondo": e["second"],
            "squadra": e["team"]["name"], "tipo": tipo, "giocatore": giocatore, "dettaglio": dettaglio}


def card_of(e):
    for k in ("foul_committed", "bad_behaviour"):
        c = e.get(k, {}).get("card")
        if c:
            return c["name"]
    return None


def new_player():
    return defaultdict(float)


def analyse(meta):
    mid = meta["match_id"]
    ev_path = DATA / "events" / f"{mid}.json"
    if not ev_path.exists():
        return None
    events = [e for e in load(ev_path) if e["period"] <= 4]  # esclusi i rigori finali
    teams = [meta["casa"], meta["trasferta"]]
    base = {"n": meta["n"], "match_id": mid, "competizione": meta["competizione"],
            "stagione": meta["stagione"], "data": meta["data"]}

    by_id = {e["id"]: e for e in events}

    # --- 360 -------------------------------------------------------------
    frames = {}
    p360 = DATA / "three-sixty" / f"{mid}.json"
    if p360.exists():
        try:
            for f in load(p360):
                frames[f["event_uuid"]] = f
        except json.JSONDecodeError:
            frames = {}  # file 360 corrotto nei dati sorgente (es. 3845506): analisi senza 360

    # --- anagrafica dai lineup, minuti dagli eventi -----------------------
    players = defaultdict(new_player)
    info = {}
    lu_path = DATA / "lineups" / f"{mid}.json"
    if lu_path.exists():
        for t in load(lu_path):
            for p in t["lineup"]:
                if not p.get("positions"):
                    continue  # in panchina, non entrato
                info[(t["team_name"], p["player_id"])] = {
                    "giocatore": p["player_name"], "soprannome": p.get("player_nickname") or "",
                    "maglia": p.get("jersey_number"), "ruolo": p["positions"][0]["position"],
                    "titolare": int(p["positions"][0].get("start_reason") == "Starting XI"),
                    "nazionalita": (p.get("country") or {}).get("name", "")}

    # tempo di gioco effettivo: somma delle durate dei periodi precedenti + timestamp nel periodo
    period_len = defaultdict(float)
    for e in events:
        period_len[e["period"]] = max(period_len[e["period"]], ts(e["timestamp"]))
    offset = {p: sum(period_len[q] for q in period_len if q < p) for p in period_len}
    end_time = sum(period_len.values())
    elapsed = lambda e: offset[e["period"]] + ts(e["timestamp"])
    on_time, off_time = {}, {}
    for e in events:
        team = e["team"]["name"]
        typ = e["type"]["name"]
        if typ == "Starting XI":
            for p in e["tactics"]["lineup"]:
                on_time[(team, p["player"]["id"])] = 0.0
        elif typ == "Substitution":
            off_time.setdefault((team, e["player"]["id"]), elapsed(e))
            on_time.setdefault((team, e["substitution"]["replacement"]["id"]), elapsed(e))
        elif card_of(e) in ("Red Card", "Second Yellow") and e.get("player"):
            off_time.setdefault((team, e["player"]["id"]), elapsed(e))
    for key, start in on_time.items():
        players[key]["minuti"] = round((off_time.get(key, end_time) - start) / 60, 1)

    # --- xG per possesso (per xG chain) e xA ------------------------------
    poss_xg = defaultdict(float)
    xa = defaultdict(float)
    for e in events:
        if e["type"]["name"] == "Shot":
            sh = e["shot"]
            xg = sh.get("statsbomb_xg", 0.0) or 0.0
            poss_xg[(e["possession"], e["team"]["name"])] += xg
            if sh.get("key_pass_id"):
                xa[sh["key_pass_id"]] += xg

    T = {t: defaultdict(float) for t in teams}
    shots, edges = [], defaultdict(int)
    loc_sum = defaultdict(lambda: [0.0, 0.0, 0])
    heat = defaultdict(lambda: [0] * 24)
    chain = defaultdict(set)
    opp_near = defaultdict(lambda: [0, 0, 0])  # n eventi 360, somma avversari 5m, eventi con >=2 avversari
    team_near = defaultdict(lambda: [0, 0, 0])
    formation, current_formation = {}, {}
    poss_passes = defaultdict(int)  # (squadra, possesso) -> passaggi
    max_min = max((e["minute"] for e in events), default=90)
    momentum = {t: [0] * (max_min // 5 + 1) for t in teams}
    heat_team = {t: {k: [0] * 24 for k in ("tocchi", "pressioni", "difesa")} for t in teams}
    key_events = []
    sca = defaultdict(lambda: [0, 0])  # giocatore -> [azioni che portano al tiro, ... al gol]
    last_actions = defaultdict(list)  # (squadra, possesso) -> ultime azioni offensive

    for e in events:
        typ = e["type"]["name"]
        team = e["team"]["name"]
        if team not in T:
            continue
        opp = teams[1] if team == teams[0] else teams[0]
        t, o = T[team], T[opp]
        pl = e.get("player")
        key = (team, pl["id"]) if pl else None
        P = players[key] if key else defaultdict(float)
        if key and key not in info:
            info[key] = {"giocatore": pl["name"], "soprannome": "", "maglia": None,
                         "ruolo": e.get("position", {}).get("name", ""), "titolare": 0, "nazionalita": ""}
        loc = e.get("location")
        if typ == "Starting XI":
            formation[team] = str(e["tactics"].get("formation", ""))
        elif typ == "Tactical Shift":
            fm = str(e["tactics"].get("formation", ""))
            prev = current_formation.get(team, formation.get(team, ""))
            if fm != prev:  # solo veri cambi di modulo, non scambi di posizione
                key_events.append(kev(base, e, "Cambio modulo", "", f'{"-".join(prev)} → {"-".join(fm)}'))
                current_formation[team] = fm
        elif typ == "Substitution":
            key_events.append(kev(base, e, "Sostituzione", pl["name"],
                                  f'entra {e["substitution"]["replacement"]["name"]}'
                                  + (f' ({e["substitution"]["outcome"]["name"]})' if e["substitution"].get("outcome") else "")))
        elif typ == "Own Goal Against":
            key_events.append(kev(base, e, "Autogol", pl["name"] if pl else "", f"a favore di {opp}"))
        if loc and typ in TOUCH_TYPES:
            heat_team[team]["tocchi"][zone(loc)] += 1
            if loc[0] >= 80:
                momentum[team][e["minute"] // 5] += 1
        if loc and typ in ("Duel", "Interception", "Ball Recovery", "Block", "Clearance"):
            heat_team[team]["difesa"][zone(loc)] += 1
        if e.get("possession_team", {}).get("name") == team and typ in ("Pass", "Dribble", "Foul Won", "Shot", "Carry"):
            ok_action = (typ == "Pass" and "outcome" not in e["pass"]) or \
                        (typ == "Dribble" and e["dribble"]["outcome"]["name"] == "Complete") or typ in ("Foul Won", "Shot")
            if typ == "Shot":
                g = e["shot"]["outcome"]["name"] == "Goal"
                for k2 in last_actions[(team, e["possession"])][-2:]:
                    sca[k2][0] += 1
                    sca[k2][1] += g
            if ok_action and key:
                last_actions[(team, e["possession"])].append(key)
        if key and loc and typ in TOUCH_TYPES:
            ls = loc_sum[key]
            ls[0] += loc[0]; ls[1] += loc[1]; ls[2] += 1
            heat[key][zone(loc)] += 1
            P["azioni_con_palla"] += 1
            if in_box(loc):
                P["tocchi_in_area"] += 1
        if key and e.get("possession_team", {}).get("name") == team:
            chain[key].add(e["possession"])
        if e.get("duration") and e.get("possession_team"):
            pt = e["possession_team"]["name"]
            if pt in T:
                T[pt]["_durata_possesso"] += e["duration"]

        # 360: avversari entro 5 m dal giocatore in azione
        fr = frames.get(e["id"])
        if fr and key:
            actor = next((p for p in fr["freeze_frame"] if p.get("actor")), None)
            if actor:
                near = sum(1 for p in fr["freeze_frame"]
                           if not p["teammate"] and dist(p["location"], actor["location"]) <= 5)
                for acc in (opp_near[key], team_near[team]):
                    acc[0] += 1; acc[1] += near; acc[2] += near >= 2

        if typ == "Pass":
            ps = e["pass"]
            ptype = ps.get("type", {}).get("name")
            ok = "outcome" not in ps
            end = ps.get("end_location", loc)
            t["passaggi"] += 1; P["passaggi"] += 1
            poss_passes[(team, e["possession"])] += 1
            t["_lunghezza_passaggi"] += ps.get("length", 0)
            P["_lunghezza_passaggi"] += ps.get("length", 0)
            if end[0] - loc[0] > 2:
                P["passaggi_avanti"] += 1; t["passaggi_avanti"] += 1
            elif end[0] - loc[0] < -2:
                P["passaggi_indietro"] += 1
            if e.get("under_pressure"):
                t["passaggi_sotto_pressione"] += 1
            if ps.get("length", 0) >= 32:
                t["lanci_lunghi"] += 1
            if ok:
                t["passaggi_riusciti"] += 1; P["passaggi_riusciti"] += 1
            if loc[0] >= 80 or end[0] >= 80:
                t["_passaggi_terzo_finale_tilt"] += 1
            if loc[0] < 72:
                t["_passaggi_propria_meta60"] += 1
            if ps.get("cross"):
                t["cross"] += 1; P["cross"] += 1
                if ok:
                    t["cross_riusciti"] += 1; P["cross_riusciti"] += 1
            if ptype == "Corner":
                t["corner"] += 1
            if ps.get("shot_assist") or ps.get("goal_assist"):
                P["passaggi_chiave"] += 1; t["passaggi_chiave"] += 1
            if ps.get("goal_assist"):
                P["assist"] += 1
            P["xa"] += xa.get(e["id"], 0.0)
            if ps.get("switch"):
                P["cambi_gioco"] += 1
            if ps.get("through_ball") or ps.get("technique", {}).get("name") == "Through Ball":
                P["filtranti"] += 1
            if ps.get("length", 0) >= 32:
                P["lanci_lunghi"] += 1
                if ok:
                    P["lanci_lunghi_riusciti"] += 1
            if ok:
                gain = xt_gain(loc, end)
                P["xt"] += gain; P["xt_passaggi"] += gain; t["xt"] += gain
            if ok and ptype not in SET_PIECE_PASSES:
                if is_progressive(loc, end):
                    t["passaggi_progressivi"] += 1; P["passaggi_progressivi"] += 1
                if end[0] >= 80 and loc[0] < 80:
                    t["passaggi_terzo_finale"] += 1; P["passaggi_terzo_finale"] += 1
                if in_box(end) and not in_box(loc):
                    t["passaggi_in_area"] += 1; P["passaggi_in_area"] += 1
                if ps.get("recipient"):
                    edges[(team, pl["id"], ps["recipient"]["id"])] += 1
                    P["_dist_progressiva"] += max(0.0, end[0] - loc[0])
            if e.get("under_pressure"):
                P["passaggi_sotto_pressione"] += 1
                if ok:
                    P["passaggi_sotto_pressione_riusciti"] += 1
            if ps.get("aerial_won"):
                P["aerei_vinti"] += 1; t["aerei_vinti"] += 1

        elif typ == "Ball Receipt*":
            if "ball_receipt" not in e:
                P["ricezioni"] += 1
                if loc and loc[0] >= 80:
                    P["ricezioni_terzo_finale"] += 1

        elif typ == "Carry":
            end = e["carry"]["end_location"]
            gain = xt_gain(loc, end)
            P["xt"] += gain; P["xt_conduzioni"] += gain; t["xt"] += gain
            if is_progressive(loc, end, 5):
                t["conduzioni_progressive"] += 1; P["conduzioni_progressive"] += 1
            if in_box(end) and not in_box(loc):
                P["conduzioni_in_area"] += 1
            if end[0] >= 80 and loc[0] < 80:
                P["conduzioni_terzo_finale"] += 1
            P["_dist_progressiva"] += max(0.0, end[0] - loc[0])

        elif typ == "Shot":
            sh = e["shot"]
            xg = sh.get("statsbomb_xg", 0.0) or 0.0
            out = sh["outcome"]["name"]
            stype = sh.get("type", {}).get("name", "")
            is_pen = stype == "Penalty"
            t["tiri"] += 1; P["tiri"] += 1
            t["xg"] += xg; P["xg"] += xg
            o["xg_subiti"] += xg
            if not is_pen:
                t["npxg"] += xg; P["npxg"] += xg
            t[f"xg_{e['period'] if e['period'] <= 2 else 'suppl'}t"] += xg
            if out in ("Goal", "Saved", "Saved To Post"):
                t["tiri_in_porta"] += 1; P["tiri_in_porta"] += 1
            if e.get("play_pattern", {}).get("name") == "From Counter":
                t["tiri_contropiede"] += 1
            if out == "Goal":
                key_events.append(kev(base, e, "Gol su rigore" if is_pen else "Gol", pl["name"],
                                      f'xG {xg:.2f}' + (f', assist {by_id[sh["key_pass_id"]]["player"]["name"]}'
                                                        if sh.get("key_pass_id") in by_id else "")))
                P["gol"] += 1
                if not is_pen:
                    P["gol_np"] += 1
            if loc and in_box(loc):
                t["tiri_in_area"] += 1
            if sh.get("aerial_won"):
                P["aerei_vinti"] += 1; t["aerei_vinti"] += 1
            ff = sh.get("freeze_frame", [])
            defenders = sum(1 for p in ff if not p["teammate"] and p["position"]["name"] != "Goalkeeper"
                            and in_triangle(p["location"], loc, (120, 36), (120, 44)))
            gk = next((p for p in ff if not p["teammate"] and p["position"]["name"] == "Goalkeeper"), None)
            kp = by_id.get(sh.get("key_pass_id"))
            endl = (sh.get("end_location") or []) + [""] * 3
            shots.append({**base, "squadra": team, "avversario": opp, "giocatore": pl["name"],
                          "player_id": pl["id"], "periodo": e["period"], "minuto": e["minute"],
                          "secondo": e["second"], "x": loc[0], "y": loc[1],
                          "distanza_porta": round(dist(loc, GOAL), 1),
                          "xg": round(xg, 4), "esito": out, "gol": int(out == "Goal"),
                          "tipo": stype, "parte_corpo": sh.get("body_part", {}).get("name", ""),
                          "tecnica": sh.get("technique", {}).get("name", ""),
                          "azione": e.get("play_pattern", {}).get("name", ""),
                          "primo_tocco": int(bool(sh.get("first_time"))),
                          "sotto_pressione": int(bool(e.get("under_pressure"))),
                          "difensori_nel_triangolo": defenders,
                          "portiere_dist_porta": round(dist(gk["location"], GOAL), 1) if gk else "",
                          "assistman": kp["player"]["name"] if kp else "",
                          "fine_x": endl[0], "fine_y": endl[1], "fine_z": endl[2]})

        elif typ == "Pressure":
            t["pressioni"] += 1; P["pressioni"] += 1
            heat_team[team]["pressioni"][zone(loc)] += 1
            if loc[0] >= 80:
                t["pressioni_alte"] += 1; P["pressioni_alte"] += 1
            if e.get("counterpress"):
                t["contropressioni"] += 1; P["contropressioni"] += 1

        elif typ == "Duel":
            d = e["duel"]
            dtype = d.get("type", {}).get("name")
            if dtype == "Tackle":
                P["contrasti"] += 1
                if d.get("outcome", {}).get("name") in TACKLE_WON:
                    P["contrasti_vinti"] += 1; t["contrasti_vinti"] += 1
                if loc[0] >= 48:
                    t["_azioni_difensive_ppda"] += 1
            elif dtype == "Aerial Lost":
                P["aerei_persi"] += 1

        elif typ == "50/50":
            if e.get("50_50", {}).get("outcome", {}).get("name") in ("Won", "Success To Team"):
                P["contese_vinte"] += 1; t["contese_vinte"] += 1

        elif typ == "Interception":
            P["intercetti"] += 1; t["intercetti"] += 1
            if loc[0] >= 48:
                t["_azioni_difensive_ppda"] += 1

        elif typ == "Ball Recovery":
            if not e.get("ball_recovery", {}).get("recovery_failure"):
                P["recuperi"] += 1; t["recuperi"] += 1
                if loc and loc[0] >= 80:
                    P["recuperi_alti"] += 1; t["recuperi_alti"] += 1

        elif typ == "Clearance":
            P["respinte"] += 1
            if e.get("clearance", {}).get("aerial_won"):
                P["aerei_vinti"] += 1; t["aerei_vinti"] += 1

        elif typ == "Block":
            P["blocchi"] += 1

        elif typ == "Dribble":
            P["dribbling"] += 1; t["dribbling"] += 1
            if e["dribble"]["outcome"]["name"] == "Complete":
                P["dribbling_riusciti"] += 1; t["dribbling_riusciti"] += 1

        elif typ == "Dribbled Past":
            P["saltato_da_avversario"] += 1

        elif typ == "Foul Committed":
            P["falli_commessi"] += 1; t["falli"] += 1
            if loc and loc[0] >= 48:
                t["_azioni_difensive_ppda"] += 1

        elif typ == "Foul Won":
            P["falli_subiti"] += 1

        elif typ in ("Dispossessed", "Miscontrol"):
            P["palle_perse"] += 1; t["palle_perse"] += 1
            if typ == "Miscontrol" and e.get("miscontrol", {}).get("aerial_won"):
                P["aerei_vinti"] += 1

        elif typ == "Offside":
            t["fuorigioco"] += 1

        elif typ == "Goal Keeper":
            gtype = e["goalkeeper"].get("type", {}).get("name", "")
            if gtype in ("Shot Saved", "Shot Saved To Post", "Shot Saved Off Target", "Penalty Saved"):
                P["parate"] += 1; t["parate"] += 1
            if gtype == "Goal Conceded":
                P["gol_subiti_portiere"] += 1
            if gtype == "Keeper Sweeper":
                P["uscite"] += 1
            if gtype == "Collected":
                P["prese_alte"] += 1
            if gtype == "Punch":
                P["respinte_di_pugno"] += 1

        c = card_of(e)
        if c and key:
            key_events.append(kev(base, e, {"Yellow Card": "Giallo", "Second Yellow": "Secondo giallo"}.get(c, "Rosso"),
                                  pl["name"], ""))
            if c == "Yellow Card":
                P["gialli"] += 1; t["gialli"] += 1
            else:
                P["rossi"] += 1; t["rossi"] += 1

    # --- righe squadre ----------------------------------------------------
    total_poss = sum(T[x]["_durata_possesso"] for x in teams) or 1
    total_tilt = sum(T[x]["_passaggi_terzo_finale_tilt"] for x in teams) or 1
    score = {teams[0]: meta["gol_casa"], teams[1]: meta["gol_trasferta"]}
    team_rows = []
    for i, team in enumerate(teams):
        t, opp = T[team], teams[1 - i]
        o = T[opp]
        r = {**base, "squadra": team, "avversario": opp, "casa_trasferta": "casa" if i == 0 else "trasferta",
             "gol": score[team], "gol_subiti": score[opp],
             "esito": "V" if score[team] > score[opp] else "P" if score[team] < score[opp] else "N"}
        for k in ("xt", "xg", "npxg", "xg_subiti", "xg_1t", "xg_2t", "xg_supplt", "tiri", "tiri_in_porta",
                  "tiri_in_area", "passaggi", "passaggi_riusciti", "passaggi_progressivi",
                  "passaggi_terzo_finale", "passaggi_in_area", "passaggi_chiave", "cross", "cross_riusciti",
                  "conduzioni_progressive", "dribbling", "dribbling_riusciti", "pressioni", "pressioni_alte",
                  "contropressioni", "recuperi", "recuperi_alti", "contrasti_vinti", "intercetti",
                  "aerei_vinti", "palle_perse", "parate", "falli", "gialli", "rossi", "corner", "fuorigioco"):
            v = t.get(k, 0)
            r[k] = round(v, 3) if isinstance(v, float) and not v.is_integer() else int(v)
        r["tiri_subiti"] = int(o["tiri"])
        r["modulo"] = "-".join(formation.get(team, ""))
        r["allenatore"] = meta["allenatori"].get(team, "")
        for k in ("fase", "giornata", "stadio", "arbitro"):
            r[k] = meta[k]
        poss = [v for (pt, _), v in poss_passes.items() if pt == team]
        r["possessi"] = len(poss)
        r["passaggi_per_possesso"] = round(sum(poss) / len(poss), 2) if poss else 0
        r["sequenze_10_passaggi"] = sum(1 for v in poss if v >= 10)
        r["lunghezza_media_passaggi_m"] = round(t["_lunghezza_passaggi"] / t["passaggi"] * 0.9144, 1) if t["passaggi"] else 0
        r["passaggi_avanti_pct"] = round(100 * t["passaggi_avanti"] / t["passaggi"], 1) if t["passaggi"] else 0
        r["lanci_lunghi"] = int(t["lanci_lunghi"])
        r["passaggi_sotto_pressione"] = int(t["passaggi_sotto_pressione"])
        r["tiri_contropiede"] = int(t["tiri_contropiede"])
        r["contese_vinte"] = int(t["contese_vinte"])
        r["azioni_tiro_sca"] = sum(v[0] for (tm, _), v in sca.items() if tm == team)
        r["momentum_5min"] = ";".join(map(str, momentum[team]))
        for k in ("tocchi", "pressioni", "difesa"):
            r[f"heatmap_{k}_6x4"] = ";".join(map(str, heat_team[team][k]))
        r["xg_diff"] = round(t["xg"] - o["xg"], 3)
        r["xg_per_tiro"] = round(t["xg"] / t["tiri"], 3) if t["tiri"] else 0
        r["precisione_passaggi_pct"] = round(100 * t["passaggi_riusciti"] / t["passaggi"], 1) if t["passaggi"] else 0
        r["possesso_pct"] = round(100 * t["_durata_possesso"] / total_poss, 1)
        r["field_tilt_pct"] = round(100 * t["_passaggi_terzo_finale_tilt"] / total_tilt, 1)
        r["ppda"] = round(o["_passaggi_propria_meta60"] / t["_azioni_difensive_ppda"], 2) if t["_azioni_difensive_ppda"] else ""
        tn = team_near.get(team)
        r["dati_360"] = int(bool(frames))
        r["avversari_5m_medi_360"] = round(tn[1] / tn[0], 2) if tn and tn[0] else ""
        r["azioni_pressate_360_pct"] = round(100 * tn[2] / tn[0], 1) if tn and tn[0] else ""
        team_rows.append(r)

    # --- righe giocatori ------------------------------------------------
    player_rows = []
    for key, P in players.items():
        team, pid = key
        if team not in T or key not in info:
            continue
        mins = P.get("minuti", 0.0)
        if mins <= 0 and not P.get("azioni_con_palla"):
            continue
        ls = loc_sum.get(key)
        on = opp_near.get(key)
        opp = teams[1] if team == teams[0] else teams[0]
        r = {**base, "squadra": team, "avversario": opp, "player_id": pid, **info[key], "minuti": mins}
        for k in ("gol", "gol_np", "assist", "xg", "npxg", "xa", "xt", "xt_passaggi", "xt_conduzioni", "tiri", "tiri_in_porta", "passaggi_chiave",
                  "passaggi", "passaggi_riusciti", "passaggi_progressivi", "passaggi_terzo_finale",
                  "passaggi_in_area", "passaggi_sotto_pressione", "passaggi_sotto_pressione_riusciti",
                  "cross", "cross_riusciti", "filtranti", "cambi_gioco", "lanci_lunghi", "lanci_lunghi_riusciti",
                  "ricezioni", "ricezioni_terzo_finale", "conduzioni_progressive", "conduzioni_terzo_finale",
                  "conduzioni_in_area", "dribbling", "dribbling_riusciti", "azioni_con_palla", "tocchi_in_area",
                  "pressioni", "pressioni_alte", "contropressioni", "contrasti", "contrasti_vinti", "intercetti",
                  "recuperi", "recuperi_alti", "respinte", "blocchi", "aerei_vinti", "aerei_persi",
                  "saltato_da_avversario", "palle_perse", "falli_commessi", "falli_subiti", "gialli", "rossi",
                  "parate", "gol_subiti_portiere"):
            v = P.get(k, 0)
            r[k] = round(v, 4) if isinstance(v, float) and not v.is_integer() else int(v)
        r["sca"] = sca[key][0] if key in sca else 0
        r["gca"] = sca[key][1] if key in sca else 0
        for k in ("passaggi_avanti", "passaggi_indietro", "contese_vinte", "uscite", "prese_alte", "respinte_di_pugno"):
            r[k] = int(P.get(k, 0))
        r["lunghezza_media_passaggi_m"] = round(P["_lunghezza_passaggi"] / P["passaggi"] * 0.9144, 1) if P.get("passaggi") else ""
        r["xg_chain"] = round(sum(poss_xg.get((p, team), 0.0) for p in chain.get(key, ())), 4)
        r["metri_progressivi"] = round(P.get("_dist_progressiva", 0.0) * 0.9144, 1)  # yard -> metri
        r["precisione_passaggi_pct"] = round(100 * P["passaggi_riusciti"] / P["passaggi"], 1) if P.get("passaggi") else ""
        r["pos_media_x"] = round(ls[0] / ls[2], 1) if ls and ls[2] else ""
        r["pos_media_y"] = round(ls[1] / ls[2], 1) if ls and ls[2] else ""
        r["heatmap_6x4"] = ";".join(map(str, heat[key])) if key in heat else ""
        r["eventi_360"] = on[0] if on else 0
        r["avversari_5m_medi_360"] = round(on[1] / on[0], 2) if on and on[0] else ""
        r["azioni_pressate_360_pct"] = round(100 * on[2] / on[0], 1) if on and on[0] else ""
        player_rows.append(r)

    names = {k: v["giocatore"] for k, v in info.items()}
    edge_rows = [{**base, "squadra": team, "passatore_id": a, "passatore": names.get((team, a), ""),
                  "ricevente_id": b, "ricevente": names.get((team, b), ""), "passaggi": c}
                 for (team, a, b), c in edges.items() if c >= 2]
    return team_rows, player_rows, shots, edge_rows, key_events


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


def load_matches(selected):
    comps = load(DATA / "competitions.json")
    gender = {(c["competition_id"], c["season_id"]): c["competition_gender"] for c in comps}
    with open(HERE / "partite.csv", encoding="utf-8") as fh:
        index = {int(r["match_id"]): r for r in csv.DictReader(fh)}
    metas = []
    for (cid, sid) in gender:
        f = DATA / "matches" / str(cid) / f"{sid}.json"
        if not f.exists():
            continue
        for m in load(f):
            r = index.get(m["match_id"])
            if not r or (selected and int(r["n"]) not in selected):
                continue
            metas.append({"n": int(r["n"]), "match_id": m["match_id"], "competizione": r["competizione"],
                          "stagione": r["stagione"], "data": r["data"],
                          "casa": m["home_team"]["home_team_name"], "trasferta": m["away_team"]["away_team_name"],
                          "gol_casa": m["home_score"], "gol_trasferta": m["away_score"],
                          "fase": (m.get("competition_stage") or {}).get("name", ""),
                          "giornata": m.get("match_week") or "",
                          "stadio": (m.get("stadium") or {}).get("name", ""),
                          "arbitro": (m.get("referee") or {}).get("name", ""),
                          "allenatori": {m["home_team"]["home_team_name"]: managers(m["home_team"]),
                                         m["away_team"]["away_team_name"]: managers(m["away_team"])}})
    return sorted(metas, key=lambda x: x["n"])


def managers(team):
    return ", ".join(x.get("nickname") or x["name"] for x in team.get("managers") or [])


def write(path, rows):
    if not rows:
        return
    cols = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", help="numeri di partita da partite.csv, es. 1-10,831")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=str(HERE / "output"))
    args = ap.parse_args()

    metas = load_matches(parse_n(args.n) if args.n else None)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    teams, players, shots, edges, kevs = [], [], [], [], []
    errors = []
    with Pool(args.workers) as pool:
        for i, (meta, res) in enumerate(pool.imap_unordered(_safe, metas, chunksize=4), 1):
            if isinstance(res, str):
                errors.append(f"{meta['n']} ({meta['match_id']}): {res}")
            elif res:
                teams += res[0]; players += res[1]; shots += res[2]; edges += res[3]; kevs += res[4]
            if i % 100 == 0 or i == len(metas):
                print(f"{i}/{len(metas)} partite", file=sys.stderr, flush=True)
    key = lambda r: (r["n"], r["squadra"])
    write(out / "squadre.csv", sorted(teams, key=key))
    write(out / "giocatori.csv", sorted(players, key=lambda r: (r["n"], r["squadra"], -r["minuti"])))
    write(out / "tiri.csv", sorted(shots, key=lambda r: (r["n"], r["periodo"], r["minuto"], r["secondo"])))
    write(out / "rete_passaggi.csv", sorted(edges, key=lambda r: (r["n"], r["squadra"], -r["passaggi"])))
    write(out / "eventi_chiave.csv", sorted(kevs, key=lambda r: (r["n"], r["periodo"], r["minuto"], r["secondo"])))
    print(f"Fatto: {len(teams)//2} partite, {len(players)} righe giocatori, {len(shots)} tiri. Errori: {len(errors)}")
    for e in errors:
        print("  ", e)


def _safe(meta):
    try:
        return meta, analyse(meta)
    except Exception as exc:  # una partita con dati anomali non deve fermare tutto
        return meta, f"{type(exc).__name__}: {exc}"


if __name__ == "__main__":
    main()
