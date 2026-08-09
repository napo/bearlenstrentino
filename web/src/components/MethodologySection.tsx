interface SeeAlsoLink {
  label: string;
  href: string;
}

type BiasGroup = "chi-osserva" | "dove-osserviamo" | "quando-osserviamo" | "cosa-significa";

interface BiasEntry {
  id: string;
  group: BiasGroup;
  title: string;
  body: string;
  seeAlso?: SeeAlsoLink[];
}

const GROUP_LABELS: Record<BiasGroup, string> = {
  "chi-osserva": "Chi osserva",
  "dove-osserviamo": "Dove osserviamo",
  "quando-osserviamo": "Quando osserviamo",
  "cosa-significa": "Cosa significa una segnalazione",
};

const GROUP_ORDER: BiasGroup[] = ["chi-osserva", "dove-osserviamo", "quando-osserviamo", "cosa-significa"];

// Catalog of ways this kind of data can mislead a reader (see README.md /
// REFERENCES.md). Kept as prose here, self-contained in the deployed
// site, rather than only linking out to REFERENCES.md — a static export
// of the site may not bundle the repository's other markdown files.
// "Bias" is kept in parentheses next to a plain-language name because
// it's the term the cited papers themselves use. Grouped into 4 families
// (who/where/when/what) rather than shown as one flat list of 11 — same
// content, easier to scan; each entry collapses into an accordion so the
// page reads as 4 short groups, not a wall of open cards.
const BIASES: BiasEntry[] = [
  {
    id: "bias-osservazione",
    group: "chi-osserva",
    title: "Effetto di osservazione (bias)",
    body:
      "Un orso si può osservare solo dove e quando c'è qualcuno a guardare. Uno studio (Ditmer et al. 2021) mostra che la luce artificiale notturna — che segnala quante persone vivono in una zona, non quanti orsi ci sono — da sola predice il numero di segnalazioni meglio di quasi ogni altro fattore: in una zona adatta all'orso ma poco illuminata, gli orsi previsti erano circa il 375% in più di quelli davvero segnalati.",
    seeAlso: [
      { label: "Grafico sugli orari", href: "#chart-time-of-day" },
      { label: "Ditmer et al. 2021", href: "#ref-ditmer-2021" },
    ],
  },
  {
    id: "bias-segnalazione",
    group: "chi-osserva",
    title: "Effetto di chi segnala (bias)",
    body:
      "Non tutti gli episodi hanno la stessa probabilità di finire segnalati. Uno studio (Sherman et al. 2025) mostra che il livello socioeconomico e la composizione di un quartiere prevedono quante segnalazioni di carnivori arrivano sui social, a prescindere da quanti animali ci siano davvero.",
    seeAlso: [{ label: "Sherman et al. 2025", href: "#ref-sherman-2025" }],
  },
  {
    id: "bias-accessibilita",
    group: "chi-osserva",
    title: "Distorsione di accessibilità (bias)",
    body:
      "Strade, sentieri e luoghi frequentati aumentano solo la possibilità che qualcuno veda l'orso: non dicono nulla su dove l'orso si trovi davvero.",
  },
  {
    id: "bias-campionamento-spaziale",
    group: "dove-osserviamo",
    title: "Distorsione di campionamento nello spazio (bias)",
    body:
      "Le persone non si distribuiscono in modo uniforme sul territorio: si concentrano vicino a strade, sentieri e paesi. Uno studio (Geldmann et al. 2016) mostra che la distanza dalle strade e la densità di popolazione guidano questo tipo di distorsione in più progetti di citizen science, indipendentemente dalla specie osservata.",
    seeAlso: [{ label: "Geldmann et al. 2016", href: "#ref-geldmann-2016" }],
  },
  {
    id: "bias-incertezza-coordinate",
    group: "dove-osserviamo",
    title: "Coordinate non sempre precise",
    body:
      "Le coordinate di una segnalazione condivisa da privati cittadini non hanno tutte la stessa precisione: un punto può indicare il luogo esatto dell'evento, oppure solo un riferimento approssimativo, come il centro del paese più vicino. Il dataset non distingue sempre i due casi, perché la fonte non lo dichiara.",
  },
  {
    id: "bias-accumulo-temporale",
    group: "quando-osserviamo",
    title: "Distorsione di accumulo nel tempo (bias)",
    body:
      "Mostrare insieme segnalazioni di periodi diversi dà l'impressione di una presenza costante e diffusa, anche se i fatti non sono mai successi tutti insieme. Per questo il grafico nel tempo mostra sempre l'intero storico, separato dai filtri di periodo.",
    seeAlso: [{ label: "Grafico nel tempo", href: "#chart-timeline" }],
  },
  {
    id: "bias-osservazioni-duplicate",
    group: "quando-osserviamo",
    title: "Segnalazioni ripetute o collegate",
    body:
      "Più segnalazioni vicine nello spazio e nel tempo possono riguardare lo stesso episodio o lo stesso animale. Non deduciamo mai automaticamente che eventi vicini siano lo stesso orso: un'eventuale analisi futura in questo senso sarà sempre presentata come ipotesi da verificare, mai come identificazione certa.",
  },
  {
    id: "bias-eterogeneita-evidenza",
    group: "cosa-significa",
    title: "Prove di tipo diverso",
    body:
      "Un avvistamento diretto, una foto da fototrappola, un'impronta e un danno a un allevamento non valgono allo stesso modo come prova. Li distinguiamo sempre visivamente (colore e forma, mai uno solo) e indichiamo sempre un livello di affidabilità della classificazione, mai una probabilità statistica.",
    seeAlso: [
      { label: "Grafico sui tipi di segnalazione", href: "#chart-type-breakdown" },
      { label: "Grafico su come classifichiamo", href: "#chart-classification-method" },
    ],
  },
  {
    id: "bias-eterogeneita-fonte",
    group: "cosa-significa",
    title: "Segnalazioni raccolte in modi diversi",
    body:
      "Le segnalazioni arrivano da persone e canali diversi (social network, gruppi WhatsApp), non da un protocollo di monitoraggio uguale per tutti. Lo dice apertamente anche la mappa da cui arrivano i dati, ed è bene tenerlo presente in ogni confronto nel tempo o tra zone.",
    seeAlso: [{ label: "Grafico su come classifichiamo", href: "#chart-classification-method" }],
  },
  {
    id: "bias-confondimento-ecologico",
    group: "cosa-significa",
    title: "Confondimento ecologico",
    body:
      "Un divario tra segnalazioni e territorio accessibile non prova da solo un effetto di osservazione: più studi (Sıkdokur et al. 2024, Wilson et al. 2005, McFadden-Hiller et al. 2016) mostrano che gli orsi possono davvero spostarsi verso i margini abitati in cerca di cibo, specialmente in autunno prima del letargo. Lo stesso schema sulla mappa è compatibile con entrambe le spiegazioni, e questo dataset da solo non permette di scegliere tra le due.",
    seeAlso: [
      { label: "Sıkdokur et al. 2024", href: "#ref-sikdokur-2024" },
      { label: "Wilson et al. 2005", href: "#ref-wilson-2005" },
      { label: "McFadden-Hiller et al. 2016", href: "#ref-mcfadden-hiller-2016" },
    ],
  },
  {
    id: "bias-denominatore-mancante",
    group: "cosa-significa",
    title: "Manca un termine di paragone",
    body:
      "Per stimare una vera probabilità di incontro servirebbe sapere quante persone erano presenti in una zona, quanto tempo ci hanno passato, e con quale probabilità avrebbero segnalato un evento. Questo dataset non contiene questi numeri: per questo non calcoliamo mai una \"probabilità di incontro\" a partire solo dai punti sulla mappa.",
  },
];

export function MethodologySection() {
  return (
    <div className="methodology-catalog">
      {GROUP_ORDER.map((group) => (
        <div key={group}>
          <h3 className="bias-group-title">{GROUP_LABELS[group]}</h3>
          {BIASES.filter((bias) => bias.group === group).map((bias) => (
            <details key={bias.id} id={bias.id}>
              <summary>{bias.title}</summary>
              <p>{bias.body}</p>
              {bias.seeAlso && bias.seeAlso.length > 0 && (
                <p className="chart-links">
                  Vedi anche:{" "}
                  {bias.seeAlso.map((link, i) => (
                    <span key={link.href}>
                      {i > 0 && ", "}
                      <a href={link.href}>{link.label}</a>
                    </span>
                  ))}
                  .
                </p>
              )}
            </details>
          ))}
        </div>
      ))}
    </div>
  );
}
