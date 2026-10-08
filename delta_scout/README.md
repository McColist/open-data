# Delta Scout – analisi partite

Dati: StatsBomb Open Data (citare StatsBomb come fonte se si pubblica).

## Uso

```bash
python delta_scout/lista_partite.py              # rigenera partite.csv / partite.md (lista numerata)
python delta_scout/analizza.py                   # analizza tutte le partite
python delta_scout/analizza.py --n 778,831-894   # solo alcuni numeri della lista
```

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
| dati_360, avversari_5m_medi_360, azioni_pressate_360_pct | solo partite 360: media avversari entro 5 yard da chi ha la palla, % azioni con ≥2 avversari vicini |

## output/giocatori.csv – una riga per giocatore per partita

Anagrafica: `player_id, giocatore, soprannome, maglia, ruolo` (ruolo iniziale), `titolare, nazionalita, minuti`.

| Colonna | Significato |
|---|---|
| gol, gol_np, assist, xg, npxg, xa | produzione offensiva; xa = somma xG dei tiri nati da un suo passaggio |
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

## output/tiri.csv – un tiro per riga

Squadra, giocatore, periodo/minuto, `x, y`, `distanza_porta`, `xg`, `esito`, `gol`, `tipo` (Open Play, Penalty, Free Kick…), `parte_corpo`, `tecnica`, `azione` (tipo di azione), `primo_tocco`, `sotto_pressione`, `difensori_nel_triangolo` (difensori tra il tiratore e i pali), `portiere_dist_porta`, `assistman`, `fine_x/y/z` (punto di arrivo del tiro).
Per la linea temporale degli xG: cumulare `xg` per squadra ordinando per periodo/minuto.

## output/rete_passaggi.csv – rete di passaggi

Coppie passatore → ricevente con almeno 2 passaggi riusciti nella partita. Per disegnare la rete usare come posizione dei nodi `pos_media_x/y` da `giocatori.csv`.
