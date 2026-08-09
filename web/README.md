# web/

Frontend React + TypeScript, mappe con MapLibre GL JS, grafici con ECharts. Vedi il `README.md` nella root per la descrizione del progetto.

Consuma esclusivamente i file GeoJSON già calcolati dalla pipeline Python in `data/` — nessun join geospaziale o statistico lato browser: quello che il sito mostra è sempre lo stesso identico numero che la pipeline ha scritto su disco.

## Comandi

```bash
npm install
npm run dev        # server di sviluppo, esegue prima "sync-data"
npm run build      # build di produzione, esegue prima "sync-data"
npm run sync-data  # copia data/normalized/observations.geojson e data/media/ in public/
```

Basemap: `https://styles.maptoolkit.org/summer.json`. Rilievo 3D: tile terrain-RGB di Mapterhorn.
