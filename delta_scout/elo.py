"""Delta Scout - rating Elo delle squadre, calcolato in ordine cronologico sui risultati del dataset.

Formula tipo World Football Elo: K=30, moltiplicatore per scarto gol, +60 al fattore campo
(0 nei tornei a sede neutra). Ogni squadra parte da 1500.
Attenzione: il dataset copre alcune squadre in modo parziale (es. solo le partite del Barcellona in Liga),
quindi il rating è affidabile solo per squadre con molte partite alle spalle (colonna partite_storia).

Uso:
    python delta_scout/elo.py
Scrive delta_scout/output/elo.csv (usato da report.py).
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
K, HOME = 30, 60
NEUTRAL = ("World Cup", "Euro", "Copa America", "African Cup", "Champions League", "Europa League", "Copa del Rey")


def main():
    with open(HERE / "output" / "squadre.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    matches = {}
    for r in rows:
        m = matches.setdefault(int(r["n"]), {"data": r["data"], "comp": r["competizione"], "fase": r.get("fase", "")})
        m[r["casa_trasferta"]] = r
    rating, played = {}, {}
    out = []
    for n, m in sorted(matches.items(), key=lambda x: (x[1]["data"], x[0])):
        if "casa" not in m or "trasferta" not in m:
            continue
        h, a = m["casa"], m["trasferta"]
        th, ta = h["squadra"], a["squadra"]
        rh, ra = rating.get(th, 1500.0), rating.get(ta, 1500.0)
        adv = 0 if any(x in m["comp"] for x in NEUTRAL) else HOME
        we = 1 / (10 ** (-(rh + adv - ra) / 400) + 1)
        gh, ga = int(h["gol"]), int(a["gol"])
        w = 1.0 if gh > ga else 0.5 if gh == ga else 0.0
        gd = abs(gh - ga)
        mult = 1 if gd <= 1 else 1.5 if gd == 2 else (11 + gd) / 8
        delta = K * mult * (w - we)
        for t, r_pre, exp, d in ((th, rh, we, delta), (ta, ra, 1 - we, -delta)):
            out.append({"n": n, "data": m["data"], "squadra": t, "elo_pre": round(r_pre), "elo_post": round(r_pre + d),
                        "prob_vittoria_attesa": round(100 * exp, 1), "partite_storia": played.get(t, 0)})
        rating[th], rating[ta] = rh + delta, ra - delta
        played[th] = played.get(th, 0) + 1
        played[ta] = played.get(ta, 0) + 1
    with open(HERE / "output" / "elo.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(sorted(out, key=lambda r: (r["n"], r["squadra"])))
    top = sorted(rating.items(), key=lambda x: -x[1])[:10]
    print("Elo calcolato per", len(rating), "squadre. Top 10 finale:")
    for t, r in top:
        print(f"  {r:6.0f}  {t}  ({played[t]} partite)")


if __name__ == "__main__":
    main()
