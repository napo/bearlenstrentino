import { useEffect, useRef, useState, type RefObject } from "react";

// Shared by MapView and PerceptionMap so both maps get an identical
// fullscreen button — mirrors the same pattern already used for charts
// (see charts/ChartCard.tsx), just targeting a map container instead of
// an ECharts instance. `onChange` typically calls the MapLibre map's own
// `.resize()`, which the map never does on its own when its container
// changes size outside of a window resize event.
export function useFullscreenToggle(
  containerRef: RefObject<HTMLElement | null>,
  onChange?: (isFullscreen: boolean) => void
) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    const handler = () => {
      const active = document.fullscreenElement === containerRef.current;
      setIsFullscreen(active);
      onChangeRef.current?.(active);
    };
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, [containerRef]);

  function toggleFullscreen() {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      containerRef.current?.requestFullscreen();
    }
  }

  return { isFullscreen, toggleFullscreen };
}
