"""Delta Scout - classifiche di tutti i tempi per ruolo, su tutte le partite del dataset.

Uso:
    python delta_scout/classifiche.py
Scrive:
    delta_scout/output/carriere_giocatori.csv  totali e valori per 90' di ogni giocatore (tutte le partite)
    delta_scout/classifiche.html               pagina con classifiche filtrabili per ruolo, sesso, minuti, metrica
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"

ROLE = {
    "Goalkeeper": "Portiere",
    "Center Back": "Difensore centrale", "Left Center Back": "Difensore centrale", "Right Center Back": "Difensore centrale",
    "Left Back": "Terzino", "Right Back": "Terzino", "Left Wing Back": "Terzino", "Right Wing Back": "Terzino",
    "Center Defensive Midfield": "Mediano", "Left Defensive Midfield": "Mediano", "Right Defensive Midfield": "Mediano",
    "Center Midfield": "Centrocampista", "Left Center Midfield": "Centrocampista", "Right Center Midfield": "Centrocampista",
    "Left Midfield": "Centrocampista", "Right Midfield": "Centrocampista",
    "Center Attacking Midfield": "Trequartista / Ala", "Left Attacking Midfield": "Trequartista / Ala",
    "Right Attacking Midfield": "Trequartista / Ala", "Left Wing": "Trequartista / Ala", "Right Wing": "Trequartista / Ala",
    "Center Forward": "Attaccante", "Left Center Forward": "Attaccante", "Right Center Forward": "Attaccante",
    "Secondary Striker": "Attaccante",
}

SUM = ["gol", "gol_np", "assist", "xg", "npxg", "xa", "xt", "xg_chain", "sca", "gca", "tiri", "tiri_in_porta",
       "passaggi", "passaggi_riusciti", "passaggi_chiave", "passaggi_progressivi", "passaggi_terzo_finale", "passaggi_in_area",
       "passaggi_sotto_pressione", "passaggi_sotto_pressione_riusciti", "cross", "cross_riusciti", "lanci_lunghi",
       "lanci_lunghi_riusciti", "conduzioni_progressive", "conduzioni_in_area", "metri_progressivi", "dribbling",
       "dribbling_riusciti", "tocchi_in_area", "ricezioni_terzo_finale", "pressioni", "pressioni_alte", "contropressioni",
       "contrasti", "contrasti_vinti", "intercetti", "recuperi", "recuperi_alti", "respinte", "blocchi", "aerei_vinti",
       "aerei_persi", "palle_perse", "falli_commessi", "falli_subiti", "parate", "gol_subiti_portiere", "uscite"]

# (chiave, etichetta, tipo) - tipo: p90 = per 90 minuti, tot = totale, pct = percentuale, diff = differenza totale
METRICS = [
    ("gol_p90", "Gol", "p90"), ("npxg_p90", "xG senza rigori", "p90"), ("finalizzazione", "Gol − xG (senza rigori)", "diff"),
    ("conversione_pct", "Tiri trasformati in gol %", "pct"), ("xa_p90", "xA (assist attesi)", "p90"), ("assist_p90", "Assist", "p90"),
    ("xg_xa_p90", "xG + xA", "p90"), ("xt_p90", "xT – minaccia creata", "p90"), ("xg_chain_p90", "xG chain", "p90"),
    ("sca_p90", "Azioni che portano al tiro (SCA)", "p90"), ("passaggi_chiave_p90", "Passaggi chiave", "p90"),
    ("passaggi_progressivi_p90", "Passaggi progressivi", "p90"), ("passaggi_in_area_p90", "Passaggi in area", "p90"),
    ("conduzioni_progressive_p90", "Conduzioni progressive", "p90"), ("metri_progressivi_p90", "Metri progressivi", "p90"),
    ("dribbling_riusciti_p90", "Dribbling riusciti", "p90"), ("dribbling_pct", "Dribbling riusciti %", "pct"),
    ("tocchi_in_area_p90", "Tocchi in area", "p90"), ("precisione_passaggi_pct", "Precisione passaggi %", "pct"),
    ("passaggi_sotto_pressione_pct", "Passaggi riusciti sotto pressione %", "pct"),
    ("lanci_lunghi_pct", "Lanci lunghi riusciti %", "pct"), ("cross_riusciti_p90", "Cross riusciti", "p90"),
    ("pressioni_p90", "Pressioni", "p90"), ("pressioni_alte_p90", "Pressioni alte", "p90"),
    ("contrasti_vinti_p90", "Contrasti vinti", "p90"), ("intercetti_p90", "Intercetti", "p90"),
    ("recuperi_p90", "Recuperi", "p90"), ("recuperi_alti_p90", "Recuperi alti", "p90"),
    ("azioni_difensive_p90", "Azioni difensive (contrasti + intercetti + recuperi)", "p90"),
    ("aerei_vinti_p90", "Duelli aerei vinti", "p90"), ("aerei_pct", "Duelli aerei vinti %", "pct"),
    ("blocchi_p90", "Tiri / passaggi bloccati", "p90"), ("palle_perse_p90", "Palle perse (meno è meglio)", "p90"),
    ("parate_p90", "Parate", "p90"), ("parate_pct", "Parate % (tiri in porta subiti)", "pct"), ("uscite_p90", "Uscite", "p90"),
]
LOWER_BETTER = {"palle_perse_p90"}
PCT_MIN = {"conversione_pct": ("tiri", 30), "dribbling_pct": ("dribbling", 30), "precisione_passaggi_pct": ("passaggi", 300),
           "passaggi_sotto_pressione_pct": ("passaggi_sotto_pressione", 100), "lanci_lunghi_pct": ("lanci_lunghi", 50),
           "aerei_pct": ("_aerei", 30), "parate_pct": ("_tiri_porta_subiti", 30)}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def main():
    anag = {}
    if (OUT / "anagrafica_giocatori.csv").exists():
        with open(OUT / "anagrafica_giocatori.csv", encoding="utf-8") as fh:
            anag = {r["player_id"]: r for r in csv.DictReader(fh) if r["reep_id"]}

    P = defaultdict(lambda: defaultdict(float))
    info, roles, teams, comps, years = {}, defaultdict(Counter), defaultdict(Counter), defaultdict(Counter), defaultdict(list)
    with open(OUT / "giocatori.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pid = r["player_id"]
            mins = num(r["minuti"])
            p = P[pid]
            p["partite"] += 1
            p["minuti"] += mins
            for k in SUM:
                p[k] += num(r.get(k))
            info[pid] = {"giocatore": r["giocatore"], "soprannome": r["soprannome"], "nazionalita": r["nazionalita"],
                         "sesso": "F" if "(F)" in r["competizione"] else "M"}
            roles[pid][ROLE.get(r["ruolo"], "Altro")] += mins
            teams[pid][r["squadra"]] += mins
            comps[pid][f'{r["competizione"]} {r["stagione"]}'] += 1
            years[pid].append(r["data"][:4])

    rows = []
    for pid, p in P.items():
        m = p["minuti"]
        if m <= 0:
            continue
        r = {"player_id": pid, **info[pid], "ruolo": roles[pid].most_common(1)[0][0],
             "squadre": ", ".join(t for t, _ in teams[pid].most_common(3)),
             "periodo": f'{min(years[pid])}–{max(years[pid])}' if min(years[pid]) != max(years[pid]) else min(years[pid]),
             "competizioni": len(comps[pid]), "partite": int(p["partite"]), "minuti": round(m)}
        a = anag.get(pid, {})
        r.update({"data_nascita": a.get("data_nascita", ""), "altezza_cm": a.get("altezza_cm", ""),
                  "transfermarkt": a.get("transfermarkt", ""), "fbref": a.get("fbref", "")})
        for k in SUM:
            r[k] = round(p[k], 3) if not float(p[k]).is_integer() else int(p[k])
            r[f"{k}_p90"] = round(p[k] / m * 90, 3)
        r["xg_xa_p90"] = round((p["xg"] + p["xa"]) / m * 90, 3)
        r["azioni_difensive_p90"] = round((p["contrasti_vinti"] + p["intercetti"] + p["recuperi"]) / m * 90, 3)
        r["finalizzazione"] = round(p["gol_np"] - p["npxg"], 2)
        pct = lambda a_, b_: round(100 * a_ / b_, 1) if b_ else None
        r["conversione_pct"] = pct(p["gol"], p["tiri"])
        r["dribbling_pct"] = pct(p["dribbling_riusciti"], p["dribbling"])
        r["precisione_passaggi_pct"] = pct(p["passaggi_riusciti"], p["passaggi"])
        r["passaggi_sotto_pressione_pct"] = pct(p["passaggi_sotto_pressione_riusciti"], p["passaggi_sotto_pressione"])
        r["lanci_lunghi_pct"] = pct(p["lanci_lunghi_riusciti"], p["lanci_lunghi"])
        r["_aerei"] = p["aerei_vinti"] + p["aerei_persi"]
        r["aerei_pct"] = pct(p["aerei_vinti"], r["_aerei"])
        r["_tiri_porta_subiti"] = p["parate"] + p["gol_subiti_portiere"]
        r["parate_pct"] = pct(p["parate"], r["_tiri_porta_subiti"])
        rows.append(r)
    rows.sort(key=lambda r: -r["minuti"])

    cols = [c for c in rows[0] if not c.startswith("_")]
    with open(OUT / "carriere_giocatori.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    keep = ["player_id", "giocatore", "soprannome", "nazionalita", "sesso", "ruolo", "squadre", "periodo", "partite", "minuti",
            "data_nascita", "altezza_cm", "transfermarkt", "fbref", "gol", "assist", "xg", "tiri"]
    data = []
    for r in rows:
        if r["minuti"] < 450:
            continue
        d = [r[k] for k in keep] + [r.get(k) for k, _, _ in METRICS]
        # i valori percentuali con pochi tentativi non sono significativi
        for i, (k, _, t) in enumerate(METRICS):
            if k in PCT_MIN and num(r.get(PCT_MIN[k][0])) < PCT_MIN[k][1]:
                d[len(keep) + i] = None
        data.append(d)
    page = TEMPLATE.replace("__DATA__", json.dumps({"keep": keep, "metrics": METRICS, "lower": sorted(LOWER_BETTER),
                                                    "pctmin": {k: v[1] for k, v in PCT_MIN.items()}, "rows": data},
                                                   ensure_ascii=False, separators=(",", ":")))
    (HERE / "classifiche.html").write_text(page, encoding="utf-8")
    print(f"{len(rows)} giocatori in output/carriere_giocatori.csv; {len(data)} con almeno 450' in classifiche.html")


TEMPLATE = r"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Delta Scout – Classifiche</title><style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b1f24;--mute:#66707a;--line:#e3e6ea;--acc:#2a6fdb;--bar:#dbe6fa}
@media (prefers-color-scheme:dark){:root{--bg:#14171a;--card:#1d2125;--ink:#e8eaed;--mute:#9aa3ad;--line:#30363d;--acc:#6aa0ff;--bar:#25344d}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1150px;margin:0 auto;padding:16px}a{color:var(--acc)}h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mute);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px}
.f{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:end}.f label{display:flex;flex-direction:column;font-size:12px;color:var(--mute);gap:3px}
select,input{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chips button{font:inherit;font-size:13px;padding:4px 10px;border-radius:14px;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}
.chips button.on{background:var(--ink);color:var(--card)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:13px}
th{text-align:right;color:var(--mute);font-weight:600;padding:5px 6px;border-bottom:1px solid var(--line);white-space:nowrap}
td{text-align:right;padding:5px 6px;border-bottom:1px solid var(--line);white-space:nowrap}th.l,td.l{text-align:left}td.w{white-space:normal;min-width:160px;max-width:240px}
td.v{font-weight:700;position:relative;min-width:110px}td.v span{position:relative}td.v i{position:absolute;left:0;top:4px;bottom:4px;background:var(--bar);border-radius:3px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}.grid h3{font-size:14px;margin:0 0 6px}.grid ol{margin:0;padding-left:20px}.grid li{margin:2px 0}
</style></head><body><main>
<h1>Delta Scout – Classifiche di tutti i tempi</h1>
<p class="sub">Tutte le partite StatsBomb Open Data del dataset (1958–2025). Valori per 90 minuti salvo dove indicato.
Attenzione: il dataset è sbilanciato (molto Barcellona/Messi in Liga, Arsenal 2003/04, Leverkusen 2023/24, poche partite prima del 2000):
le classifiche descrivono questi dati, non l'intera storia del calcio. Le percentuali richiedono un numero minimo di tentativi.</p>
<div class="card"><div class="f">
<label>Metrica<select id="m"></select></label>
<label>Sesso<select id="s"><option value="M">Maschile</option><option value="F">Femminile</option></select></label>
<label>Minuti minimi<select id="min"><option>450</option><option>900</option><option selected>1800</option><option>3600</option><option>9000</option></select></label>
<label>Mostra<select id="top"><option>25</option><option selected>50</option><option>100</option><option>500</option></select></label>
<label>Cerca giocatore o squadra<input id="q" placeholder="es. Messi, Arsenal"></label>
</div><div class="chips" id="roles" style="margin-top:12px"></div></div>
<div class="card"><h2 id="h" style="font-size:17px;margin:0 0 10px"></h2><div class="scroll"><table id="t"></table></div><p class="sub" id="n"></p></div>
<div class="card"><h2 style="font-size:17px;margin:0 0 10px">Podi per ruolo <span class="sub">(sesso e minuti minimi come sopra)</span></h2><div class="grid" id="pod"></div></div>
<p class="sub">Dati: StatsBomb Open Data · anagrafica: Reep (CC0) · generato da Delta Scout.</p>
</main><script>
const D=__DATA__;const K=D.keep,M=D.metrics,ix=k=>K.indexOf(k),mi=k=>K.length+M.findIndex(m=>m[0]===k);
const ROLES=["Tutti","Attaccante","Trequartista / Ala","Centrocampista","Mediano","Terzino","Difensore centrale","Portiere"];
const PODI={"Attaccante":["npxg_p90","finalizzazione","xt_p90","tocchi_in_area_p90"],"Trequartista / Ala":["xg_xa_p90","xt_p90","dribbling_riusciti_p90","sca_p90"],
"Centrocampista":["passaggi_progressivi_p90","xt_p90","passaggi_chiave_p90","azioni_difensive_p90"],"Mediano":["passaggi_progressivi_p90","azioni_difensive_p90","pressioni_p90","passaggi_sotto_pressione_pct"],
"Terzino":["xt_p90","cross_riusciti_p90","conduzioni_progressive_p90","azioni_difensive_p90"],"Difensore centrale":["azioni_difensive_p90","aerei_vinti_p90","passaggi_progressivi_p90","precisione_passaggi_pct"],
"Portiere":["parate_pct","parate_p90","uscite_p90","lanci_lunghi_pct"]};
let role="Tutti";const $=id=>document.getElementById(id);
M.forEach(m=>{const o=document.createElement("option");o.value=m[0];o.textContent=m[1]+(m[2]==="p90"?" (per 90')":m[2]==="diff"?" (totale)":"");$("m").appendChild(o)});
$("m").value="xt_p90";
ROLES.forEach(r=>{const b=document.createElement("button");b.textContent=r;b.className=r===role?"on":"";b.onclick=()=>{role=r;[...$("roles").children].forEach(x=>x.className=x===b?"on":"");draw()};$("roles").appendChild(b)});
["m","s","min","top","q"].forEach(id=>$(id).addEventListener("input",draw));
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const name=r=>r[ix("soprannome")]||r[ix("giocatore")];
const fmt=(v,t)=>v==null?"–":t==="pct"?v.toFixed(1)+"%":t==="diff"?(v>0?"+":"")+v.toFixed(2):Math.abs(v)>=100?v.toFixed(0):v.toFixed(2);
function age(r){const d=r[ix("data_nascita")];if(!d)return"";const p=r[ix("periodo")].split("–");return`${p[0]-d.slice(0,4)}${p[1]?"–"+(p[1]-d.slice(0,4)):""}`}
function pool(key,rl){const s=$("s").value,mn=+$("min").value,q=$("q").value.toLowerCase(),j=mi(key),low=D.lower.includes(key);
return D.rows.filter(r=>r[ix("sesso")]===s&&r[ix("minuti")]>=mn&&r[j]!=null&&(rl==="Tutti"||r[ix("ruolo")]===rl)&&
(!q||(r[ix("giocatore")]+" "+r[ix("soprannome")]+" "+r[ix("squadre")]).toLowerCase().includes(q))).sort((a,b)=>low?a[j]-b[j]:b[j]-a[j])}
function draw(){const key=$("m").value,t=M.find(m=>m[0]===key)[2],j=mi(key),rows=pool(key,role),top=rows.slice(0,+$("top").value);
const mx=Math.max(...top.map(r=>Math.abs(r[j])),1e-9);
$("t").innerHTML=`<tr><th>#</th><th class="l">Giocatore</th><th class="l">Ruolo</th><th class="l">Squadre principali</th><th>Periodo</th><th>Età</th><th>Partite</th><th>Minuti</th><th>Gol</th><th>xG</th><th title="${esc(M.find(m=>m[0]===key)[1])}">Valore</th></tr>`+
top.map((r,i)=>{const tm=r[ix("transfermarkt")],nm=esc(name(r));return`<tr><td>${i+1}</td><td class="l">${tm?`<a href="${esc(tm)}" target="_blank" rel="noopener">${nm}</a>`:nm} <span class="sub">${esc(r[ix("nazionalita")])}</span></td>
<td class="l">${esc(r[ix("ruolo")])}</td><td class="l sub w">${esc(r[ix("squadre")])}</td><td>${esc(r[ix("periodo")])}</td><td>${age(r)}</td><td>${r[ix("partite")]}</td><td>${r[ix("minuti")].toLocaleString("it")}</td>
<td>${r[ix("gol")]}</td><td>${(+r[ix("xg")]).toFixed(1)}</td><td class="v"><i style="width:${(100*Math.abs(r[j])/mx).toFixed(1)}%"></i><span>${fmt(r[j],t)}</span></td></tr>`}).join("");
$("h").textContent=M.find(m=>m[0]===key)[1]+(t==="p90"?" – per 90 minuti":t==="diff"?" – totale in carriera":"")+(role==="Tutti"?"":" · "+role);
$("n").textContent=`${rows.length} giocatori soddisfano i filtri.`+(D.pctmin[key]?` Minimo ${D.pctmin[key]} tentativi per questa percentuale.`:"");
$("pod").innerHTML=Object.entries(PODI).map(([rl,ks])=>ks.map(k=>{const m=M.find(x=>x[0]===k),jj=mi(k),p=pool(k,rl).slice(0,5);
return`<div><h3>${esc(rl)} · ${esc(m[1])}</h3><ol>${p.map(r=>`<li>${esc(name(r))} <span class="sub">${fmt(r[jj],m[2])}</span></li>`).join("")||'<li class="sub">nessuno</li>'}</ol></div>`}).join("")).join("")}
draw();
</script></body></html>"""


if __name__ == "__main__":
    main()
