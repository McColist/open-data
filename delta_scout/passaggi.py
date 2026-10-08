"""Delta Scout - tutti i passaggi di ogni partita, compressi, per le mappe individuali dei report
(passing map e palloni ricevuti di ogni giocatore).

Uso:
    python delta_scout/passaggi.py
Scrive delta_scout/output/passaggi/<n>.json.gz, uno per partita (letti da report.py).
Formato: {"p": [[passatore_id, ricevente_id|0, x, y, fine_x, fine_y, esito, minuto, flag], ...]}
esito: 1 riuscito, 0 sbagliato. flag (somma): 1 chiave, 2 assist, 4 progressivo, 8 cross, 16 in area, 32 palla inattiva.
"""
import csv
import gzip
import json
from multiprocessing import Pool
from pathlib import Path

from analizza import DATA, HERE, SET_PIECE_PASSES, in_box, is_progressive

OUT = HERE / "output" / "passaggi"


def passes(meta):
    n, mid = meta
    try:
        with open(DATA / "events" / f"{mid}.json", encoding="utf-8") as fh:
            events = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return 0
    rows = []
    for e in events:
        if e["type"]["name"] != "Pass" or e["period"] > 4 or not e.get("player"):
            continue
        ps = e["pass"]
        a, b = e["location"], ps.get("end_location", e["location"])
        ok = "outcome" not in ps
        ptype = ps.get("type", {}).get("name")
        flag = (1 if ps.get("shot_assist") or ps.get("goal_assist") else 0) + (2 if ps.get("goal_assist") else 0) \
            + (4 if ok and ptype not in SET_PIECE_PASSES and is_progressive(a, b) else 0) + (8 if ps.get("cross") else 0) \
            + (16 if ok and in_box(b) and not in_box(a) else 0) + (32 if ptype in SET_PIECE_PASSES else 0)
        rows.append([e["player"]["id"], ps.get("recipient", {}).get("id", 0), round(a[0], 1), round(a[1], 1),
                     round(b[0], 1), round(b[1], 1), int(ok), e["minute"], flag])
    with gzip.open(OUT / f"{n}.json.gz", "wt", encoding="utf-8") as fh:
        json.dump({"p": rows}, fh, separators=(",", ":"))
    return len(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(HERE / "partite.csv", encoding="utf-8") as fh:
        metas = [(int(r["n"]), r["match_id"]) for r in csv.DictReader(fh)]
    tot = 0
    with Pool(4) as pool:
        for i, k in enumerate(pool.imap(passes, metas, chunksize=8), 1):
            tot += k
            if i % 500 == 0:
                print(f"{i}/{len(metas)} partite", flush=True)
    print(f"{tot} passaggi salvati in {OUT}")


if __name__ == "__main__":
    main()
