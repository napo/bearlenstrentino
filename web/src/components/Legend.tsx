import { CATEGORY_STYLES, type DisplayCategory } from "../data/categories";

const SHAPE_CSS: Record<string, React.CSSProperties> = {
  circle: { borderRadius: "50%" },
  "circle-outline": { borderRadius: "50%", background: "white", border: "2px solid currentColor" },
  diamond: { transform: "rotate(45deg)", width: 10, height: 10 },
  square: {},
  triangle: {
    width: 0,
    height: 0,
    background: "none",
    borderLeft: "7px solid transparent",
    borderRight: "7px solid transparent",
    borderBottom: "12px solid currentColor",
  },
};

// The legend doubles as the map's type filter (Milestone 7): clicking a
// category toggles its visibility on the map above. This is the only
// interactive control for "which evidence types are shown" — deliberately
// local to the map rather than a separate global filter, since it only
// changes what's drawn, not the underlying dataset (see AGENTS.md: the
// map's own display state is not data).
export function Legend({
  visible,
  onToggle,
}: {
  visible: Set<DisplayCategory>;
  onToggle: (category: DisplayCategory) => void;
}) {
  return (
    <div className="legend">
      {Object.values(CATEGORY_STYLES).map((style) => {
        const isVisible = visible.has(style.id);
        return (
          <button
            key={style.id}
            type="button"
            className="legend-item legend-item-toggle"
            aria-pressed={isVisible}
            onClick={() => onToggle(style.id)}
            style={{ color: style.color, opacity: isVisible ? 1 : 0.4 }}
            title={isVisible ? "Clicca per nascondere sulla mappa" : "Clicca per mostrare sulla mappa"}
          >
            <span
              className="legend-swatch"
              style={{
                background: style.shape === "triangle" || style.shape === "circle-outline" ? undefined : style.color,
                ...SHAPE_CSS[style.shape],
              }}
            />
            {style.label}
          </button>
        );
      })}
      <span className="legend-note">
        Clicca una voce per mostrarla/nasconderla sulla mappa. Il numero di
        segnalazioni non è il numero di orsi. L'opacità indica quanto è recente la
        data dell'evento (piena = recente, tenue = storica o non datata); non indica
        gravità.
      </span>
    </div>
  );
}
