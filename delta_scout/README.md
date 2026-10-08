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
python delta_scout/classifiche.py                # classifiche di tutti i tempi -> classifiche.html + output/carriere_giocatori.csv
python delta_scout/sequenze.py                   # conduzioni (con esito) e recuperi palla -> output/conduzioni.csv, output/recuperi.csv
python delta_scout/voti.py                       # voto Delta Scout 0-10 per giocatore e partita -> output/voti.csv
python delta_scout/passaggi.py                   # tutti i passaggi compressi -> output/passaggi/<n>.json.gz (mappe individuali)
python delta_scout/studi.py                      # studi sul dataset con grafici -> studi.html
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

## Classifiche di tutti i tempi

`classifiche.html` (apri direttamente nel browser): classifiche per ruolo su tutte le partite, filtri per sesso, minuti minimi,
metrica (36 metriche: per 90', percentuali con minimo di tentativi, Gol − xG in carriera) e ricerca; sotto, i podi per ruolo.
Il ruolo di un giocatore è quello in cui ha giocato più minuti. `output/carriere_giocatori.csv` contiene totali e valori per 90'
di tutti i 9.884 giocatori.

## Voto Delta Scout, contesto, pressing

- `output/voti.csv`: voto 0–10 per prestazione (s.v. sotto 20 minuti). Ogni statistica è confrontata (z-score) con tutte le
  prestazioni dello stesso reparto e dello stesso calcio (maschile/femminile); pesi per reparto in `voti.py` (`WEIGHTS`).
  Scala centrata su 6,6 e compressa agli estremi. È un indice di Delta Scout, non una verità oggettiva.
- `output/recuperi.csv`: recuperi palla, intercetti e contrasti vinti con esito nei 10 secondi successivi (tiro, gol, palla persa…).
- Nel report: voto in formazione e tabelle, migliore in campo, scheda "Rispetto alla carriera" (valore per 90' / media in carriera),
  mappa del pressing, carry map con frecce, esito e filtri, reti di passaggi per tutta la partita e per ogni finestra tra i cambi, menu di navigazione.

## Studi

`studi.html`: 13 studi ricalcolati dai dati (epoche, Mondiali, maschile/femminile, portieri, gol olimpici, fattore campo,
minuti dei gol, possesso, punti attesi 2015/16, Leicester, squadre dominanti, finalizzatori, vittorie improbabili). Ogni studio
ha grafico, campione, metodo, limiti, tabella dei dati ed esportazione per i social. Gli studi basati sugli eventi escludono
le partite in cui la fonte non contiene gli eventi di una delle due squadre (100 partite: ISL 2021/22, WSL 2019–21,
Ligue 1 2015/16, NWSL 2018), riconosciute da 0 passaggi o da gol degli eventi diversi dal risultato.

## Pubblicare sui social

In ogni report, sotto l'intestazione, c'è **Pubblica sui social**: un clic crea il report come carosello (copertina, analisi,
statistiche, pagelle, formazioni, xG, tiri, momentum, carry map, pressing, reti di passaggi) nel formato scelto
(4:5 Instagram/LinkedIn, 1:1, 9:16 TikTok/Storie, 16:9 X) e scarica uno zip con le slide PNG e un PDF (per i post-documento
di LinkedIn). Tutto avviene nel browser con le librerie in `vendor/` (JSZip e jsPDF, licenza MIT), anche offline.

## Logo, copyright e protezione

Logo in `logo.svg` (ricostruzione vettoriale): in testa a ogni pagina, come favicon e in filigrana su ogni grafico ("© Delta Scout").
Piè di pagina con copyright e attribuzione obbligatoria a StatsBomb (logo `statsbomb_logo.png`, richiesto dalle loro condizioni).
Deterrenti leggeri: tasto destro e trascinamento disattivati sui grafici, meta `noai`. Nessuna misura impedisce davvero la copia
di una pagina pubblica: la tutela reale è il copyright e la filigrana.

## Carry map e mappe individuali

`output/conduzioni.csv`: conduzioni progressive, che entrano nel terzo finale o in area (inizio, fine, metri, xT, pressione).
`output/passaggi/<n>.json.gz`: tutti i passaggi della partita (passatore, ricevente, coordinate, esito, minuto, flag:
1 chiave, 2 assist, 4 progressivo, 8 cross, 16 in area, 32 palla inattiva).
Nel report: carry map di squadra e, per ogni giocatore, passing map, palloni ricevuti e conduzioni (menu a tendina).

## output/tiri.csv – un tiro per riga

Squadra, giocatore, periodo/minuto, `x, y`, `distanza_porta`, `xg`, `esito`, `gol`, `tipo` (Open Play, Penalty, Free Kick…), `parte_corpo`, `tecnica`, `azione` (tipo di azione), `primo_tocco`, `sotto_pressione`, `difensori_nel_triangolo` (difensori tra il tiratore e i pali), `portiere_dist_porta`, `assistman`, `fine_x/y/z` (punto di arrivo del tiro).
Per la linea temporale degli xG: cumulare `xg` per squadra ordinando per periodo/minuto.

## output/eventi_chiave.csv – cronaca

Gol (anche su rigore e autogol), cartellini, sostituzioni (con motivo) e cambi di modulo, con minuto e squadra.

## output/rete_passaggi.csv – rete di passaggi

Coppie passatore → ricevente con almeno 2 passaggi riusciti nella partita. Per disegnare la rete usare come posizione dei nodi `pos_media_x/y` da `giocatori.csv`.
