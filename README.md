# BearLens Trentino

BearLens Trentino raccoglie le segnalazioni di presenza dell'orso in Trentino pubblicate su una Google My Maps, e le ripubblica con una lettura più critica e trasparente di quanto permetta una mappa statica di punti: mai confondendo il numero di segnalazioni con il numero di orsi, distinguendo sempre dato originale da dato dedotto, e dichiarando apertamente ogni limite metodologico.

> This project turns a crowdsourced Google My Maps of bear sightings in Trentino, Italy into a more transparent, critically-annotated dataset and website — never treating report counts as a population estimate. See `data/` for pipeline output and `web/` for the site (React + MapLibre GL JS).

Non è un progetto della Fondazione Bruno Kessler, né della Provincia Autonoma di Trento, né ha alcun rapporto con l'autore della mappa sorgente (Michele Corti, che l'ha resa pubblica lui stesso): è un'iniziativa personale, nata per curiosità e portata avanti nel tempo libero.

## Cosa contiene questo repository

- **`pipeline/`** — codice Python che scarica, normalizza e arricchisce i dati (nessuna dipendenza pesante: `xml.etree.ElementTree` invece di lxml, `shapely`/`pyproj` solo dove serve davvero un calcolo geometrico).
- **`scripts/`** — i comandi che eseguono ogni stadio della pipeline (vedi sotto).
- **`data/`** — l'output della pipeline: dati grezzi pseudonimizzati, normalizzati, arricchiti, derivati.
- **`web/`** — il sito React + MapLibre GL JS + ECharts che legge solo i file già calcolati in `data/` (mai un calcolo geospaziale nel browser).
- **`tests/`** — test unitari per ogni stadio della pipeline, senza dipendenze di rete.

## La pipeline, stadio per stadio

```text
acquisizione → normalizzazione (redazione, date, orari, classificazione)
             → arricchimento (distanza da strade/edifici via OpenStreetMap, luce notturna)
             → analisi statistica sperimentale (facoltativa, non mostrata sul sito)
             → sito web
```

| Script | Cosa fa |
|---|---|
| `scripts/acquire.py` | Scarica il KML sorgente, lo valida, pseudonimizza i nomi propri, estrae e classifica le segnalazioni, aggiorna la cronologia. Scrive anche una copia locale delle foto citate nelle segnalazioni (vedi "Foto", sotto). |
| `scripts/enrich_osm.py` | Calcola la distanza di ogni segnalazione da strade, edifici e insediamenti, usando OpenStreetMap. |
| `scripts/enrich_nightlight.py` | Stima la luminosità artificiale notturna nel punto di ogni segnalazione (proxy visivo da immagini satellitari NASA GIBS, non una misura calibrata). |
| `scripts/generate_baseline.py` e `scripts/compare_baseline.py` | Generano un campione di punti scelti a caso sul territorio e lo confrontano con le segnalazioni, per esplorare se le segnalazioni sono più vicine a strade/edifici del previsto. **Analisi sperimentale**: il risultato non è più mostrato sul sito pubblico (si presta troppo facilmente a essere letto come una prova di qualcosa che non dimostra), ma resta eseguibile qui per chi vuole verificarlo di persona. |
| `scripts/fit_used_available_model.py` | Una regressione logistica "used-available" che stima il peso relativo di alcuni fattori territoriali. Volutamente sperimentale, non ancora passata per una revisione indipendente: disponibile nei dati (`data/derived/used_available_model.json`), non presentata sul sito come risultato. |

Ogni stadio è testabile isolatamente con fixture locali, senza rete (`pytest`).

## Privacy: pseudonimizzazione dei nomi propri

Le descrizioni originali contengono occasionalmente nomi di persone private (es. testimoni citati per nome) e recapiti di contatto. Per non ripubblicare dati personali:

- Il file KML/KMZ **così come scaricato da Google non viene mai committato**: resta locale (`data/_local_raw/`, in `.gitignore`).
- Una copia **pseudonimizzata** (`data/raw_redacted/`) viene versionata pubblicamente: identica all'originale in struttura, coordinate, date e layer, con nomi propri e numeri di telefono sostituiti da codici (`PERSON_0001`, `PHONE_0001`, ...).
- La tabella di corrispondenza codice↔nome reale (`data/private/name_mapping.csv`) resta **solo locale** e non viene mai pubblicata.

È l'unica trasformazione che il progetto si concede sul dato sorgente, ed è dichiarata apertamente, non silenziosa. La redazione è euristica (pattern testuali, non un modello NLP — vedi `pipeline/privacy/redactor.py`): può occasionalmente oscurare un toponimo per eccesso di prudenza, ma è calibrata per non lasciar passare un nome reale.

## Foto

Le segnalazioni includono a volte una foto, ospitata dal servizio di Google usato dalla mappa sorgente. Quel servizio blocca il caricamento delle immagini da un sito esterno come questo, quindi `scripts/acquire.py` ne scarica una copia in `data/media/` e viene pubblicata così come scaricata, senza alcuna modifica: sono già pubbliche sulla mappa sorgente, e questo progetto le ripubblica per lo stesso motivo per cui ripubblica il testo delle segnalazioni. A differenza del testo, però, le foto non passano per nessuna redazione automatica (una foto potrebbe mostrare una persona riconoscibile). Chi si riconosce in una foto e desidera che venga rimossa può aprire una issue sul repository.

## Come eseguire la pipeline in locale

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,enrichment,raster,analysis]"
pytest
```

Per aggiornare i dati dalla mappa sorgente:

```bash
python scripts/acquire.py
```

## Come lanciare il sito

```bash
cd web
npm install
npm run dev
```

Il sito legge esclusivamente i file statici in `web/public/data/` (copiati da `data/` con `npm run sync-data`, eseguito automaticamente prima di `dev`/`build`) — non fa mai un calcolo geospaziale o statistico nel browser che la pipeline non abbia già fatto.

## Limiti noti

- Non c'è un ID stabile nella fonte: l'identità delle segnalazioni nel tempo è ricostruita euristicamente (nome, layer, coordinate arrotondate).
- La redazione dei nomi è un'euristica su pattern testuali, non un modello linguistico: può avere falsi positivi (un toponimo oscurato per prudenza) e, più raramente, falsi negativi.
- Il confronto con punti scelti a caso (`compare_baseline.py`) usa un campionamento uniforme su tutto il territorio, incluse zone dove l'orso non è mai stato segnalato: è voluto (un campione mirato smetterebbe di rappresentare "il territorio"), ma rende il confronto meno preciso di quanto una scelta più mirata otterrebbe — per questo non è presentato sul sito come una conclusione.
- Il progetto non ha alcun rapporto con l'autore della mappa sorgente, con la Provincia Autonoma di Trento, o con la Fondazione Bruno Kessler.

Le fonti scientifiche che motivano queste scelte sono elencate in [REFERENCES.md](REFERENCES.md) e, in forma divulgativa, direttamente sul sito.

## Licenza

Codice distribuito con licenza WTFPL (vedi `LICENSE`). Per la natura e i termini d'uso dei dati, vedi [DATA_NOTICE.md](DATA_NOTICE.md).
