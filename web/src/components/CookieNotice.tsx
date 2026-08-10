// This project genuinely sets no cookies — verified by hand: no
// document.cookie/localStorage use anywhere in this codebase, no
// analytics, and the map tile/style providers (MapToolkit, Mapterhorn)
// don't set any either. The one real risk was the YouTube video embeds
// in PopupContent.tsx, which used to load youtube.com/embed — confirmed
// via a real browser that it sets several tracking cookies on load. Now
// pointed at youtube-nocookie.com/embed, confirmed to set zero.
//
// The one thing this component itself stores (a "seen" flag) is
// localStorage, not a cookie: never sent to any server, and disclosed as
// such in the notice text below rather than left unmentioned.
const SEEN_KEY = "bearlens-cookie-notice-seen";

export function hasSeenCookieNotice(): boolean {
  try {
    return localStorage.getItem(SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

function markCookieNoticeSeen(): void {
  try {
    localStorage.setItem(SEEN_KEY, "1");
  } catch {
    // Storage unavailable (e.g. blocked) — nothing to fall back to here,
    // the notice will just show again next visit, which is harmless.
  }
}

export function CookieNotice({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="cookie-notice" role="status">
      <div className="cookie-notice-body">
        <h4>Nessun cookie</h4>
        <p>
          Questo sito non usa cookie: niente tracciamento, niente pubblicità, nessuna
          analisi del comportamento di navigazione. I video di YouTube nei popup delle
          segnalazioni sono incorporati in modalità privacy (
          <code>youtube-nocookie.com</code>), che non imposta cookie.
        </p>
        <p className="cookie-notice-note">
          L'unica cosa salvata sul tuo dispositivo è un segnale locale per ricordare
          che hai già letto questo avviso: non è un cookie, resta solo nel tuo
          browser e non viene mai inviato da nessuna parte. Puoi rileggere questo
          messaggio in qualsiasi momento dal link in fondo alla pagina.
        </p>
      </div>
      <button
        type="button"
        onClick={() => {
          markCookieNoticeSeen();
          onDismiss();
        }}
      >
        Ho capito
      </button>
    </div>
  );
}
