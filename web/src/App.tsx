import { useEffect, useMemo, useState } from "react";
import { useObservations } from "./data/useObservations";
import { applyTemporalFilter, filterLabel, type TemporalFilter } from "./data/temporalFilter";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { CookieNotice, hasSeenCookieNotice } from "./components/CookieNotice";
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
  const [cookieNoticeVisible, setCookieNoticeVisible] = useState(() => !hasSeenCookieNotice());

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

      {cookieNoticeVisible && (
        <CookieNotice onDismiss={() => setCookieNoticeVisible(false)} />
      )}

      <div className="hero">
        <h1>Una mappa delle segnalazioni non è una mappa degli orsi.</h1>
        <p className="hero-tagline">
          Gli stessi dati possono raccontare storie molto diverse, a seconda di come li
          raccogliamo e li rappresentiamo.
        </p>
        <a className="hero-cta" href="#atto-1">
          Esplora i dati ↓
        </a>
      </div>

      <div className="project-premise">
        <h2>Perché esiste questo sito</h2>
        <p>
	BearLens Trentino parte dalle segnalazioni della mappa collaborativa pubblica "<a href="https://www.google.com/maps/d/u/0/viewer?hl=it&ll=46.04601685463594%2C11.082050151280466&z=9&mid=1d43YdLzznhl-VxXOz6kg5ZKLdf5RjG4" target="_new">Mappa avvistamento orsi Trentino</a>" per esplorare come leggere e interpretare meglio questi dati.
        </p>
        <p className="disclaimer">
          È un progetto personale di <a href="https://github.com/napo" target="_blank" rel="noreferrer">napo</a>, nato per curiosità e portato avanti nel tempo libero.<br/>Non è un progetto della Provincia autonoma di Trento né della Fondazione Bruno Kessler e non nasce da alcun incarico istituzionale.
        </p>
      </div>

      <h2 className="act-title" id="atto-1">
        <span className="act-kicker">Atto I</span>
        I dati
      </h2>

      <section className="narrative">
        <h2>Cosa stai davvero guardando?</h2>
        <p>
          I punti sulla mappa sotto sono <strong>segnalazioni</strong> - osservazioni
          riportate da persone, raccolte dalla{" "}
          <a
            href="https://www.google.com/maps/d/u/0/viewer?hl=it&ll=46.046016854635916%2C11.082050151280466&z=9&mid=1d43YdLzznhl-VxXOz6kg5ZKLdf5RjG4"
            target="_blank"
            rel="noreferrer"
          >
            mappa collaborativa pubblica
          </a>{" "}
          "Mappa orsi Trentino" - non una mappa di dove vivono gli orsi.
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
              <span className="value">{summary.earliest ?? "-"}</span>
              <span className="label">prima segnalazione (data completa)</span>
            </div>
            <div className="stat-tile">
              <span className="value">{summary.latest ?? "-"}</span>
              <span className="label">ultima segnalazione (data completa)</span>
            </div>
          </div>
        )}
        <div className="core-concept">
          <p>Una segnalazione non corrisponde a un orso.</p>
          <p>
            Più segnalazioni possono riferirsi allo stesso individuo o allo stesso
            episodio.
          </p>
        </div>
        <div className="map-shows-box">
          <div className="shows">
            <h4>Questa mappa mostra</h4>
            <ul>
              <li>Dove sono state raccolte le segnalazioni presenti in questo dataset.</li>
            </ul>
          </div>
          <div className="not-shows">
            <h4>Questa mappa NON mostra</h4>
            <ul>
              <li>La distribuzione reale degli orsi sul territorio.</li>
              <li>La densità della popolazione.</li>
              <li>Il rischio di incontro in un dato luogo.</li>
            </ul>
          </div>
        </div>
        <p>
          Il rilievo 3D è solo un riferimento geografico, non un indicatore di
          quantità.
          {isFiltered && ` Dati mostrati per il periodo: ${filterLabel(temporalFilter)}.`}
        </p>
        <p className="legend-note">
          Clicca su un punto per il dettaglio della segnalazione. Clicca una voce
          della legenda per mostrare o nascondere quel tipo.
        </p>
        <MapView features={filteredFeatures} />
      </section>

      <div className="mental-model">
        <p className="mental-model-kicker">Una segnalazione dipende da</p>
        <ul className="mental-model-factors">
          <li>Presenza dell'orso</li>
          <li>Possibilità di osservarlo</li>
          <li>Propensione a segnalarlo</li>
        </ul>
        <p className="mental-model-result">→ ciò che compare sulla mappa</p>
      </div>
      <p className="mental-model-caption">
        Non è una formula statistica: è il modo più semplice per tenere a mente perché
        contare le segnalazioni non basta a contare gli orsi. Il resto di questa pagina
        entra nel dettaglio di ciascuno di questi tre fattori.
      </p>

      <section className="narrative">
        <h2>Quando sono avvenuti?</h2>
        <p>
          Le date qui sotto sono estratte dal testo libero delle segnalazioni quando
          possibile - non tutte le segnalazioni includono una data interpretabile, e
          questo grafico lo segnala esplicitamente invece di far finta che tutte le
          segnalazioni siano databili.
        </p>
        <TimelineChart features={features} />
        <p className="callout">
          Quando lo storico coprirà più anni, un punto di anni fa e un punto di ieri
          potranno comparire entrambi in questa pagina: non rappresenteranno comunque
          una presenza simultanea sul territorio, solo l'accumulo di segnalazioni nel
          tempo. Il grafico qui sopra mostra sempre l'intero storico; usa i filtri qui
          sotto per restringere il periodo mostrato nella mappa più sopra e nella
          prossima sezione (tipo di evidenza).
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
            Periodo selezionato: {filterLabel(temporalFilter)} - {filteredFeatures.length} su{" "}
            {features.length} segnalazioni totali.
          </p>
        )}
      </section>

      <section className="narrative">
        <h2>Che tipo di segnalazione è?</h2>
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

      <h2 className="act-title" id="atto-2">
        <span className="act-kicker">Atto II</span>
        La lente
      </h2>

      <section className="narrative">
        <h2>Come le mappe cambiano le percezioni</h2>
        <p>
          Le stesse identiche segnalazioni, rappresentate in modi diversi, possono
          suggerire impressioni molto diverse.
        </p>
        <p>
          Prova a passare da una modalità all'altra: i dati sotto non cambiano mai,
          cambia solo come vengono mostrati.
        </p>
        <PerceptionMap features={features} />
      </section>

      <section className="narrative">
        <h2>Cosa può ingannarci in questi dati</h2>
        <p>
          Qualunque raccolta di segnalazioni fatte da persone, invece che da un
          monitoraggio scientifico organizzato, porta con sé alcune distorsioni note e
          studiate. Elencarle non significa screditare i dati: serve a leggerli con gli
          occhi giusti.
        </p>
        <p>
          Le fonti scientifiche citate qui sotto sono riportate per intero, non solo
          linkate, nell'elenco pieghevole in fondo alla sezione.
        </p>
        <MethodologySection />
        <Bibliography />
      </section>

      <h2 className="act-title" id="atto-3">
        <span className="act-kicker">Atto III</span>
        Le conclusioni
      </h2>

      <section className="narrative">
        <h2>Cosa possiamo concludere?</h2>
        <ul>
          <li>Dove sono state registrate le segnalazioni presenti in questo dataset.</li>
          <li>Quando sono state registrate, quando il testo lo permette.</li>
          <li>Quale tipo di evidenza è riportato, e con quale grado di confidenza è stato classificato.</li>
          <li>Come le segnalazioni si distribuiscono nel tempo e per tipo, all'interno di questo dataset.</li>
        </ul>
      </section>

      <section className="narrative">
        <h2>Cosa NON possiamo concludere</h2>
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

      <Footer onShowCookieNotice={() => setCookieNoticeVisible(true)} />
    </div>
  );
}
