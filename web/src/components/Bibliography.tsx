interface SeeAlsoLink {
  label: string;
  href: string;
}

interface Reference {
  id: string;
  citation: string;
  doi?: string;
  takeaway: string;
  seeAlso?: SeeAlsoLink[];
}

// Plain-language distillation of REFERENCES.md, kept as page content
// (not a link to a file in the repository) so the site is readable on
// its own. Full methodological detail — which project decision each
// paper motivated — stays in the repository for anyone who wants to
// dig into the engineering side.
const REFERENCES: Reference[] = [
  {
    id: "ref-ditmer-2021",
    citation: "Ditmer, Iannarilli, Tri, Garshelis & Carter (2021), Journal of Animal Ecology",
    doi: "10.1111/1365-2656.13338",
    takeaway:
      "La luce artificiale notturna, che segnala dove c'è più presenza umana, da sola predice il numero di segnalazioni di orso meglio di quasi ogni altro fattore territoriale.",
    seeAlso: [{ label: "Effetto di osservazione (bias)", href: "#bias-osservazione" }],
  },
  {
    id: "ref-airst-fleming-2024",
    citation: "Airst & Fleming (2024), Human–Wildlife Interactions",
    doi: "10.26077/2f07-828b",
    takeaway:
      "Le interazioni uomo-orso segnalate si concentrano vicino a strade e in paesaggi frammentati, più che in aree remote.",
    seeAlso: [{ label: "Distorsione di campionamento nello spazio (bias)", href: "#bias-campionamento-spaziale" }],
  },
  {
    id: "ref-mcfadden-hiller-2016",
    citation: "McFadden-Hiller, Beyer & Belant (2016), PLOS ONE",
    doi: "10.1371/journal.pone.0154474",
    takeaway:
      "In Michigan il segnale più forte per gli incidenti con orsi era la copertura forestale frammentata, non la vicinanza alle case: un indizio di comportamento reale dell'animale, non solo di osservazione umana.",
    seeAlso: [{ label: "Confondimento ecologico", href: "#bias-confondimento-ecologico" }],
  },
  {
    id: "ref-wilson-2005",
    citation: "Wilson, Madel, Mattson, Graham, Burchfield & Belsky (2005), Ursus",
    doi: "10.2192/1537-6176(2005)016[0117:NLFHAA]2.0.CO;2",
    takeaway:
      "I conflitti si concentrano dove ci sono attrattori legati all'uomo (bestiame, arnie, discariche): proteggerli riduce concretamente i conflitti.",
    seeAlso: [{ label: "Confondimento ecologico", href: "#bias-confondimento-ecologico" }],
  },
  {
    id: "ref-sikdokur-2024",
    citation: "Sıkdokur, Naderi, Çeltik, Kemahlı Aytekin, Kušak, Sağlam & Şekercioğlu (2024), Ecological Informatics",
    doi: "10.1016/j.ecoinf.2024.102643",
    takeaway:
      "In Turchia i conflitti orso-uomo si concentrano vicino ad aree protette: gli autori lo leggono come vero comportamento dell'orso attratto dal cibo umano, non solo come un effetto di maggiore osservazione.",
    seeAlso: [{ label: "Confondimento ecologico", href: "#bias-confondimento-ecologico" }],
  },
  {
    id: "ref-franchini-2026",
    citation: "Franchini, Raniolo, Corazzin, Zanghellini, Bragalanti & Bovolenta (2026), Scientific Reports",
    doi: "10.1038/s41598-026-38371-4",
    takeaway:
      "Il sistema ufficiale di monitoraggio di Trentino e Friuli-Venezia Giulia (2009-2023) mostra un avvicinamento progressivo dell'orso agli insediamenti dal 2018, con dati verificati sul campo — a differenza del dataset raccolto da questo progetto.",
    seeAlso: [{ label: "Programma ufficiale di monitoraggio PAT", href: "#official-monitoring" }],
  },
  {
    id: "ref-sherman-2025",
    citation: "Sherman, Schell & Wilkinson (2025), Science of the Total Environment",
    doi: "10.1016/j.scitotenv.2025.179227",
    takeaway:
      "Chi segnala un animale selvatico sui social non è un campione neutro: il livello socioeconomico di un quartiere predice quante segnalazioni arrivano, a prescindere da quanti animali ci siano davvero.",
    seeAlso: [{ label: "Effetto di chi segnala (bias)", href: "#bias-segnalazione" }],
  },
  {
    id: "ref-geldmann-2016",
    citation: "Geldmann, Heilmann-Clausen, Holm, Levinsky, Markussen, Olsen, Rahbek & Tøttrup (2016), Diversity and Distributions",
    doi: "10.1111/ddi.12477",
    takeaway:
      "In diversi progetti di citizen science, la distanza dalle strade e la densità di popolazione guidano dove le persone effettivamente osservano e segnalano, indipendentemente dalla specie.",
    seeAlso: [{ label: "Distorsione di campionamento nello spazio (bias)", href: "#bias-campionamento-spaziale" }],
  },
];

export function Bibliography() {
  return (
    <details className="bibliography">
      <summary>Bibliografia scientifica citata in questa pagina</summary>
      <ul>
        {REFERENCES.map((ref) => (
          <li key={ref.citation} id={ref.id}>
            <p className="bibliography-citation">
              {ref.citation}
              {ref.doi && (
                <>
                  {" — "}
                  <a href={encodeURI(`https://doi.org/${ref.doi}`)} target="_blank" rel="noreferrer">
                    doi.org/{ref.doi}
                  </a>
                </>
              )}
            </p>
            <p>{ref.takeaway}</p>
            {ref.seeAlso && ref.seeAlso.length > 0 && (
              <p className="chart-links">
                Vedi anche:{" "}
                {ref.seeAlso.map((link, i) => (
                  <span key={link.href}>
                    {i > 0 && ", "}
                    <a href={link.href}>{link.label}</a>
                  </span>
                ))}
                .
              </p>
            )}
          </li>
        ))}
      </ul>
    </details>
  );
}
