import { useEffect, useMemo, useState } from "react";
import { useObservations } from "./data/useObservations";
import { applyTemporalFilter, filterLabel, type TemporalFilter } from "./data/temporalFilter";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { TemporalFilterControls } from "./components/TemporalFilterControls";
import { MethodologySection } from "./components/MethodologySection";
import { Bibliography } from "./components/Bibliography";
import { MapView } from "./map/MapView";
import { PerceptionMap } from "./map/PerceptionMap";
import { TimelineChart } from "./charts/TimelineChart";
import { TimeOfDayChart } from "./charts/TimeOfDayChart";
import { TypeBreakdownChart } from "./charts/TypeBreakdownChart";
import { ClassificationTransparencyChart } from "./charts/ClassificationTransparencyChart";

function useSummary(features: ReturnType<typeof useObservations>["features"]) {
  return useMemo(() => {
    const fullDates = features
      .map((f) => f.properties.event_date)
      .filter((d): d is string => Boolean(d))
      .sort();
    return {
      total: features.length,
      earliest: fullDates[0] ?? null,
      latest: fullDates[fullDates.length - 1] ?? null,
    };
  }, [features]);
}

export default function App() {
  const { loading, error, features } = useObservations();
  const summary = useSummary(features);
  const [temporalFilter, setTemporalFilter] = useState<TemporalFilter>({ kind: "last_days", days: 30 });
  const filteredFeatures = useMemo(
    () => applyTemporalFilter(features, temporalFilter),
    [features, temporalFilter]
  );
  const isFiltered = temporalFilter.kind !== "all";

  useEffect(() => {
    // Cross-links into the bibliography point at <li> entries inside a
    // collapsed <details>; a plain anchor jump scrolls to a hidden,
    // zero-height target unless we open the ancestor first.
    const openAndScrollToHash = () => {
      const id = window.location.hash.slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      let opened = false;
      let node: HTMLElement | null = target;
      while (node) {
        if (node instanceof HTMLDetailsElement && !node.open) {
          node.open = true;
          opened = true;
        }
        node = node.parentElement;
      }
      if (opened) target.scrollIntoView();
    };
    openAndScrollToHash();
    window.addEventListener("hashchange", openAndScrollToHash);
    return () => window.removeEventListener("hashchange", openAndScrollToHash);
  }, []);

  return (
    <div className="app-shell">
      <Header />

      <div className="project-premise">
        <h2>Perché esiste questo sito</h2>
        <p>
          Le segnalazioni di orso raccolte in Trentino raccontano qualcosa di reale, e
          questo progetto non mette in discussione né gli avvistamenti né il fatto che
          la convivenza con l'orso sia un problema concreto per chi vive e lavora sul
          territorio. L'obiettivo è un altro: rendere questi dati più facili da leggere
          e offrirne una lettura critica, appoggiata alla letteratura scientifica su
          orsi e citizen science, per capire meglio cosa questi numeri possono
          davvero dirci — e cosa no.
        </p>
        <p className="disclaimer">
          BearLens Trentino non è un progetto della Fondazione Bruno Kessler: è
          un'iniziativa personale, nata per curiosità e portata avanti nel tempo
          libero, senza alcun incarico né affiliazione istituzionale.
        </p>
      </div>

      <section className="narrative">
        <h2>1. Cosa stai guardando?</h2>
        <p>
          I punti che vedi in questa pagina sono <strong>segnalazioni</strong> relative
          alla presenza dell'orso in Trentino, raccolte dalla{" "}
          <a
            href="https://www.google.com/maps/d/u/0/viewer?hl=it&ll=46.046016854635916%2C11.082050151280466&z=9&mid=1d43YdLzznhl-VxXOz6kg5ZKLdf5RjG4"
            target="_blank"
            rel="noreferrer"
          >
            mappa collaborativa pubblica
          </a>{" "}
          "Mappa orsi Trentino". Una segnalazione non equivale automaticamente a un
          individuo, e il numero di punti sulla mappa non equivale automaticamente alla
          densità della popolazione di orsi o alla probabilità di incontrarne uno.
        </p>
        {loading && <p>Caricamento dati…</p>}
        {error && (
          <p className="callout attention">
            Non è stato possibile caricare i dati normalizzati ({error}). Esegui{" "}
            <code>npm run sync-data</code> dopo aver lanciato{" "}
            <code>python scripts/acquire.py</code> nella root del progetto.
          </p>
        )}
        {!loading && !error && (
          <div className="stat-row">
            <div className="stat-tile">
              <span className="value">{summary.total}</span>
              <span className="label">segnalazioni nel dataset</span>
            </div>
            <div className="stat-tile">
              <span className="value">{summary.earliest ?? "—"}</span>
              <span className="label">prima segnalazione (data completa)</span>
            </div>
            <div className="stat-tile">
              <span className="value">{summary.latest ?? "—"}</span>
              <span className="label">ultima segnalazione (data completa)</span>
            </div>
          </div>
        )}
      </section>

      <section className="narrative">
        <h2>2. Quando sono avvenuti?</h2>
        <p>
          Le date qui sotto sono estratte dal testo libero delle segnalazioni quando
          possibile — non tutte le segnalazioni includono una data interpretabile, e
          questo grafico lo segnala esplicitamente invece di far finta che tutte le
          segnalazioni siano databili.
        </p>
        <TimelineChart features={features} />
        <p className="callout">
          Quando lo storico coprirà più anni, un punto di anni fa e un punto di ieri
          potranno comparire entrambi in questa pagina: non rappresenteranno comunque
          una presenza simultanea sul territorio, solo l'accumulo di segnalazioni nel
          tempo. Il grafico qui sopra mostra sempre l'intero storico; usa i filtri qui
          sotto per restringere il periodo mostrato nelle sezioni successive (tipo di
          evidenza e mappa).
        </p>
        <h3>In che momento della giornata?</h3>
        <p>
          Anche qui, solo per le segnalazioni che riportano un orario nel testo: le
          altre sono raggruppate come "non specificato", non nascoste.
        </p>
        <TimeOfDayChart features={features} />
        <TemporalFilterControls
          features={features}
          filter={temporalFilter}
          onChange={setTemporalFilter}
        />
        {isFiltered && (
          <p className="legend-note">
            Periodo selezionato: {filterLabel(temporalFilter)} — {filteredFeatures.length} su{" "}
            {features.length} segnalazioni totali.
          </p>
        )}
      </section>

      <section className="narrative">
        <h2>3. Che tipo di segnalazione è?</h2>
        <p>
          Aver visto l'orso con i propri occhi, aver trovato un'impronta o aver subito
          un danno a un allevamento non sono la stessa cosa: hanno un peso diverso come
          prova. Li distinguiamo sempre visivamente, anche sulla mappa (colore{" "}
          <em>e</em> forma, mai uno solo).
          {isFiltered && ` Dati mostrati per il periodo: ${filterLabel(temporalFilter)}.`}
        </p>
        <TypeBreakdownChart features={filteredFeatures} />
        <ClassificationTransparencyChart features={filteredFeatures} />
      </section>

      <section className="narrative">
        <h2>4. Dove vengono raccolte le segnalazioni?</h2>
        <p>
          La mappa sotto mostra il terreno in 3D (valli, versanti, quota) solo per dare
          un riferimento geografico reale — non per suggerire quantità: il rilievo non
          cambia il significato dei punti. Clicca su un punto per vedere il dettaglio:
          il testo della segnalazione così come è stato scritto, quando è successo, e
          come l'abbiamo classificata. Clicca una voce della legenda per mostrare o
          nascondere quel tipo di segnalazione.
          {isFiltered && ` Dati mostrati per il periodo: ${filterLabel(temporalFilter)}.`}
        </p>
        <MapView features={filteredFeatures} />
      </section>

      <section className="narrative">
        <h2>5. Come le mappe cambiano le percezioni</h2>
        <p>
          Le stesse identiche segnalazioni, rappresentate in modi diversi, possono
          suggerire impressioni molto diverse. Prova a passare da una modalità
          all'altra: i dati sotto non cambiano mai, cambia solo come vengono mostrati.
        </p>
        <PerceptionMap features={features} />
      </section>

      <section className="narrative">
        <h2>6. Cosa può ingannarci in questi dati</h2>
        <p>
          Qualunque raccolta di segnalazioni fatte da persone, invece che da un
          monitoraggio scientifico organizzato, porta con sé alcune distorsioni note e
          studiate. Elencarle non significa screditare i dati: serve a leggerli con gli
          occhi giusti. Le fonti scientifiche citate qui sotto sono riportate per
          intero, non solo linkate, nell'elenco pieghevole in fondo alla sezione.
        </p>
        <MethodologySection />
        <Bibliography />
      </section>

      <section className="narrative">
        <h2>7. Cosa possiamo concludere?</h2>
        <ul>
          <li>Dove sono state registrate le segnalazioni presenti in questo dataset.</li>
          <li>Quando sono state registrate, quando il testo lo permette.</li>
          <li>Quale tipo di evidenza è riportato, e con quale grado di confidenza è stato classificato.</li>
          <li>Come le segnalazioni si distribuiscono nel tempo e per tipo, all'interno di questo dataset.</li>
        </ul>
      </section>

      <section className="narrative">
        <h2>8. Cosa NON possiamo concludere</h2>
        <ul>
          <li>Quanti orsi ci sono in Trentino, né dove si trovano tutti.</li>
          <li>La densità reale della popolazione di orsi.</li>
          <li>La probabilità di incontro o il rischio individuale in un dato luogo.</li>
          <li>Se segnalazioni vicine nello spazio/tempo riguardino lo stesso individuo.</li>
          <li>Lo sforzo di osservazione o la frequenza di presenza umana che ha reso possibile ogni segnalazione.</li>
        </ul>
        <p className="callout attention" id="official-monitoring">
          Per dati ufficiali e verificati sul campo su popolazione e danni da orso in
          Trentino, fai riferimento al{" "}
          <a
            href="https://grandicarnivori.provincia.tn.it/Segnalazioni-orse-con-piccoli/MAPPA-SEGNALAZIONI-2026"
            target="_blank"
            rel="noreferrer"
          >
            programma ufficiale di monitoraggio della Provincia Autonoma di Trento
          </a>
          .
        </p>
      </section>

      <Footer />
    </div>
  );
}
