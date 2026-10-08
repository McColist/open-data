"""Genera la lista numerata di tutte le partite disponibili (delta_scout/partite.csv e partite.md)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent


def main():
    comps = json.loads((DATA / "competitions.json").read_text(encoding="utf-8"))
    has_360 = {p.stem for p in (DATA / "three-sixty").glob("*.json")}
    rows = []
    for c in comps:
        f = DATA / "matches" / str(c["competition_id"]) / f"{c['season_id']}.json"
        if not f.exists():
            continue
        for m in json.loads(f.read_text(encoding="utf-8")):
            rows.append({
                "competizione": m["competition"]["competition_name"]
                + (" (F)" if c["competition_gender"] == "female" else ""),
                "stagione": m["season"]["season_name"],
                "data": m["match_date"],
                "casa": m["home_team"]["home_team_name"],
                "risultato": f"{m['home_score']}-{m['away_score']}",
                "trasferta": m["away_team"]["away_team_name"],
                "fase": (m.get("competition_stage") or {}).get("name", ""),
                "dati_360": "si" if str(m["match_id"]) in has_360 else "",
                "match_id": m["match_id"],
            })
    rows.sort(key=lambda r: (r["competizione"], r["stagione"], r["data"], r["casa"]))
    for i, r in enumerate(rows, 1):
        r["n"] = i

    cols = ["n", "competizione", "stagione", "data", "casa", "risultato",
            "trasferta", "fase", "dati_360", "match_id"]
    with open(OUT / "partite.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    lines = ["# Delta Scout – Lista partite", "",
             f"{len(rows)} partite. `360` = dati StatsBomb 360 disponibili.", ""]
    cur = None
    for r in rows:
        key = (r["competizione"], r["stagione"])
        if key != cur:
            cur = key
            lines += ["", f"## {r['competizione']} – {r['stagione']}", ""]
        tag = " `360`" if r["dati_360"] else ""
        fase = f" _({r['fase']})_" if r["fase"] and r["fase"] != "Regular Season" else ""
        lines.append(f"{r['n']}. {r['data']} – {r['casa']} **{r['risultato']}** {r['trasferta']}{fase}{tag}")
    (OUT / "partite.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} partite scritte")


if __name__ == "__main__":
    main()
