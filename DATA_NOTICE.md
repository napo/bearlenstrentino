# Nota sui dati / Data notice

## Italiano

### Provenienza

Il dataset di partenza è una Google My Maps pubblica ("Mappa orsi Trentino", `MAP_ID` di default `1d43YdLzznhl-VxXOz6kg5ZKLdf5RjG4`), dichiarata dalla mappa stessa come raccolta di segnalazioni pervenute a social network e gruppi WhatsApp dedicati al tema, curata da un singolo autore (Michele Corti). **Non è un dato ufficiale della Provincia Autonoma di Trento né di alcun ente di monitoraggio faunistico.** BearLens Trentino non ha alcuna affiliazione con l'autore della mappa sorgente.

Questo progetto non modifica il giudizio editoriale della fonte (quali segnalazioni includere, come categorizzarle nei folder originali): li preserva come `source_layer` e li usa come dato di partenza per un'analisi indipendente, con i limiti espliciti descritti in `README.md` e `REFERENCES.md`.

### Dati ufficiali di riferimento

Per dati verificati sul campo su popolazione, danni e conflitti con l'orso in Provincia Autonoma di Trento, fare riferimento al programma ufficiale di monitoraggio della PAT. Franchini et al. (2026, *Scientific Reports*, vedi `REFERENCES.md`) descrivono tale sistema (dati 2009–2023, eventi verificati con tecnici faunistici e genetica). BearLens Trentino non sostituisce questa fonte.

### Dati personali

Le descrizioni originali contengono occasionalmente nomi propri di persone private (es. testimoni citati per nome) e recapiti di contatto. Il trattamento di questi dati è descritto in dettaglio in `README.md` (sezione "Privacy: pseudonimizzazione"). In sintesi: il file sorgente reale non viene mai pubblicato; viene pubblicata solo una copia con nomi/numeri di telefono sostituiti da codici; la tabella di corrispondenza resta locale e privata.

Se sei una persona citata per nome nella mappa sorgente e hai richieste relative alla pubblicazione (anche pseudonimizzata) dei tuoi dati, apri una issue sul repository.

### Foto

Alcune segnalazioni includono una foto, già pubblica sulla mappa sorgente. Questo progetto ne pubblica una copia (`data/media/`), scaricata così com'è: a differenza del testo, le foto non passano per nessuna redazione automatica, quindi possono mostrare persone riconoscibili. Chi si riconosce in una foto e desidera che venga rimossa può aprire una issue sul repository, con lo stesso criterio descritto sopra per i nomi propri.

### OpenStreetMap (a partire dalla Milestone 8)

I dati OpenStreetMap usati per l'enrichment sono © OpenStreetMap contributors, distribuiti con licenza [ODbL](https://opendatacommons.org/licenses/odbl/). Ogni snapshot userà verrà accompagnato da attribuzione esplicita e data di estrazione.

### Licenza dei dati derivati

Il codice di questo repository è distribuito con licenza WTFPL (`LICENSE`). I dati derivati pubblicati (`data/raw_redacted/`, e in futuro `data/normalized/`, `data/enriched/`, `data/derived/`) sono resi disponibili in buona fede per finalità di trasparenza e ricerca; non essendo il progetto proprietario del dataset sorgente originale, non viene attribuita loro una licenza dati esclusiva. Chiunque riutilizzi questi dati derivati deve attribuire sia BearLens Trentino sia, per quanto verificabile, la fonte originale.

---

## English

### Provenance

The source dataset is a public Google My Maps ("Mappa orsi Trentino", default `MAP_ID` `1d43YdLzznhl-VxXOz6kg5ZKLdf5RjG4`), which self-describes as a collection of reports received via social networks and dedicated WhatsApp groups, curated by a single author (Michele Corti). **It is not an official dataset of the Autonomous Province of Trento or of any wildlife-monitoring body.** BearLens Trentino has no affiliation with the source map's author.

### Official reference data

For field-verified data on bear population, damages, and conflicts in the Autonomous Province of Trento, refer to PAT's official monitoring program. Franchini et al. (2026, *Scientific Reports*, see `REFERENCES.md`) describe this system. BearLens Trentino does not replace this source.

### Personal data

Original descriptions occasionally contain private individuals' full names and contact details. Handling is described in `README.md` ("Privacy: pseudonymization"): the true source file is never published; only a copy with names/phone numbers replaced by codes is published; the code↔name mapping stays local and private. If you are named in the source map and have requests regarding publication of your (even pseudonymized) data, please open a repository issue.

### Photos

Some reports include a photo, already public on the source map. This project publishes a copy of it (`data/media/`) exactly as downloaded: unlike text, photos do not go through any automated redaction, so they may show identifiable people. If you recognize yourself in a photo and want it removed, please open a repository issue, same as for personal names above.

### OpenStreetMap (from Milestone 8)

OSM data used for enrichment is © OpenStreetMap contributors, licensed under [ODbL](https://opendatacommons.org/licenses/odbl/).

### License of derived data

Code is WTFPL-licensed (`LICENSE`). Published derived data is made available in good faith for transparency and research purposes; since the project does not own the original source dataset, no exclusive data license is asserted over it. Reusers should attribute both BearLens Trentino and, where verifiable, the original source.
