# data/

Ogni sottocartella ha uno stato di visibilità esplicito. Non spostare file tra queste cartelle senza aggiornare anche `.gitignore` e questa nota.

| Cartella | Visibilità | Contenuto |
|---|---|---|
| `_local_raw/` | **privata** (in `.gitignore`) | KML/KMZ originale, byte-identico a quanto scaricato da Google. Può contenere nomi propri e recapiti di terzi. Non committare mai. |
| `private/` | **privata** (in `.gitignore`) | `name_mapping.csv`: corrispondenza codice↔nome reale usata dalla pseudonimizzazione. Non committare mai. |
| `raw_redacted/` | pubblica | Copia del KML sorgente, identica in struttura/coordinate/date/layer, con nomi propri e telefoni sostituiti da codici (`PERSON_NNNN`, `PHONE_NNNN`). |
| `raw_log.jsonl` | pubblica | Log append-only di ogni acquisizione: hash, timestamp, conteggio placemark, flag di cambiamento. Nessun dato personale. |
| `normalized/` | pubblica (da Milestone 2) | `observations.csv` / `observations.geojson` nello schema normalizzato. |
| `history/` | pubblica (da Milestone 4) | `state.json` (identità cross-run: id, layer, coordinate, snippet di descrizione già pseudonimizzato, timestamp — nessun dato personale), `changes-<data>.json` (record aggiunti/rimossi/modificati), `report-<data>.json` (conteggi di validazione). |
| `osm/` | pubblica (da Milestone 8) | `snapshot-<data>/`: dati grezzi OpenStreetMap (strade per categoria, edifici, insediamenti, punti turistici) scaricati dall'Overpass API entro un raggio da ogni segnalazione, con `manifest.json` (raggi usati, licenza ODbL, conteggi). Aggiornato manualmente/periodicamente, non ogni giorno. |
| `enriched/` | pubblica (da Milestone 8) | `observations_enriched.csv`/`.geojson`: normalized + indicatori OSM separati (distanza da strade per categoria, conteggi/aree edifici, insediamento più vicino, punti turistici) — mai un indice unico di antropizzazione. |
| `derived/` | pubblica (da Milestone 9) | `study_area.geojson` (confine amministrativo PAT, fonte OSM/Nominatim), `baseline_points.geojson` (10.000 punti di controllo casuali uniformi), `baseline_manifest.json` (metodo, seed, N, CRS, limiti dichiarati). Da Milestone 10: confronti osservazioni/baseline, cluster esplorativi. |

Vedi `AGENTS.md` per il principio generale ("conservazione del dato originale" e la sua unica eccezione dichiarata) e `README.md` per la spiegazione completa della pseudonimizzazione.
