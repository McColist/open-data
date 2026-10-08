"""Delta Scout - conduzioni palla significative per la carry map dei report.

Salva solo le conduzioni progressive (avvicinano la palla alla porta di almeno il 25% e di almeno 5 yard)
o che entrano nel terzo finale / in area: sono quelle che contano per lo scouting e tengono il file leggero.

Uso:
    python delta_scout/conduzioni.py
Scrive delta_scout/output/conduzioni.csv (usato da report.py).
"""
import csv
import json
from multiprocessing import Pool
from pathlib import Path

from analizza import DATA, HERE, in_box, is_progressive, xt_gain


def carries(meta):
    n, mid = meta
    try:
        with open(DATA / "events" / f"{mid}.json", encoding="utf-8") as fh:
            events = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    out = []
    for e in events:
        if e["type"]["name"] != "Carry" or e["period"] > 4:
            continue
        a, b = e["location"], e["carry"]["end_location"]
        prog = is_progressive(a, b, 5)
        box = in_box(b) and not in_box(a)
        third = b[0] >= 80 and a[0] < 80
        if not (prog or box or third):
            continue
        out.append({"n": n, "match_id": mid, "squadra": e["team"]["name"], "player_id": e["player"]["id"],
                    "giocatore": e["player"]["name"], "periodo": e["period"], "minuto": e["minute"], "secondo": e["second"],
                    "x": a[0], "y": a[1], "fine_x": b[0], "fine_y": b[1],
                    "metri": round(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 * 0.9144, 1),
                    "xt": round(xt_gain(a, b), 4), "progressiva": int(prog), "in_area": int(box), "terzo_finale": int(third),
                    "sotto_pressione": int(bool(e.get("under_pressure")))})
    return out


def main():
    with open(HERE / "partite.csv", encoding="utf-8") as fh:
        metas = [(int(r["n"]), r["match_id"]) for r in csv.DictReader(fh)]
    rows = []
    with Pool(4) as pool:
        for i, res in enumerate(pool.imap(carries, metas, chunksize=8), 1):
            rows += res
            if i % 500 == 0:
                print(f"{i}/{len(metas)} partite", flush=True)
    with open(HERE / "output" / "conduzioni.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} conduzioni in output/conduzioni.csv")


if __name__ == "__main__":
    main()
