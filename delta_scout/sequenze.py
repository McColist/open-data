"""Delta Scout - sequenze di gioco per carry map e mappa del pressing.

Per ogni partita salva:
  - le conduzioni significative (progressive, nel terzo finale o in area) con il loro esito nei 10 secondi successivi:
    gol, tiro, fallo subito, palla persa o possesso mantenuto;
  - i recuperi palla (recuperi, intercetti vinti, contrasti vinti) con l'esito nei 10 secondi successivi.

Uso:
    python delta_scout/sequenze.py
Scrive delta_scout/output/conduzioni.csv e delta_scout/output/recuperi.csv (usati da report.py).
"""
import csv
import json
from multiprocessing import Pool

from analizza import DATA, HERE, TACKLE_WON, in_box, is_progressive, ts, xt_gain

WINDOW = 10.0  # secondi


def outcome(events, i, team, t0):
    """Cosa succede entro WINDOW secondi dall'istante t0 (evento i escluso)."""
    period = events[i]["period"]
    for e in events[i + 1:]:
        if e["period"] != period or ts(e["timestamp"]) - t0 > WINDOW:
            return "possesso mantenuto"
        typ = e["type"]["name"]
        if e["team"]["name"] == team:
            if typ == "Shot":
                return "gol" if e["shot"]["outcome"]["name"] == "Goal" else "tiro"
            if typ == "Foul Won":
                return "fallo subito"
        if e.get("possession_team", {}).get("name") not in (None, team) and typ not in ("Pressure", "Ball Receipt*"):
            return "palla persa"
    return "possesso mantenuto"


def analyse(meta):
    n, mid = meta
    try:
        with open(DATA / "events" / f"{mid}.json", encoding="utf-8") as fh:
            events = [e for e in json.load(fh) if e["period"] <= 4]
    except (OSError, json.JSONDecodeError):
        return [], []
    carries, regains = [], []
    for i, e in enumerate(events):
        typ = e["type"]["name"]
        team = e["team"]["name"]
        pl = e.get("player")
        if not pl or not e.get("location"):
            continue
        base = {"n": n, "match_id": mid, "squadra": team, "player_id": pl["id"], "giocatore": pl["name"],
                "periodo": e["period"], "minuto": e["minute"], "secondo": e["second"]}
        if typ == "Carry":
            a, b = e["location"], e["carry"]["end_location"]
            prog, box, third = is_progressive(a, b, 5), in_box(b) and not in_box(a), b[0] >= 80 and a[0] < 80
            if prog or box or third:
                carries.append({**base, "x": a[0], "y": a[1], "fine_x": b[0], "fine_y": b[1],
                                "metri": round(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 * 0.9144, 1),
                                "xt": round(xt_gain(a, b), 4), "progressiva": int(prog), "in_area": int(box),
                                "terzo_finale": int(third), "sotto_pressione": int(bool(e.get("under_pressure"))),
                                "esito": outcome(events, i, team, ts(e["timestamp"]) + (e.get("duration") or 0))})
            continue
        kind = None
        if typ == "Ball Recovery" and not e.get("ball_recovery", {}).get("recovery_failure"):
            kind = "recupero"
        elif typ == "Interception" and e["interception"]["outcome"]["name"] in ("Won", "Success In Play", "Success Out"):
            kind = "intercetto"
        elif typ == "Duel" and e["duel"].get("type", {}).get("name") == "Tackle" and \
                e["duel"].get("outcome", {}).get("name") in TACKLE_WON:
            kind = "contrasto"
        if kind:
            res = outcome(events, i, team, ts(e["timestamp"]))
            # file compatto (sono ~550.000 righe): il nome del giocatore si ricava da giocatori.csv con player_id
            regains.append({"n": n, "squadra": team, "player_id": pl["id"], "periodo": e["period"], "minuto": e["minute"],
                            "x": round(e["location"][0], 1), "y": round(e["location"][1], 1), "tipo": kind, "esito": res})
    return carries, regains


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    with open(HERE / "partite.csv", encoding="utf-8") as fh:
        metas = [(int(r["n"]), r["match_id"]) for r in csv.DictReader(fh)]
    carries, regains = [], []
    with Pool(4) as pool:
        for i, (c, r) in enumerate(pool.imap(analyse, metas, chunksize=8), 1):
            carries += c
            regains += r
            if i % 500 == 0:
                print(f"{i}/{len(metas)} partite", flush=True)
    write(HERE / "output" / "conduzioni.csv", carries)
    write(HERE / "output" / "recuperi.csv", regains)
    print(f"{len(carries)} conduzioni, {len(regains)} recuperi")


if __name__ == "__main__":
    main()
