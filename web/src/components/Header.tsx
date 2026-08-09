export function Header() {
  return (
    <header className="app-header">
      <img src={`${import.meta.env.BASE_URL}logo.png`} alt="BearLens Trentino" />
      <div className="title-block">
        <h1>BearLens Trentino</h1>
        <p>Una lente critica sulle segnalazioni di orso in Trentino.</p>
      </div>
    </header>
  );
}
