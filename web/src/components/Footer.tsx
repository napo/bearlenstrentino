export function Footer() {
  return (
    <footer className="app-footer">
      <h2>Da dove vengono i dati</h2>
      <ol>
        <li>
          Le segnalazioni al centro di questo sito vengono dalla{" "}
          <a
            href="https://www.google.com/maps/d/u/0/viewer?hl=it&ll=46.046016854635916%2C11.082050151280466&z=9&mid=1d43YdLzznhl-VxXOz6kg5ZKLdf5RjG4"
            target="_blank"
            rel="noreferrer"
          >
            mappa pubblica "Mappa orsi Trentino"
          </a>
          , curata da Michele Corti a partire da segnalazioni ricevute su social
          network e gruppi WhatsApp — lo diciamo apertamente perché è lui stesso ad
          averla resa pubblica. Non è un dato ufficiale della Provincia Autonoma di
          Trento né di alcun ente di monitoraggio faunistico, e questo progetto non ha
          alcuna affiliazione con l'autore della mappa sorgente.
        </li>
        <li>
          La posizione di strade ed edifici usata per calcolare le distanze nelle
          sezioni precedenti viene da{" "}
          <a href="https://www.openstreetmap.org" target="_blank" rel="noreferrer">
            OpenStreetMap
          </a>{" "}
          (© contributori di OpenStreetMap, licenza ODbL).
        </li>
        <li>
          Il rilievo del terreno in 3D viene da Mapterhorn, la mappa di base da
          MapToolkit, e la stima della luminosità artificiale notturna da immagini
          satellitari pubbliche NASA GIBS.
        </li>
      </ol>
      <p>
        I nomi di persona e i recapiti citati nelle segnalazioni originali sono
        sostituiti con un codice prima della pubblicazione, per proteggere le persone
        coinvolte.
      </p>
      <p>
        Per dati ufficiali, verificati sul campo, su popolazione e danni da orso in
        Trentino, fai riferimento alla{" "}
        <a
          href="https://grandicarnivori.provincia.tn.it/Segnalazioni-orse-con-piccoli/MAPPA-SEGNALAZIONI-2026"
          target="_blank"
          rel="noreferrer"
        >
          mappa ufficiale della Provincia Autonoma di Trento
        </a>
        . BearLens Trentino non la sostituisce: le è complementare, e non verificato
        sul campo.
      </p>
      <p className="tagline">
        BearLens Trentino — progetto open source, iniziativa personale portata avanti
        nel tempo libero, non affiliata alla Fondazione Bruno Kessler né ad alcun
        ente.
      </p>
    </footer>
  );
}
