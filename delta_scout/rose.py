"""Delta Scout - rose complete per partita (titolari, subentrati, riserve non utilizzate) dai lineup StatsBomb.

Uso:
    python delta_scout/rose.py
Scrive delta_scout/output/rose.csv (usato da report.py per formazioni e panchine).
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
CARDS = {"Yellow Card": "Giallo", "Second Yellow": "Secondo giallo", "Red Card": "Rosso"}


def main():
    with open(HERE / "partite.csv", encoding="utf-8") as fh:
        index = {r["match_id"]: r for r in csv.DictReader(fh)}
    rows = []
    for mid, m in index.items():
        f = DATA / "lineups" / f"{mid}.json"
        if not f.exists():
            continue
        for t in json.loads(f.read_text(encoding="utf-8")):
            for p in t["lineup"]:
                pos = [x for x in p.get("positions", []) if x.get("from_period", 1) <= 4]
                if not pos:
                    stato = "non entrato"
                elif pos[0].get("start_reason") == "Starting XI":
                    stato = "titolare"
                else:
                    stato = "subentrato"
                ruoli = []
                for x in pos:
                    if not ruoli or ruoli[-1] != x["position"]:
                        ruoli.append(x["position"])
                rows.append({
                    "n": int(m["n"]), "match_id": mid, "squadra": t["team_name"], "player_id": p["player_id"],
                    "giocatore": p["player_name"], "soprannome": p.get("player_nickname") or "",
                    "maglia": p.get("jersey_number") or "", "nazionalita": (p.get("country") or {}).get("name", ""),
                    "stato": stato, "ruolo_iniziale": ruoli[0] if ruoli else "", "ruoli": " → ".join(ruoli),
                    "cartellini": ", ".join(CARDS.get(c["card_type"], c["card_type"])  # minuti: vedi eventi_chiave.csv
                                            for c in p.get("cards", []) if c.get("period", 1) <= 4)})
    # alcune partite (es. Premier League 2003/04) hanno la maglia 0 nei dati sorgente:
    # si usa il numero più frequente dello stesso giocatore nella stessa squadra e stagione, altrimenti in qualsiasi stagione
    stagione = {m["n"]: m["stagione"] for m in index.values()}
    by_season, by_team = defaultdict(Counter), defaultdict(Counter)
    for r in rows:
        if r["maglia"]:
            by_season[(r["squadra"], r["player_id"], stagione[str(r["n"])])][r["maglia"]] += 1
            by_team[(r["squadra"], r["player_id"])][r["maglia"]] += 1
    fixed = 0
    for r in rows:
        r["maglia_stimata"] = 0
        if not r["maglia"]:
            c = by_season.get((r["squadra"], r["player_id"], stagione[str(r["n"])])) or by_team.get((r["squadra"], r["player_id"]))
            r["maglia"] = c.most_common(1)[0][0] if c else ""
            r["maglia_stimata"] = 1
            fixed += bool(r["maglia"])
    print(f"Maglie mancanti recuperate da altre partite: {fixed}")
    order = {"titolare": 0, "subentrato": 1, "non entrato": 2}
    rows.sort(key=lambda r: (r["n"], r["squadra"], order[r["stato"]], int(r["maglia"] or 99)))
    with open(HERE / "output" / "rose.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} righe in output/rose.csv")


if __name__ == "__main__":
    main()
