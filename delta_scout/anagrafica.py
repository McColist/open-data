"""Delta Scout - anagrafica giocatori da Reep (registro identità del calcio, licenza CC0).

Collega i giocatori StatsBomb ai record Reep per nome + nazionalità + data di nascita plausibile e aggiunge:
data di nascita, altezza, ruolo, link Transfermarkt / FBref / Wikidata.

Uso:
    python delta_scout/anagrafica.py                      # scarica people.csv di Reep (circa 65 MB) se manca
    python delta_scout/anagrafica.py --reep percorso/people.csv
Scrive delta_scout/output/anagrafica_giocatori.csv (usato da report.py).
"""
import argparse
import csv
import re
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REEP_URL = "https://raw.githubusercontent.com/withqwerty/reep/main/data/people.csv"

NAT_ALIAS = {
    "united states of america": "united states", "cote d'ivoire": "ivory coast", "venezuela (bolivarian republic)": "venezuela",
    "congo, (kinshasa)": "dr congo", "democratic republic of the congo": "dr congo", "korea (south)": "south korea",
    "korea, south": "south korea", "macedonia, republic of": "north macedonia", "congo (brazzaville)": "republic of the congo",
    "congo": "republic of the congo", "iran, islamic republic of": "iran", "tanzania, united republic of": "tanzania",
    "lao pdr": "laos", "gambia": "the gambia", "czechia": "czech republic", "turkiye": "turkey",
    "guadeloupe": "france", "martinique": "france", "french guiana": "france", "reunion": "france",
    "england": "united kingdom", "scotland": "united kingdom", "wales": "united kingdom", "northern ireland": "united kingdom",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = s.replace("\xa0", " ")
    return re.sub(r"[^a-z0-9' ]+", " ", s).strip()


def nat(s):
    n = re.sub(r"\s+", " ", norm(s))
    return NAT_ALIAS.get(n, n)


def name_keys(full, nick):
    keys = {norm(x) for x in (full, nick) if x}
    toks = norm(full).split()
    if len(toks) >= 3:  # nomi ispanici/portoghesi: nome + primo cognome (es. Lionel Andrés Messi Cuccittini)
        keys.add(f"{toks[0]} {toks[-2]}")
        keys.add(f"{toks[0]} {toks[-1]}")
    return {re.sub(r"\s+", " ", k) for k in keys if k}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reep", default=str(HERE / "reep_people.csv"))
    args = ap.parse_args()
    reep = Path(args.reep)
    if not reep.exists():
        print("Scarico l'anagrafica Reep…", flush=True)
        urllib.request.urlretrieve(REEP_URL, reep)

    index = defaultdict(list)
    with open(reep, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["type"] != "player":
                continue
            r["_keys"] = sum(1 for k, v in r.items() if k.startswith("key_") and v)
            for n in {norm(r["name"]), norm(r["full_name"])}:
                if n:
                    index[re.sub(r"\s+", " ", n)].append(r)

    players = {}
    with open(HERE / "output" / "giocatori.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            p = players.setdefault(r["player_id"], {"player_id": r["player_id"], "giocatore": r["giocatore"],
                                                    "soprannome": r["soprannome"], "nazionalita": r["nazionalita"],
                                                    "prima": r["data"], "ultima": r["data"]})
            p["prima"] = min(p["prima"], r["data"])
            p["ultima"] = max(p["ultima"], r["data"])

    rows, found = [], 0
    for p in players.values():
        exact = {norm(x) for x in (p["giocatore"], p["soprannome"]) if x}
        cands = {}
        for k in name_keys(p["giocatore"], p["soprannome"]):
            for r in index.get(k, ()):
                cands[r["reep_id"]] = (r, k in exact)
        y0, y1 = int(p["prima"][:4]), int(p["ultima"][:4])
        scored = []
        for r, is_exact in cands.values():
            dob = r["date_of_birth"] if re.match(r"\d{4}-\d\d-\d\d$", r["date_of_birth"] or "") else ""
            r["date_of_birth"] = dob
            if dob and not (y1 - 46 <= int(dob[:4]) <= y0 - 14):
                continue  # età incompatibile con le partite giocate
            same_nat = bool(r["nationality"]) and nat(r["nationality"]) == nat(p["nazionalita"])
            if r["nationality"] and not same_nat:
                continue
            if not is_exact and not same_nat:
                continue  # i nomi abbreviati richiedono la stessa nazionalità
            scored.append((same_nat + is_exact + bool(dob), r["_keys"], r))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        best = None
        if scored and (len(scored) == 1 or scored[0][:2] != scored[1][:2]):
            if len(scored) == 1 or scored[0][0] > scored[1][0] or scored[0][1] >= 2 * max(1, scored[1][1]):
                best = scored[0]
        row = {k: p[k] for k in ("player_id", "giocatore", "soprannome", "nazionalita")}
        if best:
            found += 1
            r = best[2]
            row.update({
                "reep_id": r["reep_id"], "data_nascita": r["date_of_birth"], "altezza_cm": r["height_cm"].split(".")[0],
                "ruolo": r["position_detail"] or r["position"],
                "transfermarkt": f'https://www.transfermarkt.com/x/profil/spieler/{r["key_transfermarkt"]}' if r["key_transfermarkt"] else "",
                "fbref": f'https://fbref.com/en/players/{r["key_fbref"]}/' if r["key_fbref"] else "",
                "wikidata": f'https://www.wikidata.org/wiki/{r["key_wikidata"]}' if r["key_wikidata"] else "",
                "affidabilita": "alta" if best[0] >= 3 else "media"})
        rows.append(row)
    cols = ["player_id", "giocatore", "soprannome", "nazionalita", "reep_id", "data_nascita", "altezza_cm", "ruolo",
            "transfermarkt", "fbref", "wikidata", "affidabilita"]
    with open(HERE / "output" / "anagrafica_giocatori.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: int(r["player_id"])))
    print(f"Collegati {found} giocatori su {len(rows)} ({100 * found / len(rows):.0f}%) → output/anagrafica_giocatori.csv")


if __name__ == "__main__":
    main()
