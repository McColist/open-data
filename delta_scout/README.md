# Delta Scout – analisi partite

Dati: StatsBomb Open Data (citare StatsBomb come fonte se si pubblica).

## Uso

```bash
python delta_scout/lista_partite.py              # rigenera partite.csv / partite.md (lista numerata)
python delta_scout/analizza.py                   # analizza tutte le partite
python delta_scout/analizza.py --n 778,831-894   # solo alcuni numeri della lista
python delta_scout/xt.py                         # stima la griglia xT (xt_griglia.json), prima di analizza.py
python delta_scout/elo.py                        # rating Elo delle squadre -> output/elo.csv
python delta_scout/anagrafica.py                 # età, altezza, link Transfermarkt/FBref da Reep -> output/anagrafica_giocatori.csv
python delta_scout/rose.py                       # rose complete (titolari, subentrati, riserve) -> output/rose.csv
python delta_scout/report.py                     # report HTML di ogni partita in delta_scout/report/
python delta_scout/report.py --n 778 --out C:\DeltaScout\report
```

Apri `delta_scout/report/index.html` nel browser: elenco di tutte le partite, ognuna con analisi scritta automatica
(risultato vs xG, controllo del gioco, pressing/PPDA, qualità delle occasioni, giocatori chiave), statistiche di squadra
a confronto, andamento xG, mappa dei tiri, reti di passaggi e tabelle complete dei giocatori con heatmap.
`report.py` usa solo i CSV in `output/` (non servono i dati grezzi); tutte le partite in meno di un minuto, circa 630 MB.
Esempio: `esempio_report_778.html` (finale Mondiali 2022).

Solo Python 3 standard, nessuna dipendenza. Tutte le partite: circa 20–30 minuti con 4 core.
Ogni file di output ha le colonne `n` (numero in `partite.csv`) e `match_id`.

## Convenzioni

- Coordinate StatsBomb: campo 120×80 (yard), ogni squadra attacca da sinistra (x=0) a destra (x=120), porta in (120, 40).
- Rigori finali (periodo 5) esclusi da tutte le statistiche.
- **Passaggio/conduzione progressiva**: avvicina la palla alla porta di almeno il 25% della distanza (conduzioni: anche ≥5 yard). Solo passaggi riusciti, esclusi calci piazzati.
- **Terzo finale**: x ≥ 80. **Area**: x ≥ 102, 18 ≤ y ≤ 62. **Pressione/recupero alto**: x ≥ 80.
- **Minuti**: tempo effettivo dagli eventi (recupero incluso), dall'ingresso a sostituzione/espulsione.

## output/squadre.csv – una riga per squadra per partita

| Colonna | Significato |
|---|---|
| gol, gol_subiti, esito | risultato (V/N/P) |
| xg, npxg, xg_subiti, xg_diff | expected goals StatsBomb (npxg = senza rigori) |
| xg_1t, xg_2t, xg_supplt | xG per tempo |
| tiri, tiri_in_porta, tiri_in_area, tiri_subiti, xg_per_tiro | volume e qualità dei tiri |
| possesso_pct | quota del tempo di possesso |
| field_tilt_pct | quota dei passaggi nel terzo offensivo rispetto all'avversario |
| ppda | passaggi concessi all'avversario nel suo 60% di campo per ogni azione difensiva (contrasto, intercetto, fallo). Più basso = pressing più intenso |
| passaggi_*, cross_*, passaggi_chiave | costruzione e rifinitura |
| conduzioni_progressive, dribbling_* | portata palla |
| pressioni, pressioni_alte, contropressioni, recuperi, recuperi_alti, contrasti_vinti, intercetti, aerei_vinti | fase difensiva |
| palle_perse, parate, falli, gialli, rossi, corner, fuorigioco | varie |
| modulo, allenatore, fase, giornata, stadio, arbitro | contesto della partita (modulo iniziale) |
| tiri_contropiede, azioni_tiro_sca, contese_vinte | SCA = ultime 2 azioni offensive (passaggio riuscito, dribbling riuscito, fallo subito, tiro) prima di un tiro |
| possessi, passaggi_per_possesso, sequenze_10_passaggi | stile di possesso |
| lunghezza_media_passaggi_m, passaggi_avanti_pct, lanci_lunghi, passaggi_sotto_pressione | stile di passaggio |
| momentum_5min | azioni nel terzo offensivo per intervalli di 5 minuti (separati da `;`) |
| heatmap_tocchi_6x4, heatmap_pressioni_6x4, heatmap_difesa_6x4 | griglie 6×4 come per i giocatori |
| dati_360, avversari_5m_medi_360, azioni_pressate_360_pct | solo partite 360: media avversari entro 5 yard da chi ha la palla, % azioni con ≥2 avversari vicini |

## output/giocatori.csv – una riga per giocatore per partita

Anagrafica: `player_id, giocatore, soprannome, maglia, ruolo` (ruolo iniziale), `titolare, nazionalita, minuti`.

| Colonna | Significato |
|---|---|
| gol, gol_np, assist, xg, npxg, xa | produzione offensiva; xa = somma xG dei tiri nati da un suo passaggio |
| sca, gca | azioni che portano a un tiro / a un gol (vedi sopra) |
| passaggi_avanti, passaggi_indietro, lunghezza_media_passaggi_m, contese_vinte | |
| uscite, prese_alte, respinte_di_pugno | portieri |
| xg_chain | xG totale dei possessi della squadra a cui ha partecipato |
| tiri, tiri_in_porta, tocchi_in_area | |
| passaggi, passaggi_riusciti, precisione_passaggi_pct | |
| passaggi_chiave, passaggi_progressivi, passaggi_terzo_finale, passaggi_in_area, filtranti, cambi_gioco, lanci_lunghi(_riusciti), cross(_riusciti) | |
| passaggi_sotto_pressione(_riusciti) | resistenza al pressing |
| ricezioni, ricezioni_terzo_finale | |
| conduzioni_progressive, conduzioni_terzo_finale, conduzioni_in_area, metri_progressivi | metri_progressivi = avanzamento palla (passaggi riusciti + conduzioni), in metri |
| dribbling, dribbling_riusciti, saltato_da_avversario | |
| azioni_con_palla | tutte le azioni con una posizione (passaggi, ricezioni, conduzioni, tiri, duelli…) |
| pressioni, pressioni_alte, contropressioni, contrasti, contrasti_vinti, intercetti, recuperi, recuperi_alti, respinte, blocchi, aerei_vinti, aerei_persi | fase difensiva |
| palle_perse, falli_commessi, falli_subiti, gialli, rossi | |
| parate, gol_subiti_portiere | portieri |
| pos_media_x, pos_media_y | posizione media delle azioni (nodi della rete di passaggi) |
| heatmap_6x4 | 24 conteggi separati da `;`, riga per riga: 6 colonne di 20 yard lungo il campo × 4 righe di 20 yard in larghezza (riga 0 = y 0–20) |
| eventi_360, avversari_5m_medi_360, azioni_pressate_360_pct | come sopra, per il singolo giocatore |

Per confronti tra giocatori conviene normalizzare per 90 minuti: `valore / minuti * 90` (filtrando ad es. minuti ≥ 30).

## xT (Expected Threat)

Griglia 16×12 stimata con il metodo di Karun Singh su tutte le partite del dataset (`xt_griglia.json`).
Ogni passaggio o conduzione riuscita vale xT(arrivo) − xT(partenza): misura quanto il giocatore ha avvicinato la squadra al gol.
Colonne: `xt` (squadre e giocatori), `xt_passaggi`, `xt_conduzioni` (giocatori).

## output/elo.csv

Rating Elo pre e post partita per squadra (K=30, scarto gol, +60 in casa, 0 nei tornei), `prob_vittoria_attesa` e
`partite_storia` (partite precedenti nel dataset: sotto 10 il valore è poco affidabile, perché alcune squadre sono coperte solo in parte).

## output/anagrafica_giocatori.csv

Collegamento con [Reep](https://github.com/withqwerty/reep) (licenza CC0) per nome, nazionalità e data di nascita plausibile:
`data_nascita, altezza_cm, ruolo, transfermarkt, fbref, wikidata, affidabilita`. Circa l'80% dei giocatori è collegato;
i casi ambigui (omonimi) sono lasciati vuoti invece di rischiare un collegamento sbagliato.

## output/rose.csv

Tutti i convocati di ogni partita: `stato` (titolare / subentrato / non entrato), `maglia`, `ruolo_iniziale`,
`ruoli` (sequenza dei ruoli occupati), `cartellini`, `maglia_stimata` (1 = numero mancante nella fonte, recuperato dalle altre partite del giocatore; se non recuperabile, nella grafica compaiono le iniziali). Nel report alimenta la grafica **Formazioni**: titolari a specchio
nella posizione media reale (stile Sofascore), con gol, assist, cartellini e minuto di uscita, e sotto allenatore,
modulo e cambi di modulo, titolari con ruoli, sostituzioni (minuto, motivo) e riserve non utilizzate.

## output/tiri.csv – un tiro per riga

Squadra, giocatore, periodo/minuto, `x, y`, `distanza_porta`, `xg`, `esito`, `gol`, `tipo` (Open Play, Penalty, Free Kick…), `parte_corpo`, `tecnica`, `azione` (tipo di azione), `primo_tocco`, `sotto_pressione`, `difensori_nel_triangolo` (difensori tra il tiratore e i pali), `portiere_dist_porta`, `assistman`, `fine_x/y/z` (punto di arrivo del tiro).
Per la linea temporale degli xG: cumulare `xg` per squadra ordinando per periodo/minuto.

## output/eventi_chiave.csv – cronaca

Gol (anche su rigore e autogol), cartellini, sostituzioni (con motivo) e cambi di modulo, con minuto e squadra.

## output/rete_passaggi.csv – rete di passaggi

Coppie passatore → ricevente con almeno 2 passaggi riusciti nella partita. Per disegnare la rete usare come posizione dei nodi `pos_media_x/y` da `giocatori.csv`.
