"""Delta Scout - voto partita 0-10 per ogni giocatore ("indice Delta Scout").

Metodo: per ogni reparto (portiere, difensore, centrocampista, attaccante) ogni statistica della partita viene
standardizzata (z-score) rispetto a tutte le prestazioni dello stesso reparto nel dataset; il voto è la somma pesata
degli z-score, riportata su una scala centrata su 6,6 (circa ±0,75 per deviazione standard, compressa agli estremi così che il 10
resti irraggiungibile in pratica): quasi tutti i voti tra 5,5 e 8, sopra 9 solo prestazioni eccezionali. Piccolo correttivo per il risultato (±0,2).
Servono almeno 20 minuti giocati, altrimenti "s.v.".
È una formula di Delta Scout, trasparente ma non una verità: i pesi sono in WEIGHTS.

Uso:
    python delta_scout/voti.py
Scrive delta_scout/output/voti.csv (usato da report.py e classifiche).
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
MIN_MINUTES = 20

WEIGHTS = {
    "Attaccante": {"gol": 1.2, "assist": 0.8, "xg": 0.6, "xa": 0.5, "xt": 0.5, "sca": 0.4, "dribbling_riusciti": 0.3,
                   "tocchi_in_area": 0.2, "passaggi_chiave": 0.3, "pressioni": 0.15, "recuperi": 0.1,
                   "palle_perse": -0.25, "falli_commessi": -0.05, "gialli": -0.2, "rossi": -1.0},
    "Centrocampista": {"gol": 1.0, "assist": 0.7, "xg": 0.3, "xa": 0.4, "xt": 0.6, "passaggi_progressivi": 0.5,
                       "passaggi_chiave": 0.3, "sca": 0.3, "passaggi_riusciti": 0.3, "passaggi_sbagliati": -0.2,
                       "conduzioni_progressive": 0.3, "azioni_difensive": 0.5, "pressioni": 0.2, "aerei_vinti": 0.1,
                       "palle_perse": -0.3, "saltato_da_avversario": -0.2, "gialli": -0.2, "rossi": -1.0},
    "Difensore": {"gol": 0.8, "assist": 0.6, "xt": 0.3, "passaggi_progressivi": 0.3, "passaggi_riusciti": 0.3,
                  "azioni_difensive": 0.6, "respinte": 0.3, "blocchi": 0.3, "aerei_vinti": 0.4, "aerei_persi": -0.2,
                  "saltato_da_avversario": -0.4, "palle_perse": -0.3, "falli_commessi": -0.1, "gialli": -0.2,
                  "rossi": -1.0, "xg_subiti_squadra": -0.3, "gol_subiti_squadra": -0.3},
    "Portiere": {"parate": 0.8, "gol_evitati": 0.9, "uscite": 0.2, "prese_alte": 0.2, "passaggi_riusciti": 0.2,
                 "palle_perse": -0.3, "rossi": -1.0},
}


def reparto(role):
    if role == "Goalkeeper":
        return "Portiere"
    if "Back" in role:
        return "Difensore"
    if "Midfield" in role:
        return "Centrocampista"
    return "Attaccante"


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def main():
    teams = {}
    with open(OUT / "squadre.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            teams[(r["n"], r["squadra"])] = r
    rows = []
    with open(OUT / "giocatori.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            mins = num(r["minuti"])
            t = teams.get((r["n"], r["squadra"]), {})
            share = min(mins / 90, 1.0)
            feats = {k: num(r.get(k)) for k in ("gol", "assist", "xg", "xa", "xt", "sca", "dribbling_riusciti", "tocchi_in_area",
                                                  "passaggi_chiave", "pressioni", "recuperi", "palle_perse", "falli_commessi",
                                                  "gialli", "rossi", "passaggi_progressivi", "passaggi_riusciti",
                                                  "conduzioni_progressive", "aerei_vinti", "aerei_persi", "saltato_da_avversario",
                                                  "respinte", "blocchi", "parate", "uscite", "prese_alte")}
            feats["passaggi_sbagliati"] = num(r["passaggi"]) - num(r["passaggi_riusciti"])
            feats["azioni_difensive"] = num(r["contrasti_vinti"]) + num(r["intercetti"]) + num(r["recuperi"])
            feats["xg_subiti_squadra"] = num(t.get("xg_subiti")) * share
            feats["gol_subiti_squadra"] = num(t.get("gol_subiti")) * share
            feats["gol_evitati"] = (num(t.get("xg_subiti")) - num(t.get("gol_subiti"))) * share
            esito = t.get("esito", "N")
            rows.append({"n": r["n"], "player_id": r["player_id"], "squadra": r["squadra"], "minuti": mins,
                         "reparto": reparto(r["ruolo"]), "esito": esito, "f": feats,
                         "g": ("F" if "(F)" in r["competizione"] else "M", reparto(r["ruolo"]))})

    # media e deviazione di ogni statistica per reparto (solo prestazioni con minuti sufficienti)
    stats = {}  # calcio maschile e femminile hanno medie diverse: confronto separato
    for grp in {x["g"] for x in rows}:
        w = WEIGHTS[grp[1]]
        pool = [x["f"] for x in rows if x["g"] == grp and x["minuti"] >= MIN_MINUTES]
        stats[grp] = {}
        for k in w:
            vals = [p[k] for p in pool]
            m = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)) or 1.0
            stats[grp][k] = (m, sd)
    raw = defaultdict(list)
    for x in rows:
        if x["minuti"] < MIN_MINUTES:
            x["raw"] = None
            continue
        st, w = stats[x["g"]], WEIGHTS[x["reparto"]]
        x["raw"] = sum(w[k] * (x["f"][k] - st[k][0]) / st[k][1] for k in w)
        raw[x["g"]].append(x["raw"])
    scale = {rep: (sum(v) / len(v), math.sqrt(sum((a - sum(v) / len(v)) ** 2 for a in v) / len(v))) for rep, v in raw.items()}

    out = []
    for x in rows:
        if x["raw"] is None:
            voto = ""
        else:
            m, sd = scale[x["g"]]
            z = (x["raw"] - m) / sd
            # scala morbida: ±0,75 per deviazione vicino alla media, poi compressa verso 10 e verso 3 (tanh)
            top = 3.4 if z > 0 else 3.6
            v = 6.6 + math.copysign(top * math.tanh(0.75 * abs(z) / top), z) + {"V": 0.2, "P": -0.2}.get(x["esito"], 0.0)
            voto = round(min(max(v, 3.0), 10.0), 1)
        out.append({"n": x["n"], "player_id": x["player_id"], "squadra": x["squadra"], "reparto": x["reparto"], "voto": voto})
    with open(OUT / "voti.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    vs = [o["voto"] for o in out if o["voto"] != ""]
    print(f"{len(vs)} voti (su {len(out)} prestazioni), media {sum(vs) / len(vs):.2f}, "
          f"sopra 8: {100 * sum(v >= 8 for v in vs) / len(vs):.1f}%, sotto 5.5: {100 * sum(v < 5.5 for v in vs) / len(vs):.1f}%")


if __name__ == "__main__":
    main()
