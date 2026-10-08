"""Delta Scout - stima della griglia Expected Threat (xT) dai dati StatsBomb.

Metodo di Karun Singh (2018): il campo è diviso in 16x12 zone; per ogni zona si stimano la probabilità di
tirare, di segnare tirando e di muovere la palla verso le altre zone; xT è il valore di "minaccia" di
ogni zona, risolto per iterazione. Il valore xT di un passaggio o di una conduzione riuscita è
xT(arrivo) - xT(partenza).

Uso:
    python delta_scout/xt.py                 # tutte le partite
    python delta_scout/xt.py --ogni 3        # una partita ogni 3 (più veloce, stima comunque stabile)
Scrive delta_scout/xt_griglia.json, letto da analizza.py.
"""
import argparse
import json
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
NX, NY = 16, 12


def cell(p):
    x = min(int(p[0] / 120 * NX), NX - 1)
    y = min(int(p[1] / 80 * NY), NY - 1)
    return y * NX + x


def count(path):
    n = NX * NY
    shots, goals, moves = [0] * n, [0] * n, [0] * n
    trans = {}
    try:
        with open(path, encoding="utf-8") as fh:
            events = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    for e in events:
        if e["period"] > 4 or not e.get("location"):
            continue
        typ = e["type"]["name"]
        z = cell(e["location"])
        if typ == "Shot":
            if e["shot"].get("type", {}).get("name") == "Penalty":
                continue
            shots[z] += 1
            goals[z] += e["shot"]["outcome"]["name"] == "Goal"
        elif typ in ("Pass", "Carry"):
            moves[z] += 1
            ok = typ == "Carry" or "outcome" not in e["pass"]
            end = e["carry"]["end_location"] if typ == "Carry" else e["pass"].get("end_location")
            if ok and end:
                k = (z, cell(end))
                trans[k] = trans.get(k, 0) + 1
    return shots, goals, moves, trans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ogni", type=int, default=1, help="usa una partita ogni N")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    files = sorted((DATA / "events").glob("*.json"))[::args.ogni]
    n = NX * NY
    S, G, M = [0] * n, [0] * n, [0] * n
    T = {}
    with Pool(args.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(count, files, chunksize=8), 1):
            if res:
                for acc, v in zip((S, G, M), res[:3]):
                    for z in range(n):
                        acc[z] += v[z]
                for k, c in res[3].items():
                    T[k] = T.get(k, 0) + c
            if i % 200 == 0:
                print(f"{i}/{len(files)} partite", flush=True)

    s = [S[z] / (S[z] + M[z]) if S[z] + M[z] else 0 for z in range(n)]
    m = [M[z] / (S[z] + M[z]) if S[z] + M[z] else 0 for z in range(n)]
    g = [G[z] / S[z] if S[z] else 0 for z in range(n)]
    out = {}
    for (a, b), c in T.items():
        out.setdefault(a, []).append((b, c / M[a]))
    xt = [0.0] * n
    for it in range(100):
        new = [s[z] * g[z] + m[z] * sum(p * xt[b] for b, p in out.get(z, ())) for z in range(n)]
        diff = max(abs(a - b) for a, b in zip(new, xt))
        xt = new
        if diff < 1e-7:
            break
    grid = [[round(xt[y * NX + x], 6) for x in range(NX)] for y in range(NY)]
    (HERE / "xt_griglia.json").write_text(json.dumps({
        "metodo": "Karun Singh 2018, griglia 16x12 su campo StatsBomb 120x80; riga = y, colonna = x",
        "partite": len(files), "iterazioni": it + 1, "griglia": grid}, indent=1), encoding="utf-8")
    print(f"Griglia xT da {len(files)} partite, {it + 1} iterazioni. Max xT {max(xt):.3f}")


if __name__ == "__main__":
    main()
