export function Header() {
  return (
    <header className="app-header">
      <img src={`${import.meta.env.BASE_URL}logo.png`} alt="BearLens Trentino" />
      <div className="title-block">
        <h1>BearLens Trentino</h1>
        <p>Segnalazioni di presenza dell'orso: cosa mostrano, e cosa no.</p>
      </div>
    </header>
  );
}
