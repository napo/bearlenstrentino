import type { ObservationProperties } from "../data/types";
import {
  CLASSIFICATION_CONFIDENCE_LABELS,
  CLASSIFICATION_METHOD_LABELS,
  DATE_STATUS_LABELS,
  OBSERVATION_TYPE_LABELS,
} from "../data/categories";
import { classifyMediaLinks } from "./mediaLinks";

// The point detail view keeps the source text as close to the original
// as possible (only names/phone numbers are pseudonymized upstream —
// see pipeline/privacy/redactor.py) and separates it from what the
// pipeline additionally worked out (date, time, evidence type), so
// nobody mistakes an inference for something the source literally said.
//
// <br> is turned into a real line break (the source writes short
// paragraphs this way); other tags are stripped but their text is kept,
// on purpose — including a bare photo/video URL if the source repeated
// one as visible link text, since the point is fidelity to the input,
// not tidiness.
function toDisplayText(html: string): string {
  return html
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function formatDateIt(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

function formatTime(properties: ObservationProperties): string | null {
  if (properties.time_parse_status === "not_present" || properties.event_hour == null) {
    return null;
  }
  const hh = String(properties.event_hour).padStart(2, "0");
  if (properties.time_parse_status === "exact" && properties.event_minute != null) {
    const mm = String(properties.event_minute).padStart(2, "0");
    return `alle ${hh}:${mm}`;
  }
  return `verso le ${hh}`;
}

export function PopupContent({ properties }: { properties: ObservationProperties }) {
  const media = classifyMediaLinks(properties.media_links);
  const time = formatTime(properties);

  return (
    <div className="popup-detail">
      <section>
        <h4>La segnalazione, così come scritta</h4>
        <p>
          <strong>{properties.name_public ?? "(senza nome)"}</strong>
          {properties.source_layer ? ` — ${properties.source_layer}` : null}
        </p>
        {properties.description_public && (
          <p style={{ whiteSpace: "pre-wrap" }}>{toDisplayText(properties.description_public)}</p>
        )}
        {media.map((item, i) => {
          if (item.kind === "youtube") {
            return (
              <p key={i}>
                <iframe
                  width="100%"
                  height="220"
                  src={`https://www.youtube-nocookie.com/embed/${item.videoId}`}
                  title="Video associato alla segnalazione"
                  style={{ border: 0, borderRadius: 6, maxWidth: "100%" }}
                  allow="encrypted-media"
                  allowFullScreen
                />
              </p>
            );
          }
          const local = properties.media_local?.[i];
          // The source hosts photos on a domain that blocks cross-site
          // embedding (mymaps.usercontent.google.com), so the popup
          // always shows a locally cached copy — never the original URL
          // directly — and says so plainly when no copy is available yet,
          // instead of silently dropping a photo the source did include.
          return local ? (
            <p key={i}>
              <a
                className="popup-photo-link"
                href={`${import.meta.env.BASE_URL}${local}`}
                target="_blank"
                rel="noreferrer"
                title="Apri la foto a dimensione intera"
              >
                <img src={`${import.meta.env.BASE_URL}${local}`} alt="Foto associata alla segnalazione" />
              </a>
            </p>
          ) : (
            <p key={i} className="popup-note">
              Questa segnalazione include una foto, ma non è ancora stato possibile
              recuperarne una copia da mostrare qui.
            </p>
          );
        })}
        {properties.redaction_applied && (
          <p style={{ fontStyle: "italic" }}>
            I nomi di persona e i numeri di telefono citati nel testo originale sono
            stati sostituiti con un codice, per proteggere chi è coinvolto nella
            segnalazione.
          </p>
        )}
      </section>

      <section>
        <h4>Quando è successo</h4>
        {properties.date_text_raw && (
          <p>Il testo originale dice: “{properties.date_text_raw}”</p>
        )}
        <p>
          {properties.event_date
            ? `Data: ${formatDateIt(properties.event_date)}`
            : `Data: ${DATE_STATUS_LABELS[properties.date_parse_status] ?? "non indicata chiaramente"}`}
          {time ? ` — ${time}` : ""}
        </p>
      </section>

      <section>
        <h4>Che tipo di segnalazione è</h4>
        <p>{OBSERVATION_TYPE_LABELS[properties.observation_type] ?? properties.observation_type}</p>
        <p className="popup-note">
          Come lo sappiamo: {CLASSIFICATION_METHOD_LABELS[properties.classification_method] ?? properties.classification_method}
          {" · "}
          affidabilità della classificazione: {CLASSIFICATION_CONFIDENCE_LABELS[properties.classification_confidence] ?? properties.classification_confidence}
        </p>
        {properties.coordinate_error && (
          <p className="popup-note">Coordinate non valide: {properties.coordinate_error}</p>
        )}
        <p className="popup-note">id: {properties.id}</p>
      </section>
    </div>
  );
}
